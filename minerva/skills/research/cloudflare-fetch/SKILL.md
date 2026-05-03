---
name: cloudflare-fetch
description: Cloudflare-resistant page fetching using Camoufox (patched Firefox). Use when browser-source/Chrome is blocked by Cloudflare or when a site is timing out from too many fast requests. Covers Smithsonian, National Archives, Wikipedia, museum collections, and any site showing "Just a moment..." or a Ray ID error.
version: 0.1.0
author: Michael Fox / Claude Code
license: MIT
metadata:
  hermes:
    tags: [Research, Browser, Cloudflare, Sources, Scholarly, GHB, Automation, Firefox]
    related_skills: [browser-source, scholarly-source-acquisition, vault-cold-memory]
---

# Cloudflare-Resistant Fetch

Uses Camoufox — a patched Firefox with humanized fingerprinting — to fetch pages
blocked by Cloudflare's bot detection. Falls back to this skill when `browser-source`
(Chrome CDP) returns a "Just a moment..." Cloudflare challenge page.

Also the correct tool when sites timeout from rapid successive requests (Wikipedia,
Wikipedia Commons, large institutional archives). Use `--delay` to pace requests.

## When to Use

| Symptom | Use this skill |
|---|---|
| "Just a moment..." or CF Ray ID in response | Yes — Cloudflare challenge |
| Chrome `browser-source` returns empty / 403 | Yes |
| Wikipedia/Commons timeouts on rapid fetches | Yes — add `--delay 3` |
| Smithsonian, National Archives, Met, JSTOR blocked | Yes |
| Normal page load, no challenge | No — use `browser-source` instead |

## Running a Fetch

```bash
# Basic fetch — returns HTML to stdout
python ~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py <url>

# Plain text output (no HTML tags — good for reading content)
python ~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py <url> --text

# Save to file
python ~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py <url> --output /tmp/result.html

# Rate-limit courtesy (use when fetching multiple pages in sequence)
python ~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py <url> --delay 3

# Longer timeout for slow challenges (default is 45s)
python ~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py <url> --timeout 90
```

## Approval Workflow

Same as `browser-source`: **Minerva does not fetch autonomously without Mike's OK.**

Before running:
1. Compose the fetch command with the target URL
2. Telegram Mike: describe what you'll fetch and show the command
3. Wait for "run it" (or equivalent)
4. Execute and report results

**Example Telegram:**
```
Smithsonian SI-unit page is blocking Chrome with a CF challenge.
I'll use cf_fetch (Camoufox/Firefox) to get it:

  cf_fetch.py https://collections.si.edu/search/... --text --timeout 60

OK to run?
```

## Rate Limiting Guidance

When fetching multiple pages from the same domain, space them out:

| Domain | Recommended delay |
|---|---|
| Wikipedia / Wikimedia Commons | 3–5s between requests |
| Smithsonian Collections | 5s |
| National Archives | 5s |
| JSTOR | 10s (strict) |
| Other institutional archives | 3–5s |

Rapid-fire fetches (< 1s apart) will get the IP soft-banned even with a real browser fingerprint.

## How It Works

Camoufox downloads and manages a patched Firefox binary (~100MB, stored in
`~/.camoufox/`) that:
- Spoofs the headless browser flag (CF checks `navigator.webdriver`)
- Randomizes Canvas/WebGL fingerprints on each launch
- Uses humanized timing on page interactions
- Passes Cloudflare's TLS fingerprint check (Firefox JA3 signature, not Chrome)

The Firefox install is separate from Mike's system Firefox (`/Applications/Firefox.app`)
and does not interfere with it.

## Infrastructure

- Script: `~/.hermes/skills/research/cloudflare-fetch/scripts/cf_fetch.py`
- Camoufox binary cache: `~/.camoufox/` (auto-managed)
- Install: run `~/.hermes/skills/research/cloudflare-fetch/scripts/install.sh` once
- Source-controlled: `federated_village/minerva/skills/research/cloudflare-fetch/`

## Escalation Path

If Camoufox is also blocked (rare — usually means the site has per-IP blocks or requires login):
1. Try `--delay 10` and retry once
2. Report to Mike via Telegram — may need a different IP or manual access
3. Fall back to `scholarly-source-acquisition` for API-based retrieval if available
