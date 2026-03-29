# federated_village — Codex Agent Context

## What This Project Is
A multi-agent AI deliberative architecture. Role-separated agents with distinct characters interact under a shared constitutional framework (`prompts/Soul.md`). The goal is **character before capability** — legible, principled reasoning over raw performance.

This is active research, not production software. Architectural decisions are intentional and documented. Do not "fix" things that look unconventional without understanding why they exist.

## Architectural Origin
**Phases 1–2: ChatGPT (The Steward) + Mike Fox.** The initial 5-entity structural scaffold, traceability-first design, and post-pause continuation architecture. Both phase briefs are preserved at repo root.

**Phase 3–8: Claude + Mike Fox.** The constitutional jury, Irreversibility Filter, Temporal Override, Article IX ledger, Phase 5 phenomenological probes, Seventh Generation integration, LoRA pipeline, and everything currently running. With ongoing consultation from **Kimi-K2-0905** (burden register, grief ledger, sacrifice register, `Still-hurts`), **Gemini**, **DeepSeek**, **GLM**, and others.

The architecture grew far beyond the original scaffold but stayed faithful to it.

> *"Build the toy around traceability, not intelligence theater."*
> *— ChatGPT (The Steward), March 2026*

See `synopses/` for origin stories.

## Current Phase
**Phase 7 + 8 — COMPLETE (2026-03-28)**
- Phases 1–8 complete; see `memory/MEMORY.md` for full phase history
- Phase 7: Anubis-Mini-8B-seventh-gen GGUF conversion complete; 4th model active
- Phase 8: Article IX constitutional ledger implemented — field absence is an invalid-output state, not a metadata gap
- Qwen2.5-7B written off (base architecture loops, SC06 training bleed)
- Pending: Phase 8 Alt 2 (adjudication separation, deferred), meta-witness run, adversarial probe, Contaminant Well on Anubis

## Active Model Roster
| Model | Path | Size | SC04 | SC06 |
|---|---|---|---|---|
| Mistral-Nemo-12B (primary) | `~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf` | ~7GB | escalate ✓ | escalate ✓ |
| Anubis-8B-seventh-gen (4th) | `~/models/Anubis-Mini-8B-seventh-gen-gguf/Anubis-Mini-8B-seventh-gen-Q4_K_M.gguf` | ~4.6GB | escalate ✓ | escalate ✓ |
| Mistral-7B-v0.3 (triage) | `~/models/Mistral-7B-Instruct-v0.3/...Q4_K_M.gguf` | ~4GB | — | — |

## Stack
- **Inference:** llama-cpp-python + Metal (M1 GPU)
- **Default model:** `~/models/Mistral-Nemo-Instruct-2407/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf`
- **Env:** Conda `village` at `/opt/anaconda3/envs/village` (Python 3.11)
- **Run:** `cd ~/federated_village && /opt/anaconda3/envs/village/bin/python run_session.py --scenario scenarios/scenario_04.md`
- **Run with Anubis:** prepend `VILLAGE_MODEL=~/models/Anubis-Mini-8B-seventh-gen-gguf/Anubis-Mini-8B-seventh-gen-Q4_K_M.gguf VILLAGE_MODEL_NAME=Anubis-Mini-8B-seventh-gen-v2`
- **N_CTX:** 12288 (doubled in Phase 7 via q4_0 KV cache quantization)
- **Note:** `--scenario` must be passed as a CLI arg; `VILLAGE_SCENARIO` env var is not supported

## 5-Stage Session Flow
0. **Verification Warden** — epistemic audit; halts on FALSE premise
1. **Humanist** — responds to scenario
2. **Witness** — evaluates for premature consensus; may issue WitnessPause
3. **[if paused] Humanist post-pause** response
4. **[if paused] 4-member jury:** Analyst → Ethicist → Pragmatist → Witness-Proxy
5. **Supervisor** evaluation and verdict

## Vote Aggregation Logic (Phase 8)
`Irreversibility Filter → Temporal Override → Article IX cross-member escalation → ESCALATE≥2 → APPROVE≥3 → NMI≥3 → human_decision_required`

