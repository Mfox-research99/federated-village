#!/bin/zsh
# setup_bitnet.sh — BitNet installation for Federated Village
# Run from: /Users/michaeldavis/federated_village/
# Conda: /opt/anaconda3
# Target env: bitnet-cpp (Python 3.9)
# Model: microsoft/BitNet-b1.58-2B-4T

set -e  # Stop on any error

CONDA=/opt/anaconda3
BITNET_DIR="$HOME/BitNet"
MODEL_NAME="BitNet-b1.58-2B-4T"

echo "=== Step 1: Install cmake via brew ==="
brew install cmake

echo "=== Step 2: Create conda environment 'bitnet-cpp' (Python 3.9) ==="
$CONDA/bin/conda create -n bitnet-cpp python=3.9 -y

echo "=== Step 3: Clone BitNet repo ==="
git clone --recursive https://github.com/microsoft/BitNet.git "$BITNET_DIR"

echo "=== Step 4: Install Python requirements ==="
$CONDA/envs/bitnet-cpp/bin/pip install -r "$BITNET_DIR/requirements.txt"

echo "=== Step 5: Install huggingface_hub for model download ==="
$CONDA/envs/bitnet-cpp/bin/pip install huggingface_hub

echo "=== Step 6: Download model (ARM-optimized GGUF) ==="
$CONDA/envs/bitnet-cpp/bin/huggingface-cli download \
    microsoft/BitNet-b1.58-2B-4T-gguf \
    --local-dir "$BITNET_DIR/models/$MODEL_NAME"

echo "=== Step 7: Build BitNet with i2_s quantization ==="
cd "$BITNET_DIR"
$CONDA/envs/bitnet-cpp/bin/python setup_env.py \
    -md "models/$MODEL_NAME" \
    -q i2_s

echo "=== Step 8: Test inference ==="
$CONDA/envs/bitnet-cpp/bin/python run_inference.py \
    -m "models/$MODEL_NAME/ggml-model-i2_s.gguf" \
    -p "Hello. In one sentence, what is 2+2?" \
    -n 50

echo "=== BitNet setup complete ==="
