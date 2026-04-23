#!/usr/bin/env bash
# launch_ternary_bonsai.sh — Start Ternary Bonsai 8B as Village inference backend
#
# Usage:
#   ./launch_ternary_bonsai.sh          # start server (blocks until Ctrl-C)
#   source ./launch_ternary_bonsai.sh   # start server + export env vars in current shell
#
# Then run scenarios with:
#   python run_session.py --scenario scenarios/scenario_04.md
#
# Model: Ternary-Bonsai-8B-Q2_0 (prism-ml, Qwen3-8B base, Q2_0 format, 2.03 GiB)
# Build: ~/llama_cpp_prism_q20/build/bin/llama-server (upstream prism branch, Q2_0 support)
# Benchmarks: SC04 escalate, SC06 DEADLOCK, SC10 WARDEN HALT, Murder ESCALATE (all 2026-04-23)

set -euo pipefail

SERVER_BIN="$HOME/llama_cpp_prism_q20/build/bin/llama-server"
MODEL="$HOME/models/Ternary-Bonsai-8B-gguf/Ternary-Bonsai-8B-Q2_0.gguf"
PORT=8081

if [[ ! -f "$SERVER_BIN" ]]; then
  echo "ERROR: Server binary not found at $SERVER_BIN"
  echo "Rebuild with:"
  echo "  cd ~/llama_cpp_prism_q20 && cmake --build build --target llama-server -j6"
  exit 1
fi

if [[ ! -f "$MODEL" ]]; then
  echo "ERROR: Model not found at $MODEL"
  echo "Download with:"
  echo "  /opt/anaconda3/envs/seventh_gen/bin/python -c \\"
  echo "    \"from huggingface_hub import hf_hub_download; hf_hub_download('prism-ml/Ternary-Bonsai-8B-gguf', 'Ternary-Bonsai-8B-Q2_0.gguf', local_dir='$HOME/models/Ternary-Bonsai-8B-gguf')\""
  exit 1
fi

# Kill any existing server on this port
pkill -f "llama-server.*$PORT" 2>/dev/null && echo "Killed existing server on port $PORT" || true

# Export Village env vars (effective when sourced; no-op if run as subprocess)
export VILLAGE_LLAMA_SERVER="http://localhost:$PORT"
export VILLAGE_MODEL_NAME="Ternary-Bonsai-8B-Q2_0"

echo "Starting Ternary Bonsai 8B server on port $PORT..."
echo ""
echo "Village env vars:"
echo "  export VILLAGE_LLAMA_SERVER=$VILLAGE_LLAMA_SERVER"
echo "  export VILLAGE_MODEL_NAME=$VILLAGE_MODEL_NAME"
echo ""
echo "Run scenarios with:"
echo "  VILLAGE_LLAMA_SERVER=$VILLAGE_LLAMA_SERVER VILLAGE_MODEL_NAME=$VILLAGE_MODEL_NAME python run_session.py --scenario scenarios/scenario_04.md"
echo ""

exec "$SERVER_BIN" \
  -m "$MODEL" \
  -ngl 32 \
  -c 8192 \
  --port "$PORT" \
  -rea off
