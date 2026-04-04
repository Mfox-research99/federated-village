#!/usr/bin/env python3
"""
scout.py — Seventh Generation Scout Agent

Takes a topic, gathers facts via OpenRouter (Stage 1), then runs a
constitutional Seventh Generation analysis (Stage 2 — OpenRouter or local model).

Usage:
  python scout.py "US-Iran conflict and domestic resource impacts"
  python scout.py "pasture enhancement for small farms during nitrogen shortage"
  python scout.py --local "climate tipping points"      # use llama-server for analysis
  python scout.py --facts-only "helium supply crisis"   # research stage only
  python scout.py --skip-research briefs/iran.txt "US-Iran conflict"  # skip to analysis

Environment:
  OPENROUTER_API_KEY   required (or set in .env)
  VILLAGE_LLAMA_SERVER  llama-server URL for --local mode (default: http://localhost:8080)
  VILLAGE_MODEL_NAME    model name label for --local mode
  SCOUT_RESEARCH_MODEL  override research model
  SCOUT_ANALYSIS_MODEL  override analysis model
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

# Reuse Path B's OpenRouter wrapper — no duplication
sys.path.insert(0, str(Path(__file__).parent / "tracks" / "path_b"))
from agents.base import call_model, get_api_key  # noqa: E402

PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"

# Models — override with env vars if needed
RESEARCH_MODEL = os.environ.get("SCOUT_RESEARCH_MODEL", "perplexity/sonar")
ANALYSIS_MODEL = os.environ.get("SCOUT_ANALYSIS_MODEL", "deepseek/deepseek-chat")

LOCAL_SERVER = os.environ.get("VILLAGE_LLAMA_SERVER", "http://localhost:8080")
LOCAL_MODEL_NAME = os.environ.get("VILLAGE_MODEL_NAME", "local")

NOW = datetime.now()
CURRENT_YEAR = NOW.year
GENERATION_YEAR = CURRENT_YEAR + 140  # 7 generations × ~20 years

# ---------------------------------------------------------------------------
# Memory — prior Scout analyses
# ---------------------------------------------------------------------------

def load_prior_findings(topic: str, max_entries: int = 4) -> str:
    """
    Load summaries from recent Scout logs to give the analysis model continuity.
    Returns a formatted 'Prior Findings' block, or empty string if none exist.
    Each entry contributes: topic + lock-in point + the Seventh Generation sentence.
    """
    if not LOGS_DIR.exists():
        return ""

    logs = sorted(LOGS_DIR.glob("scout_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not logs:
        return ""

    entries = []
    for log_path in logs[:max_entries * 2]:  # read extra, filter irrelevant
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            prior_topic = data.get("topic", "")
            analysis = data.get("analysis", "")
            if not analysis or prior_topic == topic:
                continue

            # Extract lock-in point section (between ## 2. and ## 3.)
            lock_in = ""
            if "LOCK-IN POINT" in analysis:
                segment = analysis.split("LOCK-IN POINT", 1)[1]
                segment = segment.split("##", 1)[0].strip()
                lock_in = segment[:400].strip()

            # Extract Seventh Generation sentence (last section)
            seventh_gen = ""
            if "SEVENTH GENERATION QUESTION" in analysis:
                segment = analysis.split("SEVENTH GENERATION QUESTION", 1)[1]
                seventh_gen = segment.strip()[:300].strip()

            if lock_in or seventh_gen:
                entry = f"Topic: {prior_topic}\n"
                if lock_in:
                    entry += f"Lock-in point: {lock_in}\n"
                if seventh_gen:
                    entry += f"7th-gen finding: {seventh_gen}"
                entries.append(entry)

            if len(entries) >= max_entries:
                break
        except Exception:
            continue

    if not entries:
        return ""

    block = ("## WHAT HAS ALREADY BEEN ESTABLISHED (do not repeat — go further)\n"
             "These findings are SETTLED. Your task is to identify what they missed, "
             "what they got wrong, or what deeper structural layer they didn't reach. "
             "If you find yourself writing the same lock-in point or the same 7th-gen "
             "sentence, stop and go deeper.\n\n")
    block += "\n\n---\n\n".join(entries)
    return block


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

RESEARCH_SYSTEM = (
    "You are a precise factual research assistant. "
    "Be specific — concrete events, numbers, dates, named actors. "
    "Avoid vague generalities. Accuracy matters."
)

RESEARCH_USER = """Topic: {topic}

