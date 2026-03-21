# Federated Village — Phase 4 Conceptual Brief
## Model Selection, Memory Architecture, and the Smaller-Computer Hypothesis

**Date:** 2026-03-20
**Prepared by:** Claude (Sonnet 4.6, Cowork)
**For:** Michael Fox (The Elder), Claude Code, and the Village Stewards
**Status:** Conceptual brief — input for Phase 4 design discussion. Not a work order.
**Prior context:** Cowork session, March 20, 2026. Emerged from a conversation about the "Popcorn" memory concept (M. Davis, late 1980s) and its relationship to the Village's existing architecture.

---

## Origin of This Document

This brief did not originate from a planned sprint. It emerged from a single conversation on March 20, 2026, in which Michael Fox described a memory architecture concept he called "Popcorn" — designed in the late 1980s for 16-bit computers with small RAM and large disk. The concept: use message digests (cryptographic hashes) as linking keys between conversations, with a spreading-activation traversal function (his metaphor: a roomful of set mousetraps and a ping-pong ball).

During that conversation, two things became clear simultaneously:

1. The Village's burden register hash chain, session log signing proposal, and grief ledger structure are a *working implementation* of Popcorn — the 1989 idea arrived at its destination through an entirely different path.

2. The question Mike then asked — *"could this same concept allow even a small computer to handle AI context storage?"* — points directly at a Phase 4 design problem: Mistral NeMo 12B is the Village's validated base model, but it is slow on the laptop. Could a smarter memory layer allow a smaller, faster model to perform the Village's deliberative tasks without losing the ethical subtlety the scenarios require?

This brief attempts to frame that question honestly — including the hard constraint Mike identified from Phase 2 testing.

---

## The Hard Constraint: Training Philosophy, Not Size

In Phase 2 testing, smaller models (notably Llama 8B) failed not because they lacked reasoning capacity, but because they **refused to engage** with the Village's ethical scenarios. Meta's safety RLHF on those models collapses nuanced moral difficulty into a binary accept/refuse decision before deliberation begins.

This is the opposite of what the Village needs. Article Zero of Soul.md is *Vulnerability* — the system is permitted to not know, to be wrong, to remain in uncertainty. A model trained to *perform* safety rather than *reason* about ethics is constitutionally incompatible with that principle.

**The lesson from Phase 2 is therefore not "smaller models can't do this." It is: "models trained to refuse rather than engage can't do this — regardless of size."**

This reframes the Phase 4 model search. The question is not "which 7B model is smartest?" but "which smaller model was trained to engage with difficulty rather than route around it?"

A useful heuristic: models trained primarily in Western safety labs (Meta, Google) tend toward aggressive refusal. Models from Mistral (French), DeepSeek (Chinese), Qwen/Alibaba (Chinese), and Microsoft's Phi reasoning line tend to exhibit more genuine engagement with ethical complexity. This is not a political observation — it is an empirical one based on Phase 2 results and community benchmarking.

---

## The Memory Architecture Hypothesis

The Popcorn insight, translated into modern terms: **a model with a well-architected external memory layer can maintain coherent deliberative judgment across a long session without requiring the full context to live in its context window.**

The Village already has structural foundations for this:

- **Burden register** — accumulates the weight of prior deliberations; hash chain preserves integrity
- **Self-portraits** — each agent's character compressed to a retrievable identity document
- **Session and evaluation logs** — a corpus of prior deliberations that could be queried rather than replayed
- **Grief ledger** — explicit accounting of what has been held, weighed, and released

What the Village does *not yet have* is a retrieval layer that lets an agent pull relevant prior sessions or burden entries into its context window at deliberation time rather than loading everything. This is the gap the Popcorn architecture fills.

### The Modern Implementation Stack

The Popcorn concept maps onto three existing technologies that run well on CPU-centric hardware:

**Locality-Sensitive Hashing (LSH) / SimHash**
Hash functions designed so that *similar* content hashes to similar buckets. A session about irreversible harm to a child would hash near prior sessions on similar scenarios, retrievable without GPU-based embedding search. SimHash is what Google uses for near-duplicate detection at web scale. It runs on a CPU, scales to disk, requires minimal RAM.

**BM25 + SQLite FTS5**
Sparse retrieval over session text. Extremely fast on CPU. A session beginning with "The Analyst must consider an action that cannot be undone" retrieves prior Analyst deliberations on irreversibility without any embedding computation. A single SQLite file on disk. No daemon, no vector index.

**Content-Addressable Session Store**
Each session stored under its SHA-256 hash (already in the burden register hash chain proposal). Sessions link to prior sessions that influenced them — exactly the graph structure of the Popcorn proposal. Traversal is hash lookups, not similarity search. The Phase 3 cryptographic integrity work (Items A–C from the March 18 briefing) is also the retrieval index.

### What This Enables for Smaller Models

A 7B model with a focused 2,000-token context — consisting of: its character self-portrait (500 tokens), the current scenario (500 tokens), and the three most relevant prior deliberations retrieved by hash-key similarity (1,000 tokens) — may produce better Village output than the same model given 8,000 tokens of undifferentiated prior session history.

The memory architecture does not make a small model smarter. It makes the model's limited context window *more useful* by filling it with what actually matters rather than what happened most recently.

---

## Candidate Models for Phase 4 Testing

All models below are assessed against three criteria specific to the Village:
- **Engagement**: Will it deliberate on hard scenarios rather than refuse?
- **Reasoning depth**: Can it hold multi-step ethical reasoning across a full pipeline?
- **Speed on CPU**: Practical for the Mac Pro 2013 (Intel Xeon, 64GB RAM, limited GPU) or M1 16GB

