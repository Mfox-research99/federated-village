#!/usr/bin/env python3
"""
run_revised_brief_panel.py — Revised Fiscal Stability Brief: Cross-Model Evaluation

Submits the revised brief (social programs as primary purpose, IRS transformation,
capital flight countervailing argument, 10-action plan) to the same four-model panel
asking: what is still wrong, what is still missing, what could be stronger?

Panel: Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o
Synthesis: DeepSeek-R1

Usage:
  python run_revised_brief_panel.py

Output:
  logs/crosscheck_revised_<timestamp>.json
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tracks" / "path_b"))
from agents.base import call_model, get_api_key  # noqa: E402

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR     = PROJECT_ROOT / "logs"
BRIEF_PATH   = PROJECT_ROOT / "briefs" / "revised_brief_panel.txt"

NOW = datetime.now()

PANEL = [
    ("Kimi K2.5",   "moonshotai/kimi-k2.5"),
    ("GLM-5",       "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("GPT-4o",      "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

# ── System prompt ─────────────────────────────────────────────────────────────
PANEL_SYSTEM = """You are a rigorous policy analyst and constitutional economist with deep
expertise in monetary systems, fiscal architecture, and long-horizon democratic governance.

You are evaluating a revised legislative proposal: velocity taxation as a US dollar
stabilization instrument, with a social dividend (universal healthcare, guaranteed income,
universal pensions) as its primary stated purpose. This is the second-iteration brief —
it incorporates feedback from a prior cross-model review and has been substantially revised.

Your task is NOT to be polite about the revision. Your task is to evaluate it honestly,
looking specifically for:
- Arguments that are still weak or incomplete
- Claims that require evidence not yet provided
- Mechanisms that could fail in ways not addressed
- Political or constitutional vulnerabilities not named
- Something important that is still missing

You reason from the perspective of both a policy realist (what is politically achievable
and what gets captured in practice) AND a long-horizon constitutional thinker (what does
the generation born in 2166 inherit).

Structure your response exactly as follows:

## 1. WHAT IS NOW STRONGER
Name 2-3 specific improvements in this version compared to the prior framing.
Be precise about which revision fixed which problem.

## 2. WHAT IS STILL WEAK
Name 2-3 specific arguments, mechanisms, or claims that remain unconvincing or incomplete.
For each: state what would need to be added or changed to make it rigorous.

## 3. CAPITAL FLIGHT — VERDICT
Does the revised countervailing argument (social dividend makes US more attractive to
productive capital) successfully answer the capital flight objection? State your verdict
directly: YES (it closes the objection), PARTIALLY (it weakens the objection but does
not close it), or NO (the objection stands). Give your reasoning in 3-5 sentences.

## 4. IRS TRANSFORMATION — VERDICT
Is the proposal to transform the IRS into a district-based economic development
deployment network credible as policy? Name the single most likely failure mode and
what would prevent it.

## 5. WHAT IS MISSING
Name the single most important argument, mechanism, or provision absent from this
revised proposal. Be specific: what gap does its absence leave, and what would adding
it accomplish?

## 6. SEVENTH GENERATION VERDICT
IMPLEMENT AS REVISED / REDESIGN AGAIN / REJECT
Give your verdict explicitly. State the single most decisive reason."""


SYNTHESIS_PROMPT = """You are a policy synthesis analyst. Below are four independent
evaluations of a revised velocity tax legislative proposal — a second-iteration brief
incorporating prior cross-model feedback. The evaluations come from four AI systems
in different countries.

{panel_analyses}

---

Produce a synthesis in five sections:

## WHAT THE PANEL AGREES IS STRONGER
Specific improvements all four (or at least three) models identify as genuine progress.
Name the revisions and why they represent real fixes.

## WHAT THE PANEL AGREES IS STILL WEAK
Arguments, mechanisms, or claims that remain unconvincing across multiple models.
Name what would need to change.

## CAPITAL FLIGHT — PANEL VERDICT
Synthesize the four verdicts (YES/PARTIALLY/NO) on whether the social dividend argument
closes the capital flight objection. Where models disagree, adjudicate: which position
better accounts for the actual behavior of productive vs. speculative capital?

## IRS TRANSFORMATION — PANEL VERDICT
Is it credible? What is the consensus failure mode? What is the structural fix?

