---
name: browser-source
description: Browser automation for scholarly source acquisition. Minerva composes a Python script, sends it to Mike for approval via Telegram, then runs it through browser-harness (headless Chrome/CDP). Use when API-based retrieval is blocked by JS rendering or paywalls.
version: 0.2.0
author: Michael Fox / Claude Code
license: MIT
metadata:
  hermes:
    tags: [Research, Browser, Sources, Scholarly, GHB, Automation]
    related_skills: [scholarly-source-acquisition, vault-cold-memory, research-model-routing]
---

# Browser Source Acquisition

Runs browser-harness (browser-use/browser-harness) to reach sources that block API access: JSTOR, museum collections, paywalled journals, JS-rendered library databases.

## Approval Workflow

**Minerva does not run browser scripts autonomously without Mike's permission.**

Before executing any browser task:

1. Compose the Python script that will run (using helpers.py primitives — see below)
2. Send Mike a Telegram message describing what the script will do in plain language and showing the code
3. Wait for Mike to reply "run it" (or equivalent affirmation)
4. Execute via `browse_run.py`
5. Report results back via Telegram

This approval step may be relaxed over time as Mike gains confidence in Minerva's browser judgment. Until then, always ask first.

**Example Telegram message to Mike:**
```
I need to browse to fetch the abstract for this JSTOR article. Here's what I'll run:

  ensure_real_tab()
  goto('https://www.jstor.org/stable/10.2307/xxxxxx')
  wait_for_load()
  text = js("document.querySelector('.abstract').innerText")
  print(text)

OK to run?
```

## Running a Script

```bash
python ~/.hermes/skills/research/browser-source/scripts/browse_run.py << 'PY'
ensure_real_tab()
goto('https://commons.wikimedia.org/wiki/Category:Venus_figurines')
wait_for_load()
print(page_info())
PY
```

Or from a file:

```bash
python ~/.hermes/skills/research/browser-source/scripts/browse_run.py --script /tmp/task.py
```

Chrome starts automatically if not running.

## Available Helper Primitives

From `~/browser-harness/helpers.py`:

| Function | Purpose |
|---|---|
| `ensure_real_tab()` | Create or focus a real browser tab |
| `goto(url)` | Navigate to URL |
| `wait_for_load(timeout=15)` | Wait for page to finish loading |
| `page_info()` | Returns dict: url, title, viewport dimensions |
| `js(expression)` | Run JavaScript, returns result |
| `screenshot(path)` | Save screenshot to path |
| `click(x, y)` | Click at coordinates |
| `type_text(text)` | Type into focused element |
| `scroll(x, y, dy)` | Scroll page |
| `http_get(url)` | Direct HTTP GET (no browser render) |
| `new_tab(url)` | Open a new tab |
| `list_tabs()` | List open tabs |

## Workflow for GHB Source Work

1. Attempt source via `scholarly-source-acquisition` (API-based, no browser needed)
2. If blocked by JS/paywall, invoke `browser-source`:
   - Compose the Python script
   - Send to Mike for approval
   - Run and return result + BibTeX
3. Append BibTeX to `~/ObsidianVault/07 - Global History Book/References/GHB_bibliography.bib`

## Good Targets for Browser Retrieval

- `commons.wikimedia.org` — image search and file metadata
- `jstor.org` — abstracts and full text (where open access)
- `archive.org` — document and book fetches
- `scholar.google.com` — search (no login required)
- Museum collection pages (British Museum, Met, etc.) — note: some block headless Chrome via Cloudflare

## Cloudflare Fallback

If Chrome returns a "Just a moment..." page, a CF Ray ID, or a 403, **switch to `cloudflare-fetch`**:

```bash
cf_fetch <url> --text
```

`cloudflare-fetch` uses Camoufox (patched Firefox) with a humanized fingerprint that passes
Cloudflare's JS challenge. Known problematic sites: Smithsonian Collections, National Archives,
some museum databases. Wikipedia timeouts from rapid requests also benefit from `cf_fetch --delay 3`.

## Model Note

Chrome runs CPU-only on the 2013 Mac Pro (AMD GPU cards unsupported). `browse_run.py` handles this transparently via `BU_CDP_WS`. No GPU is needed for browser-harness tasks.

## Infrastructure

- Chrome launch script: `~/bin/chrome-minerva.sh` (headless, port 9222, CPU-only)
- browser-harness install: `~/browser-harness/` (managed via `uv`)
- Runner script: `~/.hermes/skills/research/browser-source/scripts/browse_run.py`
- Source-controlled version: `federated_village/minerva/skills/research/browser-source/`
