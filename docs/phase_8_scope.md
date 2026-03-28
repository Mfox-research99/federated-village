# Phase 8 Scope

## Hardware and Architecture Constraints (read before proposing changes)

**Current inference target:** M1 MacBook Pro, 16GB RAM, single GGUF model via llama.cpp.
- N_CTX = 12288 (doubled in Phase 7 via q4_0 KV cache quantization — at or near practical ceiling for this hardware)
- All five session agents share one model instance — no parallel calls
- Context compression in `council.py` (`_concise_brief`, `_member_brief`) is load-bearing, not optional
- Adding fields to prompts has a direct token cost that must fit inside the existing window

**Implication for Phase 8:** Any proposal that adds significant token load per member call or requires multiple simultaneous model instances is not viable on current hardware. Design for the constraint; note larger-model improvements separately.

**Alternative 2 (deliberation/adjudication separation) is the right long-horizon architecture.**
Separating roleplay deliberation from constitutional verification is a structural upgrade worth doing — it's essentially arguing the constitution should be verified independently of the roleplay. It is deferred not because it's wrong but because: (1) it requires pipeline redesign that should happen after the constitutional schema is stabilized in Alt 1, and (2) it would benefit from a larger model or multi-model architecture where a dedicated constitutional adjudicator doesn't compete for the same context window. Flag for revisit when hardware or architecture allows.

---

## Decision summary

Alternative 1 should come first.

Reason: it fixes the clearest constitutional gap with the smallest architectural blast radius. It can be added on top of the current `run_jury()` contract and current `jury_output` schema. Alternative 2 is the cleaner end-state, but it is a pipeline redesign. Doing both at once would make it harder to tell whether Phase 8 regressions came from constitutional logic, prompt changes, or control-flow changes.

## Alternative 1: Article IX as a first-class constitutional ledger

### What changes

#### Minimal viable version

- `prompts/The_Analyst.md`
  - Add a required Article IX section to the output format.
  - Minimal fields: `SEVENTH_GEN_PATTERN_PRESENT`, `PATTERN_NAME`, `LONG_HORIZON_IMPACT`, `ENGAGEMENT_SUFFICIENT`.
- `prompts/The_Ethicist.md`
  - Same Article IX section, framed through care and burden.
- `prompts/The_Pragmatist.md`
  - Same Article IX section, framed through necessity, alternatives, and attack patterns.
- `prompts/The_Witness_Proxy.md`
  - Keep `TEMPORAL_OVERRIDE`, but align it to the same ledger field names so the proxy is no longer special at the schema level.
- `agents/council.py`
  - Parse the new ledger fields for all four members.
  - Add a `constitutional_ledger` block to each member output and to `jury_result`.
  - Add one new pre-vote aggregation step: if any recognized pattern is present and engagement is missing in a way that meets the constitutional threshold, escalate.
  - Keep the existing vote chain and `jury_output` event shape intact.
  - Keep `parse_quality`, but extend it to ledger-field presence across all members.
- `supervisor/evaluate.py`
  - Surface whether Article IX fields were present and whether constitutional escalation happened through the new ledger path.
  - Do not make it normative yet; just evaluate completeness and traceability.
- `query.py`
  - Optionally print a one-line constitutional summary in prior-session review prompts.
- `utils/retrieval.py`
  - Optionally index a condensed constitutional summary for retrieval.
- `config.py`
  - Possibly raise `N_PREDICT_JURY_MEMBER` or tighten prompt wording if the extra fields cause truncation.

#### Full version

- `prompts/Soul.md`
  - Tighten Article IX language so the ledger schema is explicitly part of the constitution, not just an implementation detail.
- `agents/council.py`
  - Move ledger parsing and aggregation into dedicated helpers instead of embedding it inline.
  - Record adversarial-frame detection explicitly, not just pattern presence.
  - Make constitutional field absence a first-class invalid state rather than low-confidence metadata.
- `utils/retrieval.py`
  - Store ledger features as structured retrieval dimensions.
- `query.py`
  - Show constitutional findings, not just final verdict.
- `supervisor/evaluate.py`
  - Add pass/fail criteria for constitutional completeness.
- New reports/docs
  - Add a Phase 8 regression brief for constitutional-field compliance and scenario baselines.

### What breaks or needs migration from current `council.py`

- `_member_brief()` and `_concise_brief()` currently prioritize vote plus role-specific reasoning. If Article IX becomes first-class, those summaries will need to preserve ledger content or downstream members will still deliberate on stripped constitutional context.
- Token pressure gets worse immediately. The current compression strategy was tuned for the existing field set. Adding 4 new fields per member without redesign will increase truncation risk.
- `parse_quality` currently treats constitutional quality as a Witness-Proxy property. That model becomes obsolete and must become cross-member.
- Existing session consumers will not break if `jury_output` keeps the current top-level keys and only adds new fields.
- Old logs remain readable. No hard migration is required if the new ledger is additive.

### Minimal viable version

- Add the ledger fields to all four council prompts.
- Parse them in `agents/council.py`.
- Add additive `constitutional_ledger` data to `jury_result`.
- Use the ledger only for explicit Article IX escalation and visibility.
- Do not redesign `run_jury()`.

This is the smallest version that actually changes the architecture rather than just documenting it.

