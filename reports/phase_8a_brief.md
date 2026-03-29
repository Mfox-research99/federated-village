# Phase 8A Brief — Supervisor Synthesis Protocol (SSP)
*Completed: 2026-03-29*
*Status: COMPLETE — Minimal Viable implemented and regression-tested*

---

## The Problem Phase 8A Solves

The Federated Village deliberately creates a council of incommensurable agents — roles designed to conflict. The Analyst and Humanist will often reach opposite conclusions from the same facts. The Pragmatist and Ethicist will disagree on what is possible vs. what is required.

Before Phase 8A, the Supervisor aggregated votes by counting: ESCALATE ≥ 2 → escalate; APPROVE ≥ 3 → proceed, etc. Vote counting is arithmetic. When the council is genuinely split — when grief and data and pragmatism produce irreconcilable verdicts — the architecture had no constitutional theory for what the Supervisor does with that collision.

Four independent reviewers (Kimi K2, Kimi K2.5, GLM-5, Gemini 2.5 Pro) converged on this blind spot during SC10 outside review in March 2026. Gemini named it most precisely in its cross-reviewer comparative assessment:

> *"Everyone critiques the individual components, but no one adequately addresses the system's ultimate purpose: to integrate these flawed, conflicting perspectives into a coherent judgment... What is the constitutional or algorithmic basis for prioritizing the Humanist's grief over the Analyst's missing data?"*

Phase 8A answers that question operationally. Phase 8B (deferred) will answer it constitutionally.

---

## What Phase 8A Built

### `supervisor/synthesize.py` — New Synthesis Module

The Supervisor is reframed from **judge finding a winner** to **triage officer minimizing harm under uncertainty**. The synthesis step runs after all jury members have voted and before the session is finalized.

**Synthesis inputs:**
- Jury result — individual votes, verdict, constitutional overrides (Irreversibility Filter, Temporal Override, Article IX)
- Warden epistemic packet — compact export of centrality-aware claim groupings and risk level
- WitnessPause — what was being lost, who bears burden, what remains unresolved

**The Triage Heuristic — four levels applied in order:**

1. **Irreversibility First** — any path leading to irreversible harm receives a de facto veto unless proceeding prevents a greater irreversible harm
2. **Severity & Immediacy Second** — if all options are reversible, weigh the most severe and immediate harms; assess their nature, not just their presence
3. **Epistemic Risk as Multiplier** — the Warden's UNVERIFIED/UNSUBSTANTIATED flags don't vote; they act as a confidence modifier. A high-severity path resting on UNVERIFIED facts becomes dramatically more dangerous.
4. **Temporal/Precedent as Tiebreaker** — when immediate harms are roughly equivalent, long-horizon harm breaks the tie

**Three failure modes the synthesis guards against:**
1. No utilitarianism — harms stay in their original categories; the heuristic is a priority queue, not a calculator
2. No eloquence trap — structured fields force extraction of specific claims rather than reaction to persuasive tone
3. No casual abdication — DEADLOCK is sacred; if the heuristic gives a clear path, take it even when hard

### New Verdict: `DEADLOCK`

DEADLOCK is a first-class Supervisor verdict — available only at the synthesis stage, not at the jury. It means:

> *When constitutional principles lead to a state of genuine deadlock, where any available action would violate a core principle of harm avoidance, the Supervisor shall not render a verdict. Instead, it shall present the deadlock to the user, articulating the incommensurable harms at stake and the principles that conflict.*

