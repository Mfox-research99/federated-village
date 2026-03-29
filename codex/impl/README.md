# codex/impl/

Codex implementation work — experimental code that is not yet promoted to core.

## Structure

Organize by track:

```
codex/impl/
  path_a/     ← Path A parallel inference experiments
  path_b/     ← Path B API multi-model experiments
  path_c/     ← Path C LoRA per-character experiments
  path_d/     ← Path D Witness→Shard wiring
  utils/      ← standalone utility scripts (no session flow dependency)
```

## Rules

- Code here runs in isolation — it does not import from `core/` unless explicitly approved
- If your code needs a core file to work, copy only what you need into your track dir
  and note the source file + version
- Do not write to `logs/`, `memory/`, or `grief_ledger/` from experimental code
- Test files go next to the code they test (no separate test dir needed at this stage)

## Promotion Path

When experimental code is ready for review:
1. Write a design doc in `codex/designs/` summarizing what it does
2. Flag for Mike's review
3. Mike and Claude Code architect the promotion to the appropriate track or core
4. Codex does not self-promote to core

## Current Implementations

(empty — add entries as work accumulates)
