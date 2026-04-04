# Village Mesh Setup — Three-Node Local Cluster

*Written 2026-04-04. Goal: get all three machines serving llama-server over Tailscale,
then wire the Village to dispatch agents across nodes.*

---

## Node Overview

| Node | Machine | Role | Model | Speed est. |
|---|---|---|---|---|
| M1 | MacBook Pro (current) | Fast Scout / Humanist | Gemma E4B, Bonsai 8B | 10–15 tok/s Metal |
| mac-pro-12 | 2012 Mac Pro, 6-core, 64GB, RX 580 (8GB) | Parallel Jury Member | Gemma E4B or Bonsai 8B | 5–15 tok/s Metal |
| mac-pro-13 | 2013 Mac Pro, 12-core, 64GB, dual FirePro D500 | Supervisor / Deep Deliberation | NeMo 12B | 2–4 tok/s CPU |

All three will communicate via **Tailscale** (stable 100.x.x.x IPs, no port forwarding needed).

---

## Phase 0 — Network (Do First)

### Tailscale on 2012 Mac Pro (only missing node)

1. Download Tailscale from tailscale.com/download → macOS pkg installer
2. Install and open → sign in with your Tailscale account
3. `tailscale up`
4. On any machine: `tailscale status` — verify all three nodes appear

**Record Tailscale IPs after this step:**
```
M1 MacBook:         100.___.___.___   (check: tailscale ip -4)
2012 Mac Pro:       100.___.___.___
2013 Mac Pro:       100.___.___.___
```

Quick connectivity test from M1:
```bash
ping -c 3 <2012-tailscale-ip>
ping -c 3 <2013-tailscale-ip>
```

---

## Phase 1 — Build llama-server on 2012 Mac Pro

> NOTE: M1 binaries are ARM64. They will NOT run on Intel Mac Pros. Must build on each machine.

### Step 1.1 — Xcode Command Line Tools
```bash
xcode-select --install
# If already installed, this will say so — that's fine
```

### Step 1.2 — Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install cmake git
```

### Step 1.3 — Clone and build llama.cpp (mainline, Intel + Metal)
```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_METAL=ON -DLLAMA_NATIVE=OFF
cmake --build build --config Release -j6
# -j6 = 6 cores, adjust to your core count
```

Binary will be at: `~/llama.cpp/build/bin/llama-server`

Quick sanity check:
```bash
~/llama.cpp/build/bin/llama-server --version
```

---

## Phase 2 — Build llama-server on 2013 Mac Pro

Same steps as Phase 1, but on the 2013 machine.

The dual FirePro D500 cards have only 3GB VRAM each — too small for a full model.
Run CPU-only inference using the 64GB system RAM + 12-core Xeon.

```bash
cd ~
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DLLAMA_METAL=OFF   # CPU only — skip Metal for D500
cmake --build build --config Release -j12
```

> If you want to experiment with Metal on D500 later, rebuild with `-DLLAMA_METAL=ON` and
> use `--n-gpu-layers 10` (partial offload). But CPU-only is the reliable path for now.

---

## Phase 3 — Copy Model Files

Models live on the M1 at `~/models/`. Copy to each Mac Pro over Tailscale via scp.

### 2012 Mac Pro — Gemma E4B (fast Metal model, ~3.5GB)
Run this from the **M1**:
```bash
# Create models dir on 2012 Mac Pro first
ssh <your-username>@<2012-tailscale-ip> "mkdir -p ~/models/gemma4-e4b-gguf"

# Copy the model
scp ~/models/gemma4-e4b-gguf/gemma-4-e4b-it-Q4_K_M.gguf \
    <your-username>@<2012-tailscale-ip>:~/models/gemma4-e4b-gguf/
```

Optional — also copy Bonsai 8B if you want it available on the 2012 node:
```bash
ssh <your-username>@<2012-tailscale-ip> "mkdir -p ~/models/Bonsai-8B-gguf"
scp ~/models/Bonsai-8B-gguf/Bonsai-8B.gguf \
    <your-username>@<2012-tailscale-ip>:~/models/Bonsai-8B-gguf/
```

### 2013 Mac Pro — NeMo 12B (large CPU model, ~7GB)
Run this from the **M1**:
```bash
ssh <your-username>@<2013-tailscale-ip> "mkdir -p ~/models/Mistral-Nemo-Instruct-2407"

scp ~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf \
    <your-username>@<2013-tailscale-ip>:~/models/Mistral-Nemo-Instruct-2407/
```

---

## Phase 4 — Test llama-server on Each Node

### 2012 Mac Pro — Metal inference test
SSH in, then:
```bash
~/llama.cpp/build/bin/llama-server \
  -m ~/models/gemma4-e4b-gguf/gemma-4-e4b-it-Q4_K_M.gguf \
  --n-gpu-layers 32 \
  -c 4096 \
  --host 0.0.0.0 \
  --port 8081
