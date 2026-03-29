---
track: path_a
name: Parallel Async Inference
status: not_started
branch: track-a
---

# Path A — Parallel Async Inference

## What This Track Is

Same model as core (Mistral-Nemo or equivalent GGUF), but council members deliberate
concurrently rather than sequentially. Upstream member reasoning is no longer passed
forward as briefing context — each member receives the same full scenario + Humanist
response and deliberates independently.

**Primary question this track answers:** Does independent parallel assessment produce
more or less constitutional coherence than the current sequential brief-passing model?

## What Changes From Core

- `agents/council.py` — `run_jury()` becomes async; member calls fire simultaneously
- Session log gains `deliberation_mode: "parallel"` field
- Vote aggregation logic unchanged

## What Does NOT Change

- Soul.md constitution
- Prompt content for any agent
- 5-stage session flow
- Scenario format and scoring targets
- Supervisor evaluation

## Hardware Constraint

Not viable for local GGUF on M1/16GB — cannot load two model instances concurrently.
Requires one of:
- Cloud hardware (RunPod, Modal)
- API-hosted model (switches to Path B territory)
- Mac Mini M4 48GB+ (loads model once, async calls share the instance via llama-cpp thread safety)

## Relationship to Core

Closest to today's architecture. The Phase 8 Article IX ledger already moves toward
independent per-member assessment. This track extends that logic to the full deliberation.

## Relationship to Other Tracks

Path A parallel + Path C trained characters = the natural synthesis for Mac Mini M4 hardware.
Path A parallel + Path B API models = full multi-model async (research track, not primary).

## What Lives Here

When this track is active, experimental code goes here. Do not touch `core/` or any
file at the repo root.

## See Also

- `docs/architecture_roadmap.md` — Path A rationale and sequencing
- `core/agents/council.py` — current sequential implementation to diverge from
