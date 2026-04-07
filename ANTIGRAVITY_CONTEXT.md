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

## Operational Rules
- NEVER run multiple model inference processes in parallel — M1 16GB cannot handle concurrent GGUF loads
- Do NOT autonomously edit files without explicit instruction from Mike
- Read `AGENTS.md` in the federated_village repo for full project context
- Read `memory/MEMORY.md` for current phase status
