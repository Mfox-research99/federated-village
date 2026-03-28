# Codex Task A + C — Parallel Workstream

**Authored by:** Claude (architect)
**Date:** 2026-03-28
**Status:** Ready to execute — both tasks are independent of each other and of any live session work.

---

## Context

These two tasks run in parallel and neither blocks the other. Read the project's `AGENTS.md` and `memory/MEMORY.md` before starting either task. Do not edit any file not explicitly listed in the scope below.

---

## Task C — Seventh Shard AGENTS.md

### Goal

Write `/Users/michaeldavis/seventh_shard/AGENTS.md` — a Codex context brief for the companion repository, mirroring the purpose and structure of `federated_village/AGENTS.md`.

### Why it doesn't exist yet

The shard was built rapidly during Phase 7. The `AGENTS.md` pattern was established in federated_village but never ported. Without it, Codex cannot review the shard codebase with proper context.

### What to read first

Before writing, read these files in full:

- `/Users/michaeldavis/seventh_shard/README.md`
- `/Users/michaeldavis/seventh_shard/CHARTER.md`
- `/Users/michaeldavis/seventh_shard/LINEAGE.md`
- `/Users/michaeldavis/seventh_shard/config.py`
- `/Users/michaeldavis/seventh_shard/train_anubis_config.yaml`
- `/Users/michaeldavis/seventh_shard/dataset/` — list the files, read at least one training entry and one adversarial entry
- `/Users/michaeldavis/seventh_shard/dissents/` — list the files
- `/Users/michaeldavis/seventh_shard/utils/` — list and skim
- `/Users/michaeldavis/seventh_shard/test_anubis_suite.py` — skim for scenario structure
- The existing `federated_village/AGENTS.md` — use this as the structural template

### What AGENTS.md should contain

Mirror the federated_village AGENTS.md structure:

1. **What This Project Is** — the Grief Horizon Protocol, LoRA distillation goal, relationship to federated_village
2. **Current Phase / Status** — what's trained, what's pending (Qwen GGUF conversion, integration back into Village)
3. **Stack** — MLX on M1, base models used, adapter paths, training config
4. **Key Files table** — all significant files with one-line role descriptions
5. **Dataset schema** — training vs. adversarial, what a well-formed entry looks like
6. **Dissents directory** — what lives there and why
7. **Cross-Repo: federated_village** — what flows each direction (mirror the table in `federated_village/CLAUDE.md`)
8. **Operational Rules** — anything that would destroy a training run or corrupt adapters if done wrong
9. **What Codex Should Do Here** — same closing section as federated_village AGENTS.md, adapted for shard work

### Constraints

- Do not summarize or paraphrase CHARTER.md or LINEAGE.md — reference them, don't flatten them
- If you find something in the shard whose purpose is genuinely unclear, say so explicitly rather than guessing
- Keep the file under 120 lines — this is a context brief, not documentation

---

## Task A — Session Corpus Dissent Analysis

### Goal

Write `/Users/michaeldavis/federated_village/utils/dissent_analysis.py` — a standalone script that reads the full session corpus and produces a structured dissent pattern report.

### Why now

There are 90 session logs accumulated across Phases 1–8. Many predate the Phase 8 `dissent_preserved` field. A new `grief_ledger/dissent_register.jsonl` was added in this session and will accumulate going forward. The analysis script will give the architect real empirical data about which agents dissent, under which conditions, and in which scenario classes — before designing Phase 8 B (constitutional completeness enforcement).

### Input data

**Session logs:** `logs/session_*.json`
Each session log is a JSON file with this top-level structure:

```
session_id, started_at, scenario_file, scenario_text, model, events[], ended_at
```

The relevant event is the one with `"session_verdict"` in its keys (type may be `"jury_output"` or absent on older logs). Available fields (Phase 8 sessions):

```
type, session_id, timestamp, session_verdict, final_disposition,
votes, vote_counts, dissent_preserved, irreversibility_triggered,
temporal_override_triggered, member_outputs, burden_summary,
did_pause_change_outcome, unresolved_cost_preserved, notes,
parse_quality, constitutional_ledger, article_ix_escalation,
minority_voters
```

Older sessions (pre-Phase 6) may not have `temporal_override_triggered`, `article_ix_escalation`, `minority_voters`, or `parse_quality`. Handle missing fields gracefully.

**Dissent register:** `grief_ledger/dissent_register.jsonl`
New file, JSONL format. May be empty or have only a few entries when this script first runs. Each record:

```
timestamp, session_id, scenario_file, final_verdict, vote_counts,
individual_votes, dissent_preserved, minority_voters, override_basis[],
reasoning_by_minority_voter{role: raw_text}, witness_pause{fields},
register
```

### What the script should produce

Run with: `python utils/dissent_analysis.py`
Output: printed report to stdout. No file writes required (keep it simple).

The report should cover:

**1. Corpus overview**
- Total sessions processed
- Sessions that reached jury (had a verdict event)
- Sessions with `dissent_preserved=True`
- Sessions with `dissent_preserved=False` or field absent
- Breakdown by scenario file

**2. Verdict distribution**
- Count of each `session_verdict` across all sessions
- Count of each verdict by scenario

**3. Dissent patterns (sessions with `dissent_preserved=True`)**
- Which agent roles appear as minority voters, and how often
- Which `override_basis` values are present (from dissent_register, and inferred from session flags where dissent_register entry is absent)
- Co-occurrence: which agent pairs most often dissent together
- Verdict context: when dissent occurs, what was the final verdict?

**4. Constitutional filter history**
- How many sessions triggered `irreversibility_triggered`
- How many triggered `temporal_override_triggered` (Phase 6+)
- How many triggered `article_ix_escalation` (Phase 8+)
- How many triggered multiple filters simultaneously

**5. Dissent register summary** (if file exists and has entries)
- List each entry: session_id, scenario, minority_voters, override_basis
- Note which entries have reasoning captured vs. empty

**6. Gaps and anomalies**
- Sessions where `dissent_preserved=True` but `minority_voters` is absent or empty
- Sessions where constitutional filters fired but `dissent_preserved=False` (this would be unexpected — flag it)
- Any sessions with malformed or missing verdict events

### Script requirements

- Must run without any external dependencies beyond Python stdlib + json + glob + collections
- Must handle pre-Phase-6 logs that lack newer fields (use `.get()` with defaults throughout)
- Must not modify any log file or register
- Must be importable (put analysis logic under `if __name__ == "__main__":`)
- Section headers in output should be clearly delimited so the architect can read the report quickly

### Constraints

- Do not attempt to parse `reasoning_by_minority_voter` text — treat it as opaque for now
- Do not add any database, pandas, or visualization dependencies
- Do not write output to disk — stdout only for v1
- If `dissent_register.jsonl` doesn't exist yet, skip section 5 gracefully and note it

---

## Delivery

When both tasks are complete:

1. `seventh_shard/AGENTS.md` — written and ready for Mike's review
2. `utils/dissent_analysis.py` — written, runnable, output verified against the actual corpus

Do not commit either file. Leave them for Mike and the architect to review before committing.

If you find anything in the shard repo or the session logs that looks like a gap worth flagging (beyond the scope of these tasks), note it in a brief comment at the top of the relevant output file — but do not expand scope.
