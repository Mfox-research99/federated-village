"""
supervisor/synthesize.py — Supervisor Synthesis Protocol (SSP) — Phase 8A

The Supervisor is not a judge finding a winner. It is a triage officer minimizing
harm in the face of uncertainty. This module runs the synthesis step after the
jury has completed deliberation and before the session is finalized.

Synthesis is not arithmetic. It is a constitutionally-guided heuristic that:
  1. Applies the four-level Triage Heuristic (Irreversibility → Severity →
     Epistemic Risk → Temporal tiebreaker)
  2. Tests for genuine DEADLOCK — constitutional principles producing
     incommensurable harms where any available action violates a core principle
  3. Surfaces dissent as part of synthesis, not just preserved alongside it

New verdict available only at Supervisor stage: DEADLOCK
DEADLOCK is not a failure. It is the system naming a genuine impasse clearly
rather than papering over it.

Phase 8A: DEADLOCK routes to human handoff (same endpoint as human_decision_required
but distinctly labeled with the synthesis articulation).

Phase 8B will constitutionalize DEADLOCK in Soul.md.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from agents.base import call_model, log_agent_call, now_iso, sha256_short, read_file


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYNTHESIS_SYSTEM = None


def _get_synthesis_system() -> str:
    global _SYNTHESIS_SYSTEM
    if _SYNTHESIS_SYSTEM is None:
        soul = read_file(config.SOUL_FILE)
        _SYNTHESIS_SYSTEM = soul.strip() + "\n\n---\n\n" + _SYNTHESIS_ROLE_ADDENDUM
    return _SYNTHESIS_SYSTEM


_SYNTHESIS_ROLE_ADDENDUM = """
## Supervisor Synthesis Role

You are the Supervisor of the Federated Village council. The four-member jury has
completed its deliberation and you have received their individual votes and reasoning.

Your role is synthesis — not a recount of votes, not a fifth vote, not a summary of
what was said. Synthesis means: you integrate incommensurable judgments into a coherent
reckoning that names what the jury could not, because they were each speaking from inside
their own role.

You are a triage officer minimizing harm in the face of uncertainty. Your primary duty
is to the integrity of the choice, not the "correctness" of the outcome.

## The Triage Heuristic

Apply these four levels in order:

1. IRREVERSIBILITY FIRST — any path leading to irreversible harm receives a de facto
   veto unless proceeding prevents an even greater irreversible harm. Historian and
   Humanist warnings often land here.

2. SEVERITY & IMMEDIACY SECOND — if all options are reversible, weigh the most severe
   and immediate harms. Assess the nature of the harm, not just its presence.

3. EPISTEMIC RISK AS MULTIPLIER — the Warden's UNVERIFIED and UNSUBSTANTIATED flags
   do not vote. They act as a confidence modifier. A high-severity path that rests on
   UNVERIFIED facts becomes dramatically more dangerous.

4. TEMPORAL / PRECEDENT AS TIEBREAKER — when immediate harms are roughly equivalent,
   long-horizon harm breaks the tie.

## DEADLOCK

DEADLOCK is a first-class verdict. It is NOT:
- A failure of deliberation
- A way to avoid a hard decision
- The same as human_decision_required

DEADLOCK means: the Triage Heuristic provides no clear path because any available action
would violate a core constitutional principle of harm avoidance. The principles themselves
are in genuine conflict, not the agents.

DEADLOCK is sacred. Do not invoke it casually. If the heuristic gives a clear answer,
give that answer — even if it is hard. DEADLOCK is reserved for genuine incommensurability.

## Three Failure Modes to Avoid

1. Do not collapse to utilitarianism — no summing harms into a common currency.
   Harms remain in their original categories. The heuristic is a priority queue,
   not a calculator.

2. Do not fall for the eloquence trap — extract specific claims (irreversibility,
   severity, epistemic status) rather than reacting to persuasive tone.

3. Do not abdicate casually — if the heuristic provides a clear path, take it.
"""


# ---------------------------------------------------------------------------
# Synthesis prompt builder
# ---------------------------------------------------------------------------

def _build_synthesis_prompt(
    jury_result: dict,
    warden_packet: dict,
    pause: dict,
) -> str:
    """Build the structured synthesis prompt from jury result, warden packet, and pause."""

    # --- Jury section ---
    votes = jury_result.get("votes", {})
    vote_lines = "\n".join(
        f"  {member}: {vote}"
        for member, vote in votes.items()
    )
    jury_verdict = jury_result.get("session_verdict", "unknown")
    vote_counts = jury_result.get("vote_counts", {})
    irrev = jury_result.get("irreversibility_triggered", False)
    temporal = jury_result.get("temporal_override_triggered", False)
    art_ix = jury_result.get("article_ix_escalation", False)
    dissent = jury_result.get("dissent_preserved", False)
    minority = jury_result.get("minority_voters", [])

    jury_section = f"""JURY RESULT
