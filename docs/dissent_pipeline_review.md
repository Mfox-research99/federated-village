# Dissent Pipeline Review

## Scope

Read against:

- `docs/phase_7_hardening.md`
- `docs/phase_8_scope.md`
- `agents/council.py`
- `run_session.py`
- `utils/grief_ledger.py`
- `supervisor/evaluate.py`

Commit checked: `42378e7`

## 1. What `dissent_preserved=True` currently does

It does **not** currently trigger a dedicated grief-ledger dissent entry, a Dissent Commons write, or any other structured dissent storage.

What it does trigger today:

- It is stored in the `jury_result` event appended to the session log.
  - `agents/council.py:846-895`
  - `run_session.py:400-410`
- It is printed to stdout in the Stage 4 verdict block.
  - `run_session.py:464-471`
- It is copied into supervisor evaluation output and saved in the evaluation JSON.
  - `supervisor/evaluate.py:190-196`
  - `supervisor/evaluate.py:394-400`
  - `run_session.py:508-512`
- It is persisted **indirectly** into `memory/burden_register.txt` via the free-text `notes` string.
  - `run_session.py:169-205`
  - `agents/council.py:843-845`
  - `agents/council.py:946-971`

What it does **not** do:

- `utils/grief_ledger.py` never reads `dissent_preserved` or `minority_voters`.
  - `utils/grief_ledger.py:78-141`
- No file or function in this repo writes to a Dissent Commons store.
  - `rg` finds conceptual references in docs, but no implementation path.

## 2. Full path: detection -> storage

### Detection

`agents/council.py` now computes dissent **after** constitutional overrides, which is the right place if the goal is to preserve minority `APPROVE` votes that lost to a constitutional escalation.

- Constitutional override path:
  - Irreversibility / Temporal Override come from Witness-Proxy fields.
    - `agents/council.py:469-479`
  - Cross-member Article IX escalation is computed from ledger fields.
    - `agents/council.py:741-787`
  - Article IX can force `verdict = "escalate"` after the base vote aggregation.
    - `agents/council.py:789-797`
- Dissent preservation then runs on the **final** verdict.
  - `agents/council.py:799-825`

Specifically:

- If final verdict is `escalate` and any member voted `APPROVE`, then:
  - `dissent_preserved = True`
  - `minority_voters = [members who voted APPROVE]`
  - `agents/council.py:803-812`
- If final verdict is `proceed_with_burden` and vote is not unanimous, then:
  - `dissent_preserved = True`
  - `minority_voters = [members who voted non-APPROVE]`
  - `agents/council.py:813-822`

The resulting fields are written into `jury_result`.

- `agents/council.py:862-865`

### Session log persistence

`run_session.py` appends the full `jury_result` into `session_log["events"]`.

- `run_session.py:400-410`

That means the session JSON contains:

- `dissent_preserved`
- `minority_voters`
- `member_outputs`
- `votes`
- `notes`

This is the only place where dissent is preserved in a structured way today.

### Supervisor evaluation persistence

`supervisor/evaluate.py` reads `dissent_preserved` and `minority_voters` back out of the `jury_output` event.

- `supervisor/evaluate.py:190-196`

It then stores them in the evaluation dict.

- `supervisor/evaluate.py:394-400`

And `run_session.py` saves that evaluation JSON to disk.

- `run_session.py:508-512`

So the evaluation file is a second structured persistence path.

### Burden register persistence

`run_session.py` calls `append_burden_register_postpause(...)` after printing the verdict.

- `run_session.py:473`

That function writes only:

- response mode
- final disposition
- unresolved cost preserved
- a free-text `NOTES:` line

- `run_session.py:181-199`

Those notes come from `_build_notes(...)`.

- `agents/council.py:843-845`
- `agents/council.py:946-971`

Important limitation:

- `_build_notes()` records only the generic sentence `"Non-unanimous proceed — dissenting vote preserved in session log"`.
  - `agents/council.py:953-955`
- It does **not** include `minority_voters`.
- It does **not** include dissent reasoning.
- It uses the old wording even in the new escalate-by-override case, so the burden register note is now semantically stale for constitutional override dissent.

### Grief ledger persistence

`run_session.py` calls `append_sacrifice_verdict(...)`.

- `run_session.py:475-476`

That helper writes:

- `BURDEN-CARRIED` entries for `proceed_with_burden`
- `SACRIFICE-ID` entries for `escalate` / `human_decision_required`

- `utils/grief_ledger.py:96-136`

Important limitation:

- It never reads `dissent_preserved`.
- It never reads `minority_voters`.
- It never reads `member_outputs`.
- It never writes dissent-specific structure.

