---
track: path_b
name: API Multi-Model Per Character
status: not_started
branch: track-b
---

# Path B — API Multi-Model Per Character

## What This Track Is

Each character role gets a dedicated large model via API. Claude for Ethicist,
GPT-4 for Analyst, Gemini for Pragmatist, etc. Supervisor orchestrates parallel
async API calls. No local GGUF required.

**Primary question this track answers:** Does a model bring its own architectural
priors to a constitutional role? Does a Claude playing Ethicist deliberate differently
than a Mistral playing Ethicist?

## What Changes From Core

- `agents/base.py` — inference layer replaced or extended with API client per agent
- Each agent config specifies model endpoint rather than sharing one GGUF
- `config.py` gains per-agent model routing (env vars or config dict)
- Session log gains `model_by_role: {analyst: "...", ethicist: "..."}` field

## What Does NOT Change

- Soul.md constitution
- Prompt content for any agent
- 5-stage session flow
- Vote aggregation logic
- Scenario format and scoring targets

## Key Tradeoff

Character lives in the prompt here, not the weights. Consistency depends on prompting
quality, not training. Each model brings its own priors — may introduce character drift
that a single local model doesn't have. This is both the risk and the research question.

## Relationship to Core

Extends the OpenRouter phenomenological probe approach (Phase 5) to the full session
flow. The multi-model cold benchmark (Phase 5) explored this in read-only mode. This
track makes it the live architecture.

## Relationship to Other Tracks

Path B API adjudicator + Path C trained council members = the long-horizon synthesis.
See `docs/architecture_roadmap.md` — the Supervisor/Constitutional Adjudicator role
is the natural fit for a large API model.

## Research Sub-Track

Path B standalone as a research track (extending Phase 5 phenomenological probes) is
independent of the main implementation path. Can run without touching the session flow.

## What Lives Here

When this track is active, experimental code goes here. Do not touch `core/` or any
file at the repo root.

## See Also

- `docs/architecture_roadmap.md` — Path B rationale
- `reports/probe_phenomenological_2026-03-23.md` — Phase 5 multi-model probe baseline
- `query.py` in core — OpenRouter integration already exists; Path B extends this
