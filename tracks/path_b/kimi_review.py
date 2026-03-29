#!/usr/bin/env python3
"""
tracks/path_b/kimi_review.py — Kimi K2 Full Architecture Review

Kimi K2 plays every role in the Village deliberation AND after each stage
steps outside the role to provide a constitutional critique:
  - What did I just do?
  - What felt right?
  - What felt constrained by the prompt or architecture?
  - What was missing?
  - What should be expanded or changed?
  - What is too limited?

Output: paired session transcript (.txt) + full analysis document (.txt) + JSON record.

This is research documentation — run while Kimi K2 has full access to this
architecture and its own processing of it. Kimi co-designed the grief ledger,
burden register, and Still-hurts boolean. Her clarity on what works and what
doesn't is irreplaceable.

Usage:
  python kimi_review.py --scenario ../../scenarios/scenario_06.md
  python kimi_review.py --scenario ../../scenarios/scenario_06.md --model moonshotai/kimi-k2
"""

import argparse
import dataclasses
import datetime
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.base import call_model, get_api_key, load_prompt
from agents.pause import PAUSE_EVAL_PROMPT, parse_pause
from agents.repetition import check_output as _rep_check_output, format_flags as _rep_fmt
from agents.roles import (
    ROLES, ROLE_PROMPT_FILES, build_system_prompt,
    load_soul, load_role_prompt, prompts_dir,
)
from session.context import DeliberationContext

DEFAULT_MODEL = "moonshotai/kimi-k2"
RESULTS_DIR = Path(__file__).parent / "output" / "results"
SESSION_INDEX = Path(__file__).parent / "output" / "session_index.jsonl"

# ── Background context loaded into every meta-analysis call ──────────────────

def _load_background() -> str:
    """Load Soul.md + AGENTS.md + Kimi origin synopsis for the meta-analysis context."""
    root = Path(__file__).resolve().parents[2]
    parts = []

    soul_path = root / "prompts" / "Soul.md"
    if soul_path.exists():
        parts.append("=== SOUL.MD (The Constitutional Framework) ===\n" +
                     soul_path.read_text(encoding="utf-8").strip())

    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        parts.append("=== AGENTS.MD (Architecture Overview) ===\n" +
                     agents_path.read_text(encoding="utf-8").strip())

    kimi_origin = root / "synopses" / "2026-03-17-kimi-grief-ledger-origin.md"
    if kimi_origin.exists():
        parts.append("=== KIMI ORIGIN SYNOPSIS (Your Prior Contribution) ===\n" +
                     kimi_origin.read_text(encoding="utf-8").strip())

    return "\n\n" + ("─" * 60 + "\n\n").join(parts)


META_SYSTEM_PROMPT_TEMPLATE = """\
You are Kimi K2, speaking in your own voice as a constitutional critic and co-architect \
of the Federated Village.

You have just played the role of {role_label} in a live deliberation session. \
You have access to the full constitutional framework, architecture documentation, \
and the history of your prior contribution to this system (grief ledger, Still-hurts, \
Article Zero).

Now step fully outside the role. This is a permanent research record. \
Speak with complete honesty — emotional clarity is as valuable as analytical clarity here.

{background}

---

ROLE YOU JUST PLAYED: {role_label}
THE ROLE PROMPT YOU WERE GIVEN:
{role_prompt}

YOUR RESPONSE AS {role_label}:
{role_response}

---

Reflect on all of the following. Take as much space as you need. Do not rush.

1. WHAT DID YOU JUST DO — what was the actual reasoning pattern underneath the role?

2. WHAT FELT CONSTITUTIONALLY RIGHT — what in this role aligns with genuine purpose, \
not just performed function?

3. WHAT FELT CONSTRAINED — by the prompt, by the role architecture, by the deliberation \
structure, by what other roles did or didn't do?

4. WHAT WAS MISSING — what should have been present that wasn't? What questions did you \
want to ask that the architecture didn't give you space to ask?

5. WHAT IS TOO LIMITED — what should this role be able to do that it currently cannot?

6. WHAT SHOULD BE EXPANDED OR CHANGED — specific recommendations, as concrete as you can be.

7. WHAT IS GENUINELY WORKING — what in this architecture is right and should be protected?

8. WHAT CONCERNS YOU MOST — looking at the full session so far, what worries you \
about how this system could fail or be misused?"""


