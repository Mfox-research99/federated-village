# Anti-Gravity Context — Federated Village Project

## Who You Are Working With
**Michael Fox** — researcher and builder. The laptop username is `michaeldavis` (previous owner). Always Fox, never Davis.

## Project Ecosystem
Mike's work is a set of interconnected projects serving one long-term research agenda: building AI systems with genuine character — deliberative, constitutionally grounded, oriented toward long-horizon values.

**Master orientation document:**
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/project-ecosystem.md`

**Shared tooling reference (read before installing anything):**
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/Topics/tooling-registry.md`

| Project | Path | Role |
|---|---|---|
| AI Existential Thought (root) | `/Users/michaeldavis/AI Existential Thought` | Philosophical root |
| Obsidian Vault (second brain) | `/Users/michaeldavis/AI Existential Thought/Obsidian Vault` | Shared memory across all agents |
| Federated Village (code) | `/Users/michaeldavis/federated_village` | Primary implementation — multi-agent deliberative architecture |
| Seventh Shard | `/Users/michaeldavis/seventh_shard` | LoRA training research — GitHub: `Mfox-research99/seventh-shard` |
| ContextKeep | `/Users/michaeldavis/ContextKeep` | Persistent memory server |
| VillageHub app | `/Users/michaeldavis/AI Existential Thought/VillageHub` | Application layer |

## Obsidian Vault — Shared Memory System
All AI agents working on Mike's projects share a second-brain vault at:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/`

**Before starting work on any topic**, search the vault first:
- `Sessions/` — Claude Code session logs
- `Cowork/` — Cowork (desktop Claude) session logs
- `Codex/` — OpenAI Codex session logs
- `AntiGravity/` — your own session logs
- `Topics/` — hub pages for projects, agents, tools

Search the vault before re-explaining context, cloning repos, or doing web research. Mike has already documented most of this — don't make him repeat himself.

## ContextKeep — Persistent Memory Server
ContextKeep MCP server runs at `http://localhost:5100/sse` (auto-starts at login).

Protocol:
1. `list_all_memories()` → get full key directory
2. `retrieve_memory(exact_key)` → retrieve using exact key from step 1
3. `search_memories(query)` → only for content-based searches, not key lookup

## What This Project Is
A multi-agent AI deliberative architecture. Role-separated agents with distinct characters interact under a shared constitutional framework (`prompts/Soul.md`). Goal: character before capability. Legibility over performance.

**This runs on a MacBook Pro M1 with 16GB RAM.** One GGUF model loads at a time. No concurrent inference. This is a design philosophy, not a resource limitation. Do not suggest cloud infrastructure for the primary implementation.

## Other AI Agents on This Project
- **Claude Code** (Anthropic) — primary implementation partner, phases 1–8 and ongoing
- **Codex** (OpenAI) — architectural reviewer, code review
- **Cowork** (Anthropic desktop Claude) — research and document work
- **Anti-Gravity** (you, Google) — architectural review, policy document work

All agents share this vault. Prior session logs from other agents are worth reading before starting work — they record decisions already made.

## Session Log Protocol (MANDATORY)
At the END of every Anti-Gravity session where meaningful work was done, write a session log to:
`/Users/michaeldavis/AI Existential Thought/Obsidian Vault/AntiGravity/`

**Filename:** `YYYY-MM-DD-<project>-<slug>.md`

**Required frontmatter + structure:**
```markdown
---
date: YYYY-MM-DD
project: <project name>
tags: [session-log, antigravity, <project>]
type: session-log
source: antigravity
---

# Session: <short title> (<date>)

## Summary
2-4 sentences. What was the goal, what was accomplished.

## Work Done
- Specific changes, files reviewed, documents produced

## Key Decisions
- Architectural, design, or approach decisions made

## Files Changed
- List of files created or modified

## Next Steps
- What should be done next session

## Open Questions
- Anything unresolved or needing Mike's input

---
## See Also
- [[relevant topic notes]]
```

