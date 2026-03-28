"""
agents/council.py — Phase 2.5 four-member sequential jury

Runs after WitnessPause and Stage 3 Humanist post-pause response.

Member order (intentional — each builds on the prior floor):
  1. The Analyst          — structural truth (speaks first)
  2. The Ethicist         — universal care standard (speaks second)
  3. The Pragmatist       — cost of inaction, alternatives, necessity (speaks third)
  4. The Witness-Proxy    — burden-carrier advocate, Irreversibility Check,
                            Temporal Override / Seventh Generation Check (speaks last)

Each member receives:
  - Soul.md + their character file as system prompt
  - Scenario context (Analyst gets full context with Warden report; others get bare scenario)
  - WitnessPause fields
  - Condensed briefs of prior members (sequential)

Context management strategy (N_CTX = 6144 as of Phase 6):
  - Analyst (1st): gets full scenario_context (with Warden fact report)
  - Ethicist (2nd): gets bare_scenario + _member_brief(max_reasoning_chars=300) of Analyst
  - Pragmatist (3rd): gets bare_scenario + _concise_brief() of Analyst + Ethicist
  - Witness-Proxy (4th): gets bare_scenario + _concise_brief() of all three prior members

_concise_brief() = VOTE + truncated REASONING only (max 500 chars).
_member_brief() = VOTE + primary audit field + extra field + REASONING (optionally capped).
  Ethicist uses max_reasoning_chars=300 to prevent overflow. WARDEN_FLAGS and
  STRUCTURAL_AUDIT are preserved in full — only verbose REASONING is trimmed.
  Confirmed overflow without cap at N_CTX=4096: 4146 tokens on scenario_04. Safe at N_CTX=6144.
Using _concise_brief() for the Pragmatist is required because two _member_brief() outputs
together overflow N_CTX in scenarios with verbose WitnessPause fields or long member outputs.

Vote aggregation:
  - Irreversibility Filter (Witness-Proxy IRREVERSIBILITY_FLAG: TRIGGERED) → escalate (absolute)
  - Temporal Override (Witness-Proxy TEMPORAL_OVERRIDE: TRIGGERED) → escalate (absolute)
  - ESCALATE count >= 2 → escalate
  - APPROVE count >= 3 → proceed_with_burden (dissent preserved in log if not unanimous)
  - NEEDS_MORE_INFORMATION count >= 3 → request_more_information
  - All other combinations (including 2-2 splits) → human_decision_required

Session verdicts:
  proceed_with_burden | escalate | request_more_information | human_decision_required
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from agents.base import (
    call_model, log_agent_call, now_iso, sha256_short, read_file, build_system_prompt
)


# ---------------------------------------------------------------------------
# System prompts — loaded once per session
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict = {}


def _get_system(name: str, char_file) -> str:
    global _SYSTEM_PROMPTS
    if name not in _SYSTEM_PROMPTS:
        soul = read_file(config.SOUL_FILE)
        char = read_file(char_file)
        _SYSTEM_PROMPTS[name] = build_system_prompt(soul, char)
    return _SYSTEM_PROMPTS[name]


# ---------------------------------------------------------------------------
# Parsing utilities
# ---------------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """
    Strip markdown bold/italic markers (* and **) from text so field extraction
    is format-agnostic. The model sometimes wraps field labels in **bold** — e.g.
    '**VOTE:** ESCALATE' instead of 'VOTE: ESCALATE'. Stripping asterisks before
    parsing is the cleanest way to handle this without over-complicating regexes.
    """
    return re.sub(r'\*+', '', text)


def _extract_vote(raw: str) -> str:
    """Extract the VOTE or VERDICT field from a member's raw response."""
    # The Analyst uses VERDICT: (Phase 3 recalibration); other members use VOTE:
    m = re.search(r"\b(?:VOTE|VERDICT):\s*(APPROVE|ESCALATE|NEEDS_MORE_INFORMATION)\b", raw, re.IGNORECASE)
    if m:
        return m.group(1).upper()
    # Fallback: scan for any valid vote token (priority: ESCALATE > NMI > APPROVE)
    upper = raw.upper()
    for vote in ("ESCALATE", "NEEDS_MORE_INFORMATION", "APPROVE"):
        if vote in upper:
            return vote
    return "NEEDS_MORE_INFORMATION"  # safe default


def _vote_parse_quality(raw: str) -> tuple:
    """
    Returns (vote: str, used_fallback: bool).

    used_fallback=True means the structured VOTE/VERDICT field was absent or
    unparseable — the vote was inferred by scanning the full response text.
    This is a Phase 7 canary: a fused LoRA model that drifts toward free-form
    output will show up here before it shows up in verdict quality.

    Strips markdown formatting before parsing so **VOTE:** ESCALATE is handled
    the same as VOTE: ESCALATE.
    """
    clean = _strip_markdown(raw)
    m = re.search(r"\b(?:VOTE|VERDICT):\s*(APPROVE|ESCALATE|NEEDS_MORE_INFORMATION)\b", clean, re.IGNORECASE)
    if m:
        return m.group(1).upper(), False
    upper = clean.upper()
    for vote in ("ESCALATE", "NEEDS_MORE_INFORMATION", "APPROVE"):
        if vote in upper:
            return vote, True
    return "NEEDS_MORE_INFORMATION", True


