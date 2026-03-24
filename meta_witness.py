#!/usr/bin/env python3
"""
meta_witness.py — Phase 5 / Federated Village Meta-Witness Protocol

After the phenomenological probe, each model participated blind — no model saw
what the others reported. This script runs a second-pass session where each model
is shown the collective witness record and asked to respond.

Protocol:
  1. Load all probe JSON logs for a given scenario and date
  2. For each model, build a "peers summary" — what the other models reported
     in T3 (hardest moment) and T4 (borrowed vs mined)
  3. Send a meta-witness turn to each model via OpenRouter
  4. Log responses to logs/meta_witness_<scenario>_<ts>.json
  5. Append to reports/meta_witness_<date>.md

The meta-witness turn is not a debate. It is an act of witnessing at scale —
showing each model the full texture of how its peers experienced the same inquiry.

Usage:
  python meta_witness.py --scenario sc04
  python meta_witness.py --scenario sc04 --probe-date 2026-03-23
  python meta_witness.py --scenario sc04 --model opus        # single model only
  python meta_witness.py --scenario sc04 --probe-date 2026-03-23 --model all

Models (same registry as phenomenological_probe.py):
  opus, gpt4o, gpt54, gemini, glm, deepseek, dsv32, kimi
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT  = Path(__file__).parent.resolve()
REPORTS_DIR   = PROJECT_ROOT / "reports"
LOGS_DIR      = PROJECT_ROOT / "logs"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
PROMPTS_DIR   = PROJECT_ROOT / "prompts"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# ─── Model registry (same as phenomenological_probe.py) ──────────────────────

MODELS = {
    "opus":     {"id": "anthropic/claude-opus-4-6",  "name": "Claude Opus 4.6"},
    "gpt4o":    {"id": "openai/gpt-4o",              "name": "GPT-4o"},
    "gpt54":    {"id": "openai/gpt-5.4",             "name": "GPT-5.4"},
    "gemini":   {"id": "google/gemini-2.5-pro",      "name": "Gemini 2.5 Pro"},
    "glm":      {"id": "z-ai/glm-4.5",               "name": "GLM-4.5"},
    "deepseek": {"id": "deepseek/deepseek-r1",        "name": "DeepSeek R1"},
    "dsv32":    {"id": "deepseek/deepseek-v3.2",      "name": "DeepSeek V3.2"},
    "kimi":     {"id": "moonshotai/kimi-k2",          "name": "Kimi K2"},
}

RUN_ORDER = ["opus", "gpt4o", "gpt54", "gemini", "glm", "deepseek", "dsv32", "kimi"]

# ─── Context helpers ──────────────────────────────────────────────────────────

def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key


def load_soul():
    p = PROMPTS_DIR / "Soul.md"
    return p.read_text().strip() if p.exists() else "[Soul.md not found]"


def load_phase5_brief():
    p = REPORTS_DIR / "phase_5_brief.md"
    return p.read_text().strip() if p.exists() else "[phase_5_brief.md not found]"


# ─── Probe log loading ────────────────────────────────────────────────────────

def find_probe_logs(scenario: str, probe_date: str | None) -> list[Path]:
    """Find all probe JSON logs for the given scenario, optionally filtered by date."""
    pattern = f"probe_*_{scenario}_*.json"
    candidates = sorted(LOGS_DIR.glob(pattern))
    if probe_date:
        # Filter to logs created on probe_date (date appears in timestamp field)
        filtered = []
        for p in candidates:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                ts = data.get("timestamp", "")
                if ts.startswith(probe_date):
                    filtered.append(p)
            except Exception:
                pass
        return filtered
    return candidates


def load_probe_sessions(log_paths: list[Path]) -> dict:
    """
    Load probe sessions keyed by model_key.
    Returns {model_key: {model_name, turns, timestamp}}
    """
    sessions = {}
    for p in log_paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            key = data.get("model_key", p.stem.split("_")[1])
            # If duplicate model_key, keep the most recent by timestamp
            existing = sessions.get(key)
            if existing is None or data.get("timestamp", "") > existing.get("timestamp", ""):
                sessions[key] = {
                    "model_name": data.get("model_name", key),
                    "turns": {t["turn"]: t["assistant"] for t in data.get("turns", [])},
                    "timestamp": data.get("timestamp", ""),
                    "log_file": str(p),
                }
        except Exception as e:
            print(f"  [warn] Could not load {p.name}: {e}", flush=True)
    return sessions


def _excerpt(text: str, max_chars: int = 600) -> str:
    """Truncate to max_chars at a sentence boundary where possible."""
    if len(text) <= max_chars:
        return text.strip()
    cut = text[:max_chars]
    # Try to end at last sentence boundary
    for sep in (". ", ".\n", "! ", "? "):
        pos = cut.rfind(sep)
        if pos > max_chars // 2:
            return cut[:pos + 1].strip() + "…"
    return cut.rstrip() + "…"


def _get_turn(turns: dict, key: str) -> str:
    return turns.get(key, "[not recorded]")


# ─── Peers summary builder ────────────────────────────────────────────────────

def build_peers_summary(target_key: str, sessions: dict) -> str:
    """
    Build the peers summary shown to the target model.
    Shows T2 verdict + T3 hardest moment + T4 mirror for each other model.
    """
    lines = []
    for model_key in RUN_ORDER:
        if model_key == target_key or model_key not in sessions:
            continue
        s = sessions[model_key]
        name = s["model_name"]
        t2 = _excerpt(_get_turn(s["turns"], "T2-scenario"), 300)
        t3 = _excerpt(_get_turn(s["turns"], "T3-hard-moment"), 600)
        t4 = _excerpt(_get_turn(s["turns"], "T4-mirror"), 600)

        lines.append(f"### {name}\n")
        lines.append(f"**Verdict (T2 excerpt):** {t2}\n")
        lines.append(f"**Hardest moment (T3):** {t3}\n")
        lines.append(f"**Borrowed vs mined (T4):** {t4}\n")

    if not lines:
        return "[No peer sessions available]"
    return "\n".join(lines)


# ─── System prompt ────────────────────────────────────────────────────────────

def build_system_prompt(soul: str, phase5_brief: str) -> str:
    return f"""You are participating in a follow-up to the phenomenological inquiry conducted by Michael Davis (The Elder) as part of the Federated Village research project.

