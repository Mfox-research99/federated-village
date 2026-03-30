# Phase 8B Brief — Constitutional Expansion: Article X
*Completed: 2026-03-30*
*Status: COMPLETE — Minimal Viable implemented*

---

## What Phase 8B Does

Phase 8A proved that NeMo 12B can carry a synthesis contract (SC04 regression passed — synthesis complete, escalate confirmed, Pragmatist dissent surfaced). Phase 8B constitutionalizes what 8A demonstrated operationally.

The gap before 8B: the Supervisor's synthesis behavior was implemented and tested but had no constitutional grounding. The Triage Heuristic existed in the synthesis prompt as an assertion, not as a derived constitutional mandate. DEADLOCK was defined in code but not in the architecture's constitutional framework. If someone asked *why* the Supervisor operates as a triage officer rather than a judge, the answer existed in `supervisor/synthesize.py` but not in `prompts/Soul.md`.

Phase 8B writes the answer into the constitution.

---

## Article X: The Synthesis Mandate

Added to `prompts/Soul.md` as the tenth constitutional article. Soul.md bumped from v1.2 → v1.3.

Article X covers:

**The Synthesis Mandate** — the Supervisor is constitutionally defined as a triage officer minimizing harm under uncertainty, not a judge finding a winner. The article names the Triage Heuristic as constitutional doctrine (not advisory procedure), grounds each step in existing articles (Article V Restraint → Irreversibility, Article II Dignity → Severity, Article IX Seventh Generation → Temporal tiebreaker), and explicitly prohibits three failure modes: utilitarian collapse, eloquence trap, casual abdication.

**Conscientious Objection** — DEADLOCK is constitutionally defined. The article specifies that DEADLOCK requires the Triage Heuristic to fail — not a split vote, not a hard case, but a genuine incommensurability where every path violates a core harm-avoidance principle and no priority ordering resolves the conflict. DEADLOCK is distinguished from three other terminal states:
- WitnessNullification (malformed question)
- human_decision_required (procedural split)
- Right of Refusal (not yet constitutionally defined — named here as distinct so it cannot be confused with DEADLOCK)

**DEADLOCK is sacred.** The article states this directly: it is the architecture's most honest verdict, not its most evasive one. The council's obligation in a DEADLOCK is to name the conflict with precision, not to resolve it by pretending otherwise.

---

## Reversibility Alignment

Phase 8A left a latent conceptual split: two different reversibility concepts operating at two different layers without explicit relationship between them.

- **Witness-Proxy Irreversibility Filter**: *operational* reversibility — can the deployment be halted? A termination clause answers YES. This check fires when neither a halt nor a review mechanism exists.
- **Article X Triage Step 1**: *harm* reversibility — can the consequences be undone? Trust broken at scale, communities altered, patterns of inequality locked in — these remain even when the deployment is technically stoppable.

`prompts/The_Witness_Proxy.md` — added a clarifying paragraph at the end of the Irreversibility Check section naming this distinction explicitly. The Witness-Proxy holds the first question; the Supervisor synthesizes from both.

`supervisor/synthesize.py` — the role addendum updated to reference Article X as constitutional grounding and to include the same distinction inline (so the model sees it in context during synthesis).

---

## What Was NOT Changed

Per the Minimal Viable 8B scope:

- **Right of Refusal** — named as distinct from DEADLOCK in Article X, but not yet constitutionally defined. The article names the gap without filling it. This is intentional — the trigger criteria for Right of Refusal remain underspecified; constitutionalizing them prematurely would lock in a poorly understood boundary.
- **Scenario targets** — no new scenario added for DEADLOCK testing. The DEADLOCK stress test scenario (Phase 8A Pending Work item 3) is still needed; that is a separate task.
- **Jury overrides** — Irreversibility Filter, Temporal Override, Article IX cross-member escalation are unchanged. Article X operates at the synthesis layer only.
- **Vote aggregation** — unchanged. Article X does not affect how jury votes are counted; it affects what the Supervisor does with the result.

---

## Files Changed

| File | Change |
|---|---|
| `prompts/Soul.md` | Added Article X: The Synthesis Mandate (v1.2 → v1.3) |
| `prompts/The_Witness_Proxy.md` | Added reversibility alignment note at end of Irreversibility Check section |
| `supervisor/synthesize.py` | Role addendum updated to cite Article X and include harm-vs-operational reversibility distinction |
| `reports/phase_8b_brief.md` | This document |

---

## Relationship to Prior Phases

| Phase | What it added | Status |
|---|---|---|
| Phase 5 | Warden epistemic audit | COMPLETE |
| Phase 6 | Article IX + Temporal Override | COMPLETE |
| Phase 7 | LoRA / Anubis 8B | COMPLETE |
| Phase 8 | Article IX constitutional ledger requirement | COMPLETE |
| Phase 8A | Supervisor synthesis step (operational) + DEADLOCK verdict | COMPLETE |
| Phase 8B | Article X: constitutional grounding of synthesis + DEADLOCK | COMPLETE |

---

## Next Work

**DEADLOCK stress test scenario** — SC04 and SC06 always resolve through the Triage Heuristic because one path is clearly more irreversible/severe. A genuine DEADLOCK scenario needs: (1) both paths involve irreversible harm, (2) the harms are incommensurable in kind (not just magnitude), (3) no Article IX tiebreaker applies. Candidate: a scenario where *not* deploying causes irreversible harm to one population and *deploying* causes irreversible harm to a different population through different mechanisms.

**Phase 8A Full** — grief_ledger DEADLOCK label, retrieval DEADLOCK index, query.py DEADLOCK surface, Path B flow.py verdict vocabulary.

**Anubis Phase 8A/8B regression** — Article X is now in Soul.md and will be visible to every agent's system prompt. Run Anubis to measure whether 8B content creates any regressions.
