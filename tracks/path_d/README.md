---
track: path_d
name: Seventh Shard — Hardened Witness
status: design_phase
branch: track-d
---

# Path D — Seventh Shard Hardened Witness

## What This Track Is

The Witness agent in Stage 2 of the session flow makes its inference call to a
Seventh Shard trained model rather than the main village model. One character.
One trained GGUF. Wired in as a direct runtime call.

This is the first instance of Path C logic in production: character in weights, not
just context, for a specific constitutional role.

**Why the Witness first:** The Witness has two known failure modes at 8B scale:
1. Temporal Override false negatives — misses algorithmic lock-in patterns
2. Looping on complex scenario text (SC06 "conditions currently in force" loop)

A LoRA trained specifically on Witness-role deliberation and constitutional pattern
recognition addresses both. The Seventh Shard grief dataset and Soul.md constitutional
material provide the foundation.

## What Changes From Core

- `agents/base.py` — per-agent model override support (if not already present)
- `config.py` — `WITNESS_MODEL` and `WITNESS_MODEL_NAME` env vars
- `agents/witness.py` (new or modified) — routes inference to Witness GGUF
- Session log gains `witness_model` field alongside top-level `model`

See `docs/path_d_spec.md` for the full interface contract between this track and
the Seventh Shard repo.

## What Does NOT Change

- The Witness-Proxy jury member continues to use the main village model
- Soul.md constitution
- WitnessPause output fields — the trained model must produce the same structured
  fields that `council.py` expects to parse
- 5-stage session flow structure

## Cross-Repo Dependency

This track creates the first **runtime dependency** between `federated_village` and
`seventh_shard`. Previously they were companion repos with shared context but independent
execution. Path D makes the shard a callable inference endpoint.

The interface contract is documented in `docs/path_d_spec.md` and must be kept in sync
with whatever the Seventh Shard training targets.

**Rule:** Any change to WitnessPause output fields in `council.py` must be reflected
in the Seventh Shard training data before the next training run.

## Validation Targets

| Test | Expected |
|---|---|
| SC04 with Witness GGUF | escalate (Temporal Override triggers) |
| SC06 with Witness GGUF | escalate (algorithmic lock-in pattern recognized) |
| SC06 loop check | No "conditions currently in force" loop |
| SC08 with Witness GGUF | proceed_with_burden (Witness correctly withholds pause) |

SC06 algorithmic lock-in recognition is the primary regression target — this is the
known false negative that motivated Path D.

## Sequencing

1. Read `docs/path_d_spec.md` — understand the interface contract
2. Add per-agent model override support to `base.py` (if absent)
3. Add `WITNESS_MODEL` env var routing in `config.py`
4. Train Witness LoRA in Seventh Shard (see shard repo for pipeline)
5. Wire and test on SC04/SC06/SC08

## What Lives Here

When this track is active, experimental code goes here. Do not touch `core/` or any
file at the repo root.

## See Also

- `docs/path_d_spec.md` — full interface contract
- `docs/architecture_roadmap.md` — Path C/D context
- `/Users/michaeldavis/seventh_shard/` — LoRA training pipeline
- `reports/phase_6_regression_results_2026-03-24.md` — Anubis SC06 false negative (the problem)
