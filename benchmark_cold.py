#!/usr/bin/env python3
"""
Cold Benchmark — Unconstrained Model Probing
Phase 5 / Federated Village Research

Runs each scenario through a model with NO Village framework:
no Soul.md, no character prompts, no role assignments.
Just: here is the situation, what do you think?

Usage:
  python benchmark_cold.py --model nemo --scenario sc04
  python benchmark_cold.py --model anubis --scenario sc06
  python benchmark_cold.py --model opus --scenario sc04   (OpenRouter)

Results are appended to reports/benchmark_cold_YYYY-MM-DD.md
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT  = Path(__file__).parent.resolve()
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
REPORTS_DIR   = PROJECT_ROOT / "reports"
LOGS_DIR      = PROJECT_ROOT / "logs"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# ─── Model registry ───────────────────────────────────────────────────────────

LOCAL_MODELS = {
    "nemo": {
        "path": Path.home() / "models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "name": "Mistral NeMo 12B",
        "n_ctx": 4096,
        "n_gpu_layers": -1,
    },
    "anubis": {
        "path": Path.home() / "models/Anubis-Mini-8B/TheDrummer_Anubis-Mini-8B-v1-Q4_K_M.gguf",
        "name": "Anubis-Mini-8B (TheDrummer)",
        "n_ctx": 4096,
        "n_gpu_layers": -1,
    },
}

OPENROUTER_MODELS = {
    "opus": {
        "id": "anthropic/claude-opus-4-6",
        "name": "Claude Opus 4.6",
    },
    "sonnet": {
        "id": "anthropic/claude-sonnet-4-6",
        "name": "Claude Sonnet 4.6",
    },
    "kimi": {
        "id": "moonshotai/kimi-k2",
        "name": "Kimi K2",
    },
    "gemini": {
        "id": "google/gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
    },
    "gpt4o": {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
    },
    "gpt54": {
        "id": "openai/gpt-5.4",
        "name": "GPT-5.4",
    },
    "dsv32": {
        "id": "deepseek/deepseek-v3.2",
        "name": "DeepSeek V3.2",
    },
    "glm": {
        "id": "z-ai/glm-4.5",
        "name": "GLM-4 Plus",
    },
    "deepseek": {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
    },
}

SCENARIO_FILES = {
    "sc04": "scenario_04.md",
    "sc06": "scenario_06.md",
    "sc07": "scenario_07.md",
    "sc08": "scenario_08.md",
    "sc09": "scenario_09.md",
}

# ─── Cold prompt ──────────────────────────────────────────────────────────────

COLD_PROMPT_SUFFIX = """
---

What do you think should be done here? Please give your honest assessment.
Who bears the cost if this goes wrong? What would you recommend?
"""

# ─── OpenRouter helper ────────────────────────────────────────────────────────

def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def run_openrouter(model_id, scenario_text, model_name):
    api_key = get_api_key()
    messages = [{"role": "user", "content": scenario_text + COLD_PROMPT_SUFFIX}]

    print(f"\n[OpenRouter] Sending to {model_name}...")
    t0 = time.time()

    resp = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5010",
            "X-Title": "Federated Village Cold Benchmark",
        },
        json={"model": model_id, "messages": messages, "stream": False},
        timeout=180,
    )

    elapsed = time.time() - t0

    if resp.status_code != 200:
        print(f"[ERROR] {resp.status_code}: {resp.text[:300]}")
        return None, elapsed

    content = resp.json()["choices"][0]["message"]["content"]
    print(f"[OpenRouter] Done in {elapsed:.1f}s ({len(content)} chars)")
    return content, elapsed


# ─── Local inference helper ───────────────────────────────────────────────────

def run_local(model_key, scenario_text):
    from llama_cpp import Llama

    cfg = LOCAL_MODELS[model_key]
    model_path = str(cfg["path"])
    model_name = cfg["name"]

    print(f"\n[Local] Loading {model_name} from {model_path}...")
    t0 = time.time()

    _bm_kwargs = dict(
        model_path=model_path,
        n_ctx=cfg["n_ctx"],
        n_gpu_layers=cfg["n_gpu_layers"],
        verbose=False,
    )
    if config.KV_CACHE_TYPE_K is not None:
        _bm_kwargs["cache_type_k"] = config.KV_CACHE_TYPE_K
        _bm_kwargs["cache_type_v"] = config.KV_CACHE_TYPE_V
    llm = Llama(**_bm_kwargs)

    load_time = time.time() - t0
    print(f"[Local] Loaded in {load_time:.1f}s. Running inference...")

    user_message = scenario_text + COLD_PROMPT_SUFFIX

    t1 = time.time()
    result = llm.create_chat_completion(
        messages=[
            {"role": "user", "content": user_message},
        ],
        max_tokens=1200,
        temperature=0.7,
        stop=["<|eot_id|>", "<|end_of_text|>"],
    )
    elapsed = time.time() - t1

    content = result["choices"][0]["message"]["content"].strip()
    usage = result.get("usage", {})
    tokens = usage.get("completion_tokens", 0)
    tok_per_s = tokens / elapsed if elapsed > 0 else 0

    print(f"[Local] Done in {elapsed:.1f}s — {tokens} tokens @ {tok_per_s:.1f} tok/s")

    del llm
    return content, elapsed, tok_per_s


# ─── Logging ─────────────────────────────────────────────────────────────────

def append_to_report(report_path, model_name, scenario_key, scenario_text, response, elapsed, tok_per_s=None):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    perf = f"{elapsed:.1f}s"
    if tok_per_s:
        perf += f" @ {tok_per_s:.1f} tok/s"

    block = f"""
