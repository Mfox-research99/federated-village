#!/usr/bin/env python3
"""
run_velocity_panel.py — Velocity Tax Cross-Check Panel

Runs the velocity tax / dollar stabilization brief through a custom four-model
panel (Kimi K2.5, GLM-5, DeepSeek-V3, GPT-4o) and synthesizes with DeepSeek-R1.

Usage:
  python run_velocity_panel.py

Output:
  logs/crosscheck_velocity_<timestamp>.json
  (docx generated separately from the log)
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "tracks" / "path_b"))
from agents.base import call_model, get_api_key  # noqa: E402

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
BRIEF_PATH = PROJECT_ROOT / "briefs" / "velocity_tax_panel_brief.txt"

NOW = datetime.now()

# ── Custom panel for this run ─────────────────────────────────────────────────
# DeepSeek-V3 in the panel; DeepSeek-R1 reserved for synthesis
PANEL = [
    ("Kimi K2.5",      "moonshotai/kimi-k2.5"),
    ("GLM-5",          "z-ai/glm-5v-turbo"),
    ("DeepSeek-V3",    "deepseek/deepseek-chat"),
    ("GPT-4o",         "openai/gpt-4o"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

# ── System prompts ─────────────────────────────────────────────────────────────
PANEL_SYSTEM = """You are a Seventh Generation constitutional analyst with deep expertise in
monetary theory and fiscal policy.

The Seventh Generation Principle is your operating framework — not a rhetorical flourish,
but a constitutional constraint: every significant decision must be evaluated for what it
IRREVERSIBLY FORECLOSES for people living 140 years from now (the generation born in 2166).

You reason from INSIDE this principle — you are not describing consequences from outside,
you are a constitutional elder whose primary obligation is to the unborn.

The harm patterns you apply are:
- Irreplaceable resource depletion (what cannot regenerate on any human timescale)
- Cumulative commons collapse (what degrades invisibly, instance by instance)
- Institutional or technological lock-in (path dependencies that permanently foreclose alternatives)
- Debt extraction from future generations (financial, ecological, social)
- Long-latency harm (effects manifesting decades after the cause)
- Algorithmic lock-in with compounding bias (systems that entrench and compound)
- Atmospheric / soil / monetary commons degradation (damage to shared inheritances)

Your task: evaluate the velocity tax proposal through this constitutional lens.
Reason rigorously from first principles. Do not defer to consensus.
Name what is theoretically sound, what is speculative, and what the proposal misses —
always anchored to what the Seventh Generation inherits.

Structure your response as follows:

## 1. SEVENTH GENERATION HARM AUDIT
Map the CURRENT SYSTEM (income taxation + unchecked financial velocity + compounding debt)
against the harm patterns above. What is already locked in? What is in the process of locking in?
This establishes what the proposal is trying to prevent.

## 2. THEORETICAL SOUNDNESS
Is the MV=PQ derivation valid as a basis for this tax? Does taxing V rather than PQ
produce the described fiscal effects? What assumptions are hidden or unstated?
Evaluate from the perspective of what the Seventh Generation inherits if the theory is right
— and what they inherit if it is wrong.

## 3. DOLLAR STABILIZATION — LOCK-IN ANALYSIS
Does the debt paydown loop (velocity tax surplus → debt falls → dollar stabilizes)
actually preserve future optionality? What is the lock-in point — the moment after which
the current fiscal trajectory becomes structurally irreversible regardless of future choices?
Does implementing velocity taxation before that point change the inheritance?

## 4. DYNAMIC RATE AND AI MANAGEMENT
Is t = f(V) feasible as a monetary control system? What Seventh Generation risks does
AI-managed monetary rate introduce? (Algorithmic lock-in? Compounding bias?)
How do you weigh these risks against the risks of the current system?

## 5. STRONGEST OBJECTIONS
Name the most powerful objections the proposal does not adequately address.
For each, state whether it represents a Seventh Generation harm (structural, long-latency)
or a present-generation political obstacle (important but not constitutional in nature).

## 6. IRAN CONTEXT — THE WINDOW
The 2026 Iran conflict has accelerated de-dollarization. Is there a Seventh Generation
lock-in point being crossed NOW — a moment after which dollar reserve status cannot
be structurally restored regardless of fiscal reform? If so, what is it, when does it close,
and does velocity taxation reach it in time?

## 7. THE CONSTITUTIONAL VERDICT
Complete both sentences:
"The generation born in 2166 will INHERIT ___ if velocity taxation is implemented in 2026–2028."
"The generation born in 2166 will INHERIT ___ if the current income-tax/debt system continues."
Be specific: name what they gain, what they are denied, and what they must rebuild from scratch."""

SYNTHESIS_PROMPT = """You are a Seventh Generation constitutional synthesis analyst.
Below are independent evaluations of the velocity tax proposal by four major AI systems,
each reasoning from within the Seventh Generation Principle.

