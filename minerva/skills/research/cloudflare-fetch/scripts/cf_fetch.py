#!/usr/bin/env python3
"""
cf_fetch.py — Cloudflare-resistant page fetch using Camoufox (patched Firefox).

Camoufox presents as a real Firefox browser with a humanized fingerprint,
bypassing Cloudflare's 5-second challenge and JS bot detection that blocks
headless Chrome on sites like Smithsonian, National Archives, and museum collections.

Usage:
  python cf_fetch.py <url>
  python cf_fetch.py <url> --text               # plain text, no HTML tags
  python cf_fetch.py <url> --output /tmp/out.html
  python cf_fetch.py <url> --timeout 60         # longer wait for slow challenges

Install (one-time, see install.sh):
  pip install camoufox && python -m camoufox fetch
"""

import argparse
import re
import sys
import time
from pathlib import Path

try:
    from camoufox.sync_api import Camoufox
except ImportError:
    print(
        "ERROR: camoufox not installed.\n"
        "Run: pip install camoufox && python -m camoufox fetch",
        file=sys.stderr,
    )
    sys.exit(1)


CF_CHALLENGE_MARKERS = [
    "challenge-platform",
    "cf-browser-verification",
    "cf_chl_opt",
    "Checking your browser",
    "Just a moment",
    "Ray ID",
]


def is_cf_challenge(html: str) -> bool:
    return any(m in html for m in CF_CHALLENGE_MARKERS)


def fetch(url: str, timeout_s: int = 45) -> tuple[str, str]:
    """Return (final_url, html). Waits out CF challenge if encountered."""
    with Camoufox(headless=True) as browser:
        page = browser.new_page()
        page.goto(url, timeout=timeout_s * 1000, wait_until="domcontentloaded")

        # Poll until CF challenge clears or timeout expires
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            html = page.content()
            if not is_cf_challenge(html):
                return page.url, html
            time.sleep(1.5)
            # Let the page continue working
            page.wait_for_load_state("networkidle", timeout=5000)

        # Return whatever we have — caller can decide what to do with it
        return page.url, page.content()


def strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Fetch a Cloudflare-protected URL using Camoufox (patched Firefox)"
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--output", help="Save output to file instead of stdout")
    parser.add_argument(
        "--text", action="store_true", help="Return plain text instead of HTML"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Max seconds to wait for page + CF challenge (default: 45)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait before fetching (rate-limit courtesy, default: 0)",
    )
    args = parser.parse_args()

    if args.delay:
        print(f"Waiting {args.delay}s before fetch (rate-limit delay)...", file=sys.stderr)
        time.sleep(args.delay)

    print(f"Fetching: {args.url}", file=sys.stderr)
    final_url, html = fetch(args.url, args.timeout)

    if is_cf_challenge(html):
        print(
            "WARNING: Cloudflare challenge may not have cleared — page may be incomplete.",
            file=sys.stderr,
        )

    if final_url != args.url:
        print(f"Redirected to: {final_url}", file=sys.stderr)

    output = strip_html(html) if args.text else html

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Saved {len(output):,} chars to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