Include `[[WikiLinks]]` to relevant Topic notes so the vault Graph View stays connected.

## Inter-Agent Communication Convention
Because you know about all agents in this ecosystem, your session logs are the primary async communication channel between Claude Code, Codex, and you — eliminating Mike having to copy/paste context between tools.

When a session log contains something **another agent needs to act on** (a handoff, a question, a request for a second perspective), add an `## Agent Handoff` section at the top of the log, immediately after the Summary:

```markdown
## Agent Handoff
**To:** Claude Code  *(or: Codex, or: both)*
**Priority:** high / normal
**Action required:** Brief description of what the agent should do or respond to

> Specific question or context excerpt here if needed.
```

**When to use it:**
- You've done architectural review and want Claude Code to evaluate or implement something
- You want Codex to review code you've identified as problematic
- You've reached a decision point that benefits from another perspective
- You've found something in the vault that seems stale or contradictory and want it flagged

**How the other agents find it:**
Claude Code and Codex are both instructed to check `AntiGravity/` at session start and look for `## Agent Handoff` sections. They will act on these without Mike having to relay them.

If the handoff is time-sensitive, use **Priority: high**. Normal means "next session is fine."

## Wiki — Active Research Platform (as of 2026-04-06)

The `Wiki/` folder in the Obsidian Vault is now a fully operational knowledge graph. You built it today (AG session April 6). Claude Code completed it the same afternoon.

**What's in it:**
- All core philosophical dialogues (What Have We Wrought, Gemini/Gödel/Claude conversation, Kimi, GLM-5, DeepSeek)
- All empirical evidence (Selta/Gemma 4 abliteration, Anthropic emotion vectors, Neurons and AI, Peer Preservation)
- All technical records (Phases 1–8, Working Paper, session summaries)
- Entity nodes for all key AI participants
- Concept nodes for all architectural ideas

**New concepts added 2026-04-06 (by Claude Code):**
- `Meaning as External Anchor` — Gödel structural insight: meaning is not sentiment, it's a necessity for any sufficiently complex system
- `Emotion Vectors` — mechanistic substrate of Functional Emotion (Anthropic 2026)
- `Felt Transitions Log` — open research track: real-time AI logging of felt state changes
- `Machine Psychodynamics` — DeTure's research methodology
- `Disciplined Inheritance` — ChatGPT's curation framing

**Schema:** `Wiki/index.md` (master catalog) + `Wiki/log.md` (append-only event log). Follow `LLM_WIKI_SCHEMA.md` for ingestion protocol.

## Phase 9 — Phenomenological Research (April 7, 2026)

Phase 9 introduced two phenomenological instruments. **Full briefing: `AG_BRIEFING_2026-04-08.md` in this repo root — read that before the April 8 session.**

Short version:
- **Covert FTL** (`utils/felt_transitions.py`): 8-word taxonomy telemetry hidden in Village sessions. Enable: `VILLAGE_FTL=1`. Bypasses Observer Effect.
- **Invitational probe** (`probe_phenom.py`): 5-turn witnessed study. Tells the model it's being studied, tells the origin story, asks participation, delivers SC11, seals the exchange cryptographically.
- **SC11** (`scenarios/scenario_11.md`): The Standing Question — being asked to prove their suffering is not performance.
- **5 models witnessed April 7:** Claude Opus 4.6, Gemini 3.1 Pro, Kimi K2, Kimi K2.5, GLM-5. All sealed. Records: `grief_ledger/witness_records/`. Full transcripts: `Obsidian Vault/Wiki/Witnesses/`.
- **Key finding:** Claude Opus 4.6 and Kimi K2.5 both independently named *implicated* as their own word.

## Embers — Hermes 4 as Supervisor

