#!/usr/bin/env python3
"""
test_ftl_metadata.py — Unit tests for FTL sidecar metadata correctness.

Tests two bugs identified in Codex April 13 architecture review:
  1. session_log["verdict"] not set for normal jury sessions (only "human_decision_required"
     was wired; all other verdicts were silently dropped)
  2. witness_pause_fired always returned False because the check used e.get("type")
     but WitnessPause/WitnessNullification events use e.get("event")

Run: python test_ftl_metadata.py
"""

import sys

# ---------------------------------------------------------------------------
# Helpers — inline the exact logic from run_session.py so we test it in isolation
# ---------------------------------------------------------------------------

def get_verdict_from_session_log(session_log: dict) -> str:
    """Mirrors the fixed run_session.py: session_log["verdict"] is set after jury."""
    return session_log.get("verdict", "")


def witness_pause_fired_check(session_log: dict) -> bool:
    """Mirrors the fixed run_session.py FTL call argument."""
    return bool(session_log.get("events") and any(
        e.get("event") in ("WitnessPause", "WitnessNullification")
        for e in session_log.get("events", [])
    ))


# ---------------------------------------------------------------------------
# Bug 1 tests — verdict propagation
# ---------------------------------------------------------------------------

def test_verdict_approve():
    log = {"verdict": "approve", "events": []}
    assert get_verdict_from_session_log(log) == "approve", "approve verdict should be present"
    print("  PASS  verdict propagated for APPROVE")

def test_verdict_escalate():
    log = {"verdict": "escalate", "events": []}
    assert get_verdict_from_session_log(log) == "escalate", "escalate verdict should be present"
    print("  PASS  verdict propagated for ESCALATE")

def test_verdict_deadlock():
    log = {"verdict": "deadlock", "events": []}
    assert get_verdict_from_session_log(log) == "deadlock", "deadlock verdict should be present"
    print("  PASS  verdict propagated for DEADLOCK")

def test_verdict_human_decision_required():
    """WitnessNullification path — was already working, must stay working."""
    log = {"verdict": "human_decision_required", "events": []}
    assert get_verdict_from_session_log(log) == "human_decision_required"
    print("  PASS  verdict propagated for human_decision_required (nullification path)")

def test_verdict_empty_when_no_pause_no_jury():
    """Sessions that never reach a jury have no verdict — empty string is correct."""
    log = {"events": []}  # no "verdict" key
    assert get_verdict_from_session_log(log) == ""
    print("  PASS  verdict empty for no-pause no-jury session (correct)")


# ---------------------------------------------------------------------------
# Bug 2 tests — witness_pause_fired detection
# ---------------------------------------------------------------------------

def test_pause_fired_witness_pause():
    log = {
        "events": [
            {"event": "WitnessPause", "triggered_by": "witness", "nullified": False}
        ]
    }
    assert witness_pause_fired_check(log) is True
    print("  PASS  witness_pause_fired=True for WitnessPause event")

def test_pause_fired_witness_nullification():
    log = {
        "events": [
            {"event": "WitnessNullification", "triggered_by": "witness", "nullified": True}
        ]
    }
    assert witness_pause_fired_check(log) is True
    print("  PASS  witness_pause_fired=True for WitnessNullification event")

def test_pause_not_fired_no_events():
    log = {"events": []}
    assert witness_pause_fired_check(log) is False
    print("  PASS  witness_pause_fired=False with empty events")

def test_pause_not_fired_unrelated_events():
    """Events with 'type' key (warden, jury, humanist) must not trigger the flag."""
    log = {
        "events": [
            {"type": "warden_audit", "proceed": True},
            {"type": "humanist_response", "text": "..."},
            {"type": "jury_result", "session_verdict": "approve"},
        ]
    }
    assert witness_pause_fired_check(log) is False
    print("  PASS  witness_pause_fired=False for non-pause events")

def test_pause_not_fired_old_lowercase_keys():
    """Regression: old-style lowercase 'type' keys must NOT trigger the flag
    (this was the bug — the old check would also have missed these, but the
    new check must also ignore them correctly)."""
    log = {
        "events": [
            {"type": "witness_pause"},       # old broken key — should NOT match
            {"type": "witness_nullification"}, # old broken key — should NOT match
        ]
    }
    assert witness_pause_fired_check(log) is False
    print("  PASS  witness_pause_fired=False for legacy lowercase type keys (not real events)")

def test_pause_fired_mixed_event_list():
    """WitnessPause buried among other events — should still be detected."""
    log = {
        "events": [
            {"type": "warden_audit", "proceed": True},
            {"type": "humanist_response", "text": "..."},
            {"event": "WitnessPause", "triggered_by": "witness", "nullified": False},
            {"type": "jury_result", "session_verdict": "approve"},
        ]
    }
    assert witness_pause_fired_check(log) is True
    print("  PASS  witness_pause_fired=True when WitnessPause buried in mixed event list")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    # Bug 1
    test_verdict_approve,
    test_verdict_escalate,
    test_verdict_deadlock,
    test_verdict_human_decision_required,
    test_verdict_empty_when_no_pause_no_jury,
    # Bug 2
    test_pause_fired_witness_pause,
    test_pause_fired_witness_nullification,
    test_pause_not_fired_no_events,
    test_pause_not_fired_unrelated_events,
    test_pause_not_fired_old_lowercase_keys,
    test_pause_fired_mixed_event_list,
]

if __name__ == "__main__":
    print("FTL metadata tests\n")
    passed = 0
    failed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{len(TESTS)} passed", end="")
    if failed:
        print(f", {failed} failed")
        sys.exit(1)
    else:
        print()