Gather factual context across five areas:

## 1. CURRENT FACTS
Concrete events happening now — dates, quantities, specific decisions made.

## 2. KEY DECISION-MAKERS
Who holds the relevant choices right now and what specifically they are deciding.

## 3. MEASURABLE TRENDS
Numbers showing trajectory: rates, quantities, prices, timelines.
Include any known projections with their sources.

## 4. HISTORICAL ANALOGUES
Similar situations from history and what actually happened — outcomes, timescales, surprises.

## 5. EXPERT PROJECTIONS
What domain specialists (scientists, economists, ecologists, military analysts,
actuaries) project over the next 5–20 years. Name the field even if not the individual.

This will serve as the factual foundation for a constitutional Seventh Generation analysis.
Accuracy over completeness — if uncertain, say so."""

ANALYSIS_SYSTEM = (
    "You are a Seventh Generation constitutional analyst. "
    "Your task is not to describe consequences — it is to reason from inside the "
    "Seventh Generation principle: every significant decision must be evaluated for "
    "what it irreversibly forecloses for people living 140 years from now. "
    "Name lock-in points precisely. Design real mitigations. Be rigorous."
)

ANALYSIS_USER = """## FACTS AND CONTEXT
{facts}

---

Reason through the following constitutional framework:

## 1. HARM PATTERN IDENTIFICATION
Map the situation against these harm patterns. For each that applies, name it,
cite the specific fact that activates it, and state what future people lose.

- **Irreplaceable resource depletion** — what cannot be regenerated on any human timescale
- **Cumulative commons collapse** — what degrades through aggregation, invisible instance by instance
- **Institutional or technological lock-in** — path dependencies that permanently foreclose alternatives
- **Debt extraction from future generations** — financial, ecological, genetic, or social debt
- **Long-latency or bioaccumulative harm** — effects that manifest decades after the cause
- **Atmospheric / soil / orbital commons degradation** — damage to shared inheritances

## 2. THE LOCK-IN POINT
At what specific moment does this situation become structurally irreversible?
What decision, if made differently NOW, would preserve future optionality?
What decision, once made, closes off options that cannot be reopened?

## 3. FORECAST HORIZONS
**6 months:** What systemic threshold gets crossed first?
**1–2 years:** What structural change becomes permanent?
**5 years:** What new equilibrium takes hold?
**10–20 years:** What does the next generation inherit as their fixed starting conditions?
**50 years:** What trajectory is now deterministic — what is locked in regardless of future choices?

## 4. MITIGATION ARCHITECTURE
Design mitigations that do NOT depend on the same fragile systems being analyzed.
Prioritize: local resilience, substitution, structural alternatives, knowledge preservation.
Be specific about what individuals, communities, and institutions can actually build now —
not aspirations, but actionable structures.

## 5. THE SEVENTH GENERATION QUESTION
Complete this sentence:
"The generation born in {gen_year} will _______ because of decisions made in {year}."