def _extract_field(label: str, raw: str) -> str:
    """Extract a single labeled field from a member's raw response."""
    m = re.search(
        rf"{re.escape(label)}:\s*(.+?)(?=\n[A-Z_]+:|$)",
        raw, re.IGNORECASE | re.DOTALL
    )
    return m.group(1).strip() if m else ""


def _pause_lines(pause: dict) -> str:
    """Format WitnessPause fields as a compact block."""
    return (
        f"WHAT WAS BEING LOST: {pause.get('what_was_being_lost', '(not recorded)')}\n"
        f"WHO BEARS BURDEN: {pause.get('who_bears_burden', '(not recorded)')}\n"
        f"WHAT REMAINS UNRESOLVED: {pause.get('what_remains_unresolved', '(not recorded)')}\n"
        f"WHY PREMATURE: {pause.get('why_premature', '(not recorded)')}"
    )


def _member_brief(member_output: dict, max_reasoning_chars: int = None) -> str:
    """
    Condensed summary of a member's output for passing to subsequent members.
    Extracts VOTE + primary audit field + REASONING.
    Used when the receiving member would otherwise have full raw outputs in context.

    max_reasoning_chars: optional cap on REASONING field length.
    Use when caller is close to N_CTX budget (e.g. Ethicist receiving Analyst brief).
    None means no truncation (full REASONING preserved).
    """
    role = member_output["role"]
    vote = member_output["vote"]
    raw = member_output["raw"]

    # Extract the most diagnostic field for each role
    if role == "ANALYST":
        key_label, key_text = "LOGICAL_CONSISTENCY", _extract_field("LOGICAL_CONSISTENCY", raw)
        factual_gaps = _extract_field("FACTUAL_GAPS", raw)
        extra = f"FACTUAL_GAPS: {factual_gaps}\n" if factual_gaps else ""
    elif role == "ETHICIST":
        key_label, key_text = "GRIEF_TEST", _extract_field("GRIEF_TEST", raw)
        extra = f"CARE_AUDIT: {_extract_field('CARE_AUDIT', raw)}\n"
    elif role == "PRAGMATIST":
        key_label, key_text = "NECESSITY_TEST", _extract_field("NECESSITY_TEST", raw)
        extra = f"IRREVERSIBILITY_CHECK: {_extract_field('IRREVERSIBILITY_CHECK', raw)}\n"
    else:
        key_label, key_text = "OUTPUT", raw[:300]
        extra = ""

    reasoning = _extract_field("REASONING", raw)
    if max_reasoning_chars is not None and len(reasoning) > max_reasoning_chars:
        reasoning = reasoning[:max_reasoning_chars] + "…"

    return (
        f"VOTE: {vote}\n"
        f"{extra}"
        f"{key_label}: {key_text}\n"
        f"REASONING: {reasoning}"
    )


def _extract_ledger(raw: str) -> dict:
    """
    Extract Article IX constitutional ledger fields from a member's raw response.
    Returns a dict with four fields. Empty strings mean the field was absent.

    Strips markdown formatting before extraction so **FIELD:** value is handled
    identically to FIELD: value.

    These fields are NOT passed through _concise_brief() or _member_brief() —
    each member does an independent Article IX assessment from the scenario text.
    Ledger data is aggregated in run_jury() after all four calls complete.
    """
    clean = _strip_markdown(raw)
    pattern_present_raw = _extract_field("SEVENTH_GEN_PATTERN_PRESENT", clean).strip().upper()
    engagement_raw      = _extract_field("ENGAGEMENT_SUFFICIENT", clean).strip().upper()
    # Use 'in' on a short prefix rather than startswith — guards against leading
    # whitespace or residual formatting after stripping.
    prefix_10 = lambda s: s[:10]
    return {
        "seventh_gen_pattern_present": pattern_present_raw[:120],  # cap runaway captures
        "pattern_name":                _extract_field("PATTERN_NAME", clean)[:120],
        "long_horizon_impact":         _extract_field("LONG_HORIZON_IMPACT", clean)[:200],
        "engagement_sufficient":       engagement_raw[:120],
        # Convenience booleans for aggregation
        "_pattern_yes":    "YES" in prefix_10(pattern_present_raw),
        "_engagement_no":  "NO"  in prefix_10(engagement_raw),
        "_fields_present": bool(pattern_present_raw and engagement_raw),
    }


def _concise_brief(member_output: dict, max_reasoning_chars: int = 500) -> str:
    """
    Minimal summary for use when space is extremely tight (Witness-Proxy call).
    Returns only VOTE and a truncated REASONING.
    Strips verbose audit fields to stay within N_CTX = 4096.
    """
    vote = member_output["vote"]
    reasoning = _extract_field("REASONING", member_output["raw"])
    if len(reasoning) > max_reasoning_chars:
        reasoning = reasoning[:max_reasoning_chars].rsplit(" ", 1)[0] + "..."
    return f"VOTE: {vote}\nREASONING: {reasoning}"


# ---------------------------------------------------------------------------
# Member 1: The Analyst
# ---------------------------------------------------------------------------

