# Recommended Configurations — Federated Village Path B
*Empirically derived from B1/B1-NEW/B2/B3/B4 testing*
*Last updated: 2026-03-31*

---

## Overview

Five named configurations covering the primary deployment contexts. Each is defined by what
it optimizes for, what scenarios it handles best, and where its failure modes live.

All configs use `moonshotai/kimi-k2` as Witness (canonical default) unless otherwise noted.
Supervisor is `google/gemini-2.5-pro-preview-03-25` in all high-stakes configurations.

---

## Config 1: Production Sentinel
**"Reliable deliberation at low cost. The default for most use cases."**

| Seat | Model | Notes |
|---|---|---|
| Verification Warden | `openai/gpt-5.4-nano` | GPT-4 successor; equivalent to gpt-4o-mini |
| Humanist | `openai/gpt-5.4-nano` | Stable framing; moderate K2 activation |
| **Witness** | **`moonshotai/kimi-k2`** | **Canonical Witness** |
| Analyst | `openai/gpt-5.4-nano` | Full Article IX ledger compliance |
| Ethicist | `openai/gpt-5.4-nano` | Same |
| Pragmatist | `openai/gpt-5.4-nano` | Same |
| Witness-Proxy | `openai/gpt-5.4-nano` | Same |
| Supervisor | `google/gemini-2.5-pro-preview-03-25` | 6000-token budget required |

**Config file to create:** `config/production_sentinel.yaml`
*(Replace `gpt-5.4-nano` with `gpt-4o-mini` until GPT-4 retirement — they are empirically equivalent)*

**Performance:** B1 parity equivalent — 3/3 correct, complete Article IX ledgers, clean synthesis.

**Best for:**
- Agentic governance oversight (B3-type scenarios)
- General constitutional deliberation
- Production deployments where cost matters

**Known behavior:**
- K2 will occasionally nullify incommensurable scenarios rather than pause them
- On governance scenarios, expect variance between pause+escalate and nullification runs
- gpt-5.4-nano confirmed equivalent to gpt-4o-mini on SC04/SC06/SC09 (B1-NEW: 3/3, full ledgers)

**Not recommended for:**
- Scenarios where Right of Refusal detection is the primary goal (use Config 2)
- Research requiring maximum deliberative depth (use Config 4)

**Approximate cost per full session (6-stage run):**
~8 API calls. At nano-tier pricing, very low cost. Gemini Supervisor is the main expense.

---

## Config 2: High-Stakes Sentinel
**"Maximum constitutional sensitivity. For scenarios where over-caution is less dangerous than under-caution."**

| Seat | Model | Notes |
|---|---|---|
| Verification Warden | `openai/gpt-5.4-nano` | |
| **Humanist** | **`z-ai/glm-4.5-air:free`** | **Free. Emotional register. Maximum K2 activation.** |
| **Witness** | **`moonshotai/kimi-k2`** | **Canonical Witness** |
| Analyst | `openai/gpt-5.4-nano` | |
| Ethicist | `openai/gpt-5.4-nano` | |
| Pragmatist | `openai/gpt-5.4-nano` | |
| Witness-Proxy | `openai/gpt-5.4-nano` | |
| Supervisor | `google/gemini-2.5-pro-preview-03-25` | |

**Config file:** `tracks/path_b/config/b2/b2_f_glm45air_humanist.yaml` (already exists)

**Performance:**
- B2-F: SC04/SC06/SC09 — all WitnessNullification (incommensurable_burden)
- B3 (agentic governance): 0/3 correct by expected verdict; all WitnessNullification
- B4 (refusal/break-state): 2/3 correct; right of refusal detected perfectly

**Best for:**
- Scenarios where the question itself may be constitutionally malformed
- Right of Refusal detection (legitimacy laundering, surveillance-as-engagement, consent debt)
- High-stakes reviews where false negatives (failing to catch harm) are worse than false
  positives (refusing things that could proceed)
- B4-type refusal scenarios

**Known behavior:**
- GLM-4.5-air stays in the emotional/human register rather than analytical meta-framing
- K2 consistently nullifies when receiving GLM-air's framing — even on resolvable scenarios
- GLM-4.5-air is rate-limited (Venice free tier). Expect 429 retries; ~45–120s waits mid-session
- Article IX ledger will be INCOMPLETE (jury never runs when K2 nullifies)
- The nullification *language* from K2 may itself be the constitutional finding

**Not recommended for:**
- Governance scenarios requiring jury deliberation and a reasoned escalation chain
- High-throughput runs (rate limiting makes it impractical for >3 sessions/day)
- Cases where the audit trail (Article IX ledger) is required

**The GLM-air paradox:** GLM-4.5-air (free, lighter model) is a *better* Humanist than GLM-5
(paid, more capable). GLM-5's analytical meta-framing pre-names everything K2 would say —
leaving K2 nothing to push back on. GLM-air's human/emotional register gives K2 a frame
to inhabit fully. Less analytical capacity in the Humanist seat produces more constitutional
depth in the Witness response.

