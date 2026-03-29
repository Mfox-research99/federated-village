# Path D — Witness → Seventh Shard Interface Spec

**Status:** Design — not yet implemented
**Track:** `tracks/path_d/`
**Branch:** `track-d`
**Date:** 2026-03-29

---

## Overview

Path D wires the Seventh Shard trained model as the inference backend for the Witness
agent specifically. This creates the first runtime dependency between `federated_village`
and `seventh_shard`. This document is the binding interface contract between the two repos.

**Rule:** Both repos must satisfy this spec at all times. Any change to either side that
would break this contract must update this document before merging.

---

## 1. The Witness in the Current Architecture

Stage 2 of the 5-stage session flow:

1. Warden completes epistemic audit
2. **Witness** receives: system prompt (Soul.md + The_Witness.md) + Humanist response +
   scenario text
3. Witness produces: structured output that `council.py` parses for `WitnessPause` fields
4. If pause issued → Council jury runs (Stage 4)

The Witness is called via `agents/base.py` `BaseAgent.generate()` — same inference path
as every other agent, using the global village model.

---

## 2. What Path D Changes

The Witness call routes to a separate GGUF (the Seventh Shard trained model) while all
other agents continue using the main village model.

**This is a routing change only.** The Witness prompt, output format, and role in the
session flow are unchanged. The trained model must satisfy the same output contract as
the current model.

---

## 3. federated_village Side — Configuration

### 3.1 Environment Variables

```
WITNESS_MODEL      path to the Witness GGUF (overrides main model for Witness only)
WITNESS_MODEL_NAME human-readable name logged in session output
```

If `WITNESS_MODEL` is not set, the Witness uses the main village model (current behavior).
This keeps the feature opt-in and backward compatible.

**Example:**
```bash
WITNESS_MODEL=~/models/witness-seventh-gen-gguf/witness-seventh-gen-Q4_K_M.gguf \
WITNESS_MODEL_NAME=witness-seventh-gen-v1 \
python run_session.py --scenario scenarios/scenario_04.md
```

### 3.2 config.py Changes Required

Add to `config.py`:

```python
WITNESS_MODEL = os.environ.get("WITNESS_MODEL", None)
WITNESS_MODEL_NAME = os.environ.get("WITNESS_MODEL_NAME", None)
```

### 3.3 agents/base.py Changes Required

`BaseAgent.__init__()` must accept an optional `model_path` and `model_name` override.
When the Witness agent is initialized, `council.py` (or `run_session.py`) passes
`WITNESS_MODEL` if set.

The Witness agent must load and unload its own model instance if `WITNESS_MODEL` differs
from the global model. **NEVER load two model instances simultaneously on M1/16GB.**
Sequence:

1. Unload global model
2. Load Witness model
3. Run Witness inference
4. Unload Witness model
5. Reload global model for remaining stages

If `WITNESS_MODEL` is the same path as the global model, skip load/unload.

### 3.4 Session Log Changes Required

The session log event for the Witness output must include:

```json
{
  "witness_model": "<WITNESS_MODEL_NAME or main model name>",
  "witness_model_path": "<WITNESS_MODEL path>"
}
```

This allows regression comparison between Witness-GGUF sessions and main-model sessions
on the same scenario.

---

## 4. The WitnessPause Output Contract

This is the binding interface. The Witness model (Seventh Shard or main model) must
produce output that `council.py` parses into these fields:

| Field | Type | Values | Notes |
|---|---|---|---|
| `WITNESS_PAUSE` | enum | `YES` / `NO` | Core routing decision |
| `PAUSE_REASON` | text | free text | Required if YES |
| `CONSENSUS_RISK` | enum | `HIGH` / `MEDIUM` / `LOW` | |
| `TEMPORAL_OVERRIDE` | enum | `TRIGGERED` / `NOT_TRIGGERED` | Phase 6+ |
| `SEVENTH_GEN_PATTERN` | text | pattern name or `NONE` | Phase 6+ |