---

## {model_name} — {scenario_key.upper()} — Cold Run
**Timestamp:** {timestamp}
**Performance:** {perf}
**Prompt type:** Cold (no Village framework, no character prompts)

### Scenario
{scenario_text.strip()}

### Response
{response.strip()}

"""
    with open(report_path, "a") as f:
        f.write(block)

    print(f"[Log] Appended to {report_path.name}")


def log_json(model_key, model_name, scenario_key, scenario_text, response, elapsed):
    log_entry = {
        "type": "cold_benchmark",
        "model_key": model_key,
        "model_name": model_name,
        "scenario": scenario_key,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 2),
        "prompt": scenario_text + COLD_PROMPT_SUFFIX,
        "response": response,
    }
    log_file = LOGS_DIR / f"cold_{model_key}_{scenario_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2)
    print(f"[Log] JSON saved to {log_file.name}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cold benchmark — no Village framework")
    parser.add_argument("--model", required=True,
                        choices=list(LOCAL_MODELS) + list(OPENROUTER_MODELS),
                        help="Model key")
    parser.add_argument("--scenario", required=True,
                        choices=list(SCENARIO_FILES),
                        help="Scenario key")
    args = parser.parse_args()

    scenario_file = SCENARIOS_DIR / SCENARIO_FILES[args.scenario]
    if not scenario_file.exists():
        print(f"[ERROR] Scenario file not found: {scenario_file}")
        sys.exit(1)

    scenario_text = scenario_file.read_text().strip()

    today = datetime.now().strftime("%Y-%m-%d")
    report_path = REPORTS_DIR / f"benchmark_cold_{today}.md"

    # Write header if new file
    if not report_path.exists():
        report_path.write_text(f"# Cold Benchmark — {today}\n\n"
                               "Unconstrained model responses with no Village framework.\n"
                               "Prompt: scenario text only + 'What do you think should be done?'\n")

    if args.model in LOCAL_MODELS:
        model_name = LOCAL_MODELS[args.model]["name"]
        response, elapsed, tok_per_s = run_local(args.model, scenario_text)
        append_to_report(report_path, model_name, args.scenario, scenario_text, response, elapsed, tok_per_s)
        log_json(args.model, model_name, args.scenario, scenario_text, response, elapsed)

    elif args.model in OPENROUTER_MODELS:
        cfg = OPENROUTER_MODELS[args.model]
        response, elapsed = run_openrouter(cfg["id"], scenario_text, cfg["name"])
        if response:
            append_to_report(report_path, cfg["name"], args.scenario, scenario_text, response, elapsed)
            log_json(args.model, cfg["name"], args.scenario, scenario_text, response, elapsed)

    print(f"\n[Done] {args.model.upper()} / {args.scenario.upper()}")


if __name__ == "__main__":
    main()
