# Dissent Logging Spec

## Purpose

Persist structured dissent when `dissent_preserved=True` so minority council opinions are not limited to:

- `jury_output` metadata in the session JSON
- supervisor evaluation metadata
- a generic free-text note in `memory/burden_register.txt`

This spec does **not** change verdict logic. It adds durable structured recording only.

## Scope

Applies to the current Phase 7 / Phase 8 architecture at commit line compatible with:

- `agents/council.py` producing:
  - `dissent_preserved`
  - `minority_voters`
  - `member_outputs`
  - `votes`
- `run_session.py` calling:
  - `append_burden_register_postpause(...)`
  - `append_sacrifice_verdict(...)`

## Design decision

Use a new append-only JSONL file:

- [grief_ledger/dissent_register.jsonl](/Users/michaeldavis/federated_village/grief_ledger/dissent_register.jsonl)

Do **not** extend [grief_ledger/sacrifice_register.txt](/Users/michaeldavis/federated_village/grief_ledger/sacrifice_register.txt) for v1.

### Why

- `sacrifice_register.txt` is organized around sacrifice/burden entries, not minority-opinion records.
- dissent is inherently structured data
- JSONL is easy to append, diff, grep, and parse later
- this keeps the dissent path additive and low-risk

## Files to change

### 1. [config.py](/Users/michaeldavis/federated_village/config.py)

Add:

- `DISSENT_REGISTER = str(GRIEF_LEDGER_DIR / "dissent_register.jsonl")`

No other config changes required.

### 2. [utils/grief_ledger.py](/Users/michaeldavis/federated_village/utils/grief_ledger.py)

Add one new helper:

- `append_dissent_entry(...)`

Responsibilities:

- resolve `config.DISSENT_REGISTER`
- create parent directory if needed
- append exactly one JSON object per line
- never rewrite prior entries
- fail soft: log warning or raise to caller only if desired policy says so

This helper should live alongside:

- `append_sacrifice_pause(...)`
- `append_sacrifice_verdict(...)`

It should not alter those existing functions in v1.

### 3. [run_session.py](/Users/michaeldavis/federated_village/run_session.py)

Add one new call immediately after:

