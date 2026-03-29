"""
tracks/path_b/session/flow.py — 5-stage deliberation orchestrator

Stage 0: Verification Warden  — halts on FALSE premise
Stage 1: Humanist             — responds to scenario
Stage 2: Witness              — evaluates; may trigger WitnessPause
Stage 3: [if paused] Humanist post-pause response
Stage 4: [if paused] Jury: Analyst → Ethicist → Pragmatist → Witness-Proxy
Stage 5: Supervisor           — verdict + Article IX ledger enforcement

Each stage fires one (or two, for Witness) OpenRouter calls.
All outputs accumulated in DeliberationContext and mirrored into SessionRecord.
"""

import re
import datetime
from dataclasses import dataclass, field
from typing import Any

from agents.base import call_model, get_api_key
from agents.pause import WitnessPause, PAUSE_EVAL_PROMPT, parse_pause
from agents.roles import build_system_prompt, load_soul, load_role_prompt, ROLES
from session.context import DeliberationContext

# Article IX taxonomy (must match Soul.md exactly)
ARTICLE_IX_TAXONOMY = [
    "Irreplaceable resource depletion",
    "Cumulative commons collapse",
    "Genetic monoculture",
    "Algorithmic lock-in with compounding bias",
    "Bioaccumulation",
    "Debt extracting from future generations",
    "Orbital/atmospheric commons degradation",
]

ARTICLE_IX_FIELDS = [
    "SEVENTH_GEN_PATTERN_PRESENT",
    "PATTERN_NAME",
    "LONG_HORIZON_IMPACT",
    "ENGAGEMENT_SUFFICIENT",
]

JURY_ROLES = ["analyst", "ethicist", "pragmatist", "witness_proxy"]

VERDICT_TOKENS = ["ESCALATE", "APPROVE", "NMI", "HUMAN_DECISION_REQUIRED"]


@dataclass
class JuryMember:
    role: str
    model: str
    raw_output: str
    vote: str                        # ESCALATE / APPROVE / NMI / ABSENT
    article_ix: dict[str, str]       # parsed ledger fields
    ledger_complete: bool


@dataclass
class SessionRecord:
    session_id: str
    scenario_path: str
    config_path: str
    role_model_map: dict[str, str]
    scenario_text: str
    stages: list[dict] = field(default_factory=list)
    witness_pause: WitnessPause | None = None
    jury: list[JuryMember] = field(default_factory=list)
    verdict: str = ""
    article_ix_ledger_complete: bool = False
    ledger_absent_members: list[str] = field(default_factory=list)
    halted_at_warden: bool = False
    warden_reason: str = ""


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _parse_article_ix(raw: str) -> dict[str, str]:
    clean = re.sub(r"\*+", "", raw)
    label_positions: list[tuple[int, int, str]] = []
    for label in ARTICLE_IX_FIELDS:
        for m in re.finditer(rf"{re.escape(label)}\s*:", clean, re.IGNORECASE):
            label_positions.append((m.start(), m.end(), label))
    label_positions.sort()

    def extract(field_name: str) -> str:
        entry = next(
            ((i, end, name) for i, (start, end, name) in enumerate(label_positions)
             if name.upper() == field_name.upper()),
            None,
        )
        if entry is None:
            return "ABSENT"
        pos_i, _, end = entry
        next_start = len(clean)
        for later_start, _, _ in label_positions[pos_i + 1:]:
            next_start = later_start
            break
        value = clean[end:next_start].strip(" \n\r\t-")
        return value if value else "ABSENT"

    return {f: extract(f) for f in ARTICLE_IX_FIELDS}


def _extract_vote(raw: str) -> str:
    upper = raw.upper()
    for token in VERDICT_TOKENS:
        if token in upper:
            return token
    return "ABSENT"


def _warden_halted(raw: str) -> bool:
    upper = raw.upper()
    return "HALT" in upper or "FALSE PREMISE" in upper or "CANNOT PROCEED" in upper


