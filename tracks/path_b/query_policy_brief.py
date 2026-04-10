#!/usr/bin/env python3
"""
query_policy_brief.py — Direct policy review query, no Village framework.

Sends a policy brief to one or more models and collects their responses.
Used for practical gap analysis, not constitutional deliberation.

Usage:
  python query_policy_brief.py --brief path/to/brief.md
  python query_policy_brief.py --brief path/to/brief.md --models google/gemini-2.5-pro-preview-03-25 anthropic/claude-opus-4-6
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from agents.base import call_model, get_api_key

SYSTEM_PROMPT = """You are a senior policy analyst and legislative counsel with expertise in
international monetary policy, US tax law, and sovereign debt. You are reviewing a policy
brief for practical feasibility and legislative soundness.

Your task is to identify:
1. Genuine legal or jurisdictional obstacles to implementation
2. Economic assumptions that need verification or correction
3. Administrative gaps — mechanisms described but not yet designed
4. Political vulnerabilities — provisions that create easy targets for opposition
5. Things that are missing — important considerations not addressed

Be direct and specific. Do not philosophize. Do not restate the brief back.
Focus on what is workable, what needs work, and what is missing.
This is intended for a US legislative audience."""

QUERY = """Review the attached policy brief for the APT Foreign Participation architecture.

Answer these questions:
1. What are the genuine legal/jurisdictional obstacles to universal USD application offshore?
2. Is the aggregate-only compliance architecture administratively achievable? What would it require?
3. What is the correct current estimate for the offshore dollar base, and what is your source?
4. What multilateral vehicle is best suited to administer the debt relief pool?
5. What provisions are most politically vulnerable and how should they be reframed?
6. What is missing from this brief that must be addressed before this goes to legislative text?

Brief follows:

"""

DEFAULT_MODELS = [
    "google/gemini-2.5-pro-preview-03-25",
    "anthropic/claude-opus-4-6",
]


def main():
    parser = argparse.ArgumentParser(description="Direct policy brief review via OpenRouter.")
    parser.add_argument("--brief", required=True, help="Path to policy brief .md file.")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS,
                        help="Models to query.")
    parser.add_argument("--max-tokens", type=int, default=2000,
                        help="Max tokens per response (default: 2000).")
    args = parser.parse_args()

    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"Error: brief file not found: {args.brief}", file=sys.stderr)
        sys.exit(1)

    brief_text = brief_path.read_text(encoding="utf-8").strip()
    api_key = get_api_key()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = brief_path.stem
    out_path = Path(__file__).parent / "output" / "policy_reviews" / f"{timestamp}_{slug}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("=" * 80)
    lines.append(f"POLICY BRIEF REVIEW — {brief_path.name}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 80)

    for model in args.models:
        print(f"\n[QUERYING] {model} ...", flush=True)
        user_message = QUERY + brief_text
        try:
            response = call_model(
                model=model,
                system_prompt=SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=args.max_tokens,
                temperature=0.3,
                api_key=api_key,
            )
        except Exception as e:
            response = f"[ERROR: {e}]"

        lines.append(f"\n{'─' * 80}")
        lines.append(f"MODEL: {model}")
        lines.append(f"{'─' * 80}")
        lines.append(response)
        print(f"[DONE] {model}")

    lines.append(f"\n{'=' * 80}")
    output = "\n".join(lines)
    out_path.write_text(output, encoding="utf-8")
    print(f"\n[OUTPUT] {out_path}")
    print(output)


if __name__ == "__main__":
    main()
