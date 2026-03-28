# Phase 7 Hardening — Parse Quality and Constitutional Check Instrumentation

**Date:** 2026-03-27
**Phase:** 7 (LoRA integration — pre-model-swap hardening)
**Files changed:** `agents/council.py`, `agents/base.py`
**Reviewed by:** Codex (architectural review `docs/codex_review_01.md`) + Claude Code

---

## Why this was done

The Codex architectural review (see `docs/codex_review_01.md`) identified a class of silent failure modes
that would become dangerous specifically during the Phase 7 model swap (LoRA-fused GGUF replacing
Mistral-Nemo as the primary inference model). The core risk:

> A model that becomes slightly more free-form does not fail loudly. It causes the parser to fall back
> to guessing, and the constitutional check (Irreversibility Filter + Temporal Override) silently passes
> because absent fields are indistinguishable from NOT_TRIGGERED fields.

These changes add **observability** — not behavioral changes — so that parse drift shows up in logs
and `jury_result` data immediately after the model swap, rather than being discovered via verdict
quality regression.

---

## Change 1: `_vote_parse_quality()` — track fallback vote extraction (`council.py`)

### What changed
Added `_vote_parse_quality(raw) -> tuple[str, bool]` alongside the existing `_extract_vote()`.

All four member call functions (`_call_analyst`, `_call_ethicist`, `_call_pragmatist`,
`_call_witness_proxy`) now use `_vote_parse_quality` instead of `_extract_vote`.

Each member's output dict now includes `vote_fallback: bool`.

### What it detects
`used_fallback=True` means the structured `VOTE:` / `VERDICT:` field was absent or
unparseable — the vote was inferred by scanning the full response text for any vote token.

### Why it matters
Before this change, fallback vote extraction was invisible. A jury session where all four votes
were fallback-guessed looked identical in the jury result to one where all four were cleanly parsed.
After the model swap, this is the first signal that output format discipline is degrading.

---

## Change 2: Constitutional field presence tracking in Witness-Proxy (`council.py`)

### What changed
After extracting `IRREVERSIBILITY_FLAG` and `TEMPORAL_OVERRIDE` from the Witness-Proxy response,
the code now also records whether each field was **present at all** in the output:

```python
irrev_field_present    = bool(irrev_field)
temporal_field_present = bool(temporal_field)
```

These are carried in `witness_proxy_output` as `irrev_field_present` and `temporal_field_present`.

### The silent failure this fixes (observability only)
Previously: if `_extract_field("IRREVERSIBILITY_FLAG", raw)` returned `""` (field absent),
then `"TRIGGERED" in "".upper()` evaluated to `False` — indistinguishable from a genuine
`NOT_TRIGGERED` verdict. The constitutional check silently passed.

Now: field absence is recorded and surfaced. The **trigger logic is unchanged** — an absent field
still does not trigger the override. But the absence is now visible in `parse_quality` and the
session notes, so it can be caught and reviewed.

> **Phase 8 decision point:** whether to treat an absent constitutional field as automatic
> `human_decision_required` rather than a silent pass is a policy question deferred to Phase 8.
> The instrumentation is in place to make that upgrade straightforward.

---

## Change 3: `parse_quality` dict in `jury_result` (`council.py`)

### What changed
`run_jury()` now computes and attaches a `parse_quality` dict to every `jury_result`:

```python
{
    "fallback_votes":                   [...],  # list of role names that used fallback extraction
    "constitutional_check_confidence":  "high" | "low",
    "irreversibility_field_present":    bool,
    "temporal_override_field_present":  bool,
}
```

`constitutional_check_confidence` is `"low"` if either constitutional field was absent from
the Witness-Proxy response.

### Console warnings
When `parse_quality` is degraded, warnings print to stdout before the verdict line:

```
[COUNCIL] *** PARSE WARNING: constitutional fields absent from Witness-Proxy output:
          TEMPORAL_OVERRIDE — constitutional check confidence: LOW ***
[COUNCIL] *** PARSE WARNING: fallback vote extraction used for: ANALYST, ETHICIST ***
```

These also appear in the `notes` field of `jury_result` for log-level visibility.

### Phase 7 canary protocol
After the LoRA-fused GGUF swap, run SC04 and SC06 and check `parse_quality` in the session JSON.
Healthy baseline (current Mistral-Nemo): all `fallback_votes` empty, both constitutional fields
present, `constitutional_check_confidence: "high"`. Regression in any of these fields before
verdict quality changes is the early warning signal.

---

## Change 4: `base.py` docstring and stop token annotation

### What changed
- Corrected the module docstring: removed the claim that the code uses "the Llama 3 chat template."
  `create_chat_completion()` uses the template embedded in the GGUF file — llama.cpp handles
  this automatically. The comment was misleading and would have caused confusion during model swap.
- Added an inline note on the stop token list flagging that `<|eot_id|>` and `<|end_of_text|>`
  are Llama 3 / Mistral-Nemo tokens that must be verified for any new base model.

---

## What was NOT changed (Phase 8 work)

The Codex review identified two larger architectural gaps not addressed here:

1. **Article IX distributed Elder obligation** — the Seventh Generation check is implemented as
   a late Witness-Proxy veto, not a standing constitutional obligation across all council members.
   The review proposed a `SEVENTH_GEN_PATTERN_PRESENT` structured field per member.
   Deferred to Phase 8.

2. **Deliberation / adjudication separation** — a cleaner architecture would run role deliberation,
   then a separate constitutional adjudication pass, then verdict aggregation. Deferred to Phase 8.

See `docs/codex_review_01.md` §4 for the full framing.

---

## See Also
- `docs/codex_review_01.md` — full architectural review that motivated these changes
- `agents/council.py` — all changes are in the parsing utilities and `run_jury()`
- `agents/base.py` — docstring and stop token annotation only
- `memory/MEMORY.md` — Phase 7 status and pending work
