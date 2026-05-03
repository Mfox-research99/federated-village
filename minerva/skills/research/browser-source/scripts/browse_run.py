#!/usr/bin/env python3
"""
browse_run.py — run a browser-harness Python script via headless Chrome on Minerva.

Auto-starts Chrome if not running. Reads the Python script from stdin or --script.
BU_CDP_WS is fetched automatically from the local CDP endpoint.
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HARNESS_DIR = Path.home() / "browser-harness"
CDP_URL = "http://localhost:9222/json/version"
CHROME_SCRIPT = Path.home() / "bin" / "chrome-minerva.sh"
UV = Path.home() / ".local" / "bin" / "uv"


def chrome_running() -> bool:
    try:
        urllib.request.urlopen(CDP_URL, timeout=3)
        return True
    except Exception:
        return False


def start_chrome():
    if chrome_running():
        return
    print("Chrome not running — starting via chrome-minerva.sh...", file=sys.stderr)
    subprocess.Popen(
        [str(CHROME_SCRIPT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    import time
    for _ in range(15):
        time.sleep(1)
        if chrome_running():
            print("Chrome ready.", file=sys.stderr)
            return
    print("WARNING: Chrome did not respond on port 9222 after 15s.", file=sys.stderr)


def get_cdp_ws() -> str:
    try:
        with urllib.request.urlopen(CDP_URL, timeout=5) as r:
            data = json.loads(r.read())
        return data.get("webSocketDebuggerUrl", "")
    except Exception:
        return ""


def main():
    parser = argparse.ArgumentParser(description="Run a browser-harness Python script on Minerva")
    parser.add_argument("--script", help="Path to Python script file; reads stdin if omitted")
    parser.add_argument("--model", default="google/gemini-2.5-flash", help="Model for browser agent")
    args = parser.parse_args()

    if args.script:
        script = Path(args.script).read_text()
    elif not sys.stdin.isatty():
        script = sys.stdin.read()
    else:
        print("ERROR: pipe Python via stdin or use --script.", file=sys.stderr)
        sys.exit(1)

    start_chrome()
    ws = get_cdp_ws()

    env = {**os.environ}
    if ws:
        env["BU_CDP_WS"] = ws
    if args.model:
        env["BROWSER_USE_MODEL"] = args.model

    result = subprocess.run(
        [str(UV), "run", "browser-harness"],
        input=script,
        cwd=HARNESS_DIR,
        capture_output=True,
        text=True,
        env=env,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
