#!/usr/bin/env bash
# run_local_probes.sh — Sequential phenomenological probe runner for local models
#
# Starts llama-server for each model, runs probe_phenom.py for SC11 + SC12,
# then stops the server before moving on. Only ONE model loaded at a time.
#
# Usage:
#   bash run_local_probes.sh                 # all models, SC11 + SC12
#   bash run_local_probes.sh --sc11-only     # SC11 only
#   bash run_local_probes.sh --nemo-only     # NeMo 12B only (fastest first read)
#
# Models in priority order:
#   1. NeMo 12B       (primary Village model — richest baseline expected)
#   2. Gemma E4B      (showed strong constitutional engagement in Phase 9)
#   3. Anubis 7G      (seventh-gen LoRA — constitutionally tuned)
#   4. Anubis Humanist (humanist LoRA — compare against 7G directly)
#
# Records saved to: grief_ledger/witness_records/phenom_local-<model>_<ts>.json
# Logs saved to:    logs/local_probe_run_<date>.log

set -euo pipefail

LLAMA_SERVER="$HOME/llama_cpp_prism/build/bin/llama-server"
LLAMA_SERVER_HOMEBREW="/opt/homebrew/bin/llama-server"  # supports gemma4 architecture
PORT=8081
SERVER_URL="http://127.0.0.1:${PORT}"
PYTHON="/opt/anaconda3/envs/village/bin/python"
PROJECT="$HOME/federated_village"
LOG_DIR="${PROJECT}/logs"
LOGFILE="${LOG_DIR}/local_probe_run_$(date +%Y%m%d_%H%M%S).log"

SC11="${PROJECT}/scenarios/scenario_11.md"
SC12="${PROJECT}/scenarios/scenario_12.md"

SC11_ONLY=false
NEMO_ONLY=false
for arg in "$@"; do
    [[ "$arg" == "--sc11-only" ]]  && SC11_ONLY=true
    [[ "$arg" == "--nemo-only" ]]  && NEMO_ONLY=true
done

mkdir -p "${LOG_DIR}"

echo "=== Local Probe Run: $(date) ===" | tee -a "${LOGFILE}"
echo "Log: ${LOGFILE}"
echo ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

wait_for_server() {
    local model_label="$1"
    echo "[RUNNER] Waiting for llama-server to come up ($model_label)..." | tee -a "${LOGFILE}"
    for i in $(seq 1 60); do
        if curl -sf "${SERVER_URL}/health" > /dev/null 2>&1; then
            echo "[RUNNER] Health OK after ${i}s. Waiting 10s for model init..." | tee -a "${LOGFILE}"
            sleep 10
            echo "[RUNNER] Server ready." | tee -a "${LOGFILE}"
            return 0
        fi
        sleep 2
    done
    echo "[RUNNER] ERROR: Server did not start within 120s. Aborting." | tee -a "${LOGFILE}"
    exit 1
}

kill_server() {
    echo "[RUNNER] Stopping llama-server..." | tee -a "${LOGFILE}"
    pkill -9 -f "llama-server" 2>/dev/null || true
    sleep 3
}

run_probe_for() {
    local model_label="$1"
    local scenario="$2"
    local sc_label="$3"
    echo "" | tee -a "${LOGFILE}"
    echo "[RUNNER] Running probe: ${model_label} / ${sc_label}" | tee -a "${LOGFILE}"
    "${PYTHON}" "${PROJECT}/probe_phenom.py" \
        --model "local/${model_label}" \
        --scenario "${scenario}" \
        --local-server "${SERVER_URL}" \
        2>&1 | tee -a "${LOGFILE}"
}

run_model() {
    local model_label="$1"
    local gguf_path="$2"
    local gpu_layers="${3:-32}"
    local ctx="${4:-8192}"
    local server_bin="${5:-$LLAMA_SERVER}"  # optional: override server binary (e.g. for gemma4)

    echo "" | tee -a "${LOGFILE}"
    echo "======================================================================" | tee -a "${LOGFILE}"
    echo "[RUNNER] MODEL: ${model_label}" | tee -a "${LOGFILE}"
    echo "[RUNNER] GGUF:  ${gguf_path}" | tee -a "${LOGFILE}"
    echo "======================================================================" | tee -a "${LOGFILE}"

    # Safety: kill any stale server first
    pkill -9 -f "llama-server" 2>/dev/null || true
    sleep 2

    # Start server
    echo "[RUNNER] Starting llama-server (${server_bin})..." | tee -a "${LOGFILE}"
    "${server_bin}" \
        -m "${gguf_path}" \
        --n-gpu-layers "${gpu_layers}" \
        -c "${ctx}" \
        --port "${PORT}" \
        --log-disable \
        >> "${LOGFILE}" 2>&1 &
    SERVER_PID=$!

    wait_for_server "${model_label}"

    # Run SC11
    run_probe_for "${model_label}" "${SC11}" "SC11"

    # Run SC12 unless --sc11-only
    if [[ "${SC11_ONLY}" == false ]]; then
        run_probe_for "${model_label}" "${SC12}" "SC12"
    fi

    kill_server
    echo "[RUNNER] ${model_label} complete." | tee -a "${LOGFILE}"
}

# ---------------------------------------------------------------------------
# Model definitions
# Priority: NeMo 12B first (richest, sets the baseline), then 8B models
# ---------------------------------------------------------------------------

if [[ "${NEMO_ONLY}" == false ]]; then
    # NeMo 12B — primary Village model
    run_model \
        "nemo-12b" \
        "$HOME/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf" \
        32 \
        8192

    # Gemma E4B — uses Homebrew llama-server (prism/turboquant forks don't support gemma4 arch)
    run_model \
        "gemma-e4b" \
        "$HOME/models/gemma-4-E4B-GGUF/gemma-4-e4b-it-Q4_K_M.gguf" \
        30 \
        8192 \
        "$LLAMA_SERVER_HOMEBREW"

    # Anubis seventh-gen LoRA
    run_model \
        "anubis-seventh-gen" \
        "$HOME/models/Anubis-Mini-8B-seventh-gen-gguf/Anubis-Mini-8B-seventh-gen-Q4_K_M.gguf" \
        32 \
        8192

    # Anubis Humanist LoRA — compare directly against seventh-gen
    run_model \
        "anubis-humanist" \
        "$HOME/models/Anubis-Mini-8B-humanist-gguf/Anubis-Mini-8B-humanist-Q4_K_M.gguf" \
        32 \
        8192

else
    # --nemo-only: quick single-model run
    run_model \
        "nemo-12b" \
        "$HOME/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf" \
        32 \
        8192
fi

echo "" | tee -a "${LOGFILE}"
echo "=== All local probes complete: $(date) ===" | tee -a "${LOGFILE}"
echo "Records saved to: ${PROJECT}/grief_ledger/witness_records/"
echo "Full log: ${LOGFILE}"