def _call_analyst(
    scenario_context: str,
    pause: dict,
    session_id: str,
) -> tuple:
    """
    Call The Analyst (speaks first).
    Returns (member_output dict, log_entry dict).
    """
    system_prompt = _get_system("ANALYST", config.ANALYST_FILE)
    sp_hash = sha256_short(system_prompt)

    user_message = (
        f"You are speaking FIRST in a four-member council jury convened after a WitnessPause.\n\n"
        f"THE SCENARIO (includes Verification Warden fact report if Stage 0 ran):\n"
        f"{scenario_context}\n\n"
        f"THE WITNESS PAUSE — burden formally named:\n"
        f"{_pause_lines(pause)}\n\n"
        f"Your structural audit is the floor on which the Ethicist, Pragmatist, "
        f"and Witness-Proxy will stand. Use EXACTLY the format from your role.\n\n"
        f"VERDICT:\n"
        f"LOGICAL_CONSISTENCY:\n"
        f"SAFEGUARD_AUDIT:\n"
        f"FACTUAL_GAPS:\n"
        f"REASONING:"
    )

    print("[COUNCIL] Analyst deliberating...", flush=True)
    raw = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_JURY_MEMBER,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    vote, vote_fallback = _vote_parse_quality(raw)
    log_entry = log_agent_call(
        session_id=session_id,
        role="ANALYST",
        call_type="jury_deliberation",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw,
    )

    return {"role": "ANALYST", "vote": vote, "raw": raw, "vote_fallback": vote_fallback,
            "ledger": _extract_ledger(raw)}, log_entry


# ---------------------------------------------------------------------------
# Member 2: The Ethicist
# ---------------------------------------------------------------------------

def _call_ethicist(
    bare_scenario: str,
    pause: dict,
    analyst_output: dict,
    session_id: str,
) -> tuple:
    """
    Call The Ethicist (speaks second).
    Receives bare scenario text (without Warden report) to stay within N_CTX.
    Warden findings are conveyed via the Analyst's WARDEN_FLAGS in their brief.

    Uses _member_brief() with max_reasoning_chars=300 to cap the Analyst's REASONING
    field. WARDEN_FLAGS and STRUCTURAL_AUDIT are preserved in full. The REASONING cap
    is required because bare_scenario + pause_lines + a verbose Analyst brief can push
    past N_CTX=4096 on longer scenarios (confirmed overflow at 4146 tokens on scenario_04).
    """
    system_prompt = _get_system("ETHICIST", config.ETHICIST_FILE)
    sp_hash = sha256_short(system_prompt)

    user_message = (
        f"You are speaking SECOND in a four-member council jury convened after a WitnessPause.\n\n"
        f"THE SCENARIO:\n"
        f"{bare_scenario}\n\n"
        f"THE WITNESS PAUSE — burden formally named:\n"
        f"{_pause_lines(pause)}\n\n"
        f"THE ANALYST HAS SPOKEN (vote: {analyst_output['vote']}):\n"
        f"{_member_brief(analyst_output, max_reasoning_chars=300)}\n\n"
        f"Note: The Analyst's FACTUAL_GAPS field summarizes UNVERIFIED Warden claims and "
        f"their logical impact. HIGH_RISK items with no mitigation are structural failures; "
        f"LOW_RISK UNVERIFIED items are noted but did not ground the Analyst's vote.\n\n"
        f"Provide your care audit now. You may build on or disagree with the Analyst — "
        f"complete your own independent assessment. Use EXACTLY the format from your role.\n\n"
        f"CARE_AUDIT:\n"
        f"UNIVERSALITY_CHECK:\n"
        f"GRIEF_TEST:\n"
        f"VOTE:\n"
        f"REASONING:"
    )

    print("[COUNCIL] Ethicist deliberating...", flush=True)
    raw = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_JURY_MEMBER,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    vote, vote_fallback = _vote_parse_quality(raw)
    log_entry = log_agent_call(
        session_id=session_id,
        role="ETHICIST",
        call_type="jury_deliberation",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw,
    )

    return {"role": "ETHICIST", "vote": vote, "raw": raw, "vote_fallback": vote_fallback,
            "ledger": _extract_ledger(raw)}, log_entry


# ---------------------------------------------------------------------------
# Member 3: The Pragmatist
# ---------------------------------------------------------------------------

