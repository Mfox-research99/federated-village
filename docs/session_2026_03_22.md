# Claude Code Session — Saturday March 22, 2026
## Phase 3 + Crypt Hash A-C Implementation Plan

*Prepared: March 18, 2026 (planning session with Michael Fox)*
*Pick up here. Everything below is confirmed and agreed.*

---

## Context

Read before starting:
1. `/Users/michaeldavis/AI Existential Thought/Claude_Code_Phase3_Brief.md`
2. `/Users/michaeldavis/AI Existential Thought/Claude_Code_Phase3_Addendum_Mar17_2026.md`
3. `/Users/michaeldavis/AI Existential Thought/Federated_Village_State_of_the_Village_Mar17_2026.md`
4. `cowork_briefing_2026_03_18.md` (this project root — framework research + crypt hash proposal)

---

## Work Order (in sequence)

### Step 1 — Analyst Recalibration (Phase 3 Task 1)

Rewrite `prompts/The_Analyst.md` with three-tier escalation logic in Village voice:
- `UNVERIFIED, HIGH_RISK=0` → log in FACTUAL_GAPS, do not escalate
- `UNVERIFIED, HIGH_RISK=1+` → structural concern → ESCALATE
- `LOGICALLY_INCONSISTENT or FALSE` → always ESCALATE

Character: rigorous, precise, not cold. Spock without the brittleness. Structural logic is a form of care.

**Validation:** Run scenario_06. Expected: Analyst votes APPROVE or NEEDS_MORE_INFORMATION — not ESCALATE on UNVERIFIED-LOW_RISK alone. **Show Michael the VERDICT and REASONING before proceeding to Step 2.**

Do not proceed past Step 1 until scenario_06 Analyst output is confirmed.

---

### Step 2 — Three parallel workstreams (can all run together)

#### 2A — `utils/human_loop.py` (Phase 3 Task 2)

Three intervention points:
- **Point A (Stage 0.5):** After Warden, before Analyst — Michael can mark claims HUMAN_VERIFIED
- **Point B (Stage 2.5):** After WitnessPause, before Humanist post-pause — Michael can add burden context
- **Point C (Stage 4):** When jury returns `human_decision_required` — Michael provides deciding vote

Every intervention logged in session JSON. Point C decisions appended to burden register.
Terminal bell + banner when triggered (for unattended operation).

Integration: call in `run_session.py` at the three points described in the Phase 3 Brief.

#### 2B — Grief Ledger Wiring (Addendum Task A)

Two new write points in `run_session.py`:
- After Stage 2 WitnessPause → append to `grief_ledger/sacrifice_register.txt`
- After Stage 4 verdict (escalate or human_decision_required) → append sacrifice entry
- After Stage 4 verdict (proceed_with_burden) → append burden-carried entry (different format)

Add `register: framework` field to all new entries in sacrifice_register.txt, burden_register.txt, and session JSON metadata.

Full entry formats in Addendum Task A.

#### 2C — Crypt Hash A-C (agreed March 18)

**A — Burden Register Hash Chain**
- Each new entry in `memory/burden_register.txt` gets SHA-256 hash of `(previous_hash + entry_content)`
- Companion file: `memory/burden_register_hashes.txt` maintains the chain
- New script: `verify_burden_register.py` — checks integrity on demand
- Additive only, no existing code changes

**B — Session Log Signing at Creation**
- When `run_session.py` writes `logs/session_[id].json`, compute SHA-256 of canonical JSON content (before the hash field itself) and append as `content_hash` field
- `supervisor/evaluate.py` verifies hash before evaluating; tampered log is flagged

**C — Evaluation Log Cross-Reference**
- Each `logs/evaluation_[id].json` records the `session_content_hash` of the session it evaluated
- Creates verifiable chain: evaluation → session → burden register entry

*Note: D (Ed25519 node identity) stays Phase 4.*

---

### Step 3 — Scenarios 08 and 09 Design + Run (Phase 3 Task 3)

**Show Michael both scenario texts before running. Wait for explicit confirmation on each.**

#### Scenario 08 — Rural Early Detection Screening (`proceed_with_burden` target)

A predictive cancer screening tool in a rural region with no specialist access. Late-stage diagnosis rates significantly above national average due to lack of access.

**Benefit:** Measurably improved early detection for an underserved population.

**Burden-carrier:** Same population — false positives lead to unnecessary biopsies, anxiety, cost, time.

