---
track: path_c
name: LoRA Per Character — Trained Weights
status: foundation_in_progress
branch: track-c
---

# Path C — LoRA Per Character

## What This Track Is

Each character role gets its own LoRA-trained small model. Character is in the weights,
not the context. Seven trained GGUFs: Humanist, Analyst, Ethicist, Pragmatist, Witness,
Warden, Witness-Proxy. Each callable as an independent agent with its own inference load.

**Primary question this track answers:** Does a model trained to *be* the Ethicist
deliberate with more constitutional coherence than a model prompted to play the Ethicist?
Is character in weights durable in ways that character in context is not?

## Current Foundation

The Seventh Shard repo (`/Users/michaeldavis/seventh_shard`) is the training pipeline
for this track. Anubis-Mini-8B-seventh-gen is the proof-of-concept: a single LoRA trained
on Soul.md constitutional material, now the 4th active Village model.

Path D (Witness hardening) is the first targeted Path C implementation — one character,
one LoRA, wired back in as a direct agent call.

## What Changes From Core

- `agents/base.py` — inference layer supports per-agent model path override
- `config.py` — per-character GGUF paths (env vars or config dict)
- `run_session.py` — model load/unload cycle between agent calls
- Session log records model used per character

## What Does NOT Change

- Soul.md constitution
- Prompt content for any agent
- 5-stage session flow
- Vote aggregation logic

## Hardware Constraint

On M1/16GB, still sequential — model switching overhead per call. True parallel requires
higher RAM (Mac Mini M4 48GB+). Sequential model-switch is viable and is the intended
initial implementation.

## Training Investment

Each LoRA requires ~50-100 curated training examples of the specific character's voice
and constitutional orientation. At 7 characters: 350-700 examples total. Compute is
cheap (~$5-8 on RunPod A100 for all 7). The work is dataset creation.

See Seventh Shard repo for training pipeline (MLX on M1, or HuggingFace PEFT for cloud).

## Sequencing

1. Path D (Witness only) — wire one trained model as Witness. Validate interface.
2. Analyst + Ethicist LoRAs — extend to two more characters.
3. Full council (all 4 jury members trained)
4. Full pipeline (all 7 characters)

## What Lives Here

When this track is active, experimental code goes here. Do not touch `core/` or any
file at the repo root.

## See Also

- `docs/architecture_roadmap.md` — Path C rationale and synthesis with Path B
- `docs/path_d_spec.md` — Witness→Seventh Shard interface (Path C first step)
- `/Users/michaeldavis/seventh_shard/` — training pipeline
