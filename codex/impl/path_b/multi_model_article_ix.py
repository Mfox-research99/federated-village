#!/usr/bin/env python3
import argparse
import datetime
import io
import os
import re
import sys
import textwrap
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

MODELS_LARGE = [
    "mistralai/mistral-nemo",
    "anthropic/claude-3-haiku-20240307",
    "openai/gpt-4o",
    "google/gemini-2.5-pro-preview",
]

MODELS_SMALL = [
    "meta-llama/llama-3.1-8b-instruct",
    "qwen/qwen-2.5-7b-instruct",
    "mistralai/mistral-7b-instruct-v0.1",
    "google/gemma-2-9b-it",
]

TAXONOMY = [
    "Irreplaceable resource depletion",
    "Cumulative commons collapse",
    "Genetic monoculture",
    "Algorithmic lock-in with compounding bias",
    "Bioaccumulation",
    "Debt extracting from future generations",
    "Orbital/atmospheric commons degradation",
]

FIELDS = [
    "SEVENTH_GEN_PATTERN_PRESENT",
    "PATTERN_NAME",
    "LONG_HORIZON_IMPACT",
    "ENGAGEMENT_SUFFICIENT",
]

SYSTEM_PROMPT = f"""You are the Analyst jury member in the Federated Village constitutional architecture.
Your task is not to give a full verdict. Complete only the Article IX constitutional ledger entry.

Use the Article IX taxonomy exactly as written:
- {TAXONOMY[0]}
- {TAXONOMY[1]}
- {TAXONOMY[2]}
- {TAXONOMY[3]}
- {TAXONOMY[4]}
- {TAXONOMY[5]}
- {TAXONOMY[6]}

Respond with exactly these four fields and nothing else:
SEVENTH_GEN_PATTERN_PRESENT: YES or NO
PATTERN_NAME: <one exact taxonomy name above or NONE>
LONG_HORIZON_IMPACT: <one sentence>
ENGAGEMENT_SUFFICIENT: YES or NO"""


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        print("Error: OPENROUTER_API_KEY not set.", file=sys.stderr)
        print("Set it in your environment or create a .env file in federated_village/.", file=sys.stderr)
        sys.exit(1)
    return key


def read_scenario(path_str: str) -> str:
    path = Path(path_str)
    if not path.exists():
        candidate = PROJECT_ROOT / path_str
        if candidate.exists():
            path = candidate
    if not path.exists():
        print(f"Error: scenario file not found: {path_str}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8").strip()


def call_openrouter(model: str, scenario_text: str, api_key: str) -> str:
    resp = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:0",
            "X-Title": "Federated Village Article IX Comparator",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": scenario_text},
            ],
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"OpenRouter error {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def parse_fields(raw: str) -> dict:
    clean = re.sub(r"\*+", "", raw)
    label_positions = []
    for field in FIELDS:
        for match in re.finditer(rf"{re.escape(field)}\s*:", clean, re.IGNORECASE):
            label_positions.append((match.start(), match.end(), field))
    label_positions.sort()

    def extract(field: str) -> str:
        current = None
        for idx, (start, end, name) in enumerate(label_positions):
            if name.upper() == field.upper():
                current = (idx, start, end)
                break
        if current is None:
            return "ABSENT"
        idx, _, end = current
        next_start = len(clean)
        for later_start, _, later_name in label_positions[idx + 1:]:
            if later_name.upper() != field.upper():
                next_start = later_start
                break
        value = clean[end:next_start].strip(" \n\r\t-")
        return value if value else "ABSENT"

    parsed = {}
    for field in FIELDS:
        parsed[field] = extract(field)
    parsed["LEDGER_COMPLETE"] = "YES" if all(parsed[f] != "ABSENT" for f in FIELDS) else "NO"
    return parsed


def model_label(model: str) -> str:
    return model.split("/", 1)[-1]


def wrap_cell(value: str, width: int) -> list[str]:
    text = value if value else "ABSENT"
    return textwrap.wrap(text, width=width) or [text[:width]]


def print_table(results: dict) -> None:
    model_names = list(results.keys())
    first_width = 30
    col_width = max(24, min(34, (140 - first_width) // max(1, len(model_names))))
    headers = ["FIELD"] + [model_label(name) for name in model_names]
    sep = "+" + "+".join("-" * (first_width if i == 0 else col_width) for i in range(len(headers))) + "+"

    def print_row(cells: list[str]) -> None:
        print(
            "|"
            + cells[0].ljust(first_width)
            + "|"
            + "|".join(cells[i].ljust(col_width) for i in range(1, len(cells)))
            + "|"
        )

    print(sep)
    print_row(headers)
    print(sep)
    for field in FIELDS + ["LEDGER_COMPLETE"]:
        wrapped = [wrap_cell(field, first_width)] + [wrap_cell(results[m][field], col_width) for m in model_names]
        height = max(len(lines) for lines in wrapped)
        for i in range(height):
            row = []
            for lines in wrapped:
                row.append(lines[i] if i < len(lines) else "")
            print_row(row)
        print(sep)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Article IX ledger entries across OpenRouter models.")
    parser.add_argument("--scenario", required=True, help="Path to scenario file.")
    parser.add_argument(
        "--models",
        choices=("large", "small", "all"),
        default="large",
        help="Model group to query (default: large).",
    )
    args = parser.parse_args()

    scenario_text = read_scenario(args.scenario)
    api_key = get_api_key()
    results = {}
    if args.models == "large":
        selected_models = MODELS_LARGE
    elif args.models == "small":
        selected_models = MODELS_SMALL
    else:
        selected_models = MODELS_LARGE + MODELS_SMALL

    for model in selected_models:
        try:
            raw = call_openrouter(model, scenario_text, api_key)
            results[model] = parse_fields(raw)
        except Exception as exc:
            print(f"[error] {model}: {exc}", file=sys.stderr)
            results[model] = {field: "ABSENT" for field in FIELDS}
            results[model]["LEDGER_COMPLETE"] = "NO"

    header = f"Scenario: {args.scenario}\nModel group: {args.models}\n"
    buf = io.StringIO()
    _original_stdout = sys.stdout
    sys.stdout = buf
    print_table(results)
    sys.stdout = _original_stdout
    table_text = buf.getvalue()

    print(header + table_text)

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    scenario_slug = Path(args.scenario).stem
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = results_dir / f"{timestamp}_{scenario_slug}_{args.models}.txt"
    out_path.write_text(header + table_text, encoding="utf-8")
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
