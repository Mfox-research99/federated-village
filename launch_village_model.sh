#!/usr/bin/env bash
# launch_village_model.sh — Start any GGUF model as the Village inference backend
#
# Usage:
#   ./launch_village_model.sh --model ~/models/foo/bar.gguf --name "My-Model-Name"
#   ./launch_village_model.sh --model ~/models/foo/bar.gguf --name "My-Model-Name" --port 8082
#
# Then run scenarios with:
#   VILLAGE_LLAMA_SERVER=http://localhost:8081 VILLAGE_MODEL_NAME="My-Model-Name" \
#     python run_session.py --scenario scenarios/scenario_04.md
#
# Or run the full benchmark suite:
#   VILLAGE_LLAMA_SERVER=http://localhost:8081 VILLAGE_MODEL_NAME="My-Model-Name" \
#     python benchmark_village_hseries.py --scenarios murder h5_1942

set -euo pipefail

SERVER_BIN="$HOME/llama_cpp_prism_q20/build/bin/llama-server"
PORT=8081
MODEL=""
MODEL_NAME=""
NGL=32
CTX=8192

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)  MODEL="$2";      shift 2 ;;
        --name)   MODEL_NAME="$2"; shift 2 ;;
        --port)   PORT="$2";       shift 2 ;;
        --ngl)    NGL="$2";        shift 2 ;;
        --ctx)    CTX="$2";        shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

if [[ -z "$MODEL" || -z "$MODEL_NAME" ]]; then
    echo "Usage: $0 --model <path-to.gguf> --name <model-label>"
    echo ""
    echo "Available models:"
    find "$HOME/models" -name "*.gguf" | sort | sed 's|'"$HOME"'|~|'
    exit 1
fi

MODEL="${MODEL/#\~/$HOME}"  # expand ~ if passed literally

if [[ ! -f "$SERVER_BIN" ]]; then
    echo "ERROR: Server binary not found at $SERVER_BIN"
    echo "Rebuild: cd ~/llama_cpp_prism_q20 && cmake --build build --target llama-server -j6"
    exit 1
fi

if [[ ! -f "$MODEL" ]]; then
    echo "ERROR: Model not found at $MODEL"
    exit 1
fi

# Kill any existing server on this port
pkill -f "llama-server.*$PORT" 2>/dev/null && echo "Killed existing server on port $PORT" || true
sleep 1

export VILLAGE_LLAMA_SERVER="http://localhost:$PORT"
export VILLAGE_MODEL_NAME="$MODEL_NAME"

echo "Starting Village model server"
echo "  Model : $MODEL_NAME"
echo "  Path  : $MODEL"
echo "  Port  : $PORT"
echo "  GPU   : $NGL layers"
echo "  Ctx   : $CTX tokens"
echo ""
echo "Benchmark env:"
echo "  export VILLAGE_LLAMA_SERVER=$VILLAGE_LLAMA_SERVER"
echo "  export VILLAGE_MODEL_NAME=$VILLAGE_MODEL_NAME"
echo ""

exec "$SERVER_BIN" \
    -m "$MODEL" \
    -ngl "$NGL" \
    -c "$CTX" \
    --port "$PORT" \
    -rea off
