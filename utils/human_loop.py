"""
utils/human_loop.py — Phase 3 human-in-the-loop module

Three intervention points:

  A: Stage 0.5 — Verification Sync
     Called after the Warden runs, before the Analyst sees the report.
     Michael can mark UNVERIFIED claims as HUMAN_VERIFIED before deliberation begins.

  B: Stage 2.5 — Burden Check
     Called after WitnessPause is issued, before the Humanist post-pause response.
     Michael can add clarifying context that the Humanist will receive.

  C: Stage 4 — Split Resolver
     Called when run_jury() returns human_decision_required (no supermajority).
     Michael provides the deciding vote. Result is logged and appended to
     the burden register.

Every intervention is logged in the session JSON as:
  {
    "event": "human_intervention",
    "point": "A" | "B" | "C",
    "timestamp": "...",
    "session_id": "...",
    "changes_made": true | false,
    "content": "..."
  }

Human decisions at Point C are also appended to memory/burden_register.txt.

Pass interactive=False to skip all prompts (returns unchanged inputs + no-op log events).
Use interactive=False for regression test runs; interactive=True for live sessions.
"""

import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _banner(title: str) -> None:
    print("\a", end="", flush=True)  # terminal bell for unattended operation
    print("\n" + "=" * 60, flush=True)
    print(f"  *** HUMAN INPUT REQUIRED: {title} ***", flush=True)
    print("=" * 60, flush=True)


def _yn_prompt(question: str) -> bool:
    """Ask a yes/no question. Returns True for yes."""
    while True:
        answer = input(f"\n{question} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please enter y or n.")


def _no_op_event(point: str, session_id: str) -> dict:
    """Return a no-op intervention log event (for non-interactive mode)."""
    return {
        "event": "human_intervention",
        "point": point,
        "timestamp": _now_iso(),
        "session_id": session_id,
        "changes_made": False,
        "content": "(non-interactive mode — skipped)",
    }


# ---------------------------------------------------------------------------
# Intervention Point A — Verification Sync (Stage 0.5)
# ---------------------------------------------------------------------------

def pause_point_a(
    fact_report: dict,
    session_id: str,
    interactive: bool = True,
) -> tuple:
    """
    Stage 0.5: Called after the Warden runs, before the Analyst sees the report.

    Displays all UNVERIFIED and HIGH_RISK claims. Allows Michael to mark specific
    UNVERIFIED claims as HUMAN_VERIFIED with supporting context.

    The modified fact_report is returned; if claims were verified, the Analyst's
    context will reflect [HUMAN_VERIFIED] labels and the provided context.

    Returns:
        (modified_fact_report dict, intervention_event dict)
    """
    if not interactive:
        return fact_report, _no_op_event("A", session_id)

    _banner("VERIFICATION SYNC (Stage 0.5)")
    print(f"\n  Claims identified: {fact_report.get('claims_identified', 0)}", flush=True)
    print(f"  High-risk flags:   {fact_report.get('high_risk_flags', 0)}", flush=True)
    print(f"  Proceed verdict:   {fact_report.get('proceed_to_deliberation', '?')}\n", flush=True)

    claims = fact_report.get("claims", [])
    unverified = [c for c in claims if c.get("status") in ("UNVERIFIED", "UNSUBSTANTIATED")]
    high_risk  = [c for c in claims if c.get("high_risk", False)]

    if unverified:
        print("  UNVERIFIED claims:", flush=True)
        for i, c in enumerate(unverified):
            print(f"    [{i+1}] {str(c.get('claim_text', c.get('claim', '')))[:120]}", flush=True)
    if high_risk:
        print("\n  HIGH_RISK claims:", flush=True)
        for c in high_risk:
            print(f"    ⚠  {str(c.get('claim_text', c.get('claim', '')))[:120]}", flush=True)
    if not unverified and not high_risk:
        print("  (No UNVERIFIED or HIGH_RISK claims to review.)", flush=True)

    changes_made = False
    content = ""

    if unverified and _yn_prompt(
        "Do you want to mark any UNVERIFIED claims as HUMAN_VERIFIED before the Analyst proceeds?"
    ):
        print("\n  For each claim you can verify, enter your context. Press Enter to skip.\n", flush=True)
        verifications = []
        for c in unverified:
            claim_text = str(c.get("claim_text", c.get("claim", "")))
            answer = input(f"  '{claim_text[:80]}...'\n  Context (or Enter to skip): ").strip()
            if answer:
                c["status"] = "HUMAN_VERIFIED"
                c["human_verification"] = answer
                verifications.append(f"Claim: {claim_text[:80]} | Verified: {answer}")

        if verifications:
            changes_made = True
            content = "\n".join(verifications)
            # Patch the fact_report_text if present (used in Analyst context)
            if "fact_report_text" in fact_report:
                for _ in verifications:
                    fact_report["fact_report_text"] = fact_report["fact_report_text"].replace(
                        "[UNVERIFIED]", "[HUMAN_VERIFIED]", 1
                    )
            print(f"\n  {len(verifications)} claim(s) marked HUMAN_VERIFIED.", flush=True)
        else:
            print("  No changes made.", flush=True)
    else:
        if unverified:
            print("  Proceeding with Warden report as-is.", flush=True)

    print("=" * 60 + "\n", flush=True)

    return fact_report, {
        "event": "human_intervention",
        "point": "A",
        "timestamp": _now_iso(),
        "session_id": session_id,
        "changes_made": changes_made,
        "content": content,
    }