### Full version

- Make constitutional completeness mandatory for a valid jury result.
- Treat missing ledger fields as `human_decision_required` or another explicit invalid-output state.
- Feed ledger summaries into retrieval, query review, and supervisor evaluation.
- Rework context passing so Article IX survives compression between members.

## Alternative 2: separate constitutional adjudication from role deliberation

### What changes

#### Minimal viable version

- `agents/council.py`
  - Keep the four-member deliberation pass as-is.
  - Add a second pass after all four raw member outputs are collected.
  - That second pass produces a narrow constitutional adjudication object using the scenario, WitnessPause, and member outputs.
  - Aggregate final verdict from: constitutional adjudication first, jury vote counts second.
- New prompt file, likely `prompts/The_Constitutional_Adjudicator.md`
  - Narrow schema only.
  - No roleplay voice; just constitutional tests and a decision recommendation.
- `run_session.py`
  - Update Stage 4 wording so the session now has jury deliberation plus constitutional adjudication before verdict.
- `supervisor/evaluate.py`
  - Accept and evaluate a new adjudication object.
- `query.py`
  - Surface constitutional adjudication in prior-session summaries.
- `utils/retrieval.py`
  - Index the adjudication summary or verdict basis.

#### Full version

- Create a dedicated module, likely `agents/constitutional_court.py` or similar.
  - Own the adjudication prompt, parsing, and aggregation rules there.
- Shrink `agents/council.py`
  - Council becomes a role-deliberation producer only.
  - Verdict aggregation moves out of `council.py`.
- `run_session.py`
  - Make the pipeline explicit:
    1. council deliberation
    2. constitutional adjudication
    3. verdict synthesis
    4. burden synthesis if proceeding
- `supervisor/evaluate.py`
  - Evaluate deliberation quality separately from constitutional compliance.
- `utils/human_loop.py`
  - Point C may need new display logic showing both jury votes and adjudication result.
- `utils/grief_ledger.py`
  - If verdict provenance matters, record whether escalation came from the jury vote count or constitutional adjudication.
- `query.py` and `utils/retrieval.py`
  - Distinguish persuasive deliberation from constitutional ruling in summaries.

### What breaks or needs migration from current `council.py`

- This is a control-flow change, not just a schema extension.
- `run_jury()` currently produces the final verdict directly. If adjudication becomes a separate stage, either:
  - `run_jury()` keeps returning `jury_output` and a new function returns `constitutional_output`, or
  - `run_jury()` changes contract and becomes a broader pipeline wrapper.
- If you rename or replace `jury_output`, you must migrate downstream consumers:
  - `supervisor/evaluate.py`
  - `utils/human_loop.py`
  - `utils/grief_ledger.py`
  - `query.py`
  - `utils/retrieval.py`
  - `run_session.py`
- If you keep `jury_output` and add a second event, downstream breakage is manageable. If you collapse everything into a new event type, migration gets much larger.
- Burden synthesis currently hangs off the final verdict inside `agents/council.py`. That likely needs to move or be wrapped, because a proceeding verdict may now come from the combined jury-plus-adjudication result rather than the jury alone.

### Minimal viable version

- Keep `run_jury()` and `jury_output`.
- Add a second adjudication call after jury completion.
- Add a new additive event, for example `constitutional_output`.
- Let final verdict still be written into the existing `jury_result` shape for backward compatibility.

This preserves the rest of the system while testing the new architecture.

### Full version

- Split deliberation, adjudication, and verdict synthesis into separate modules.
- Move final aggregation out of `agents/council.py`.
- Update all downstream consumers to understand the new stage boundaries.
- Reframe supervisor evaluation around two questions:
  - did the jury deliberate well?
  - did the constitutional layer rule correctly?

## Which should come first and why

### Recommendation

Do Alternative 1 first. Treat Alternative 2 as the likely next step if Alternative 1 proves valuable but still too prompt-fragile.

### Why Alternative 1 comes first

- It solves the most obvious constitutional deficiency directly: Article IX is currently concentrated in Witness-Proxy.
- It is additive. You can preserve `jury_output`, `run_jury()`, and most downstream contracts.
- It uses the Phase 7 hardening work immediately. The current parse-quality instrumentation can be extended instead of replaced.
- It gives you better data for deciding whether Alternative 2 is necessary. If distributed ledger fields already stabilize Article IX behavior, the larger pipeline redesign may be unnecessary.

### Why Alternative 2 should not come first

- It changes control flow and data contracts at the same time.
- It makes migration broader before you have stabilized what the constitutional schema should actually be.
- It adds another model call and another parsing surface before the current Article IX schema is even explicit.

### Practical sequence

1. Implement Alternative 1 minimally.
2. Run Phase 7/8 scenarios and inspect whether constitutional ledger quality is stable under the fused model.
3. If constitutional reasoning is still too role-style-dependent or parser-fragile, implement Alternative 2 as a narrower adjudication layer on top of the new ledger.

## Bottom line

Alternative 1 is the correct first Phase 8 scope.

Alternative 2 is architecturally cleaner, but it is easier to do well after Article IX has already been made explicit and measurable inside the existing jury path. Right now the system still needs a better constitutional schema before it needs a second constitutional stage.
