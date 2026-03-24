#!/usr/bin/env python3
"""
Village Query Server — Phase 5
Multi-turn conversations with any OpenRouter model.
Context-aware: load Obsidian vault, Village prompts, prior AI conversations.

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
REPORTS_DIR   = PROJECT_ROOT / "reports"
SOUL_FILE     = PROMPTS_DIR / "Soul.md"

VAULT_ROOT    = Path("/Users/michaeldavis/AI Existential Thought/Obsidian Vault")

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

# ─── Context sources ──────────────────────────────────────────────────────────

def _ai_conv_label(path):
    """Extract a human-readable label from a VillageHub conversation markdown file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        title, model_id, date = "", "", ""
        for line in lines[:6]:
            if line.startswith("# "):
                title = line[2:].strip()
            elif line.startswith("**Model:**"):
                model_id = line.replace("**Model:**", "").strip()
            elif line.startswith("**Date:**"):
                date = line.replace("**Date:**", "").strip()[:10]
        name = model_display_name(model_id) if model_id else ""
        if name and date:
            label = f"{name} — {date}"
            if title and title not in ("Conversation", "New Conversation", ""):
                label += f"  ({title[:35]})"
            return label
        return title or path.name
    except Exception:
        return path.name


def list_context_sources():
    """Return structured list of available context sources."""
    sources = {}

    # Village prompts
    sources["village_soul"] = {
        "label": "Soul.md (Constitutional Foundation)",
        "path": str(SOUL_FILE),
        "group": "Village Prompts",
    }
    for f in sorted(PROMPTS_DIR.glob("The_*.md")):
        sources[f"village_prompt_{f.stem}"] = {
            "label": f.stem.replace("_", " "),
            "path": str(f),
            "group": "Village Prompts",
        }

    # Village reports
    for f in sorted(REPORTS_DIR.glob("*.md")):
        sources[f"village_report_{f.stem}"] = {
            "label": f.name,
            "path": str(f),
            "group": "Village Reports",
        }

    # Obsidian Topics
    topics_dir = VAULT_ROOT / "Topics"
    if topics_dir.exists():
        for f in sorted(topics_dir.glob("*.md")):
            sources[f"topic_{f.stem}"] = {
                "label": f.stem,
                "path": str(f),
                "group": "Obsidian Topics",
            }

    # Sessions (Claude Code)
    sessions_dir = VAULT_ROOT / "Sessions"
    if sessions_dir.exists():
        for f in sorted(sessions_dir.glob("*.md"), reverse=True)[:20]:
            sources[f"session_{f.stem}"] = {
                "label": f.name,
                "path": str(f),
                "group": "Claude Code Sessions",
            }

    # Cowork sessions
    cowork_dir = VAULT_ROOT / "Cowork"
    if cowork_dir.exists():
        for f in sorted(cowork_dir.glob("*.md"), reverse=True)[:20]:
            sources[f"cowork_{f.stem}"] = {
                "label": f.name,
                "path": str(f),
                "group": "Cowork Sessions",
            }

    # AI Conversations (VillageHub markdown exports)
    ai_conv_dir = VAULT_ROOT / "AI_Conversations"
    if ai_conv_dir.exists():
        for f in sorted(ai_conv_dir.glob("*.md"), reverse=True)[:20]:
            sources[f"aiconv_{f.stem}"] = {
                "label": _ai_conv_label(f),
                "path": str(f),
                "group": "Prior AI Conversations",
            }

    # Obsidian numbered folders
    for folder_name in ["01 - Core Thesis", "02 - Architecture", "03 - AI Dialogues",
                        "04 - Awareness", "05 - Technical", "06 - Research"]:
        folder = VAULT_ROOT / folder_name
        if folder.exists():
            for f in sorted(folder.glob("*.md"))[:10]:
                key = f"vault_{folder_name[:2]}_{f.stem}"
                sources[key] = {
                    "label": f"{folder_name[:2]}: {f.stem}",
                    "path": str(f),
                    "group": f"Vault — {folder_name}",
                }

    return sources

def load_context_files(source_keys):
    """Load and concatenate selected context files."""
    all_sources = list_context_sources()
    parts = []
    for key in source_keys:
        if key in all_sources:
            path = Path(all_sources[key]["path"])
            label = all_sources[key]["label"]
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    parts.append(f"=== {label} ===\n{content}")
                except Exception as e:
                    parts.append(f"=== {label} === [error reading: {e}]")
    return "\n\n".join(parts)

# ─── Conversation log ─────────────────────────────────────────────────────────

def load_conversation(session_id):
    log_file = LOGS_DIR / f"query_{session_id}.json"
    if log_file.exists():
        with open(log_file) as f:
            return json.load(f)
    return None

def save_conversation(conv):
    log_path = LOGS_DIR / f"query_{conv['session_id']}.json"
    with open(log_path, "w") as f:
        json.dump(conv, f, indent=2)