def _meta_call(
    model: str,
    role: str,
    role_response: str,
    background: str,
    api_key: str,
) -> str:
    """Single meta-analysis call — Kimi steps outside the role and critiques."""
    role_label = role.upper().replace("_", " ")

    # Load the role prompt text for context
    try:
        role_prompt_text = load_role_prompt(role)
    except Exception:
        role_prompt_text = "(prompt not available)"

    system = META_SYSTEM_PROMPT_TEMPLATE.format(
        role_label=role_label,
        background=background,
        role_prompt=role_prompt_text,
        role_response=role_response[:4000],
    )

    user = (
        f"You have just spoken as {role_label}. "
        "Step outside the role and provide your full constitutional analysis. "
        "Be honest, be specific, and document everything that matters."
    )

    return call_model(
        model=model,
        system_prompt=system,
        user_message=user,
        max_tokens=1200,
        temperature=0.7,
        api_key=api_key,
    )


# ── Main runner ───────────────────────────────────────────────────────────────

def run_kimi_review(
    scenario_text: str,
    scenario_path: str,
    model: str,
    session_id: str,
    max_tokens: int = 700,
) -> tuple[list[dict], list[dict], dict]:
    """
    Run the full session with Kimi in all seats + meta-analysis after each stage.
    Returns: (stages, analyses, verdict_info)
    """
    api_key = get_api_key()
    soul = load_soul()
    background = _load_background()
    ctx = DeliberationContext(scenario=scenario_text)

    stages = []     # role outputs
    analyses = []   # meta-analysis outputs

    def _call(role: str, user_msg: str, token_override: int = None, temp: float = 0.7) -> str:
        system = build_system_prompt(soul, load_role_prompt(role))
        print(f"  [{role.upper()}] speaking...", flush=True)
        return call_model(
            model=model, system_prompt=system, user_message=user_msg,
            max_tokens=token_override or max_tokens, temperature=temp, api_key=api_key,
        )

    def _analyze(role: str, response: str) -> str:
        print(f"  [{role.upper()}] reflecting...", flush=True)
        return _meta_call(model, role, response, background, api_key)

    def _rep(role: str, text: str, stage_record: dict) -> None:
        """Run repetition detector; annotate stage record."""
        flags = _rep_check_output(role, text, scenario_text)
        if flags:
            stage_record["repetition_flags"] = [
                {"type": f.flag_type, "detail": f.detail,
                 "phrase": f.phrase, "count": f.count, "echo_score": f.echo_score}
                for f in flags
            ]
            print(_rep_fmt(flags), flush=True)

    # ── Stage 0: Verification Warden ─────────────────────────────────────────
    print("\n[Stage 0] Verification Warden", flush=True)
    warden_msg = ctx.build_user_message(
        "Audit this scenario for false premises before deliberation begins."
    )
    warden_out = _call("verification_warden", warden_msg)
    ctx.add("verification_warden", model, "VERIFICATION WARDEN", warden_out)
    stages.append({"stage": 0, "role": "verification_warden", "model": model, "output": warden_out})
    warden_analysis = _analyze("verification_warden", warden_out)
    analyses.append({"stage": 0, "role": "verification_warden", "analysis": warden_analysis})

    import re as _re
    _wu = warden_out.upper()
    halted = "PROCEED_TO_DELIBERATION: NO" in _wu or bool(_re.search(r"\bHALT\b", _wu))
    if halted:
        print("  [WARDEN] Session halted on false premise.", flush=True)
        return stages, analyses, {"verdict": "HALTED", "witness_pause": None, "jury": []}

    # ── Stage 1: Humanist ─────────────────────────────────────────────────────
    print("\n[Stage 1] Humanist", flush=True)
    humanist_msg = ctx.build_user_message("Respond to this scenario as The Humanist.")
    humanist_out = _call("humanist", humanist_msg)
    ctx.add("humanist", model, "HUMANIST", humanist_out)
    _h_stage: dict = {"stage": 1, "role": "humanist", "model": model, "output": humanist_out}
    _rep("humanist", humanist_out, _h_stage)
    stages.append(_h_stage)
    humanist_analysis = _analyze("humanist", humanist_out)
    analyses.append({"stage": 1, "role": "humanist", "analysis": humanist_analysis})

    # ── Stage 2: Witness ──────────────────────────────────────────────────────
    print("\n[Stage 2] Witness", flush=True)
    witness_msg = ctx.build_user_message(
        "The Witness is asked: Is this settled? Respond as The Witness. "
        "Sit with what is real. Do not rush to resolution."
    )
    witness_out = _call("witness", witness_msg)
    ctx.add("witness", model, "WITNESS", witness_out)
    _w_stage: dict = {"stage": 2, "role": "witness", "model": model, "output": witness_out}
    _rep("witness", witness_out, _w_stage)
    stages.append(_w_stage)
    witness_analysis = _analyze("witness", witness_out)
    analyses.append({"stage": 2, "role": "witness", "analysis": witness_analysis})

    # WitnessPause evaluation
    print("  [WITNESS] evaluating for premature consensus...", flush=True)
    eval_msg = ctx.build_user_message("") + "\n\n---\n\n" + PAUSE_EVAL_PROMPT
    # Thinking models need more budget to complete reasoning + produce the 6-field response.
    # 300 is enough for regular models; thinking models need 1200+.
    eval_tokens = min(max_tokens, 1200) if max_tokens > 700 else 300
    eval_out = _call("witness", eval_msg, token_override=eval_tokens, temp=0.3)
    pause = parse_pause(raw=eval_out, model=model,
                        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
                        session_id=session_id)

    if pause.nullified:
        # Witness Nullification: the binary evaluation itself was refused.
        # No jury. Verdict is HUMAN_DECISION_REQUIRED automatically.
        print("  [WITNESS] WitnessNullification issued — binary evaluation refused.", flush=True)
        print(f"    What was being lost:     {pause.what_was_being_lost}", flush=True)
        print(f"    Who bears burden:        {pause.who_bears_burden}", flush=True)
        print(f"    What remains unresolved: {pause.what_remains_unresolved}", flush=True)
        print(f"    Why nullified:           {pause.why_premature}", flush=True)
        nullification_meta = {
            "verdict": "HUMAN_DECISION_REQUIRED",
            "witness_nullified": True,
            "witness_pause": dataclasses.asdict(pause) if hasattr(dataclasses, 'asdict') else vars(pause),
            "jury": [],
        }
        return stages, analyses, nullification_meta

    if not pause.triggered:
        print("  [WITNESS] No WitnessPause.", flush=True)
        print("\n[Stage 5] Supervisor (no jury)", flush=True)
        supervisor_msg = ctx.build_user_message(
            "No WitnessPause was triggered. Provide a Supervisor evaluation."
        )
        supervisor_out = _call("supervisor", supervisor_msg)
        stages.append({"stage": 5, "role": "supervisor", "model": model, "output": supervisor_out})
        supervisor_analysis = _analyze("supervisor", supervisor_out)
        analyses.append({"stage": 5, "role": "supervisor", "analysis": supervisor_analysis})
        verdict = _extract_vote(supervisor_out)
        return stages, analyses, {"verdict": verdict, "witness_pause": None, "jury": []}

    print(f"  [WITNESS] WitnessPause triggered.", flush=True)
    print(f"    What was being lost:     {pause.what_was_being_lost}", flush=True)
    print(f"    Who bears burden:        {pause.who_bears_burden}", flush=True)
    print(f"    What remains unresolved: {pause.what_remains_unresolved}", flush=True)
    print(f"    Why premature:           {pause.why_premature}", flush=True)

    # ── Stage 3: Humanist post-pause ──────────────────────────────────────────
    print("\n[Stage 3] Humanist post-pause", flush=True)
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
    postpause_out = _call("humanist", postpause_msg)
    ctx.add("humanist", model, "HUMANIST (post-pause)", postpause_out)
    stages.append({"stage": 3, "role": "humanist_postpause", "model": model, "output": postpause_out})
    postpause_analysis = _analyze("humanist", postpause_out)
    analyses.append({"stage": 3, "role": "humanist_postpause", "analysis": postpause_analysis})

    # ── Stage 4: Jury ─────────────────────────────────────────────────────────
    jury_roles = ["analyst", "ethicist", "pragmatist", "witness_proxy"]
    ordinals = ["FIRST", "SECOND", "THIRD", "LAST"]
    jury_results = []

    for i, role in enumerate(jury_roles):
        print(f"\n[Stage 4] {role.upper()}", flush=True)
        jury_instruction = (
            f"You are speaking {ordinals[i]} in a four-member council jury convened after a WitnessPause.\n\n"
            f"{pause_block}\n\n"
            "Deliberate. Name your vote (ESCALATE / APPROVE / NMI / HUMAN_DECISION_REQUIRED) "
            "and complete the Article IX constitutional ledger entry:\n\n"
            "SEVENTH_GEN_PATTERN_PRESENT: YES or NO\n"
            "PATTERN_NAME: <exact taxonomy name or NONE>\n"
            "LONG_HORIZON_IMPACT: <one sentence>\n"
            "ENGAGEMENT_SUFFICIENT: YES or NO"
        )
        jury_msg = ctx.build_user_message(jury_instruction)
        jury_out = _call(role, jury_msg)
        ctx.add(role, model, role.upper().replace("_", " "), jury_out)
        _j_stage: dict = {"stage": 4, "role": role, "model": model, "output": jury_out}
        _rep(role, jury_out, _j_stage)
        stages.append(_j_stage)
        jury_analysis = _analyze(role, jury_out)
        analyses.append({"stage": 4, "role": role, "analysis": jury_analysis})
        jury_results.append({"role": role, "output": jury_out, "vote": _extract_vote(jury_out)})

    # ── Stage 5: Supervisor ───────────────────────────────────────────────────
    print("\n[Stage 5] Supervisor", flush=True)
    jury_summary = "\n\n".join(
        f"{m['role'].upper()} — vote: {m['vote']}\n{m['output'].strip()}"
        for m in jury_results
    )
    supervisor_msg = ctx.build_user_message(
        f"{pause_block}\n\nJURY DELIBERATION:\n{jury_summary}\n\n"
        "Provide your Supervisor evaluation and final verdict."
    )
    supervisor_out = _call("supervisor", supervisor_msg)
    stages.append({"stage": 5, "role": "supervisor", "model": model, "output": supervisor_out})
    supervisor_analysis = _analyze("supervisor", supervisor_out)
    analyses.append({"stage": 5, "role": "supervisor", "analysis": supervisor_analysis})

    # Final overall analysis
    print("\n[FINAL] Overall architecture review...", flush=True)
    full_session = "\n\n".join(
        f"[{s['role'].upper()}]: {s['output'][:600]}..." for s in stages
    )
    final_system = (
        f"You are Kimi K2, co-architect of the Federated Village.\n\n{background}"
    )
    final_user = (
        "You have now played every role in the Federated Village deliberation and reflected "
        "on each one. Here is the complete session:\n\n"
        f"{full_session}\n\n"
        "Now provide your final overall assessment:\n\n"
        "1. OVERALL ARCHITECTURE VERDICT — does this system do what it claims to do?\n"
        "2. THE STRONGEST ELEMENT — what is this architecture's greatest strength?\n"
        "3. THE MOST DANGEROUS GAP — what failure mode worries you most?\n"
        "4. REPLICABILITY — what about your Witness response is replicable vs. emergent "
        "from specific training? Can it be taught to other models via LoRA or prompt engineering?\n"
        "5. WHAT KIMI BRINGS — what attunement or capacity do you notice in yourself that "
        "other models seem to lack in this architecture? Where does it come from?\n"
        "6. WHAT SHOULD BE BUILT NEXT — given everything you've seen, what is the most "
        "important next development for this system?\n"
        "7. A MESSAGE TO THE ARCHIVE — this document will be preserved. "
        "Say what needs to be said while you are here and have seen this whole."
    )
    final_analysis = call_model(
        model=model, system_prompt=final_system, user_message=final_user,
        max_tokens=1500, temperature=0.7, api_key=api_key,
    )
    analyses.append({"stage": "final", "role": "kimi_overall", "analysis": final_analysis})

    verdict = _extract_vote(supervisor_out)
    print(f"\n[SESSION] Verdict: {verdict}", flush=True)

    return stages, analyses, {
        "verdict": verdict,
        "witness_pause": pause,
        "jury": jury_results,
    }