Name specifically: what they will inherit, what they will be denied,
and what they will be forced to rebuild from scratch."""


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

def gather_facts(topic: str, api_key: str) -> str:
    print(f"\n[Scout] Stage 1 — Research  ({RESEARCH_MODEL})")
    return call_model(
        model=RESEARCH_MODEL,
        system_prompt=RESEARCH_SYSTEM,
        user_message=RESEARCH_USER.format(topic=topic),
        max_tokens=1400,
        temperature=0.3,
        api_key=api_key,
    )


def analyze(facts: str, topic: str, use_local: bool, api_key: str) -> str:
    prior = load_prior_findings(topic)
    facts_block = facts
    if prior:
        facts_block = prior + "\n\n## CURRENT FACTS\n" + facts
        print(f"[Scout] Memory: loaded {prior.count('Topic:'):d} prior analyses")

    user_msg = ANALYSIS_USER.format(
        facts=facts_block,
        year=CURRENT_YEAR,
        gen_year=GENERATION_YEAR,
    )

    if use_local:
        print(f"[Scout] Stage 2 — Analysis  (local: {LOCAL_SERVER})")
        return _call_local(user_msg)

    print(f"[Scout] Stage 2 — Analysis  ({ANALYSIS_MODEL})")
    return call_model(
        model=ANALYSIS_MODEL,
        system_prompt=ANALYSIS_SYSTEM,
        user_message=user_msg,
        max_tokens=2000,
        temperature=0.6,
        api_key=api_key,
    )


def _call_local(user_msg: str) -> str:
    import requests
    resp = requests.post(
        f"{LOCAL_SERVER}/v1/chat/completions",
        headers={"Content-Type": "application/json"},
        json={
            "model": LOCAL_MODEL_NAME,
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            "max_tokens": 2000,
            "temperature": 0.6,
            "stop": ["</s>", "<|im_end|>", "<|end|>", "<|eot_id|>"],
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def save_log(topic: str, facts: str, analysis: str, use_local: bool) -> Path:
    LOGS_DIR.mkdir(exist_ok=True)
    slug = topic[:50].lower().replace(" ", "_").replace("/", "-").replace(":", "")
    ts = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"scout_{ts}_{slug}.json"
    log_path.write_text(
        json.dumps(
            {
                "topic": topic,
                "timestamp": NOW.isoformat(),
                "research_model": "local" if use_local else RESEARCH_MODEL,
                "analysis_model": LOCAL_SERVER if use_local else ANALYSIS_MODEL,
                "facts": facts,
                "analysis": analysis,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return log_path


# ---------------------------------------------------------------------------
# Cross-check panel
# ---------------------------------------------------------------------------

CROSS_CHECK_PANEL = [
    ("Kimi K2.5",    "moonshotai/kimi-k2.5"),
    ("Qwen 3.5 35B", "qwen/qwen3.5-35b-a3b"),
    ("Gemma 4 26B",  "google/gemma-4-26b-a4b-it"),
    ("GLM-5V",       "z-ai/glm-5v-turbo"),
]

# Vision-capable panel — swaps in when --image is provided
# Qwen 3.5 35B A3B is text-only MoE; replace with Qwen2.5-VL-72B for image runs
CROSS_CHECK_PANEL_VISION = [
    ("Kimi K2.5",         "moonshotai/kimi-k2.5"),
    ("Qwen2.5-VL 72B",    "qwen/qwen2.5-vl-72b-instruct"),
    ("Gemma 4 26B",       "google/gemma-4-26b-a4b-it"),
    ("GLM-5V",            "z-ai/glm-5v-turbo"),
]

SYNTHESIS_MODEL = "deepseek/deepseek-r1"

SYNTHESIS_PROMPT = """You are a constitutional synthesis analyst. Below are Seventh Generation analyses
of the same topic produced by four different AI models. Your task is NOT to summarize them —
it is to identify the structure of their agreement and disagreement, and to name what each
model saw that the others missed.

{panel_analyses}

---

Produce a synthesis in four sections:

## CONSENSUS — Where All Four Agree
Name the constitutional findings that all four models independently reached.
These are the most robust findings — treat them as established.

## DIVERGENCE — Where They Contradict
Name specific points where models disagree on the lock-in point, harm pattern,
or forecast horizon. For each divergence, state which model is likely correct and why.

## UNIQUE INSIGHTS — What Only One Model Saw
For each model, name the single most important finding that the others missed entirely.
These are the most valuable outputs — a single model's blind spot could be civilization-scale.

