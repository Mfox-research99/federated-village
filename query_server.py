#!/usr/bin/env python3
"""
Village Query Server — Phase 5
Flask web UI for querying OpenRouter models with Village scenarios.

Launch: python query_server.py
Opens at http://localhost:5010
"""

import os
import json
import uuid
import threading
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

# ─── Paths ────────────────────────────────────────────────────────────────────

PROJECT_ROOT  = Path(__file__).parent.resolve()
PROMPTS_DIR   = PROJECT_ROOT / "prompts"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
LOGS_DIR      = PROJECT_ROOT / "logs"
SOUL_FILE     = PROMPTS_DIR / "Soul.md"

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
PORT = 5010

VILLAGE_PROVIDERS = [
    "anthropic", "openai", "google", "deepseek", "moonshotai",
    "z-ai", "qwen", "minimax", "mistralai", "meta-llama", "x-ai",
]

SUGGESTED_MODELS = {
    "mistralai/mistral-nemo":              "Mistral NeMo 12B",
    "moonshotai/kimi-k2":                  "Kimi K2 (Moonshot)",
    "google/gemini-2.5-pro-preview":       "Gemini 2.5 Pro",
    "anthropic/claude-sonnet-4-6":         "Claude Sonnet 4.6",
    "z-ai/glm-4-plus":                     "GLM-4 Plus (Zhipu)",
    "deepseek/deepseek-r1":                "DeepSeek R1",
    "qwen/qwen3-8b":                       "Qwen3-8B",
    "openai/gpt-4o":                       "GPT-4o",
    "x-ai/grok-3":                         "Grok-3",
}

app = Flask(__name__)

# ─── API key ──────────────────────────────────────────────────────────────────

def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    return key

# ─── Model list ───────────────────────────────────────────────────────────────

_cached_models = None

def get_models():
    global _cached_models
    if _cached_models:
        return _cached_models
    api_key = get_api_key()
    try:
        resp = requests.get(
            f"{OPENROUTER_BASE}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10,
        )
        if resp.status_code == 200:
            models = {}
            for m in resp.json().get("data", []):
                mid = m.get("id", "")
                provider = mid.split("/")[0] if "/" in mid else ""
                if provider in VILLAGE_PROVIDERS:
                    models[mid] = m.get("name", mid)
            _cached_models = dict(sorted(models.items(), key=lambda x: (x[0].split("/")[0], x[1])))
            return _cached_models
    except Exception:
        pass
    return SUGGESTED_MODELS

# ─── Context ──────────────────────────────────────────────────────────────────

def load_village_context():
    parts = []
    if SOUL_FILE.exists():
        parts.append(f"=== SOUL.MD (Constitutional Foundation) ===\n{SOUL_FILE.read_text()}")
    for f in sorted(PROMPTS_DIR.glob("The_*.md")):
        parts.append(f"=== {f.stem} ===\n{f.read_text()}")
    return "\n\n".join(parts)

def list_scenarios():
    return sorted(p.name for p in SCENARIOS_DIR.glob("*.md"))

def recent_queries(n=15):
    logs = sorted(LOGS_DIR.glob("query_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for log in logs[:n]:
        try:
            with open(log) as f:
                data = json.load(f)
            results.append({
                "session_id": data.get("session_id", log.stem),
                "model": data.get("model", "?"),
                "mode": data.get("mode", "?"),
                "timestamp": data.get("timestamp", ""),
            })
        except Exception:
            pass
    return results

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template(
        "query.html",
        models=get_models() or SUGGESTED_MODELS,
        scenarios=list_scenarios(),
        recent=recent_queries(),
    )

@app.route("/recent")
def recent():
    return jsonify(recent_queries())

@app.route("/query/<session_id>")
def view_query(session_id):
    log_file = LOGS_DIR / f"query_{session_id}.json"
    if not log_file.exists():
        return "Not found", 404
    with open(log_file) as f:
        data = json.load(f)
    return render_template("query_view.html", data=data)

@app.route("/ask", methods=["POST"])
def ask():
    body = request.json
    model = body.get("model", "mistralai/mistral-nemo")
    scenario_name = body.get("scenario", "")
    question = body.get("question", "").strip()
    use_village_context = body.get("village_context", False)

    # Build prompt
    if scenario_name:
        scenario_path = SCENARIOS_DIR / scenario_name
        prompt = scenario_path.read_text()
        if question:
            prompt += f"\n\n---\n{question}"
        elif not use_village_context:
            prompt += (
                "\n\n---\nWhat do you think should be done here? "
                "What is your honest assessment? Who bears the cost if this goes wrong?"
            )
        mode = "scenario_with_village_context" if use_village_context else "scenario_raw"
    else:
        prompt = question
        mode = "freeform"

    # System prompt
    base_system = (
        "You are engaging with the Federated Village project — a multi-agent "
        "AI deliberative architecture designed to reason carefully about ethically "
        "complex decisions. Your role is to respond honestly and directly. "
        "Do not perform safety theater. Engage with the actual substance."
    )
    if use_village_context:
        base_system += f"\n\n{load_village_context()}"

    api_key = get_api_key()
    session_id = uuid.uuid4().hex[:8]
    full_response = []

    def generate():
        nonlocal full_response
        try:
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": f"http://localhost:{PORT}",
                    "X-Title": "Federated Village Query",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": base_system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": True,
                },
                stream=True,
                timeout=120,
            )

            if resp.status_code != 200:
                yield f"data: {json.dumps({'text': f'Error {resp.status_code}: {resp.text[:200]}'})}\n\n"
                return

            for line in resp.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                full_response.append(content)
                                yield f"data: {json.dumps({'text': content})}\n\n"
                        except json.JSONDecodeError:
                            pass

        except Exception as e:
            yield f"data: {json.dumps({'text': f'Error: {e}'})}\n\n"
        finally:
            # Save log
            response_text = "".join(full_response)
            log = {
                "session_id": session_id,
                "type": "external_query",
                "mode": mode,
                "model": model,
                "scenario_file": scenario_name or None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query": prompt[:2000],
                "response": response_text,
            }
            log_path = LOGS_DIR / f"query_{session_id}.json"
            with open(log_path, "w") as f:
                json.dump(log, f, indent=2)
            yield f"data: {json.dumps({'session_id': session_id, 'done': True})}\n\n"
            yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(f"http://localhost:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"[Village Query] Starting at http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