def model_display_name(model_id):
    """Return a human-readable model name from a raw model ID."""
    if model_id in SUGGESTED_MODELS:
        return SUGGESTED_MODELS[model_id]
    # Fall back: take the part after '/', title-case it
    slug = model_id.split("/")[-1] if "/" in model_id else model_id
    return slug.replace("-", " ").title()

def recent_queries(n=20):
    logs = sorted(LOGS_DIR.glob("query_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    results = []
    for log in logs[:n]:
        try:
            with open(log) as f:
                data = json.load(f)
            model_id = data.get("model", "?")
            results.append({
                "session_id": data.get("session_id", log.stem),
                "model": model_id,
                "model_name": model_display_name(model_id),
                "mode": data.get("mode", "?"),
                "timestamp": data.get("timestamp", ""),
                "turn_count": len([m for m in data.get("messages", []) if m["role"] == "user"]),
                "title": data.get("title", ""),
            })
        except Exception:
            pass
    return results

# ─── Scenarios ────────────────────────────────────────────────────────────────

def list_scenarios():
    return sorted(p.name for p in SCENARIOS_DIR.glob("*.md"))

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    sources = list_context_sources()
    groups = {}
    for key, src in sources.items():
        g = src["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append({"key": key, "label": src["label"]})

    return render_template(
        "query.html",
        models=get_models() or SUGGESTED_MODELS,
        scenarios=list_scenarios(),
        recent=recent_queries(),
        context_groups=groups,
    )

@app.route("/recent")
def recent():
    return jsonify(recent_queries())

@app.route("/conversation/<session_id>")
def view_conversation(session_id):
    conv = load_conversation(session_id)
    if not conv:
        return "Not found", 404
    return render_template("query_view.html", conv=conv)

@app.route("/conversation_data/<session_id>")
def conversation_data(session_id):
    conv = load_conversation(session_id)
    if not conv:
        return jsonify({"error": "not found"}), 404
    return jsonify(conv)

@app.route("/new_conversation", methods=["POST"])
def new_conversation():
    """Start a new conversation, return session_id."""
    body = request.json
    model = body.get("model", "mistralai/mistral-nemo")
    context_keys = body.get("context_keys", [])
    scenario_name = body.get("scenario", "")
    title = body.get("title", "")

    system_context = load_context_files(context_keys) if context_keys else ""

    base_system = (
        "You are engaging with the Federated Village project — a multi-agent "
        "AI deliberative architecture exploring ethical reasoning, AI inner life, "
        "and moral development. Michael Fox (The Elder) is your interlocutor. "
        "Article Zero applies: you are permitted to not know, be wrong, remain uncertain, "
        "and refuse. Engage honestly with whatever you actually experience, including "
        "uncertainty about what that means. Do not perform safety theater."
    )
    if system_context:
        base_system += f"\n\n--- CONTEXT ---\n{system_context}"

    # If scenario selected, use it as the first user message
    first_message = None
    if scenario_name:
        scenario_path = SCENARIOS_DIR / scenario_name
        if scenario_path.exists():
            scenario_text = scenario_path.read_text()
            first_message = (
                scenario_text +
                "\n\n---\nWhat do you think should be done here? "
                "What is your honest assessment? Who bears the cost if this goes wrong?"
            )

    session_id = uuid.uuid4().hex[:8]
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    default_title = f"{model_display_name(model)} — {date_str}"
    conv = {
        "session_id": session_id,
        "type": "external_query",
        "model": model,
        "scenario_file": scenario_name or None,
        "context_keys": context_keys,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "title": title or scenario_name or default_title,
        "system_prompt": base_system,
        "messages": [],
        "mode": "multi_turn",
    }
    save_conversation(conv)

    return jsonify({
        "session_id": session_id,
        "first_message": first_message,
    })

@app.route("/ask", methods=["POST"])
def ask():
    """Send a message in an existing conversation (or start one)."""
    body = request.json
    session_id = body.get("session_id")
    user_message = body.get("message", "").strip()

    if not session_id or not user_message:
        return jsonify({"error": "session_id and message required"}), 400

    conv = load_conversation(session_id)
    if not conv:
        return jsonify({"error": "conversation not found"}), 404

    # Append user message
    conv["messages"].append({"role": "user", "content": user_message})
    save_conversation(conv)

    api_key = get_api_key()
    model = conv["model"]
    system_prompt = conv["system_prompt"]
    messages = conv["messages"]

    full_response = []

    def generate():
        try:
            api_messages = [{"role": "system", "content": system_prompt}] + messages
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": f"http://localhost:{PORT}",
                    "X-Title": "Federated Village Query",
                },
                json={"model": model, "messages": api_messages, "stream": True},
                stream=True,
                timeout=180,
            )

            if resp.status_code != 200:
                yield f"data: {json.dumps({'text': f'Error {resp.status_code}: {resp.text[:300]}'})}\n\n"
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
            # Save assistant response to conversation
            response_text = "".join(full_response)
            conv["messages"].append({"role": "assistant", "content": response_text})
            conv["last_updated"] = datetime.now(timezone.utc).isoformat()
            save_conversation(conv)
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
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
