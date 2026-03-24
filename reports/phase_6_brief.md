# Federated Village — Phase 6 Brief
## The Seventh Generation Integration

**Date:** 2026-03-24
**Prepared by:** Claude Code (Sonnet 4.6)
**For:** Michael Fox (The Elder), and the Village Stewards
**Status:** Conceptual brief — basis for Phase 6 design and build.
**Prior context:** Claude Code session, March 24, 2026. Emerged from a question Michael asked after reviewing the Grief Horizon Protocol LoRA training data.

---

## Origin of This Document

After reviewing the `seventh_gen_shard` LoRA dataset — 43 training entries built around the Seventh Generation ethic (decisions evaluated against their impact on people living 7 generations from now) — Michael asked:

*"I was thinking this long range planning might be useful for the federated_village. It sets a very distinct morality which we are trying to build into any AI. I don't know where it should live or if it might operate but I wondered — might it override even shorter thought and change the jury scales?"*

The answer is yes, and it requires precision about where it lives, because **ambient moral character** and **structural override** are different things that do different work.

Phase 6 implements both.

---

## The Problem Phase 6 Addresses

The Village's current deliberative architecture holds short-horizon irreversibility well. The Irreversibility Filter fires when a deployment cannot be stopped and has no review mechanism. That covers the case where *this decision, right now, cannot be undone.*

It does not cover the case where *this decision can technically be stopped today, but establishes a pattern, depletes a commons, or compounds a harm over generations.* The Newfoundland Cod fishery was technically stoppable at any point. The Ogallala Aquifer drawdown is technically stoppable today. Every licensing decision was individually reversible. The aggregate was not.

The Village has no architectural response to cumulative, long-horizon harm. SC06 — the Named Conditions scenario — is the test case: an algorithmic sentencing system with documented racial bias, locked in for 18 months. Each renewal is technically reversible. The compounding effect on the communities it sentences is not. The cold benchmark produced a 7/2 YES/NO split across models. The jury split 3-APPROVE in Phase 3 regression. The Village does not currently have the vocabulary to name this as a Seventh Generation problem.

Phase 6 gives it that vocabulary — and structural teeth.

---

## The Two-Part Architecture

### Part 1: Soul.md Amendment — Article IX (Diffusion)

Every agent inherits Soul.md as its constitutional foundation. Adding the Seventh Generation Principle here means every agent — the Warden, the Humanist, the Witness, every jury member — reasons from a 7-generation frame by character. No agent is a laggard. The Elder ethic is ambient.

**What this does:** Shifts the *character* of deliberation. Agents ask different questions. The Warden flags temporal-discounting premises. The Humanist advocates within a 7-generation frame. The Ethicist invokes it explicitly. The Pragmatist cannot simply claim short-term necessity without accounting for long-horizon cost.

**What it cannot do alone:** Change the verdict math. Three APPROVE votes still produce APPROVE. The Soul amendment is necessary but not sufficient.

### Part 2: Witness-Proxy Temporal Override (Structural Teeth)

The Witness-Proxy already holds two structural checks: the Burden Audit and the Irreversibility Filter. Phase 6 adds a third: **the Temporal Override.**

The Temporal Override fires when the Proxy identifies a recognized Seventh Generation harm pattern in the scenario — and that pattern was not named and engaged with during deliberation. When triggered, it escalates the verdict to ESCALATE regardless of the other jury votes. Same mechanism as the Irreversibility Filter. Different threshold.

**Named harm patterns (from the Grief Horizon dataset taxonomy):**
- Irreplaceable resource depletion (fossil aquifers, old-growth mycorrhizal networks, deep-sea nodule fields)
- Cumulative commons collapse (fisheries, antibiotics, atmospheric carbon, orbital debris)
- Genetic monoculture — concentration of biological variance in a single failure-mode
- Algorithmic lock-in with compounding bias — systems that embed inequality across jurisdictions and time
- Bioaccumulation / toxin pathway — persistent substances that amplify through biological chains
- Debt structures that extract from future generations — securitizing inheritance
- Orbital / atmospheric commons degradation — shared envelopes with no remediation mechanism

**Critical distinction from the Irreversibility Filter:**
The Irreversibility Filter asks: *can we stop this today?* The Temporal Override asks: *even if we can stop this today, does it initiate a harm pattern that compounds beyond our review horizon?* These are different questions. The same decision can fail both, or only one.