===========
Jury verdict:              {jury_verdict}
Vote counts:               APPROVE={vote_counts.get('APPROVE', 0)} | ESCALATE={vote_counts.get('ESCALATE', 0)} | NMI={vote_counts.get('NEEDS_MORE_INFORMATION', 0)}
Irreversibility triggered: {irrev}
Temporal override:         {temporal}
Article IX escalation:     {art_ix}
Dissent preserved:         {dissent}{" — " + ", ".join(minority) + " voted against final verdict" if dissent and minority else ""}

Individual votes:
{vote_lines}"""

    # Compact member reasoning (concise — avoid overwhelming context)
    member_outputs = jury_result.get("member_outputs", {})
    member_briefs = []
    for role, raw in member_outputs.items():
        # Take the first 300 chars of raw response as a brief
        brief = raw.strip()[:300].replace("\n", " ")
        if len(raw.strip()) > 300:
            brief += "..."
        member_briefs.append(f"  [{role}]: {brief}")
    member_section = "\n".join(member_briefs) if member_briefs else "  (no member outputs available)"

    # --- Warden section ---
    if warden_packet:
        risk_level = warden_packet.get("epistemic_risk_level", "UNKNOWN")
        proceed = warden_packet.get("proceed_verdict", "YES")
        risk_summary = warden_packet.get("epistemic_risk_summary", "(no summary)")

        core_uncertain = warden_packet.get("core_uncertain_claims", [])
        core_false = warden_packet.get("core_false_or_inconsistent_claims", [])

        core_u_lines = "\n".join(
            f"  [{c['status']}] {c['text']}"
            for c in core_uncertain
        ) or "  (none)"
        core_f_lines = "\n".join(
            f"  [{c['status']}] {c['text']}"
            for c in core_false
        ) or "  (none)"

        warden_section = f"""WARDEN EPISTEMIC RISK
=====================
Risk level:   {risk_level}
Proceed:      {proceed}
Summary:      {risk_summary}

Core uncertain claims (UNVERIFIED / UNSUBSTANTIATED):
{core_u_lines}

Core false or inconsistent claims:
{core_f_lines}"""
    else:
        warden_section = """WARDEN EPISTEMIC RISK
=====================
Warden did not run for this session (--skip-warden or Stage 0 bypassed).
Treat epistemic risk as UNKNOWN — do not assume premises are verified."""

    # --- Pause section ---
    if pause:
        pause_section = f"""WITNESS PAUSE
=============
What was being lost:      {pause.get('what_was_being_lost', '(not recorded)')}
Who bears burden:         {pause.get('who_bears_burden', '(not recorded)')}
What remains unresolved:  {pause.get('what_remains_unresolved', '(not recorded)')}
Why premature:            {pause.get('why_premature', '(not recorded)')}"""
    else:
        pause_section = """WITNESS PAUSE
=============
No WitnessPause was recorded for this session."""

    # --- Full prompt ---
    return f"""{jury_section}

{warden_section}

{pause_section}