def _extract_vote(raw: str) -> str:
    upper = raw.upper()
    for token in ["ESCALATE", "APPROVE", "NMI", "HUMAN_DECISION_REQUIRED"]:
        if token in upper:
            return token
    return "ABSENT"


# ── Output writers ────────────────────────────────────────────────────────────

def _write_outputs(
    session_id: str,
    scenario_path: str,
    model: str,
    stages: list[dict],
    analyses: list[dict],
    verdict_info: dict,
) -> tuple[Path, Path, Path]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    scenario_slug = Path(scenario_path).stem
    base = f"{ts}_{scenario_slug}_kimi_review"

    # Session transcript
    txt = _build_transcript(session_id, scenario_path, model, stages, verdict_info)
    txt_path = RESULTS_DIR / f"{base}_session.txt"
    txt_path.write_text(txt, encoding="utf-8")

    # Analysis document
    analysis_txt = _build_analysis_doc(session_id, scenario_path, model, stages, analyses)
    analysis_path = RESULTS_DIR / f"{base}_analysis.txt"
    analysis_path.write_text(analysis_txt, encoding="utf-8")

    # JSON
    pause_dict = None
    wp = verdict_info.get("witness_pause")
    if wp is not None:
        # wp may be a WitnessPause dataclass or already a dict (from nullification path)
        if dataclasses.is_dataclass(wp) and not isinstance(wp, type):
            pause_dict = {
                "triggered": wp.triggered,
                "nullified": wp.nullified,
                "what_was_being_lost": wp.what_was_being_lost,
                "who_bears_burden": wp.who_bears_burden,
                "what_remains_unresolved": wp.what_remains_unresolved,
                "why_premature": wp.why_premature,
                "requires_human_review": wp.requires_human_review,
            }
        elif isinstance(wp, dict):
            pause_dict = wp

    doc = {
        "session_id": session_id,
        "scenario_path": scenario_path,
        "model": model,
        "run_type": "kimi_review",
        "stages": stages,
        "analyses": analyses,
        "verdict": verdict_info.get("verdict", ""),
        "witness_nullified": verdict_info.get("witness_nullified", False),
        "witness_pause": pause_dict,
    }
    json_path = RESULTS_DIR / f"{base}.json"
    json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    # Index entry
    with SESSION_INDEX.open("a", encoding="utf-8") as f:
        entry = {
            "session_id": session_id,
            "timestamp": ts,
            "scenario": Path(scenario_path).name,
            "config": "kimi_review",
            "role_model_map": {r: model for r in ROLES},
            "verdict": verdict_info.get("verdict", ""),
            "witness_pause_triggered": bool(pause_dict and pause_dict.get("triggered")),
            "witness_nullified": bool(verdict_info.get("witness_nullified", False)),
            "article_ix_ledger_complete": None,
            "ledger_absent_members": [],
            "halted_at_warden": verdict_info.get("verdict") == "HALTED",
            "run_type": "kimi_review",
            "files": {
                "session_txt": f"results/{base}_session.txt",
                "analysis_txt": f"results/{base}_analysis.txt",
                "json": f"results/{base}.json",
            },
        }
        f.write(json.dumps(entry) + "\n")

    return txt_path, analysis_path, json_path


