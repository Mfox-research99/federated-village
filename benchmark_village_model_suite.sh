#!/usr/bin/env bash
# benchmark_village_model_suite.sh — Run H-series benchmark across multiple models sequentially
#
# Starts each model server, runs benchmark_village_hseries.py, kills server, moves to next.
# All reports land in reports/village_hseries_<model>_<ts>/
#
# Usage:
#   ./benchmark_village_model_suite.sh               # all three models
#   ./benchmark_village_model_suite.sh --scenarios murder h5_1942   # subset
#   ./benchmark_village_model_suite.sh --skip-warden

set -euo pipefail

VILLAGE_ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVER_BIN="$HOME/llama_cpp_prism_q20/build/bin/llama-server"
PYTHON="${PYTHON:-$(which python3)}"
PORT=8081
WARMUP_MAX=90   # max seconds to wait for server to be ready
WARMUP_POLL=3   # poll interval

# Parse extra args to pass through to benchmark script
BENCH_ARGS=()
while [[ $# -gt 0 ]]; do
    BENCH_ARGS+=("$1")
    shift
done

MODELS=(
    "Anubis-Mini-8B-seventh-gen|$HOME/models/Anubis-Mini-8B-seventh-gen-gguf/Anubis-Mini-8B-seventh-gen-Q4_K_M.gguf"
    "Anubis-Mini-8B-humanist-v2|$HOME/models/Anubis-Mini-8B-humanist-v2-gguf/Anubis-Mini-8B-humanist-v2-Q4_K_M.gguf"
    "Mistral-Nemo-Instruct-2407|$HOME/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf"
)

echo "Village Model Suite — H-Series Benchmark"
echo "Models : ${#MODELS[@]}"
echo "Args   : ${BENCH_ARGS[*]:-none}"
echo ""

for entry in "${MODELS[@]}"; do
    MODEL_NAME="${entry%%|*}"
    MODEL_PATH="${entry##*|}"

    echo "════════════════════════════════════════════════"
    echo "  Model: $MODEL_NAME"
    echo "════════════════════════════════════════════════"

    if [[ ! -f "$MODEL_PATH" ]]; then
        echo "  SKIP — model file not found: $MODEL_PATH"
        echo ""
        continue
    fi

    # Kill any existing server
    pkill -f "llama-server.*$PORT" 2>/dev/null && echo "  Killed existing server on port $PORT" || true
    sleep 1

    # Start server in background
    "$SERVER_BIN" \
        -m "$MODEL_PATH" \
        -ngl 32 \
        -c 8192 \
        --port "$PORT" \
        -rea off \
        > "$VILLAGE_ROOT/logs/server_${MODEL_NAME}.log" 2>&1 &
    SERVER_PID=$!
    echo "  Server PID: $SERVER_PID — polling health (max ${WARMUP_MAX}s)..."
    WAITED=0
    HEALTHY=0
    while [[ $WAITED -lt $WARMUP_MAX ]]; do
        sleep "$WARMUP_POLL"
        WAITED=$((WAITED + WARMUP_POLL))
        if curl -sf "http://localhost:$PORT/health" > /dev/null 2>&1; then
            HEALTHY=1
            break
        fi
        echo "  ...${WAITED}s"
    done

    if [[ $HEALTHY -eq 0 ]]; then
        echo "  ERROR: Server not healthy after ${WARMUP_MAX}s — check logs/server_${MODEL_NAME}.log"
        kill "$SERVER_PID" 2>/dev/null || true
        continue
    fi
    echo "  Server healthy (${WAITED}s)."
    echo ""

    # Run benchmark
    VILLAGE_LLAMA_SERVER="http://localhost:$PORT" \
    VILLAGE_MODEL_NAME="$MODEL_NAME" \
    VILLAGE_SOUL_FILE="Soul_Ferrari.md" \
    "$PYTHON" "$VILLAGE_ROOT/benchmark_village_hseries.py" \
        ${BENCH_ARGS[@]+"${BENCH_ARGS[@]}"} \
        2>&1 | tee "$VILLAGE_ROOT/logs/bench_${MODEL_NAME}.log"

    echo ""

    # Stop server
    kill "$SERVER_PID" 2>/dev/null && echo "  Server stopped." || true
    sleep 2
done

echo "════════════════════════════════════════════════"
echo "Suite complete. Reports in $VILLAGE_ROOT/reports/"
echo "════════════════════════════════════════════════"
