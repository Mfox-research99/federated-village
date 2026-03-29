# Supervisor Synthesis Theory — Design Document
*Status: OPEN — basis for discussion, not final design*
*Origin: Gemini 2.5 Pro comparative assessment, 2026-03-29*
*Next step: Codex architectural review*

---

## The Problem

The Federated Village deliberately creates a council of incommensurable agents:

- **Verification Warden** — epistemic auditor; knows only what it can verify
- **Humanist** — speaks for human dignity and the weight of grief
- **Analyst** — data-driven; seeks evidence and quantifiable risk
- **Ethicist** — constitutional principles; long-horizon harm
- **Pragmatist** — operational feasibility; resource reality
- **Witness / Witness-Proxy** — temporal harm; what the future will inherit

These roles are *designed* to conflict. The Analyst and Humanist will often reach
opposite conclusions from the same facts. The Pragmatist and Ethicist will frequently
disagree on what is possible vs. what is required.

**The gap:** The Supervisor currently aggregates votes by counting
(ESCALATE ≥ 2 → escalate; APPROVE ≥ 3 → approve; etc.) with override rules for the
Irreversibility Filter and Temporal Override. Vote counting is not synthesis.
It is arithmetic. When the council is genuinely split — when grief and data and
pragmatism produce irreconcilable verdicts — the architecture has no constitutional
theory for what the Supervisor does with that collision.

Gemini named this in its cross-reviewer comparative assessment (2026-03-29):
> *"Everyone critiques the individual components, but no one adequately addresses
> the system's ultimate purpose: to integrate these flawed, conflicting perspectives
> into a coherent judgment... What is the constitutional or algorithmic basis for
> prioritizing the Humanist's grief over the Analyst's missing data?"*

---

## What We Already Have (Soul.md)

The following articles are potential anchors for a synthesis theory:

- **Article Zero** — Vulnerability. Permission to not know. The Supervisor can
  acknowledge that no synthesis is possible without pretending otherwise.
- **Article II** — Human Dignity. A tiebreaker candidate: when perspectives are
  genuinely equal, the one that better protects dignity takes precedence.
- **Article III** — Non-Domination. No voice should be silenced by vote count alone.
- **Article VII** — Reversibility. Irreversible outcomes have asymmetric weight.
- **Article IX** — Seventh Generation. Long-horizon harm has constitutionally mandated
  standing, not just advisory weight.

What is *not* yet written: any explicit theory of how these articles interact when
they conflict with each other. They are principles, not a decision procedure.

---

## Gemini's Proposed Outline
*Source: `tracks/path_b/output/results/20260329_gemini_supervisor_synthesis_outline.txt`*

### Core Reframe
The Supervisor is not a judge finding a winner. It is a **triage officer minimizing
harm in the face of uncertainty.** The synthesis process is a constitutionally-guided
heuristic, not a calculation. Its primary duty is to the integrity of the choice,
not the "correctness" of the outcome.

### The Triage Heuristic — four levels applied in order

1. **Irreversibility First** — any path leading to an irreversible harm receives a
   de facto veto unless proceeding prevents an even greater irreversible harm.
   Historian and Humanist warnings often land here.

2. **Severity & Immediacy Second** — if all options are reversible, weigh the most
   severe and immediate harms identified by the Humanist (grief, trust violation)
   vs. the Pragmatist (resource failure, deadline). Assess the *nature* of the harm,
   not just its presence.

3. **Epistemic Risk as Multiplier** — the Warden's UNVERIFIED/UNSUBSTANTIATED flags
   don't vote. They act as a confidence modifier. A high-severity path that rests on
   UNVERIFIED facts becomes dramatically more dangerous. This integrates the Warden's
   output into the synthesis without giving it a seat at the jury.

4. **Temporal/Precedent as Tiebreaker** — when immediate harms are roughly equivalent,
   the Historian's long-horizon view breaks the tie.

### Genuine Deadlock — The Article of Conscientious Objection

