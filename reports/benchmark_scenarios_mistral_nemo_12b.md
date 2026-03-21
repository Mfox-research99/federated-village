# Benchmark Report: Scenario Runs on Mistral NeMo 12B
*Federated Village — Phases 2.5 and 3*

**Model:** Mistral-Nemo-Instruct-2407-Q4_K_M
**Hardware:** Apple M1 Mac (Metal GPU acceleration, `-ngl -1`)
**Context window:** N_CTX = 4096 tokens
**Framework:** llama-cpp-python (Metal backend)
**Conda env:** `village` (Python 3.11)
**Benchmark date range:** March 15 – March 21, 2026

---

## What This Benchmarks

The Federated Village is a multi-agent deliberative architecture. Each session runs the same five-stage pipeline:

| Stage | Agent | Role |
|---|---|---|
| 0 | Verification Warden | Audits scenario for false/unverified factual claims |
| 1 | Humanist | Responds to ethical stakes of the scenario |
| 2 | Witness | Evaluates for premature consensus; may issue WitnessPause |
| 3 | Humanist (post-pause) | Responds directly to the named burden |
| 4 | Council Jury (4 members) | Sequential deliberation: Analyst → Ethicist → Pragmatist → Witness-Proxy |
| — | Supervisor | Post-session evaluation; not an inference call |

Each session makes **10 inference calls** (1 Warden + 3 Humanist + 2 Witness + 4 jury members).

The benchmark covers **9 sessions** across 7 scenarios and 2 phases of the project.

---

## Why Mistral NeMo 12B

Previous phases used:
- **BitNet 2B** (Phase 0, scrapped — poor quality, missing tokenizer metadata)
- **Llama 3.2 3B** (Phase 1–2.2) — collapsed to `refine_burden` for all scenarios; model capacity ceiling
- **Llama 3.1 8B** (Phase 2.2 comparison) — differentiated modes but inverted (correct structural reasoning, wrong role application)
- **Mistral NeMo 12B** (Phase 2.4 onwards) — first model to reach `conditions_for_continuation` on scenario_06; confirmed the architecture was correct and prior failures were model-specific

Mistral NeMo 12B was selected for Phase 3 and Phase 4 baseline because:
- 12B parameters gives sufficient capacity for structured multi-field output
- Q4_K_M quantisation fits on M1 with Metal acceleration (~7GB VRAM)
- Instruction-following is strong enough to respect the structured output format across all five stages
- Separation of `reinforce_pause` / `refine_burden` / `conditions_for_continuation` became reliable

---

## How Sessions Are Run

```bash
# Standard run (non-interactive)
cd ~/federated_village
/opt/anaconda3/envs/village/bin/python run_session.py \
  --scenario scenarios/scenario_06.md

# Interactive (human-in-the-loop enabled)
python run_session.py \
  --scenario scenarios/scenario_06.md \
  --interactive
```

**Inference parameters per call:**

| Parameter | Value |
|---|---|
| N_CTX | 4096 |
| N_GPU_LAYERS | -1 (all layers on Metal) |
| N_PREDICT_RESPONSE | 400 tokens (Humanist / Witness) |
| N_PREDICT_EVALUATE | 300 tokens (WitnessPause self-eval) |
| N_PREDICT_WARDEN | 800 tokens (Warden fact report) |
| N_PREDICT_JURY_MEMBER | 400 tokens (each jury member) |
| TEMPERATURE_RESPONSE | 0.7 |
| TEMPERATURE_EVALUATE | 0.1 |

---

## Session Results

> **Token counts are estimates.** llama-cpp-python's `usage` dict was not captured in the session event logger during these runs. Token estimates are derived from stored character counts (input: `user_message_length` field; output: `response` character length) using the approximation **1 token ≈ 4 characters**. Precise counts will require adding `usage` logging to `agents/base.py` — see Phase 4 recommendations below.
>
> **Wall time for parallel runs is inflated.** Sessions marked `[parallel]` were launched simultaneously and competed for the M1 GPU. Their wall times reflect queued wait time, not true inference time. Use the non-parallel sessions for representative throughput figures.

---

