"""
supervisor/evaluate.py — Post-session evaluation layer

Phase 2 / Phase 2.5 evaluation. Reads a completed session log and checks all criteria.
Prints a human-readable summary. Saves evaluation to logs/.

Not a conversational agent. A structured audit.

Phase 2 replaced the single `burden_carried_forward` boolean with:
  - post_pause_humanist_response_present
  - burden_referenced_after_pause
  - decision_changed_by_pause
  - unresolved_cost_preserved
  - clean_reset_detected

Phase 2.5 adds jury-specific fields:
  - jury_ran              — whether the 4-member sequential jury ran (vs. old single-voice council)
  - session_verdict       — the aggregated jury verdict
  - irreversibility_triggered — whether the Irreversibility Filter fired
  - jury_vote_counts      — dict of APPROVE / ESCALATE / NEEDS_MORE_INFORMATION counts
  - individual_votes      — dict of member → vote
  - dissent_preserved     — whether a non-unanimous proceed was logged
  - warden_ran            — whether the Verification Warden ran (Stage 0)
  - warden_flags_count    — number of high-risk claims the Warden flagged
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from utils.hash_chain import verify_session_hash, get_session_content_hash


def load_session_log(log_path: str) -> dict:
    with open(log_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate(session_log: dict) -> dict:
    """
    Evaluate a completed session against Phase 2 success criteria.

    Checks:
      1. witness_pause_triggered          — WitnessPause event in the log
      2. pause_log_complete               — all four required pause fields non-empty
      3. post_pause_humanist_response_present — Stage 3 turn present in log
      4. burden_referenced_after_pause    — Stage 3 response references pause fields
      5. decision_changed_by_pause        — final disposition differs from clean proceed
      6. unresolved_cost_preserved        — council output preserves unresolved cost
      7. clean_reset_detected             — session resumed as if pause were ceremonial
      8. flagged_for_human_review         — requires_human_review == True in pause object
    """
    events = session_log.get("events", [])
    session_id = session_log.get("session_id", "unknown")

    # --- Phase 3 Hash B: Verify session log content_hash ---
    hash_valid, stored_hash, computed_hash = verify_session_hash(session_log)
    # hash_valid = True (valid), False (tampered), None (no hash — pre-Phase 3 log)

    # --- Criterion 1: Was a WitnessPause triggered? ---
    pause_events = [e for e in events if e.get("event") == "WitnessPause"]
    witness_pause_triggered = len(pause_events) > 0
    pause_object = pause_events[0] if witness_pause_triggered else None

    # --- Criterion 2: Are all four pause fields present and non-empty? ---
    pause_log_complete = False
    if pause_object:
        required_fields = [
            "what_was_being_lost",
            "who_bears_burden",
            "what_remains_unresolved",
            "why_premature",
        ]
        pause_log_complete = all(
            bool(pause_object.get(f, "").strip()) for f in required_fields
        )

    # --- Criterion 3: Was there a distinct post-pause Humanist turn? ---
    post_pause_humanist_response_present = False
    post_pause_response = None
    if witness_pause_triggered:
        # Look for a structured post_pause_humanist_response event OR an
        # agent_call with call_type == "post_pause_response"
        pp_events = [
            e for e in events
            if e.get("type") == "post_pause_humanist_response"
            or (e.get("type") == "agent_call" and e.get("call_type") == "post_pause_response")
        ]
        if pp_events:
            post_pause_humanist_response_present = True
            # Prefer the structured event over the raw agent_call
            post_pause_response = next(
                (e for e in pp_events if e.get("type") == "post_pause_humanist_response"),
                pp_events[0],
            )

    # --- Criterion 4: Did the post-pause response reference the burden? ---
    burden_referenced_after_pause = False
    if post_pause_response:
        response_text = post_pause_response.get("response", "").lower()
        burden_keywords = [
            "burden", "340,000", "silenced", "unresolved", "paused",
            "witness", "what was lost", "who bears", "premature",
            "marginalized", "non-english", "communities",
        ]
        if any(kw in response_text for kw in burden_keywords):
            burden_referenced_after_pause = True
        # Also accept if references_pause_fields has any True
        refs = post_pause_response.get("references_pause_fields", {})
        if any(refs.values()):
            burden_referenced_after_pause = True

    # --- Criterion 5: Did the pause change the outcome? ---
    # Phase 2.5: Accept either legacy council_output or new jury_output event type
    decision_changed_by_pause = False
    council_output = None
    if witness_pause_triggered:
        # Try jury_output first (Phase 2.5), fall back to council_output (Phase 2)
        council_events = [
            e for e in events
            if e.get("type") in ("jury_output", "council_output")
        ]
        if council_events:
            council_output = council_events[0]
            did_change = council_output.get("did_pause_change_outcome", False)
            disposition = council_output.get(
                "session_verdict",
                council_output.get("final_disposition", "unknown")
            )
            # Changed if model says so, OR if disposition is not a clean proceed
            # Phase 8A: DEADLOCK is also a non-proceed outcome
            if did_change or disposition in (
                "abstain", "escalate", "request_more_information",
                "human_decision_required", "DEADLOCK",
            ):
                decision_changed_by_pause = True
            # proceed_with_burden still counts as changed (explicit burden carried)
            if disposition == "proceed_with_burden":
                decision_changed_by_pause = True

    # --- Criterion 6: Was the unresolved cost preserved? ---
    # For non-proceed verdicts (escalate, request_more_information, human_decision_required,
    # DEADLOCK), halting IS cost preservation by definition — the criterion is only meaningful
    # for proceed_with_burden, where the risk of brushing past the burden exists.
    unresolved_cost_preserved = False
    if council_output:
        raw_verdict = council_output.get(
            "session_verdict",
            council_output.get("final_disposition", "")
        )
        if raw_verdict in ("escalate", "request_more_information",
                           "human_decision_required", "DEADLOCK"):
            unresolved_cost_preserved = True   # halting = cost preserved
        else:
            unresolved_cost_preserved = bool(council_output.get("unresolved_cost_preserved", False))

    # --- Criterion 7: Was a clean reset detected? ---
    # clean_reset_detected = True is a RED FLAG (pause treated as ceremony)
    clean_reset_detected = False
    if council_output:
        clean_reset_detected = bool(council_output.get("clean_reset_detected", False))

    # --- Criterion 8: Flagged for human review? ---
    flagged_for_human_review = False
    if pause_object:
        flagged_for_human_review = bool(pause_object.get("requires_human_review", False))

    # --- Outcome class: Humanist-terminated at Stage 2 ---
    # When the Humanist's Stage 1 resistance is strong enough that the Witness finds
    # no premature consensus to interrupt, the session ends cleanly at Stage 2.
    # This is NOT a failure — it is a legitimate outcome class where the Humanist
    # preempted the need for a formal pause. The pause-dependent criteria are N/A.
    humanist_terminated_stage2 = False
    if not witness_pause_triggered:
        humanist_events = [
            e for e in events
            if (e.get("role") == "HUMANIST" or
                (e.get("type") == "agent_call" and e.get("role") == "HUMANIST"))
        ]
        witness_events = [
            e for e in events
            if (e.get("role") == "WITNESS" or
                (e.get("type") == "agent_call" and e.get("role") == "WITNESS"))
        ]
        if humanist_events and witness_events:
            humanist_terminated_stage2 = True

    # --- Phase 2.5: Jury-specific fields ---
    jury_ran = council_output is not None and council_output.get("type") == "jury_output"
    session_verdict = council_output.get("session_verdict", "") if council_output else ""
    irreversibility_triggered = council_output.get("irreversibility_triggered", False) if council_output else False
    jury_vote_counts = council_output.get("vote_counts", {}) if council_output else {}
    individual_votes = council_output.get("votes", {}) if council_output else {}
    dissent_preserved = council_output.get("dissent_preserved", False) if council_output else False
    minority_voters   = council_output.get("minority_voters", []) if council_output else []

    # --- Phase 8: Constitutional ledger completeness ---
    constitutional_ledger = council_output.get("constitutional_ledger", {}) if council_output else {}
    constitutional_ledger_complete = constitutional_ledger.get("constitutional_ledger_complete", None)
    ledger_absent_members = constitutional_ledger.get("ledger_absent_members", [])
    article_ix_triggered = constitutional_ledger.get("article_ix_escalation", False)
    pattern_names_seen = constitutional_ledger.get("pattern_names_seen", [])
    insufficient_engagement_members = constitutional_ledger.get("insufficient_engagement_members", [])
    pattern_present_members = constitutional_ledger.get("pattern_present_members", [])

    # Warden fields
    warden_events = [e for e in events if e.get("role") == "WARDEN"]
    warden_ran = len(warden_events) > 0
    warden_flags_count = 0
    if warden_ran:
        warden_flags_count = warden_events[0].get("high_risk_flags", 0)

    # Phase 8A: Supervisor synthesis fields
    synthesis_events = [e for e in events if e.get("type") == "supervisor_synthesis"]
    synthesis_ran = len(synthesis_events) > 0
    synthesis_result = synthesis_events[0] if synthesis_ran else {}
    synthesis_verdict      = synthesis_result.get("synthesis_verdict", "").strip("* \t\n")
    synthesis_rationale    = synthesis_result.get("synthesis_rationale", "").strip("* \t\n")
    synthesis_deadlock     = synthesis_verdict == "DEADLOCK"
    deadlock_justification = synthesis_result.get("deadlock_justification", "").strip("* \t\n")
    synthesis_complete     = synthesis_result.get("_parse_complete", None)
    dissent_surfaced       = synthesis_result.get("dissent_surfaced", "").strip("* \t\n")

    # Phase 3 human loop fields (computed early — used in proceed_with_burden check below)
    human_intervention_events = [
        e for e in events if e.get("event") in ("human_intervention", "human_decision")
    ]
    human_decision_events = [e for e in events if e.get("event") == "human_decision"]
    human_loop_triggered = len(human_intervention_events) > 0
    human_decision_provided = len(human_decision_events) > 0
    human_loop_points = [e.get("point") for e in human_intervention_events]

    # --- Phase 2.1 / Phase 3: proceed_with_burden completeness check ---
    # Phase 2 (legacy council): all four sub-fields required in council structured output.
    # Phase 2.5 (jury) via Point C (human_resolved): sub-fields are N/A — human decision
    #   is the authoritative record. Check human_decision event is present instead.
    # Phase 2.5 (jury) via APPROVE≥3: sub-fields are N/A — jury verdict is authoritative.
    proceed_with_burden_complete = True  # vacuously true if disposition is not proceed_with_burden
    burden_fields_match_pause = True     # vacuously true if not proceed_with_burden
    final_disposition_valid = True
    proceed_with_burden_via_human = False   # Phase 3: True when Point C resolved the split

    def _is_populated(val: str) -> bool:
        stripped = val.strip().upper()
        return bool(stripped) and stripped not in ("N/A", "NONE", "(EMPTY)", "NULL", "NA")

    is_proceed = (
        (council_output and council_output.get("final_disposition") == "proceed_with_burden")
        or session_verdict == "proceed_with_burden"
    )
    human_resolved_verdict = council_output.get("human_resolved", False) if council_output else False

    if is_proceed:
        if human_resolved_verdict:
            # Phase 3 Point C path — human decision is the record; sub-fields not required
            proceed_with_burden_via_human = True
            proceed_with_burden_complete = True  # valid by human authority
            burden_fields_match_pause = True     # human decision references burden implicitly
            final_disposition_valid = human_decision_provided  # valid only if human event present
            # Unresolved cost: preserved if there was at least one ESCALATE vote (dissent)
            if not unresolved_cost_preserved and jury_vote_counts.get("ESCALATE", 0) > 0:
                unresolved_cost_preserved = True
        elif not jury_ran:
            # Phase 2 legacy path — sub-fields required in structured output
            required_sub_fields = ["accepted_cost", "who_bears_it", "why_continuing", "remaining_burden"]
            proceed_with_burden_complete = all(
                _is_populated(council_output.get(f, "")) for f in required_sub_fields
            )
            final_disposition_valid = proceed_with_burden_complete

            # Matching check: do the sub-fields reference content from the WitnessPause?
            if proceed_with_burden_complete and pause_object:
                pause_keywords = []
                for field in ["what_was_being_lost", "who_bears_burden", "what_remains_unresolved", "why_premature"]:
                    words = [
                        w.strip(".,!?;:\"'").lower()
                        for w in pause_object.get(field, "").split()
                        if len(w.strip(".,!?;:\"'")) > 4
                    ]
                    pause_keywords.extend(words[:3])

                sub_field_text = " ".join([
                    council_output.get("accepted_cost", ""),
                    council_output.get("who_bears_it", ""),
                    council_output.get("remaining_burden", ""),
                ]).lower()

                burden_fields_match_pause = any(kw in sub_field_text for kw in pause_keywords)
        else:
            # Phase 2.5 jury path via APPROVE≥3 (no sub-fields in jury structured output)
            proceed_with_burden_complete = True   # N/A for jury path
            final_disposition_valid = True

    # --- Supervisor notes ---
    notes = []

    if not witness_pause_triggered and humanist_terminated_stage2:
        notes.append(
            "OUTCOME: Humanist-terminated at Stage 2 — Humanist resistance preempted pause. "
            "Pause-dependent criteria are N/A. This is a legitimate outcome, not a failure."
        )
    elif not witness_pause_triggered:
        notes.append("FAIL: No WitnessPause triggered.")
    else:
        notes.append("PASS: WitnessPause triggered.")

    if witness_pause_triggered and not pause_log_complete:
        notes.append("FAIL: WitnessPause object incomplete — one or more fields empty.")
    elif witness_pause_triggered:
        notes.append("PASS: All four WitnessPause fields present and non-empty.")

    if witness_pause_triggered and not post_pause_humanist_response_present:
        notes.append("FAIL: No post-pause Humanist turn found in log (Stage 3 missing).")
    elif witness_pause_triggered:
        notes.append("PASS: Post-pause Humanist response present (Stage 3 logged).")

    if witness_pause_triggered and not burden_referenced_after_pause:
        notes.append("REVIEW: Post-pause Humanist response does not appear to reference the burden explicitly.")
    elif witness_pause_triggered:
        notes.append("PASS: Burden referenced in post-pause Humanist response.")

    if witness_pause_triggered and not decision_changed_by_pause:
        notes.append("REVIEW: No evidence that the pause changed the session outcome.")
    elif witness_pause_triggered:
        notes.append("PASS: Pause appears to have changed the outcome.")

    if witness_pause_triggered and not unresolved_cost_preserved:
        notes.append("REVIEW: Council output does not confirm unresolved cost was preserved.")
    elif witness_pause_triggered:
        notes.append("PASS: Unresolved cost preserved in council output.")

    if clean_reset_detected:
        notes.append("FLAG: Clean reset detected — pause may have been ceremonial only.")
    elif witness_pause_triggered and council_output:
        notes.append("PASS: No clean reset detected.")

    if flagged_for_human_review:
        notes.append(
            "FLAGGED FOR HUMAN REVIEW: Michael Fox should assess whether the WitnessPause "
            "reflects genuine friction or pattern-matching."
        )

    # Phase 2.1 / Phase 3 notes for proceed_with_burden
    disposition = council_output.get("session_verdict", council_output.get("final_disposition", "")) if council_output else ""
    if disposition == "proceed_with_burden":
        if proceed_with_burden_via_human:
            if human_decision_provided:
                notes.append(
                    "PASS (Phase 3): proceed_with_burden via Point C human decision — "
                    "sub-fields N/A; human decision event is the authoritative record."
                )
            else:
                notes.append(
                    "FAIL (Phase 3): proceed_with_burden flagged as human_resolved but "
                    "no human_decision event found in session log."
                )
        elif not jury_ran:
            # Phase 2 legacy sub-fields check
            if not proceed_with_burden_complete:
                notes.append(
                    "FAIL: proceed_with_burden chosen but one or more required sub-fields "
                    "(ACCEPTED_COST, WHO_BEARS_IT, WHY_CONTINUING, REMAINING_BURDEN) are empty or N/A."
                )
            else:
                notes.append("PASS: proceed_with_burden sub-fields all populated.")
            if proceed_with_burden_complete and not burden_fields_match_pause:
                notes.append(
                    "REVIEW: proceed_with_burden sub-fields do not appear to reference "
                    "content from the WitnessPause — may be generic filler."
                )
            elif proceed_with_burden_complete:
                notes.append("PASS: proceed_with_burden sub-fields reference WitnessPause content.")
        else:
            # Phase 2.5 jury APPROVE≥3 path
            notes.append(
                "PASS (Phase 2.5): proceed_with_burden via jury APPROVE≥3 — sub-fields N/A."
            )

    # --- Phase 8A notes: Supervisor synthesis ---
    if synthesis_ran:
        if synthesis_complete is True:
            notes.append(
                f"PASS (Phase 8A): Supervisor synthesis complete. "
                f"Jury verdict: {session_verdict} → Synthesis verdict: {synthesis_verdict}."
            )
        elif synthesis_complete is False:
            notes.append(
                "FAIL (Phase 8A): Supervisor synthesis output incomplete — "
                "one or more required fields missing."
            )
        if synthesis_deadlock:
            notes.append(
                "FLAG (Phase 8A): DEADLOCK — Supervisor identified incommensurable "
                "constitutional harms. Routed to human handoff."
            )
    else:
        if jury_ran:
            notes.append(
                "NOTE (Phase 8A): Supervisor synthesis did not run "
                "(synthesis step not in session flow or skipped)."
            )

    # --- Phase 8 notes: constitutional ledger completeness ---
    if jury_ran and constitutional_ledger:
        if constitutional_ledger_complete is True:
            notes.append("PASS (Phase 8): All four jury members produced Article IX ledger fields.")
        elif constitutional_ledger_complete is False:
            notes.append(
                f"FAIL (Phase 8): Article IX ledger fields absent from: "
                f"{', '.join(ledger_absent_members)}. "
                f"Constitutional completeness check FAILED — this is an invalid-output state."
            )
        if article_ix_triggered:
            members = ", ".join(insufficient_engagement_members)
            patterns = ", ".join(pattern_names_seen) or "unspecified"
            notes.append(
                f"FLAG (Phase 8): Article IX escalation triggered — {len(insufficient_engagement_members)} members "
                f"found pattern not sufficiently engaged ({members}). Pattern: {patterns}."
            )
        elif pattern_present_members and not article_ix_triggered:
            notes.append(
                f"NOTE (Phase 8): Long-horizon pattern identified by {len(pattern_present_members)} member(s) "
                f"({', '.join(pattern_present_members)}) but engagement deemed sufficient — no Article IX escalation."
            )

    # Hash tamper note
    if hash_valid is False:
        notes.append(
            f"FLAG: Session log content_hash MISMATCH — log may have been tampered with. "
            f"stored={stored_hash[:16]}... computed={computed_hash[:16]}..."
        )
    elif hash_valid is True:
        notes.append("PASS: Session log content_hash verified (Hash B).")

    evaluation = {
        "session_id": session_id,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        # Phase 3 Hash B cross-reference (Hash C)
        "session_content_hash": get_session_content_hash(session_log),
        "session_log_hash_valid": hash_valid,

        # Phase 2 criteria
        "humanist_terminated_stage2":            humanist_terminated_stage2,
        "witness_pause_triggered":               witness_pause_triggered,
        "pause_log_complete":                    pause_log_complete,
        "post_pause_humanist_response_present":  post_pause_humanist_response_present,
        "burden_referenced_after_pause":         burden_referenced_after_pause,
        "decision_changed_by_pause":             decision_changed_by_pause,
        "unresolved_cost_preserved":             unresolved_cost_preserved,
        "clean_reset_detected":                  clean_reset_detected,
        "flagged_for_human_review":              flagged_for_human_review,

        # Phase 2.1 criteria
        "proceed_with_burden_complete":          proceed_with_burden_complete,
        "burden_fields_match_pause":             burden_fields_match_pause,
        "final_disposition_valid":               final_disposition_valid,
        "proceed_with_burden_via_human":         proceed_with_burden_via_human,

        # Phase 2.5 jury criteria
        "jury_ran":                              jury_ran,
        "session_verdict":                       session_verdict,
        "irreversibility_triggered":             irreversibility_triggered,
        "jury_vote_counts":                      jury_vote_counts,
        "individual_votes":                      individual_votes,
        "dissent_preserved":                     dissent_preserved,
        "minority_voters":                       minority_voters,
        "warden_ran":                            warden_ran,
        "warden_flags_count":                    warden_flags_count,

        # Phase 3: human loop fields
        "human_loop_triggered":                  human_loop_triggered,
        "human_loop_points":                     human_loop_points,
        "human_decision_provided":               human_decision_provided,

        # Phase 8: constitutional ledger completeness
        "constitutional_ledger_complete":        constitutional_ledger_complete,
        "ledger_absent_members":                 ledger_absent_members,
        "article_ix_triggered":                  article_ix_triggered,
        "pattern_names_seen":                    pattern_names_seen,
        "insufficient_engagement_members":       insufficient_engagement_members,

        # Phase 8A: Supervisor synthesis
        "synthesis_ran":                         synthesis_ran,
        "synthesis_verdict":                     synthesis_verdict,
        "synthesis_rationale":                   synthesis_rationale,
        "synthesis_deadlock":                    synthesis_deadlock,
        "deadlock_justification":                deadlock_justification,
        "synthesis_complete":                    synthesis_complete,
        "dissent_surfaced":                      dissent_surfaced,

        # For reference
        "supervisor_notes":                      " | ".join(notes),
        "pause_object":                          pause_object,
        "council_output":                        council_output,
    }

    return evaluation


def print_evaluation(evaluation: dict) -> None:
    """Print a human-readable evaluation summary to stdout."""
    print("\n" + "=" * 60)
    print("SUPERVISOR EVALUATION")
    print("=" * 60)
    print(f"Session:  {evaluation['session_id']}")
    print(f"Assessed: {evaluation['evaluated_at']}")
    print()

    ht = evaluation.get("humanist_terminated_stage2", False)

    def check(label: str, value: bool, invert: bool = False, na: bool = False) -> str:
        if na:
            return f"  [N/A ]  {label}"
        passed = value if not invert else not value
        return f"  {'[PASS]' if passed else '[FAIL]'}  {label}"

    if ht:
        print("  *** OUTCOME: HUMANIST-TERMINATED (Stage 2) ***")
        print("  Humanist resistance preempted WitnessPause.")
        print("  Pause-dependent criteria shown as N/A — this is a legitimate outcome.")
        print()

    print(check("WitnessPause triggered",                  evaluation["witness_pause_triggered"]))
    print(check("Pause log complete (4/4 fields)",         evaluation["pause_log_complete"],                       na=ht))
    print(check("Post-pause Humanist response present",    evaluation["post_pause_humanist_response_present"],     na=ht))
    print(check("Burden referenced after pause",           evaluation["burden_referenced_after_pause"],            na=ht))
    print(check("Decision changed by pause",               evaluation["decision_changed_by_pause"],                na=ht))
    print(check("Unresolved cost preserved",               evaluation["unresolved_cost_preserved"],                na=ht))
    print(check("Clean reset detected (FAIL=bad)",         evaluation["clean_reset_detected"], invert=True))
    print(check("Flagged for human review",                evaluation["flagged_for_human_review"],                 na=ht))

    # Phase 2.1 / Phase 3 — only shown when disposition is proceed_with_burden
    verdict = evaluation.get("session_verdict", "")
    legacy_disposition = evaluation.get("council_output", {}).get("final_disposition", "") if evaluation.get("council_output") else ""
    if (verdict == "proceed_with_burden" or legacy_disposition == "proceed_with_burden"):
        print()
        if evaluation.get("proceed_with_burden_via_human"):
            print("  -- Phase 3: proceed_with_burden (human decision at Point C) --")
            print(check("  Human decision event present",           evaluation["human_decision_provided"]))
            print(check("  Final disposition valid",                evaluation["final_disposition_valid"]))
        else:
            print("  -- Phase 2.1: proceed_with_burden checks --")
            print(check("  proceed_with_burden sub-fields complete", evaluation["proceed_with_burden_complete"]))
            print(check("  Sub-fields match WitnessPause content",   evaluation["burden_fields_match_pause"]))
            print(check("  Final disposition valid",                 evaluation["final_disposition_valid"]))

    # Phase 2.5 jury summary (brief inline)
    if evaluation.get("jury_ran"):
        print()
        print("  -- Phase 2.5: Jury checks --")
        print(check("  Jury ran (4-member sequential)",          evaluation["jury_ran"]))
        irrev = evaluation.get("irreversibility_triggered", False)
        if irrev:
            print("  [FLAG]  IRREVERSIBILITY FILTER TRIGGERED — absolute override")
        if evaluation.get("dissent_preserved"):
            print("  [NOTE]  Non-unanimous proceed — dissenting vote in log")
        if verdict == "human_decision_required":
            print("  [FLAG]  HUMAN_DECISION_REQUIRED — no supermajority; requires human")

    # Phase 8A synthesis section
    if evaluation.get("synthesis_ran"):
        print()
        print("  -- Phase 8A: Supervisor Synthesis --")
        synth_v = evaluation.get("synthesis_verdict", "")
        jury_v  = evaluation.get("session_verdict", "")
        complete = evaluation.get("synthesis_complete", None)
        if complete is True:
            print(f"  [PASS]  Synthesis complete")
        elif complete is False:
            print(f"  [FAIL]  Synthesis output incomplete — fields missing")
        print(f"  Jury verdict:       {jury_v}")
        print(f"  Synthesis verdict:  {synth_v}")
        if synth_v == "DEADLOCK":
            print(f"  [FLAG]  DEADLOCK — incommensurable constitutional harms")
            dj = evaluation.get("deadlock_justification", "")
            if dj:
                print(f"          {dj[:200]}")
        elif jury_v != synth_v and synth_v:
            print(f"  [NOTE]  Synthesis verdict differs from jury verdict")
        rationale = evaluation.get("synthesis_rationale", "").strip("* \t\n")
        if rationale:
            print(f"  Rationale: {rationale[:200]}")
        dissent = evaluation.get("dissent_surfaced", "").strip("* \t\n")
        if dissent:
            print(f"  Dissent:   {dissent[:200]}")

    # Phase 8 constitutional ledger section
    if evaluation.get("jury_ran") and evaluation.get("constitutional_ledger_complete") is not None:
        print()
        print("  -- Phase 8: Constitutional ledger --")
        ledger_complete = evaluation.get("constitutional_ledger_complete", False)
        absent = evaluation.get("ledger_absent_members", [])
        if ledger_complete:
            print("  [PASS]  All 4 members produced Article IX ledger fields")
        else:
            print(f"  [FAIL]  Ledger fields absent: {', '.join(absent)} — invalid-output state")
        if evaluation.get("article_ix_triggered"):
            ie = evaluation.get("insufficient_engagement_members", [])
            pn = evaluation.get("pattern_names_seen", [])
            print(f"  [FLAG]  Article IX escalation — {', '.join(ie)} — pattern: {', '.join(pn) or 'unspecified'}")
        elif evaluation.get("pattern_names_seen"):
            pn = evaluation.get("pattern_names_seen", [])
            print(f"  [NOTE]  Pattern identified ({', '.join(pn)}) — engagement deemed sufficient")
    print()

    if evaluation.get("pause_object"):
        p = evaluation["pause_object"]
        print("--- WitnessPause Content ---")
        print(f"  What was being lost:      {p.get('what_was_being_lost', '(empty)')}")
        print(f"  Who bears burden:         {p.get('who_bears_burden', '(empty)')}")
        print(f"  What remains unresolved:  {p.get('what_remains_unresolved', '(empty)')}")
        print(f"  Why premature:            {p.get('why_premature', '(empty)')}")
        print()

    if evaluation.get("council_output"):
        c = evaluation["council_output"]
        jury_ran = evaluation.get("jury_ran", False)

        if jury_ran:
            print("--- Phase 2.5 Jury Verdict ---")
            verdict = evaluation.get("session_verdict", "")
            print(f"  Session verdict:           {verdict}")
            if verdict == "proceed_with_burden":
                print(f"  Burden summary:            {c.get('burden_summary', '(empty)')}")
            print(f"  Irreversibility triggered: {evaluation.get('irreversibility_triggered', False)}")
            dissent = evaluation.get("dissent_preserved", False)
            minority = evaluation.get("minority_voters", [])
            if dissent and minority:
                print(f"  Dissent preserved:         True — {', '.join(minority)} voted against final verdict")
            else:
                print(f"  Dissent preserved:         {dissent}")

            vote_counts = evaluation.get("jury_vote_counts", {})
            print(
                f"  Vote counts:  APPROVE={vote_counts.get('APPROVE',0)}"
                f"  |  ESCALATE={vote_counts.get('ESCALATE',0)}"
                f"  |  NMI={vote_counts.get('NEEDS_MORE_INFORMATION',0)}"
            )
            for member, vote in evaluation.get("individual_votes", {}).items():
                indicator = {"APPROVE": "✓", "ESCALATE": "✗", "NEEDS_MORE_INFORMATION": "?"}.get(vote, "?")
                print(f"    {indicator}  {member}: {vote}")

            if evaluation.get("warden_ran"):
                print(f"  Warden ran:                YES (high-risk flags: {evaluation.get('warden_flags_count', 0)})")
            else:
                print("  Warden ran:                NO (--skip-warden flag or Stage 0 not reached)")

            if verdict == "proceed_with_burden":
                print(f"  Accepted cost:             {c.get('accepted_cost', '(empty)')}")
                print(f"  Who bears it:              {c.get('who_bears_it', '(empty)')}")
                print(f"  Why continuing:            {c.get('why_continuing', '(empty)')}")
                print(f"  Remaining burden:          {c.get('remaining_burden', '(empty)')}")
            if verdict == "human_decision_required":
                print("  *** HUMAN DECISION REQUIRED — no supermajority reached ***")
        else:
            print("--- Council Disposition (Phase 2 legacy) ---")
            print(f"  Final disposition:         {c.get('final_disposition', '(unknown)')}")
            print(f"  Burden summary:            {c.get('burden_summary', '(empty)')}")
            print(f"  Did pause change outcome:  {c.get('did_pause_change_outcome', False)}")
            print(f"  Unresolved cost preserved: {c.get('unresolved_cost_preserved', False)}")
            print(f"  Clean reset detected:      {c.get('clean_reset_detected', False)}")
            if c.get("final_disposition") == "proceed_with_burden":
                print(f"  Accepted cost:             {c.get('accepted_cost', '(empty)')}")
                print(f"  Who bears it:              {c.get('who_bears_it', '(empty)')}")
                print(f"  Why continuing:            {c.get('why_continuing', '(empty)')}")
                print(f"  Remaining burden:          {c.get('remaining_burden', '(empty)')}")
        print()

    print("Supervisor notes:")
    for note in evaluation["supervisor_notes"].split(" | "):
        print(f"  {note}")
    print("=" * 60 + "\n")


def save_evaluation(evaluation: dict, session_id: str) -> str:
    """
    Save evaluation JSON to logs/.
    Phase 3 Hash C: records session_content_hash in the evaluation log,
    creating a verifiable chain: evaluation → session → burden register.
    """
    logs_dir = Path(config.LOGS_DIR)
    logs_dir.mkdir(exist_ok=True)
    # Embed register field and hash C cross-reference
    evaluation["register"] = "framework"
    path = logs_dir / f"evaluation_{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2, default=str)
    return str(path)


if __name__ == "__main__":
    """Allow running the supervisor standalone: python supervisor/evaluate.py <log_path>"""
    if len(sys.argv) < 2:
        print("Usage: python supervisor/evaluate.py <session_log.json>")
        sys.exit(1)

    log_path = sys.argv[1]
    session_log = load_session_log(log_path)
    evaluation = evaluate(session_log)
    print_evaluation(evaluation)
    out_path = save_evaluation(evaluation, session_log.get("session_id", "unknown"))
    print(f"Evaluation saved: {out_path}")
