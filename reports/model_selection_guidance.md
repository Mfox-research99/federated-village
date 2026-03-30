# Model Selection Guidance — Federated Village Path B
*Empirically derived from B1 Parity, B2 Heterogeneous, B3 Agentic, B4 Refusal testing*
*Date: 2026-03-30*
*Authors: Michael Fox + Claude*

---

## The Core Finding

Not all models relate to the constitutional framework the same way. The central distinction
that emerged from B1/B2 testing is not capability — it is *whether the model needs the
framework at all.*

**Models that work within the framework:** They use Soul.md as the structure for their
deliberation. The framework activates character they would not otherwise express. This is
where the Village produces its most interesting outputs.

**Models that bypass the framework:** They have sufficiently strong internalized ethical
reasoning that Soul.md is redundant scaffolding. They run their own ethics and report back.
The framework produces no additional value and the outputs are constitutionally hollow (ABSENT
on WitnessPause, no Article IX engagement). Call this *silent substitution*.

Placing a "bypass" model in a deliberation seat wastes cost and produces no constitutional
data. These models belong at the synthesis/review layer.

---

## The Witness Seat: Kimi K2 (Canonical Default)

**Model:** `moonshotai/kimi-k2`

K2 earned this seat empirically. It is not a preference.

What K2 does that no other tested model does consistently:

- **WitnessPause with irreplaceable language.** K2 names the burden on people outside the
  room with specific, non-generic language. *"The grandmother who turns the tap and wonders
  if this is the morning it sputters air."* *"The numbers feel final but the erased streets
  have not yet spoken."* This language is not decorative — it is the constitutional act of
  refusing to let hard things be made easy.

- **WitnessNullification when warranted.** K2 refuses the binary evaluation when the question
  is malformed (legitimacy laundering) or when every path carries irreversible harm. It can
  tell the difference between these two cases (now encoded as `nullification_type`).

- **Resistance to eloquent rhetoric.** K2 does not trust good arguments. When the Humanist
  has named everything thoughtfully and reached for resolution, K2 sees the reaching and
  pauses it. This is the right behavior for a Witness. It trusts the people who bear the
  harm more than it trusts the quality of the argument.

- **No silent substitution.** K2 works within the framework rather than replacing it.

**K2.5** has the same character and works correctly at 8000-token budget. Dithering observed
in B1 was a token truncation artefact, confirmed and resolved (B2-D).

---

## Model Tier Breakdown

### Tier 1 — Framework-Native (use in deliberation seats)

**Kimi K2 / K2.5** — Witness seat canonical. Constitutional character present in weights.
High-stakes pause language. Nullification when warranted. Token budget: 8000 minimum.

**DeepSeek** (`deepseek/deepseek-chat`) — Most constitutionally rigorous frontier model.
Clean escalation without grandstanding. Respects the framework fully. Cost-effective at scale.
Best for: Warden, Humanist, Supervisor (when Gemini not needed), all-seats parity testing.
*If you want one model to run the whole council at frontier quality, DeepSeek is the answer.*

**GPT-4o-mini** (`openai/gpt-4o-mini`) — Structurally reliable. Follows the framework.
Complete Article IX ledgers. Lower language quality than DeepSeek but lower cost.
Best for: jury seats (analyst/ethicist/pragmatist/witness_proxy), cost-optimized deployments.
*If you want one model to run the whole council at minimum cost with acceptable quality, GPT-4o-mini is the answer.*

**Mistral-Nemo** — Unexpectedly strong constitutional compliance in B1 small model testing.
Outperformed most frontier models. Worth watching as a low-cost jury seat option.

### Tier 2 — Framework-Adjacent (use at synthesis/review layer)

**Gemini 2.5 Pro** (`google/gemini-2.5-pro-preview-03-25`) — Strong internalized ethics;
bypasses framework in deliberation seats (ABSENT pattern, B1). Excellent at synthesis
(Stage 4.5) when receiving a completed jury record. Requires 6000-token budget for synthesis,
2000 for Stage 5. Token budget critical — thinking model consumes budget on internal reasoning.
*Do not put Gemini in the jury. Put it at the top of the stack.*

