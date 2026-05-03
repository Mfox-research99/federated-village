#!/usr/bin/env bash
# install.sh — one-time setup for cloudflare-fetch on Minerva (Mac Pro 2013)
# Run as: bash ~/.hermes/skills/research/cloudflare-fetch/scripts/install.sh

set -euo pipefail

SKILL_DIR="$HOME/.hermes/skills/research/cloudflare-fetch"
SCRIPTS_DIR="$SKILL_DIR/scripts"

echo "=== cloudflare-fetch install ==="

# 1. Install camoufox into a dedicated venv alongside the skill
if [ ! -d "$SKILL_DIR/.venv" ]; then
    echo "Creating venv at $SKILL_DIR/.venv ..."
    python3 -m venv "$SKILL_DIR/.venv"
fi

echo "Installing camoufox ..."
"$SKILL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SKILL_DIR/.venv/bin/pip" install --quiet camoufox playwright

# 2. Download the patched Firefox binary (~100MB, stored in ~/.camoufox/)
echo "Downloading Camoufox patched Firefox binary (~100MB) ..."
"$SKILL_DIR/.venv/bin/python" -m camoufox fetch

# 3. Write a launcher wrapper so Hermes can call it without activating the venv
WRAPPER="$HOME/bin/cf_fetch"
mkdir -p "$HOME/bin"
cat > "$WRAPPER" << EOF
#!/usr/bin/env bash
# cf_fetch — wrapper for cloudflare-fetch skill
exec "$SKILL_DIR/.venv/bin/python" "$SCRIPTS_DIR/cf_fetch.py" "\$@"
EOF
chmod +x "$WRAPPER"

echo ""
echo "=== Done ==="
echo "Run: cf_fetch <url> --text"
echo "Or:  python $SCRIPTS_DIR/cf_fetch.py <url>"
echo ""
echo "Camoufox binary stored at: ~/.camoufox/"
echo "Venv at: $SKILL_DIR/.venv"
