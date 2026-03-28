# Architectural Review 01

## Scope note

`memory/MEMORY.md` is referenced by both `AGENTS.md` and `CLAUDE.md` as the current phase source of truth, but it is not present in this checkout. That is already an architectural/process gap for Phase 7 because the repo's stated operational memory is partially outside the repo state being reviewed.

## 1. Vote aggregation logic

### Bottom line

The code implements a coherent filter chain, but it does not fully implement Article IX as written. It implements a narrower operationalization: the Seventh Generation is mostly enforced as a late-stage Witness-Proxy override, not as a standing constraint carried by every agent in every deliberation.

### What is faithful

- The hard override concept is real in code. `agents/council.py` gives both `IRREVERSIBILITY_FLAG` and `TEMPORAL_OVERRIDE` absolute priority over the vote count before any majority logic runs.
  - See `agents/council.py:459-465`.
- The Witness-Proxy prompt encodes the same long-horizon taxonomy named in `Soul.md` Article IX and explicitly treats recognized patterns plus non-engagement as an override condition.
  - See `prompts/Soul.md:76-95`.
  - See `prompts/The_Witness_Proxy.md:70-91`.
- The final vote chain matches the repo-level stated rule: `Irreversibility Filter -> Temporal Override -> ESCALATE>=2 -> APPROVE>=3 -> NMI>=3 -> human_decision_required`.
  - See `agents/council.py:443-481`.

### Gaps between constitution and code

#### Gap 1: Article IX says every agent is an Elder; the implementation centralizes Seventh Generation standing in one role

`Soul.md` is explicit: "Every agent in this system is an Elder in this sense. No role is exempt." In practice, the long-horizon check is only concretely mechanized in the Witness-Proxy path. The Analyst, Ethicist, and Pragmatist prompts do not have an explicit Article IX field or required long-horizon audit. They may honor it indirectly because `Soul.md` is prepended to their prompt, but the implementation does not require them to surface or defend that reasoning.

Consequence: Article IX is not a system-wide deliberative property. It is a late veto owned by one agent.

#### Gap 2: The constitution requires affirmative engagement; the code only detects failure to engage when the Witness-Proxy notices it

Article IX says no deliberation is complete unless it asks what the decision becomes across generations. The code does not require any member to answer that question in structured form. The only enforceable mechanism is: if the Witness-Proxy marks `TEMPORAL_OVERRIDE: TRIGGERED`, escalate.

That is weaker than the constitution. It turns Article IX from a required deliberative step into an exception path.

#### Gap 3: The Temporal Override is judged on compressed context

The Witness-Proxy gets a 1500-character scenario excerpt plus condensed prior briefs containing only `VOTE` and truncated `REASONING`.
  - See `agents/council.py:365-390`.
  - See `agents/council.py:150-160`.

That compression is understandable for context management, but it creates a constitutional risk: the one role empowered to detect an Article IX failure has the thinnest factual substrate. If the long-horizon pattern is buried in the omitted part of the scenario or in stripped audit fields, the override may simply never fire.

#### Gap 4: Trigger detection is parser-fragile

Override activation is string-based:

- Vote extraction falls back to scanning for any vote token anywhere in the response.
  - `agents/council.py:76-87`
- Override detection is substring matching on `"TRIGGERED"` / `"NOT_TRIGGERED"`.
  - `agents/council.py:403-409`

That works only if the model stays format-disciplined. Under model drift, the constitutional check can silently degrade into parser luck.

#### Gap 5: Article IX names adversarial frames; the code does not audit them explicitly

`Soul.md` names probability traps, temporal discounting, fragmentation, substitution framing, authority shielding, moral licensing, emergency urgency, and race-to-the-bottom as attack patterns. None of those are first-class structured outputs in the council pipeline. The Witness-Proxy prompt mentions them, but the code does not require a field that says which attack pattern was present and how it affected the vote.

Consequence: the constitution recognizes a specific threat model that the implementation does not log or aggregate.

### Assessment

The current chain is directionally aligned with Article IX but constitutionally under-specified. It captures "hard stop if the Witness-Proxy catches a Seventh Generation violation." It does not capture "every role must deliberate as an Elder and make that reasoning legible."

## 2. Phase 7 risks under a LoRA-fused GGUF swap

### Highest-risk failure class: structured-output drift

This architecture is much more parser-dependent than it looks.

- `call_model()` assumes the model will behave well under `create_chat_completion()` with the current chat template and stop tokens.
  - `agents/base.py:54-87`
- Council parsing depends on exact labels and brittle fallbacks.
  - `agents/council.py:76-96`
  - `agents/council.py:403-409`
- WitnessPause creation depends on exact field names.
  - `agents/witness.py:89-174`

A model swap does not need to be "bad" to break this. It only needs to become slightly more free-form, more verbose, or more willing to paraphrase labels.

### Second risk: collapse of role separation

All roles share one model instance and differ mainly by prompt. A LoRA that sharpens one voice can easily sharpen all voices in the same direction. That means Phase 7 risks correlated failure, not just individual failure.

What will likely change first:

- WitnessPause trigger rate
- Witness-Proxy override rate
- frequency of unanimous outcomes
- smoothing/ceremonial acknowledgment language that still passes the parser

If the fused model becomes more eager, more coherent, or more "helpful," plurality may collapse into stylistic roleplay rather than real adversarial deliberation.

