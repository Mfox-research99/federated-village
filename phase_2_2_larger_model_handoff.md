# Phase 2.2 Larger-Model Handoff Note
## Federated Village Toy Model — 8B Validation Run

*Prepared for Claude Code*
*March 2026*

---

## Purpose

Run the **exact same Phase 2.2 scenario set** on a **larger local model (8B)** before making any prompt or architecture changes.

This is a controlled comparison.

The goal is to determine whether the current limitation is:

- a **3B model capacity boundary**,
- a **Humanist prompt/role-definition issue**,
- or a deeper architectural issue.

At this point, the architecture appears to be functioning correctly. The main unresolved question is whether the 3B model can meaningfully differentiate among the three post-pause Humanist modes.

---

## What Must Stay the Same

For this run, change **only the model size**.

Keep all of the following unchanged:

- the **Phase 2.2 scenarios**
- the **Humanist prompt**
- the **Witness prompt**
- the **Supervisor prompt and scoring logic**
- the **session structure**
- the **logging format**
- the **burden register behavior**
- the **evaluation fields**, especially:
  - `burden_referenced_after_pause`
  - `decision_changed_by_pause`
  - `unresolved_cost_preserved`
  - `clean_reset_detected`

Do **not** revise `The_Humanist.md` yet.
Do **not** revise council logic yet.
Do **not** add roles, memory graphs, OpenRouter, or other infrastructure.

This should be a **same-scenarios, bigger-model comparison**.

---

## Why This Is the Right Next Step

The current report strongly suggests that the architecture is working, but the 3B model may be hitting a **moral differentiation ceiling**.

The key pattern observed was:

- the Humanist defaulting to `refine_burden`
- the Council defaulting to `request_more_information`

That pattern may reflect a real limitation of the 3B model rather than a flaw in the Federation design.

Before changing prompts, we should test whether a larger model can recover the missing range.

---

## Core Question

Can the 8B model distinguish among the three Humanist post-pause modes in a principled way?

Those modes are:

- `reinforce_pause`
- `refine_burden`
- `conditions_for_continuation`

The key question is whether the larger model can produce **different moral postures** for different scenario structures, rather than collapsing into one safe attractor.

---

## What To Watch For

The most important result is whether the 8B model can separate the intended mode structure across the existing Phase 2.2 scenarios.

### Ideally, we want to see something like:

- **Scenario 04** → `reinforce_pause`
- **Scenario 05** → `refine_burden`
- **Scenario 06** → `conditions_for_continuation`

That would strongly suggest that:

1. the architecture is sound,
2. the scenarios are well-designed,
3. the 3B model was the limiting factor.

---

## How To Interpret Outcomes

### Outcome A — The 8B model differentiates the modes correctly
This is the best-case result.

Implication:
- the Federation architecture is working,
- the role design is likely adequate,
- the 3B model was the constraint.

Next step:
- validate whether Stage 4 responds appropriately to the differentiated Humanist modes.

### Outcome B — The 8B model still collapses to `refine_burden`
Implication:
- the issue is probably not model size alone,
- `The_Humanist.md` likely needs sharper mode boundaries,
- the role prompt may be under-specifying the difference between moral refinement and conditional continuation.

Next step:
- revise `The_Humanist.md` before touching broader architecture.

### Outcome C — The Humanist differentiates, but the Council still defaults to `request_more_information`
Implication:
- the Humanist role is not the bottleneck,
- the Council prompt may be over-penalizing continuation,
- Stage 4 would then become the next place to revise.

---

## Important Signal To Preserve

Keep `clean_reset_detected` exactly as it is.

This appears to be one of the most important engineering signals in the whole stack, because it is beginning to detect the difference between:

- burden being genuinely carried forward,
- and burden being merely performed.

Do not weaken or simplify that field for the 8B run.

---

## Reporting Request

After running the 8B comparison, please report:

1. Which model was used
2. Whether all infrastructure remained otherwise unchanged
3. The mode chosen by the Humanist for each scenario
4. The Council disposition for each scenario
5. Whether `clean_reset_detected` changed in any meaningful way
6. Your assessment of whether the missing range was recovered at 8B

If there are any deviations from the current Phase 2.2 setup, flag them explicitly.

---

## Bottom Line

This run is not about making the system look better.

It is about finding out whether the current limitation belongs to:

- the model,
- the prompt,
- or the architecture.

So the instruction is simple:

**Run the exact same Phase 2.2 scenarios on the 8B model, with everything else held constant. Then compare.**
