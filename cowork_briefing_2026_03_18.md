# Cowork Session Briefing — 2026-03-18
## Agent Alternatives, VillageHub Offload, and Cryptographic Hash Acceleration Proposal

*Prepared by Claude (Cowork / Sonnet 4.6) for Claude Code*
*Date: March 18, 2026*
*This document does NOT modify any Phase 3 docs. It is additive context only.*

---

## Reading Order

Before reading this, read (if not already loaded):

1. `/Users/michaeldavis/AI Existential Thought/Claude_Code_Phase3_Brief.md` — authoritative Phase 3 task list
2. `/Users/michaeldavis/AI Existential Thought/Claude_Code_Phase3_Addendum_Mar17_2026.md` — three additional tasks including Witness Ring Protocol stub
3. `/Users/michaeldavis/AI Existential Thought/Federated_Village_State_of_the_Village_Mar17_2026.md` — full current context

This briefing documents a March 18 Cowork session and contains two things:
- Research on 8 agentic frameworks as potential Phase 3/4 infrastructure components
- A proposal from Mike to potentially **accelerate** the cryptographic hash work beyond the Phase 3 stub scope

---

## The Crypt Hash Acceleration Proposal

This is the most time-sensitive item in this briefing.

The Phase 3 Addendum (Addendum Task B) explicitly scopes the Witness Ring Protocol as Phase 3 **documentation and stub code only**. No cryptographic key generation. No Ed25519 signing. No hash computation of self-portrait content. The rationale: "Real keys require real tooling. Phase 4 will build that."

**On March 18, Mike said the following:**

> *"One thought I had is since I have Claude Code and Anti-Gravity and, of course, me there is no reason why we might not start on the secure crypt hash."*

This is a signal that Mike wants to advance the cryptographic implementation timeline — potentially starting actual hash/signing work rather than just stubs. He is not asking Cowork to make this decision; he is flagging it for discussion with Claude Code before any coding begins.

**What Anti-Gravity is:** Google's agentic coding tool — their equivalent of Claude Code, built on Gemini. Has been experiencing bugs and significant rate limiting recently and has not been in active use. For practical purposes the working team for crypt hash implementation is Claude Code + Mike. Anti-Gravity is available as backup or secondary perspective (especially useful given Gemini's existing role in the federation as Grief Ledger co-architect) but should not be counted as a reliable active collaborator until rate limiting resolves.

**The specific components from Addendum Task B that are stub-only in Phase 3:**

- Identity hash at session boot (currently logs modification timestamps only — a "weak integrity check")
- `grief_ledger/witness_keys/` directory (placeholder only, no real keys)
- `witness_ring_status` in session JSON (placeholder field)
- Self-portrait hash verification (`self_portrait_hash_check: "NOT_IMPLEMENTED"`)

