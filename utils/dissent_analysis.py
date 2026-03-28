#!/usr/bin/env python3
"""
Corpus-level dissent analysis for Federated Village session logs.

Note: the current corpus spans multiple architecture phases. Many older jury
sessions predate `minority_voters`, `parse_quality`, and Phase 8 constitutional
fields, so this script infers only the minimum needed for reporting and treats
raw dissent reasoning as opaque text.
"""

from __future__ import annotations

import glob
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parent.parent
LOG_GLOB = str(ROOT / "logs" / "session_*.json")
DISSENT_REGISTER = ROOT / "grief_ledger" / "dissent_register.jsonl"


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                records.append(json.loads(text))
            except json.JSONDecodeError:
                records.append({
                    "_malformed": True,
                    "_lineno": lineno,
                    "_raw": text[:200],
                })
    return records


def basename(path_str: Optional[str]) -> str:
    if not path_str:
        return "<missing>"
    return Path(path_str).name


def find_verdict_event(events: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for event in events:
        if isinstance(event, dict) and "session_verdict" in event:
            return event
    return None


def infer_minority_voters(event: Dict[str, Any]) -> List[str]:
    explicit = event.get("minority_voters")
    if isinstance(explicit, list) and explicit:
        return [str(role) for role in explicit]

    if not event.get("dissent_preserved"):
        return []

    votes = event.get("votes") or {}
    if not isinstance(votes, dict) or not votes:
        return []

    verdict = event.get("session_verdict")
    if verdict == "proceed_with_burden":
        return [role for role, vote in votes.items() if vote != "APPROVE"]
    if verdict == "escalate":
        return [role for role, vote in votes.items() if vote == "APPROVE"]
    return []


def infer_override_basis(event: Dict[str, Any]) -> List[str]:
    basis: List[str] = []
    if event.get("irreversibility_triggered"):
        basis.append("irreversibility_filter")
    if event.get("temporal_override_triggered"):
        basis.append("temporal_override")
    if event.get("article_ix_escalation"):
        basis.append("article_ix_escalation")
    if event.get("dissent_preserved") and event.get("session_verdict") == "proceed_with_burden":
        basis.append("supermajority")
    if event.get("dissent_preserved") and event.get("session_verdict") == "escalate" and not basis:
        basis.append("unknown")
    return basis


def compact_counter(counter: Counter) -> str:
    if not counter:
        return "(none)"
    return ", ".join(f"{key}={counter[key]}" for key in sorted(counter))


def print_header(title: str) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")


def main() -> None:
    paths = [Path(p) for p in sorted(glob.glob(LOG_GLOB))]
    sessions = []
    malformed_verdict_sessions: List[str] = []
    no_verdict_sessions: List[str] = []
    no_verdict_warden_halt: List[str] = []
    scenario_totals: Counter = Counter()
    scenario_jury: Counter = Counter()
    scenario_dissent: Counter = Counter()
    verdict_counts: Counter = Counter()
    verdict_by_scenario: Dict[str, Counter] = defaultdict(Counter)
    minority_role_counts: Counter = Counter()
    dissent_pair_counts: Counter = Counter()
    dissent_verdict_context: Counter = Counter()
    override_basis_counts: Counter = Counter()
    filter_counts: Counter = Counter()
    multi_filter_count = 0
    dissent_sessions = []
    constitutional_filter_without_dissent: List[str] = []
    dissent_missing_minority: List[str] = []

    for path in paths:
        try:
            session = load_json(path)
        except json.JSONDecodeError:
            malformed_verdict_sessions.append(path.name)
            continue

        scenario = basename(session.get("scenario_file"))
        scenario_totals[scenario] += 1
        events = session.get("events", [])
        verdict = find_verdict_event(events)
        if verdict is None:
            no_verdict_sessions.append(path.name)
            if session.get("warden_halt"):
                no_verdict_warden_halt.append(path.name)
            continue

        if not isinstance(verdict, dict):
            malformed_verdict_sessions.append(path.name)
            continue

        scenario_jury[scenario] += 1
        session_id = str(session.get("session_id", path.stem))
        final_verdict = str(verdict.get("session_verdict", "<missing>"))
        verdict_counts[final_verdict] += 1
        verdict_by_scenario[scenario][final_verdict] += 1

        filters = [
            ("irreversibility_filter", bool(verdict.get("irreversibility_triggered"))),
            ("temporal_override", bool(verdict.get("temporal_override_triggered"))),
            ("article_ix_escalation", bool(verdict.get("article_ix_escalation"))),
        ]
        active_filters = [name for name, active in filters if active]
        for name in active_filters:
            filter_counts[name] += 1
        if len(active_filters) > 1:
            multi_filter_count += 1

        dissent_preserved = bool(verdict.get("dissent_preserved"))
        minority_voters = infer_minority_voters(verdict)
        if dissent_preserved:
            scenario_dissent[scenario] += 1
            dissent_verdict_context[final_verdict] += 1
            if not verdict.get("minority_voters"):
                dissent_missing_minority.append(path.name)
            for role in minority_voters:
                minority_role_counts[role] += 1
            for pair in combinations(sorted(set(minority_voters)), 2):
                dissent_pair_counts[" + ".join(pair)] += 1
            basis = infer_override_basis(verdict)
            for item in basis:
                override_basis_counts[item] += 1
            dissent_sessions.append({
                "session_id": session_id,
                "scenario": scenario,
                "final_verdict": final_verdict,
                "minority_voters": minority_voters,
                "override_basis": basis,
                "votes": verdict.get("votes", {}),
            })

        if active_filters and not dissent_preserved:
            constitutional_filter_without_dissent.append(path.name)

        sessions.append({
            "path": path.name,
            "session_id": session_id,
            "scenario": scenario,
            "verdict": final_verdict,
            "dissent_preserved": dissent_preserved,
        })

    register_records = safe_jsonl(DISSENT_REGISTER)
    register_valid = [record for record in register_records if not record.get("_malformed")]
    register_malformed = [record for record in register_records if record.get("_malformed")]
    register_reasoning_present = sum(
        1 for record in register_valid
        if any((text or "").strip() for text in (record.get("reasoning_by_minority_voter") or {}).values())
    )

    print_header("1. Corpus Overview")
    print(f"Total sessions processed: {len(paths)}")
    print(f"Sessions that reached jury: {len(sessions)}")
    print(f"Sessions with dissent_preserved=True: {sum(1 for s in sessions if s['dissent_preserved'])}")
    print(f"Sessions with dissent_preserved=False or field absent: {len(paths) - sum(1 for s in sessions if s['dissent_preserved'])}")
    print("\nBreakdown by scenario:")
    for scenario in sorted(scenario_totals):
        print(
            f"  {scenario}: total={scenario_totals[scenario]} | "
            f"jury={scenario_jury[scenario]} | dissent={scenario_dissent[scenario]}"
        )

    print_header("2. Verdict Distribution")
    print(f"Across jury sessions: {compact_counter(verdict_counts)}")
    print("\nBy scenario:")
    for scenario in sorted(verdict_by_scenario):
        print(f"  {scenario}: {compact_counter(verdict_by_scenario[scenario])}")

    print_header("3. Dissent Patterns")
    print(f"Dissent sessions: {len(dissent_sessions)}")
    print(f"Minority roles: {compact_counter(minority_role_counts)}")
    print(f"Override basis: {compact_counter(override_basis_counts)}")
    print(f"Verdict context: {compact_counter(dissent_verdict_context)}")
    print("Most common dissent co-occurrences:")
    if dissent_pair_counts:
        for pair, count in dissent_pair_counts.most_common(10):
            print(f"  {pair}: {count}")
    else:
        print("  (none)")
    print("Dissent sessions:")
    if dissent_sessions:
        for item in dissent_sessions:
            print(
                f"  {item['session_id'][:8]} | {item['scenario']} | {item['final_verdict']} | "
                f"minority={item['minority_voters'] or ['<missing>']} | "
                f"basis={item['override_basis'] or ['<none>']}"
            )
    else:
        print("  (none)")

    print_header("4. Constitutional Filter History")
    print(f"Irreversibility filter triggered: {filter_counts['irreversibility_filter']}")
    print(f"Temporal override triggered: {filter_counts['temporal_override']}")
    print(f"Article IX escalation triggered: {filter_counts['article_ix_escalation']}")
    print(f"Multiple filters in same session: {multi_filter_count}")

    print_header("5. Dissent Register Summary")
    if not DISSENT_REGISTER.exists():
        print(f"Dissent register missing: {DISSENT_REGISTER}")
    elif not register_records:
        print(f"Dissent register exists but is empty: {DISSENT_REGISTER}")
    else:
        print(f"Entries: {len(register_valid)} valid, {len(register_malformed)} malformed")
        print(f"Entries with reasoning captured: {register_reasoning_present}/{len(register_valid)}")
        for record in register_valid:
            scenario = basename(record.get("scenario_file"))
            print(
                f"  {str(record.get('session_id', ''))[:8]} | {scenario} | "
                f"{record.get('minority_voters', []) or ['<missing>']} | "
                f"{record.get('override_basis', []) or ['<missing>']} | "
                f"reasoning={'yes' if any((text or '').strip() for text in (record.get('reasoning_by_minority_voter') or {}).values()) else 'no'}"
            )
        for record in register_malformed:
            print(f"  MALFORMED line {record.get('_lineno')}: {record.get('_raw')}")

    print_header("6. Gaps and Anomalies")
    print(f"Sessions with malformed or unreadable verdict logs: {len(malformed_verdict_sessions)}")
    if malformed_verdict_sessions:
        print(f"  {', '.join(malformed_verdict_sessions[:10])}")
    print(f"Sessions with no verdict event: {len(no_verdict_sessions)}")
    if no_verdict_sessions:
        print(f"  sample: {', '.join(no_verdict_sessions[:10])}")
        print(f"  warden_halt among no-verdict sessions: {len(no_verdict_warden_halt)}")
    print(f"Sessions with dissent_preserved=True but minority_voters absent/empty: {len(dissent_missing_minority)}")
    if dissent_missing_minority:
        print(f"  {', '.join(dissent_missing_minority[:10])}")
    print(f"Sessions with constitutional filters but dissent_preserved=False: {len(constitutional_filter_without_dissent)}")
    if constitutional_filter_without_dissent:
        print(f"  {', '.join(constitutional_filter_without_dissent[:10])}")


if __name__ == "__main__":
    main()