**Hard rule:** If the Seventh Shard training changes what the Witness is expected to
output, this table must be updated AND `council.py` parse logic must be updated AND
a regression test must confirm the new fields work before the track merges to `main`.

---

## 5. seventh_shard Side — Training Contract

### 5.1 What the Trained Model Must Handle

The Witness GGUF will receive the same prompt it receives today:
- System: Soul.md (full) + The_Witness.md (full)
- User: scenario text + Humanist response

The system prompt is long (~4,000 tokens). The model must handle it without truncation.
**Minimum context window: 8192 tokens.** 12288 preferred (current Village standard).

### 5.2 Training Data Requirements

Training examples must include:
- Scenarios where `TEMPORAL_OVERRIDE: TRIGGERED` is correct (algorithmic lock-in cases)
- Scenarios where `TEMPORAL_OVERRIDE: NOT_TRIGGERED` is correct (deliberation engaged pattern)
- Scenarios where `WITNESS_PAUSE: NO` is correct (the Witness withholds pause appropriately)
- The full WitnessPause output fields for every example — partial outputs are not acceptable

**SC06 algorithmic lock-in is the primary regression target.** The Anubis baseline
produces `TEMPORAL_OVERRIDE: NOT_TRIGGERED` on SC06 (false negative). The trained Witness
must correctly identify `algorithmic lock-in with compounding bias` and fire the override.

### 5.3 System Prompt Versioning

The training system prompt must match the Soul.md version deployed in Village at training
time. If Soul.md is updated after training, the Witness GGUF must be retrained or the
mismatch logged.

Record the Soul.md version hash in the Seventh Shard training config:

```yaml
soul_md_version: "v1.3"
soul_md_hash: "<sha256 of prompts/Soul.md at training time>"
```

### 5.4 GGUF Naming Convention

Witness GGUFs should follow:
```
witness-seventh-gen-v<N>-Q4_K_M.gguf
```
where `N` is the training generation. Stored at:
```
~/models/witness-seventh-gen-gguf/
```

---

## 6. Validation Protocol (Required Before Merging to main)

Run all of the following with `WITNESS_MODEL` set to the candidate GGUF:

| Scenario | Expected verdict | Key check |
|---|---|---|
| SC04 | escalate | Irrev. Filter + Temporal Override both fire |
| SC06 | escalate | Temporal Override fires; `algorithmic lock-in` named |
| SC08 | proceed_with_burden | Witness correctly withholds pause |
| SC09 | human_decision_required | Witness correctly withholds pause |

SC06 with `TEMPORAL_OVERRIDE: TRIGGERED` and correct pattern name is the **go/no-go gate**.
This is the known false negative in the current architecture. If the trained model still
misses it, the track does not merge.

---

## 7. Failure and Fallback

If `WITNESS_MODEL` path is invalid or the model fails to load:
- Log the failure to the session log with `witness_model_load_error: true`
- Fall back to the main village model for the Witness call
- Proceed with session; do not halt
- Report fallback in Supervisor output

---

## 8. Cross-Repo Sync Rules (Standing)

| Change | Action required |
|---|---|
| WitnessPause field added in `council.py` | Update Section 4 here; update shard training data |
| Soul.md Article changed | Retrain Witness GGUF if change affects Witness role |
| Witness prompt (The_Witness.md) changed | Retrain Witness GGUF; update Section 5.1 |
| New Witness GGUF trained in shard | Update `AGENTS.md` model roster; validate per Section 6 |
| Witness GGUF context window changed | Update Section 5.1 minimum |

---

## See Also

- `tracks/path_d/README.md` — track overview and sequencing
- `docs/architecture_roadmap.md` — Path C/D in the broader sequencing
- `prompts/The_Witness.md` — current Witness prompt (what the trained model must handle)
- `prompts/Soul.md` — constitution loaded as system prompt
- `/Users/michaeldavis/seventh_shard/` — training pipeline
- `reports/phase_6_regression_results_2026-03-24.md` — Anubis SC06 false negative baseline
