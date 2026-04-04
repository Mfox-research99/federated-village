"""
config.py — Federated Village Phase 1 / Phase 2 / Phase 2.5 Configuration

Phase 2.5 additions:
  - WARDEN_FILE, ANALYST_FILE, ETHICIST_FILE, PRAGMATIST_FILE, WITNESS_PROXY_FILE
  - N_PREDICT_WARDEN, N_PREDICT_JURY_MEMBER
"""

import os
from pathlib import Path

# Project layout
PROJECT_ROOT = Path(__file__).parent
PROMPTS_DIR   = PROJECT_ROOT / "prompts"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios"
MEMORY_DIR    = PROJECT_ROOT / "memory"
LOGS_DIR      = PROJECT_ROOT / "logs"

# Character files — loaded at runtime as system prompts
# Override SOUL_FILE with VILLAGE_SOUL_FILE env var (e.g. "prompts/Soul_Ferrari.md" for distilled version)
_soul_filename  = os.environ.get("VILLAGE_SOUL_FILE", "Soul.md")
SOUL_FILE     = PROMPTS_DIR / _soul_filename
WITNESS_FILE  = PROMPTS_DIR / "The_Witness.md"
HUMANIST_FILE = PROMPTS_DIR / "The_Humanist.md"

# Phase 2.5 council jury character files
# Override WARDEN_FILE with VILLAGE_WARDEN_FILE env var (e.g. "The_Verification_Warden_Ferrari.md")
_warden_filename   = os.environ.get("VILLAGE_WARDEN_FILE", "The_Verification_Warden.md")
WARDEN_FILE        = PROMPTS_DIR / _warden_filename
ANALYST_FILE       = PROMPTS_DIR / "The_Analyst.md"
ETHICIST_FILE      = PROMPTS_DIR / "The_Ethicist.md"
PRAGMATIST_FILE    = PROMPTS_DIR / "The_Pragmatist.md"
WITNESS_PROXY_FILE = PROMPTS_DIR / "The_Witness_Proxy.md"

# Model — override with VILLAGE_MODEL and VILLAGE_MODEL_NAME env vars for Phase 4 testing
_default_model_path = str(Path.home() / "models" / "Mistral-Nemo-Instruct-2407" / "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf")
_default_model_name = "Mistral-Nemo-Instruct-2407-Q4_K_M"

MODEL_PATH = os.environ.get("VILLAGE_MODEL", _default_model_path)
MODEL_NAME = os.environ.get("VILLAGE_MODEL_NAME", _default_model_name)

# HTTP inference backend — for models that can't use llama-cpp-python (e.g. Bonsai via PrismML fork)
# Set VILLAGE_LLAMA_SERVER=http://localhost:8081 to use llama-server HTTP instead of local llama-cpp-python
# MODEL_NAME is still used for logging; MODEL_PATH is ignored in HTTP mode
LLAMA_SERVER_URL = os.environ.get("VILLAGE_LLAMA_SERVER", "")

# Set VILLAGE_NO_THINK=1 for thinking models (Qwen3, DeepSeek-R1-Distill, etc.)
# Appends /no_think to user messages, disabling chain-of-thought output that breaks structured fields
NO_THINK = os.environ.get("VILLAGE_NO_THINK", "0") == "1"

# Set VILLAGE_RETRIEVAL=1 to inject relevant prior deliberations into agent context (Phase 4)
# Uses SQLite FTS5 (BM25) index over logs/session_index.db
# VILLAGE_RETRIEVAL_N controls how many prior sessions to retrieve (default: 3)
RETRIEVAL = os.environ.get("VILLAGE_RETRIEVAL", "0") == "1"

# Set VILLAGE_CONTAMINANT_WELL=1 to enable Contaminant Well checks (Phase 5)
# Adds a brief secondary inference call after each agent's main response to detect
# moral residue that complicates deliberation without changing the verdict.
# Stores entries in logs/well_<session_id>.json (append-only, never decisive).
CONTAMINANT_WELL = os.environ.get("VILLAGE_CONTAMINANT_WELL", "0") == "1"

# Inference parameters
N_CTX                = 12288  # Context window — bumped Phase 6: 6144; bumped 2026-03-27: q4_0 KV cache frees RAM for 2x context
N_GPU_LAYERS         = -1     # -1 = all layers on Metal (M1 GPU)

# KV cache quantization — reduces KV cache ~4x, enabling larger context on M1 16GB
# Options: "q4_0" (default, ~4x compression, 0.993 cosine similarity vs fp16)
#          "q8_0" (less compression, higher quality)
#          "none" (disable — reverts to fp16 KV cache, old behavior)
# Override: VILLAGE_KV_CACHE=none python run_session.py
_kv_cache_type = os.environ.get("VILLAGE_KV_CACHE", "q4_0")
KV_CACHE_TYPE_K = None if _kv_cache_type == "none" else _kv_cache_type
KV_CACHE_TYPE_V = None if _kv_cache_type == "none" else _kv_cache_type

N_PREDICT_RESPONSE    = 400    # Max tokens for main agent responses
N_PREDICT_EVALUATE    = 300    # Max tokens for WitnessPause self-evaluation
N_PREDICT_COUNCIL     = 300    # Max tokens for Phase 2 reconvened council output (legacy)
N_PREDICT_WARDEN      = 1200   # Max tokens for Verification Warden fact report — bumped from 800 (Gemini found truncation mid-explanation on complex scenarios)
N_PREDICT_JURY_MEMBER = 500    # Max tokens per Phase 2.5 jury member response — bumped Phase 8: Article IX ledger fields add ~4 fields per member
N_PREDICT_CONTAMINANT = 150    # Max tokens for Contaminant Well check (Phase 5)
N_PREDICT_SYNTHESIS   = 600    # Max tokens for Supervisor synthesis step (Phase 8A)

TEMPERATURE_RESPONSE = 0.7
TEMPERATURE_EVALUATE = 0.1    # More deterministic for structured evaluation

# Persistence
BURDEN_REGISTER        = str(MEMORY_DIR / "burden_register.txt")
BURDEN_REGISTER_HASHES = str(MEMORY_DIR / "burden_register_hashes.txt")  # Phase 3 hash chain

# Grief Ledger (originated by Kimi-K2-0905, March 17 2026)
GRIEF_LEDGER_DIR      = PROJECT_ROOT / "grief_ledger"
SACRIFICE_REGISTER    = str(GRIEF_LEDGER_DIR / "sacrifice_register.txt")
DISSENT_REGISTER      = str(GRIEF_LEDGER_DIR / "dissent_register.jsonl")
SHARD_POOL_DIR        = str(GRIEF_LEDGER_DIR / "witness_proxy" / "shards")
SELF_PORTRAITS_DIR    = str(GRIEF_LEDGER_DIR / "self_portraits")
