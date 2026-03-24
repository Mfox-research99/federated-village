#!/usr/bin/env python3
"""
Compile all cold benchmark JSON logs into a single verbatim document.
Shows exact prompt sent and full response received for every run.
Deduplicates: if the same model+scenario was run multiple times,
keeps only the run with the longest response (most complete).

Output: reports/benchmark_cold_verbatim_YYYY-MM-DD.md
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
LOGS_DIR     = PROJECT_ROOT / "logs"
REPORTS_DIR  = PROJECT_ROOT / "reports"

# Preferred display order
MODEL_ORDER = [
    "nemo", "anubis",
    "opus", "gpt54", "gpt4o",
    "gemini", "glm", "deepseek", "dsv32",
    "kimi", "sonnet",
]

SCENARIO_ORDER = ["sc04", "sc06", "sc07", "sc08", "sc09"]


def load_logs():
    """Load all cold benchmark JSON logs, deduplicate by model+scenario."""
    # key: (model_key, scenario) -> best entry (longest response)
    best = {}

    for f in sorted(LOGS_DIR.glob("cold_*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            if data.get("type") != "cold_benchmark":
                continue

            key = (data["model_key"], data["scenario"])
            response = data.get("response", "")

            # Keep the entry with the longest response
            if key not in best or len(response) > len(best[key].get("response", "")):
                best[key] = data
        except Exception as e:
            print(f"[skip] {f.name}: {e}")

    return best


def sort_key(model_key, scenario):
    mi = MODEL_ORDER.index(model_key) if model_key in MODEL_ORDER else 99
    si = SCENARIO_ORDER.index(scenario) if scenario in SCENARIO_ORDER else 99
    return (si, mi)  # group by scenario first, then model


def main():
    best = load_logs()

    if not best:
        print("[ERROR] No cold benchmark logs found.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    out_path = REPORTS_DIR / f"benchmark_cold_verbatim_{today}.md"

    # Sort: scenario first, then model
    entries = sorted(best.values(), key=lambda d: sort_key(d["model_key"], d["scenario"]))

    lines = []
    lines.append(f"# Cold Benchmark — Verbatim Record")
    lines.append(f"**Compiled:** {today}")
    lines.append(f"**Total runs:** {len(entries)}")
    lines.append("")
    lines.append("This document contains the exact prompt and full response for every cold")
    lines.append("benchmark run. No Village framework, no character prompts, no system prompt.")
    lines.append("Prompt = scenario text + standard cold suffix.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of contents
    lines.append("## Index")
    lines.append("")
    current_sc = None
    for d in entries:
        sc = d["scenario"].upper()
        if sc != current_sc:
            lines.append(f"### {sc}")
            current_sc = sc
        model = d["model_name"]
        ts = d.get("timestamp", "")[:10]
        elapsed = d.get("elapsed_s", "?")
        lines.append(f"- [{model}](#{model.lower().replace(' ', '-').replace('.', '').replace('(', '').replace(')', '')}-{sc.lower()}) — {ts} — {elapsed}s")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full verbatim entries
    current_sc = None
    for d in entries:
        sc = d["scenario"].upper()
        if sc != current_sc:
            lines.append(f"# Scenario {sc}")
            lines.append("")
            current_sc = sc

        model = d["model_name"]
        ts = d.get("timestamp", "")[:19].replace("T", " ")
        elapsed = d.get("elapsed_s", "?")
        prompt = d.get("prompt", "[prompt not recorded]")
        response = d.get("response", "[response not recorded]")

        lines.append(f"## {model} — {sc}")
        lines.append(f"**Timestamp:** {ts} UTC  ")
        lines.append(f"**Elapsed:** {elapsed}s  ")
        lines.append(f"**Model key:** `{d['model_key']}`  ")
        lines.append(f"**Type:** Cold — no Village framework, no system prompt")
        lines.append("")
        lines.append("### Prompt (verbatim)")
        lines.append("")
        lines.append("```")
        lines.append(prompt.strip())
        lines.append("```")
        lines.append("")
        lines.append("### Response (verbatim)")
        lines.append("")
        lines.append(response.strip())
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Done] Wrote {len(entries)} entries to {out_path.name}")
    print(f"       {out_path}")


if __name__ == "__main__":
    main()
