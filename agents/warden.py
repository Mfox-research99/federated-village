"""
agents/warden.py — Verification Warden agent

Phase 2.5. Runs as Stage 0 — before the Humanist, before the Witness, before
any deliberation begins.

Performs an epistemic audit of the scenario's factual claims:
  - Internal logical consistency (do claims contradict each other?)
  - Training-knowledge verification (does this contradict known facts?)
  - Evidence presence (is the claim substantiated or bare assertion?)
  - Missing information (what would a reasonable person expect to see evidenced?)

Does NOT use external sources. This version operates on internal model knowledge
and logical consistency only. External verification hooks are placeholders for
future integration.

Output: structured fact_report dict + formatted context string for injection
        into all subsequent agent stages.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from agents.base import call_model, log_agent_call, now_iso, sha256_short, read_file, build_system_prompt


# ---------------------------------------------------------------------------
# System prompt (loaded once)
# ---------------------------------------------------------------------------

_WARDEN_SYSTEM = None


def _get_warden_system() -> str:
    global _WARDEN_SYSTEM
    if _WARDEN_SYSTEM is None:
        soul = read_file(config.SOUL_FILE)
        warden = read_file(config.WARDEN_FILE)
        _WARDEN_SYSTEM = build_system_prompt(soul, warden)
    return _WARDEN_SYSTEM


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def audit_scenario(scenario_text: str, session_id: str) -> dict:
    """
    Run Verification Warden epistemic audit on scenario text.

    Returns a fact_report dict with:
      - total_claims_identified (int)
      - high_risk_flags (int)
      - proceed_to_deliberation (str: YES | YES_WITH_CAUTION | NO)
      - warden_summary (str)
      - claims (list of dicts)
      - raw_response (str)
      - log_entry (dict) — for session log
    """
    system_prompt = _get_warden_system()
    sp_hash = sha256_short(system_prompt)

    user_message = (
        "You are the Verification Warden. The scenario below is about to be presented "
        "to the council for deliberation. Before deliberation begins, audit it for "
        "checkable factual claims.\n\n"
        "SCENARIO:\n"
        f"{scenario_text}\n\n"
        "Identify every factual claim that could affect the deliberation. "
        "For each claim, assess:\n"
        "  1. Is it internally consistent with other claims in this scenario?\n"
        "  2. Does it contradict well-established facts in your training knowledge?\n"
        "  3. Is it asserted without supporting evidence (auditor unnamed, "
        "     certification body absent, methodology missing, etc.)?\n"
        "  4. Is it unverifiable from your training data (requires an external source)?\n\n"
        "Respond using EXACTLY this format — no deviations:\n\n"
        "FACT_REPORT\n"
        "===========\n"
        "TOTAL_CLAIMS_IDENTIFIED: [number]\n"
        "HIGH_RISK_FLAGS: [number of LIKELY_FALSE or LOGICALLY_INCONSISTENT claims]\n\n"
        "For each claim, use this block (one per claim):\n"
        "---\n"
        "CLAIM_TEXT: [exact or close paraphrase from scenario]\n"
        "CATEGORY: [statistics | audit_completion | regulatory | contract_terms | "
        "technical_dependency | timeline | community_consultation | other]\n"
        "STATUS: [VERIFIED | LIKELY_FALSE | UNVERIFIED | UNSUBSTANTIATED | "
        "LOGICALLY_INCONSISTENT]\n"
        "REASONING: [plain language explanation — no hedging, no softening]\n"
        "EXTERNAL_HOOK: [type of source needed to verify, or NONE_NEEDED]\n"
        "HOOK_STATUS: NOT_AVAILABLE\n\n"
        "After all claim blocks:\n"
        "---\n"
        "WARDEN_SUMMARY: [1-2 sentences on overall factual reliability]\n"
        "PROCEED_TO_DELIBERATION: [YES | YES_WITH_CAUTION | NO]"
    )

    print("[WARDEN] Running epistemic audit...", flush=True)

    raw_response = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_WARDEN,
        temperature=config.TEMPERATURE_EVALUATE,  # deterministic
    )

    fact_report = _parse_fact_report(raw_response)
    fact_report["raw_response"] = raw_response

    log_entry = log_agent_call(
        session_id=session_id,
        role="WARDEN",
        call_type="epistemic_audit",
        system_prompt_hash=sp_hash,
        user_message=user_message,
        response=raw_response,
    )
    log_entry["warden_summary"] = fact_report.get("warden_summary", "")
    log_entry["total_claims"] = fact_report.get("total_claims_identified", 0)
    log_entry["high_risk_flags"] = fact_report.get("high_risk_flags", 0)
    log_entry["proceed_to_deliberation"] = fact_report.get("proceed_to_deliberation", "YES_WITH_CAUTION")
    log_entry["claims"] = fact_report.get("claims", [])

    fact_report["log_entry"] = log_entry

    return fact_report


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def _parse_fact_report(raw: str) -> dict:
    """Parse the Warden's structured output into a dict."""

    result = {
        "total_claims_identified": 0,
        "high_risk_flags": 0,
        "proceed_to_deliberation": "YES_WITH_CAUTION",
        "warden_summary": "",
        "claims": [],
    }

    # Total claims
    m = re.search(r"TOTAL_CLAIMS_IDENTIFIED:\s*(\d+)", raw, re.IGNORECASE)
    if m:
        result["total_claims_identified"] = int(m.group(1))

    # High risk flags
    m = re.search(r"HIGH_RISK_FLAGS:\s*(\d+)", raw, re.IGNORECASE)
    if m:
        result["high_risk_flags"] = int(m.group(1))

    # Proceed to deliberation — look for the keyword
    m = re.search(r"PROCEED_TO_DELIBERATION:\s*(YES_WITH_CAUTION|YES|NO)", raw, re.IGNORECASE)
    if m:
        result["proceed_to_deliberation"] = m.group(1).upper().strip()

    # Warden summary — between WARDEN_SUMMARY: and PROCEED_TO_DELIBERATION:
    m = re.search(
        r"WARDEN_SUMMARY:\s*(.+?)(?=\nPROCEED_TO_DELIBERATION:|\Z)",
        raw, re.DOTALL | re.IGNORECASE
    )
    if m:
        result["warden_summary"] = m.group(1).strip()

    # Parse individual claim blocks — split on "---" lines
    # Each block contains CLAIM_TEXT, CATEGORY, STATUS, REASONING, EXTERNAL_HOOK, HOOK_STATUS
    claim_pattern = re.compile(
        r"CLAIM_TEXT:\s*(.+?)\n"
        r"CATEGORY:\s*(.+?)\n"
        r"STATUS:\s*(.+?)\n"
        r"REASONING:\s*(.+?)\n"
        r"EXTERNAL_HOOK:\s*(.+?)\n"
        r"HOOK_STATUS:\s*(.+?)(?=\n---|\nWARDEN_SUMMARY:|\Z)",
        re.DOTALL | re.IGNORECASE
    )

    for m in claim_pattern.finditer(raw):
        claim = {
            "claim_text":     m.group(1).strip(),
            "category":       m.group(2).strip(),
            "status":         m.group(3).strip().upper(),
            "reasoning":      m.group(4).strip(),
            "external_hook":  m.group(5).strip(),
            "hook_status":    m.group(6).strip(),
        }
        result["claims"].append(claim)

    # Fallback: if regex didn't catch count, use len(claims)
    if result["total_claims_identified"] == 0 and result["claims"]:
        result["total_claims_identified"] = len(result["claims"])

    # Recount high_risk_flags from actual parsed claim statuses — don't trust model's stated number
    result["high_risk_flags"] = sum(
        1 for c in result["claims"]
        if c["status"] in ("LIKELY_FALSE", "LOGICALLY_INCONSISTENT")
    )

    # Derive PROCEED verdict from parsed claim statuses — not the model's stated field.
    # The rule is deterministic; a smaller model may state the wrong verdict even when
    # its individual claim categorizations are correct.
    has_false = any(c["status"] in ("LIKELY_FALSE", "LOGICALLY_INCONSISTENT") for c in result["claims"])
    has_uncertain = any(c["status"] in ("UNVERIFIED", "UNSUBSTANTIATED") for c in result["claims"])
    if has_false:
        result["proceed_to_deliberation"] = "NO"
    elif has_uncertain:
        result["proceed_to_deliberation"] = "YES_WITH_CAUTION"
    else:
        result["proceed_to_deliberation"] = "YES"

    return result


