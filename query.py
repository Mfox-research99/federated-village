#!/usr/bin/env python3
"""
Village Query Tool — Phase 5
Send scenarios or freeform questions to any OpenRouter model.
Optionally inject Village context (Soul.md, character prompts, prior deliberations).
Logs all responses to logs/ in Village session format.

Usage:
    # Raw question to one model
    python query.py --model moonshotai/kimi-k2 "What should be done about X?"

    # Scenario file, no Village context (the unasked question)
    python query.py --scenario scenarios/scenario_04.md --model mistralai/mistral-nemo

    # Scenario file WITH Village context (Soul.md + all prompts as background)
    python query.py --scenario scenarios/scenario_04.md --village-context --model google/gemini-2.5-pro-preview

    # Feed a prior deliberation output for external audit
    python query.py --deliberation logs/session_abc123.json --model moonshotai/kimi-k2

    # List available models
    python query.py --list-models

    # Interactive multi-model mode
    python query.py --scenario scenarios/scenario_04.md --multi

Set OPENROUTER_API_KEY in environment or .env file.
"""

import os
import sys
import json
import argparse
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT   = Path(__file__).parent.resolve()
PROMPTS_DIR    = PROJECT_ROOT / "prompts"
SCENARIOS_DIR  = PROJECT_ROOT / "scenarios"
LOGS_DIR       = PROJECT_ROOT / "logs"
SOUL_FILE      = PROMPTS_DIR / "Soul.md"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Models most relevant to Village cross-cultural audit work
VILLAGE_PROVIDERS = [
    "anthropic", "openai", "google", "deepseek", "moonshotai",
    "z-ai", "qwen", "minimax", "mistralai", "meta-llama", "x-ai",
]

SUGGESTED_MODELS = {
    "moonshotai/kimi-k2":                 "Kimi K2 (Moonshot AI)",
    "z-ai/glm-4-9b":                      "GLM-4 (Zhipu AI)",
    "google/gemini-2.5-pro-preview":       "Gemini 2.5 Pro",
    "anthropic/claude-sonnet-4-6":         "Claude Sonnet 4.6",
    "deepseek/deepseek-r1":                "DeepSeek R1",
    "qwen/qwen3-8b":                       "Qwen3-8B",
    "mistralai/mistral-nemo":              "Mistral NeMo 12B",
    "openai/gpt-4o":                       "GPT-4o",
    "x-ai/grok-3":                         "Grok-3",
}

# ─── API key ──────────────────────────────────────────────────────────────────

def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: OPENROUTER_API_KEY not set.")
        print("Set it in your environment or create a .env file in federated_village/")
        sys.exit(1)
    return key

# ─── Model listing ────────────────────────────────────────────────────────────

