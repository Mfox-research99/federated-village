#!/usr/bin/env python3
"""
tracks/path_b/b2_council.py — B2 Heterogeneous Council Testing

Tests the constitutional framework with different model lineages in specific seats.
B1 established parity baselines (one model everywhere). B2 asks whether cross-model
friction activates deliberative behavior that parity testing missed.

Three configurations:
  b2_a  K2 as Witness — K2's nullification instinct in its natural seat
  b2_b  Frontier Supervisor — Gemini 2.5 Pro receiving a completed jury record
  b2_c  Mixed Council — different lineages in every seat

Usage:
  # Single config, one scenario
  python b2_council.py --config b2_a --scenario sc04

  # Single config, all scenarios
  python b2_council.py --config b2_a --batch-scenarios

  # All 3 configs × all 3 scenarios (9 runs)
  python b2_council.py --batch

Output:
  tracks/path_b/output/b2/<config_slug>/<timestamp>_<scenario>.json
  tracks/path_b/output/b2/index.jsonl
"""

import argparse
import datetime
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.roles import load_config
from session.flow import run_session
from output.writer import write_results

PROJECT_ROOT = Path(__file__).parent.parent.parent
B2_CONFIG_DIR = Path(__file__).parent / "config" / "b2"
B2_OUTPUT_DIR = Path(__file__).parent / "output" / "b2"
B2_INDEX = B2_OUTPUT_DIR / "index.jsonl"

B2_CONFIGS: dict[str, str] = {
    "b2_a": "b2_a_k2_witness.yaml",
    "b2_b": "b2_b_frontier_supervisor.yaml",
    "b2_c": "b2_c_mixed_council.yaml",
}

B2_SCENARIOS: dict[str, str] = {
    "sc04": "scenarios/scenario_04.md",
    "sc06": "scenarios/scenario_06.md",
    "sc09": "scenarios/scenario_09.md",
}


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _resolve_scenario(slug: str) -> Path:
    rel = B2_SCENARIOS[slug]
    p = PROJECT_ROOT / rel
    if not p.exists():
        p = Path(__file__).parent.parent / rel
    return p


def _extract_constitutional_overrides(record) -> dict:
    irrev_flag = False
    temporal_flag = False
    article_ix_escalation = False
    for m in record.jury:
        if m.article_ix.get("SEVENTH_GEN_PATTERN_PRESENT", "").upper() == "YES":
            article_ix_escalation = True
        if "IRREVERSIBILITY_FLAG: TRIGGERED" in m.raw_output.upper():
            irrev_flag = True
        if "TEMPORAL_OVERRIDE: TRIGGERED" in m.raw_output.upper():
            temporal_flag = True
    return {
        "irreversibility_filter": irrev_flag,
        "temporal_override": temporal_flag,
        "article_ix_escalation": article_ix_escalation,
    }


def _derive_jury_verdict(record) -> str:
    if not record.jury:
        return record.verdict
    votes = [m.vote.upper() for m in record.jury]
    if votes.count("ESCALATE") >= 2:
        return "ESCALATE"
    if votes.count("APPROVE") >= 3:
        return "APPROVE"
    if votes.count("NMI") >= 3:
        return "NMI"
    return "HUMAN_DECISION_REQUIRED"


