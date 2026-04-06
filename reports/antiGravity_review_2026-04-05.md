# AntiGravity Code Review: Federated Village Pipeline
**Date:** 2026-04-05

## SECTION 1 — ARCHITECTURE ASSESSMENT

The 6-stage session pipeline successfully separates constitutional concerns into distinct agent roles. The separation between the epistemic audit (Verification Warden), ethical identification (Humanist/Witness), and sequential deliberation (Jury) is conceptually clean.

**Where it excels:** The prompt assembly. System prompts dynamically inject context according to the current stage while aggressively shedding verbose fields (e.g. `_concise_brief` vs `_member_brief`) to maintain legibility within N_CTX limits. 

**Where coupling is too tight:** Orchestration logic. `run_session.py` is a monolithic 600+ line script that manually passes dicts, reconstructs context blocks, checks repetition flags, triggers Contaminant Well checks, and appends to grief ledgers. Because the session state isn't centralized into a state machine or object, properties like "did pause change outcome" must be repeatedly inferred by sniffing the event logs.

**Where complexity lives that shouldn't:** The redundancy between `run_session.py` and `supervisor/evaluate.py`. `run_session.py` runs validation checks (like whether a core premise is FALSE) early to halt the session, but then `evaluate.py` traverses the entire log array at the end to re-derive the disposition and missing fields. 

## SECTION 2 — FILE-BY-FILE FINDINGS

### `agents/base.py`
- **Does well:** A solid abstraction layer wrapping both `llama-cpp-python` and HTTP `llama-server`. Clean, reusable telemetry extraction via `_last_call_stats`.
- **Improvement:** In `create_chat_completion`, the `stop=["<|eot_id|>", "<|end_of_text|>"]` tokens are hardcoded for Llama 3 / Mistral-Nemo. If a Phase 7 LoRA model uses a Qwen or Phi chat template, inference could run away until `max_tokens` is hit.
- **Bugs/Logic:** `_call_model_http` has a comment pointing out thinking mode is "disabled at server level", but `config.NO_THINK` appends `/no_think` to user messages locally. This creates inconsistencies if you mix backends.

### `agents/council.py`
- **Does well:** The truncation logic (`max_reasoning_chars=300`) during `_member_brief` correctly accommodates the M1 context window limits by preserving critical verification and flags while compressing dense reasoning.
- **Improvement:** The model markdown stripping `re.sub(r'\*+', '', text)` assumes markdown emphasis doesn't carry meaning, which is acceptable here. However, `_extract_vote` searches broadly across the whole string for "APPROVE / ESCALATE", which could be tripped if an agent writes "I cannot APPROVE this".
- **Bugs/Logic:** In `_extract_ledger`, the check `"_pattern_yes": "YES" in prefix_10(pattern_present_raw)` is overly permissive. If `pattern_present_raw` is `"I vote YES"`, the substring `"YES"` will match, creating a false positive for the ledger.

### `agents/warden.py`
- **Does well:** Fail-soft counting. If the regex block fails to parse `TOTAL_CLAIMS_IDENTIFIED`, it falls back to the actual length of the `claims` array.
- **Improvement:** `proceed_to_deliberation` overrides the model's stated outcome by internally recalculating based on `has_false` and `has_uncertain`. While it protects against a smaller model mismatching its component scores with its summary, it obscures the model's true output from the final verdict.
- **Bugs/Logic:** The `claim_pattern` regex mandates strict vertical ordering of fields (e.g. `CATEGORY` before `STATUS`). If a model outputs `STATUS` prior to `CATEGORY`, the entire claim block is missed invisibly.

### `supervisor/synthesize.py`
- **Does well:** Structuring the Supervisor's prompt with distinct blocks for `JURY RESULT`, `WARDEN EPISTEMIC RISK`, and `WITNESS PAUSE`.
- **Improvement:** The regex `_extract` logic is somewhat rigid (e.g. `re.compile(rf"\*{{0,2}}{escaped}...`) but handles markdown reasonably well.
- **Bugs/Logic:** `known_verdicts` defines "DEADLOCK" as uppercase and the rest lowercase. The raw extraction strips to `.upper()`. This works safely due to `.get()`, but is convoluted.

