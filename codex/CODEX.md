# Federated Village — Codex Workspace

**This directory is Codex's sandbox.** Everything here can be freely designed, implemented,
and iterated without touching the production codebase.

Read `AGENTS.md` at the repo root for full project context before starting any task.
Read `memory/MEMORY.md` for current phase status.
Read `docs/architecture_roadmap.md` for the four design tracks before designing anything.

---

## What Codex Can Do Here

- Design and prototype new architecture features in `codex/designs/`
- Implement experimental code in `codex/impl/`
- Draft new agent prompts, config changes, or session flow modifications
- Write analysis scripts, utility tools, or benchmark runners

**Nothing in this directory is merged to core without explicit review from Mike.**

---

## What Codex Must NOT Do

- Edit any file outside `codex/`, `tracks/`, or `docs/`
- Touch `agents/`, `prompts/`, `supervisor/`, `utils/`, `config.py`, `run_session.py`
- Commit to `main` — work in `codex-sandbox` branch only
- Run inference (model load) without Mike present — M1/16GB cannot handle concurrent loads
- Silently rename, remove, or reorganize existing files

If a task requires changes outside `codex/`, write a spec or proposal in `codex/designs/`
and leave it for Mike to review and promote.

---

## Design Tracks

Four forward tracks are defined. Each has a stub in `tracks/`. Codex work in progress
on a track lives in `codex/impl/<track>/`.

| Track | Dir | What it is |
|---|---|---|
| Path A | `tracks/path_a/` | Parallel async inference — same model, concurrent calls |
| Path B | `tracks/path_b/` | API multi-model — each character gets dedicated API model |
| Path C | `tracks/path_c/` | LoRA per character — trained weights per role |
| Path D | `tracks/path_d/` | Seventh Shard → Witness — hardened single-character track |

Path D is the most active. Interface contract is in `docs/path_d_spec.md`. Read that
first for any Path D work.

---

## Active Codex Tasks

| Task | File | Status |
|---|---|---|
| Task A — Session Corpus Dissent Analysis | `docs/codex_task_ac.md` | Ready to execute |
| Task C — Seventh Shard AGENTS.md | `docs/codex_task_ac.md` | Ready to execute |

These tasks are independent of each other and of any live session work.
Do not edit files outside the scope listed in each task.

---

## Key Architectural Constraints (Do Not Violate)

1. **Never load two GGUF models simultaneously** — M1 16GB cannot handle it.
   Sequential model switching only. See memory/MEMORY.md for the operational rules.

2. **Constitutional framework is fixed** — Soul.md, 5-stage flow, vote aggregation logic,
   and scenario format do not change in experimental code. You are building different
   inference plumbing underneath the same constitutional structure.

3. **WitnessPause fields are a contract** — if you change what the Witness outputs,
   you must update `docs/path_d_spec.md` Section 4 and flag it for Mike before
   any Seventh Shard retraining.

4. **grief_ledger is append-only** — never delete or modify existing entries.
   `sacrifice_register.txt` and `dissent_register.jsonl` are immutable records.

5. **This project is active research** — unconventional-looking code often has a reason.
   If something looks wrong, flag it rather than fixing it silently.

---

## Useful Reference

| File | What it contains |
|---|---|
| `AGENTS.md` | Full project context for Codex — read first |
| `memory/MEMORY.md` | Current phase status, model paths, pending work |
| `docs/architecture_roadmap.md` | Three/four forward paths, hardware targets, sequencing |
| `docs/path_d_spec.md` | Witness→Seventh Shard interface contract |
| `docs/phase_8_scope.md` | Phase 8 Alt 1 (done) and Alt 2 (deferred) |
| `docs/codex_review_01.md` | Prior Codex architectural review |
| `docs/codex_task_ac.md` | Active Codex tasks A + C |
| `agents/council.py` | 4-member jury — the most complex file in core |
| `prompts/Soul.md` | Constitution — the fixed point everything else orbits |