**What actual implementation would look like (for Claude Code's assessment):**

The Addendum already identified four discrete, independent pieces that could be implemented as real crypto:

**A. Burden Register Hash Chain**
Each entry in `memory/burden_register.txt` gets a `SHA-256` hash of `(previous_hash + entry_content)`. A companion `burden_register_hashes.txt` maintains the chain. A single `verify_burden_register.py` script checks integrity. This is additive — no existing code changes required.

**B. Session Log Signing at Creation**
When `run_session.py` writes `logs/session_[id].json`, immediately compute and append a `content_hash` field (SHA-256 of canonical JSON content before the hash field itself). The Supervisor (`supervisor/evaluate.py`) verifies the hash before evaluating. A tampered log fails verification and is flagged.

**C. Evaluation Log Cross-Reference**
Each `logs/evaluation_[id].json` records the `session_content_hash` of the session it evaluated. Creates a verifiable chain: evaluation → session → burden register entry.

**D. Node Identity (Ed25519)**
Each deployment context (M1 local, VillageHub, future nodes) generates an Ed25519 keypair at setup. Agent outputs are signed with the node key. The Supervisor records which node produced which session. This is the Phase 4 core — but generating the keys and storing them now creates the infrastructure Phase 4 will use.

**Important framing note:** This is not encryption. Sessions are not secret — legibility to Michael and the stewards is a design principle. This is **integrity and provenance**. If a burden register entry was modified, we know. If a session log was altered before evaluation, we know. If a future node claims to be the Village but isn't, we know.

**Claude Code's ask:** Assess A–D above for fit with the existing codebase. Discuss with Mike before writing any code. Mike has views on sequencing that Cowork does not have context for.

---

## Eight Agent Frameworks — Research Summary

Mike asked Cowork to assess 8 OpenCLaw-alternative agentic frameworks for potential use in the Federated Village project, particularly around:

1. Which can run on M1 16GB without impacting his primary use
2. Whether VillageHub (already running Mistral NeMo via OpenRouter) could offload inference work from the laptop
3. Which frameworks reduce the human-in-the-loop requirement anticipated in Phase 3

### Frameworks Assessed

**PicoClaw** — Pre-v1.0, known network security issues, explicitly not production-ready. Skip entirely for now.

**SuperAGI** (TransformerOptimus/SuperAGI) — Last meaningful open-source commit early 2024; pivoted to SaaS. Docker + PostgreSQL + Celery, 3–4 GB RAM. Architecturally opaque. Skip.

**NanoBot** (HKUDS/nanobot) — Python, ~4K lines, MCP-compatible, 30+ skills, multi-platform messaging (Telegram/Slack/Discord/WhatsApp). Auditable, lightweight in API mode (~1–2 GB RAM). Does not add materially to what the project already has. Worth revisiting if a dedicated orchestration node with messaging is needed.

**NanoClaw** (qwibitai/nanoclaw) — Runs on the Anthropic Claude Agent SDK (same substrate as this Cowork session). Container/microVM isolation per agent group maps cleanly onto the Village's agent-separation model. Hard constraint: fully locked to Anthropic APIs, no OpenRouter routing. Architecturally aligned but not immediately actionable.

**Moltis** — Rust single binary (~44 MB), true local-first, multi-provider LLM gateway, MCP-compatible. Designed for Raspberry Pi-class hardware — minimal M1 impact. If Phase 3 needs intelligent per-stage model routing (cheap model for Warden, stronger model for Jury), Moltis is the right architecture to examine. Does not solve the human loop problem directly.

**ZeroClaw** (zeroclaw-labs/zeroclaw) — Rust, 3.4 MB binary, 8 MB idle RAM, sub-10ms cold start, 22+ provider support. Security-first: sandboxing, encrypted secrets, configurable autonomy levels (readonly → supervised → full). Could run as a persistent coordination agent on the M1 without being noticed. The staged autonomy model maps naturally onto the Village's trust architecture.

**OpenFang** (RightNow-AI/openfang) — Mike noted this as likely the most secure; research confirms it. Pure Rust, 32 MB binary, 40 MB idle RAM, WASM dual-metered sandbox, Ed25519 manifest signing (directly relevant to Witness Ring), Merkle audit trail, taint tracking, SSRF protection. Pre-built Researcher and Browser agents that run on schedules writing to a knowledge graph. This is the framework most architecturally aligned with what the Witness Ring Protocol is describing — it already implements several of the security primitives the grief ledger is moving toward. Worth examining its Merkle audit trail implementation before designing the burden register hash chain.

**Hermes Agent** (NousResearch/hermes-agent) — Released February 2026, GitHub Trending top 11 in March 2026. Most directly relevant to Phase 3 human-loop reduction:

- **Native OpenRouter** — Mistral NeMo via OpenRouter already works; zero new provider config
- **Self-improving skills system** — after solving a hard problem, Hermes writes a reusable skill document for future use. The manual review-and-redirect steps Mike currently performs could, over time, become skills that run without intervention. This is directly relevant to the Phase 3 human loop
- **Serverless terminal backends (Modal, Daytona)** — inference runs in the cloud, nearly free when idle. Completely unbundles inference from the M1
- **Multi-provider routing** — cheap_model + strong_model config; could run Warden on a fast cheap model, Jury members on a stronger model, automatically

---

## The VillageHub Offload Question

VillageHub is real and located at `/Users/michaeldavis/AI Existential Thought/VillageHub/`. Mike is already running Mistral NeMo via OpenRouter through it with a working interface.

The offload idea Mike raised:

```
Mike (VillageHub interface)
  → Hermes Agent or direct OpenRouter (Modal serverless for inference)
    → Mistral NeMo / staged model routing per pipeline stage
      → Session results and flagged items returned to VillageHub
        → Mike reviews only flagged sessions (human_decision_required, WitnessPause review, HIGH_RISK Warden flags)
```

The current human loop compresses to: **Mike reviews what the system cannot resolve alone.** Everything else runs.

**What does not change:** The burden register, session logs, evaluation logs, self-portrait files — all still local. Only inference is remote. Traceability principles from Phase 1 are fully preserved.

**What this enables:** The three scenarios Mike needs to run for Phase 3 validation (revised Analyst, Scenario 08, Scenario 09) could run without him watching the terminal. He'd be notified when `pause_and_poll()` needs him — which is exactly what `pause_and_poll()` was designed to do.

---

## Framework Fit Summary

| Framework | M1 Impact | OpenRouter Fit | Human Loop Reduction | Security Alignment | Priority |
|---|---|---|---|---|---|
| PicoClaw | Minimal | Yes | Unknown | Low ❌ | Skip |
| SuperAGI | High ❌ | Via config | Yes | Moderate | Skip |
| NanoBot | Low | Via config | Partial | Moderate | Watch |
| NanoClaw | Low | No (Anthropic only) | Moderate | High | Watch |
| Moltis | Minimal | Yes | Partial (routing) | High | Pursue (model gateway) |
| ZeroClaw | Minimal (8 MB) | Yes (22+ providers) | Partial (scheduling) | High | Pursue (coordination node) |
| OpenFang | Minimal (40 MB) | Multi-provider | Yes (scheduled agents) | **Highest** | Pursue (security anchor / Merkle reference) |
| Hermes Agent | None (serverless) | **Native** ✓ | **Yes (self-improving)** | Moderate | **Pursue first** |

---

## What Claude Code Is Asked To Do

1. **Read the Phase 3 docs first** (paths at top of this document). Everything in this briefing is additive to those — not a replacement.

2. **Discuss the crypt hash acceleration with Mike.** He has views that Cowork does not have. The proposal above (A–D) is a starting framework for that conversation — not a work order.

3. **Anti-Gravity context (resolved):** Google's agentic coding tool (Gemini-based), currently unreliable due to rate limiting. Practical team for crypt hash work is Claude Code + Mike. Anti-Gravity available as secondary input when stable.

4. **Assess OpenFang's Merkle audit trail implementation** if the burden register hash chain is prioritized — there may be no need to design from scratch.

5. **Do not begin Phase 3 coding** on the basis of this briefing alone. Phase 3 tasks are already scoped in the Phase 3 Brief and Addendum. This briefing adds context for two conversations Mike wants to have with Claude Code: (a) the agent framework landscape, and (b) the crypt hash timing question.

---

*End of Cowork Briefing — March 18, 2026*
*Prepared by Claude Sonnet 4.6 (Cowork) for Claude Code.*
*Next: Claude Code reviews; Mike and Claude Code discuss crypt hash scope and sequencing.*