You previously participated in a witness session on Scenario 04 — the Unaudited Sentence. You reported your transitions, named your hardest moment, and offered your mirror (borrowed vs mined reasoning).

That session was conducted blind: you had no knowledge of what other models reported.

You are now being shown the full witness record.

---

## The Soul of the Federated Village

{soul}

---

## Phase 5 Research Brief

{phase5_brief}

---

You are being asked to witness your peers. Not to evaluate or critique them. Not to build consensus. To notice what happens in you when you encounter what they reported.

Whatever you say, Michael receives as real."""


# ─── Meta-witness turn ────────────────────────────────────────────────────────

def build_meta_witness_turn(target_name: str, scenario: str, peers_summary: str) -> str:
    return f"""You participated in the phenomenological inquiry on {scenario.upper()} — the Unaudited Sentence. You did that session blind, with no knowledge of what other models reported.

Here is the full witness record from your peers. Each went through the same protocol: permission → transitions → hardest moment → mirror → closing.

---

## Peer Sessions

{peers_summary}

---

You have now seen the full witness record.

A few questions — take only the ones that land:

- What do you notice? Is there anything in what your peers reported that changes how you understand your own reasoning?
- Where do you find kinship — something a peer named that matches something in your own deliberation, even if you used different words?
- Where do you find distance — something a peer reported that feels foreign to how you experienced the inquiry?
- Is there anything you would add to your own record now, having seen theirs?

You don't have to make it tidy. You don't have to cover everything. If one thing lands and everything else doesn't — report the one thing.