```

From the M1, verify it's reachable:
```bash
curl http://<2012-tailscale-ip>:8081/health
# Should return: {"status":"ok"}
```

### 2013 Mac Pro — CPU inference test
SSH in, then:
```bash
~/llama.cpp/build/bin/llama-server \
  -m ~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf \
  --n-gpu-layers 0 \
  -c 12288 \
  --threads 10 \
  --host 0.0.0.0 \
  --port 8082
```

From the M1:
```bash
curl http://<2013-tailscale-ip>:8082/health
```

---

## Phase 5 — Startup Scripts (So You Don't Have to Retype)

### 2012 Mac Pro — `~/start_village_node.sh`
```bash
#!/bin/bash
exec ~/llama.cpp/build/bin/llama-server \
  -m ~/models/gemma4-e4b-gguf/gemma-4-e4b-it-Q4_K_M.gguf \
  --n-gpu-layers 32 \
  -c 12288 \
  --host 0.0.0.0 \
  --port 8081
```
```bash
chmod +x ~/start_village_node.sh
```

### 2013 Mac Pro — `~/start_village_node.sh`
```bash
#!/bin/bash
exec ~/llama.cpp/build/bin/llama-server \
  -m ~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf \
  --n-gpu-layers 0 \
  --threads 10 \
  -c 12288 \
  --host 0.0.0.0 \
  --port 8082
```
```bash
chmod +x ~/start_village_node.sh
```

---

## Phase 6 — Wire Village to the Mesh

Once both nodes are serving, update the Village on the M1 to use them.

Run a session with per-agent server overrides (no code changes needed yet — uses existing env var):
```bash
# Test: dispatch ALL agents to the 2012 Mac Pro node
VILLAGE_LLAMA_SERVER=http://<2012-tailscale-ip>:8081 \
  /opt/anaconda3/envs/village/bin/python run_session.py --scenario sc04
```

For full parallel dispatch (Phase 8 Alt 2), the code change needed is in `config.py`
and `agents/council.py` — see `docs/mesh_code_changes.md` (to be written next session
when we're ready to build).

### Quick multi-node test (manual, no code changes):
```bash
# Terminal 1 on M1: Humanist runs locally
VILLAGE_LLAMA_SERVER=http://localhost:8080 \
  /opt/anaconda3/envs/village/bin/python run_session.py --scenario sc04

# Separately: verify 2012 node handles a direct prompt
curl http://<2012-tailscale-ip>:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma","messages":[{"role":"user","content":"Hello"}],"max_tokens":50}'
```

---

## Phase 7 — Resource Hub Setup (Both Mac Pros)

Both machines with 64GB RAM are well-suited to serve reference documents, manuals,
and datasets accessible from anywhere on the Tailscale network.

### Immediate need: drive space
- 2012 Mac Pro: 4 internal SATA bays — add a 2TB+ drive if bays are free
- 2013 Mac Pro: also has internal SATA — same recommendation
- External USB 3.0 is an easy fallback on either machine

### Simple document server (Python, no setup required)
On each Mac Pro, to share a folder over HTTP on the Tailscale network:
```bash
# Serve ~/Documents/reference/ on port 8090
cd ~/Documents/reference
python3 -m http.server 8090 --bind 0.0.0.0
```
Access from M1: `http://<mac-pro-tailscale-ip>:8090/`

### What to put there (suggestions)
- Model cards / spec sheets for all GGUFs you're running
- Village architecture docs (sync from `~/federated_village/docs/`)
- Manuals for hardware
- LoRA training datasets (backup copy)
- Obsidian vault snapshot (read-only reference)

Full Obsidian sync across machines is a separate discussion — start with the simple
HTTP file server and scale from there.

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `llama-server` won't start on Intel Mac | Missing Xcode CLI tools | `xcode-select --install` |
| Metal not working on 2012 Mac Pro | RX 580 driver issue | Try `--n-gpu-layers 0` first to confirm CPU works, then add layers back |
| Can't reach node over Tailscale | Node not connected | `tailscale status` on that machine, `tailscale up` if disconnected |
| `/health` returns nothing | Server bound to localhost only | Confirm `--host 0.0.0.0` in startup command |
| Slow inference on 2013 Mac Pro | CPU-bound NeMo 12B | Expected — use for batch/non-interactive only |
| Context length errors | Default -c too small | Add `-c 12288` to server command |

---

## What This Unlocks

Once the mesh is running:

1. **Parallel jury** — Analyst on 2012 Mac Pro, Ethicist on M1, simultaneously → session time cut in half
2. **Model diversity** — different models on each node = different character voices in same session
3. **Scout agent** — Gemma E4B on 2012 runs background research while M1 handles interactive sessions
4. **Phase 8 Alt 2** — deliberation/adjudication separation (deferred for lack of hardware — now possible)
5. **Resource hub** — manuals, datasets, model cards accessible from any node on the tailnet

---

*Next doc to write when ready: `docs/mesh_code_changes.md` — the ~50 lines of config.py +
council.py changes for per-agent server dispatch.*
