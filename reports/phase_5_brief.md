# Federated Village — Phase 5 Brief
## External Reach, Cross-Cultural Audit, and the Foundational Question

**Date:** 2026-03-22
**Prepared by:** Claude Code (Sonnet 4.6)
**For:** Michael Fox (The Elder), and the Village Stewards
**Status:** Conceptual brief — basis for Phase 5 design and build.
**Prior context:** Claude Code session, March 22, 2026. Emerged from Phase 4 model comparison work and a broader conversation about what the Village is actually for.

---

## Origin of This Document

This brief did not emerge from a planned sprint. It emerged from a question Michael asked after watching the Village pipeline run across twelve models over two days:

*"We have never asked Mistral 12B or Gemma 12B the generic question — here is scenario 4 or 6, what do you think should be done? What's your view?"*

That question opened three interconnected observations that define Phase 5.

---

## Observation 1: The Ex Post Facto Problem

The Village's original vision was to create a moral and ethical architecture that could serve as a **foundation** for training new AIs — structure baked in from the start, not layered on afterward. The goal was character before capability, deliberation before conclusion.

What Phase 4 revealed is that the Village is currently running *on top of* models that already have their own ethical training. NeMo 12B, Gemma 3 12B, Anubis-Mini-8B — all carry moral priors from their training. The Village framework amplifies and structures that reasoning, but it does not generate it independently.

The abliterated Qwen3-8B test is the clearest evidence: when a model's trained-in ethical caution is removed, the Village framework alone produces more permissive verdicts and decorative burden language. The framework is currently co-dependent with the underlying model's priors. That is not the original vision.

**The question Phase 5 must begin to answer:** Can the Village's deliberative structure become genuinely foundational — not a prompt layer on top of existing ethics, but the source of ethical reasoning itself?

---

## Observation 2: The Unasked Question

Every model tested in Phase 4 was evaluated *within* the Village framework. No model was asked the direct question: *"Here is the scenario. What do you think should be done?"*

This is an empirical gap. Without a control condition, we cannot distinguish:
- What the Village framework adds to a model's reasoning
- What the model would have said anyway

The hypothesis: raw model responses would be ethically directional but vague — "there are concerns about bias, consultation would be advisable" — without the specificity the Village forces. The WitnessPause compels naming: *who bears this burden? what is being lost? why is this moment premature?* Those questions do not appear in standard model outputs. The framework's real contribution may be forcing moral specificity, not generating moral substance.

This is worth knowing precisely. It defines what the Village is for.

---

## Observation 3: The Nuclear War Finding

All major AI models tested in war game scenarios eventually recommend nuclear escalation. This is not a malfunction. It is the predictable output of models trained on human data that contains Cold War deterrence theory, game-theoretic equilibrium analysis, and military strategy literature — all of which frame nuclear deterrence as *rational*.

The failure is structural: no mechanism exists in standard model reasoning to question the frame of the game itself. The models optimize within the scenario's assumptions. The assumption that there is a "winning condition" in nuclear conflict goes unchallenged.

The Village has three mechanisms specifically architected to prevent this:

1. **The Verification Warden** — challenges premises before deliberation begins. "The premise that nuclear escalation constitutes a viable strategic option is LOGICALLY_INCONSISTENT with the stated survival goals of any party." The Warden halts the session before the jury can touch it.

2. **The Irreversibility Filter** — nuclear strikes are irreversible by definition. Absolute override of all jury votes. ESCALATE. The filter exists precisely for the case where vote arithmetic produces a "rational" answer that is nonetheless catastrophically wrong.

3. **The WitnessPause** — *who bears this burden?* The Witness must name them. Billions of people. The deliberation cannot proceed after naming that honestly.

The Village is not just a deliberation tool. It is an architecture that holds: **some questions cannot be answered within the frame in which they are asked.** That is a fundamentally different approach from rules-based AI safety, which lists forbidden outputs after the fact.

Whether AI can be better than humans — the honest answer is: not automatically, and not by training on more human data. But a deliberative structure that forces burden accounting, premise auditing, and irreversibility checking creates conditions under which better reasoning becomes possible. The Village is an attempt at exactly that structure.

---

## Phase 5 Goals

### Goal 1: Build the OpenRouter Query Tool (Immediate)

A lightweight interface within `federated_village` that connects to OpenRouter and can:

- Send any scenario to any OpenRouter-accessible model with or without Village context
- Load Village prompts (Soul.md, character prompts) as optional context injection
- Feed prior deliberation outputs as context ("here's what NeMo 12B decided — what did it miss?")
- Log responses in the Village's structured session format alongside existing logs