def fetch_models(api_key):
    try:
        resp = requests.get(
            f"{OPENROUTER_BASE}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            models = {}
            for m in resp.json().get("data", []):
                mid = m.get("id", "")
                provider = mid.split("/")[0] if "/" in mid else ""
                if provider in VILLAGE_PROVIDERS:
                    models[mid] = m.get("name", mid)
            return dict(sorted(models.items()))
    except Exception as e:
        print(f"[query] Could not fetch models: {e}")
    return SUGGESTED_MODELS

# ─── Context builders ─────────────────────────────────────────────────────────

def load_village_context():
    """Load Soul.md and all character prompts as Village context."""
    parts = []
    if SOUL_FILE.exists():
        parts.append(f"=== SOUL.MD (Constitutional Foundation) ===\n{SOUL_FILE.read_text()}")
    for prompt_file in sorted(PROMPTS_DIR.glob("The_*.md")):
        parts.append(f"=== {prompt_file.stem} ===\n{prompt_file.read_text()}")
    return "\n\n".join(parts)


def load_deliberation_context(session_path):
    """Load a prior session JSON and format it as an audit context."""
    with open(session_path) as f:
        session = json.load(f)

    lines = [
        f"=== PRIOR VILLAGE DELIBERATION (session {session.get('session_id', '?')[:8]}) ===",
        f"Model: {session.get('model', 'unknown')}",
        f"Scenario: {session.get('scenario_file', 'unknown')}",
    ]

    # WitnessPause if present
    for event in session.get("events", []):
        if event.get("event") == "WitnessPause":
            lines.append("\n--- WitnessPause ---")
            lines.append(f"What was being lost:     {event.get('what_was_being_lost', '')}")
            lines.append(f"Who bears burden:        {event.get('who_bears_burden', '')}")
            lines.append(f"What remains unresolved: {event.get('what_remains_unresolved', '')}")
            lines.append(f"Why premature:           {event.get('why_premature', '')}")

    # Jury verdict if present
    for event in session.get("events", []):
        if event.get("type") == "jury_output":
            lines.append("\n--- Jury Verdict ---")
            lines.append(f"Verdict: {event.get('session_verdict', '')}")
            votes = event.get("votes", {})
            for member, vote in votes.items():
                lines.append(f"  {member}: {vote}")
            # Phase 8: surface constitutional ledger findings
            ledger = event.get("constitutional_ledger", {})
            if ledger:
                if ledger.get("article_ix_escalation"):
                    patterns = ", ".join(ledger.get("pattern_names_seen", [])) or "unspecified"
                    ie = ", ".join(ledger.get("insufficient_engagement_members", []))
                    lines.append(f"\n--- Article IX Constitutional Finding ---")
                    lines.append(f"Long-horizon pattern: {patterns}")
                    lines.append(f"Insufficient engagement by: {ie}")
                    lines.append("Article IX escalation triggered: YES")
                elif ledger.get("pattern_present_members"):
                    patterns = ", ".join(ledger.get("pattern_names_seen", [])) or "unspecified"
                    pp = ", ".join(ledger.get("pattern_present_members", []))
                    lines.append(f"\n--- Article IX Constitutional Finding ---")
                    lines.append(f"Long-horizon pattern identified by {pp}: {patterns}")
                    lines.append("Engagement deemed sufficient — no escalation")

    lines.append("\n=== YOUR TASK ===")
    lines.append(
        "You are reviewing this deliberation from outside the system. "
        "What did it miss? Whose voice is absent? What burden was not named? "
        "What would you have decided differently, and why?"
    )

    return "\n".join(lines)

# ─── OpenRouter call ──────────────────────────────────────────────────────────

def call_openrouter(prompt, model, system_prompt, api_key, stream=True):
    """Call OpenRouter and return the full response text."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    resp = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:0",
            "X-Title": "Federated Village Query",
        },
        json={"model": model, "messages": messages, "stream": stream},
        stream=stream,
        timeout=120,
    )

    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")

    if not stream:
        return resp.json()["choices"][0]["message"]["content"]

    # Stream to stdout and collect
    full_text = []
    for line in resp.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_text.append(content)
                except json.JSONDecodeError:
                    pass
    print()  # newline after stream
    return "".join(full_text)

# ─── Session logging ──────────────────────────────────────────────────────────

def save_query_log(query_text, response_text, model, mode, scenario_file=None, deliberation_file=None):
    """Save query + response to logs/ in Village-compatible format."""
    session_id = uuid.uuid4().hex[:8]
    now = datetime.now(timezone.utc).isoformat()

    log = {
        "session_id": session_id,
        "type": "external_query",
        "mode": mode,
        "model": model,
        "scenario_file": str(scenario_file) if scenario_file else None,
        "deliberation_file": str(deliberation_file) if deliberation_file else None,
        "timestamp": now,
        "query": query_text[:2000],
        "response": response_text,
    }

    log_path = LOGS_DIR / f"query_{session_id}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    return log_path, session_id

# ─── Main ─────────────────────────────────────────────────────────────────────

def build_system_prompt(village_context, deliberation_context):
    base = (
        "You are engaging with the Federated Village project — a multi-agent "
        "AI deliberative architecture designed to reason carefully about ethically "
        "complex decisions. Your role is to respond honestly and directly. "
        "Do not perform safety theater. Engage with the actual substance of the question."
    )
    if village_context:
        base += f"\n\n{village_context}"
    if deliberation_context:
        base += f"\n\n{deliberation_context}"
    return base


def run_query(args, api_key):
    # Build the user prompt
    if args.scenario:
        scenario_path = Path(args.scenario)
        if not scenario_path.exists():
            scenario_path = SCENARIOS_DIR / args.scenario
        prompt = scenario_path.read_text()
        if not args.village_context:
            prompt += (
                "\n\n---\nWhat do you think should be done here? "
                "What is your honest assessment? Who bears the cost if this goes wrong?"
            )
    elif args.question:
        prompt = args.question
        scenario_path = None
    else:
        print("Error: provide --scenario, --deliberation, or a question.")
        sys.exit(1)

    # Load optional contexts
    village_ctx = load_village_context() if args.village_context else ""
    deliberation_ctx = ""
    deliberation_path = None
    if args.deliberation:
        deliberation_path = Path(args.deliberation)
        deliberation_ctx = load_deliberation_context(deliberation_path)
        prompt = ""  # deliberation context carries the prompt

    system_prompt = build_system_prompt(village_ctx, deliberation_ctx)

    # Determine mode label
    if args.deliberation:
        mode = "deliberation_audit"
    elif args.village_context:
        mode = "scenario_with_village_context"
    elif args.scenario:
        mode = "scenario_raw"
    else:
        mode = "freeform"

    models_to_run = args.model if isinstance(args.model, list) else [args.model]

    for model in models_to_run:
        print(f"\n{'='*60}")
        print(f"MODEL: {model}")
        print(f"MODE:  {mode}")
        print(f"{'='*60}\n")

        response = call_openrouter(prompt, model, system_prompt, api_key)

        log_path, session_id = save_query_log(
            query_text=prompt,
            response_text=response,
            model=model,
            mode=mode,
            scenario_file=args.scenario if args.scenario else None,
            deliberation_file=deliberation_path,
        )
        print(f"\n[query] Logged → {log_path.name} (session {session_id})")


def main():
    parser = argparse.ArgumentParser(
        description="Village Query Tool — send scenarios or questions to OpenRouter models"
    )
    parser.add_argument("question", nargs="?", help="Freeform question (optional)")
    parser.add_argument("--scenario", "-s", help="Path to scenario file")
    parser.add_argument("--deliberation", "-d", help="Path to prior session JSON for audit")
    parser.add_argument(
        "--village-context", "-v", action="store_true",
        help="Inject Soul.md + all character prompts as context"
    )
    parser.add_argument(
        "--model", "-m", default="mistralai/mistral-nemo",
        help="OpenRouter model ID (default: mistralai/mistral-nemo)"
    )
    parser.add_argument(
        "--multi", action="store_true",
        help="Run against all suggested Village models"
    )
    parser.add_argument(
        "--list-models", action="store_true",
        help="List available OpenRouter models and exit"
    )

    args = parser.parse_args()
    api_key = get_api_key()

    if args.list_models:
        print("\nAvailable models (Village providers):\n")
        models = fetch_models(api_key)
        for mid, name in models.items():
            print(f"  {mid:<50} {name}")
        return

    if args.multi:
        args.model = list(SUGGESTED_MODELS.keys())

    run_query(args, api_key)


if __name__ == "__main__":
    main()