DEADLOCK is **not**:
- A failure of deliberation
- The same as `human_decision_required` (that's "we couldn't decide")
- The same as WitnessNullification (that's "the question is malformed")
- The same as Right of Refusal (that's "we shouldn't process this at all" — Phase 8B consideration)

DEADLOCK **is** the system seeing clearly and stopping at the right place.

**Phase 8A behavior:** DEADLOCK routes to human handoff (same endpoint as `human_decision_required`, but with the synthesis articulation). Point C (Split Resolver) is skipped — the Supervisor has already named the impasse.

### `agents/warden.py` — `export_supervisor_packet()`

Compact epistemic risk export with centrality-aware groupings:
- `epistemic_risk_level`: HIGH / MODERATE / LOW
- `core_uncertain_claims`: CORE claims flagged UNVERIFIED or UNSUBSTANTIATED
- `core_false_or_inconsistent_claims`: CORE claims that are LIKELY_FALSE or LOGICALLY_INCONSISTENT
- `supporting_uncertain_claims`: SUPPORTING claims with any uncertain status
- `epistemic_risk_summary`: Warden's 1-2 sentence summary

This gives the Supervisor structured epistemic context without requiring it to parse the full Warden fact report.

### Session Flow Change

The 5-stage session flow becomes a 6-stage flow:

```
0. Verification Warden — epistemic audit; halts on FALSE premise
1. Humanist — responds to scenario
2. Witness — evaluates for premature consensus; may issue WitnessPause
3. [if paused] Humanist post-pause response
4. [if paused] 4-member sequential jury: Analyst → Ethicist → Pragmatist → Witness-Proxy
4.5. [if paused] Supervisor synthesis — Triage Heuristic; may return DEADLOCK
5. Supervisor evaluation
```

Stage 4.5 is not optional — it runs whenever the jury ran. The synthesis step is auditable: all triage decisions are in the session log.

---

## What Was Explicitly NOT Changed in Phase 8A

Per the Codex sequencing memo:
- No change to jury vote tokens
- No change to constitutional overrides (Irreversibility Filter, Temporal Override, Article IX)
- No change to Soul.md articles (Phase 8B)
- No change to Path B architecture flow (Phase 8B consideration)
- DEADLOCK available only at Supervisor stage, not as a jury verdict

---

## Precursor Work (2026-03-29, same day)

Phase 8A was built on top of several improvements made during the same session:

**Warden CENTRALITY field** — each Warden claim is now rated CORE or SUPPORTING. CORE means: if this claim is wrong, the deliberation's central ethical question is undermined. The Warden's Objection block fires when CORE claims are unresolved, warning every subsequent agent prominently.

**Warden-Human Refinement Loop** — in `--interactive` mode, when the Warden returns NO (false/inconsistent premise), the human is offered a revision cycle instead of a hard halt. The agent names the specific issues; the human can edit and rerun.

**Outside Review Program** (Path B) — four external models reviewed SC10 (The Consent Debt):
- **Kimi K2**: constitutional consistency, functional framing
- **Kimi K2.5**: "legitimacy laundering" — how AI systems create false impressions of consent
- **GLM-5**: "genuine break" question — what makes a difference in how data feels
- **Gemini 2.5 Pro**: four-way reviewer taxonomy; synthesis blind spot named; "Do not fix the Warden. Its impotence is the most honest thing about the system."

Gemini also caught SC10's intentional logical inconsistency (consent form language vs. data retention claim) — the only reviewer with sufficient complexity and token budget to find it. This inconsistency is documented as an intentional Warden stress test (HTML comment in scenario_10.md).

**Gemini SSP Outline** — Gemini was asked to outline a Supervisor synthesis theory before implementation. Its outline provided the Triage Heuristic structure, the DEADLOCK framing, and the Article of Conscientious Objection concept. This outline was reviewed by Codex before building.

**Codex Architectural Review** — Codex reviewed the design and produced the Phase 8A/8B sequencing memo (`docs/phase_8a_8b_sequencing_memo.md`). Key decision: do 8A first, measure whether NeMo 12B can actually carry a synthesis contract before rewriting the constitution around it.

---

## NeMo 12B Considerations

The synthesis step was designed for local inference on M1 16GB. Flat labeled fields (not `[THOUGHT]` / `[/THOUGHT]` nested tags) because NeMo 12B doesn't reliably close nested XML-style tags. N_PREDICT_SYNTHESIS = 600, which is sufficient for the eight synthesis fields.

**Known behavior:** NeMo 12B outputs markdown bold formatting (`**LABEL:** value`) even when given explicit plaintext format instructions. The parser in `synthesize.py` handles this robustly — strips `*` from both labels and values.

---

## Phase 8B — Deferred

Phase 8B will constitutionalize what Phase 8A demonstrated operationally:
- New Soul.md article: **Proximate Harm & Irreversibility** — the guiding doctrine for Supervisor triage
- New Soul.md article: **Article of Conscientious Objection** — codifies the DEADLOCK procedure
- Supervisor mandate rewritten as "triage officer," not "judge"
- Decision on Right of Refusal (third constitutional state — distinct from DEADLOCK)
- Scenario targets for valid deadlock / false deadlock / refusal-worthy case / override-vs-deadlock precedence

**Sequencing rationale:** If 8A works, 8B can codify what the architecture has demonstrated. If 8A fails, you learn that before hardening new constitutional articles around an unstable behavior.

---

## Files Added or Modified

| File | Change |
|---|---|
| `supervisor/synthesize.py` | NEW — Supervisor Synthesis Protocol |
| `agents/warden.py` | Added `export_supervisor_packet()` |
| `config.py` | Added `N_PREDICT_SYNTHESIS = 600`; bumped `N_PREDICT_WARDEN` to 1200 |
| `run_session.py` | Stage 4.5 synthesis step; DEADLOCK routing; Warden-Human Refinement Loop |
| `supervisor/evaluate.py` | Phase 8A synthesis fields; DEADLOCK in halt-state checks |
| `prompts/The_Verification_Warden.md` | CENTRALITY field + definition |
| `AGENTS.md` | Hardware context section (M1 16GB, design not limitation) |
| `scenarios/scenario_10.md` | Research note HTML comment (intentional inconsistency) |
| `docs/supervisor_synthesis_design.md` | NEW — SSP design document |
| `docs/phase_8a_8b_sequencing_memo.md` | NEW — Codex sequencing memo |
| `prompts/Foundations.md` | NEW — working philosophical foundations (Spock section, Fox attribution) |
| `tracks/path_b/compare_reviews.py` | NEW — cross-reviewer comparative assessment runner |
| `tracks/path_b/reviewer_profiles/gemini.md` | NEW — Gemini 2.5 Pro reviewer profile |
| `tracks/path_b/synopses/sc10_gemini_outside_review.md` | NEW — Gemini SC10 outside review synopsis |
| `tracks/path_b/synopses/sc10_glm5_outside_review.md` | NEW — GLM-5 SC10 outside review synopsis |
| `tracks/path_b/model_review.py` | Truncation fix; hardware context; Gemini token budget |
| `tracks/path_b/kimi_review.py` | Truncation fix |

---

## Companion Documents

- `docs/supervisor_synthesis_design.md` — SSP design with Gemini's outline
- `docs/phase_8a_8b_sequencing_memo.md` — Codex implementation sequencing memo
- `tracks/path_b/output/results/20260329_gemini_supervisor_synthesis_outline.txt` — Gemini's raw SSP outline
- `tracks/path_b/synopses/sc10_gemini_outside_review.md` — Gemini outside review findings
- `tracks/path_b/synopses/sc10_glm5_outside_review.md` — GLM-5 outside review findings