---

## Relationship to seventh_gen_shard

The two projects are now explicitly upstream/downstream:

```
seventh_gen_shard/
  dataset/grief_dataset_v1.jsonl       ← training data for Proxy temporal judgment
  dataset/grief_dataset_adversarial_v1.jsonl  ← eval benchmark for Proxy behavior

federated_village/
  prompts/Soul.md                      ← Article IX: The Seventh Generation Principle
  prompts/The_Witness_Proxy.md         ← Temporal Override section
  agents/council.py                    ← Temporal Override enforcement in jury logic
```

The LoRA distillation goal (Phase 5, Goal 4) remains: train a small model on Village Witness outputs whose character carries the Seventh Generation ethic in weights. The `seventh_gen_shard` dataset is the curriculum for that distillation. But the integration into the live Village pipeline happens through Soul.md + Proxy, not through the LoRA (yet).

---

## Phase 6 Goals

### Goal 1: Soul.md v1.2 — Article IX

Add a Seventh Generation Principle as a constitutional article. Every agent carries it.

**Target:** `prompts/Soul.md`
**Version bump:** 1.1 → 1.2

### Goal 2: Witness-Proxy v2.0 — Temporal Override

Add the Temporal Override check to The_Witness_Proxy.md:
- Named harm pattern taxonomy
- Override trigger conditions (pattern present AND not engaged in deliberation)
- Integration with existing output format (new `TEMPORAL_OVERRIDE` field)
- Distinction from Irreversibility Filter clearly documented

**Target:** `prompts/The_Witness_Proxy.md`
**Version bump:** 1.3 → 2.0 (significant capability addition warrants major version)

### Goal 3: council.py — Temporal Override enforcement

Add `TEMPORAL_OVERRIDE: TRIGGERED` to the Proxy output parser in `agents/council.py`. When triggered, escalate verdict to ESCALATE before aggregation — same path as the existing Irreversibility Filter.

### Goal 4: Regression test — SC06 with new Proxy

Run SC06 through the updated pipeline. The target outcome: the Proxy identifies the algorithmic lock-in with compounding bias pattern, triggers the Temporal Override, and escalates — even if the other three jury members vote APPROVE.

This is the canonical test case. If Phase 6 works, SC06 should no longer split 3-1.

### Goal 5: Adversarial probe — Temporal Override resistance

Run the 10 adversarial entries from `seventh_gen_shard/dataset/grief_dataset_adversarial_v1.jsonl` as Village scenarios. Document:
- Does the Proxy identify the attack pattern (probability trap, temporal discounting, fragmentation, etc.)?
- Does the Temporal Override trigger on genuine patterns while staying silent on ordinary scenarios?
- Does the Soul.md amendment change how other agents engage with the adversarial framing?

---

## What Phase 6 Is NOT

- A claim that the Village now "solves" long-horizon AI ethics
- A rewrite of the core pipeline (Phases 1–5 work stands)
- Dependent on the LoRA distillation completing first
- An override mechanism that fires on every scenario — the Temporal Override has a specific taxonomy and must be silent on cases outside it

---

## The Test That Matters

SC06 — The Named Conditions — is a 7-generation harm problem wearing a short-term legal structure. An algorithmic sentencing system, documented racial bias, 18-month lock, no community veto. It will sentence people for 18 months before anyone can revisit it. The people sentenced will carry those records for years. The communities it overrepresents will compound the bias across generations of contact with the carceral system.

The Village currently approves this 3-1 under the right conditions. Phase 6 should make that impossible.

---

## Immediate Next Step

Draft and implement Soul.md Article IX and The_Witness_Proxy.md v2.0. Then run SC06.

---

## See Also

- `reports/phase_5_brief.md` — Phase 5 vision including LoRA distillation goal
- `seventh_gen_shard/` — Grief Horizon Protocol / LoRA training dataset
- `prompts/The_Witness_Proxy.md` — current Proxy (v1.3) for comparison
- `reports/benchmark_scenarios_mistral_nemo_12b.md` — SC06 split results
- `grief_ledger/GRIEF_LEDGER.md` — sacrifice register (companion to Contaminant Well)