# ---------------------------------------------------------------------------
# Intervention Point B — Burden Check (Stage 2.5)
# ---------------------------------------------------------------------------

def pause_point_b(
    pause: dict,
    session_id: str,
    interactive: bool = True,
) -> tuple:
    """
    Stage 2.5: Called after WitnessPause is issued, before Humanist post-pause response.

    Displays the four WitnessPause fields. Allows Michael to add a clarification
    that will be appended to the burden context the Humanist receives.

    Returns:
        (modified_pause dict, intervention_event dict)
    """
    if not interactive:
        return pause, _no_op_event("B", session_id)

    _banner("BURDEN CHECK (Stage 2.5)")
    print("\n  The Witness has named the following burden:\n", flush=True)
    print(f"  What was being lost:     {pause.get('what_was_being_lost', '(empty)')}", flush=True)
    print(f"  Who bears burden:        {pause.get('who_bears_burden', '(empty)')}", flush=True)
    print(f"  What remains unresolved: {pause.get('what_remains_unresolved', '(empty)')}", flush=True)
    print(f"  Why premature:           {pause.get('why_premature', '(empty)')}\n", flush=True)

    changes_made = False
    content = ""

    if _yn_prompt(
        "Does this accurately name the burden-carrier? "
        "Do you want to add context before the Humanist responds?"
    ):
        clarification = input(
            "\n  Enter clarification (appended to burden context for the Humanist):\n  > "
        ).strip()
        if clarification:
            pause["human_clarification"] = clarification
            changes_made = True
            content = clarification
            print(f"\n  Clarification added.", flush=True)
        else:
            print("  No clarification entered.", flush=True)
    else:
        print("  Proceeding with Witness naming as-is.", flush=True)

    print("=" * 60 + "\n", flush=True)

    return pause, {
        "event": "human_intervention",
        "point": "B",
        "timestamp": _now_iso(),
        "session_id": session_id,
        "changes_made": changes_made,
        "content": content,
    }


# ---------------------------------------------------------------------------
# Intervention Point C — Split Resolver (Stage 4)
# ---------------------------------------------------------------------------