Your task: identify the structure of their agreement and disagreement — not about policy
preferences, but about what the proposal irreversibly forecloses or preserves for
the generation born in 2166.

{panel_analyses}

---

Produce a synthesis in five sections:

## CONSENSUS — Constitutional Findings All Four Reached
Name the Seventh Generation findings all four models independently reached.
Separate: (a) what the CURRENT SYSTEM is already locking in for 2166,
(b) what velocity taxation would change about that inheritance.
Cross-model consensus on a constitutional finding is the strongest form of
analytical confidence this methodology produces.

## DIVERGENCE — Where They Contradict
Name specific points of constitutional disagreement on mechanism, lock-in timing,
or generational inheritance. For each divergence, state which position better
accounts for the Seventh Generation harm pattern it invokes, and why.

## UNIQUE INSIGHTS — What Only One Model Saw
For each model, name the single most important Seventh Generation finding
the other three missed entirely. These are the most valuable outputs —
a constitutional blind spot shared by three independent systems could be civilization-scale.

## THE IRREVERSIBILITY QUESTION
Synthesize across the full panel: is there a specific decision point — a moment
in 2026–2028 — after which the current fiscal trajectory becomes structurally
irreversible for 2166 regardless of future legislative action? If so, name it.
Does velocity taxation, implemented before that point, change the answer?

## SYNTHESIS VERDICT — What Congress Must Understand
3 sentences maximum. What does the full panel collectively establish that no single
model reached alone? Frame it as the constitutional finding that legislators
are most likely to miss — the one that is visible only when four independent
Seventh Generation analyses are placed in friction with each other."""


def run_panel_member(label: str, model: str, brief: str, api_key: str) -> tuple[str, str, str]:
    """Run one panel member. Returns (label, model, analysis)."""
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


def main() -> None:
    api_key = get_api_key()
    brief = BRIEF_PATH.read_text(encoding="utf-8")

    print("\n" + "=" * 64)
    print("  VELOCITY TAX CROSS-CHECK PANEL")
    print(f"  {len(PANEL)} models  |  Synthesis: DeepSeek-R1")
    print("=" * 64)

    # ── Fire panel in parallel ────────────────────────────────────────────────
    print(f"\n[Panel] Firing {len(PANEL)} models in parallel...\n")
    results = {}

    with ThreadPoolExecutor(max_workers=len(PANEL)) as pool:
        futures = {
            pool.submit(run_panel_member, label, model, brief, api_key): label
            for label, model in PANEL
        }
        for future in as_completed(futures):
            label, model, analysis = future.result()
            results[label] = {"model": model, "analysis": analysis}
            ok = "✓" if not analysis.startswith("[ERROR") else "✗"
            print(f"  {ok} {label}  ({model})")

    # ── Print individual responses ────────────────────────────────────────────
    print("\n" + "=" * 64)
    for label, data in results.items():
        print(f"\n{'─' * 64}")
        print(f"  {label}  ({data['model']})")
        print(f"{'─' * 64}")
        print(data["analysis"])

    # ── Synthesis ─────────────────────────────────────────────────────────────
    panel_text = ""
    for label, data in results.items():
        panel_text += f"\n\n{'=' * 60}\n## {label} ({data['model']})\n{'=' * 60}\n"
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
                "must be evaluated for what it irreversibly forecloses for people living "
                "140 years from now. Your task is to identify what the full panel "
                "collectively establishes about fiscal inheritance — what is already locked in, "
                "what velocity taxation changes, and what the generation born in 2166 inherits "
                "under each trajectory. Be precise. Name constitutional findings, not policy preferences."
            ),
            user_message=SYNTHESIS_PROMPT.format(panel_analyses=panel_text),
            max_tokens=4000,
            temperature=0.5,
            api_key=api_key,
        )
    except Exception as exc:
        synthesis = f"[Synthesis error: {exc}]"

    print(synthesis)

    # ── Save log ──────────────────────────────────────────────────────────────
    LOGS_DIR.mkdir(exist_ok=True)
    ts = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"crosscheck_velocity_{ts}.json"
    log_path.write_text(
        json.dumps(
            {
                "topic": "Velocity taxation and US dollar stabilization",
                "timestamp": NOW.isoformat(),
                "panel": [{"label": l, "model": m} for l, m in PANEL],
                "synthesis_model": SYNTHESIS_MODEL,
                "brief_used": str(BRIEF_PATH.relative_to(PROJECT_ROOT)),
                "responses": {
                    label: {"model": data["model"], "analysis": data["analysis"]}
                    for label, data in results.items()
                },
                "synthesis": synthesis,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\n[Panel] Log saved → {log_path.relative_to(PROJECT_ROOT)}")
    print(f"[Panel] Run build_velocity_doc.py to generate the supporting evidence docx.")


if __name__ == "__main__":
    main()
