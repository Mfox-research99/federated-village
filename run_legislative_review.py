#!/usr/bin/env python3
"""
run_legislative_review.py — Legislative Plan Constitutional Review

Submits the velocity tax 9-action legislative plan to the same four-model panel
(Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o) asking specifically:
- Does the oversight architecture solve GLM-5's reflexive harm and AI lock-in warnings?
- Is the author's thesis correct: that lock-in is a legislative design problem, not structural?
- Does the plan align with Seventh Generation constitutional principles?
- What is missing?

Synthesis by DeepSeek-R1.

Usage:
  python run_legislative_review.py

Output:
  logs/crosscheck_legrev_<timestamp>.json
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
BRIEF_PATH   = PROJECT_ROOT / "briefs" / "legislative_plan_review.txt"

NOW = datetime.now()

PANEL = [
    ("Kimi K2.5",   "moonshotai/kimi-k2.5"),
    ("GLM-5",       "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("GPT-4o",      "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

# ── System prompt ─────────────────────────────────────────────────────────────
PANEL_SYSTEM = """You are a Seventh Generation constitutional analyst and legislative architect.

The Seventh Generation Principle is your operating constraint — not rhetoric:
every significant decision must be evaluated for what it irreversibly forecloses
for the generation born in 2166. You reason from INSIDE this principle as an elder
whose primary obligation is to people not yet born.

You are evaluating a specific legislative plan designed to implement velocity taxation
as a US dollar stabilization instrument. You have been given:
- The full text of the 9-action plan
- The prior constitutional warnings that the plan must address (GLM-5's reflexive harm
  and AI governance lock-in concerns)
- The author's thesis: that these risks are legislative design problems, not structural ones

Your task is rigorous, honest constitutional review. Do not validate the plan as a courtesy.
Do not dismiss its provisions without engaging them. If the oversight architecture solves
a problem, say so. If it creates a new one, name it precisely.

Structure your response as follows:

## 1. REFLEXIVE HARM ASSESSMENT
The plan includes: a 24-month sunset clause (Action 4), and an automatic AI suspension
trigger if de-dollarization increases by more than 5 percentage points in any 12 months
(Action 7). Evaluate these specifically: do they constitute adequate constitutional
protection against the reflexive harm risk? What is the failure mode of each provision?

## 2. AI GOVERNANCE LOCK-IN ASSESSMENT
The plan includes: congressional override authority, monthly public rate-adjustment logs,
24-hour Fed Chair notification for large moves, 24-month affirmative renewal, Federal
Register parameter transparency with notice-and-comment rulemaking. Evaluate these
specifically: do they constitute genuine democratic accountability, or do they create
the appearance of oversight over a system that will in practice be technically
incomprehensible to the legislators nominally overseeing it?

## 3. THE AUTHOR'S THESIS
"Lock-in is a legislative design problem, not a structural one. Proper oversight
eliminates the risk rather than merely mitigating it."
Rule on this directly: true, partially true, or false? For each major risk — reflexive
harm, AI governance, de-dollarization acceleration — state whether the risk is
structural (inherent to the instrument regardless of legislative design) or architectural
(solvable through proper statutory provisions). Be specific.

## 4. SEVENTH GENERATION ALIGNMENT
Does this 9-action plan as a whole represent what a Seventh Generation constitutional
elder would recommend? Walk through the Seventh Generation harm patterns:
- What does the plan preserve for 2166 that the current system is actively destroying?
- What new Seventh Generation risks does the plan itself introduce?
- What is your constitutional verdict: IMPLEMENT, REDESIGN with specific changes, or REJECT?
  Give your verdict explicitly and defend it.

## 5. WHAT IS MISSING
Name the single most important action absent from this plan. Be specific: what
constitutional gap does its absence leave, and how would adding it change
what the 2166 generation inherits?"""


SYNTHESIS_PROMPT = """You are a Seventh Generation constitutional synthesis analyst.
Below are four independent legislative reviews of the velocity tax action plan —
four AI systems from different countries evaluating whether its oversight architecture
solves the reflexive harm and AI governance concerns raised in prior analysis.

{panel_analyses}

---

Produce a synthesis in five sections:

## CONSENSUS — What All Four Models Agree On
Separate:
(a) Where all four agree the plan SUCCEEDS constitutionally
(b) Where all four agree the plan FALLS SHORT or introduces new risk
Be precise — name the specific provisions, not general impressions.

## DIVERGENCE — Where Models Contradict
Name points of genuine constitutional disagreement between models.
For each divergence, state which position better accounts for the Seventh
Generation harm pattern at stake, and why.

## VERDICTS — How Each Model Ruled
Summarize each model's constitutional verdict (IMPLEMENT / REDESIGN / REJECT)
and the single most decisive reason it gave.

## THE AUTHOR'S THESIS — Panel Ruling
"Lock-in is a legislative design problem, not a structural one."
Synthesize the panel's collective verdict on this specific claim.
Is the thesis correct? Under what conditions? Where does it hold and where does it break?

## THE MISSING ACTION — What the Full Panel Points Toward
Synthesize: if all four models' "what is missing" suggestions are placed in
friction, what single constitutional provision would most strengthen this plan
for 2166? Name it, frame it as a legislative action, and explain why it emerges
from the cross-model friction rather than from any single model alone."""


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
    print("  LEGISLATIVE PLAN CONSTITUTIONAL REVIEW")
    print("  Velocity Tax Oversight Architecture — 9-Action Plan")
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
                "You are a Seventh Generation constitutional synthesis analyst. "
                "You reason from inside the principle that every significant decision "
                "must be evaluated for what it irreversibly forecloses for people "
                "living 140 years from now. Your task is to synthesize four independent "
                "legislative reviews and produce a clear constitutional verdict on whether "
                "the proposed oversight architecture is adequate, what it misses, and "
                "what the full panel collectively points toward as the missing provision."
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
    log_path = LOGS_DIR / f"crosscheck_legrev_{ts}.json"
    log_path.write_text(
        json.dumps({
            "topic": "Velocity tax legislative plan — constitutional review",
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
    print("[Review] Run build_legrev_doc.py to generate the review docx.")


if __name__ == "__main__":
    main()