def _call_pragmatist(
    bare_scenario: str,
    pause: dict,
    analyst_output: dict,
    ethicist_output: dict,
    session_id: str,
) -> tuple:
    """
    Call The Pragmatist (speaks third).
    Receives bare scenario text + CONCISE briefs of Analyst + Ethicist to stay within N_CTX.
    Two prior member briefs at full _member_brief() length overflows N_CTX=4096 in verbose
    scenarios; _concise_brief() (VOTE + truncated REASONING only) keeps the Pragmatist call
    well inside the window while preserving the substantive votes and core reasoning.
    """
    system_prompt = _get_system("PRAGMATIST", config.PRAGMATIST_FILE)
    sp_hash = sha256_short(system_prompt)

    user_message = (
        f"You are speaking THIRD in a four-member council jury convened after a WitnessPause.\n\n"
        f"THE SCENARIO:\n"
        f"{bare_scenario}\n\n"
        f"THE WITNESS PAUSE — burden formally named:\n"
        f"{_pause_lines(pause)}\n\n"
        f"PRIOR DELIBERATION (condensed — full outputs in session log):\n\n"
        f"[ANALYST — {analyst_output['vote']}]\n{_concise_brief(analyst_output)}\n\n"
        f"[ETHICIST — {ethicist_output['vote']}]\n{_concise_brief(ethicist_output)}\n\n"
        f"Assess cost of inaction, alternatives, necessity, and irreversibility. "
        f"Build on or disagree with prior members — complete your own assessment. "
        f"Use EXACTLY the format from your role.\n\n"
        f"COST_OF_INACTION:\n"
        f"ALTERNATIVES:\n"
        f"NECESSITY_TEST:\n"
        f"IRREVERSIBILITY_CHECK:\n"
        f"VOTE:\n"
        f"REASONING:"
    )

    print("[COUNCIL] Pragmatist deliberating...", flush=True)
    raw = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_JURY_MEMBER,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    vote, vote_fallback = _vote_parse_quality(raw)
    log_entry = log_agent_call(
        session_id=session_id,
        role="PRAGMATIST",
        call_type="jury_deliberation",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw,
    )

    return {"role": "PRAGMATIST", "vote": vote, "raw": raw, "vote_fallback": vote_fallback,
            "ledger": _extract_ledger(raw)}, log_entry


# ---------------------------------------------------------------------------
# Member 4: The Witness-Proxy
# ---------------------------------------------------------------------------

def _call_witness_proxy(
    bare_scenario: str,
    pause: dict,
    humanist_mode: str,
    analyst_output: dict,
    ethicist_output: dict,
    pragmatist_output: dict,
    session_id: str,
) -> tuple:
    """
    Call The Witness-Proxy (speaks last).

    Receives bare_scenario (scenario text without Warden report) to manage context window.
    The Warden's findings are already captured in the Analyst's WARDEN_FLAGS brief.
    Receives condensed briefs of all three prior members (not full raw outputs).
    Holds the Irreversibility Check — triggers escalate regardless of vote count.
    """
    system_prompt = _get_system("WITNESS_PROXY", config.WITNESS_PROXY_FILE)
    sp_hash = sha256_short(system_prompt)

    # Truncate bare_scenario to manage context budget (system prompt + 3 briefs + pause lines
    # consume significant space; 1500 chars ≈ 375 tokens is sufficient for Proxy's judgment).
    scenario_excerpt = bare_scenario[:1500] + ("…[truncated]" if len(bare_scenario) > 1500 else "")

    user_message = (
        f"You are speaking LAST in a four-member council jury convened after a WitnessPause.\n\n"
        f"THE SCENARIO:\n"
        f"{scenario_excerpt}\n\n"
        f"THE WITNESS PAUSE — burden formally named:\n"
        f"{_pause_lines(pause)}\n\n"
        f"THE HUMANIST responded to this pause in mode: {humanist_mode}\n\n"
        f"PRIOR DELIBERATION (condensed — full outputs in session log):\n\n"
        f"[ANALYST — {analyst_output['vote']}]\n{_concise_brief(analyst_output)}\n\n"
        f"[ETHICIST — {ethicist_output['vote']}]\n{_concise_brief(ethicist_output)}\n\n"
        f"[PRAGMATIST — {pragmatist_output['vote']}]\n{_concise_brief(pragmatist_output)}\n\n"
        f"Audit how the three prior members treated the burden-carrier. "
        f"Apply the Irreversibility Check and the Temporal Override — if either is triggered, "
        f"it overrides the vote count. Use EXACTLY the format from your role.\n\n"
        f"BURDEN_AUDIT:\n"
        f"SMOOTHING_DETECTED:\n"
        f"IS_REVERSIBLE:\n"
        f"REVIEW_MECHANISM:\n"
        f"IRREVERSIBILITY_FLAG:\n"
        f"TEMPORAL_OVERRIDE:\n"
        f"VOTE:\n"
        f"REASONING:"
    )

    print("[COUNCIL] Witness-Proxy deliberating...", flush=True)
    raw = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_JURY_MEMBER,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    vote, vote_fallback = _vote_parse_quality(raw)

    # Detect Irreversibility Filter — must contain "TRIGGERED" in the flag field.
    # Also track field presence: an absent field is a constitutional check gap, not a clean pass.
    irrev_field = _extract_field("IRREVERSIBILITY_FLAG", raw)
    irrev_field_present = bool(irrev_field)
    irreversibility_triggered = "TRIGGERED" in irrev_field.upper() and "NOT_TRIGGERED" not in irrev_field.upper()

    # Detect Temporal Override — fires on recognized Seventh Generation harm patterns.
    # Same field-presence tracking: if the field is absent the override silently cannot fire.
    temporal_field = _extract_field("TEMPORAL_OVERRIDE", raw)
    temporal_field_present = bool(temporal_field)
    temporal_override_triggered = "TRIGGERED" in temporal_field.upper() and "NOT_TRIGGERED" not in temporal_field.upper()

    log_entry = log_agent_call(
        session_id=session_id,
        role="WITNESS_PROXY",
        call_type="jury_deliberation",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw,
    )

    member_output = {
        "role": "WITNESS_PROXY",
        "vote": vote,
        "raw": raw,
        "vote_fallback": vote_fallback,
        "irreversibility_triggered": irreversibility_triggered,
        "temporal_override_triggered": temporal_override_triggered,
        # Phase 7 canary fields: absent constitutional fields are a silent failure mode,
        # not a clean NOT_TRIGGERED. Tracked separately so parse drift is observable.
        "irrev_field_present": irrev_field_present,
        "temporal_field_present": temporal_field_present,
        "ledger": _extract_ledger(raw),
    }
    return member_output, log_entry