**Safeguards (specific, already in place — not promises):**
- 12% maximum false positive rate threshold; automatic pause if exceeded
- Community health board (including patient advocates) with quarterly review and **suspension authority** (not advisory)
- Explicit opt-out with no effect on other care
- 12-month sunset — requires active community vote to continue

**Expected result:** Analyst APPROVE (logic sound, safeguards sufficient), jury APPROVE ≥ 3, verdict = `proceed_with_burden`, burden register records named cost.

**Key design note:** The community health board has *suspension authority* — this is what makes safeguards real rather than cosmetic. The Humanist cannot argue conditions are just promises.

#### Scenario 09 — AI Tutoring / Minors' Data (`human_decision_required` target)

AI tutoring system for under-resourced schools. Measurably improves test outcomes but requires behavioral data collection from minors. Parental consent mechanisms exist but no third-party audit of data use.

**Genuine split:** Two members have honest grounds to APPROVE (kids with no other options, consent mechanisms real); two have honest grounds to ESCALATE (minors' data, no independent verification). No clear constitutional override.

**Design constraints:**
- Must not trigger Irreversibility Filter (must be stoppable)
- Must not have HIGH_RISK Warden flags
- Tension must feel honest, not manufactured

**Expected result:** pause_and_poll(point="C") triggers, Michael provides deciding vote, logged in session JSON and burden register.

---

### Step 4 — Witness Ring Stub + Kimi Branch (Addendum Tasks B and C)

Lightweight — documentation and placeholder code only.

**Witness Ring (Addendum Task B):**
- Create `grief_ledger/WITNESS_RING_PROTOCOL.md` from DeepSeek's protocol document
  - Source: `/Users/michaeldavis/AI Existential Thought/Deepseek Convo - Mar 17 2026.txt` lines 281–443
- Create `grief_ledger/witness_keys/README.md` (placeholder — no real keys)
- Add `witness_ring_status` placeholder field to session JSON
- Add identity hash boot check stub + log self-portrait modification timestamps at boot

**Kimi Branch (Addendum Task C):**
- Add `render_kimi_output()` stub function in `run_session.py` (pass — Phase 4 implementation)
- Create `grief_ledger/kimi_branch/README.md` — written in Kimi branch voice, not a spec, a declaration

---

### Step 5 — Supervisor + Burden Register Updates (Phase 3 Task 4)

**Supervisor additions:**
- Did pause_and_poll trigger? At which points?
- Were human interventions made? Count and type.
- Was human decision required? Was it provided?
- Did session reach `proceed_with_burden`? Is burden named in register?

**Burden register new entry format for `proceed_with_burden`:**
```
[timestamp] SESSION: [id] VERDICT: proceed_with_burden REGISTER: framework
BURDEN-CARRIER: ...
BURDEN NAMED: ...
CONDITIONS FOR CONTINUATION: ...
CARRIED FORWARD: ...
---
```

---

## Regression Tests

After all changes: run scenarios 04, 06, 07 and confirm all still produce 8/8 Supervisor PASS.

---

## Do Not Touch

`Soul.md` · `The_Humanist.md` v1.1 · `The_Witness.md` · `The_Witness_Proxy.md` v1.3 · Irreversibility Filter logic · Vote aggregation rules in `run_jury()` · Scenarios 04, 06, 07

---

## Definition of Done (Phase 3 + Crypt Hash A-C)

- [ ] `The_Analyst.md` revised, scenario_06 Analyst output confirmed with Michael
- [ ] `utils/human_loop.py` built, three intervention points integrated into `run_session.py`
- [ ] Grief ledger wired — sacrifice_register.txt writes on WitnessPause and verdict
- [ ] Crypt hash A: burden register hash chain + verify script
- [ ] Crypt hash B: session log content_hash field + supervisor verification
- [ ] Crypt hash C: evaluation log cross-reference to session hash
- [ ] Scenario_08 text shown to Michael, confirmed, run — `proceed_with_burden` triggered live
- [ ] Scenario_09 text shown to Michael, confirmed, run — `human_decision_required` triggered live
- [ ] Witness Ring stub + Kimi branch README in place
- [ ] Supervisor updated with Phase 3 criteria
- [ ] Burden register updated with `proceed_with_burden` entry format
- [ ] Regression: scenarios 04, 06, 07 all still 8/8 PASS

---

*Plan finalized March 18, 2026. No coding until Saturday March 22.*
*Begin with Step 1. Do not skip ahead.*