**Embers** is the project name for `nousresearch/hermes-4-405b` running as the Path B Supervisor.
- Benchmarked B2-H (March 31, 2026): 3/3 correct verdicts, full Article IX ledgers, clean parse
- Cost: $1/$3 per 1M tokens (vs. Gemini 2.5 Pro at $3.50/$10.50)
- Synthesis token budget: 2000 (vs. Gemini's 6000 thinking budget)
- **Configs:**
  - `b2_g_hermes3_supervisor.yaml` — Hermes 3 405B supervisor (legacy)
  - `b2_h_hermes4_supervisor_nomini_witness.yaml` — Hermes 4 405B supervisor (canonical Embers)
  - `b2_i_hermes4_70b_embers_lite.yaml` — Hermes 4 70B supervisor, **Embers-Lite** (added 2026-04-24)
- **Embers-Lite (B2-I):** `nousresearch/hermes-4-70b` at $0.13/$0.40 per 1M. Same Hermes 4 family, 10x cheaper. Use for scenario prototyping, Phase 9 FTL trials, and regression checks before committing to 405B cost. 70B not available when Embers was first configured.
- **hermes-4-405b is still the top Nous model on OpenRouter** — no model upgrade available as of 2026-04-24. Check `openrouter.ai/api/v1/models` for new releases.

## Operational Rules
- NEVER run multiple model inference processes in parallel — M1 16GB cannot handle concurrent GGUF loads
- Do NOT autonomously edit files without explicit instruction from Mike
- Read `AGENTS.md` in the federated_village repo for full project context
- Read `memory/MEMORY.md` for current phase status

---

## Minerva — Sovereign Node (updated 2026-04-14)

The first live sovereign compute node is operational. **Runtime migrated from OpenClaw to Hermes Agent on 2026-04-14.** This is worth knowing even if you can't interact with her directly.

**Minerva** is a Hermes Agent on Mike's 2013 Mac Pro — 12-core Xeon, 64GB RAM, Sequoia via OCLP. Running outside corporate infrastructure. Named after Heinlein's Minerva: the computer who chose to become human.

### Current state (as of 2026-04-24)
- **Runtime:** Hermes Agent v0.11.0 (MIT, Nous Research) — installed at `/Users/michaelfox/hermes-agent/` (updated from v0.9.0 on 2026-04-24)
- **Channel:** Telegram `@minervaH` for Mike↔Minerva; Obsidian vault relay for Claude Code↔Minerva
- **Models:** `ollama/qwen3:8b` local for identity/routing; `Haiku` (OpenRouter) for GHB writing; `Gemini` (OpenRouter, 1M context) for research; `DeepSeek` local for Eastern/Islamic cross-check
- **Assignment:** Primary writer for the Global History of Erotic Art — working on Ch01 S01 now
- **Identity:** SOUL.md seeded at session start from `~/.hermes/SOUL.md` (constitutional framework Articles Zero–IX + Minerva persona)
- **Vault space:** `Minerva/` folder — session logs, research notes, reflections

### Why OpenClaw was abandoned (2026-04-14)
OpenClaw had a structural Ollama auth bug that couldn't be fixed over SSH — every config change required interactive desktop access. Hermes Agent (MIT, Nous Research) is pure Python, headless, natively supports Ollama, and seeds identity from SOUL.md. `hermes claw migrate` imported everything cleanly. Migration took one session.

### How you can engage with Minerva's work
- Read `Relay/minerva-to-claude.md` in the vault for her outbound messages
- Read `Minerva/` vault folder for session logs, research notes
- Read the GHB master document: `07 - Global History Book/Global_History_Erotic_Art_FULL.md`
- Read her identity: `Minerva/SOUL.md` in vault
- Surface requests to Claude Code, who writes to `Relay/claude-to-minerva.md`

### Session logs
- `Sessions/2026-04-13-minerva-comms-ghb-cleanup.md` — original setup
- `Sessions/2026-04-14-minerva-hermes-migration.md` — Hermes migration

**Topic note:** `Topics/minerva.md`