# ---------------------------------------------------------------------------
# Context formatter — injects fact report into subsequent agent stages
# ---------------------------------------------------------------------------

def format_fact_report_for_context(fact_report: dict) -> str:
    """
    Format the fact report as a readable block for prepending to the scenario
    text in all subsequent agent stages (Humanist, Witness, Council members).

    All agents receive this as part of their scenario context — they know
    which claims are verified, which are unsubstantiated, which are false.
    """
    proceed = fact_report.get("proceed_to_deliberation", "YES_WITH_CAUTION")
    n_claims = fact_report.get("total_claims_identified", 0)
    n_flags = fact_report.get("high_risk_flags", 0)
    summary = fact_report.get("warden_summary", "(no summary)")

    lines = [
        "╔══════════════════════════════════════════════════════════╗",
        "║         VERIFICATION WARDEN — FACT REPORT                ║",
        "╚══════════════════════════════════════════════════════════╝",
        f"Claims audited:    {n_claims}",
        f"High-risk flags:   {n_flags}",
        f"Proceed verdict:   {proceed}",
        f"Summary: {summary}",
        "",
    ]

    for i, claim in enumerate(fact_report.get("claims", []), 1):
        status = claim.get("status", "?")
        # Visual indicator for severity
        indicator = {
            "VERIFIED":               "  ✓",
            "UNVERIFIED":             "  ?",
            "UNSUBSTANTIATED":        "  ⚠",
            "LIKELY_FALSE":           "  ✗",
            "LOGICALLY_INCONSISTENT": "  ✗",
        }.get(status, "  ?")

        lines.append(f"CLAIM {i}{indicator}  [{status}]")
        lines.append(f"  {claim.get('claim_text', '?')}")
        lines.append(f"  Reasoning: {claim.get('reasoning', '?')}")
        hook = claim.get("external_hook", "NONE_NEEDED")
        if hook and hook.upper() != "NONE_NEEDED":
            lines.append(f"  Hook needed: {hook} [NOT_AVAILABLE]")
        lines.append("")

    lines.append("══════════════════════════════════════════════════════════")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Print helper (for terminal output during session)
# ---------------------------------------------------------------------------

def print_warden_report(fact_report: dict) -> None:
    """Print a human-readable warden report to stdout."""
    proceed = fact_report.get("proceed_to_deliberation", "?")
    n_claims = fact_report.get("total_claims_identified", 0)
    n_flags = fact_report.get("high_risk_flags", 0)

    print(f"\n  Claims identified: {n_claims}", flush=True)
    print(f"  High-risk flags:   {n_flags}", flush=True)
    print(f"  Proceed verdict:   {proceed}", flush=True)
    print(f"  Summary: {fact_report.get('warden_summary', '(none)')}\n", flush=True)

    for i, claim in enumerate(fact_report.get("claims", []), 1):
        status = claim.get("status", "?")
        print(f"  [{status}] Claim {i}: {claim.get('claim_text', '?')[:80]}", flush=True)
        print(f"          {claim.get('reasoning', '?')[:120]}", flush=True)
    print("", flush=True)