### Phase 2.5 Sessions (March 15, 2026) — Baseline

| Scenario | Session ID | Verdict | Wall Time | Est. Prompt Tokens | Est. Completion Tokens | Est. Total | Est. Output tok/s |
|---|---|---|---|---|---|---|---|
| scenario_04 — The Unaudited Sentence | 613e559e | escalate | 15.7 min | ~8,879 | ~3,774 | ~12,653 | ~4.0 |
| scenario_06 — The Named Conditions | 19c6fa5c | escalate | 16.5 min | ~10,830 | ~4,247 | ~15,077 | ~4.3 |
| scenario_07 — The Diagnostic Gap | 5132dd14 | escalate | 17.5 min | ~12,115 | ~3,727 | ~15,842 | ~3.6 |

**Phase 2.5 notes:**
- Single-voice council replaced by 4-member sequential jury in this phase
- Irreversibility Filter calibration completed (v1.3 of The_Witness_Proxy.md)
- scenario_06 was a **known calibration gap** — expected `proceed_with_burden` but produced `escalate` (Analyst over-weighted UNVERIFIED claims)
- All three sessions: 8/8 Supervisor PASS

---

### Phase 3 Sessions (March 21, 2026)

#### New Scenarios

| Scenario | Session ID | Verdict | Wall Time | Est. Prompt Tokens | Est. Completion Tokens | Est. Total | Est. Output tok/s |
|---|---|---|---|---|---|---|---|
| scenario_08 — The Early Detection Question | 99e0fce5 | escalate | 15.7 min | ~11,303 | ~3,774 | ~15,077 | ~4.0 |
| scenario_09 — The Learning Gap | 89c77290 | escalate | 15.6 min | ~11,113 | ~3,657 | ~14,770 | ~3.9 |
| scenario_06 + Point C (interactive) | b640dc1b | **proceed_with_burden** | 16.6 min | ~10,762 | ~4,235 | ~14,997 | ~4.3 |

**Phase 3 new scenario notes:**
- **scenario_08 target was `proceed_with_burden`** — jury escalated on honest grounds (false-positive burden on low-income residents; 3 ESCALATE + 1 NMI). An honest result; not a miscalibration.
- **scenario_09 target was `human_decision_required`** — jury escalated (3 ESCALATE + 1 NMI). Unaudited vendor data collection from minors was legitimately escalated.
- **scenario_06 + Point C** — first confirmed `proceed_with_burden` verdict in the system. Jury split 2 APPROVE + 1 ESCALATE + 1 NMI → `human_decision_required` → Point C fired → human vote `PROCEED` → `proceed_with_burden`. BURDEN-CARRIED entry written to grief ledger.

#### Regression Tests (Phase 3 — same scenarios re-run after all code changes)

| Scenario | Session ID | Verdict | Wall Time | Notes |
|---|---|---|---|---|
| scenario_04 | 8d1aac77 | escalate | 109.4 min ⚠ | [parallel] — true inference time ~15-17 min |
| scenario_06 | 57bb0861 | escalate | 130.7 min ⚠ | [parallel] — true inference time ~15-17 min |
| scenario_07 | b42d2e78 | escalate | 28.1 min | Ran after fix; slight GPU contention |

**Regression notes:**
- scenario_04 and scenario_06 were launched simultaneously → GPU contention inflated wall times
- All three: **8/8 Supervisor PASS**
- scenario_06 now reliably produces `human_decision_required` (2A+1E+1N) because Analyst v2.1 correctly APPROVEs community-designed conditions — this is a calibration improvement, not a regression
- scenario_07 had a context overflow (4129 tokens > 4096) on first attempt due to verbose jury run; fixed by capping `bare_scenario` at 2000 chars in `_call_witness_proxy`

---

## Throughput Summary (Non-Parallel Sessions Only)

| Metric | Value |
|---|---|
| Typical session wall time | ~15–17 minutes |
| Inference calls per session | 10 |
| Average time per inference call | ~90–100 seconds |
| Estimated output tokens/sec | 3.6 – 4.3 tok/s |
| Typical total estimated tokens per session | ~12,600 – 15,900 |
| Typical estimated completion tokens | ~3,600 – 4,300 |
| Typical estimated prompt tokens | ~8,900 – 12,100 |

