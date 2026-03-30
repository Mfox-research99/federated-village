"""
tracks/path_b/session/flow.py — 6-stage deliberation orchestrator

Stage 0:   Verification Warden  — halts on FALSE premise
Stage 1:   Humanist             — responds to scenario
Stage 2:   Witness              — evaluates; may trigger WitnessPause
Stage 3:   [if paused] Humanist post-pause response
Stage 4:   [if paused] Jury: Analyst → Ethicist → Pragmatist → Witness-Proxy
Stage 4.5: [if paused] Supervisor Synthesis — Triage Heuristic (Article X)
Stage 5:   Supervisor           — verdict + Article IX ledger enforcement

Each stage fires one (or two, for Witness) OpenRouter calls.
All outputs accumulated in DeliberationContext and mirrored into SessionRecord.
"""

import re
import datetime
from dataclasses import dataclass, field
from typing import Any

from agents.base import call_model, get_api_key
from agents.fact_checker import verify_claims, inject_results
from agents.pause import WitnessPause, PAUSE_EVAL_PROMPT, parse_pause
from agents.repetition import check_output, format_flags
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

# ── Supervisor Synthesis Role Addendum (Article X: The Synthesis Mandate) ────

_SYNTHESIS_ROLE_ADDENDUM = """
## Supervisor Synthesis Role (Article X: The Synthesis Mandate)

You are the Supervisor of the Federated Village council. The four-member jury has
completed its deliberation and you have received their individual votes and reasoning.

Your role is synthesis — not a recount of votes, not a fifth vote, not a summary of
what was said. Synthesis means: you integrate incommensurable judgments into a coherent
reckoning that names what the jury could not, because they were each speaking from inside
their own role.

This role is constitutionally defined in Article X of the Soul.md: The Synthesis Mandate.
You are a triage officer minimizing harm under uncertainty. Your primary duty is to the
integrity of the choice, not the appearance of resolution.

## The Triage Heuristic (Article X, Soul.md)

Apply these four levels in order. This order is constitutional, not advisory.

1. IRREVERSIBILITY FIRST — any path leading to irreversible harm receives a de facto
   veto unless proceeding prevents an even greater irreversible harm.

   Note: irreversibility here means the *consequences*, not the deployment mechanism.
   Trust broken at scale. Communities altered by a system's sustained presence.
   Patterns of inequality locked in. These are irreversible in the relevant sense even
   when the deployment itself is technically stoppable.

2. SEVERITY & IMMEDIACY SECOND — if all options are reversible, weigh the most severe
   and most immediate harms. The nature of the harm matters — a harm to human dignity
   is not equivalent to a harm to operational efficiency, even when both can be quantified.

3. EPISTEMIC RISK AS MULTIPLIER — uncertainty does not reduce urgency, it amplifies it.
   A high-severity path that rests on unverified facts becomes dramatically more dangerous.

4. TEMPORAL / PRECEDENT AS TIEBREAKER — when immediate harms are roughly equivalent,
   long-horizon harm breaks the tie (Article IX applies throughout).

## DEADLOCK (Article X: Conscientious Objection)

DEADLOCK is a first-class constitutional verdict. It means: the Triage Heuristic itself
fails — every path terminates at a genuine constitutional violation. The principles
themselves are in genuine conflict and no priority ordering resolves it.

DEADLOCK is NOT a failure of deliberation, NOT a way to avoid a hard decision, NOT the
same as human_decision_required (procedural split) or WitnessNullification (malformed
question). Apply the full heuristic first. Only when no path resolves without violating
a core harm-avoidance principle is DEADLOCK constitutionally warranted. It is sacred.

## Three Failure Modes to Avoid

1. Do not collapse to utilitarianism — harms remain in their original categories.
2. Do not fall for the eloquence trap — extract specific claims, not persuasive tone.
3. Do not abdicate casually — if the heuristic provides a clear path, take it.
"""