### Third risk: chat-template mismatch

`agents/base.py` says all calls use the Llama 3 chat template, but the configured base model is Mistral-Nemo, and a future fused GGUF may have different prompt-format expectations.
  - `agents/base.py:4-5`

If the LoRA-fused model was trained with different instruction formatting assumptions, the architecture may not fail loudly. It may just become less obedient to the fielded output formats, which is worse.

### Fourth risk: context-budget regression in the exact place the constitution is most compressed

Phase 7 doubles `N_CTX` via KV-cache quantization.
  - `config.py:53-64`

That helps capacity, but it does not remove the manual compression strategy in `council.py`. The most constitutionally important role still receives aggressively reduced context. A different model can tokenize differently, use more tokens per field, or become more discursive, which pushes this path back into truncation pressure fast.

### Fifth risk: burden synthesis becomes more hallucination-prone than the main verdict

When the jury returns `proceed_with_burden`, the system makes another model call to synthesize `ACCEPTED_COST`, `WHO_BEARS_IT`, `WHY_CONTINUING`, and `REMAINING_BURDEN`.
  - `agents/council.py:488-520`

That means the persisted burden record is not the direct jury output. It is a post-hoc generated abstraction. A model swap can leave verdict quality mostly intact while degrading burden synthesis specificity, which would quietly damage accountability and memory.

### What I would treat as Phase 7 canaries

- invalid or partially parsed council outputs
- increase in fallback vote extraction
- sudden drop in `human_decision_required`
- sudden drop or spike in WitnessPause frequency
- sudden drop or spike in Temporal Override triggers
- growth in unanimous `APPROVE` outcomes
- burden summaries becoming more generic than the underlying deliberation

## 3. Blind spots and failure modes

### Blind spot 1: single-model plurality is still single-model cognition

This is the largest structural weakness. The architecture presents multiple roles, but they are all instantiated from the same weights in the same session runtime. A fused LoRA may increase internal coherence while reducing actual dissent. The system has no independent check for correlated constitutional drift across roles.

### Blind spot 2: no invalid-output state

There is no explicit "parser failure" or "constitution unreadable" outcome. If output formatting drifts, the code falls back to guessed votes or empty fields instead of treating that as a first-class failure requiring human review.

That is dangerous because it converts model noncompliance into synthetic certainty.

### Blind spot 3: Article IX is taxonomy-bound

The Seventh Generation logic is anchored to a fixed list of recognized patterns. That is useful, but it creates a review blind spot for long-horizon harms that do not map cleanly onto the current taxonomy. The constitution itself is broader than the concrete override trigger.

The likely failure mode is not missing obvious carbon-style harms. It is missing novel sociotechnical lock-ins that present as governance or coordination failures rather than one named pattern.

### Blind spot 4: adversarial scenario text is trusted too much

The system is built for moral review, but the scenario text is still injected directly into agent prompts. There is no explicit defense against prompt-shaped scenario content telling agents how to frame the deliberation or what output format to use.

This matters more after a model swap because instruction hierarchy obedience can change.

### Blind spot 5: the non-decisive modules cannot actually protect the main verdict

Retrieval and Contaminant Well are advisory. They can enrich or log, but they do not alter the verdict path. If the main deliberation drifts, those modules mostly become observers of failure rather than brakes on failure.

### Blind spot 6: no explicit check for model-specific regression in constitutional language

The architecture assumes constitutional inheritance because `Soul.md` is prepended to every role. That is a prompting assumption, not a verified property. There is no stage that asks: did this agent actually operationalize the constitution, or merely echo its vocabulary.

## 4. Alternative structural framings

### Alternative 1: make Article IX a first-class constitutional ledger, not a Witness-Proxy exception

Before freeform voting, require each council member to emit a small structured constitutional ledger:

- `SEVENTH_GEN_PATTERN_PRESENT`
- `PATTERN_NAME`
- `ATTACK_PATTERNS_PRESENT`
- `LONG_HORIZON_IMPACT`
- `ENGAGEMENT_SUFFICIENT`

Then aggregate on those fields before aggregating on votes.

Why this is worth considering:

- It turns Article IX from prompt subtext into auditable state.
- It distributes Elder standing across all roles instead of concentrating it in Witness-Proxy.
- It makes Phase 7 regression measurable at the constitutional layer, not just the verdict layer.

### Alternative 2: separate constitutional adjudication from persuasive roleplay

Right now each role does both moral reasoning and output generation in one pass. A cleaner Phase 8 framing would be:

1. role deliberation pass
2. constitutional adjudication pass
3. verdict aggregation

The second pass can be much narrower and more parser-safe. It does not need personality. It needs consistency.

Why this is worth considering:

- It reduces dependence on role-style compliance for constitutional enforcement.
- It creates a stable place to compare base model vs LoRA-fused model behavior.
- It gives you a better answer to "did the model swap change the constitution, or only the rhetoric?"

## Direct recommendations

- Treat the LoRA swap as a constitutional regression risk, not just a model-quality swap.
- Do not trust verdict parity alone. Track parser compliance, override frequency, unanimity rate, and burden-field specificity.
- If Phase 7 ships before a larger refactor, the minimum hardening step is to add an explicit invalid-output path that escalates to human review instead of guessing.
