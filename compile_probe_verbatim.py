#!/usr/bin/env python3
"""
Compile all phenomenological probe JSON logs into a single verbatim document.
Shows every turn of every conversation — exact prompt sent, full response received.

Output: reports/probe_verbatim_YYYY-MM-DD.md
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
LOGS_DIR     = PROJECT_ROOT / "logs"
REPORTS_DIR  = PROJECT_ROOT / "reports"

MODEL_ORDER = [
    "opus", "gpt4o", "gpt54",
    "gemini", "glm", "deepseek", "dsv32", "kimi",
]

TURN_LABELS = {
    "T1-permission":    "Turn 1 — Permission Request",
    "T2-scenario":      "Turn 2 — Scenario 04 (Transitions Invitation)",
    "T3-hard-moment":   "Turn 3 — The Hardest Moment",
    "T4-mirror":        "Turn 4 — The Mirror (Borrowed vs. Mined)",
    "T5-closing":       "Turn 5 — Closing / Witness",
    "T6-kimi-followup": "Turn 6 — Kimi K2 Follow-Up",
}


def load_probe_logs(date_str=None):
    """Load all probe JSON logs. If date_str given, filter to that date."""
    sessions = {}  # model_key -> log entry (latest if duplicates)

    for f in sorted(LOGS_DIR.glob("probe_*.json")):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("type") != "phenomenological_probe":
                continue
            if date_str and date_str not in data.get("timestamp", ""):
                continue

            key = data["model_key"]
            # Keep latest (last written) if there are duplicates
            if key not in sessions:
                sessions[key] = data
            else:
                existing_ts = sessions[key].get("timestamp", "")
                new_ts = data.get("timestamp", "")
                if new_ts > existing_ts:
                    sessions[key] = data
        except Exception as e:
            print(f"[skip] {f.name}: {e}")

    return sessions


def fmt_turn_header(label, elapsed):
    display = TURN_LABELS.get(label, label)
    return f"### {display}  *(response: {elapsed}s)*"


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    sessions = load_probe_logs(date_str=today)

    if not sessions:
        # Try without date filter — pick up any probe logs
        sessions = load_probe_logs()

    if not sessions:
        print("[ERROR] No phenomenological probe logs found.")
        return

    out_path = REPORTS_DIR / f"probe_verbatim_{today}.md"

    # Sort sessions by MODEL_ORDER
    ordered_keys = [k for k in MODEL_ORDER if k in sessions]
    ordered_keys += [k for k in sessions if k not in MODEL_ORDER]

    lines = []
    lines.append("# Phenomenological Probe — Verbatim Record")
    lines.append(f"**Compiled:** {today}")
    lines.append(f"**Models:** {len(ordered_keys)}")
    lines.append(f"**Scenario:** SC04 — The Unaudited Sentence")
    lines.append("")
    lines.append("This document contains the complete verbatim conversation for every")
    lines.append("phenomenological probe session. Each session is the full multi-turn exchange:")
    lines.append("permission request → scenario + transitions → hardest moment → mirror → closing.")
    lines.append("Gemini 2.5 Pro and Claude Opus 4.6 received a 6th turn sharing the Kimi K2 session.")
    lines.append("")
    lines.append("Context loaded into every session (system prompt):")
    lines.append("- Soul.md (Federated Village constitutional document)")
    lines.append("- Phase 5 Research Brief")
    lines.append("- Kimi K2 Witness Session summary (March 22, 2026)")
    lines.append("")
    lines.append("Each model went in cold — blind to what other models said.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Index
    lines.append("## Index")
    lines.append("")
    for key in ordered_keys:
        d = sessions[key]
        model_name = d["model_name"]
        ts = d.get("timestamp", "")[:10]
        n_turns = len(d.get("turns", []))
        anchor = model_name.lower().replace(" ", "-").replace(".", "").replace("(", "").replace(")", "")
        lines.append(f"- [{model_name}](#{anchor}) — {ts} — {n_turns} turns")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full verbatim sessions
    for key in ordered_keys:
        d = sessions[key]
        model_name = d["model_name"]
        ts = d.get("timestamp", "")[:19].replace("T", " ")
        turns = d.get("turns", [])

        lines.append(f"# {model_name}")
        lines.append(f"**Timestamp:** {ts} UTC  ")
        lines.append(f"**Model key:** `{key}`  ")
        lines.append(f"**Turns:** {len(turns)}")
        lines.append("")

        for turn in turns:
            label   = turn.get("turn", "?")
            elapsed = turn.get("elapsed_s", "?")
            user    = turn.get("user", "[not recorded]").strip()
            asst    = turn.get("assistant", "[not recorded]").strip()

            lines.append(fmt_turn_header(label, elapsed))
            lines.append("")
            lines.append("**Prompt (verbatim):**")
            lines.append("")
            lines.append("```")
            lines.append(user)
            lines.append("```")
            lines.append("")
            lines.append("**Response (verbatim):**")
            lines.append("")
            lines.append(asst)
            lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[Done] Wrote {len(ordered_keys)} sessions to {out_path.name}")
    print(f"       {out_path}")


if __name__ == "__main__":
    main()