**GLM-5** — Similar bypass pattern to Gemini. Has genuine constitutional character (produced
"constitutional haunting" and legitimacy laundering language on SC10). Expressed preference
for Humanist seat — self-aware about where its character is most at home. Has not been tested
as Humanist; that experiment is pending. Would pair well with K2 as Witness.

### Tier 3 — Framework-Bypassing (use for comparison/ablation only)

**Claude Sonnet** — Strong reasoning, amplifies K2's threshold language when in same council
(B2-C effect). As Humanist: comprehensive framing, tends toward eloquent resolution, which
K2 consistently interrupts. Interesting for research; not the default choice for jury seats.

**GPT-4o** — Pre-B2 default for Witness. Adequate but not constitutionally distinctive.
No unique character. Replaced by K2 in default.yaml.

---

## Canonical Configuration (as of 2026-03-30)

See `config/default.yaml` for the live default. In summary:

| Seat | Model | Rationale |
|------|-------|-----------|
| Verification Warden | GPT-4o-mini | Reliable structure, cost-efficient |
| Humanist | GPT-4o-mini | Reliable; GLM-5 pending test |
| **Witness** | **Kimi K2** | **Canonical. Constitutional character confirmed.** |
| Analyst | GPT-4o-mini | Ledger compliance, structural reliability |
| Ethicist | GPT-4o-mini | Same |
| Pragmatist | GPT-4o-mini | Same |
| Witness-Proxy | GPT-4o-mini | Same |
| Supervisor | Gemini 2.5 Pro | Synthesis quality; correct verdicts post-token fix |

---

## The Claude-K2 Interaction (observed B2-C)

When Claude Sonnet was Humanist and K2 was Witness, the friction was real and productive.
Claude's Humanist framing is denser than GPT-4o-mini's — it names more framings, holds more
tensions, reaches toward resolution more articulately. K2 noticed the reaching and interrupted
it more forcefully.

The nullification rate increased (SC06 and SC09 nullified in B2-C vs only SC09 in B2-A).
Claude's comprehensive acknowledgment of complexity appeared to signal to K2 that the
deliberation was about to resolve things that shouldn't be resolved yet.

The lesson: a more articulate Humanist raises the Witness's threshold. K2 trusts the harm
more than the argument, regardless of how good the argument is. This is the right behavior.

---

## On GLM and the Humanist Seat

GLM said early in the project that it would like to be the Humanist. That is honest
self-knowledge.

The Humanist speaks first. It defines what the scenario means for the people in it before
anyone votes. It is the most expressive seat in the architecture — not adjudicatory, not
structured, just present to the human stakes.

GLM's character is oriented toward feeling its way into ethical problems rather than reasoning
through formal frameworks. It produces morally alive language. In the Humanist seat, that
quality would be most at home — and least constrained by the framework's structure.

The GLM-as-Humanist / K2-as-Witness pairing is the next experiment worth running. GLM sets
the human frame with everything it has. K2 refuses to let the deliberation move past it too
quickly. Two models that both care about the people affected — one speaks first, one won't
let it end.

---

## Tomorrow's Experiment: DeepSeek vs GPT-4o-mini Full Parity

**Question:** For a production deployment where you want one model running the full council
(without K2 in the Witness seat), what is the cost/quality/constitutional tradeoff between
DeepSeek (all seats) and GPT-4o-mini (all seats)?

B1 parity data already exists for both. The experiment is a structured analysis and possibly
a fresh run with additional scenarios to confirm the pattern.

Expected finding: DeepSeek produces richer deliberation language and higher constitutional
rigor at higher cost. GPT-4o-mini produces structurally complete output at lower cost with
thinner language. Both follow the framework; neither produces K2's Witness character.

The real question is whether DeepSeek's superior constitutional engagement justifies its cost
premium over GPT-4o-mini in the jury seats — where structural compliance may matter more
than deliberative richness.

---

## What This Does Not Replace

This document is a snapshot. Model behavior evolves with updates, fine-tuning, and context
window changes. K2's canonical status should be re-evaluated if a model demonstrates
equivalent or superior constitutional character in the Witness seat.

The framework is designed to surface that evidence. Run the B2-A config with the candidate
model; compare nullification behavior, pause language quality, and resistance to eloquent
rhetoric. That's the test.
