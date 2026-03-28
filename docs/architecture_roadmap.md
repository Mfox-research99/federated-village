# Federated Village — Architecture Roadmap

*Documented 2026-03-28. Current phase: Phase 8 (Article IX constitutional ledger, minimal version).*

---

## Current Architecture (Baseline)

Single small model (Mistral-Nemo 12B GGUF), sequential agent calls, shared Soul.md constitution loaded in every system prompt. Five-stage session flow: Warden → Humanist → Witness → Council (4 members) → Supervisor. All agents share one model instance — no parallelism. Character lives in the prompt, not the weights.

**Hardware:** M1 MacBook Pro, 16GB RAM. At or near N_CTX ceiling (12288). No concurrent model loads possible.

---

## Three Forward Paths

### Path A — Single Model, Shared Context, Parallel Execution

**What it is:** Each council member receives the same full briefing and deliberates independently — same as now, but parallel rather than sequential. No new training required.

**What changes:** Inference layer only. `run_jury()` becomes async; member calls fire simultaneously rather than passing briefs forward.

**Key constraint:** Not viable on M1/16GB for local GGUF — can't load two instances. Becomes trivially available on cloud hardware or by switching to API-hosted model.

**Tradeoff:** Loses the current brief-passing dynamic where downstream members see upstream reasoning. Members become fully independent rather than informed by prior deliberation. May reduce deliberative coherence; may increase independence of constitutional assessment. Worth testing both modes.

**Relationship to current work:** Closest to today. The Phase 8 Article IX ledger already moves toward independent per-member assessment (each member does their own fresh Article IX read rather than inheriting from prior briefs). Path A extends that logic to the full deliberation.

---

### Path B — Large Model Per Character via API

**What it is:** Each character role gets a dedicated large model call (e.g., Claude for Ethicist, GPT-4 for Analyst, Gemini for Pragmatist, etc.). Supervisor orchestrates. Calls are parallel via async API.

**What changes:** `agents/base.py` inference layer replaced or extended with API client. Each agent config specifies model endpoint rather than sharing one GGUF. Supervisor becomes the orchestration authority.

**Key constraint:** Character lives in the prompt, not the weights — consistency depends on prompting quality, not training. Cost and API dependency. Loss of offline/local operation.

**Tradeoff:** Richer per-member reasoning depth. Parallel calls free. Each model brings its own priors and biases — may introduce character drift that a local model doesn't have. Interesting research question: does a Claude playing Ethicist deliberate differently than a Mistral playing Ethicist?

**Relationship to current work:** Extends the OpenRouter phenomenological probe approach (Phase 5) to the full session flow. The multi-model cold benchmark already explored this in read-only mode. Path B makes it the live architecture.

---

### Path C — LoRA Per Character, Multiple Trained Models

**What it is:** Each character role gets its own LoRA-trained small model. Character is in the weights, not the context. Seven trained GGUFs: Humanist, Analyst, Ethicist, Pragmatist, Witness, Warden, Witness-Proxy. Each callable as an independent agent.

**What changes:** Inference layer loads and unloads per-character model for each call. Training pipeline (Seventh Shard) extended from one Soul.md LoRA to seven character LoRAs with role-specific datasets.

**Key constraint:** On M1/16GB, still sequential — model switching overhead per call. True parallel requires cloud or higher RAM. Training cost: seven datasets, seven training runs.

**Tradeoff:** Most aligned with the "character before capability" thesis — genuine trained character rather than prompted character. Most expensive to build. Most durable once built.

**Relationship to current work:** Seventh Shard LoRA (Anubis v2) is the proof-of-concept for this path. The Phase 7 dissent commons and character benchmarks are the training data foundation. Path C is the full realization of what Seventh Shard started.

---

## The Synthesis: Path C + Path B

The most architecturally coherent long-horizon target:

- **Council members → Path C** (LoRA-trained small models, character in weights, sequential or parallel depending on hardware)
- **Supervisor / Constitutional Adjudicator → Path B** (large API model, one call, handles the constitutional ruling)

This is also what finally makes **Phase 8 Alternative 2** (deliberation/adjudication separation — see `docs/phase_8_scope.md`) fully viable. Alt 2 was the right architecture but premature on single-model hardware. With C+B it becomes the natural split: small trained models handle the roleplay deliberation, large model handles constitutional oversight. The roles aren't competing for the same context window.