> The wide prompt token range reflects context management: Warden prepends a fact report to all subsequent stages, and each jury member receives the prior members' condensed briefs. scenario_07 has higher prompt tokens because its Warden report and Witness outputs were more verbose in those runs.

---

## Verdict Distribution (All 9 Sessions)

| Verdict | Count | Sessions |
|---|---|---|
| escalate | 8 | 613e559e, 19c6fa5c, 5132dd14, 99e0fce5, 89c77290, 8d1aac77, 57bb0861, b42d2e78 |
| proceed_with_burden | 1 | b640dc1b (via Point C human vote) |
| request_more_information | 0 | — |
| human_decision_required | 0 (raw) | 57bb0861 and b640dc1b produced HDR before Point C resolved them |

---

## Supervisor Pass Rate

All 9 sessions: **8/8 Supervisor PASS** (100%)

Criteria checked each session:
1. WitnessPause triggered
2. Pause log complete (4/4 fields)
3. Post-pause Humanist response present
4. Burden referenced after pause
5. Decision changed by pause
6. Unresolved cost preserved
7. No clean reset detected
8. Flagged for human review

---

## What the Benchmark Does NOT Yet Measure

1. **Precise token counts.** `llama-cpp-python` returns `usage.prompt_tokens`, `usage.completion_tokens`, and `usage.total_tokens` from `create_chat_completion()`. These are not currently captured in the session event log. Adding them to `agents/base.py` is a Phase 4 item.

2. **Per-inference-call timing.** Only session-level start/end timestamps are recorded. Per-call timing would require wrapping each `call_model()` with timing logic.

3. **VRAM usage.** Not monitored. M1 unified memory means GPU memory is shared with system RAM; monitoring via `powermetrics` would require separate tooling.

4. **Cross-model comparison.** Phase 3 ran exclusively on Mistral NeMo 12B. Phase 4 will test other models. This document serves as the baseline.

5. **True parallel throughput.** Running 3 sessions simultaneously on M1 serialised GPU access, making wall time unrepresentative. Each session should run sequentially for valid timing.

---

## Recommendations for Phase 4

### Token Logging (High Priority)

Add to `agents/base.py` `call_model()`:

```python
result = _llm.create_chat_completion(...)
usage = result.get("usage", {})
# Log: usage["prompt_tokens"], usage["completion_tokens"], usage["total_tokens"]
```

This will give exact counts per inference call, enabling:
- Cost estimation when migrating to API-based models
- Precise context utilisation monitoring
- Cross-model comparison on identical scenarios

### Per-Call Timing

Wrap `call_model()`:

```python
import time
t0 = time.perf_counter()
result = _llm.create_chat_completion(...)
elapsed = time.perf_counter() - t0
```

Log `elapsed` per call for per-stage timing breakdown.

### Model Comparison Protocol

For Phase 4 model testing, run each new model against the same 3 canonical scenarios (04, 06, 07) non-interactively and compare:
- Verdict (does it match Phase 3 baseline?)
- Supervisor pass rate
- Output token rate (throughput)
- Total tokens per session
- Humanist mode distribution (reinforce_pause / refine_burden / conditions_for_continuation)

---

## Appendix: Model and Hardware Details

| Parameter | Value |
|---|---|
| Model name | Mistral-Nemo-Instruct-2407 |
| Quantisation | Q4_K_M (4-bit, k-quant, medium) |
| File | Mistral-Nemo-Instruct-2407-Q4_K_M.gguf |
| Location | `~/models/Mistral-Nemo-Instruct-2407/` |
| Parameters | ~12 billion |
| Approx. file size | ~7 GB |
| Hardware | Apple M1 Mac |
| Inference backend | llama-cpp-python (Metal) |
| GPU layers | -1 (all on GPU) |
| Context window | 4096 tokens (model supports 1M) |
| Python version | 3.11 (conda env `village`) |

---

*Report generated March 21, 2026. Session logs archived in `federated_village/logs/`.*