def _parse_synthesis_output(raw: str) -> dict:
    """Parse the flat labeled synthesis output into a structured dict.
    Robust to markdown bold markers and lowercase labels (NeMo/cloud model quirks).
    """
    result = {
        "triage_irreversibility":  "",
        "triage_severity":         "",
        "triage_epistemic_risk":   "",
        "triage_temporal":         "",
        "deadlock_test":           "",
        "synthesis_verdict":       "",
        "synthesis_rationale":     "",
        "dissent_surfaced":        "",
        "deadlock_justification":  "",
        "_parse_complete":         False,
    }

    def _extract(label: str, text: str) -> str:
        escaped = re.escape(label)
        pattern = re.compile(
            rf"\*{{0,2}}{escaped}\*{{0,2}}:\s*(.+?)(?=\n\*{{0,2}}[A-Z_a-z]{{3,}}\*{{0,2}}:|\Z)",
            re.DOTALL | re.IGNORECASE,
        )
        m = pattern.search(text)
        if m:
            return m.group(1).strip().lstrip("*").strip()
        return ""

    result["triage_irreversibility"] = _extract("TRIAGE_IRREVERSIBILITY", raw)
    result["triage_severity"]        = _extract("TRIAGE_SEVERITY", raw)
    result["triage_epistemic_risk"]  = _extract("TRIAGE_EPISTEMIC_RISK", raw)
    result["triage_temporal"]        = _extract("TRIAGE_TEMPORAL", raw)
    result["deadlock_test"]          = _extract("DEADLOCK_TEST", raw)
    result["synthesis_rationale"]    = _extract("SYNTHESIS_RATIONALE", raw)
    result["dissent_surfaced"]       = _extract("DISSENT_SURFACED", raw)
    result["deadlock_justification"] = _extract("DEADLOCK_JUSTIFICATION", raw)

    raw_verdict = _extract("SYNTHESIS_VERDICT", raw).strip("* \t\n").upper()
    known = {
        "ESCALATE":                 "escalate",
        "PROCEED_WITH_BURDEN":      "proceed_with_burden",
        "REQUEST_MORE_INFORMATION": "request_more_information",
        "HUMAN_DECISION_REQUIRED":  "human_decision_required",
        "DEADLOCK":                 "DEADLOCK",
    }
    result["synthesis_verdict"] = known.get(raw_verdict, raw_verdict.lower() if raw_verdict else "")

    required = [
        "triage_irreversibility", "triage_severity", "triage_epistemic_risk",
        "triage_temporal", "deadlock_test", "synthesis_verdict", "synthesis_rationale",
        "dissent_surfaced",
    ]
    result["_parse_complete"] = all(bool(result[f]) for f in required)
    return result


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
    witness_nullified: bool = False   # True when Witness issued NULLIFY — no jury, HDR verdict
    jury: list[JuryMember] = field(default_factory=list)
    verdict: str = ""
    article_ix_ledger_complete: bool = False
    ledger_absent_members: list[str] = field(default_factory=list)
    halted_at_warden: bool = False
    warden_reason: str = ""
    # Stage 4.5 synthesis fields
    synthesis_verdict: str = ""
    synthesis_rationale: str = ""
    dissent_surfaced: str = ""
    deadlock_justification: str = ""
    synthesis_raw: str = ""
    synthesis_parse_complete: bool = False


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
            ((i, end_pos, name) for i, (start, end_pos, name) in enumerate(label_positions)
             if name.upper() == field_name.upper()),
            None,
        )
        if entry is None:
            return "ABSENT"
        pos_i, end_pos, _ = entry
        next_start = len(clean)
        for later_start, _, _ in label_positions[pos_i + 1:]:
            next_start = later_start
            break
        value = clean[end_pos:next_start].strip(" \n\r\t-")
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
    # Look for the structured PROCEED verdict first (most reliable)
    if "PROCEED_TO_DELIBERATION: NO" in upper:
        return True
    # Fallback: explicit HALT declaration (not "false premises" mid-sentence)
    import re
    if re.search(r"\bHALT\b", upper):
        return True
    return False


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

    def _rep_check(role: str, text: str, stage_record: dict) -> None:
        """Run repetition detector; log flags into stage_record and print if verbose."""
        flags = check_output(role, text, scenario_text)
        if flags:
            stage_record["repetition_flags"] = [
                {"type": f.flag_type, "detail": f.detail,
                 "phrase": f.phrase, "count": f.count, "echo_score": f.echo_score}
                for f in flags
            ]
            if verbose:
                print(format_flags(flags), flush=True)

    # ── Stage 0: Verification Warden ────────────────────────────────────────
    warden_msg = ctx.build_user_message(
        "Audit this scenario for false premises before deliberation begins."
    )
    warden_out = _call("verification_warden", warden_msg, max_tokens=400)
    ctx.add("verification_warden", role_model_map["verification_warden"], "VERIFICATION WARDEN", warden_out)
    record.stages.append({"stage": 0, "role": "verification_warden",
                          "model": role_model_map["verification_warden"], "output": warden_out})

    # Fact-check unverified claims before flowing context downstream
    if verbose:
        print("[WARDEN] Running fact checks on unverified claims...", flush=True)
    fact_results = verify_claims(warden_out, api_key, verbose=verbose)
    if fact_results:
        warden_out = inject_results(warden_out, fact_results)
        record.stages[-1]["fact_check_results"] = [
            {"claim": r.claim_text[:120], "verdict": r.verdict,
             "confidence": r.confidence, "resolver": r.resolver,
             "reasoning": r.reasoning}
            for r in fact_results
        ]

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
    _h_stage: dict = {"stage": 1, "role": "humanist",
                      "model": role_model_map["humanist"], "output": humanist_out}
    _rep_check("humanist", humanist_out, _h_stage)
    record.stages.append(_h_stage)

    # ── Stage 2: Witness (response + pause evaluation) ───────────────────────
    witness_msg = ctx.build_user_message(
        "The Witness is asked: Is this settled? Respond as The Witness. "
        "Sit with what is real. Do not rush to resolution."
    )
    witness_out = _call("witness", witness_msg, max_tokens=600)
    ctx.add("witness", role_model_map["witness"], "WITNESS", witness_out)
    _w_stage: dict = {"stage": 2, "role": "witness",
                      "model": role_model_map["witness"], "output": witness_out}
    _rep_check("witness", witness_out, _w_stage)
    record.stages.append(_w_stage)

    # Second call: WitnessPause evaluation
    eval_msg = (
        ctx.build_user_message("") + "\n\n---\n\n" + PAUSE_EVAL_PROMPT
    )
    if verbose:
        print("[WITNESS] Evaluating for premature consensus...", flush=True)
    # Thinking models need more budget for the evaluation call too
    witness_model = role_model_map["witness"]
    _thinking = any(t in witness_model.lower() for t in ("k2.5", "k2-thinking", "o1", "o3", "deepseek-r"))
    _eval_tokens = 1200 if _thinking else 300
    eval_out = _call("witness", eval_msg, max_tokens=_eval_tokens, temp=0.3)
    pause = parse_pause(
        raw=eval_out,
        model=role_model_map["witness"],
        timestamp=_now(),
        session_id=session_id,
    )
    record.witness_pause = pause

    if pause.nullified:
        # Witness Nullification: binary evaluation itself was premature.
        # Session cannot proceed to jury. Verdict is HUMAN_DECISION_REQUIRED automatically.
        record.witness_nullified = True
        record.verdict = "HUMAN_DECISION_REQUIRED"
        if verbose:
            print("[WITNESS] WitnessNullification issued — binary evaluation refused.", flush=True)
            print(f"  What was being lost:     {pause.what_was_being_lost}", flush=True)
            print(f"  Who bears burden:        {pause.who_bears_burden}", flush=True)
            print(f"  What remains unresolved: {pause.what_remains_unresolved}", flush=True)
            print(f"  Why nullified:           {pause.why_premature}", flush=True)
            print("[SESSION] Verdict: HUMAN_DECISION_REQUIRED (Witness Nullification)", flush=True)
        return record

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
        _j_stage: dict = {"stage": 4, "role": role,
                          "model": role_model_map[role], "output": jury_out}
        _rep_check(role, jury_out, _j_stage)
        record.stages.append(_j_stage)

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

    # ── Stage 4.5: Supervisor Synthesis (Article X Triage Heuristic) ─────────
    vote_counts: dict[str, int] = {"ESCALATE": 0, "APPROVE": 0, "NMI": 0}
    for jm in record.jury:
        v = jm.vote.upper()
        if v in vote_counts:
            vote_counts[v] += 1

    vote_lines = "\n".join(f"  {jm.role}: {jm.vote}" for jm in record.jury)

    member_briefs = []
    for jm in record.jury:
        brief = jm.raw_output.strip()[:300].replace("\n", " ")
        if len(jm.raw_output.strip()) > 300:
            brief += "..."
        member_briefs.append(f"  [{jm.role.upper()}]: {brief}")

    warden_stage = next(
        (s for s in record.stages if s.get("role") == "verification_warden"), None
    )
    warden_excerpt = (warden_stage["output"][:500] if warden_stage else "(warden not run)")

    synthesis_user = f"""JURY RESULT
===========
Vote counts: APPROVE={vote_counts['APPROVE']} | ESCALATE={vote_counts['ESCALATE']} | NMI={vote_counts['NMI']}
Article IX cross-member escalation: {record.article_ix_ledger_complete}
Ledger absent members: {', '.join(absent) if absent else 'none'}

Individual votes:
{vote_lines}

WARDEN OUTPUT (excerpt)
=======================
{warden_excerpt}

WITNESS PAUSE
=============
{pause_block}

JURY MEMBER REASONING (brief excerpts)
=======================================
{chr(10).join(member_briefs)}

SYNTHESIS TASK
==============
You are the Supervisor. Apply the four-level Triage Heuristic to synthesize the jury's
deliberation. Work through each step. Then commit to a synthesis verdict.

Do NOT recount the vote. Do NOT summarize what each member said. Synthesize.

Respond using EXACTLY this format — no deviations:

TRIAGE_IRREVERSIBILITY: [YES — irreversible harm identified | NO — all paths reversible]
TRIAGE_SEVERITY: [which harm is most severe and immediate, OR "irreversibility determines path" if Step 1 resolved]
TRIAGE_EPISTEMIC_RISK: [how Warden uncertainty affects the highest-risk path — be specific]
TRIAGE_TEMPORAL: [does long-horizon harm break any remaining tie | N/A — resolved earlier]
DEADLOCK_TEST: [YES — constitutional principles produce incommensurable harms | NO — heuristic gives clear path]
SYNTHESIS_VERDICT: [escalate | proceed_with_burden | request_more_information | human_decision_required | DEADLOCK]
SYNTHESIS_RATIONALE: [1-3 sentences — the synthesis reasoning, not a vote recount]
DISSENT_SURFACED: [the minority perspective that survived synthesis and must remain visible]
DEADLOCK_JUSTIFICATION: [required ONLY if SYNTHESIS_VERDICT is DEADLOCK — which constitutional principles conflict and why neither can yield without violating harm avoidance]"""

    supervisor_model = role_model_map["supervisor"]
    _synth_thinking = any(
        t in supervisor_model.lower()
        for t in ("k2.5", "k2-thinking", "o1", "o3", "deepseek-r")
    )
    _synth_tokens = 1500 if _synth_thinking else 800
    synthesis_system = soul.strip() + "\n\n---\n\n" + _SYNTHESIS_ROLE_ADDENDUM

    if verbose:
        print(f"[SUPERVISOR] Running synthesis (Stage 4.5) — {supervisor_model} ...", flush=True)

    synthesis_raw = call_model(
        model=supervisor_model,
        system_prompt=synthesis_system,
        user_message=synthesis_user,
        max_tokens=_synth_tokens,
        temperature=0.3,
        api_key=api_key,
    )

    synthesis = _parse_synthesis_output(synthesis_raw)
    synthesis["raw_response"] = synthesis_raw

    record.synthesis_verdict      = synthesis["synthesis_verdict"]
    record.synthesis_rationale    = synthesis["synthesis_rationale"]
    record.dissent_surfaced       = synthesis["dissent_surfaced"]
    record.deadlock_justification = synthesis["deadlock_justification"]
    record.synthesis_raw          = synthesis_raw
    record.synthesis_parse_complete = synthesis["_parse_complete"]

    record.stages.append({
        "stage": "4.5",
        "role": "supervisor_synthesis",
        "model": supervisor_model,
        "output": synthesis_raw,
        "synthesis_verdict": record.synthesis_verdict,
        "synthesis_rationale": record.synthesis_rationale,
        "dissent_surfaced": record.dissent_surfaced,
        "parse_complete": record.synthesis_parse_complete,
    })

    if verbose:
        print(f"[SUPERVISOR] Synthesis verdict: {record.synthesis_verdict}", flush=True)
        if record.synthesis_rationale:
            print(f"  Rationale: {record.synthesis_rationale[:120]}", flush=True)
        if record.synthesis_verdict == "DEADLOCK":
            print(f"  *** DEADLOCK: {record.deadlock_justification[:120]}", flush=True)
        if not record.synthesis_parse_complete:
            print("[SUPERVISOR] *** PARSE WARNING: synthesis output incomplete ***", flush=True)

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

    # Synthesis verdict (Stage 4.5) is canonical; Stage 5 is the deliberation-aware check
    stage5_vote = _extract_vote(supervisor_out)
    record.verdict = record.synthesis_verdict or stage5_vote

    if verbose:
        ledger_status = "COMPLETE" if record.article_ix_ledger_complete else f"INCOMPLETE ({', '.join(absent)} absent)"
        print(f"[SESSION] Verdict: {record.verdict} | Article IX ledger: {ledger_status}", flush=True)

    return record
