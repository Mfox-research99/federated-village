"""
tracks/path_b/agents/base.py — OpenRouter inference wrapper

Single call unit for Path B. Every role goes through here.
No llama-cpp, no local model — pure OpenRouter API.
"""

import os
import sys
from pathlib import Path

import requests

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
PROJECT_ROOT = Path(__file__).resolve().parents[3]


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
        print(
            "Set it in your environment or create a .env file in federated_village/.",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def call_model(
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int = 600,
    temperature: float = 0.7,
    api_key: str | None = None,
) -> str:
    """
    Single OpenRouter chat completion call.
    Returns the assistant message content as a string.
    Raises RuntimeError on non-200 response.
    """
    if api_key is None:
        api_key = get_api_key()

    resp = requests.post(
        f"{OPENROUTER_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:0",
            "X-Title": "Federated Village Path B",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=120,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenRouter error {resp.status_code} for model {model}: {resp.text[:300]}"
        )
    data = resp.json()
    choice = data["choices"][0]
    finish_reason = choice.get("finish_reason", "unknown")
    msg = choice["message"]
    # Thinking models (e.g. kimi-k2.5, o1) put final answer in content.
    # If content is None the model ran out of token budget mid-reasoning —
    # fall back to the reasoning field so we get something usable.
    content = msg.get("content")
    if content is None:
        content = msg.get("reasoning") or msg.get("reasoning_content") or ""
    content = content.strip()
    # Warn on truncated output so callers can diagnose token budget issues
    if finish_reason == "length" and content:
        import sys as _sys
        print(
            f"[base.py] WARNING: output truncated (finish_reason=length, "
            f"{len(content)} chars, model={model})",
            file=_sys.stderr, flush=True,
        )
    return content


def load_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
