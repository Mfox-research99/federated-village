#!/usr/bin/env python3
"""
run_v4_brief_panel.py — Velocity Tax V4: Supply Chain Math + Banker Construct

Fourth panel round. Adds:
- Quantitative supply chain model (97% tax reduction; 26x less burden across chain)
- Three-mode counter-cyclical rate design (banker construct)
- Bank strategic reserve transition (minerals, gold, foreign currency)
- Legal challenge direct responses
- Simplified RDS productivity metrics

Panel: Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o
Synthesis: DeepSeek-R1

Output:
  logs/crosscheck_v4_<timestamp>.json
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
BRIEF_PATH   = PROJECT_ROOT / "briefs" / "v4_brief_panel.txt"

NOW = datetime.now()

PANEL = [
    ("Kimi K2.5",   "moonshotai/kimi-k2.5"),
    ("GLM-5",       "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("GPT-4o",      "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

PANEL_SYSTEM = """You are a rigorous policy analyst, constitutional economist, and
monetary systems expert evaluating the fourth iteration of a velocity tax proposal.

This proposal has now been through three prior rounds of cross-model review. Each round
identified specific concerns; each new version responded to them. You are evaluating
whether the responses in this version are adequate and whether the full architecture
is now approaching constitutional and economic soundness.

Two new elements require careful evaluation:

1. THE SUPPLY CHAIN MATH: The prior panel identified supply chain regressivity as
   unresolved. This version provides a quantitative model. Evaluate whether the numbers
   presented close the concern or whether a structural issue remains.

2. THE BANKER CONSTRUCT: A three-mode counter-cyclical rate design replaces the prior
   mechanical formula. Evaluate whether it resolves the procyclical concern or introduces
   new instability. The three modes: (1) prosperity — higher rate, build reserves;
   (2) general volatility — lower rate, support liquidity; (3) extreme capital outflow —
   higher rate on exit transactions, break panic momentum.

Structure your response exactly as follows:

## 1. SUPPLY CHAIN MATH — VERDICT
Does the quantitative model close the regressivity concern?
CLOSED / PARTIALLY CLOSED / STILL OPEN
Cite specifically what the model proves and what, if anything, it does not prove.

## 2. THREE-MODE RATE — VERDICT
Does the banker construct resolve the procyclical concern?
RESOLVED / PARTIALLY RESOLVED / STILL A PROBLEM
Name the remaining failure mode, if any.

## 3. LEGAL CHALLENGES — VERDICT
Do the legal responses (excise tax / South Carolina v. Baker) adequately address
the constitutional challenges? What is the strongest remaining vulnerability?

## 4. BANK STRATEGIC RESERVES — VERDICT
Is the proposal that banks transition from holding government debt to building real
asset reserves (minerals, gold, foreign currencies) sound? What is the implementation
risk?

## 5. COHERENCE OF FULL ARCHITECTURE
Does the 10-component system function coherently? Name the single remaining seam
most likely to cause systemic failure.

## 6. TRAJECTORY ASSESSMENT
This is the fourth round of review. Is the proposal converging toward IMPLEMENT?
What is the one remaining change that would get it there?

## 7. SEVENTH GENERATION VERDICT
IMPLEMENT / REDESIGN AGAIN / REJECT
Single most decisive reason."""


SYNTHESIS_PROMPT = """You are synthesizing the fourth round of cross-model evaluation
of a velocity tax proposal that has been iteratively refined across four rounds.

{panel_analyses}

---

## SUPPLY CHAIN MATH — FINAL VERDICT
Does the panel agree the quantitative model closes the regressivity concern?
Synthesize. Where models disagree, adjudicate.

## THREE-MODE RATE — FINAL VERDICT
Does the panel agree the banker construct resolves the procyclical concern?
What is the consensus remaining failure mode, if any?

## LEGAL CHALLENGES — FINAL VERDICT
Synthesize panel verdicts on the constitutional arguments. What is the strongest
remaining legal vulnerability? Is it litigable or fatal?

## COHERENCE — DOES THE SYSTEM HOLD?
Does the full 10-component architecture function as a coherent system?
What single seam is the panel most concerned about?

## TRAJECTORY — ARE WE APPROACHING IMPLEMENT?
After four rounds, what is the panel's overall assessment of the proposal's trajectory?
What is the single change that would move the collective verdict to IMPLEMENT?

## FINAL PANEL VERDICT
IMPLEMENT / REDESIGN AGAIN / REJECT
The panel's collective verdict and the single most decisive reason."""


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
    print("  VELOCITY TAX V4 — SUPPLY CHAIN MATH + BANKER CONSTRUCT")
    print("  Fourth round: quantitative model + counter-cyclical rate")
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
                "You are synthesizing the fourth and potentially final round of "
                "cross-model review of a velocity tax proposal. Prior rounds identified "
                "specific concerns; each was addressed. Your task is to determine whether "
                "the proposal has now converged on constitutional and economic soundness, "
                "or whether specific, addressable issues remain. Be direct about trajectory: "
                "is this approaching IMPLEMENT or not? If REDESIGN AGAIN, name precisely "
                "what single change would close the gap."
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
    log_path = LOGS_DIR / f"crosscheck_v4_{ts}.json"
    log_path.write_text(
        json.dumps({
            "topic": "Velocity tax v4 brief — supply chain math + banker construct",
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