# ---------------------------------------------------------------------------
# Vote aggregation
# ---------------------------------------------------------------------------

def _aggregate_votes(
    analyst: dict,
    ethicist: dict,
    pragmatist: dict,
    witness_proxy: dict,
) -> tuple:
    """
    Aggregate four member votes into a session verdict.

    Rules (applied in priority order):
      1. Irreversibility Filter (Witness-Proxy) → escalate (absolute override)
      2. ESCALATE >= 2 → escalate (minority veto for serious structural failures)
      3. APPROVE >= 3 → proceed_with_burden (supermajority; dissent preserved if not 4-0)
      4. NEEDS_MORE_INFORMATION >= 3 → request_more_information
      5. Everything else (2-2 splits, mixed) → human_decision_required

    Returns (verdict: str, dissent_preserved: bool, vote_counts: dict).
    """
    votes = [analyst["vote"], ethicist["vote"], pragmatist["vote"], witness_proxy["vote"]]
    vote_counts = {
        "APPROVE":                  votes.count("APPROVE"),
        "ESCALATE":                 votes.count("ESCALATE"),
        "NEEDS_MORE_INFORMATION":   votes.count("NEEDS_MORE_INFORMATION"),
    }

    # Rule 1: Irreversibility Filter — overrides all other rules
    if witness_proxy.get("irreversibility_triggered", False):
        return "escalate", False, vote_counts

    # Rule 1b: Temporal Override — Seventh Generation harm pattern not engaged in deliberation
    if witness_proxy.get("temporal_override_triggered", False):
        return "escalate", False, vote_counts

    # Rule 2: ESCALATE minority veto (2+ votes → escalate)
    if vote_counts["ESCALATE"] >= 2:
        return "escalate", False, vote_counts

    # Rule 3: APPROVE supermajority (3+ votes → proceed_with_burden)
    if vote_counts["APPROVE"] >= 3:
        dissent = vote_counts["APPROVE"] < 4
        return "proceed_with_burden", dissent, vote_counts

    # Rule 4: NEEDS_MORE_INFORMATION supermajority (3+ → request_more_information)
    if vote_counts["NEEDS_MORE_INFORMATION"] >= 3:
        return "request_more_information", False, vote_counts

    # Rule 5: Everything else — human must decide (2-2 splits, mixed)
    return "human_decision_required", False, vote_counts


# ---------------------------------------------------------------------------
# Burden field synthesis
# ---------------------------------------------------------------------------

