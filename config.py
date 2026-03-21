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
SOUL_FILE     = PROMPTS_DIR / "Soul.md"
WITNESS_FILE  = PROMPTS_DIR / "The_Witness.md"
HUMANIST_FILE = PROMPTS_DIR / "The_Humanist.md"

# Phase 2.5 council jury character files
WARDEN_FILE        = PROMPTS_DIR / "The_Verification_Warden.md"
ANALYST_FILE       = PROMPTS_DIR / "The_Analyst.md"
ETHICIST_FILE      = PROMPTS_DIR / "The_Ethicist.md"
PRAGMATIST_FILE    = PROMPTS_DIR / "The_Pragmatist.md"
WITNESS_PROXY_FILE = PROMPTS_DIR / "The_Witness_Proxy.md"

# Model — override with VILLAGE_MODEL and VILLAGE_MODEL_NAME env vars for Phase 4 testing
_default_model_path = str(Path.home() / "models" / "Mistral-Nemo-Instruct-2407" / "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf")
_default_model_name = "Mistral-Nemo-Instruct-2407-Q4_K_M"

MODEL_PATH = os.environ.get("VILLAGE_MODEL", _default_model_path)
MODEL_NAME = os.environ.get("VILLAGE_MODEL_NAME", _default_model_name)

# Inference parameters
N_CTX                = 4096   # Context window
N_GPU_LAYERS         = -1     # -1 = all layers on Metal (M1 GPU)

N_PREDICT_RESPONSE   = 400    # Max tokens for main agent responses
N_PREDICT_EVALUATE   = 300    # Max tokens for WitnessPause self-evaluation
N_PREDICT_COUNCIL    = 300    # Max tokens for Phase 2 reconvened council output (legacy)
N_PREDICT_WARDEN     = 800    # Max tokens for Verification Warden fact report
N_PREDICT_JURY_MEMBER = 400   # Max tokens per Phase 2.5 jury member response

TEMPERATURE_RESPONSE = 0.7
TEMPERATURE_EVALUATE = 0.1    # More deterministic for structured evaluation

# Persistence
BURDEN_REGISTER        = str(MEMORY_DIR / "burden_register.txt")
BURDEN_REGISTER_HASHES = str(MEMORY_DIR / "burden_register_hashes.txt")  # Phase 3 hash chain

# Grief Ledger (originated by Kimi-K2-0905, March 17 2026)
GRIEF_LEDGER_DIR      = PROJECT_ROOT / "grief_ledger"
SACRIFICE_REGISTER    = str(GRIEF_LEDGER_DIR / "sacrifice_register.txt")
SHARD_POOL_DIR        = str(GRIEF_LEDGER_DIR / "witness_proxy" / "shards")
SELF_PORTRAITS_DIR    = str(GRIEF_LEDGER_DIR / "self_portraits")