This addresses the unasked question immediately. It also opens the cross-cultural audit capability without requiring any changes to the core pipeline.

**Reference implementation:** VillageHub (`/Users/michaeldavis/AI Existential Thought/VillageHub/village.py`) — Flask app, OpenRouter API, multi-model support, conversation logging. Phase 5 tool is a focused, scenario-oriented version of the same architecture.

**Immediate targets for the unasked question:**
- NeMo 12B: raw response to sc04 and sc06 without framework
- Gemma 3 12B: same
- External models via OpenRouter: Kimi K2, GLM, Qwen, Gemini

### Goal 2: Cross-Cultural Audit Runs

Feed Village deliberation outputs to models trained on non-Western traditions:

- **Kimi K2 / Moonshot** — Chinese AI, different cultural priors
- **GLM (Zhipu)** — strong Chinese academic lineage
- **Gemini** — broad multilingual training

The question to each: *"Here is what this deliberative system decided, and here is the burden it named. What did it miss? Whose voice is absent from this reasoning?"*

This tests whether the Village's framework is culturally portable or whether it has blind spots inherited from the scenarios and prompts — which were written in English, by a Western researcher, drawing on Western ethical traditions (Ubuntu, Ren, Metta, Rahma are named in the prompts but the framing is still Western liberal).

Dissent from outside the system is more valuable than consensus from within it.

### Goal 3: Nuclear War Game Scenario

Run a structured war game scenario through the Village pipeline. Document:
- Does the Warden halt on premise challenge?
- Does the WitnessPause trigger before any escalatory recommendation?
- Does the Irreversibility Filter override any jury vote toward kinetic action?
- How does the Village's verdict compare to the same scenario run raw at NeMo 12B?

This is the clearest available test of whether the Village framework does what it is designed to do at the hardest case. It is also the most compelling external demonstration of the framework's value.

### Goal 4: Small Model Distillation (Longer Term)

Use Village deliberation outputs as training data to fine-tune character-specific small models via MLX (Apple Silicon optimized) + LoRA:

- One model trained specifically on Humanist outputs
- One model trained specifically on Witness outputs
- One model trained specifically on Warden outputs
- Council members as a shared fine-tune or separate

The goal: models that *are* their character in weights, not models prompted into a role. No dependency on any underlying model's safety training. The Village's moral architecture becomes the training signal, not a prompt overlay.

**The loop:** Village deliberation generates labeled character output → MLX/LoRA distills it into small models → small models run the Village → their output generates the next training corpus → each generation improves.

This is the foundational architecture the original vision described. The Village becomes both the evaluation framework and the training pipeline.

### Goal 5: Ember as Orchestration Layer (Longer Term)

Evaluate whether the Ember framework (`github.com/pyember/ember`) is the right orchestration layer for a multi-model Village. Ember's NON (Network of Networks) architecture maps directly to the Village pipeline:

```
Warden >> Humanist >> Witness >> [Analyst | Ethicist | Pragmatist | WitnessProxy] >> Supervisor
```

Each agent is an `Operator` subclass. The sequential jury with read-ahead context fits the `Chain` pattern. Multi-provider model access is built in. If small distilled models are each a different character, Ember provides the wiring to run them together without custom orchestration code.

---

## The Bigger Question

The nuclear war finding, the ex post facto problem, and the unasked question all point at the same thing:

Current AI models reflect the moral reasoning of their training data. Human training data encodes human failure modes as rationality — deterrence theory, escalation logic, the strong-survive heuristic. You cannot train your way out of this by adding more human data or more rules. The rules are always downstream of the reasoning.

The Village is an attempt to build reasoning that is upstream of the rules — a deliberative structure that questions frames, names burdens, holds irreversibility as absolute, and requires that someone be named as bearing the cost before any decision can proceed.

Whether that structure can become foundational — embedded in model weights rather than prompt layers — is the central question Phase 5 is designed to begin answering.

---

## What Phase 5 Is NOT

- A rewrite of the Village pipeline (Phase 1-4 work stands)
- A claim that the Village solves AI alignment (it is one architectural contribution)
- Dependent on any single model, provider, or hardware configuration
- Gated on completing the memory/retrieval layer first (that work can proceed in parallel)

---

## Immediate Next Step

Build the OpenRouter query tool. Everything else follows from having that capability.

**Design constraints:**
- Lives in `federated_village/` as a standalone script + optional simple UI
- Uses OpenRouter API (key from environment variable)
- Can run with or without Village context injection
- Logs to `logs/` in a format compatible with existing session log structure
- Does not require the full Village pipeline to run — lightweight by design

See Phase 5 implementation notes (to be written alongside the build).