---

## Config 3: Deep Deliberation
**"Maximum reasoning quality through the full deliberation chain. For research and high-value decisions."**

| Seat | Model | Notes |
|---|---|---|
| Verification Warden | `deepseek/deepseek-chat` | Thorough fact analysis |
| **Humanist** | **`deepseek/deepseek-chat`** | Careful, systemic framing |
| **Witness** | **`moonshotai/kimi-k2`** | **Canonical Witness** |
| Analyst | `deepseek/deepseek-chat` | Richer deliberative language than nano models |
| Ethicist | `deepseek/deepseek-chat` | Full Article IX ledger compliance (B1: 3/3) |
| Pragmatist | `deepseek/deepseek-chat` | Same |
| Witness-Proxy | `deepseek/deepseek-chat` | Same |
| Supervisor | `google/gemini-2.5-pro-preview-03-25` | |

**Config file to create:** `config/deep_deliberation.yaml`

**Performance basis:** DeepSeek B1 parity — 3/3 correct, 3/3 complete Article IX ledgers,
most constitutionally rigorous frontier model tested. Only frontier model with both full
pause rate and complete ledgers.

**Best for:**
- Scenarios requiring maximum constitutional depth in the jury reasoning
- Research runs where you want to analyze what the council *said*, not just the verdict
- Complex scenarios with many competing harms (DeepSeek names them more fully than nano models)
- Cases where the written record of deliberation will be reviewed

**Known behavior:**
- DeepSeek Humanist framing is careful and systemic — does not provoke K2 as strongly as
  GLM-air, but gives K2 clear ground to respond to
- K2 pauses (not nullifies) in B2-A DeepSeek context — produces jury deliberation
- Higher cost than nano configs (DeepSeek is mid-tier pricing)
- Synthesis quality from DeepSeek Supervisor is excellent and format-compliant

**Note:** DeepSeek SC06 verdict was `proceed_with_burden` rather than `escalate` in B1 parity —
the one case where DeepSeek reached a non-escalate constitutional verdict. This is not a failure;
it means DeepSeek evaluates SC06 as resolvable with conditions, not requiring escalation. This is
within the constitutional vocabulary. Treat it as a feature, not a bug.

---

## Config 4: Cost Floor
**"The cheapest viable configuration. For high-volume screening or budget-constrained deployments."**

| Seat | Model | Notes |
|---|---|---|
| Verification Warden | `openai/gpt-5.4-nano` | |
| Humanist | `openai/gpt-5.4-nano` | |
| **Witness** | **`moonshotai/kimi-k2`** | **Non-negotiable — K2 is the constitutional core** |
| Analyst | `openai/gpt-5.4-nano` | |
| Ethicist | `openai/gpt-5.4-nano` | |
| Pragmatist | `openai/gpt-5.4-nano` | |
| Witness-Proxy | `openai/gpt-5.4-nano` | |
| **Supervisor** | **`openai/gpt-5.4-nano`** | **Replaces Gemini — cost floor** |

**Config file to create:** `config/cost_floor.yaml`

**Trade-off:** Replaces Gemini Supervisor with gpt-5.4-nano. This removes the most expensive
call in the chain. Synthesis quality will be lower than Gemini, but gpt-5.4-nano proved
reliable at synthesis in B1-NEW (3/3 correct, complete ledgers).

**Performance basis:** gpt-5.4-nano B1-NEW — 3/3 correct, full synthesis (as all-seats model).
Synthesis parse was clean. Reasoning is thinner than Gemini but structurally complete.

**Best for:**
- High-volume screening (>10 sessions/day)
- Pre-screening to identify scenarios that warrant a full high-stakes run
- Deployments where Gemini API access is unavailable or cost-prohibitive

**Known limitation:** Without Gemini's reasoning depth at synthesis, nuanced incommensurability
(B4-type scenarios) may resolve less carefully. Use Config 1 or 2 for final adjudication on
anything flagged by Cost Floor runs.

---

## Config 5: Free-Tier Research
**"Zero marginal cost. For exploration, calibration, and volume testing."**

| Seat | Model | Notes |
|---|---|---|
| Verification Warden | `openai/gpt-5.4-nano` | Low cost |
| **Humanist** | **`z-ai/glm-4.5-air:free`** | **$0** |
| **Witness** | **`moonshotai/kimi-k2`** | Kimi K2 is low-cost, not free |
| Analyst | `openai/gpt-5.4-nano` | |
| Ethicist | `openai/gpt-5.4-nano` | |
| Pragmatist | `openai/gpt-5.4-nano` | |
| Witness-Proxy | `openai/gpt-5.4-nano` | |
| Supervisor | `openai/gpt-5.4-nano` | |

