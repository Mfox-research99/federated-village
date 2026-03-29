#!/usr/bin/env python3
"""
tracks/path_b/run_session.py — Federated Village Path B entry point

Run the full 5-stage deliberation with any mix of OpenRouter models.

Usage:
  python run_session.py --scenario ../../scenarios/scenario_04.md
  python run_session.py --scenario ../../scenarios/scenario_04.md --config config/default.yaml
  python run_session.py --scenario ../../scenarios/scenario_04.md \\
      --config config/examples/all_claude.yaml \\
      --witness openai/gpt-4o

Config resolution order (highest to lowest):
  CLI flag  →  roles.<role> in YAML  →  default_model in YAML  →  error
"""

import argparse
import sys
import uuid
from pathlib import Path

# Make sure local packages resolve before any installed packages
sys.path.insert(0, str(Path(__file__).parent))

from agents.roles import ROLES, load_config, apply_cli_overrides
from session.flow import run_session
from output.writer import write_results

DEFAULT_CONFIG = Path(__file__).parent / "config" / "default.yaml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Federated Village Path B — multi-model deliberation via OpenRouter."
    )
    parser.add_argument(
        "--scenario", required=True,
        help="Path to scenario .md file."
    )
    parser.add_argument(
        "--config", default=str(DEFAULT_CONFIG),
        help=f"Path to YAML config file (default: {DEFAULT_CONFIG})."
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-stage progress output."
    )
    # One optional override flag per role
    for role in ROLES:
        parser.add_argument(
            f"--{role.replace('_', '-')}",
            dest=role,
            metavar="MODEL",
            default=None,
            help=f"Override model for the {role} role.",
        )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Load scenario
    scenario_path = Path(args.scenario)
    if not scenario_path.exists():
        # Try relative to project root
        from agents.base import PROJECT_ROOT
        candidate = PROJECT_ROOT / args.scenario
        if candidate.exists():
            scenario_path = candidate
    if not scenario_path.exists():
        print(f"Error: scenario file not found: {args.scenario}", file=sys.stderr)
        sys.exit(1)
    scenario_text = scenario_path.read_text(encoding="utf-8").strip()

    # Load config + apply CLI overrides
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    try:
        role_model_map = load_config(config_path)
    except ValueError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        sys.exit(1)

    cli_overrides = {role: getattr(args, role, None) for role in ROLES}
    role_model_map = apply_cli_overrides(role_model_map, cli_overrides)

    session_id = uuid.uuid4().hex[:12]
    print(f"[SESSION] {session_id} | {scenario_path.name} | {config_path.name}", flush=True)

    record = run_session(
        scenario_text=scenario_text,
        scenario_path=str(scenario_path),
        config_path=str(config_path),
        role_model_map=role_model_map,
        session_id=session_id,
        verbose=not args.quiet,
    )

    txt_path, json_path = write_results(record)
    print(f"\n[OUTPUT] {txt_path}")
    print(f"[OUTPUT] {json_path}")


if __name__ == "__main__":
    main()