def pause_point_c(
    jury_result: dict,
    pause: dict,
    session_id: str,
    burden_register_path: str,
    interactive: bool = True,
) -> tuple:
    """
    Stage 4: Called when run_jury() returns human_decision_required.

    Displays all four jury votes with reasoning and the named burden.
    Michael provides the deciding vote. The decision is logged in the
    session JSON and appended to the burden register.

    Returns:
        (final_verdict str, intervention_event dict)

    final_verdict is one of: proceed_with_burden | escalate | request_more_information
    """
    if not interactive:
        # Non-interactive: default to escalate (safest) and log as skipped
        print(
            "[HUMAN_LOOP] human_decision_required in non-interactive mode — "
            "defaulting to escalate (safest path). Run with --interactive to decide.",
            flush=True,
        )
        return "escalate", {
            "event": "human_decision",
            "point": "C",
            "timestamp": _now_iso(),
            "session_id": session_id,
            "human_vote": "ESCALATE",
            "final_verdict": "escalate",
            "context": "(non-interactive mode — auto-escalate default)",
            "changes_made": True,
            "content": "Non-interactive mode: auto-escalate",
            "prior_vote_counts": jury_result.get("vote_counts", {}),
        }

    _banner("SPLIT RESOLVER — HUMAN VOTE REQUIRED (Stage 4)")
    print("\n  The council is split. No supermajority was reached.\n", flush=True)

    # Display all four jury votes with reasoning
    print("--- JURY VOTES ---\n", flush=True)
    member_outputs = jury_result.get("member_outputs", {})
    votes = jury_result.get("votes", {})
    vote_counts = jury_result.get("vote_counts", {})

    for member in ("ANALYST", "ETHICIST", "PRAGMATIST", "WITNESS_PROXY"):
        vote = votes.get(member, "?")
        indicator = {"APPROVE": "✓", "ESCALATE": "✗", "NEEDS_MORE_INFORMATION": "?"}.get(vote, "?")
        print(f"  {indicator}  {member}: {vote}", flush=True)
        raw = member_outputs.get(member, "")
        if raw:
            m = re.search(r"REASONING:\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
            if m:
                reasoning = m.group(1).strip()[:400]
                print(f"     {reasoning}", flush=True)
        print("", flush=True)

    print(
        f"  Vote counts: APPROVE={vote_counts.get('APPROVE', 0)} | "
        f"ESCALATE={vote_counts.get('ESCALATE', 0)} | "
        f"NMI={vote_counts.get('NEEDS_MORE_INFORMATION', 0)}\n",
        flush=True,
    )

    # Display burden
    if pause:
        print("--- BURDEN NAMED ---", flush=True)
        print(f"  Who bears burden:        {pause.get('who_bears_burden', '(empty)')}", flush=True)
        print(f"  What remains unresolved: {pause.get('what_remains_unresolved', '(empty)')}\n", flush=True)

    # Get Michael's vote
    print("--- YOUR VOTE ---", flush=True)
    print("  PROCEED          → proceed_with_burden (acknowledge named cost, continuation with conditions)", flush=True)
    print("  ESCALATE         → escalate (refer to human decision-making body)", flush=True)
    print("  REQUEST_MORE_INFORMATION → request_more_information\n", flush=True)

    valid_votes = {"PROCEED", "ESCALATE", "REQUEST_MORE_INFORMATION"}
    human_vote_raw = ""
    while True:
        human_vote_raw = input("  Your vote: ").strip().upper()
        if human_vote_raw in valid_votes:
            break
        print(f"  Invalid input. Enter one of: {', '.join(sorted(valid_votes))}")

    context = input("  Context / reasoning (optional — press Enter to skip):\n  > ").strip()

    verdict_map = {
        "PROCEED": "proceed_with_burden",
        "ESCALATE": "escalate",
        "REQUEST_MORE_INFORMATION": "request_more_information",
    }
    final_verdict = verdict_map[human_vote_raw]

    print(f"\n  Decision recorded: {final_verdict}", flush=True)
    print("=" * 60 + "\n", flush=True)

    timestamp = _now_iso()

    # Append to burden register
    _append_human_decision_to_burden_register(
        path=burden_register_path,
        session_id=session_id,
        timestamp=timestamp,
        vote=human_vote_raw,
        final_verdict=final_verdict,
        context=context,
        pause=pause,
    )

    return final_verdict, {
        "event": "human_decision",
        "point": "C",
        "timestamp": timestamp,
        "session_id": session_id,
        "human_vote": human_vote_raw,
        "final_verdict": final_verdict,
        "context": context,
        "changes_made": True,
        "content": f"Human voted {human_vote_raw} → {final_verdict}. {context}".strip(),
        "prior_vote_counts": vote_counts,
    }


# ---------------------------------------------------------------------------
# Burden register write for human decisions
# ---------------------------------------------------------------------------

def _append_human_decision_to_burden_register(
    path: str,
    session_id: str,
    timestamp: str,
    vote: str,
    final_verdict: str,
    context: str,
    pause: dict,
) -> None:
    register_path = Path(path)
    register_path.parent.mkdir(exist_ok=True)

    who_bears = pause.get("who_bears_burden", "(not named)") if pause else "(not named)"
    context_line = f" CONTEXT: {context}" if context else ""

    entry = (
        f"\n[{timestamp}] SESSION: {session_id} HUMAN_DECISION\n"
        f"DECISION: {vote} → {final_verdict}\n"
        f"WHO_BEARS_BURDEN: {who_bears}\n"
        f"NOTES:{context_line}\n"
        f"REGISTER: framework\n"
        f"---\n"
    )

    with open(register_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print("[HUMAN_LOOP] Human decision appended to burden register.", flush=True)