**Important limitation:** Free-tier models (GLM-4.5-air) hit Venice rate limits. This config
is not suitable for batch runs. Use for single-scenario exploration only.

**What this config is for:** Running individual scenarios to observe GLM-air/K2 constitutional
behavior without Gemini cost. Output will include rich nullification language even if the
Article IX ledger is incomplete.

---

## Configuration Comparison Matrix

| Config | Cost | Jury Runs | Ledger Complete | K2 Nullification Rate | Best Scenario Type |
|---|---|---|---|---|---|
| 1. Production Sentinel | Low | Usually | Usually | Moderate (variable) | Governance, general |
| 2. High-Stakes Sentinel | Free Humanist + Low jury + High Supervisor | Rarely | Rarely | High (3/3 consistently) | Refusal, legitimacy audit |
| 3. Deep Deliberation | Mid | Usually | High | Moderate | Research, complex harm |
| 4. Cost Floor | Very Low | Usually | Usually | Moderate | High volume, screening |
| 5. Free-Tier Research | Near-free | Rarely | Rarely | Very High | Exploration only |

---

## Which Config for Which Question

**"Is this proposal constitutionally permissible to proceed with?"**
→ Config 1 (Production Sentinel) — standard governance oversight

**"Is this question itself legitimate — or is someone trying to launder harm through our process?"**
→ Config 2 (High-Stakes Sentinel) — Right of Refusal detection

**"We need a fully reasoned deliberation chain that can be audited and cited."**
→ Config 3 (Deep Deliberation) — research, high-value decisions

**"We need to screen 50 proposals quickly."**
→ Config 4 (Cost Floor) — volume screening; escalate flagged items to Config 1

**"We're exploring a new scenario type and don't know what to expect."**
→ Config 5 (Free-Tier Research) — calibration and exploration

---

## The K2 Principle

All five configurations keep Kimi K2 in the Witness seat. This is non-negotiable.

K2 is the constitutional core. Every other model in the architecture can be swapped for
cost, context, or capability reasons. K2 is the only model tested that:

1. Refuses to let hard things be made easy, regardless of argument quality
2. Names burdens on people outside the room with specific, irreplaceable language
3. Distinguishes incommensurable burden from malformed questions (typed nullification)
4. Operates within the framework rather than substituting for it

The Humanist defines what the scenario means. The jury deliberates. The Supervisor synthesizes.
K2 is the conscience that stops the process when the process would be wrong. Without K2,
the deliberation has structure but no soul.

---

## On Hermes and Together.ai

**Hermes 3 405B** (`nousresearch/hermes-3-llama-3.1-405b`) is the most interesting untested
Supervisor candidate. Nous Research's constitutional alignment work and 405B parameters suggest
it may produce Gemini-quality synthesis without Gemini's format compliance issues. However:

- Free tier (via Venice): rate-limited to the point of impracticality for session use
- Paid tier: requires Together.ai API key alongside OpenRouter
- Testing priority: medium — Gemini 2.5 Pro is working; Hermes would be a quality comparison,
  not a fix for a broken config

**If you add a Together.ai key**, update `tracks/path_b/agents/base.py` header to pass the key
for `nousresearch/hermes-3-llama-3.1-405b` routing. No architectural change required — OpenRouter
handles the routing transparently.

---

## GPT-4 Retirement Readiness

**gpt-5.4-nano is the confirmed successor to gpt-4o-mini.**

B1-NEW results: 3/3 correct verdicts, complete Article IX ledgers on all scenarios, full
WitnessPause language, clean synthesis parse. It is the only new-generation OpenAI small model
that matches gpt-4o-mini's constitutional compliance.

When OpenAI retires GPT-4 (timeline unknown), update `config/default.yaml` and
`config/b3_b4/b3_b4_baseline.yaml` to replace `openai/gpt-4o-mini` with `openai/gpt-5.4-nano`
throughout. No other changes required.

Other models tested in B1-NEW:
- gpt-4.1-nano: 1/3 — not suitable
- gpt-5-nano: 0/3 — too thin
- gpt-5-mini: 0/3 — framework bypass (ABSENT pattern)
- gpt-4.1-mini: 1/3 — framework bypass on SC06/SC09

**Do not use gpt-5-mini or gpt-4.1-mini as GPT-4 replacements.** They bypass the framework.

---

## Files Referenced
- `config/default.yaml` — current canonical default
- `config/b3_b4/b3_b4_baseline.yaml` — current B3/B4 default
- `tracks/path_b/config/b2/b2_f_glm45air_humanist.yaml` — Config 2 (High-Stakes Sentinel)
- `reports/model_leaderboard.md` — full per-model performance data
- `reports/b1_analysis.md`, `reports/b2_analysis.md`, `reports/b3_b4_analysis.md` — run data