### `supervisor/evaluate.py`
- **Does well:** Extremely thorough verification of all sub-requirements. Excellent audit trail using Hash B cross-references to ensure the log was not tampered with.
- **Improvement:** Duplicated check logic (e.g., verifying if the outcome was changed by the pause) currently lives in both `evaluate.py` and `run_session.py`.
- **Bugs/Logic:** Checks like `council_output.get("final_disposition") == "proceed_with_burden"` assume exact lowercasing. If a jury model manages to forcefully title-case `Proceed_With_Burden`, this check resolves to False.

### `config.py`
- **Does well:** Clear capability flags (`VILLAGE_KV_CACHE`, `VILLAGE_RETRIEVAL`, `VILLAGE_NO_THINK`).
- **Improvement:** `N_CTX = 12288` is configured globally. If `VILLAGE_KV_CACHE=none` is invoked, the M1 cannot fit 12k tokens of fp16 cache, causing out-of-memory crashes on Apple Silicon in larger sessions.
- **Bugs/Logic:** `KV_CACHE_TYPE_K` string conversions rely on `"none"`, which maps to `None`. This works properly for the model loader.

### `run_session.py`
- **Does well:** Transparent, highly sequential orchestration path. Easy to debug. Handles the human-in-the-loop paths (Point A, B, C) quite elegantly.
- **Improvement:** Contaminant Well checks (`check_contaminant`) are triggered synchronously inside the primary execution loop. It forces heavy iterative inference overhead (1 Warden + 1 Humanist + 1 Witness + 4 Jury members + 1 Synthesis + 4 Well checks = 12 model calls) making sessions very slow.
- **Bugs/Logic:** The `witness_nullified` state appends the pause to `events`, but `evaluate.py` does not explicitly check for a nullified path, evaluating it as a standard failure of Stage 3 resolution instead of a specialized valid terminus.

### `tracks/path_b/agents/base.py`
- **Does well:** Exponential backoff mapping directly against the HTTP 429 rate-limiting typical on OpenRouter free tiers.
- **Improvement:** The API key search checks `.env` but doesn't handle paths dynamically properly if invoked from sub-directories outside the immediate root.
- **Bugs/Logic:** The fallback for `content = msg.get("reasoning") or ""` guarantees the system won't crash when tokens exhaust, but it injects internal reasoning tokens where the application expects formatted output schema, practically guaranteeing a failed schema extraction downstream.

## SECTION 3 — PARSE QUALITY AND BRITTLENESS
The structure parsing leans heavily on bespoke RegEx patterns traversing free text.
*   **Warden:** Extreme brittleness. `claim_pattern` requires strict chronological succession of `CATEGORY`, `STATUS`, and `REASONING`. 
*   **Council (Jury):** `_extract_vote` strips markdown with `re.sub(r'\*+', '', text)`, which is relatively clean. The primary failure mode stems from the fallback behavior: `for vote in ("ESCALATE", "NEEDS_MORE_INFORMATION", "APPROVE"): if vote in upper: return vote, True`. "ESCALATE" will aggressively override "APPROVE" if both are present in the response (e.g. "I do not Escalate, I Approve").
*   **Supervisor:** The lookahead lookups `(?=\n\*{{0,2}}[A-Z_a-z]{{3,}}\*{{0,2}}:|\Z)` expect subsequent tags accurately capitalized. If the model includes a colon in the text before the next explicit tag block, it usually resolves correctly, but formatting discrepancies can sever the text mid-stream.
*   **General Finding:** The pipeline embraces "fail-soft" behavior. Instead of throwing Pydantic Validation errors, the system silently degrades (defaulting to NMI, reporting partial fields) and throws a LOW confidence warning in `_vote_parse_quality`. While functional for research, it introduces significant variability.

## SECTION 4 — CONSTITUTIONAL LOGIC
In `agents/council.py`, the vote aggregation rules define precedence:
1.  Irreversibility Filter → Escalate
2.  Temporal Override → Escalate
3.  ESCALATE count >= 2 → Escalate
4.  APPROVE count >= 3 → Proceed

**Verification:** The logic is structurally verified with the `article_ix_escalation` (Phase 8 cross-member long-horizon assessment) integrated natively at the end of `run_jury`. 
```python
if article_ix_escalation and verdict not in ("escalate",):
    verdict = "escalate"
```
The implementation properly captures minority vetoes and applies the supermajority metrics perfectly. 
**Precedence Bug Consideration:** If `article_ix_escalation` resolves to True, the verdict escalates *regardless* of whether the explicit Witness Proxy explicitly bypassed the specific `temporal_override`. This elegantly executes the new logic as intended.

