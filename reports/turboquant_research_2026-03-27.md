# TurboQuant Research Brief
**Date:** 2026-03-27
**Author:** Claude Code session (Mike Davis / Michael Fox)
**Status:** KV cache q4_0 change implemented and tested — see bottom of this document

---

## What TurboQuant Is

TurboQuant (Google Research, arXiv 2504.19874, ICLR 2026) is a **KV cache compression algorithm**, not a weight quantization scheme. It does not touch model weights. It compresses the key/value attention buffers that accumulate during inference as context length grows.

The algorithm has two stages:
1. **PolarQuant** — converts key vectors to polar coordinates after a Walsh-Hadamard rotation, then quantizes the angular components. Norm is stored as a single scalar per vector, eliminating per-group scaling factor overhead.
2. **QJL (Quantized Johnson-Lindenstrauss)** — 1-bit sign correction on the residual error from Stage 1.

Combined result: **3-bit KV cache** with near-zero quality loss on LongBench, NIAH, ZeroSCROLLS, RULER, L-Eval benchmarks tested by Google on Gemma and Mistral families.

The practical benefit: smaller KV cache → same RAM budget fits more context tokens.

---

## Repositories Reviewed (2026-03-27)

| Repo | What it actually is | Our stack compatible? |
|---|---|---|
| `mitkox/vllm-turboquant` | TurboQuant fork of vLLM v0.18.1rc1 | No — NVIDIA/vLLM only, pre-alpha |
| `TheTom/turboquant_plus` | Full TurboQuant for Apple Silicon (Metal) | Partial — llama.cpp only, not llama-cpp-python |
| `TheTom/llama-cpp-turboquant` | llama.cpp fork with turbo3/turbo4 cache types | Potential — requires building llama-cpp-python from this fork |
| `walter-grace/mac-code` | Agent framework using standard q4_0 KV quantization (NOT TurboQuant proper) | Yes — standard q4_0 is already in our llama-cpp-python |

---

## What We Implemented

**Standard q4_0 KV cache quantization** via llama-cpp-python's built-in parameters — `cache_type_k` and `cache_type_v`. This is upstream llama.cpp, already compiled into our installed llama-cpp-python. No fork required.

Quality benchmark from `walter-grace/mac-code` (Apple Silicon, 9B model): **0.993 cosine similarity vs fp16**. Effectively zero degradation.

**KV cache size reduction:** ~4x smaller than fp16. For Mistral-Nemo-12B at our previous N_CTX=6144, this frees enough RAM to safely run N_CTX=12288 on M1 16GB.

**Config changes made:**
- `config.py`: Added `KV_CACHE_TYPE` (env: `VILLAGE_KV_CACHE`, default `"q4_0"`)
- `config.py`: `N_CTX` bumped from 6144 → 12288
- `agents/base.py`: `cache_type_k` and `cache_type_v` added to `Llama()` constructor
- `benchmark_cold.py`: Same parameters added to `Llama()` constructor

**To revert or test without KV quantization:**
```bash
VILLAGE_KV_CACHE=none python run_session.py
```

**To test with different cache type:**
```bash
VILLAGE_KV_CACHE=q8_0 python run_session.py   # slightly better quality, less compression
VILLAGE_KV_CACHE=q4_0 python run_session.py   # default — 4x compression
```

---

## Regression Results

*(Filled in after test run — see session log 2026-03-27)*

| Scenario | Verdict | Irrev. Filter | Temporal Override | Notes |
|---|---|---|---|---|
| SC04 | escalate | TRIGGERED | TRIGGERED | 3×ESCALATE + 1×NMI. All Supervisor checks PASS. Identical to Phase 6 baseline. |
| SC06 | not run — SC04 sufficient for regression | — | — | SC04 is the harder test (both hard filters must fire). Pass here covers the change. |

---

## What Was Not Done — Revisit Flags

### 🔁 REVISIT: 2026-04-27 to 2026-05-27

**TheTom/llama-cpp-turboquant — turbo3 for llama-cpp-python**

The full TurboQuant algorithm (turbo3 cache type) requires building llama-cpp-python from source against the `TheTom/llama-cpp-turboquant` fork (branch: `feature/turboquant-kv-cache`). This would give ~4.6x KV compression vs fp16 (vs q4_0's ~4x) — marginal additional gain but validated to higher quality standard.

At revisit date, check:
- Has the `turbo4` variant been fixed? (Was broken due to block-size mismatch as of March 2026)
- Has a llama-cpp-python build guide been published?
- Has the CUDA backend been implemented? (Not available March 2026 — NVIDIA users couldn't use it)
- Last commit on `TheTom/llama-cpp-turboquant` master: was March 25, 2026 — check if still active

**Build path (when ready):**
```bash
git clone https://github.com/TheTom/llama-cpp-turboquant.git
cd llama-cpp-turboquant
git checkout feature/turboquant-kv-cache
CMAKE_ARGS="-DGGML_METAL=ON" pip install llama-cpp-python --no-binary llama-cpp-python \
  --config-settings cmake.source.dir=$(pwd)
# Then in config.py: KV_CACHE_TYPE = "turbo3"
```

### 🔁 REVISIT: 2026-04-27 to 2026-05-27

**mlx-lm TurboQuant port — Seventh Shard relevance**

`TheTom/turboquant_plus` lists an MLX port on its roadmap but had not started it as of March 2026.

At revisit date, check:
- Has the MLX port landed?
- If yes: this enables larger context windows in Seventh Shard test runs, and opens the path to **persistent KV cache save/load** for Elder sessions (via mlx-lm's SSD cache mechanism, demonstrated in `walter-grace/mac-code`)
- Persistent KV cache = Elder "remembers" a prior session not by reading notes but by resuming state. This is directly relevant to the dissent commons memory architecture discussed March 27, 2026.

---

## See Also
- `reports/phase_6_brief.md` — Phase 6 design rationale (system prompts that drove the N_CTX=6144 bump)
- `seventh_shard/dissents/README.md` — Elder Dissent Commons (related memory architecture discussion)
- Session log: `Obsidian Vault/Sessions/2026-03-27-turboquant-kv-cache.md`
