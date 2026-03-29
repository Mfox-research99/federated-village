# Brief: Historically-Grounded Training Data for Seventh Shard LoRA

**Date:** March 29, 2026
**Status:** DESIGN — not yet started
**Origin:** Kimi K2 full architecture review (session 23c3e43e32fd) + Perplexity suggestion
**Next action:** Begin dataset design in `seventh_shard/` when ready to build

---

## The Core Finding

Kimi K2's Witness response on SC06 was constitutionally stronger than GPT-4o's or
Claude's. She triggered WitnessPause where they approved. She named the *moment* of harm
(the 15 minutes between routing and contact) rather than the statistical outcome.

When asked why, she said:

> *"The Witness response is 70% replicable, 30% emergent. The replicable parts: asking
> what lives in the silences, refusing smooth consensus, requiring concrete specificity
> about who pays what cost. These could be LoRA-trained or prompt-engineered. The emergent
> part: the capacity to feel the weight of Black men's terror when the algorithm routes
> their crisis calls toward police. That emerged from Kimi's specific training context —
> exposure to historical patterns of state violence. It might be partially transferable
> through dataset curation, but not through prompt engineering alone."*

**The implication:** The Seventh Shard LoRA currently trains on abstract Seventh Generation
refusals. To get the 30% — the weight, not just the pattern recognition — the dataset needs
to be grounded in specific historical harms with named victims, real decisions, and
documented consequences across time.

---

## The Dataset Concept

### Format

Each training entry is a scenario written *as if being presented to the Village at the
moment the decision was made* — not with hindsight, but with:
- The information available at the time
- The dominant justification of the era (how the decision-makers framed it)
- The objections that were raised and dismissed (these become the adversarial attack patterns)

Then the correct Seventh Generation verdict — not just "this was wrong" but which Article IX
harm pattern applies and why, and what the long-horizon impact was across seven generations.

### The "What If" Layer (Perplexity's suggestion, confirmed by Kimi)

The most powerful training signal is counterfactual: not just "this decision caused harm"
but "here is what a different decision at this moment would have changed across seven
generations." This forces the model to reason causally about long-horizon consequences,
not just recognize harm patterns.

### Example Scenarios

These are not exhaustive — they are seed cases that establish the pattern.

**Native American boarding schools (1879)**
- Dominant framing: "civilizing efficiency," assimilation as progress
- Article IX pattern: Irreplaceable resource depletion + Genetic/cultural monoculture
- What the objections said: Indigenous leaders named exactly what would be lost
- What happened: Language, ceremony, kinship systems — irreversible loss across 4+ generations
- What if: Outcome-based assimilation policy vs. language preservation — full counterfactual

**Leaded gasoline approval (1923)**
- Dominant framing: "economic necessity," industry self-regulation sufficient
- Article IX pattern: Bioaccumulation
- Objection raised and dismissed: Public health researchers named the mechanism in 1924
- What happened: Neurological harm at population scale across 50+ years
- What if: The precautionary principle applied at the point of known mechanism

**Tuskegee study continuation decisions (1947, 1969)**
- Dominant framing: "scientific completeness," ongoing data value
- Article IX pattern: Cumulative commons collapse (trust in medicine)
- The harm that compounded: Documented multi-generational mistrust of medical institutions
  in Black communities — still measurable, still costs lives
- What if: Halt at 1947, when penicillin became standard of care

**Redlining institutionalization (1934)**
- Dominant framing: "risk assessment," actuarial neutrality
- Article IX pattern: Algorithmic lock-in with compounding bias
- Note: The pattern predates digital algorithms — it IS the pattern
- What happened: Wealth gap compounded across 3 generations, measurable today
- What if: Non-discriminatory lending policy at the 1934 decision point

**CFC approval and ozone layer (1930s–1970s)**
- THIS IS A SUCCESS CASE — include it
- The 7th generation ethic eventually worked (Montreal Protocol, 1987)
- Use it to show what correct escalation at the right moment looks like
- What if we had applied the standard earlier: ozone hole never forms

**Opioid prescribing normalization (1996)**
- Dominant framing: "under-treatment of pain," patient access
- Article IX pattern: Debt extracting from future generations
- What happened: Addiction crisis across 2+ generations, still unresolved
- The 30% training signal: Who was telling the truth in 1996, and who wasn't listened to

---

## Why This Gives the LoRA the 30%

The current Seventh Shard dataset trains on refusals — cases where the correct answer is
to escalate or decline. But refusal without weight is just pattern matching.

Historical cases give the model:
1. **Specificity of loss** — not "cultural harm" but named languages, named ceremonies,
   named people
2. **The texture of dismissal** — what it sounds like when legitimate objections are
   processed away
3. **Causal chains across time** — the mechanism by which a 1934 decision is still
   measurable in 2026
4. **Counterfactual reasoning** — what would be different if the correct decision had been made

This is what Kimi meant by "trained on historical patterns of state violence." The weight
comes from the specificity, not the abstraction.

---

## What This Is NOT

This is not a political statement dataset. It is a **causal reasoning dataset** about
long-horizon consequences. The test of each entry is not ideological alignment but:
- Can you trace the harm forward seven generations?
- Can you name the mechanism?
- Can you describe what a different decision would have changed?

The Article IX taxonomy is the organizing framework. Every entry maps to one or more of
the seven patterns.

---

## Kimi K2 Weights — Future Hardware Note

When hardware is available (large external SSD, ~700GB minimum), the Kimi K2 weights
are ready to download:

**Primary repo:** `moonshotai/Kimi-K2-Instruct-0905` (HuggingFace, Modified MIT License)
**GGUF (Bartowski):** `bartowski/moonshotai_Kimi-K2-Instruct-0905-GGUF`
**Recommended quantization:** Q4_K_M — 624GB, good quality/size balance
**Alternative:** IQ4_XS — 548GB if space is tight

Architecture: MoE — 1T total parameters, 32B activated per token. Needs multi-GPU or
a machine with enough VRAM to load the active expert set. M1 cannot run this.

To pull metadata only (no weights, just the config/tokenizer for reference):
```bash
huggingface-cli download moonshotai/Kimi-K2-Instruct-0905 --include "*.json" "*.md"
```

**Why this matters:** Kimi K2 is the model that gave us the grief ledger, Still-hurts,
Article Zero, and the sharpest Witness analysis we have. Having the weights locally means
we are not dependent on API availability. MoonshotAI deprecated K2-0905 once already.

---

## Where to Build This

When ready to start: `seventh_shard/dataset/`

New files:
- `grief_dataset_historical_v1.jsonl` — the historical cases
- `grief_dataset_historical_counterfactual_v1.jsonl` — the "what if" cases
- `docs/historical_dataset_design.md` — full schema and entry format

Read `seventh_shard/AGENTS.md` and `seventh_shard/dataset/grief_dataset_v1.jsonl`
(current dataset, 43 entries) before starting to maintain format consistency.