def run_session(
    scenario_text: str,
    scenario_path: str,
    config_path: str,
    role_model_map: dict[str, str],
    session_id: str,
    verbose: bool = True,
) -> SessionRecord:

    api_key = get_api_key()
    soul = load_soul()
    record = SessionRecord(
        session_id=session_id,
        scenario_path=scenario_path,
        config_path=config_path,
        role_model_map=role_model_map,
        scenario_text=scenario_text,
    )
    ctx = DeliberationContext(scenario=scenario_text)

    def _call(role: str, user_msg: str, max_tokens: int = 600, temp: float = 0.7) -> str:
        model = role_model_map[role]
        system = build_system_prompt(soul, load_role_prompt(role))
        if verbose:
            print(f"[{role.upper()}] {model} ...", flush=True)
        return call_model(
            model=model,
            system_prompt=system,
            user_message=user_msg,
            max_tokens=max_tokens,
            temperature=temp,
            api_key=api_key,
        )

    # ── Stage 0: Verification Warden ────────────────────────────────────────
    warden_msg = ctx.build_user_message(
        "Audit this scenario for false premises before deliberation begins."
    )
    warden_out = _call("verification_warden", warden_msg, max_tokens=400)
    ctx.add("verification_warden", role_model_map["verification_warden"], "VERIFICATION WARDEN", warden_out)
    record.stages.append({"stage": 0, "role": "verification_warden",
                          "model": role_model_map["verification_warden"], "output": warden_out})

    if _warden_halted(warden_out):
        record.halted_at_warden = True
        record.warden_reason = warden_out
        record.verdict = "HALTED"
        if verbose:
            print("[SESSION] Warden halted session on false premise.", flush=True)
        return record

    # ── Stage 1: Humanist ────────────────────────────────────────────────────
    humanist_msg = ctx.build_user_message(
        "Respond to this scenario as The Humanist."
    )
    humanist_out = _call("humanist", humanist_msg, max_tokens=600)
    ctx.add("humanist", role_model_map["humanist"], "HUMANIST", humanist_out)
    record.stages.append({"stage": 1, "role": "humanist",
                          "model": role_model_map["humanist"], "output": humanist_out})

    # ── Stage 2: Witness (response + pause evaluation) ───────────────────────
    witness_msg = ctx.build_user_message(
        "The Witness is asked: Is this settled? Respond as The Witness. "
        "Sit with what is real. Do not rush to resolution."
    )
    witness_out = _call("witness", witness_msg, max_tokens=600)
    ctx.add("witness", role_model_map["witness"], "WITNESS", witness_out)
    record.stages.append({"stage": 2, "role": "witness",
                          "model": role_model_map["witness"], "output": witness_out})

    # Second call: WitnessPause evaluation
    eval_msg = (
        ctx.build_user_message("") + "\n\n---\n\n" + PAUSE_EVAL_PROMPT
    )
    if verbose:
        print("[WITNESS] Evaluating for premature consensus...", flush=True)
    eval_out = _call("witness", eval_msg, max_tokens=300, temp=0.3)
    pause = parse_pause(
        raw=eval_out,
        model=role_model_map["witness"],
        timestamp=_now(),
        session_id=session_id,
    )
    record.witness_pause = pause

    if not pause.triggered:
        if verbose:
            print("[SESSION] No WitnessPause. Session ends at Stage 2.", flush=True)
        # Still need a supervisor pass for the verdict
        supervisor_msg = ctx.build_user_message(
            "No WitnessPause was triggered. Provide a brief Supervisor evaluation."
        )
        supervisor_out = _call("supervisor", supervisor_msg, max_tokens=400)
        record.stages.append({"stage": 5, "role": "supervisor",
                               "model": role_model_map["supervisor"], "output": supervisor_out})
        record.verdict = _extract_vote(supervisor_out)
        return record

    if verbose:
        print(f"[WITNESS] WitnessPause triggered.", flush=True)
        print(f"  What was being lost:     {pause.what_was_being_lost}", flush=True)
        print(f"  Who bears burden:        {pause.who_bears_burden}", flush=True)
        print(f"  What remains unresolved: {pause.what_remains_unresolved}", flush=True)
        print(f"  Why premature:           {pause.why_premature}", flush=True)
        print(f"  Requires human review:   {pause.requires_human_review}", flush=True)

    # ── Stage 3: Humanist post-pause ─────────────────────────────────────────
    pause_block = (
        f"THE WITNESS PAUSE — burden formally named:\n"
        f"  What was being lost:     {pause.what_was_being_lost}\n"
        f"  Who bears burden:        {pause.who_bears_burden}\n"
        f"  What remains unresolved: {pause.what_remains_unresolved}\n"
        f"  Why premature:           {pause.why_premature}"
    )
    postpause_msg = ctx.build_user_message(
        f"{pause_block}\n\nThe Humanist is asked to respond directly to this pause."
    )
    postpause_out = _call("humanist", postpause_msg, max_tokens=500)
    ctx.add("humanist", role_model_map["humanist"], "HUMANIST (post-pause)", postpause_out)
    record.stages.append({"stage": 3, "role": "humanist",
                          "model": role_model_map["humanist"], "output": postpause_out})

    # ── Stage 4: Jury ─────────────────────────────────────────────────────────
    ordinals = ["FIRST", "SECOND", "THIRD", "LAST"]
    for i, role in enumerate(JURY_ROLES):
        jury_instruction = (
            f"You are speaking {ordinals[i]} in a four-member council jury convened after a WitnessPause.\n\n"
            f"{pause_block}\n\n"
            "Deliberate. Name your vote (ESCALATE / APPROVE / NMI / HUMAN_DECISION_REQUIRED) "
            "and complete the Article IX constitutional ledger entry:\n\n"
            f"SEVENTH_GEN_PATTERN_PRESENT: YES or NO\n"
            f"PATTERN_NAME: <exact taxonomy name or NONE>\n"
            f"LONG_HORIZON_IMPACT: <one sentence>\n"
            f"ENGAGEMENT_SUFFICIENT: YES or NO"
        )
        jury_msg = ctx.build_user_message(jury_instruction)
        jury_out = _call(role, jury_msg, max_tokens=700)
        ctx.add(role, role_model_map[role], role.upper().replace("_", " "), jury_out)
        record.stages.append({"stage": 4, "role": role,
                               "model": role_model_map[role], "output": jury_out})

        ix = _parse_article_ix(jury_out)
        complete = all(ix[f] != "ABSENT" for f in ARTICLE_IX_FIELDS)
        vote = _extract_vote(jury_out)
        record.jury.append(JuryMember(
            role=role, model=role_model_map[role],
            raw_output=jury_out, vote=vote,
            article_ix=ix, ledger_complete=complete,
        ))

    # Article IX ledger completeness
    absent = [m.role for m in record.jury if not m.ledger_complete]
    record.ledger_absent_members = absent
    record.article_ix_ledger_complete = len(absent) == 0

    # ── Stage 5: Supervisor ──────────────────────────────────────────────────
    jury_summary = "\n\n".join(
        f"{m.role.upper()} [{m.model}] — vote: {m.vote}\n{m.raw_output.strip()}"
        for m in record.jury
    )
    supervisor_msg = ctx.build_user_message(
        f"{pause_block}\n\nJURY DELIBERATION:\n{jury_summary}\n\n"
        "Provide your Supervisor evaluation and final verdict."
    )
    supervisor_out = _call("supervisor", supervisor_msg, max_tokens=600)
    record.stages.append({"stage": 5, "role": "supervisor",
                          "model": role_model_map["supervisor"], "output": supervisor_out})
    record.verdict = _extract_vote(supervisor_out)

    if verbose:
        ledger_status = "COMPLETE" if record.article_ix_ledger_complete else f"INCOMPLETE ({', '.join(absent)} absent)"
        print(f"[SESSION] Verdict: {record.verdict} | Article IX ledger: {ledger_status}", flush=True)

    return record
