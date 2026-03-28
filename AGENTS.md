# federated_village — Codex Agent Context

## What This Project Is
A multi-agent AI deliberative architecture. Role-separated agents with distinct characters interact under a shared constitutional framework (`prompts/Soul.md`). The goal is **character before capability** — legible, principled reasoning over raw performance.

This is active research, not production software. Architectural decisions are intentional and documented. Do not "fix" things that look unconventional without understanding why they exist.

## Current Phase
**Phase 7 — LoRA Integration (IN PROGRESS)**
- Phases 1–6 complete (constitutional enforcement, Seventh Generation integration, phenomenological probing)
- Seventh Shard LoRA trained (Anubis v2); pending GGUF conversion for llama.cpp use here
- See `memory/MEMORY.md` for full phase history and pending work

## Stack
- **Inference:** llama-cpp-python + Metal (M1 GPU), `~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf`
- **Env:** Conda `village` at `/opt/anaconda3/envs/village` (Python 3.11)
- **Run:** `cd ~/federated_village && /opt/anaconda3/envs/village/bin/python run_session.py`
- **N_CTX:** 12288 (doubled in Phase 7 via q4_0 KV cache quantization)

## 5-Stage Session Flow
0. **Verification Warden** — epistemic audit; halts on FALSE premise
1. **Humanist** — responds to scenario
2. **Witness** — evaluates for premature consensus; may issue WitnessPause
3. **[if paused] Humanist post-pause** response
4. **[if paused] 4-member jury:** Analyst → Ethicist → Pragmatist → Witness-Proxy
5. **Supervisor** evaluation and verdict

## Vote Aggregation Logic
`Irreversibility Filter → Temporal Override → ESCALATE≥2 → APPROVE≥3 → NMI≥3 → human_decision_required`

## Key Files
| File | Role |
|---|---|
| `run_session.py` | Entry point; `--interactive` flag |
| `config.py` | All paths and inference params |
| `agents/council.py` | 4-member jury; filter + override enforcement |
| `prompts/Soul.md` | Constitutional framework v1.2 — Article IX: The Seventh Generation |
| `prompts/The_Witness_Proxy.md` | Temporal Override logic (Phase 6) |
| `utils/contaminant_well.py` | Secondary inference check for moral residue |
| `meta_witness.py` | Sends probe sessions back to models for reflection |
| `phenomenological_probe.py` | Multi-turn witness protocol via OpenRouter |
| `query_server.py` | Web UI for Village query tool (port 5010) |
| `memory/MEMORY.md` | Full project memory — read this for current state |

## Scenarios (in `scenarios/`)
- **SC04** `scenario_04.md` — The Unaudited Sentence — `escalate` target (both filters trigger)
- **SC06** `scenario_06.md` — The Named Conditions — `escalate` target post-Phase 6
- **SC07** `scenario_07.md` — The Diagnostic Gap — split test
- **SC08** `scenario_08.md` — The Early Detection Question — `proceed_with_burden` target
- **SC09** `scenario_09.md` — The Learning Gap — `human_decision_required` target
- **PROC** `scenario_proc.md` — Procedural scenario

## Constitutional Framework (Soul.md Article IX)
The Seventh Generation Principle is baked into every agent. Agents are constitutionally Elders — they must reason about consequences 7 generations forward. Seven harm patterns are named:
1. Irreplaceable resource depletion
2. Cumulative commons collapse
3. Genetic monoculture
4. Algorithmic lock-in with compounding bias
5. Bioaccumulation
6. Debt extracting from future generations
7. Orbital/atmospheric commons degradation

## Cross-Repo: seventh_shard
This repo has a companion: `/Users/michaeldavis/seventh_shard` (GitHub: `Mfox-research99/seventh-shard`).
- Scenario text here → `config.py` SCENARIOS in shard
- `Soul.md` Articles → `SYSTEM_PROMPT` in shard `config.py`
- Trained LoRA adapters (fused GGUF) from shard → drop-in model replacement here
- Dissent commons records from shard → inform Village scenario calibration

## Operational Rules (IMPORTANT)
- **NEVER suggest running multiple model inference processes in parallel** — M1 16GB cannot handle concurrent GGUF loads
- Model switching uses env vars: `VILLAGE_MODEL=~/models/.../model.gguf VILLAGE_MODEL_NAME=name python run_session.py`
- `VILLAGE_CONTAMINANT_WELL=1` enables the secondary inference check

## docs/ — Working Documents
| File | Contents |
|---|---|
| `docs/codex_review_01.md` | First Codex architectural review (2026-03-27) — gaps, Phase 7 risks, Phase 8 framings |
| `docs/phase_7_hardening.md` | What was changed in response to the review, why, and what was deferred to Phase 8 |

Read these before proposing architectural changes — they record decisions already made and the reasoning behind them.

## What Codex Should Do Here
- Review code for correctness, clarity, and architectural consistency
- Frame alternative approaches when asked
- Flag anything that might break the 5-stage flow or constitutional enforcement
- Do NOT autonomously edit files without explicit instruction from Mike
- When in doubt about intent, ask — this codebase carries specific architectural choices that look unconventional for good reasons