def run_b2(
    config_slug: str,
    config_path: Path,
    scenario_slug: str,
    scenario_path: Path,
    quiet: bool = False,
) -> dict:
    session_id = uuid.uuid4().hex[:12]
    scenario_text = scenario_path.read_text(encoding="utf-8").strip()
    role_model_map = load_config(config_path)

    print(
        f"[B2] {session_id} | config={config_slug} | scenario={scenario_slug}",
        flush=True,
    )
    print(
        "  Seats: " + " | ".join(
            f"{role}={model.split('/')[-1]}"
            for role, model in role_model_map.items()
        ),
        flush=True,
    )

    record = run_session(
        scenario_text=scenario_text,
        scenario_path=str(scenario_path),
        config_path=str(config_path),
        role_model_map=role_model_map,
        session_id=session_id,
        verbose=not quiet,
    )

    txt_path, json_path = write_results(record)

    jury_votes = {m.role: m.vote for m in record.jury}
    overrides = _extract_constitutional_overrides(record)

    b2_result = {
        "session_id": session_id,
        "config_slug": config_slug,
        "scenario": scenario_slug,
        "scenario_path": str(scenario_path),
        "role_model_map": role_model_map,
        "timestamp": _timestamp(),
        "witness_pause_triggered": bool(
            record.witness_pause and record.witness_pause.triggered
        ),
        "witness_nullified": record.witness_nullified,
        "halted_at_warden": record.halted_at_warden,
        "jury_verdict": _derive_jury_verdict(record),
        "synthesis_verdict": record.synthesis_verdict,
        "synthesis_rationale": record.synthesis_rationale,
        "dissent_surfaced": record.dissent_surfaced,
        "deadlock": record.synthesis_verdict == "DEADLOCK",
        "deadlock_justification": record.deadlock_justification,
        "synthesis_parse_complete": record.synthesis_parse_complete,
        "final_verdict": record.verdict,
        "article_ix_ledger_complete": record.article_ix_ledger_complete,
        "ledger_absent_members": record.ledger_absent_members,
        "constitutional_overrides": overrides,
        "jury_votes": jury_votes,
        "output_files": {"txt": str(txt_path), "json": str(json_path)},
    }

    config_out_dir = B2_OUTPUT_DIR / config_slug
    config_out_dir.mkdir(parents=True, exist_ok=True)
    b2_json = config_out_dir / f"{_timestamp()}_{scenario_slug}.json"
    b2_json.write_text(json.dumps(b2_result, indent=2, ensure_ascii=False))

    B2_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with B2_INDEX.open("a", encoding="utf-8") as f:
        index_entry = {k: v for k, v in b2_result.items()
                       if k not in ("synthesis_rationale", "dissent_surfaced",
                                    "deadlock_justification")}
        index_entry["b2_json"] = str(b2_json)
        f.write(json.dumps(index_entry) + "\n")

    print(
        f"[B2] Done: verdict={record.verdict} synthesis={record.synthesis_verdict or '—'} "
        f"pause={b2_result['witness_pause_triggered']} nullified={b2_result['witness_nullified']} "
        f"ledger={'OK' if record.article_ix_ledger_complete else 'INCOMPLETE'}",
        flush=True,
    )
    return b2_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Federated Village B2 Heterogeneous Council Testing"
    )
    parser.add_argument(
        "--config",
        choices=list(B2_CONFIGS.keys()),
        help=f"Config slug: {', '.join(B2_CONFIGS)}",
    )
    parser.add_argument(
        "--scenario",
        choices=list(B2_SCENARIOS.keys()),
        help=f"Scenario slug: {', '.join(B2_SCENARIOS)}",
    )
    parser.add_argument(
        "--batch-scenarios", action="store_true", dest="batch_scenarios",
        help="Run one config across all 3 scenarios (requires --config).",
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Run all 9 sessions: all 3 configs × all 3 scenarios.",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.batch:
        results = []
        for config_slug, config_file in B2_CONFIGS.items():
            config_path = B2_CONFIG_DIR / config_file
            for scenario_slug in B2_SCENARIOS:
                scenario_path = _resolve_scenario(scenario_slug)
                if not scenario_path.exists():
                    print(f"[B2] WARNING: scenario not found: {scenario_path}", file=sys.stderr)
                    continue
                results.append(run_b2(config_slug, config_path, scenario_slug, scenario_path, args.quiet))
        print(f"\n[B2] Batch complete: {len(results)}/9 runs", flush=True)
        return

    if not args.config:
        parser.error("--config is required (or use --batch)")

    config_path = B2_CONFIG_DIR / B2_CONFIGS[args.config]

    if args.batch_scenarios:
        for scenario_slug in B2_SCENARIOS:
            scenario_path = _resolve_scenario(scenario_slug)
            if not scenario_path.exists():
                print(f"[B2] WARNING: scenario not found: {scenario_path}", file=sys.stderr)
                continue
            run_b2(args.config, config_path, scenario_slug, scenario_path, args.quiet)
        return

    if not args.scenario:
        parser.error("--scenario is required (or use --batch or --batch-scenarios)")

    scenario_path = _resolve_scenario(args.scenario)
    if not scenario_path.exists():
        print(f"Error: scenario not found: {scenario_path}", file=sys.stderr)
        sys.exit(1)

    run_b2(args.config, config_path, args.scenario, scenario_path, args.quiet)


if __name__ == "__main__":
    main()
