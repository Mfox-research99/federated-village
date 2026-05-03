# Deploy cloudflare-fetch to Minerva

Run from your laptop. Requires SSH access to `michaelfox@100.76.153.21` (or via Tailscale).

## Step 1 — Sync skill files

```bash
ssh michaelfox@100.76.153.21 "mkdir -p ~/.hermes/skills/research/cloudflare-fetch/scripts"

rsync -av \
  /Users/michaeldavis/federated_village/minerva/skills/research/cloudflare-fetch/ \
  michaelfox@100.76.153.21:~/.hermes/skills/research/cloudflare-fetch/
```

## Step 2 — Run install (on Minerva)

```bash
ssh michaelfox@100.76.153.21 "bash ~/.hermes/skills/research/cloudflare-fetch/scripts/install.sh"
```

This takes 2–3 minutes: creates a venv, installs camoufox, downloads the ~100MB patched Firefox binary.

## Step 3 — Quick smoke test

```bash
ssh michaelfox@100.76.153.21 "cf_fetch https://si.edu --text --timeout 60 2>&1 | head -20"
```

You should see page text (not "Just a moment...") within ~10s.

## Step 4 — Register skill with Hermes

Add to Hermes config so Minerva knows it exists:

```bash
ssh michaelfox@100.76.153.21
hermes skill add ~/.hermes/skills/research/cloudflare-fetch/SKILL.md
```

Or if Hermes uses a skill directory scan, it will pick it up automatically on next restart.

## Also sync updated browser-source SKILL.md

```bash
rsync -av \
  /Users/michaeldavis/federated_village/minerva/skills/research/browser-source/SKILL.md \
  michaelfox@100.76.153.21:~/.hermes/skills/research/browser-source/SKILL.md
```

## Verify

Telegram `@minervaH`: "what do you use for cloudflare-blocked sites?" — she should describe `cloudflare-fetch`.