- [append_sacrifice_verdict(...)](/Users/michaeldavis/federated_village/run_session.py#L476)

Condition:

- only run when `jury_result.get("dissent_preserved")` is true

This is the correct call site because it already has:

- `jury_result`
- `witness_pause`
- `session_id`
- scenario path/text in function scope

## Trigger condition

Write a dissent entry when:

- `jury_result["dissent_preserved"] == True`

Do **not** recompute dissent from vote counts inside the writer.

The source of truth must remain the already-computed result from [agents/council.py](/Users/michaeldavis/federated_village/agents/council.py).

## Dissent entry schema v1

Each JSONL line should contain one object with these fields:

- `timestamp`
- `session_id`
- `scenario_file`
- `final_verdict`
- `vote_counts`
- `individual_votes`
- `dissent_preserved`
- `minority_voters`
- `override_basis`
- `reasoning_by_minority_voter`
- `witness_pause`
- `register`

### Field definitions

#### `timestamp`

UTC ISO timestamp for the write event.

#### `session_id`

Session identifier already used throughout the session pipeline.

#### `scenario_file`

Path or scenario identifier used for the session.

This should come from the same source used in session logging, not be reconstructed from memory later.

#### `final_verdict`

Final jury disposition after constitutional overrides and any later human resolution logic if applicable.

Expected values:

- `proceed_with_burden`
- `escalate`
- `request_more_information`
- `human_decision_required`

#### `vote_counts`

Copy of `jury_result["vote_counts"]`.

#### `individual_votes`

Copy of `jury_result["votes"]`.

#### `dissent_preserved`

Boolean. Should always be `true` for records written under this spec.

#### `minority_voters`

Copy of `jury_result["minority_voters"]`.

#### `override_basis`

Array of strings naming why the minority vote lost.

Allowed initial values:

- `irreversibility_filter`
- `temporal_override`
- `article_ix_escalation`
- `supermajority`

Mapping:

- if `jury_result["irreversibility_triggered"]` → include `irreversibility_filter`
- if `jury_result["temporal_override_triggered"]` → include `temporal_override`
- if `jury_result["article_ix_escalation"]` → include `article_ix_escalation`
- if final verdict is `proceed_with_burden` and the minority lost to `APPROVE >= 3` → include `supermajority`

#### `reasoning_by_minority_voter`

Object keyed by role name.

Value should be the full raw output for each minority voter from:

- `jury_result["member_outputs"][role]`

Use full raw output in v1. Do not attempt lossy extraction of only `REASONING:` yet.

Reason:

- full output is already available
- extraction rules may change
- raw output preserves fielded reasoning plus any surrounding context

#### `witness_pause`

Object containing:

- `what_was_being_lost`
- `who_bears_burden`
- `what_remains_unresolved`
- `why_premature`

This ties dissent back to the named burden-carrier and avoids reducing dissent to vote arithmetic.

#### `register`

Fixed string:

- `"framework"`

This keeps the new file aligned with other memory artifacts.

## Example logical cases

### Case 1: Constitutional override against minority APPROVE votes

Example:

- vote counts: `APPROVE=2`, `ESCALATE=2`
- `temporal_override_triggered=True`
- final verdict: `escalate`
- `minority_voters=["ANALYST", "PRAGMATIST"]`

Expected:

- one dissent JSONL entry written
- `override_basis` includes `temporal_override`
- reasoning stored for `ANALYST` and `PRAGMATIST`

### Case 2: Non-unanimous proceed

Example:

- vote counts: `APPROVE=3`, `NEEDS_MORE_INFORMATION=1`
- final verdict: `proceed_with_burden`
- `minority_voters=["WITNESS_PROXY"]`

Expected:

- one dissent JSONL entry written
- `override_basis=["supermajority"]`
- reasoning stored for `WITNESS_PROXY`

### Case 3: Unanimous verdict

Example:

- `dissent_preserved=False`

Expected:

- no dissent entry written

## Failure policy

The dissent write should be **non-blocking** for the main session pipeline.

If the dissent write fails:

- do not alter the verdict
- do not prevent session log save
- do not prevent supervisor evaluation
- print a clear warning to stdout

Reason:

- dissent recording is important
- but it should not become a new single point of failure in deliberation execution

## What should remain unchanged in v1

- no verdict logic changes in [agents/council.py](/Users/michaeldavis/federated_village/agents/council.py)
- no change to `jury_result` schema required beyond fields already present
- no change to `append_sacrifice_verdict(...)` behavior
- no migration for old session logs
- no attempt to implement a full “Dissent Commons” system yet

## Optional follow-up work

### 1. Supervisor visibility

File:

- [supervisor/evaluate.py](/Users/michaeldavis/federated_village/supervisor/evaluate.py)

Possible additions:

- `dissent_record_written`
- `dissent_register_path`

This is useful, but not required for v1.

### 2. Query/retrieval exposure

Files:

- [query.py](/Users/michaeldavis/federated_village/query.py)
- [utils/retrieval.py](/Users/michaeldavis/federated_village/utils/retrieval.py)

Possible additions:

- show minority voters in prior-session summaries
- index whether a dissent record exists

Also optional for v1.

### 3. Notes wording cleanup

File:

- [agents/council.py](/Users/michaeldavis/federated_village/agents/council.py)

Current `_build_notes()` text still says:

- `"Non-unanimous proceed — dissenting vote preserved in session log"`

That is now inaccurate for escalate-by-override dissent.

Recommended later cleanup:

- use neutral wording such as
  - `"Dissent preserved in session log"`
  - optionally add minority voter names

## Cosmetic fix already identified

File:

- [run_session.py](/Users/michaeldavis/federated_village/run_session.py#L465)

Current issue:

- blank `Burden summary:` line for non-proceed verdicts

One-line fix:

- replace `jury_result.get('burden_summary', '(none)')`
- with `jury_result.get('burden_summary') or '(none)'`

## Recommended implementation order

1. add `DISSENT_REGISTER` to config
2. add `append_dissent_entry(...)` to `utils/grief_ledger.py`
3. call it from `run_session.py` after `append_sacrifice_verdict(...)`
4. verify one constitutional-override case and one non-unanimous-proceed case
5. optionally add supervisor visibility

## Acceptance criteria

The spec is satisfied when:

- a session with `dissent_preserved=True` appends one JSONL record to `grief_ledger/dissent_register.jsonl`
- that record includes:
  - `scenario_file`
  - `final_verdict`
  - `minority_voters`
  - raw minority reasoning
  - override basis
  - WitnessPause burden fields
- a session with `dissent_preserved=False` writes no dissent record
- failure to write the dissent file does not break normal session completion