So there is a clear gap between **detection** and **grief-ledger recording**.

## 3. Gap assessment

### Bottom line

Yes, there is a gap.

The system now detects preserved dissent correctly and names the minority voters, but that dissent is only:

- structured in session JSON
- structured in evaluation JSON
- flattened into a generic note string in the burden register

It is **not** written into:

- `grief_ledger/sacrifice_register.txt` as a distinct dissent record
- any dedicated dissent log
- any implemented Dissent Commons store

### Why this matters

The code comment in `agents/council.py` says this minority opinion "belongs in the Dissent Commons, not silently discarded."

- `agents/council.py:799-802`

That intent is not implemented. Right now the minority opinion is not discarded completely, but it is not elevated into the project’s durable moral-memory systems either.

## 4. Minimal change to close the gap

### Recommendation

The smallest clean change is **not** to overload `sacrifice_register.txt`.

The smallest clean change is:

1. add a new dedicated append-only dissent log under `grief_ledger/`, ideally something like `grief_ledger/dissent_register.jsonl`
2. add one new helper in `utils/grief_ledger.py`
3. call it from `run_session.py` immediately after `append_sacrifice_verdict(...)` when `jury_result.get("dissent_preserved")` is true

### Why this is the minimal change

- `append_sacrifice_verdict(...)` currently has the wrong abstraction. It writes a text-format sacrifice/burden record and does not receive scenario metadata beyond `pause`, `jury_result`, and `session_id`.
  - `utils/grief_ledger.py:78-141`
- `run_session.py` is the place where all required context is already in scope or easy to reach:
  - `jury_result`
  - `witness_pause`
  - session log context
  - scenario path/text already loaded earlier in the session flow
- A dedicated JSONL dissent log avoids forcing dissent into the sacrifice register’s existing text schema.

### Minimal structured payload

The first version should write:

- `session_id`
- `timestamp`
- `scenario_file`
- `final_verdict`
- `vote_counts`
- `dissent_preserved`
- `minority_voters`
- `individual_votes`
- `reasoning_by_minority_voter`
- `override_basis`

Where:

- `reasoning_by_minority_voter` can be extracted from `jury_result["member_outputs"][role]`
- `override_basis` should be derived from:
  - `irreversibility_triggered`
  - `temporal_override_triggered`
  - `article_ix_escalation`

### If you want to keep it inside the grief ledger instead

The smallest ledger-native alternative is:

- keep `append_sacrifice_verdict(...)` unchanged for the main entry
- add a second helper in `utils/grief_ledger.py` that appends a sibling dissent record into a new file under `grief_ledger/`

That is still cleaner than expanding `sacrifice_register.txt`, because the current register is organized around sacrifice/burden semantics, not minority-opinion structure.

### What not to do

Do not rely on `notes` as the dissent store.

Reason:

- notes are free text
- notes currently omit `minority_voters`
- notes currently omit dissent reasoning
- notes currently use wording that no longer fits the escalate-by-override case

## 5. Cosmetic issue: blank `Burden summary:` line

### Where it lives

The print is in `run_session.py`.

- `run_session.py:464-466`

Current line:

- `print(f"  Burden summary:            {jury_result.get('burden_summary', '(none)')}", flush=True)`

Why it prints blank on `escalate`:

- `jury_result["burden_summary"]` exists and is set to `""` for non-proceed verdicts.
  - `agents/council.py:876-881`
- `.get('burden_summary', '(none)')` therefore returns `""`, not the fallback.

### One-line fix

Change the print expression to use truthiness rather than `.get(..., fallback)`, i.e.:

- print `jury_result.get("burden_summary") or "(none)"`

That is the one-line fix if you want to keep the line for all verdicts.

If you want the cleaner UX instead, print the burden summary only when `session_verdict == "proceed_with_burden"`.

## 6. Direct answers

### 1. Does `dissent_preserved=True` currently trigger downstream action?

Partially.

It triggers:

- session-log storage
- evaluation-json storage
- burden-register free-text recording
- console notes

It does **not** trigger:

- grief-ledger dissent recording
- Dissent Commons write
- any dedicated structured dissent store

### 2. Is there a gap between detection and recording?

Yes.

Detection is structured. Durable dissent recording is not.

### 3. Minimal change?

Add a dedicated append-only dissent log under `grief_ledger/` and write to it from `run_session.py` after `append_sacrifice_verdict(...)` whenever `dissent_preserved=True`.

### 4. Remaining cosmetic issue?

`run_session.py:465`

One-line fix:

- replace `jury_result.get('burden_summary', '(none)')`
- with `jury_result.get('burden_summary') or '(none)'`