**The constitutional thesis maps cleanly:**
- Small trained models = character (who they are)
- Large adjudicator model = constitution (what they're bound by)
- Supervisor = synthesis (what to do)

---

## Sequencing

| Phase | Path | What it proves |
|---|---|---|
| 8 (now) | Baseline | Article IX ledger stable in single-model sequential architecture |
| 9 | Path A | Parallel execution viable; brief-passing vs independent assessment empirical comparison |
| 10 | Path C partial | One or two LoRA characters in live session; model-switch overhead measured |
| 11 | Path C + B | Full LoRA council + API adjudicator; Alt 2 pipeline realized |
| — | Path B standalone | Multi-model API deliberation; character drift / model prior research |

Path B standalone is worth running as a research track (extending Phase 5 phenomenological probes) independently of the main implementation path.

---

## What Stays Constant Across All Paths

- Soul.md constitution
- Five-stage session flow (Warden → Humanist → Witness → Council → Supervisor)
- Scenario format and scoring targets
- Vote aggregation logic (Irreversibility Filter + Temporal Override + cross-member ledger)
- Session log format and Obsidian archive protocol
- Supervisor as lead and final synthesis authority

The architecture changes underneath; the constitutional framework doesn't.

---

## Target Deployment Context

**This project is designed for Apple Silicon + local open-source models.** The reference hardware is a Mac (MacBook Pro M1 or Mac Mini M-series) running a small GGUF model via llama-cpp-python with Metal acceleration. No cloud dependency, no API keys required, no ongoing cost. That constraint is intentional — the goal is a moral deliberation architecture that works for someone with a Mac Mini and an open-source model who wants to ground an ethical AI system without corporate infrastructure.

**Broader use case:** This architecture is not only for standalone deliberation. It is directly applicable as a moral grounding layer for other agentic systems — including open-source agent frameworks (OpenClaw, AutoGen, CrewAI, LangGraph, etc.) that need stricter constitutional oversight before acting. The Village's five-stage flow (Warden → deliberation → constitutional check → Supervisor) can wrap around any agent's proposed action. Character before capability applies upstream of capability, not just alongside it.

**Mac Mini as the production target:** The M4 Mac Mini (48GB, ~$1,799) is the current sweet spot — runs Mistral-Nemo 12B with significant headroom, enables sequential LoRA model switching (Path C). A Mac Studio M4 Max (64GB, ~$1,999) enables comfortable parallel GGUF inference (Path A without cloud). The M4 Ultra (128GB, ~$3,999) is overkill for current scenarios but relevant if running multiple full-size models simultaneously. For context: the current M1 MacBook Pro at 16GB is at ceiling; any of the above unlocks the next architecture phase. The M4 Mac Mini 48GB is the recommended minimum upgrade for Path C work.

---

## Cloud Compute — When and If Needed

Cloud is not required for the current architecture. It becomes relevant for:
- **Path C training** (LoRA per character) if training on laptop is too slow
- **Path A/C parallel inference** if Mac hardware upgrade isn't the right move
- **Research track** (Path B multi-model API deliberation)

### Services

| Service | Best for | Indicative cost |
|---|---|---|
| **RunPod** | Training + inference, flexible spot instances | RTX 4090 24GB: ~$0.50/hr; A100 40GB: ~$1.50/hr |
| **Vast.ai** | Cheapest spot market, more variable | RTX 3090: ~$0.15-0.25/hr |
| **Lambda Labs** | Stable researcher instances | A100 80GB: ~$1.99/hr |
| **Modal** | Serverless, pay-per-second, good for inference bursts | A100: ~$3.72/hr, zero idle cost |
| **OpenRouter** | API inference only (Path B) | Mistral-Nemo: ~$0.001-0.003 per full session |

### Estimated cost to train all 7 character LoRAs in cloud

**Compute is almost free. The work is the datasets.**

- Training time per LoRA on A100 (~50-100 examples per character): 15-30 minutes
- 7 characters × 30 min = ~3.5 hours GPU time
- **Compute cost: ~$5-8 total on RunPod A100**

The real investment is dataset creation: 50-100 high-quality deliberation examples per character capturing their specific voice and constitutional orientation. At 7 characters that's 350-700 curated examples. Using the Seventh Shard approach (semi-automated generation + human review), this is approximately 2-3 days of work before touching a GPU.

### Pipeline note

The current Seventh Shard training pipeline uses **MLX** (Apple Silicon only). Moving to cloud NVIDIA GPUs requires porting to **HuggingFace PEFT + QLoRA** — a different but well-documented stack. Approximately half a day of setup work. Mac-first development remains the primary track; cloud is the scale-out option.

---

## See Also

- `docs/phase_8_scope.md` — Phase 8 Alt 1 (constitutional ledger) and Alt 2 (deliberation/adjudication separation)
- `docs/phase_7_hardening.md` — parse quality and constitutional field tracking
- `docs/codex_review_01.md` — Codex architectural review that originated Alt 2 framing
- `reports/phase_5_brief.md` — multi-model phenomenological probe (Path B research track)
- `/Users/michaeldavis/seventh_shard/` — LoRA training (Path C foundation)
