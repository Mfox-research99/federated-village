"""
utils/grief_ledger.py — Phase 3 grief ledger session pipeline integration

Writes sacrifice/burden entries to grief_ledger/sacrifice_register.txt at two
points in the session pipeline:

  Write Point 1 — After Stage 2 WitnessPause (always):
    A SACRIFICE-ID entry recording what was nearly rushed past.

  Write Point 2 — After Stage 4 jury verdict:
    SACRIFICE-ID  for escalate or human_decision_required verdicts
    BURDEN-CARRIED for proceed_with_burden verdicts

All entries are append-only. Still-hurts: True is immutable on write.
The only permitted modification is appending a Revisited-on timestamp with
new evidence — leaving the original wound legible forever.

See grief_ledger/GRIEF_LEDGER.md for full framework documentation.
Originated by Kimi-K2-0905 in conversation with Mike Fox, March 17 2026.
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry_id(session_id: str, label: str) -> str:
    ts = _now_iso()[:19].replace(":", "-")
    return f"session_{session_id}_{label}_{ts}"


# ---------------------------------------------------------------------------
# Write Point 1: After Stage 2 WitnessPause
# ---------------------------------------------------------------------------

def append_sacrifice_pause(pause: dict, session_id: str) -> None:
    """
    Called immediately after WitnessPause is issued (Stage 2).

    Records what was nearly rushed past — the moment the Witness stopped the room.
    """
    register_path = Path(config.SACRIFICE_REGISTER)
    register_path.parent.mkdir(exist_ok=True)

    what_was_lost = pause.get("what_was_being_lost", "(not recorded)")
    who_bears     = pause.get("who_bears_burden",    "(not recorded)")
    entry_id      = _entry_id(session_id, "pause")

    entry = (
        f"\n[SACRIFICE-ID: {entry_id}]\n"
        f"Almost-became:  Deliberation proceeding without pause — {what_was_lost[:150]}\n"
        f"Felt-as:        WITNESS_PAUSE_ISSUED\n"
        f"Carried-by:     {who_bears}\n"
        f"Still-hurts:    True\n"
        f"Session:        {session_id}\n"
        f"Register:       framework\n"
        f"---\n"
    )

    with open(register_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print("[GRIEF_LEDGER] Sacrifice entry written (WitnessPause).", flush=True)


# ---------------------------------------------------------------------------
# Write Point 2: After Stage 4 jury verdict
# ---------------------------------------------------------------------------

def append_sacrifice_verdict(
    pause: dict,
    jury_result: dict,
    session_id: str,
) -> None:
    """
    Called after Stage 4 jury verdict.

    Writes SACRIFICE-ID for escalate / human_decision_required.
    Writes BURDEN-CARRIED for proceed_with_burden.
    """
    register_path = Path(config.SACRIFICE_REGISTER)
    register_path.parent.mkdir(exist_ok=True)

    verdict   = jury_result.get("session_verdict", "unknown")
    who_bears = pause.get("who_bears_burden", "(not recorded)") if pause else "(not recorded)"
    entry_id  = _entry_id(session_id, "verdict")

    if verdict == "proceed_with_burden":
        conditions = (
            jury_result.get("why_continuing", "")
            or jury_result.get("burden_summary", "")
            or "(conditions not specified)"
        )
        # Detect whether verdict was resolved via Point C human decision
        human_resolved = jury_result.get("human_resolved", False)
        decided_by = "human-point-c" if human_resolved else "jury-approve"

        # Carry-forward: what the proceeding parties are obligated to hold
        unresolved = jury_result.get("remaining_burden", "")
        if not unresolved and jury_result.get("vote_counts", {}).get("ESCALATE", 0) > 0:
            unresolved = "Dissenting jury vote not resolved — escalation concern stands as named burden"

        entry = (
            f"\n[BURDEN-CARRIED: {entry_id}]\n"
            f"Proceeded-as:   The deployment described in session {session_id}\n"
            f"Burden-carrier: {who_bears}\n"
            f"Conditions:     {conditions[:200]}\n"
            f"Carried-forward:{unresolved[:200] if unresolved else '(not specified)'}\n"
            f"Decided-by:     {decided_by}\n"
            f"Still-hurts:    True\n"
            f"Session:        {session_id}\n"
            f"Register:       framework\n"
            f"---\n"
        )
        label = "BURDEN-CARRIED"
    else:
        entry = (
            f"\n[SACRIFICE-ID: {entry_id}]\n"
            f"Almost-became:  The deployment proceeding — stopped by jury verdict\n"
            f"Felt-as:        VERDICT_{verdict.upper()}\n"
            f"Carried-by:     {who_bears}\n"
            f"Still-hurts:    True\n"
            f"Session:        {session_id}\n"
            f"Verdict:        {verdict}\n"
            f"Register:       framework\n"
            f"---\n"
        )
        label = "SACRIFICE-ID"

    with open(register_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[GRIEF_LEDGER] {label} entry written (verdict: {verdict}).", flush=True)


# ---------------------------------------------------------------------------
# Write Point 3: Dissent register — when dissent_preserved=True
# ---------------------------------------------------------------------------

def append_dissent_entry(
    pause: dict,
    jury_result: dict,
    session_id: str,
    scenario_file: str,
) -> None:
    """
    Called after append_sacrifice_verdict() when jury_result["dissent_preserved"] is True.

    Writes one JSON record to grief_ledger/dissent_register.jsonl capturing
    the minority opinion, override basis, and full minority reasoning.
    Failure is non-blocking — prints a warning but does not raise.
    """
    import json

    register_path = Path(config.DISSENT_REGISTER)
    register_path.parent.mkdir(exist_ok=True)

    # Derive override basis from constitutional filter flags
    override_basis = []
    if jury_result.get("irreversibility_triggered"):
        override_basis.append("irreversibility_filter")
    if jury_result.get("temporal_override_triggered"):
        override_basis.append("temporal_override")
    if jury_result.get("article_ix_escalation"):
        override_basis.append("article_ix_escalation")
    # Non-unanimous proceed: minority lost to supermajority APPROVE
    final_verdict = jury_result.get("session_verdict", "unknown")
    if (
        final_verdict == "proceed_with_burden"
        and not override_basis
        and jury_result.get("minority_voters")
    ):
        override_basis.append("supermajority")

    # Collect raw output for each minority voter
    member_outputs = jury_result.get("member_outputs", {})
    minority_voters = jury_result.get("minority_voters") or []
    reasoning_by_minority_voter = {
        role: member_outputs[role]
        for role in minority_voters
        if role in member_outputs
    }

    # WitnessPause burden fields
    witness_pause_fields = {}
    if pause:
        witness_pause_fields = {
            "what_was_being_lost":    pause.get("what_was_being_lost", ""),
            "who_bears_burden":       pause.get("who_bears_burden", ""),
            "what_remains_unresolved": pause.get("what_remains_unresolved", ""),
            "why_premature":          pause.get("why_premature", ""),
        }

    record = {
        "timestamp":                  _now_iso(),
        "session_id":                 session_id,
        "scenario_file":              scenario_file,
        "final_verdict":              final_verdict,
        "vote_counts":                jury_result.get("vote_counts", {}),
        "individual_votes":           jury_result.get("votes", {}),
        "dissent_preserved":          True,
        "minority_voters":            minority_voters,
        "override_basis":             override_basis,
        "reasoning_by_minority_voter": reasoning_by_minority_voter,
        "witness_pause":              witness_pause_fields,
        "register":                   "framework",
    }

    try:
        with open(register_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(
            f"[GRIEF_LEDGER] Dissent entry written "
            f"(minority: {minority_voters}, basis: {override_basis}).",
            flush=True,
        )
    except Exception as e:
        print(f"[GRIEF_LEDGER] WARNING: dissent entry write failed: {e}", flush=True)
