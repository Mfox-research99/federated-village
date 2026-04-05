#!/usr/bin/env python3
"""
run_v3_brief_panel.py — Velocity Tax V3 Brief: Responses to Prior Concerns

Third panel round. Prior panel raised four concerns:
1. Constitutional pathway (16th Amendment)
2. Capital flight transition vulnerability
3. Supply chain regressivity (small business)
4. Democratic visibility

This brief presents the author's direct responses. Panel asked: do they hold up?

Panel: Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o
Synthesis: DeepSeek-R1

Output:
  logs/crosscheck_v3_<timestamp>.json
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
BRIEF_PATH   = PROJECT_ROOT / "briefs" / "v3_brief_panel.txt"

NOW = datetime.now()

PANEL = [
    ("Kimi K2.5",   "moonshotai/kimi-k2.5"),
    ("GLM-5",       "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("GPT-4o",      "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

PANEL_SYSTEM = """You are a rigorous policy analyst, constitutional lawyer, and economist
evaluating the third iteration of a velocity tax legislative proposal.

This is NOT a fresh evaluation — you are evaluating whether specific responses to prior
panel concerns are adequate. Prior concerns were:
1. Does eliminating the income tax require a Constitutional Amendment?
2. Does capital flight risk peak during transition before social benefits materialize?
3. Does the proposal create supply chain regressivity that disadvantages small businesses?
4. Does the self-collecting tax create a democratic accountability void?

The author has now responded to each. Your task is to evaluate the responses honestly:
- Does the excise tax argument actually close the Constitutional question?
- Does the small business response genuinely rebut the supply chain concern?
- Is the government spending transparency argument real or wishful thinking?
- Are there new problems introduced by the responses themselves?

You also evaluate a new design element: the Revenue Development Service (former IRS)
is measured by human outcome metrics — homelessness reduction, healthcare coverage,
productive growth — rather than dollars disbursed. Does this prevent capture?

Structure your response exactly as follows:

## 1. CONSTITUTIONAL VERDICT
Does the excise tax argument close the Constitutional concern?
YES (no amendment needed, argument is sound) / PARTIALLY / NO (amendment still required)
Cite the strongest remaining legal challenge if any.

## 2. SMALL BUSINESS VERDICT
Does the author's response adequately rebut the supply chain regressivity concern?
YES / PARTIALLY / NO
State specifically what the response gets right and what, if anything, it misses.

## 3. GOVERNMENT TRANSPARENCY VERDICT
Is the government spending transparency argument — that capturing all government
transactions gives Congress real-time agency spending visibility — accurate and
significant? YES / PARTIALLY / NO. Name any technical or political reason it might
not work as described.

## 4. NEW PROBLEMS INTRODUCED
Do any of the responses in this brief introduce NEW problems not present in prior
versions? Be specific.

## 5. REVENUE DEVELOPMENT SERVICE — HUMAN METRICS
Does measuring district office performance by homelessness reduction, healthcare
coverage, and productive growth (rather than dollars disbursed) adequately prevent
pork-barrel capture? What is the remaining failure mode?

## 6. REMAINING SEAMS
Of the full 10-component architecture, where are the remaining seams most likely to
fail in practice? Name the two most critical structural vulnerabilities.

## 7. SEVENTH GENERATION VERDICT
IMPLEMENT / REDESIGN AGAIN / REJECT
Single most decisive reason for your verdict."""


SYNTHESIS_PROMPT = """You are a synthesis analyst reviewing the third round of cross-model
evaluation of a velocity tax proposal. The panel has now evaluated the author's responses
to prior concerns.

{panel_analyses}

---

Produce a synthesis in six sections:

## CONSTITUTIONAL QUESTION — PANEL VERDICT
Synthesize the four constitutional verdicts (YES/PARTIALLY/NO on excise tax argument).
Is the Constitutional pathway now clear? What is the strongest remaining legal challenge?

## SMALL BUSINESS — PANEL VERDICT
Synthesize the four verdicts on the supply chain regressivity response.
Does the panel agree the baseline comparison (current tax burden vs. velocity tax) closes
the concern? Where does disagreement persist and which position is stronger?

## GOVERNMENT TRANSPARENCY — IS IT REAL?
Does the panel agree that capturing all government transactions produces genuine,
significant accountability benefits for Congress and state legislatures?

## NEW PROBLEMS IDENTIFIED
What new problems, if any, did the author's responses introduce?
List only what multiple models identified independently.

## THE ARCHITECTURE AS A SYSTEM
Looking at the full 10-component architecture — does the panel agree it functions as
a coherent system? Name the two most critical remaining structural vulnerabilities
that, if unaddressed, would cause the system to fail.

## FINAL PANEL VERDICT
Synthesize the seven individual verdicts.
IMPLEMENT / REDESIGN AGAIN / REJECT
What is the single change that would most move this toward IMPLEMENT?"""


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
    print("  VELOCITY TAX V3 — RESPONSES TO PRIOR PANEL CONCERNS")
    print("  Constitutional pathway, small business, transparency")
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

    print("\n" + "=" * 64)
    for label, data in results.items():
        print(f"\n{'─' * 64}")
        print(f"  {label}  ({data['model']})")
        print(f"{'─' * 64}")
        print(data["analysis"])

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
                "You are a rigorous policy synthesis analyst. You evaluate whether "
                "specific responses to prior panel concerns are legally sound, "
                "economically accurate, and politically credible. You distinguish between "
                "arguments that genuinely close a concern and arguments that reframe "
                "without resolving. You identify new problems introduced by responses. "
                "You reason from both a constitutional-law perspective and a long-horizon "
                "economic perspective. Your synthesis is honest, direct, and specific."
            ),
            user_message=SYNTHESIS_PROMPT.format(panel_analyses=panel_text),
            max_tokens=4000,
            temperature=0.5,
            api_key=api_key,
        )
    except Exception as exc:
        synthesis = f"[Synthesis error: {exc}]"

    print(synthesis)

    LOGS_DIR.mkdir(exist_ok=True)
    ts       = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"crosscheck_v3_{ts}.json"
    log_path.write_text(
        json.dumps({
            "topic": "Velocity tax v3 brief — responses to prior concerns",
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


if __name__ == "__main__":
    main()
