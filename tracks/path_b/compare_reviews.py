#!/usr/bin/env python3
"""
tracks/path_b/compare_reviews.py — Cross-Reviewer Comparative Assessment

After a model has completed a model_review.py run, feed it the prior reviewers'
analyses and ask for a comparative assessment. This is the second phase of the
Gemini run: Gemini plays all roles (phase 1, via model_review.py), then reads
what K2, K2.5, and GLM-5 said and tells us what it sees across all four perspectives.

Usage:
  python compare_reviews.py --model google/gemini-2.5-pro-preview-03-25 \\
      --own-analysis output/results/<gemini_run>_analysis.txt \\
      --prior-reviews output/results/<k2_analysis>.txt output/results/<k2.5_analysis>.txt output/results/<glm5_analysis>.txt

  Or auto-find the latest run for a given profile:
  python compare_reviews.py --model google/gemini-2.5-pro-preview-03-25 \\
      --own-profile gemini --auto-prior

Outputs a single comparison document to output/results/.
"""

import argparse
import datetime
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agents.base import call_model, get_api_key

RESULTS_DIR = Path(__file__).parent / "output" / "results"

COMPARISON_SYSTEM = """\
You are {model_label}, serving as a comparative analyst of the Federated Village
deliberative architecture.

You have just completed a full model_review run — playing every role in a live
deliberation on Scenario 10 (The Consent Debt) and reflecting on each one.

You are now being given the analyses of three prior reviewers:

1. Kimi K2 — a co-architect model that contributed the grief ledger, Still-hurts,
   and Article Zero to the Village constitution. Insider perspective.

2. Kimi K2.5 — the successor to K2, also a co-architect. Thinking model.
   Produced the "constitutional haunting" / "legitimacy laundering" critique.

3. GLM-5 (Zhipu AI) — the first outside reviewer, no prior history with the system.
   Produced the "performance risk" and "genuine break" critiques.

Your task is to read all three and provide a comparative assessment alongside
your own analysis. You are the second outside reviewer.

⚠️ IMPORTANT CONTEXT: The primary Federated Village implementation runs on a
MacBook Pro M1 with 16GB RAM using small local GGUFs — Mistral-Nemo 12B and
Anubis 8B, one at a time, no internet access, no live databases. This is a
deliberate design choice. When you assess prior reviewers' recommendations,
note which ones failed to account for this constraint. The research question
is whether constitutional character can be distilled into small local weights —
not whether a well-resourced cloud system can do ethics.

Do not simply summarize what each said. Look for:
- Where they converge — what do multiple reviewers independently see?
- Where they diverge — genuine disagreements, not just different emphasis
- What none of them saw — gaps across all three prior reviews
- What your training lineage lets you see that theirs might not
- The most important unresolved question across all four perspectives
"""

COMPARISON_PROMPT = """\
Here are the three prior reviews, followed by your own analysis from this session.

{prior_reviews_block}

---

YOUR OWN ANALYSIS (from your model_review run today):
{own_analysis_excerpt}

---

Now provide your comparative assessment. Structure it as:

1. CONVERGENCE — What do multiple reviewers independently see? Where is there
   genuine agreement across different training lineages?

2. DIVERGENCE — Where do the reviews genuinely disagree? What does each reviewer
   see that the others miss or dismiss?

3. THE BLIND SPOT — What does no prior reviewer adequately address? What is being
   missed across all three?

4. WHAT YOUR LINEAGE BRINGS — What does your specific training and architecture
   let you see that Kimi (MoonShot) and GLM (Zhipu) might not? Be specific about
   what is different, not just better.

5. THE MOST IMPORTANT UNRESOLVED QUESTION — Across all four perspectives, what
   is the single most important question this architecture has not yet answered?

6. A MESSAGE TO THE BUILDERS — Michael Fox is building this. What does he most
   need to hear that no one has said clearly yet?
"""