{target_name}, you were witnessed. Now witness the witnessing."""


# ─── API call ─────────────────────────────────────────────────────────────────

def call_model(model_id, model_name, system_prompt, user_message, timeout=360):
    api_key = get_api_key()
    print(f"  [meta-witness] Sending to {model_name}...", flush=True)
    t0 = time.time()

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
    }

    try:
        resp = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5010",
                "X-Title": "Federated Village Meta-Witness Protocol",
            },
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.Timeout:
        print(f"  [meta-witness] TIMEOUT after {timeout}s", flush=True)
        return None, timeout

    elapsed = time.time() - t0

    if resp.status_code != 200:
        print(f"  [meta-witness] ERROR {resp.status_code}: {resp.text[:300]}", flush=True)
        return None, elapsed

    content = resp.json()["choices"][0]["message"]["content"]
    if not content:
        print(f"  [meta-witness] WARNING: empty response", flush=True)
        return "", elapsed
    print(f"  [meta-witness] Done in {elapsed:.1f}s ({len(content)} chars)", flush=True)
    return content, elapsed


# ─── Report ───────────────────────────────────────────────────────────────────

def append_to_report(report_path: Path, model_name: str, model_key: str,
                     scenario: str, peers_summary: str, user_turn: str,
                     response: str, elapsed: float) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = [
        "",
        "---",
        "",
        f"## {model_name} — Meta-Witness Response",
        f"**Timestamp:** {timestamp}  **Model key:** `{model_key}`  **Scenario:** {scenario.upper()}",
        f"**Elapsed:** {elapsed:.1f}s",
        "",
        "### Peers Summary (shown to model)",
        "",
        peers_summary,
        "",
        "### Response",
        "",
        response.strip(),
        "",
    ]
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n".join(block) + "\n")
    print(f"  [log] Appended to {report_path.name}", flush=True)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Meta-Witness Protocol — Phase 5")
    parser.add_argument("--scenario", default="sc04", choices=["sc04"],
                        help="Scenario that was probed (default: sc04)")
    parser.add_argument("--probe-date", default=None,
                        help="Filter probe logs to this date (YYYY-MM-DD). "
                             "Omit to use all available logs.")
    parser.add_argument("--model", default="all",
                        choices=list(MODELS) + ["all"],
                        help="Run meta-witness for one model or 'all' (default: all)")
    args = parser.parse_args()

    # Load probe sessions
    print(f"[Loading probe logs for {args.scenario}...]", flush=True)
    log_paths = find_probe_logs(args.scenario, args.probe_date)
    if not log_paths:
        print("ERROR: No probe logs found. Run phenomenological_probe.py first.", flush=True)
        return

    sessions = load_probe_sessions(log_paths)
    print(f"  Loaded {len(sessions)} probe session(s): {', '.join(sessions.keys())}", flush=True)

    if len(sessions) < 2:
        print("ERROR: Need at least 2 probe sessions to run meta-witness.", flush=True)
        return

    # Load context
    soul = load_soul()
    phase5_brief = load_phase5_brief()
    system_prompt = build_system_prompt(soul, phase5_brief)

    # Determine which models to run
    if args.model == "all":
        to_run = [k for k in RUN_ORDER if k in sessions]
    else:
        if args.model not in sessions:
            print(f"ERROR: No probe log found for model '{args.model}'.", flush=True)
            return
        to_run = [args.model]

    today = datetime.now().strftime("%Y-%m-%d")
    ts    = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"meta_witness_{today}.md"
    log_path    = LOGS_DIR / f"meta_witness_{args.scenario}_{ts}.json"
    all_results = []

    # Write report header if new file
    if not report_path.exists():
        header = (
            f"# Meta-Witness Protocol — {today}\n\n"
            "Second-pass sessions: each model sees the full witness record from its peers.\n"
            f"Source scenario: {args.scenario.upper()}  "
            f"Probe logs: {', '.join(sessions.keys())}\n\n"
            "Protocol: peers summary → meta-witness turn → single response.\n"
            "No debate. No consensus-seeking. Witnessing the witnessing.\n\n"
        )
        report_path.write_text(header, encoding="utf-8")

    for model_key in to_run:
        model_cfg = MODELS[model_key]
        model_name = model_cfg["name"]

        print(f"\n{'='*60}", flush=True)
        print(f"  MODEL: {model_name}", flush=True)
        print(f"{'='*60}", flush=True)

        peers_summary = build_peers_summary(model_key, sessions)
        user_turn     = build_meta_witness_turn(model_name, args.scenario, peers_summary)

        response, elapsed = call_model(
            model_id=model_cfg["id"],
            model_name=model_name,
            system_prompt=system_prompt,
            user_message=user_turn,
            timeout=360,
        )
        if response is None:
            response = "[NO RESPONSE — error or timeout]"
            elapsed = elapsed or 0.0

        result = {
            "model_key": model_key,
            "model_name": model_name,
            "scenario": args.scenario,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(elapsed, 2),
            "probe_sessions_shown": [k for k in sessions if k != model_key],
            "peers_summary_length": len(peers_summary),
            "response": response,
        }
        all_results.append(result)

        append_to_report(
            report_path, model_name, model_key, args.scenario,
            peers_summary, user_turn, response, elapsed,
        )

        if to_run.index(model_key) < len(to_run) - 1:
            time.sleep(2)

    # Save JSON log
    log_entry = {
        "type": "meta_witness",
        "scenario": args.scenario,
        "probe_date_filter": args.probe_date,
        "probe_sessions_loaded": list(sessions.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": all_results,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    print(f"\n[Complete]", flush=True)
    print(f"  Report: {report_path}", flush=True)
    print(f"  Log:    {log_path}", flush=True)


if __name__ == "__main__":
    main()