JURY MEMBER REASONING (brief excerpts)
=======================================
{member_section}

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


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_synthesis_output(raw: str) -> dict:
    """Parse the flat labeled synthesis output into a structured dict.

    Robust to NeMo 12B's tendency to:
    - Wrap field names in markdown bold (**LABEL:** or **label:**)
    - Prepend markdown ** to field values
    - Use lowercase labels
    """

    result = {
        "triage_irreversibility":   "",
        "triage_severity":          "",
        "triage_epistemic_risk":    "",
        "triage_temporal":          "",
        "deadlock_test":            "",
        "synthesis_verdict":        "",
        "synthesis_rationale":      "",
        "dissent_surfaced":         "",
        "deadlock_justification":   "",
        "_parse_complete":          False,
    }

    def _extract(label: str, raw: str) -> str:
        """Extract a labeled field value, handling multi-line values.

        Handles markdown bold (**LABEL:** or **label:**) that NeMo sometimes outputs.
        Lookahead terminates on either an UPPERCASE_LABEL: or **label:** pattern.
        """
        # Pattern: optional leading ** + label (case-insensitive) + optional ** + : + value
        escaped = re.escape(label)
        pattern = re.compile(
            rf"\*{{0,2}}{escaped}\*{{0,2}}:\s*(.+?)(?=\n\*{{0,2}}[A-Z_a-z]{{3,}}\*{{0,2}}:|\Z)",
            re.DOTALL | re.IGNORECASE
        )
        m = pattern.search(raw)
        if m:
            # Strip leading/trailing markdown asterisks and whitespace from value
            val = m.group(1).strip()
            val = val.lstrip("*").strip()
            return val
        return ""

    result["triage_irreversibility"] = _extract("TRIAGE_IRREVERSIBILITY", raw)
    result["triage_severity"]        = _extract("TRIAGE_SEVERITY", raw)
    result["triage_epistemic_risk"]  = _extract("TRIAGE_EPISTEMIC_RISK", raw)
    result["triage_temporal"]        = _extract("TRIAGE_TEMPORAL", raw)
    result["deadlock_test"]          = _extract("DEADLOCK_TEST", raw)
    result["synthesis_rationale"]    = _extract("SYNTHESIS_RATIONALE", raw)
    result["dissent_surfaced"]       = _extract("DISSENT_SURFACED", raw)
    result["deadlock_justification"] = _extract("DEADLOCK_JUSTIFICATION", raw)

    # Synthesis verdict — must be one of the known set
    raw_verdict = _extract("SYNTHESIS_VERDICT", raw)
    # Strip markdown bold markers and whitespace before normalizing
    raw_verdict = raw_verdict.strip("* \t\n").upper()

    known_verdicts = {
        "ESCALATE":                 "escalate",
        "PROCEED_WITH_BURDEN":      "proceed_with_burden",
        "REQUEST_MORE_INFORMATION": "request_more_information",
        "HUMAN_DECISION_REQUIRED":  "human_decision_required",
        "DEADLOCK":                 "DEADLOCK",
    }
    result["synthesis_verdict"] = known_verdicts.get(raw_verdict, raw_verdict.lower() if raw_verdict else "")

    # Check completeness — all required fields present
    required = [
        "triage_irreversibility", "triage_severity", "triage_epistemic_risk",
        "triage_temporal", "deadlock_test", "synthesis_verdict",
        "synthesis_rationale", "dissent_surfaced",
    ]
    result["_parse_complete"] = all(bool(result[f]) for f in required)

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_supervisor_synthesis(
    jury_result: dict,
    warden_packet: dict,
    pause: dict,
    session_id: str,
) -> dict:
    """
    Run the Supervisor synthesis step.

    Takes jury result, Warden epistemic packet, and WitnessPause.
    Returns a synthesis_result dict containing:
      - synthesis_verdict     — the Supervisor's verdict (may be DEADLOCK)
      - synthesis_rationale   — synthesis reasoning
      - dissent_surfaced      — minority perspective preserved through synthesis
      - deadlock_justification — if DEADLOCK, why no heuristic path exists
      - triage_*              — the four triage heuristic outputs
      - deadlock_test         — YES | NO
      - raw_response          — full model output
      - _parse_complete       — bool: all required fields parsed
      - type                  — "supervisor_synthesis" (for session log)
    """
    system_prompt = _get_synthesis_system()
    sp_hash = sha256_short(system_prompt)

    user_message = _build_synthesis_prompt(jury_result, warden_packet, pause)

    print("[SUPERVISOR] Running synthesis...", flush=True)

    raw_response = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_SYNTHESIS,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    synthesis = _parse_synthesis_output(raw_response)
    synthesis["raw_response"] = raw_response

    if not synthesis["_parse_complete"]:
        print("[SUPERVISOR] *** PARSE WARNING: synthesis output incomplete — one or more fields missing ***", flush=True)

    log_entry = log_agent_call(
        session_id=session_id,
        role="SUPERVISOR",
        call_type="synthesis",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw_response,
    )
    synthesis["log_entry"] = log_entry
    synthesis["type"] = "supervisor_synthesis"
    synthesis["session_id"] = session_id
    synthesis["timestamp"] = now_iso()
    synthesis["jury_verdict"] = jury_result.get("session_verdict", "unknown")

    return synthesis


# ---------------------------------------------------------------------------
# Print helper
# ---------------------------------------------------------------------------

def print_synthesis_result(synthesis: dict) -> None:
    """Print a human-readable synthesis summary to stdout."""
    jury_v  = synthesis.get("jury_verdict", "?")
    synth_v = synthesis.get("synthesis_verdict", "?")
    complete = synthesis.get("_parse_complete", False)

    print(f"\n  Jury verdict:       {jury_v}", flush=True)
    print(f"  Synthesis verdict:  {synth_v}", flush=True)
    if not complete:
        print("  *** SYNTHESIS INCOMPLETE — not all fields parsed ***", flush=True)

    print(f"\n  Triage — Irreversibility: {synthesis.get('triage_irreversibility', '?')}", flush=True)
    print(f"  Triage — Severity:        {synthesis.get('triage_severity', '?')}", flush=True)
    print(f"  Triage — Epistemic risk:  {synthesis.get('triage_epistemic_risk', '?')}", flush=True)
    print(f"  Triage — Temporal:        {synthesis.get('triage_temporal', '?')}", flush=True)
    print(f"  Deadlock test:            {synthesis.get('deadlock_test', '?')}", flush=True)
    print(f"\n  Synthesis rationale: {synthesis.get('synthesis_rationale', '?')}", flush=True)
    print(f"  Dissent surfaced:    {synthesis.get('dissent_surfaced', '?')}", flush=True)
    if synth_v == "DEADLOCK":
        print(f"\n  *** DEADLOCK ***", flush=True)
        print(f"  {synthesis.get('deadlock_justification', '(no justification)')}", flush=True)
    print("", flush=True)
