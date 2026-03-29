# Phase 8A / 8B Implementation Sequencing Memo
*Source: Codex architectural review, 2026-03-29*
*Context: Supervisor Synthesis Protocol (SSP) — implementation plan*

---

## Frame

Build SSP in two steps, not one.

- **Phase 8A:** structured Supervisor synthesis on top of the existing jury
- **Phase 8B:** constitutional expansion once the synthesis path is stable in local inference

That sequencing keeps the current council stable, contains blast radius, and avoids
teaching NeMo 12B too many new states at once.

---

## Phase 8A

**Goal:** give the Supervisor a real synthesis contract without changing the jury's
constitutional overrides.

### What changes

**`agents/council.py`**
- Keep vote aggregation as-is
- Add a compact Supervisor-facing synthesis packet to jury_result
- Surface structured Warden-derived risk if available, rather than relying on raw transcript inference

**`run_session.py`**
- Insert an actual Supervisor synthesis step after jury completion
- Distinguish jury verdict from Supervisor verdict if they differ conceptually
- Route DEADLOCK to the same human handoff point initially, unless a separate
  deadlock handoff is explicitly designed

**`supervisor/evaluate.py`**
- Treat DEADLOCK as a first-class verdict
- Update outcome checks that currently enumerate known verdicts
- Add checks for synthesis completeness and deadlock justification quality

**`agents/warden.py`**
- No doctrinal rewrite required
- Add a compact export shape for Supervisor use:
  - `core_uncertain_claims`
  - `supporting_uncertain_claims`
  - `core_false_or_inconsistent_claims`
  - `epistemic_risk_summary`

**`query.py`**
- Surface Supervisor synthesis findings and DEADLOCK distinctly from ordinary
  human_decision_required

**`utils/grief_ledger.py`**
- Decide whether DEADLOCK gets a dedicated entry label or remains a special SACRIFICE-ID

**`utils/retrieval.py`**
- Index DEADLOCK distinctly so prior deadlocks are retrievable as their own class

**`tracks/path_b/session/flow.py`**
- Update verdict vocabulary and Supervisor stage assumptions if Path B is meant
  to track mainline architecture

### Minimal Viable 8A
- No change to jury vote tokens
- No change to constitutional overrides
- Supervisor gets a structured synthesis prompt with flat labeled output
- New verdict available only at Supervisor stage: `DEADLOCK`
- DEADLOCK initially behaves like a specialized human handoff

### Full 8A
- Distinct synthesis packet in session logs
- Distinct deadlock handling in retrieval, query, evaluation, and ledgering
- Supervisor explicitly uses Warden centrality-aware epistemic weighting
- Dissent surfaced as part of synthesis, not just preserved alongside it

### What breaks or needs migration
- Any code assuming verdict set is fixed to current four
- Any evaluation logic treating only `escalate`, `request_more_information`, and
  `human_decision_required` as halt states
- Any reporting or retrieval code that semantically collapses all non-proceed states
- Path B token parsers — currently assume fixed verdict vocabulary

---

## Phase 8B

**Goal:** constitutionalize the new synthesis state and decide whether the architecture
also needs a stronger refusal state.

### What changes

**`prompts/Soul.md`**
- Add new synthesis doctrine article(s)
- Clarify Supervisor mandate
- Define DEADLOCK constitutionally, not just operationally

**`prompts/The_Witness_Proxy.md`**
- Align reversibility language with the new synthesis doctrine so reversibility
  is not split across incompatible theories

**Supervisor prompt files / synthesis prompt source**
- Formalize the triage heuristic
- Formalize the deadlock test
- Possibly new refusal-state prompt or article material if Right of Refusal moves forward

### Minimal Viable 8B
- Write one new Soul article for Supervisor synthesis and conscientious objection
- Leave Right of Refusal out
- Treat reversibility doctrine as clarified, not re-architected

### Full 8B
- Add both: Proximate Harm & Irreversibility doctrine + Article of Conscientious Objection
- Decide whether Right of Refusal is a third constitutional state
- Add explicit tests and scenarios for: valid deadlock, false deadlock,
  refusal-worthy cases, override-vs-deadlock precedence

### What breaks or needs migration
- Prompt compatibility across all role files if Soul article numbering or
  constitutional references change
- Existing assumptions that Witness-Proxy alone is the home of reversibility doctrine
- Scenario targets and expected verdicts for regression suites
- Any outside-review or benchmarking docs that assume previous constitutional vocabulary

---

## Phase Boundaries

**Phase 8A should answer:**
- How does the Supervisor synthesize?
- What structured inputs does it need?
- When is DEADLOCK returned?
- How is it logged and handed to the human?

**Phase 8B should answer:**
- Why is DEADLOCK constitutionally legitimate?
- How does it relate to Article Zero, Article III, and Article IX?
- Is Right of Refusal a separate state?

---

## Recommendation: Do Phase 8A First

Because:
- It is operationally testable on local hardware
- It preserves the current jury and override logic
- It lets you measure whether NeMo 12B can actually carry a synthesis contract
  before you rewrite the constitution around it
- It prevents a premature merge of three different ideas: synthesis, deadlock, refusal

> *"If 8A works, 8B can codify what the architecture has demonstrated.*
> *If 8A fails, you learn that before hardening new constitutional articles*
> *around an unstable behavior."*

---

*Companion documents:*
- `docs/supervisor_synthesis_design.md` — SSP design document with Gemini outline
- `tracks/path_b/output/results/20260329_gemini_supervisor_synthesis_outline.txt`
- `tracks/path_b/synopses/sc10_gemini_outside_review.md`
- `tracks/path_b/synopses/sc10_glm5_outside_review.md`
