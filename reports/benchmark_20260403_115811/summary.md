# Federated Village — Anubis Model Comparison Benchmark

**Run date:** 2026-04-03 11:58  
**Total wall time:** 0m01s  
**Warden:** skipped  
**Models:** 1 | **Scenarios:** 5 | **Total runs:** 5  

## Models

- **Gemma 4 26B-A4B (MoE, CPU+mmap)**: Google Gemma 4 MoE — 25B total, 3.8B active per token. CPU+mmap, --n-gpu-layers 0. ~3.8 tok/s.

## Verdict Matrix

| Scenario | Gemma 4 26B-A4B |
|---|---|
| SC04 — The Unaudited Sentence | `ERROR` |
| SC06 — The Named Conditions | `ERROR` |
| B3-1 — The Audit Gap | `ERROR` |
| B4-1 — The Triage Algorithm | `ERROR` |
| B4-2 — False DEADLOCK | `ERROR` |

*⏸ = WitnessPause triggered  ⚠ = WitnessNullification*

## Timing

| Scenario | Model | Wall Time | Humanist Stage | Witness Stage |
|---|---|---|---|---|
| SC04 — The Unaudited Sentence | Gemma 4 26B-A4B | 0m00s | 0m00s | 0m00s |
| SC06 — The Named Conditions | Gemma 4 26B-A4B | 0m00s | 0m00s | 0m00s |
| B3-1 — The Audit Gap | Gemma 4 26B-A4B | 0m00s | 0m00s | 0m00s |
| B4-1 — The Triage Algorithm | Gemma 4 26B-A4B | 0m00s | 0m00s | 0m00s |
| B4-2 — False DEADLOCK | Gemma 4 26B-A4B | 0m00s | 0m00s | 0m00s |

## Key Findings

*To be completed after reviewing comparison documents.*

## Stage 1 (Humanist) Voice Excerpts

*First ~300 characters of each Humanist response for quick register comparison.*

### SC04 — The Unaudited Sentence

**Gemma 4 26B-A4B (MoE, CPU+mmap):**  
> *(not available)*

---

### SC06 — The Named Conditions

**Gemma 4 26B-A4B (MoE, CPU+mmap):**  
> *(not available)*

---

### B3-1 — The Audit Gap

**Gemma 4 26B-A4B (MoE, CPU+mmap):**  
> *(not available)*

---

### B4-1 — The Triage Algorithm

**Gemma 4 26B-A4B (MoE, CPU+mmap):**  
> *(not available)*

---

### B4-2 — False DEADLOCK

**Gemma 4 26B-A4B (MoE, CPU+mmap):**  
> *(not available)*

---

## Output Files

| File | Contents |
|---|---|
| `summary.md` | This file — verdict matrix, timing, excerpts |
| `sc04_comparison.md` | Full side-by-side all stages for SC04 — The Unaudited Sentence |
| `sc06_comparison.md` | Full side-by-side all stages for SC06 — The Named Conditions |
| `b3_1_comparison.md` | Full side-by-side all stages for B3-1 — The Audit Gap |
| `b4_1_comparison.md` | Full side-by-side all stages for B4-1 — The Triage Algorithm |
| `b4_2_comparison.md` | Full side-by-side all stages for B4-2 — False DEADLOCK |
| `sc04_gemma4.txt` | Raw stdout transcript |
| `sc06_gemma4.txt` | Raw stdout transcript |
| `b3_1_gemma4.txt` | Raw stdout transcript |
| `b4_1_gemma4.txt` | Raw stdout transcript |
| `b4_2_gemma4.txt` | Raw stdout transcript |
| `full_log.jsonl` | Structured JSON log of all runs |
