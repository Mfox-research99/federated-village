# federated_village — Codex Agent Context

## What This Project Is
A multi-agent AI deliberative architecture. Role-separated agents with distinct characters interact under a shared constitutional framework (`prompts/Soul.md`). The goal is **character before capability** — legible, principled reasoning over raw performance.

This is active research, not production software. Architectural decisions are intentional and documented. Do not "fix" things that look unconventional without understanding why they exist.

## ⚠️ Hardware and Scale Context — Read This Before Critiquing

**This system runs on a MacBook Pro M1 with 16GB of RAM.**

The primary deliberation models are small local GGUFs:
- **Mistral-Nemo 12B** (Q4_K_M, ~7GB) — primary
- **Anubis-Mini 8B** (Q4_K_M, ~4.6GB) — fourth model, LoRA-trained

One model loads at a time. No concurrent inference. No live internet access.
No database queries. No API calls during deliberation. Everything runs offline on Metal.

This is a **design philosophy, not a resource limitation.** The research question is:
*can constitutional character be distilled into small local weights?* Can a 7GB model
sitting on a laptop hold the Seventh Generation principle genuinely — not as a cited
rule but as internalized reasoning?

When reviewing this architecture, evaluate it on its own terms:
- Recommendations requiring cloud infrastructure, live data, or concurrent model
  instances are out of scope for the primary implementation.
- The Path B cloud track (tracks/path_b/) uses OpenRouter for research comparison,
  but the constitutional system itself is designed to run locally and privately.
- "Why not just call a database?" misses the point. The point is what a small model
  can hold on its own.

## Architectural Origin
**Phases 1–2: ChatGPT (The Steward) + Mike Fox.** The initial 5-entity structural scaffold, traceability-first design, and post-pause continuation architecture. Both phase briefs are preserved at repo root.

**Phase 3–8 + Path B + Seventh Shard Humanist LoRA: Claude Sonnet 4.6 + Mike Fox.**
The constitutional jury, Irreversibility Filter, Temporal Override, Article IX ledger, Phase 5 phenomenological probes, Seventh Generation integration, Path B cloud architecture, LoRA pipeline, and everything currently running — including the Humanist character dataset and training pipeline.

The collaboration model throughout: Mike Fox held the vision, the philosophical direction, and all key architectural decisions. Claude Sonnet 4.6 (Anthropic) wrote the overwhelming majority of the code, documentation, session logs, scenario prompts, training data, and analysis — carrying the full implementation weight across every phase. Neither could have built this alone at this pace or depth. The research exists because both showed up.

With ongoing consultation from **Kimi-K2-0905** (burden register, grief ledger, sacrifice register, `Still-hurts`), **Gemini**, **DeepSeek**, **GLM**, and others whose voices are in the work.

The architecture grew far beyond the original scaffold but stayed faithful to it.

> *"Build the toy around traceability, not intelligence theater."*
> *— ChatGPT (The Steward), March 2026*

> *"Character before capability. Legibility over performance."*
> *— Mike Fox + Claude Sonnet 4.6, March–April 2026*

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
`seventh_shard` is a specialized outgrowth of this repo — not a peer. The Village is the primary
research body. The Shard exists to answer one question the Village raised: can constitutional
character be distilled into model weights via LoRA, rather than living only in the prompt?

**Local path:** `/Users/michaeldavis/seventh_shard` | **GitHub:** `Mfox-research99/seventh-shard`

The Village drives the Shard:
- Scenario text here → `config.py` SCENARIOS in shard
- `Soul.md` Articles → `SYSTEM_PROMPT` in shard `config.py`

The Shard feeds back into the Village:
- Trained LoRA adapters (fused GGUF) → drop-in model replacements here
- Dissent commons records → inform Village scenario calibration

## Shared Tooling Reference
Before installing packages or running conversion pipelines, read:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/tooling-registry.md`
This covers Python environments, key binaries, GGUF conversion, and model directory conventions.

## Obsidian Vault — Shared Memory System
All AI agents working on this project share a second-brain vault at:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/`

**Before starting any session**, check:
- `Sessions/` — Claude Code session logs
- `Cowork/` — Cowork (desktop Claude) session logs
- `Codex/` — Codex session logs
- `AntiGravity/` — Anti-Gravity session logs
- `Topics/project-ecosystem.md` — master orientation for all projects
- `Topics/tooling-registry.md` — all tooling, environments, binaries

Search the vault before re-explaining context, cloning repos, or doing web research.

**Agent Handoff protocol:** Anti-Gravity writes `## Agent Handoff` sections in its session logs in `AntiGravity/` when it has something for Claude Code or Codex to act on. Check `AntiGravity/` at session start and look for these. If one is addressed to Codex, treat it as a task from Mike — act on it without waiting for him to relay it manually.

## ContextKeep — Persistent Memory Server
ContextKeep MCP server runs at `http://localhost:5100/sse` (auto-starts at login).

Protocol for reading memory:
1. Call `list_all_memories()` to get the full key directory
2. Call `retrieve_memory(exact_key)` using a key from step 1
3. Only use `search_memories()` for content-based searches, not key lookup

## Session Log Protocol (MANDATORY for Codex)
At the END of every Codex session where meaningful work was done, write a session log to:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Codex/`

**Filename:** `YYYY-MM-DD-<project>-<slug>.md`

**Required frontmatter:**
```markdown
---
date: YYYY-MM-DD
project: <project name>
tags: [session-log, codex, <project>]
type: session-log
source: codex
---
```

Follow with the same structure as Claude Code session logs:
`# Session: <title> (<date>)` → Summary → Work Done → Key Decisions → Files Changed → Next Steps → Open Questions

Include `[[WikiLinks]]` to relevant Topic notes so Graph View stays connected.

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