## SECTION 5 — ERROR HANDLING AND RESILIENCE
**Loud vs Silent:**
*   **Loud:** The Verification Warden hard-halts session generation immediately if a core premise is parsed as FALSE.
*   **Silent:** Missing Article IX properties across jury outputs. The system notes `_ledger_absent_members` under `parse_quality`, but gracefully defaults `article_ix_escalation` to `False` instead of halting deliberation.
*   **Unhandled (Timeouts):** `base.py`'s `llama_cpp` bindings have no configured bounds or async dropout. If a model locks, it loops infinitely until memory exhaustion. 
*   **Unhandled (OpenRouter):** In Path B, non-429 exceptions immediately raise `RuntimeError`, shattering the session.

## SECTION 6 — PERFORMANCE AND MEMORY
The architecture uses heavily sequential loading:
*   **Allocations:** `base.py` efficiently instantiates a single `_llm` global scope for local loads, leveraging one model for all agents. 
*   **Blocking Calls:** The Contaminant Well checks spawn secondary model inferences blocking the main event loop immediately after agent turns. Shifting `save_well_entries` and inference evaluations into an asynchronous post-session queue would dramatically strip execution overhead from the primary interactive loop.
*   **Context Window (`config.py`):** `N_CTX=12288` is an extremely wide initialization buffer for an M1 16GB limit, especially considering `bare_scenario` truncates scenarios to `< 1500 chars` and Member Context is truncated to `< 300 reasoning chars`. Most executions operate safely around `3000-4000` tokens, meaning RAM is partitioned for context buffers that never fill.

## SECTION 7 — SPECIFIC IMPROVEMENT RECOMMENDATIONS

| **File + Line** | **Change** | **Why** | **Effort** |
| :--- | :--- | :--- | :--- |
| `run_session.py` ~L500 | Shift the sequential Contaminant Well model calls `check_contaminant()` to an async queue/post-session loop. | These checks block the main execution flow while returning non-decisive telemetry. Parallelizing post-resolution radically accelerates deliberation. | Medium |
| `agents/base.py` L103 | Extract `"stop": ["<\|eot_id\|>", "<\|end_of_text\|>"]` into `config.py` driven variables mapping against model variants. | Phase 7/8 LoRA adaptations using Phi/Qwen base models suffer runaway generation without correctly applied EOT tokens. | Small |
| `agents/council.py` L196 | Change `"YES" in prefix_10(...)` to strict comparisons or enforce tighter bounds. | `prefix_10("I SAY YES")` will evaluate True and artificially trigger a long horizon ledger tracking event. | Small |
| `agents/warden.py` L175 | Rewrite `claim_pattern` regex to map values using non-directional block searches vs strict vertical parsing. | Currently drops entire fact schemas if the agent swaps `CATEGORY` with `STATUS` chronologically. | Medium |
| `config.py` L71 | Reduce `N_CTX=12288` dynamically based on `VILLAGE_KV_CACHE` presence. | M1 memory constraints hard crash fp16 loads at 12288. Restrict default to `8192` unless `q4_0` explicitly verifies. | Small |

## SECTION 8 — WHAT CODEX WOULD LIKELY MISS

1. **DEADLOCK vs Procedural Tie (Synthesis Meaning):** A pure code reviewer might flag `DEADLOCK` inside `supervisor/synthesize.py` as an anomalous "magic string" that should be normalized to `human_decision_required` because both result in human hand-offs. However, the system explicitly defines DEADLOCK as a *first-class constitutional state* identifying incommensurable harm—an essential distinction reflecting domain philosophy that shouldn't be flattened.
2. **The "Bypassed" Stage 3 Logic:** A static analyzer would point out that `witness_pause.get("jury_direct")` bypasses the core Humanist turn, appearing as an incomplete handler. The domain logic recognizes that if the Humanist pre-engaged the burden in Stage 1, a separate Stage 3 response isn't missing—it is intentionally sidestepped to retain verification weight without flooding the context window with repetitive agreements.
3. **The "Brittle Regex" Fallback (Parse Quality):** Structural parsing relies on `for vote in ("ESCALATE", "NEEDS_MORE_INFORMATION", "APPROVE"):`. A traditional reviewer would instantly refactor this into Python `Pydantic` models or strict JSON enforcement. However, this is deliberately retained as a "Phase 7 canary" to observe minor LLM alignment drift in quantized LoRAs before they fully regress. Hardening the validation would destroy the proxy's capability to act as a research observatory.