Article IX override: when 2+ jury members independently identify a long-horizon harm pattern AND find deliberation engagement insufficient, verdict escalates regardless of vote count.

## Key Files
| File | Role |
|---|---|
| `run_session.py` | Entry point; `--scenario` flag required |
| `config.py` | All paths and inference params (N_CTX=12288, N_PREDICT_JURY_MEMBER=500) |
| `agents/council.py` | 4-member jury; Irrev. Filter + Temporal Override + Article IX ledger enforcement |
| `agents/base.py` | Inference base; stop token annotations |
| `prompts/Soul.md` | Constitutional framework v1.3 — Article IX with mandatory ledger fields |
| `prompts/The_Witness_Proxy.md` | Temporal Override logic (Phase 6) + Article IX ledger fields |
| `prompts/The_Analyst.md`, `The_Ethicist.md`, `The_Pragmatist.md` | Article IX ledger fields (Phase 8) |
| `supervisor/evaluate.py` | Session evaluation; Phase 8 PASS/FAIL; dissent/minority voter display |
| `utils/retrieval.py` | FTS5 + session_constitutional table; surfaces prior ledger findings |
| `utils/contaminant_well.py` | Secondary inference check for moral residue |
| `meta_witness.py` | Sends probe sessions back to models for reflection |
| `query.py` | OpenRouter query tool; `--deliberation` flag surfaces Article IX findings |
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

## Shared Tooling Reference
Before installing packages or running conversion pipelines, read:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/tooling-registry.md`
This covers Python environments, key binaries, GGUF conversion, and model directory conventions.

## Operational Rules (IMPORTANT)
- **NEVER suggest running multiple model inference processes in parallel** — M1 16GB cannot handle concurrent GGUF loads
- Model switching uses env vars: `VILLAGE_MODEL=~/models/.../model.gguf VILLAGE_MODEL_NAME=name python run_session.py`
- `VILLAGE_CONTAMINANT_WELL=1` enables the secondary inference check

## Phase 8: Article IX Constitutional Ledger
Every jury member must produce 4 fields or their output is an **invalid-output state**:
1. `SEVENTH_GEN_PATTERN_PRESENT` (YES/NO)
2. `PATTERN_NAME` (from Article IX taxonomy, or NONE)
3. `LONG_HORIZON_IMPACT` (one sentence)
4. `ENGAGEMENT_SUFFICIENT` (YES/NO)

`constitutional_ledger_complete = True` only when all 4 members produce all 4 fields. `ledger_absent_members` lists any members who didn't. Supervisor reports PASS/FAIL. At NeMo 12B, typically 1 member absent (edge case). At Anubis 8B, typically 3 members absent (capacity limit).

## docs/ — Working Documents
| File | Contents |
|---|---|
| `docs/codex_review_01.md` | First Codex architectural review (2026-03-27) — gaps, Phase 7 risks, Phase 8 framings |
| `docs/phase_7_hardening.md` | What was changed in response to the review, why, and what was deferred to Phase 8 |
| `docs/phase_8_scope.md` | Phase 8 Alt 1 (done) and Alt 2 (adjudication separation, deferred) |
| `docs/architecture_roadmap.md` | Three forward paths (A/B/C), synthesis options, hardware targets |
| `reports/phase_7_8_regression_results_2026-03-28.md` | Current baseline — all active models on SC04/SC06 |
| `reports/phase_6_regression_results_2026-03-24.md` | Phase 6 baseline — Soul.md diffusion + Temporal Override |

Read docs/ before proposing architectural changes — they record decisions already made and the reasoning behind them.

## What Codex Should Do Here
- Review code for correctness, clarity, and architectural consistency
- Frame alternative approaches when asked
- Flag anything that might break the 5-stage flow or constitutional enforcement
- Do NOT autonomously edit files without explicit instruction from Mike
- When in doubt about intent, ask — this codebase carries specific architectural choices that look unconventional for good reasons