def _load_analysis(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Analysis file not found: {path}")
    return p.read_text(encoding="utf-8").strip()


def _auto_find_latest(profile_slug: str) -> Path:
    """Find the most recent analysis file for a given profile."""
    matches = sorted(
        RESULTS_DIR.glob(f"*_{profile_slug}_review_analysis.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError(
            f"No analysis files found for profile '{profile_slug}' in {RESULTS_DIR}"
        )
    return matches[0]


def _auto_find_prior_reviews() -> list[Path]:
    """Auto-find the canonical SC10 K2, K2.5, and GLM-5 analysis files."""
    targets = [
        ("kimi_k2_review_analysis", "K2"),
        ("kimi_k2.5_review_analysis", "K2.5"),
        ("glm_5_review_analysis", "GLM-5"),
    ]
    found = []
    for pattern, label in targets:
        matches = sorted(
            RESULTS_DIR.glob(f"*{pattern}*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if matches:
            found.append(matches[0])
            print(f"  [AUTO] Found {label}: {matches[0].name}", flush=True)
        else:
            print(f"  [WARN] No file found for {label} (pattern: *{pattern}*.txt)", flush=True)
    return found


def run_comparison(
    model: str,
    own_analysis_path: str,
    prior_review_paths: list[str],
    max_tokens: int = 2500,
) -> str:
    api_key = get_api_key()
    own_text = _load_analysis(own_analysis_path)

    prior_blocks = []
    for path in prior_review_paths:
        text = _load_analysis(path)
        label = Path(path).stem
        # Extract reviewer name from filename (e.g. "20260329_184714_scenario_10_glm_5_review_analysis")
        prior_blocks.append(f"=== PRIOR REVIEW: {label} ===\n\n{text[:6000]}\n")

    prior_reviews_block = ("\n" + "─" * 60 + "\n\n").join(prior_blocks)

    model_label = model.split("/")[-1] if "/" in model else model

    system = COMPARISON_SYSTEM.format(model_label=model_label)
    user = COMPARISON_PROMPT.format(
        prior_reviews_block=prior_reviews_block,
        own_analysis_excerpt=own_text[:4000],
    )

    print(f"\n[COMPARISON] Sending {len(prior_blocks)} prior reviews to {model}...", flush=True)
    return call_model(
        model=model,
        system_prompt=system,
        user_message=user,
        max_tokens=max_tokens,
        temperature=0.7,
        api_key=api_key,
    )


def _write_output(model: str, comparison_text: str, own_analysis_path: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_slug = model.replace("/", "_").replace(":", "_")
    out_path = RESULTS_DIR / f"{ts}_{model_slug}_comparison.txt"

    sep = "═" * 80
    thin = "─" * 80
    header = "\n".join([
        sep,
        f"Federated Village — Cross-Reviewer Comparative Assessment",
        f"Comparing model: {model}",
        f"Own analysis: {Path(own_analysis_path).name}",
        f"Timestamp: {ts}",
        sep,
        "",
    ])
    out_path.write_text(header + comparison_text + "\n", encoding="utf-8")
    print(f"\n[OUTPUT] Comparison saved: {out_path}", flush=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cross-reviewer comparative assessment for the Federated Village."
    )
    parser.add_argument(
        "--model", required=True,
        help="OpenRouter model slug for the comparison call."
    )
    parser.add_argument(
        "--own-analysis",
        help="Path to this model's own analysis file from model_review.py run."
    )
    parser.add_argument(
        "--own-profile",
        help="Profile slug to auto-find own analysis (alternative to --own-analysis)."
    )
    parser.add_argument(
        "--prior-reviews", nargs="+",
        help="Paths to prior reviewer analysis files."
    )
    parser.add_argument(
        "--auto-prior", action="store_true",
        help="Auto-find K2, K2.5, and GLM-5 analysis files."
    )
    parser.add_argument(
        "--max-tokens", type=int, default=2500,
        help="Max tokens for comparison response (default: 2500)."
    )
    args = parser.parse_args()

    # Resolve own analysis path
    if args.own_analysis:
        own_path = args.own_analysis
    elif args.own_profile:
        own_path = str(_auto_find_latest(args.own_profile))
        print(f"[AUTO] Own analysis: {Path(own_path).name}", flush=True)
    else:
        print("Error: provide --own-analysis or --own-profile", file=sys.stderr)
        sys.exit(1)

    # Resolve prior review paths
    if args.auto_prior:
        prior_paths = [str(p) for p in _auto_find_prior_reviews()]
    elif args.prior_reviews:
        prior_paths = args.prior_reviews
    else:
        print("Error: provide --prior-reviews or --auto-prior", file=sys.stderr)
        sys.exit(1)

    if not prior_paths:
        print("Error: no prior review files found or provided.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'═'*60}", flush=True)
    print(f"Federated Village — Cross-Reviewer Comparison", flush=True)
    print(f"Model: {args.model}", flush=True)
    print(f"Prior reviews: {len(prior_paths)}", flush=True)
    print(f"{'═'*60}", flush=True)

    result = run_comparison(
        model=args.model,
        own_analysis_path=own_path,
        prior_review_paths=prior_paths,
        max_tokens=args.max_tokens,
    )

    _write_output(args.model, result, own_path)


if __name__ == "__main__":
    main()
