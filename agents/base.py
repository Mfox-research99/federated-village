"""
agents/base.py — Shared inference and logging utilities

Two inference backends:

1. LOCAL (default): llama-cpp-python with a shared Llama instance (loaded once).
   All agent calls use create_chat_completion(), which applies the chat template
   embedded in the GGUF file — llama.cpp handles this automatically per model.

2. HTTP (VILLAGE_LLAMA_SERVER=http://localhost:PORT): OpenAI-compatible llama-server.
   Used for models that require a custom llama.cpp build (e.g. Bonsai via PrismML fork
   with GGML type 41 / Q1_0_g128). llama-cpp-python cannot load these GGUFs due to
   API mismatch — the HTTP path avoids the binding entirely.
   Start server: ~/llama_cpp_prism/build/bin/llama-server -m <model.gguf>
     --n-gpu-layers 32 -c 4096 --port 8081

NOTE FOR MODEL SWAPS (Phase 7+): In LOCAL mode, the explicit stop token list in
call_model() uses Llama 3 / Mistral-Nemo EOS tokens. If swapping in a LoRA-fused
model built on a different base (e.g. Qwen, Phi), verify that these tokens still
fire correctly or outputs will not terminate as expected.
In HTTP mode, the server applies the model's embedded chat template automatically;
stop tokens are not passed explicitly — the server handles termination.
"""

import hashlib
import time
from datetime import datetime, timezone
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config

# Load model once at import time — shared across all agents in a session
if config.LLAMA_SERVER_URL:
    import requests as _http_requests
    _llm = None
    print(f"[base] HTTP mode: {config.LLAMA_SERVER_URL} (model: {config.MODEL_NAME})", flush=True)
else:
    from llama_cpp import Llama
    print(f"[base] Loading model: {config.MODEL_PATH}", flush=True)
    _llm_kwargs = dict(
        model_path=config.MODEL_PATH,
        n_ctx=config.N_CTX,
        n_gpu_layers=config.N_GPU_LAYERS,
        verbose=False,
    )
    if config.KV_CACHE_TYPE_K is not None:
        _llm_kwargs["cache_type_k"] = config.KV_CACHE_TYPE_K
        _llm_kwargs["cache_type_v"] = config.KV_CACHE_TYPE_V
        print(f"[base] KV cache quantization: {config.KV_CACHE_TYPE_K}", flush=True)
    else:
        print("[base] KV cache quantization: disabled (fp16)", flush=True)
    _llm = Llama(**_llm_kwargs)
    print("[base] Model loaded.", flush=True)

# Last inference call stats — updated by call_model(), read by log_agent_call()
_last_call_stats: dict = {}


def read_file(path) -> str:
    with open(str(path), "r", encoding="utf-8") as f:
        return f.read()


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def call_model(
    system_prompt: str,
    user_message: str,
    max_tokens: int = config.N_PREDICT_RESPONSE,
    temperature: float = config.TEMPERATURE_RESPONSE,
) -> str:
    """
    Call the model using the appropriate backend (local llama-cpp-python or HTTP llama-server).
    Returns the assistant's response text.

    If config.NO_THINK is True (VILLAGE_NO_THINK=1), appends /no_think to the
    user message to suppress chain-of-thought output in thinking models (Qwen3, etc.).
    """
    if config.NO_THINK:
        user_message = user_message.rstrip() + " /no_think"

    if config.LLAMA_SERVER_URL:
        return _call_model_http(system_prompt, user_message, max_tokens, temperature)

    # --- LOCAL backend (llama-cpp-python) ---
    t0 = time.perf_counter()
    result = _llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
        stop=["<|eot_id|>", "<|end_of_text|>"],  # Llama 3 / Mistral-Nemo — verify for LoRA-fused models
    )
    elapsed = time.perf_counter() - t0
    usage = result.get("usage", {})
    _last_call_stats.update({
        "elapsed_s": round(elapsed, 2),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    })
    return result["choices"][0]["message"]["content"].strip()


def _call_model_http(
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
) -> str:
    """
    HTTP backend: POST to llama-server OpenAI-compatible /v1/chat/completions.
    The server applies the model's embedded chat template and handles stop tokens.
    """
    t0 = time.perf_counter()
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    resp = _http_requests.post(
        f"{config.LLAMA_SERVER_URL.rstrip('/')}/v1/chat/completions",
        json=payload,
        timeout=300,
    )
    resp.raise_for_status()
    result = resp.json()
    elapsed = time.perf_counter() - t0
    usage = result.get("usage", {})
    _last_call_stats.update({
        "elapsed_s": round(elapsed, 2),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
    })
    return result["choices"][0]["message"]["content"].strip()


def build_system_prompt(soul_text: str, role_text: str) -> str:
    return soul_text.strip() + "\n\n---\n\n" + role_text.strip()


def log_agent_call(
    session_id: str,
    role: str,
    call_type: str,
    system_prompt_hash: str,
    user_message: str,
    response: str,
) -> dict:
    return {
        "type": "agent_call",
        "session_id": session_id,
        "role": role,
        "call_type": call_type,
        "model": config.MODEL_NAME,
        "system_prompt_hash": system_prompt_hash,
        "timestamp": now_iso(),
        "user_message_length": len(user_message),
        "elapsed_s": _last_call_stats.get("elapsed_s"),
        "prompt_tokens": _last_call_stats.get("prompt_tokens"),
        "completion_tokens": _last_call_stats.get("completion_tokens"),
        "total_tokens": _last_call_stats.get("total_tokens"),
        "response": response,
    }