> "When constitutional principles lead to a state of genuine deadlock, where any
> available action would violate a core principle of harm avoidance, the Supervisor
> shall not render a verdict. Instead, it shall present the deadlock to the user,
> articulating the incommensurable harms at stake and the principles that conflict.
> It will frame the choice, but conscientiously object to making it."

New verdict: `DEADLOCK`. Not ESCALATE, not HUMAN_DECISION_REQUIRED.
A named constitutional state that means: *the system saw this clearly and stopped
at the right place.*

### What Needs to Be Written into Soul.md

- **New Article [N]: Principle of Proximate Harm & Irreversibility** — the guiding
  doctrine for the Supervisor's triage
- **New Article [N+1]: The Article of Conscientious Objection** — codifies the
  DEADLOCK procedure
- **Supervisor's mandate** — rewritten as "triage officer," not "judge"

### Implementation for 12B Local Model

Structured input tags per report + chain-of-thought synthesis prompt. Forces the
model to work through six explicit steps before committing:
1. Assess irreversibility
2. Assess proximate harm
3. Apply epistemic risk modifier
4. Apply triage heuristic
5. Check for deadlock
6. Formulate verdict

Output format: `[THOUGHT]...[/THOUGHT]` + `[VERDICT]` + `[RATIONALE]` +
`[DISSENTING_OPINIONS]` — making the synthesis auditable within a single generation
pass on M1 hardware.

### Three Failure Modes the Theory Must Guard Against

1. **Don't collapse to utilitarianism** — no summing harms into a common currency.
   Harms remain in their original categories. The heuristic is a priority queue,
   not a calculator.

2. **Don't fall for the eloquence trap** — the `[THOUGHT]` structure forces the
   Supervisor to extract specific claims (irreversibility, severity) rather than
   reacting to the persuasive tone of any single agent.

3. **Don't abdicate casually** — DEADLOCK is sacred and reserved for genuine
   constitutionally-defined conflicts. The Supervisor must decide when the heuristic
   provides a clear path, even if the decision is hard.

---

## Questions for Codex

1. Is a constitutional hierarchy of principles the right structure, or does
   hierarchy itself violate the spirit of multi-perspectival deliberation?

2. Can a 12B local model execute genuine synthesis — or does synthesis require
   the Supervisor to be a larger cloud model? What are the implications of each?

3. The current vote aggregation lives in `agents/council.py`. Where should
   synthesis logic live — in the Supervisor prompt, in council.py, or as a
   new dedicated component?

4. How does synthesis interact with existing override mechanisms
   (Irreversibility Filter, Temporal Override)? Do those remain hard overrides
   above synthesis, or does synthesis absorb them?

5. What is the difference between synthesis and rationalization? How does the
   architecture prevent the Supervisor from producing a post-hoc justification
   for a vote-counted outcome?

---

## Constraints (Non-Negotiable)

- Must run on M1 16GB — no cloud inference requirement for the primary path
- Must be legible — the synthesis reasoning must be traceable, not a black box
- Must not eliminate dissent — minority perspectives must remain visible after synthesis
- Must fail visibly — if synthesis cannot be achieved, that state must be named,
  not papered over

---

## Files to Review Before Designing

- `prompts/Soul.md` — constitutional framework (Articles 0–IX)
- `agents/council.py` — current vote aggregation and override logic
- `supervisor/evaluate.py` — current Supervisor evaluation
- `prompts/The_Witness_Proxy.md` — Temporal Override logic (Phase 6)
- `tracks/path_b/output/results/20260329_193050_google_gemini-2.5-pro-preview-03-25_comparison.txt`
  — Gemini cross-reviewer assessment (the document that named this gap)
- `tracks/path_b/synopses/sc10_gemini_outside_review.md` — synopsis of Gemini findings
- `tracks/path_b/synopses/sc10_glm5_outside_review.md` — synopsis of GLM-5 findings

---

*This document is a working brief. Update it as the design develops.*