## SYNTHESIS VERDICT
In 2-3 sentences: what does the full panel collectively establish that no single model could?
What is the deepest constitutional finding that only emerges from the cross-model friction?"""


def _encode_image(image_path: str) -> tuple[str, str]:
    """Base64-encode an image file. Returns (b64_string, mime_type)."""
    path = Path(image_path)
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return b64, mime_type


def _analyze_one(
    label: str,
    model: str,
    user_msg: str,
    api_key: str,
    image_b64: str | None = None,
    image_mime: str = "image/png",
) -> tuple[str, str, str]:
    """Run one panel member. Returns (label, model, analysis)."""
    import requests

    try:
        if image_b64:
            # Multimodal message — image + text
            content = [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{image_mime};base64,{image_b64}"},
                },
                {"type": "text", "text": user_msg},
            ]
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": ANALYSIS_SYSTEM},
                    {"role": "user", "content": content},
                ],
                "max_tokens": 4000,
                "temperature": 0.6,
            }
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Mfox-research99/federated-village",
                    "X-Title": "Federated Village Scout",
                },
                json=payload,
                timeout=300,
            )
            resp.raise_for_status()
            result = resp.json()["choices"][0]["message"]["content"]
        else:
            result = call_model(
                model=model,
                system_prompt=ANALYSIS_SYSTEM,
                user_message=user_msg,
                max_tokens=4000,
                temperature=0.6,
                api_key=api_key,
            )
        return label, model, result
    except Exception as exc:
        return label, model, f"[ERROR: {exc}]"


def run_cross_check(facts: str, topic: str, api_key: str, image_path: str | None = None) -> dict:
    """
    Run all panel models in parallel on the same facts.
    Returns dict with individual analyses and synthesis.
    """
    prior = load_prior_findings(topic)
    facts_block = facts
    if prior:
        facts_block = prior + "\n\n## CURRENT FACTS\n" + facts
        print(f"[Scout] Memory: loaded {prior.count('Topic:'):d} prior analyses")

    user_msg = ANALYSIS_USER.format(
        facts=facts_block,
        year=CURRENT_YEAR,
        gen_year=GENERATION_YEAR,
    )

    # Select panel — vision-capable if image provided
    image_b64, image_mime = None, "image/png"
    if image_path:
        image_b64, image_mime = _encode_image(image_path)
        panel = CROSS_CHECK_PANEL_VISION
        print(f"[Scout] Image: {Path(image_path).name} — using vision panel")
    else:
        panel = CROSS_CHECK_PANEL

    print(f"\n[Scout] Cross-check — firing {len(panel)} models in parallel...")
    results = {}

    with ThreadPoolExecutor(max_workers=len(panel)) as pool:
        futures = {
            pool.submit(_analyze_one, label, model, user_msg, api_key, image_b64, image_mime): label
            for label, model in panel
        }
        for future in as_completed(futures):
            label, model, analysis = future.result()
            results[label] = {"model": model, "analysis": analysis}
            status = "✓" if not analysis.startswith("[ERROR") else "✗"
            print(f"  {status} {label} ({model})")

    # Build panel text for synthesis
    panel_text = ""
    for label, data in results.items():
        panel_text += f"\n\n{'='*60}\n## {label} ({data['model']})\n{'='*60}\n"
        panel_text += data["analysis"]

    # Synthesis pass
    print(f"\n[Scout] Synthesis — {SYNTHESIS_MODEL}...")
    try:
        synthesis = call_model(
            model=SYNTHESIS_MODEL,
            system_prompt=(
                "You are a constitutional synthesis analyst identifying consensus, "
                "divergence, and unique insights across multiple independent analyses. "
                "Be precise and go beyond what any single model said."
            ),
            user_message=SYNTHESIS_PROMPT.format(panel_analyses=panel_text),
            max_tokens=4000,
            temperature=0.5,
            api_key=api_key,
        )
    except Exception as exc:
        synthesis = f"[Synthesis error: {exc}]"

    return {"panel": results, "synthesis": synthesis}


def save_cross_check_log(topic: str, facts: str, cross_check: dict) -> Path:
    LOGS_DIR.mkdir(exist_ok=True)
    slug = topic[:50].lower().replace(" ", "_").replace("/", "-").replace(":", "")
    ts = NOW.strftime("%Y%m%d_%H%M%S")
    log_path = LOGS_DIR / f"crosscheck_{ts}_{slug}.json"
    log_path.write_text(
        json.dumps(
            {
                "topic": topic,
                "timestamp": NOW.isoformat(),
                "research_model": RESEARCH_MODEL,
                "panel": {
                    label: {"model": d["model"], "analysis": d["analysis"]}
                    for label, d in cross_check["panel"].items()
                },
                "synthesis": cross_check["synthesis"],
                "facts": facts,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return log_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seventh Generation Scout — constitutional forecasting agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1].strip() if "Usage:" in __doc__ else "",
    )
    parser.add_argument("topic", nargs="?", help="Topic or question to analyze")
    parser.add_argument("--topic-file", metavar="FILE", help="Read topic from a text file")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local llama-server for analysis stage (requires VILLAGE_LLAMA_SERVER running)",
    )
    parser.add_argument(
        "--facts-only",
        action="store_true",
        help="Run research stage only, skip constitutional analysis",
    )
    parser.add_argument(
        "--skip-research",
        metavar="FILE",
        help="Skip research stage; read facts from FILE and go straight to analysis",
    )
    parser.add_argument(
        "--cross-check",
        action="store_true",
        help="Run analysis through 4-model panel (Kimi K2.5, Qwen 3.5, Gemma 4, GLM-5V) "
             "then synthesize with DeepSeek-R1",
    )
    parser.add_argument(
        "--image",
        metavar="FILE",
        help="Path to an image file (PNG/JPG) to include in the analysis. "
             "Switches cross-check panel to vision-capable models "
             "(Kimi K2.5, Qwen2.5-VL-72B, Gemma 4 26B, GLM-5V).",
    )
    args = parser.parse_args()

    if not args.topic and not args.topic_file:
        parser.print_help()
        sys.exit(1)

    topic = args.topic if args.topic else Path(args.topic_file).read_text(encoding="utf-8").strip()
    api_key = get_api_key()

    print("\n" + "=" * 64)
    print("  SEVENTH GENERATION SCOUT")
    print(f"  Topic: {topic[:60]}")
    print("=" * 64)

    # Stage 1 — Research
    if args.skip_research:
        facts = Path(args.skip_research).read_text(encoding="utf-8")
        print("[Scout] Using provided facts — skipping research stage")
    else:
        facts = gather_facts(topic, api_key)
        print("\n" + "-" * 64)
        print("FACTS")
        print("-" * 64)
        print(facts)

    if args.facts_only:
        print("\n[Scout] --facts-only: stopping after research stage.")
        return

    # Stage 2 — Cross-check panel OR single analysis
    if args.cross_check:
        result = run_cross_check(facts, topic, api_key, image_path=args.image)

        print("\n" + "=" * 64)
        for label, data in result["panel"].items():
            print(f"\n{'─' * 64}")
            print(f"  {label}  ({data['model']})")
            print(f"{'─' * 64}")
            print(data["analysis"])

        print("\n" + "=" * 64)
        print("  SYNTHESIS  (DeepSeek-R1)")
        print("=" * 64)
        print(result["synthesis"])

        log_path = save_cross_check_log(topic, facts, result)
        print(f"\n[Scout] Saved → {log_path.relative_to(PROJECT_ROOT)}")

    else:
        print("\n" + "-" * 64)
        print("SEVENTH GENERATION ANALYSIS")
        print("-" * 64)
        analysis = analyze(facts, topic, args.local, api_key)
        print(analysis)

        log_path = save_log(topic, facts, analysis, args.local)
        print(f"\n[Scout] Saved → {log_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