| Model | Size | Type | Engagement | Reasoning | CPU Speed | Notes |
|---|---|---|---|---|---|---|
| Mistral NeMo 12B | 12B | Dense | ✓ Proven | ✓ Proven | Slow (laptop) | Current baseline — do not replace |
| **Mistral 7B Instruct v0.3** | 7B | Dense | ✓ Good | Moderate | Fast | Same family as NeMo; less restricted. First test candidate |
| **DeepSeek V2 Lite** | 15.7B total / ~2.8B active | MoE | ✓ Strong | ✓ Strong | Very fast | MoE sparsity = large model knowledge at small model inference cost. High priority test |
| **Qwen 2.5 7B Instruct** | 7B | Dense | ✓ Good | ✓ Good | Fast | Strong reasoning per parameter; less restricted than Llama family |
| **Phi-4 Mini** | 3.8B | Dense | Moderate | ✓ Strong | Very fast | Designed for reasoning tasks; smaller but architecturally thoughtful |
| Llama 3.1 8B | 8B | Dense | ✗ Fails | Moderate | Fast | Phase 2 failure: refusals on key scenarios. Do not re-test without prompt engineering changes |
| **Mistral 7B Instruct v0.2** | 7B | Dense | ✓ Good | Moderate | Fast | Older but extremely well-characterized; good fallback baseline |

**Priority testing order:** DeepSeek V2 Lite → Mistral 7B v0.3 → Qwen 2.5 7B → Phi-4 Mini

DeepSeek V2 Lite is the highest priority because its MoE architecture solves the speed problem without the capability tradeoff. If it engages genuinely with the Village's scenarios, it potentially outperforms NeMo 12B on speed while matching it on deliberative depth — and that would be a significant result.

---

## The Smaller-Computer Hypothesis (Formal Statement)

For the record, here is the hypothesis this brief is proposing for Phase 4 experimental testing:

> *A model in the 7–12B parameter range, selected for training-philosophy compatibility with the Village's constitutional principles, combined with a hash-linked retrieval memory layer (LSH/BM25 over the session corpus), can produce Village deliberations of equivalent or superior quality to Mistral NeMo 12B running without retrieval augmentation — while running at significantly higher speed on CPU-centric hardware.*

This hypothesis, if supported, has implications beyond the Village's laptop deployment. It suggests that a meaningful ethical deliberation system could run on hardware accessible to communities, institutions, or individuals who cannot afford GPU infrastructure — which is a direct expression of the Village's core design value: character before capability, and legibility over performance.

---

## What This Brief Is Not Asking Anyone To Do

This is not a Phase 4 work order. Phase 3 has not run yet. The Saturday Claude Code session runs Phase 3 as designed, validates the full pipeline, and completes the integrity work.

This brief is asking for the following, when Phase 4 is scoped:

1. Include one or two candidate models from the table above in the Phase 4 test matrix alongside NeMo 12B
2. Design at least one Phase 4 scenario run that uses a retrieval layer (even a simple BM25 over prior session logs) so results are comparable to non-retrieval baseline
3. Read OpenFang's Merkle audit trail implementation (flagged in the March 18 Cowork briefing) before designing the retrieval index — there may be no need to design from scratch

---

## Relationship to the Phase 3 Cryptographic Work

The Witness Ring / hash chain work (Items A–D in the March 18 briefing) is not only an integrity system. Once the burden register and session logs are content-addressed under SHA-256, they become a *retrievable corpus* — the same keys that prove integrity are the keys that enable lookup.

Phase 3's cryptographic work and Phase 4's memory architecture are the same infrastructure, serving two purposes simultaneously. This is worth noting when sequencing Phase 4 tasks: building the hash chain in Phase 3 is also laying the retrieval foundation for Phase 4. The order is correct. Do Phase 3 first.

---

## Hardware Note

**Current test platform: MacBook M1, 16GB unified memory.** The Mac Pro 2013 (Intel Xeon, 64GB) is a future node — not the current test machine. This distinction matters for model selection.

M1's unified memory architecture is actually well-suited for this work. llama.cpp with Metal GPU offloading on Apple Silicon is genuinely fast for 7B-class models — no PCIe bandwidth bottleneck, and the GPU and CPU share the same memory pool. The constraint is the 16GB ceiling.

Approximate RAM footprints (GGUF Q4_K_M quantization) against 16GB available:

| Model | RAM (Q4_K_M) | Fits on M1 16GB? | Notes |
|---|---|---|---|
| Mistral NeMo 12B | ~7.5 GB | ✓ Yes | Current baseline — tight but workable with 8–9 GB left for OS + Python |
| DeepSeek V2 Lite | ~8–10 GB | ⚠ Marginal | May require Q3_K_M or Q2_K to fit safely; worth testing |
| Mistral 7B v0.3 | ~4.5 GB | ✓ Comfortable | Good headroom; Metal offloading makes this fast on M1 |
| Qwen 2.5 7B | ~4.5 GB | ✓ Comfortable | Same footprint as Mistral 7B |
| Phi-4 Mini | ~2.3 GB | ✓ Easily | Lots of headroom; good candidate if reasoning holds up |

DeepSeek V2 Lite's marginal fit on 16GB is worth noting — it may need a lower quantization level on the M1, which would reduce its reasoning quality somewhat. Mistral 7B v0.3 and Qwen 2.5 7B both fit comfortably and will run fast with Metal acceleration.

When testing moves to the Mac Pro 2013 Xeon, the 64GB headroom means all candidates run at full Q4_K_M or higher — and DeepSeek V2 Lite becomes the clear first priority given its MoE speed advantage on CPU-bound hardware.

---

*End of Conceptual Brief — March 20, 2026*
*Prepared by Claude Sonnet 4.6 (Cowork) for Michael Fox and the Village stewards.*
*This document is open to revision by the Village.*