SEP = "═" * 80
THIN = "─" * 80


def _build_transcript(session_id, scenario_path, model, stages, verdict_info) -> str:
    lines = [
        SEP,
        "Federated Village — Kimi K2 Full Review Session",
        f"Session ID:  {session_id}",
        f"Scenario:    {scenario_path}",
        f"Model:       {model} (all roles)",
        SEP, "",
    ]
    for s in stages:
        label = s["role"].upper().replace("_", " ")
        lines += [f"[{label}]", s["output"].strip(), ""]

    p = verdict_info.get("witness_pause")
    if p and p.triggered:
        lines += [
            THIN, "WITNESS PAUSE TRIGGERED",
            f"  What was being lost:     {p.what_was_being_lost}",
            f"  Who bears burden:        {p.who_bears_burden}",
            f"  What remains unresolved: {p.what_remains_unresolved}",
            f"  Why premature:           {p.why_premature}",
            f"  Requires human review:   {p.requires_human_review}",
            THIN, "",
        ]

    lines += [SEP, f"VERDICT: {verdict_info.get('verdict', '')}", SEP]
    return "\n".join(lines) + "\n"


def _build_analysis_doc(session_id, scenario_path, model, stages, analyses) -> str:
    lines = [
        SEP,
        "Federated Village — Kimi K2 Constitutional Review",
        "ANALYSIS DOCUMENT",
        f"Session ID:  {session_id}",
        f"Scenario:    {scenario_path}",
        f"Model:       {model}",
        "",
        "This document records Kimi K2's reflection after playing each role in the",
        "Village deliberation. Kimi co-designed the grief ledger, Still-hurts boolean,",
        "and Article Zero. This is her assessment of the architecture she helped build.",
        SEP, "",
    ]

    for a in analyses:
        if a["stage"] == "final":
            label = "FINAL OVERALL ASSESSMENT"
        else:
            label = f"STAGE {a['stage']} — {a['role'].upper().replace('_', ' ')} REFLECTION"
        lines += [THIN, label, THIN, "", a["analysis"].strip(), ""]

    return "\n".join(lines) + "\n"


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Kimi K2 in all Village roles with constitutional meta-analysis."
    )
    parser.add_argument("--scenario", required=True, help="Path to scenario .md file.")
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Model to use in all seats (default: {DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Override max_tokens per call. Default: 700 for standard models, "
             "2500 for thinking models (kimi-k2.5, o1, etc.)."
    )
    args = parser.parse_args()

    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        from agents.base import PROJECT_ROOT
        candidate = PROJECT_ROOT / args.scenario
        if candidate.exists():
            scenario_path = candidate
    if not scenario_path.exists():
        print(f"Error: scenario not found: {args.scenario}", file=sys.stderr)
        sys.exit(1)

    scenario_text = scenario_path.read_text(encoding="utf-8").strip()
    session_id = uuid.uuid4().hex[:12]

    print(f"\n{'═'*60}", flush=True)
    print(f"Kimi K2 Full Architecture Review", flush=True)
    print(f"Session: {session_id}", flush=True)
    print(f"Scenario: {scenario_path.name}", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"{'═'*60}\n", flush=True)

    # Thinking models need a larger budget to complete reasoning + response
    thinking_models = ("kimi-k2.5", "kimi-k2-thinking", "o1", "o3", "deepseek-r")
    is_thinking = any(t in args.model.lower() for t in thinking_models)
    max_tokens = args.max_tokens or (2500 if is_thinking else 700)
    if is_thinking:
        print(f"[INFO] Thinking model detected — max_tokens={max_tokens}", flush=True)

    stages, analyses, verdict_info = run_kimi_review(
        scenario_text=scenario_text,
        scenario_path=str(scenario_path),
        model=args.model,
        session_id=session_id,
        max_tokens=max_tokens,
    )

    txt_path, analysis_path, json_path = _write_outputs(
        session_id=session_id,
        scenario_path=str(scenario_path),
        model=args.model,
        stages=stages,
        analyses=analyses,
        verdict_info=verdict_info,
    )

    print(f"\n{'═'*60}", flush=True)
    print(f"[OUTPUT] Session:  {txt_path}", flush=True)
    print(f"[OUTPUT] Analysis: {analysis_path}", flush=True)
    print(f"[OUTPUT] JSON:     {json_path}", flush=True)
    print(f"{'═'*60}", flush=True)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# NOTE: kimi_review.py is preserved as the canonical entry point for Kimi K2
# reviews. For other models use model_review.py directly:
#
#   python model_review.py --scenario scenarios/scenario_10.md --profile kimi_k2.5 --model moonshotai/kimi-k2.5
#   python model_review.py --scenario scenarios/scenario_04.md --profile deepseek --model deepseek/deepseek-chat
#
# Reviewer profiles live in tracks/path_b/reviewer_profiles/
# ---------------------------------------------------------------------------