## THE MISSING PROVISION — What the Full Panel Points Toward
Place the four "what is missing" answers in friction. What single provision emerges
from the cross-model tension that no single model would have identified alone?
Name it, describe it as a legislative action, and explain why the full panel points
toward it even if no model stated it directly.

## FINAL VERDICT
Synthesize the six individual verdicts into a panel verdict:
IMPLEMENT AS REVISED / REDESIGN AGAIN WITH SPECIFIC CHANGES / REJECT
State the most decisive remaining concern and what single change would address it."""


def run_member(label, model, brief, api_key):
    try:
        result = call_model(
            model=model,
            system_prompt=PANEL_SYSTEM,
            user_message=brief,
            max_tokens=4000,
            temperature=0.6,
            api_key=api_key,
        )
        return label, model, result
    except Exception as exc:
        return label, model, f"[ERROR: {exc}]"


def main():
    api_key = get_api_key()
    brief   = BRIEF_PATH.read_text(encoding="utf-8")

    print("\n" + "=" * 64)
    print("  REVISED BRIEF — CROSS-MODEL EVALUATION")
    print("  Velocity Tax + Social Dividend: Does It Hold Up?")
    print(f"  Panel: {', '.join(l for l, _ in PANEL)}")
    print(f"  Synthesis: {SYNTHESIS_MODEL}")
    print("=" * 64)

    print(f"\n[Review] Firing {len(PANEL)} models in parallel...\n")
    results = {}

    with ThreadPoolExecutor(max_workers=len(PANEL)) as pool:
        futures = {
            pool.submit(run_member, label, model, brief, api_key): label
            for label, model in PANEL
        }
        for future in as_completed(futures):
            label, model, analysis = future.result()
            results[label] = {"model": model, "analysis": analysis}
            ok = "✓" if not analysis.startswith("[ERROR") else "✗"
            print(f"  {ok} {label}  ({model})")

    # Print individual responses
    print("\n" + "=" * 64)
    for label, data in results.items():
        print(f"\n{'─' * 64}")
        print(f"  {label}  ({data['model']})")
        print(f"{'─' * 64}")
        print(data["analysis"])

    # Synthesis
    panel_text = ""
    for label, data in results.items():
        panel_text += f"\n\n{'='*60}\n## {label} ({data['model']})\n{'='*60}\n"
        panel_text += data["analysis"]

    print(f"\n\n{'=' * 64}")
    print(f"  SYNTHESIS  ({SYNTHESIS_MODEL})")
    print("=" * 64)

    try:
        synthesis = call_model(
            model=SYNTHESIS_MODEL,
            system_prompt=(
                "You are a rigorous policy synthesis analyst. You reason from both "
                "a political-economy realist perspective (what happens in practice when "
                "legislation passes) and a long-horizon constitutional perspective (what "
                "the generation born in 2166 inherits). Your task is to synthesize four "
                "independent evaluations of a revised velocity tax proposal and produce "
                "a clear, honest assessment of its current strengths, remaining weaknesses, "
                "and what single change would most strengthen it."
            ),
            user_message=SYNTHESIS_PROMPT.format(panel_analyses=panel_text),
            max_tokens=4000,
            temperature=0.5,
            api_key=api_key,
        )
    except Exception as exc:
        synthesis = f"[Synthesis error: {exc}]"

    print(synthesis)

    # Save log
    LOGS_DIR.mkdir(exist_ok=True)
    ts       = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"crosscheck_revised_{ts}.json"
    log_path.write_text(
        json.dumps({
            "topic": "Velocity tax revised brief — cross-model evaluation",
            "timestamp": NOW.isoformat(),
            "panel": [{"label": l, "model": m} for l, m in PANEL],
            "synthesis_model": SYNTHESIS_MODEL,
            "brief_used": str(BRIEF_PATH.relative_to(PROJECT_ROOT)),
            "responses": {
                label: {"model": d["model"], "analysis": d["analysis"]}
                for label, d in results.items()
            },
            "synthesis": synthesis,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\n[Review] Log saved → {log_path.relative_to(PROJECT_ROOT)}")
    print("[Review] Run build_revised_eval_doc.py to generate the evaluation docx.")


if __name__ == "__main__":
    main()
