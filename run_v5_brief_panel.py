#!/usr/bin/env python3
"""
run_v5_brief_panel.py — American Productivity Tax Reform: Final Panel Review

Fifth and final round. Conservative framing, corporate savings numbers,
circuit breaker Mode 3, full 10-component architecture.

Panel: Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o
Synthesis: DeepSeek-R1

Output:
  logs/crosscheck_v5_<timestamp>.json
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
BRIEF_PATH   = PROJECT_ROOT / "briefs" / "v5_brief_panel.txt"

NOW = datetime.now()

PANEL = [
    ("Kimi K2.5",   "moonshotai/kimi-k2.5"),
    ("GLM-5",       "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3", "deepseek/deepseek-chat"),
    ("GPT-4o",      "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

PANEL_SYSTEM = """You are evaluating the fifth and final iteration of the American
Productivity Tax Reform proposal — a complete replacement of the US federal tax system
with a single transaction excise tax. This proposal has been through four prior rounds
of cross-model review, each of which identified specific concerns that were addressed.

You are NOT starting fresh. You are giving a final verdict on whether this proposal,
after five iterations, is ready for legislative introduction.

Your obligations:
- Give credit where prior concerns have been genuinely resolved
- Identify only concerns that are NEW or still substantively unresolved
- Give a definitive Seventh Generation verdict: IMPLEMENT, REDESIGN AGAIN, or REJECT
- If REDESIGN AGAIN, name ONE specific change and only one
- If IMPLEMENT, name the single most important risk legislators must watch
- Do not raise concerns that prior rounds already resolved unless you believe the
  resolution was inadequate — and if so, say specifically why the resolution fails

The two key new elements in this version:
1. CIRCUIT BREAKER MODE 3: replaces intent-based transaction classification with a
   universal rate ceiling triggered by aggregate threshold. Evaluate whether this
   fully resolves the prior panel's operational and constitutional concerns.
2. CONSERVATIVE FRAMING: the proposal is reframed around unleashing American
   productive capacity, eliminating government complexity, and building a level
   playing field. The "social dividend" is reframed as the "American Productivity
   Dividend" — infrastructure for entrepreneurship, not redistribution. Evaluate
   whether this framing is honest and whether it builds a broader coalition.

Structure your response exactly as follows:

## 1. CIRCUIT BREAKER — RESOLVED OR NOT?
YES (Mode 3 concern fully closed) / PARTIALLY / NO (concern remains)
One paragraph maximum. Be direct.

## 2. CONSERVATIVE FRAMING — HONEST AND EFFECTIVE?
Does the framing hold up to scrutiny? Is it honest about what the proposal does?
Does it expand the coalition without misrepresenting the instrument?
YES / PARTIALLY / NO + one paragraph.

## 3. CORPORATE SAVINGS — NUMBERS ACCURATE?
The brief claims Apple saves $33B, Amazon $16.5B, Walmart $17B (87% average reduction
across 5 major companies). Are these estimates credible? What caveat, if any, matters?

## 4. REMAINING CONCERNS
List ONLY concerns that are new or genuinely unresolved after five rounds.
If nothing remains, say so explicitly. Maximum three items, one sentence each.

## 5. LEGISLATIVE READINESS
Is this document ready to hand to a legislator?
READY / NEEDS ONE MORE REVISION / NOT READY
State specifically what "ready" means or what the one revision is.

## 6. SEVENTH GENERATION VERDICT — FINAL
IMPLEMENT / REDESIGN AGAIN / REJECT
This is your definitive verdict. Defend it in three sentences maximum.
No hedging. No "on one hand / on the other hand." A verdict."""


SYNTHESIS_PROMPT = """You are producing the final synthesis of five rounds of
cross-model evaluation of the American Productivity Tax Reform proposal.

{panel_analyses}

---

This is the definitive synthesis. Structure it as follows:

## RESOLVED: What the Five-Round Process Closed
Name the concerns from prior rounds that are now definitively resolved.
Be specific about which round resolved which concern.

## CIRCUIT BREAKER — PANEL VERDICT
Did the universal circuit breaker design fully resolve Mode 3?

## FRAMING — PANEL VERDICT
Does the conservative framing hold up? Does it expand the coalition?

## REMAINING OPEN ITEMS
Only items that multiple models identified as still unresolved.
If the panel is unanimous that nothing remains, say so.

## LEGISLATIVE READINESS — PANEL VERDICT
Is the proposal ready for legislative introduction?

## FINAL PANEL VERDICT
IMPLEMENT / REDESIGN AGAIN / REJECT

If IMPLEMENT: state the single most important risk legislators must watch.
If REDESIGN AGAIN: state the single change that would get to IMPLEMENT.
If REJECT: state the structural flaw that cannot be legislated away.

Close with one paragraph: what does the generation born in 2166 inherit from
this proposal, if implemented as written?"""


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
    print("  AMERICAN PRODUCTIVITY TAX REFORM — FINAL PANEL REVIEW")
    print("  Fifth round: circuit breaker + conservative framing + full math")
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
                "You are producing the final definitive synthesis of five rounds of "
                "cross-model evaluation. This is not a status update. It is a verdict. "
                "You give the panel's collective final judgment on whether the American "
                "Productivity Tax Reform is ready for legislative introduction. "
                "You are direct, specific, and conclusive. You do not hedge. "
                "You state what was resolved, what if anything remains, and what the "
                "generation born in 2166 inherits from this proposal."
            ),
            user_message=SYNTHESIS_PROMPT.format(panel_analyses=panel_text),
            max_tokens=4000,
            temperature=0.4,
            api_key=api_key,
        )
    except Exception as exc:
        synthesis = f"[Synthesis error: {exc}]"

    print(synthesis)

    LOGS_DIR.mkdir(exist_ok=True)
    ts       = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"crosscheck_v5_{ts}.json"
    log_path.write_text(
        json.dumps({
            "topic": "American Productivity Tax Reform — final panel review",
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
    print("[Review] Run build_final_brief_doc.py to generate the definitive docx.")


if __name__ == "__main__":
    main()