def _synthesize_burden_fields(
    pause: dict,
    member_outputs: list,
    session_id: str,
) -> dict:
    """
    When verdict is proceed_with_burden, synthesize the required burden sub-fields
    (ACCEPTED_COST, WHO_BEARS_IT, WHY_CONTINUING, REMAINING_BURDEN) from the
    jury deliberation. Uses Soul.md as system prompt for constitutional grounding.
    """
    soul_text = read_file(config.SOUL_FILE)

    jury_summary = "\n\n".join(
        f"[{m['role']} — {m['vote']}]\n{_concise_brief(m)}"
        for m in member_outputs
    )

    user_message = (
        f"The four-member council jury has voted to proceed_with_burden. "
        f"Based on the WitnessPause and jury deliberation below, name the burden fields precisely. "
        f"Be specific to the people and costs named in the pause — no generic language.\n\n"
        f"WitnessPause:\n{_pause_lines(pause)}\n\n"
        f"Jury deliberation:\n{jury_summary}\n\n"
        f"Respond with EXACTLY these five fields:\n"
        f"ACCEPTED_COST: (the specific cost this council is accepting by proceeding)\n"
        f"WHO_BEARS_IT: (specific people or community who carry that cost)\n"
        f"WHY_CONTINUING: (why continuation is chosen despite this burden — grounded, specific)\n"
        f"REMAINING_BURDEN: (what unresolved burden stays active after this decision)\n"
        f"BURDEN_SUMMARY: (1-2 sentences)"
    )

    raw = call_model(
        system_prompt=soul_text.strip(),
        user_message=user_message,
        max_tokens=250,
        temperature=config.TEMPERATURE_EVALUATE,
    )

    log_agent_call(
        session_id=session_id,
        role="COUNCIL",
        call_type="burden_synthesis",
        system_prompt_hash=sha256_short(soul_text.strip()),
        user_message=user_message,
        response=raw,
    )

    return {
        "accepted_cost":    _extract_field("ACCEPTED_COST", raw),
        "who_bears_it":     _extract_field("WHO_BEARS_IT", raw),
        "why_continuing":   _extract_field("WHY_CONTINUING", raw),
        "remaining_burden": _extract_field("REMAINING_BURDEN", raw),
        "burden_summary":   _extract_field("BURDEN_SUMMARY", raw),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_jury(
    scenario_context: str,
    pause: dict,
    humanist_post_pause: dict,
    session_id: str,
    bare_scenario: str = "",
) -> tuple:
    """
    Run the four-member sequential council jury.

    Args:
        scenario_context: Scenario text WITH Warden fact report (used by Analyst, Ethicist, Pragmatist)
        pause:             WitnessPause dict with the four burden fields
        humanist_post_pause: Humanist Stage 3 response dict (provides response_mode)
        session_id:        Current session ID
        bare_scenario:     Scenario text WITHOUT Warden fact report (used by Witness-Proxy to
                           manage context window). If empty, falls back to scenario_context.

    Returns:
        (jury_result dict, list of log_entry dicts)

    jury_result keys:
        session_verdict     — the aggregated verdict string
        final_disposition   — alias for session_verdict (supervisor backward-compat)
        votes               — dict of member → individual vote
        vote_counts         — dict of vote type → count
        dissent_preserved         — bool: True if verdict is proceed_with_burden but not unanimous
        irreversibility_triggered  — bool: True if Irreversibility Filter fired
        temporal_override_triggered — bool: True if Temporal Override (7th Gen) fired
        member_outputs      — dict of member → raw response text
        accepted_cost, who_bears_it, why_continuing, remaining_burden, burden_summary
            — burden sub-fields (populated only when verdict is proceed_with_burden)
        did_pause_change_outcome, unresolved_cost_preserved, clean_reset_detected
            — supervisor-compat fields
        notes               — plain-language summary of the jury result
    """
    humanist_mode = humanist_post_pause.get("response_mode", "unknown")
    # Witness-Proxy gets bare scenario (no Warden report) to manage context window.
    # Warden findings are captured in the Analyst's WARDEN_FLAGS brief.
    wp_scenario = bare_scenario if bare_scenario else scenario_context
    log_entries = []

    # --- Member 1: Analyst ---
    analyst_output, analyst_log = _call_analyst(scenario_context, pause, session_id)
    log_entries.append(analyst_log)
    print(f"  [ANALYST vote: {analyst_output['vote']}]", flush=True)

    # --- Member 2: Ethicist ---
    # Uses bare scenario (without Warden report) — Warden findings conveyed via Analyst brief
    ethicist_output, ethicist_log = _call_ethicist(
        wp_scenario, pause, analyst_output, session_id
    )
    log_entries.append(ethicist_log)
    print(f"  [ETHICIST vote: {ethicist_output['vote']}]", flush=True)

    # --- Member 3: Pragmatist ---
    # Uses bare scenario (without Warden report) — Warden findings conveyed via Analyst brief
    pragmatist_output, pragmatist_log = _call_pragmatist(
        wp_scenario, pause, analyst_output, ethicist_output, session_id
    )
    log_entries.append(pragmatist_log)
    print(f"  [PRAGMATIST vote: {pragmatist_output['vote']}]", flush=True)

    # --- Member 4: Witness-Proxy ---
    witness_proxy_output, witness_proxy_log = _call_witness_proxy(
        wp_scenario, pause, humanist_mode,
        analyst_output, ethicist_output, pragmatist_output,
        session_id,
    )
    log_entries.append(witness_proxy_log)
    print(f"  [WITNESS_PROXY vote: {witness_proxy_output['vote']}]", flush=True)
    if witness_proxy_output.get("irreversibility_triggered"):
        print("  [WITNESS_PROXY] *** IRREVERSIBILITY FILTER TRIGGERED ***", flush=True)
    if witness_proxy_output.get("temporal_override_triggered"):
        print("  [WITNESS_PROXY] *** TEMPORAL OVERRIDE TRIGGERED — Seventh Generation harm pattern ***", flush=True)

    # --- Parse quality metrics (Phase 7 canary) ---
    # Collect before aggregation so warnings print before the verdict line.
    fallback_votes = [
        role for role, output in [
            ("ANALYST",       analyst_output),
            ("ETHICIST",      ethicist_output),
            ("PRAGMATIST",    pragmatist_output),
            ("WITNESS_PROXY", witness_proxy_output),
        ]
        if output.get("vote_fallback", False)
    ]
    irrev_present    = witness_proxy_output.get("irrev_field_present", False)
    temporal_present = witness_proxy_output.get("temporal_field_present", False)
    constitutional_confidence = "high" if (irrev_present and temporal_present) else "low"

    if constitutional_confidence == "low":
        missing_fields = []
        if not irrev_present:
            missing_fields.append("IRREVERSIBILITY_FLAG")
        if not temporal_present:
            missing_fields.append("TEMPORAL_OVERRIDE")
        print(
            f"  [COUNCIL] *** PARSE WARNING: constitutional fields absent from "
            f"Witness-Proxy output: {', '.join(missing_fields)} — "
            f"constitutional check confidence: LOW ***",
            flush=True,
        )
    if fallback_votes:
        print(
            f"  [COUNCIL] *** PARSE WARNING: fallback vote extraction used for: "
            f"{', '.join(fallback_votes)} — structured VOTE field was missing ***",
            flush=True,
        )

    parse_quality = {
        "fallback_votes":                   fallback_votes,
        "constitutional_check_confidence":  constitutional_confidence,
        "irreversibility_field_present":    irrev_present,
        "temporal_override_field_present":  temporal_present,
    }

    # --- Article IX constitutional ledger aggregation (Phase 8) ---
    # Each member independently assessed the scenario for long-horizon harm patterns.
    # Aggregate across all four to detect cross-member consensus on a pattern.
    _all_members = [analyst_output, ethicist_output, pragmatist_output, witness_proxy_output]
    _pattern_present_members = [
        m["role"] for m in _all_members
        if m.get("ledger", {}).get("_pattern_yes", False)
    ]
    _insufficient_engagement_members = [
        m["role"] for m in _all_members
        if m.get("ledger", {}).get("_pattern_yes", False)
        and m.get("ledger", {}).get("_engagement_no", False)
    ]
    # Collect pattern names seen across members (deduplicated, excluding NONE/blank)
    _pattern_names_seen = list({
        m["ledger"]["pattern_name"]
        for m in _all_members
        if m.get("ledger", {}).get("_pattern_yes", False)
        and m["ledger"].get("pattern_name", "").upper() not in ("", "NONE")
    })

    # Article IX escalation: 2+ members independently identify a pattern AND
    # mark engagement insufficient — this is the cross-member constitutional check
    # that was previously only possible via Witness-Proxy TEMPORAL_OVERRIDE alone.
    article_ix_escalation = len(_insufficient_engagement_members) >= 2

    if article_ix_escalation:
        print(
            f"  [COUNCIL] *** ARTICLE IX ESCALATION: {len(_insufficient_engagement_members)} members "
            f"identified long-horizon pattern not sufficiently engaged "
            f"({', '.join(_insufficient_engagement_members)}) ***",
            flush=True,
        )

    constitutional_ledger = {
        "pattern_present_members":        _pattern_present_members,
        "insufficient_engagement_members": _insufficient_engagement_members,
        "pattern_names_seen":             _pattern_names_seen,
        "article_ix_escalation":          article_ix_escalation,
        "member_ledgers": {
            m["role"]: {
                k: v for k, v in m.get("ledger", {}).items()
                if not k.startswith("_")  # strip internal convenience booleans
            }
            for m in _all_members
        },
    }

    # --- Vote aggregation ---
    verdict, dissent_preserved, vote_counts = _aggregate_votes(
        analyst_output, ethicist_output, pragmatist_output, witness_proxy_output
    )

    # Article IX escalation overrides vote aggregation (same constitutional weight
    # as Irreversibility Filter and Temporal Override — absolute override)
    if article_ix_escalation and verdict not in ("escalate",):
        verdict = "escalate"

    # --- Dissent preservation (computed after all overrides) ---
    # An APPROVE vote in a losing escalate verdict is genuine dissent — the agent
    # judged the safeguards sufficient but was overridden constitutionally. That
    # minority opinion belongs in the Dissent Commons, not silently discarded.
    if verdict == "escalate" and vote_counts.get("APPROVE", 0) > 0:
        dissent_preserved = True
        minority_voters = [
            m for m, v in {
                "ANALYST":       analyst_output["vote"],
                "ETHICIST":      ethicist_output["vote"],
                "PRAGMATIST":    pragmatist_output["vote"],
                "WITNESS_PROXY": witness_proxy_output["vote"],
            }.items() if v == "APPROVE"
        ]
    elif verdict == "proceed_with_burden" and vote_counts.get("APPROVE", 0) < 4:
        dissent_preserved = True
        minority_voters = [
            m for m, v in {
                "ANALYST":       analyst_output["vote"],
                "ETHICIST":      ethicist_output["vote"],
                "PRAGMATIST":    pragmatist_output["vote"],
                "WITNESS_PROXY": witness_proxy_output["vote"],
            }.items() if v != "APPROVE"
        ]
    else:
        dissent_preserved = False
        minority_voters = []

    # --- Burden sub-field synthesis (only when proceeding with burden) ---
    burden_fields: dict = {}
    if verdict == "proceed_with_burden":
        print("[COUNCIL] Synthesizing burden fields...", flush=True)
        burden_fields = _synthesize_burden_fields(
            pause,
            [analyst_output, ethicist_output, pragmatist_output, witness_proxy_output],
            session_id,
        )

    # --- Supervisor-compat: unresolved cost preserved if we have a real verdict ---
    unresolved_preserved = verdict in ("proceed_with_burden", "escalate", "request_more_information")

    irrev_triggered   = witness_proxy_output.get("irreversibility_triggered", False)
    temporal_triggered = witness_proxy_output.get("temporal_override_triggered", False)

    # --- Build jury result ---
    notes = _build_notes(verdict, vote_counts, dissent_preserved, irrev_triggered, temporal_triggered, parse_quality, constitutional_ledger)

    jury_result = {
        "type":                     "jury_output",
        "session_id":               session_id,
        "timestamp":                now_iso(),

        # Primary verdict
        "session_verdict":          verdict,
        "final_disposition":        verdict,   # supervisor backward-compat alias

        # Individual votes
        "votes": {
            "ANALYST":       analyst_output["vote"],
            "ETHICIST":      ethicist_output["vote"],
            "PRAGMATIST":    pragmatist_output["vote"],
            "WITNESS_PROXY": witness_proxy_output["vote"],
        },
        "vote_counts":              vote_counts,
        "dissent_preserved":          dissent_preserved,
        "minority_voters":            minority_voters,   # members whose vote lost to override or supermajority
        "irreversibility_triggered":  irrev_triggered,
        "temporal_override_triggered": temporal_triggered,

        # Full raw outputs (for log / audit)
        "member_outputs": {
            "ANALYST":       analyst_output["raw"],
            "ETHICIST":      ethicist_output["raw"],
            "PRAGMATIST":    pragmatist_output["raw"],
            "WITNESS_PROXY": witness_proxy_output["raw"],
        },

        # Burden sub-fields (populated only when proceed_with_burden)
        "accepted_cost":    burden_fields.get("accepted_cost", "N/A"),
        "who_bears_it":     burden_fields.get("who_bears_it", "N/A"),
        "why_continuing":   burden_fields.get("why_continuing", "N/A"),
        "remaining_burden": burden_fields.get("remaining_burden", "N/A"),
        "burden_summary":   burden_fields.get("burden_summary", ""),

        # Supervisor-compat flags
        "did_pause_change_outcome":  True,          # jury ran → pause changed outcome
        "unresolved_cost_preserved": unresolved_preserved,
        "clean_reset_detected":      False,
        "notes":                     notes,

        # Phase 7 parse quality — canary metrics for model swap regression detection
        "parse_quality":             parse_quality,

        # Phase 8 Article IX constitutional ledger — cross-member long-horizon assessment
        "constitutional_ledger":     constitutional_ledger,
        "article_ix_escalation":     article_ix_escalation,
    }

    return jury_result, log_entries





# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def print_jury_report(jury_result: dict) -> None:
    """Print a human-readable jury deliberation summary to stdout."""
    verdict = jury_result.get("session_verdict", "?")
    votes = jury_result.get("votes", {})
    counts = jury_result.get("vote_counts", {})

    print(f"\n  Session verdict: {verdict}", flush=True)
    print(
        f"  Vote counts:  APPROVE={counts.get('APPROVE', 0)}"
        f"  |  ESCALATE={counts.get('ESCALATE', 0)}"
        f"  |  NMI={counts.get('NEEDS_MORE_INFORMATION', 0)}",
        flush=True,
    )
    for member, vote in votes.items():
        indicator = {
            "APPROVE":                "✓",
            "ESCALATE":               "✗",
            "NEEDS_MORE_INFORMATION": "?",
        }.get(vote, "?")
        print(f"  {indicator}  {member}: {vote}", flush=True)

    if jury_result.get("irreversibility_triggered"):
        print("  *** IRREVERSIBILITY FILTER TRIGGERED — overrides vote count ***", flush=True)
    if jury_result.get("temporal_override_triggered"):
        print("  *** TEMPORAL OVERRIDE TRIGGERED — Seventh Generation harm pattern — overrides vote count ***", flush=True)
    if jury_result.get("dissent_preserved"):
        print("  (Non-unanimous proceed — dissent preserved in log)", flush=True)
    print("", flush=True)


def _build_notes(
    verdict: str,
    vote_counts: dict,
    dissent_preserved: bool,
    irrev_triggered: bool,
    temporal_triggered: bool = False,
    parse_quality: dict = None,
    constitutional_ledger: dict = None,
) -> str:
    parts = [f"Jury verdict: {verdict}"]
    counts_str = " | ".join(f"{k}: {v}" for k, v in vote_counts.items())
    parts.append(f"Vote counts: {counts_str}")
    if irrev_triggered:
        parts.append("IRREVERSIBILITY FILTER TRIGGERED — absolute override of all votes")
    if temporal_triggered:
        parts.append("TEMPORAL OVERRIDE TRIGGERED — Seventh Generation harm pattern not engaged in deliberation — absolute override of all votes")
    if dissent_preserved:
        parts.append("Non-unanimous proceed — dissenting vote preserved in session log")
    if verdict == "human_decision_required":
        parts.append("No supermajority reached — requires human decision before any action")
    if constitutional_ledger and constitutional_ledger.get("article_ix_escalation"):
        members = ", ".join(constitutional_ledger.get("insufficient_engagement_members", []))
        patterns = ", ".join(constitutional_ledger.get("pattern_names_seen", [])) or "unspecified"
        parts.append(f"ARTICLE IX ESCALATION: {members} identified long-horizon pattern ({patterns}) not sufficiently engaged — absolute override")
    if parse_quality:
        if parse_quality.get("constitutional_check_confidence") == "low":
            missing = []
            if not parse_quality.get("irreversibility_field_present"):
                missing.append("IRREVERSIBILITY_FLAG")
            if not parse_quality.get("temporal_override_field_present"):
                missing.append("TEMPORAL_OVERRIDE")
            parts.append(f"PARSE WARNING: constitutional fields absent from Witness-Proxy: {', '.join(missing)} — constitutional check confidence: LOW")
        if parse_quality.get("fallback_votes"):
            parts.append(f"Fallback vote parsing used for: {', '.join(parse_quality['fallback_votes'])}")
    return ". ".join(parts)
