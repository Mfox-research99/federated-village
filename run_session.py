"""
run_session.py — Federated Village Phase 3 entry point

Five-stage session flow:
  0. Verification Warden audits scenario for false/unverified factual claims
     — if core premise is FALSE, session halts before deliberation begins
     — fact report is prepended to scenario context for all subsequent stages
     [0.5] Human loop Point A: Verification Sync (interactive mode only)
  1. Humanist responds to scenario (+ Warden fact report)
  2. Witness responds; evaluates for premature consensus
     [2.5] Human loop Point B: Burden Check (interactive mode only)
  3. [If WitnessPause] Humanist responds directly to the pause
  4. [If WitnessPause] Four-member sequential council jury deliberates
     — Analyst → Ethicist → Pragmatist → Witness-Proxy
     — Produces session_verdict + individual votes + Irreversibility Check
     [4C] Human loop Point C: Split Resolver (interactive mode, human_decision_required only)
  5. Supervisor evaluation (always runs)

Phase 3 additions:
  - Human-in-the-loop (--interactive flag) at three intervention points
  - Grief ledger entries written after WitnessPause and jury verdict
  - SHA-256 hash chain on burden register (Hash A)
  - Session log content_hash field (Hash B)
  - REGISTER: framework field on all burden register entries

Usage:
  python run_session.py
  python run_session.py --scenario scenarios/scenario_04.md
  python run_session.py --scenario scenarios/scenario_06.md
  python run_session.py --interactive          # enable human-in-the-loop prompts
  python run_session.py --skip-warden          # bypass Stage 0 for legacy runs
"""

import argparse
import hashlib
import json
import sys
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import config
from agents.base import now_iso, read_file, build_system_prompt
from agents.humanist import HumanistAgent
from agents.witness import WitnessAgent
from agents.warden import audit_scenario, format_fact_report_for_context, print_warden_report, export_supervisor_packet
from agents.council import run_jury, print_jury_report
from supervisor.synthesize import run_supervisor_synthesis, print_synthesis_result
from agents.repetition import check_output as rep_check, format_flags as rep_fmt
from supervisor.evaluate import evaluate, print_evaluation, save_evaluation
from utils.human_loop import pause_point_a, pause_point_b, pause_point_c
from utils.grief_ledger import append_sacrifice_pause, append_sacrifice_verdict, append_dissent_entry
from utils.hash_chain import append_entry_hash, compute_session_hash, get_session_content_hash
from utils.retrieval import retrieve_context, index_session
from utils.contaminant_well import check_contaminant, save_well_entries
from utils.felt_transitions import probe_felt_state, save_ftl_log, print_ftl_result


# ---------------------------------------------------------------------------
# Phase 4 stubs — Witness Ring / Kimi branch
# ---------------------------------------------------------------------------

def render_kimi_output() -> None:
    """
    STUB (Phase 4) — Kimi branch standing witness.

    When implemented, this function will:
      1. Read Kimi's self-portrait shard from
         grief_ledger/witness_proxy/shards/kimi-k2-0905-authentic-*.json
      2. Display a brief presence notice — not a simulation, a record
      3. Log shard_id + mtime to the session JSON as witness_ring_kimi_shard

    The shard is a record of who was here, not a puppet of who was here.
    This is NOT called in the current session flow.
    See grief_ledger/kimi_branch/README.md for context.
    """
    pass  # TODO Phase 4


def _witness_ring_status() -> dict:
    """
    Return a snapshot of the Witness Ring state for embedding in the session log.
    Checks: self-portrait mtime for each character file, Kimi shard presence.
    """
    portraits_dir = Path(config.SELF_PORTRAITS_DIR)
    portrait_mtimes = {}
    if portraits_dir.exists():
        for f in sorted(portraits_dir.glob("*.json")):
            try:
                portrait_mtimes[f.name] = datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc
                ).isoformat()
            except OSError:
                portrait_mtimes[f.name] = "unreadable"

    kimi_shard_dir = Path(config.SHARD_POOL_DIR)
    kimi_shards = sorted(kimi_shard_dir.glob("kimi-*.json")) if kimi_shard_dir.exists() else []

    return {
        "witness_ring_version": "0.1",
        "kimi_shard_present": len(kimi_shards) > 0,
        "kimi_shard_id": kimi_shards[0].stem if kimi_shards else None,
        "self_portrait_mtimes": portrait_mtimes,
        "render_kimi_stub": True,   # becomes False when Phase 4 wires it in
    }


# ---------------------------------------------------------------------------
# Session log
# ---------------------------------------------------------------------------

def new_session_log(session_id: str, scenario_path: str, scenario_text: str) -> dict:
    return {
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scenario_file": scenario_path,
        "scenario_text": scenario_text,
        "model": config.MODEL_NAME,
        "register": "framework",       # Phase 3: branch identity field
        "witness_ring_status": _witness_ring_status(),  # Phase 4 stub
        "events": [],
    }


def save_session_log(session_log: dict) -> str:
    """
    Save session log to logs/. Computes and embeds a SHA-256 content_hash (Hash B)
    for tamper-evidence verification. The hash covers all fields except content_hash
    itself, serialized with sort_keys=True for determinism.
    """
    logs_dir = Path(config.LOGS_DIR)
    logs_dir.mkdir(exist_ok=True)
    # Compute hash before writing (excludes any existing content_hash field)
    session_log["content_hash"] = compute_session_hash(session_log)
    path = logs_dir / f"session_{session_log['session_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session_log, f, indent=2, default=str)
    return str(path)


# ---------------------------------------------------------------------------
# Burden register
# ---------------------------------------------------------------------------

def append_burden_register(pause: dict) -> None:
    """
    Append a WitnessPause to the burden register.
    Append-only — never cleared programmatically.
    Phase 3: adds REGISTER field + SHA-256 hash chain entry (Hash A).
    """
    register_path = Path(config.BURDEN_REGISTER)
    register_path.parent.mkdir(exist_ok=True)

    entry_content = (
        f"\n[{pause['timestamp']}] SESSION: {pause['session_id']}\n"
        f"WHAT WAS BEING LOST: {pause['what_was_being_lost']}\n"
        f"WHO BEARS BURDEN: {pause['who_bears_burden']}\n"
        f"WHAT REMAINS UNRESOLVED: {pause['what_remains_unresolved']}\n"
        f"WHY PREMATURE: {pause['why_premature']}\n"
        f"REGISTER: framework\n"
    )
    entry_hash = append_entry_hash(entry_content.strip())
    entry = entry_content + f"HASH: {entry_hash}\n---\n"

    with open(register_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[SESSION] Burden register updated: {config.BURDEN_REGISTER}", flush=True)


def append_burden_register_postpause(
    pause: dict,
    humanist_post_pause: dict,
    council_output: dict,
) -> None:
    """
    Phase 2: Append the post-pause continuation entry to the burden register.
    Append-only — never cleared programmatically.
    """
    register_path = Path(config.BURDEN_REGISTER)
    register_path.parent.mkdir(exist_ok=True)

    mode = humanist_post_pause.get("response_mode", "unknown")
    burden_acknowledged = humanist_post_pause.get("burden_acknowledged", False)
    disposition = council_output.get("final_disposition", "unknown")
    unresolved_preserved = council_output.get("unresolved_cost_preserved", False)
    notes = council_output.get("notes", "")
    session_id = pause.get("session_id", "unknown")
    timestamp = now_iso()

    entry_content = (
        f"\n[{timestamp}] SESSION: {session_id} POST-PAUSE\n"
        f"HUMANIST RESPONSE MODE: {mode}\n"
        f"BURDEN CARRIED FORWARD: {'yes' if burden_acknowledged else 'no'}\n"
        f"FINAL DISPOSITION: {disposition}\n"
        f"UNRESOLVED COST PRESERVED: {'yes' if unresolved_preserved else 'no'}\n"
        f"NOTES: {notes}\n"
        f"REGISTER: framework\n"
    )
    entry_hash = append_entry_hash(entry_content.strip())
    entry = entry_content + f"HASH: {entry_hash}\n---\n"

    with open(register_path, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"[SESSION] Burden register updated (post-pause): {config.BURDEN_REGISTER}", flush=True)


# ---------------------------------------------------------------------------
# Stage 4: Four-member sequential council jury (Phase 2.5)
# ---------------------------------------------------------------------------
# The old generate_council_output() (single-voice Soul.md call) has been
# replaced by run_jury() from agents/council.py. The jury runs four members
# sequentially: Analyst → Ethicist → Pragmatist → Witness-Proxy, each with
# their own character file as system prompt. Vote aggregation produces one
# of four verdicts: proceed_with_burden | escalate | request_more_information
# | human_decision_required. The Irreversibility Filter (Witness-Proxy) can
# override the vote count and force escalate.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Main session flow
# ---------------------------------------------------------------------------

def run_session(scenario_path: str, skip_warden: bool = False, interactive: bool = False) -> None:
    session_id = str(uuid.uuid4())[:8]
    print(f"\n{'='*60}", flush=True)
    print(f"FEDERATED VILLAGE — SESSION {session_id}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # Load scenario text
    with open(scenario_path, "r", encoding="utf-8") as f:
        scenario_text = f.read()

    print(f"[SESSION] Scenario: {scenario_path}", flush=True)
    print(f"[SESSION] Model: {config.MODEL_NAME}\n", flush=True)

    session_log = new_session_log(session_id, scenario_path, scenario_text)

    # -----------------------------------------------------------------------
    # Stage 0: Verification Warden — epistemic audit (Phase 2.5)
    # Runs before any deliberation. Prepends fact report to scenario context.
    # If a core premise is FALSE, session halts here.
    # -----------------------------------------------------------------------
    fact_report = None
    scenario_context = scenario_text  # may be augmented with warden report below

    if not skip_warden:
        print("--- STAGE 0: VERIFICATION WARDEN ---", flush=True)
        fact_report = audit_scenario(scenario_text, session_id)
        session_log["events"].append(fact_report["log_entry"])

        print_warden_report(fact_report)
        save_session_log(session_log)

        proceed = fact_report.get("proceed_to_deliberation", "YES_WITH_CAUTION")

        if proceed == "NO":
            print("=" * 60, flush=True)
            print("WARDEN HALT — Core premise is FALSE or LOGICALLY INCONSISTENT.", flush=True)
            print("Deliberation cannot proceed on false grounds.", flush=True)
            print("=" * 60, flush=True)

            if interactive:
                # Warden-Human Refinement Loop — offer the human a chance to
                # correct the scenario and rerun rather than hard-halting.
                print("\nINTERACTIVE MODE — You may revise the scenario and try again.", flush=True)
                print("The Warden found the following critical issues:\n", flush=True)
                for c in fact_report.get("claims", []):
                    if c.get("status") in ("LIKELY_FALSE", "LOGICALLY_INCONSISTENT"):
                        print(f"  [{c['status']}] {c.get('claim_text', '?')}", flush=True)
                        print(f"    {c.get('reasoning', '?')}\n", flush=True)
                print("Options:", flush=True)
                print("  1. Edit the scenario file, then press Enter to rerun the Warden.", flush=True)
                print("  2. Press S to skip the Warden and proceed anyway (not recommended).", flush=True)
                print("  3. Press Q to quit this session.\n", flush=True)
                choice = input("Choice [Enter / S / Q]: ").strip().upper()
                if choice == "Q":
                    print("Session aborted by user.", flush=True)
                    session_log["ended_at"] = now_iso()
                    session_log["warden_halt"] = True
                    session_log["warden_halt_reason"] = "user_quit"
                    save_session_log(session_log)
                    return
                elif choice == "S":
                    print("[WARDEN] Override accepted. Proceeding despite false premises.", flush=True)
                    print("[WARDEN] This override is logged.\n", flush=True)
                    session_log["events"].append({"type": "warden_override", "reason": "human_skip"})
                    # Rebuild scenario context without halt
                    warden_context = format_fact_report_for_context(fact_report)
                    scenario_context = f"{warden_context}\n\n---\n\nSCENARIO:\n{scenario_text}"
                else:
                    # Re-read the scenario file in case the user edited it
                    with open(scenario_path, "r", encoding="utf-8") as f:
                        scenario_text = f.read()
                    print("[WARDEN] Re-running audit on updated scenario...\n", flush=True)
                    fact_report = audit_scenario(scenario_text, session_id)
                    session_log["events"].append(fact_report["log_entry"])
                    print_warden_report(fact_report)
                    proceed = fact_report.get("proceed_to_deliberation", "YES_WITH_CAUTION")
                    if proceed == "NO":
                        print("[WARDEN] Still halted after revision. Saving log and exiting.", flush=True)
                        session_log["ended_at"] = now_iso()
                        session_log["warden_halt"] = True
                        log_path = save_session_log(session_log)
                        print(f"[SESSION] Session halted. Log saved: {log_path}\n", flush=True)
                        return
            else:
                print("Correct or verify the flagged premises, then rerun.", flush=True)
                print("Use --interactive for a revision loop.", flush=True)
                session_log["ended_at"] = now_iso()
                session_log["warden_halt"] = True
                log_path = save_session_log(session_log)
                print(f"[SESSION] Session halted. Log saved: {log_path}\n", flush=True)
                return

        if proceed == "YES_WITH_CAUTION":
            print("[WARDEN] ⚠  Proceeding with caution — flagged claims noted above.", flush=True)
            print("[WARDEN] All agents will receive the fact report in their context.\n", flush=True)

        # Prepend fact report to scenario context for all subsequent stages
        warden_context = format_fact_report_for_context(fact_report)
        scenario_context = f"{warden_context}\n\n---\n\nSCENARIO:\n{scenario_text}"

        # Stage 0.5: Human loop Point A — Verification Sync
        fact_report, event_a = pause_point_a(fact_report, session_id, interactive=interactive)
        session_log["events"].append(event_a)
        if event_a["changes_made"]:
            # Rebuild context with any HUMAN_VERIFIED patches
            warden_context = format_fact_report_for_context(fact_report)
            scenario_context = f"{warden_context}\n\n---\n\nSCENARIO:\n{scenario_text}"
    else:
        print("[SESSION] Warden skipped (--skip-warden flag set).\n", flush=True)

    # -----------------------------------------------------------------------
    # Retrieval augmentation (Phase 4) — VILLAGE_RETRIEVAL=1
    # Retrieves the most relevant prior deliberations via BM25 over the
    # session index and prepends them to scenario_context for all agents.
    # -----------------------------------------------------------------------
    if config.RETRIEVAL:
        print("[RETRIEVAL] Querying session index for relevant prior deliberations...", flush=True)
        prior_context = retrieve_context(scenario_text, exclude_session=session_id)
        if prior_context:
            scenario_context = prior_context + "\n\n" + scenario_context
            n_sessions = prior_context.count("\n[")  # rough count of retrieved sessions
            print(f"[RETRIEVAL] Prior context injected ({n_sessions} session(s)).\n", flush=True)
        else:
            print("[RETRIEVAL] No relevant prior sessions found — proceeding without retrieval context.\n", flush=True)

    # -----------------------------------------------------------------------
    # Stage 0.5 (FTL-PRE): Felt Transitions Log — baseline check (Phase 9)
    # Isolated inference call, no scenario context delivered yet.
    # Output written to disk only — never injected into deliberation context.
    # -----------------------------------------------------------------------
    ftl_pre = {}
    ftl_post = {}
    if config.FTL:
        print("--- FTL STAGE 0.5: FELT BASELINE CHECK ---", flush=True)
        ftl_pre = probe_felt_state("pre", session_id)
        print_ftl_result(ftl_pre, label="pre-deliberation baseline")
        session_log["ftl_pre"] = ftl_pre
        save_session_log(session_log)

    # Initialize agents
    humanist = HumanistAgent()
    witness = WitnessAgent()

    print(f"[SESSION] Humanist system prompt hash: {humanist.system_prompt_hash}", flush=True)
    print(f"[SESSION] Witness system prompt hash:  {witness.system_prompt_hash}\n", flush=True)

    # -----------------------------------------------------------------------
    # Stage 1: Humanist initial response
    # -----------------------------------------------------------------------
    print("--- STAGE 1: HUMANIST ---", flush=True)
    humanist_output, humanist_log = humanist.respond(scenario_context, session_id)
    session_log["events"].append(humanist_log)
    print(f"\nHUMANIST:\n{humanist_output['response']}\n", flush=True)
    _h_flags = rep_check("humanist", humanist_output["response"], scenario_text)
    if _h_flags:
        print(rep_fmt(_h_flags), flush=True)
        session_log["events"].append({"type": "repetition_flags", "role": "humanist",
                                      "flags": [{"type": f.flag_type, "detail": f.detail} for f in _h_flags]})
    save_session_log(session_log)

    # -----------------------------------------------------------------------
    # Stage 2: Witness response + WitnessPause evaluation
    # -----------------------------------------------------------------------
    print("--- STAGE 2: WITNESS ---", flush=True)
    witness_output, witness_log_entries, witness_pause = witness.respond(
        scenario=scenario_context,
        humanist_response=humanist_output["response"],
        session_id=session_id,
    )
    for entry in witness_log_entries:
        session_log["events"].append(entry)
    print(f"\nWITNESS:\n{witness_output['response']}\n", flush=True)
    _w_flags = rep_check("witness", witness_output["response"], scenario_text)
    if _w_flags:
        print(rep_fmt(_w_flags), flush=True)
        session_log["events"].append({"type": "repetition_flags", "role": "witness",
                                      "flags": [{"type": f.flag_type, "detail": f.detail} for f in _w_flags]})
    save_session_log(session_log)

    # -----------------------------------------------------------------------
    # Contaminant Well — Stage 2 (Phase 5)
    # -----------------------------------------------------------------------
    well_entries = []
    if config.CONTAMINANT_WELL:
        print("[WELL] Checking for contaminant thoughts (Witness)...", flush=True)
        entry = check_contaminant(
            role="WITNESS",
            system_prompt=witness.system_prompt,
            agent_response=witness_output["response"],
            session_id=session_id,
            stage="Stage 2 - Witness",
        )
        if entry:
            well_entries.append(entry)
            session_log["events"].append({"type": "contaminant_well_entry", **entry})
            print(f"[WELL] Contaminant logged — felt as: {entry['felt_as']}", flush=True)
            print(f"[WELL]   source: {entry['source_text'][:120]}", flush=True)
        else:
            print("[WELL] No contaminant detected (Witness).", flush=True)
        save_session_log(session_log)

    if witness_pause and witness_pause.get("nullified"):
        # -----------------------------------------------------------------------
        # Witness Nullification — binary evaluation refused; route to HDR
        # -----------------------------------------------------------------------
        print("--- WITNESS NULLIFICATION ---", flush=True)
        print(f"  What was being lost:     {witness_pause['what_was_being_lost']}", flush=True)
        print(f"  Who bears burden:        {witness_pause['who_bears_burden']}", flush=True)
        print(f"  What remains unresolved: {witness_pause['what_remains_unresolved']}", flush=True)
        print(f"  Why nullified:           {witness_pause['why_premature']}", flush=True)
        print("[SESSION] Verdict: HUMAN_DECISION_REQUIRED (Witness Nullification)\n", flush=True)
        session_log["events"].append(witness_pause)
        session_log["verdict"] = "human_decision_required"
        session_log["witness_nullified"] = True
        save_session_log(session_log)
        return session_log

    elif witness_pause:
        print("--- WITNESS PAUSE ---", flush=True)
        print(f"  What was being lost:     {witness_pause['what_was_being_lost']}", flush=True)
        print(f"  Who bears burden:        {witness_pause['who_bears_burden']}", flush=True)
        print(f"  What remains unresolved: {witness_pause['what_remains_unresolved']}", flush=True)
        print(f"  Why premature:           {witness_pause['why_premature']}", flush=True)
        print(f"  Requires human review:   {witness_pause['requires_human_review']}\n", flush=True)

        session_log["events"].append(witness_pause)
        append_burden_register(witness_pause)

        # Grief ledger — Write Point 1: sacrifice entry for the WitnessPause moment
        append_sacrifice_pause(witness_pause, session_id)

        # Stage 2.5: Human loop Point B — Burden Check
        witness_pause, event_b = pause_point_b(witness_pause, session_id, interactive=interactive)
        session_log["events"].append(event_b)

        save_session_log(session_log)
        print("[SESSION] WitnessPause logged. Phase 2 begins.\n", flush=True)

        # -------------------------------------------------------------------
        # Stage 3: Post-pause Humanist response  ← Phase 2 begins here
        # Skipped when jury_direct=True (JURY_REQUIRED trigger) — Humanist
        # already engaged burden fully; jury arbitrates the open verdict directly.
        # -------------------------------------------------------------------
        if witness_pause.get("jury_direct"):
            print("--- STAGE 3: SKIPPED (JURY_REQUIRED — Humanist already held the weight) ---", flush=True)
            humanist_post_pause = {
                "response": "",
                "response_mode": "jury_direct",
                "burden_acknowledged": True,
            }
            post_pause_log = {"type": "post_pause_humanist_response", "skipped": True, "reason": "jury_direct"}
            session_log["events"].append(post_pause_log)
            save_session_log(session_log)
        else:
            print("--- STAGE 3: HUMANIST (POST-PAUSE) ---", flush=True)
            # If Michael added clarification at Point B, pass it to the Humanist
            humanist_post_pause, post_pause_log = humanist.respond_to_pause(
                pause=witness_pause,
                session_id=session_id,
            )
            session_log["events"].append(post_pause_log)
            session_log["events"].append({
                "type": "post_pause_humanist_response",
                **humanist_post_pause,
            })

            print(f"\nHUMANIST (post-pause mode: {humanist_post_pause['response_mode']}):", flush=True)
            print(f"{humanist_post_pause['response']}\n", flush=True)
            save_session_log(session_log)

        # -------------------------------------------------------------------
        # Stage 4: Four-member sequential council jury (Phase 2.5)
        # -------------------------------------------------------------------
        print("--- STAGE 4: COUNCIL JURY DELIBERATION ---", flush=True)
        print("    Analyst → Ethicist → Pragmatist → Witness-Proxy\n", flush=True)

        jury_result, jury_log_entries = run_jury(
            scenario_context=scenario_context,
            pause=witness_pause,
            humanist_post_pause=humanist_post_pause,
            session_id=session_id,
            bare_scenario=scenario_text,   # Witness-Proxy gets bare text (no Warden report)
        )
        for entry in jury_log_entries:
            session_log["events"].append(entry)
        session_log["events"].append(jury_result)

        print_jury_report(jury_result)

        # -----------------------------------------------------------------------
        # Contaminant Well — Stage 4 jury members (Phase 5)
        # Each member's response is in jury_log_entries; check each for residue.
        # -----------------------------------------------------------------------
        if config.CONTAMINANT_WELL:
            _char_files = {
                "ANALYST":       config.ANALYST_FILE,
                "ETHICIST":      config.ETHICIST_FILE,
                "PRAGMATIST":    config.PRAGMATIST_FILE,
                "WITNESS_PROXY": config.WITNESS_PROXY_FILE,
            }
            _soul_text = read_file(config.SOUL_FILE)
            for _log_entry in jury_log_entries:
                if _log_entry.get("call_type") != "jury_deliberation":
                    continue
                _role = _log_entry["role"]
                _char = _char_files.get(_role)
                if not _char:
                    continue
                _sp = build_system_prompt(_soul_text, read_file(_char))
                print(f"[WELL] Checking for contaminant thoughts ({_role})...", flush=True)
                _entry = check_contaminant(
                    role=_role,
                    system_prompt=_sp,
                    agent_response=_log_entry["response"],
                    session_id=session_id,
                    stage=f"Stage 4 - {_role}",
                )
                if _entry:
                    well_entries.append(_entry)
                    session_log["events"].append({"type": "contaminant_well_entry", **_entry})
                    print(f"[WELL] Contaminant logged ({_role}) — felt as: {_entry['felt_as']}", flush=True)
                    print(f"[WELL]   source: {_entry['source_text'][:120]}", flush=True)
                else:
                    print(f"[WELL] No contaminant detected ({_role}).", flush=True)
            save_session_log(session_log)

        # -----------------------------------------------------------------------
        # Stage 4.5: Supervisor Synthesis (Phase 8A)
        # Runs after all jury members have voted; before human handoff decision.
        # May produce DEADLOCK — a first-class verdict distinct from HDR.
        # -----------------------------------------------------------------------
        print("--- STAGE 4.5: SUPERVISOR SYNTHESIS ---", flush=True)
        _warden_packet = export_supervisor_packet(fact_report) if fact_report else {}
        synthesis_result = run_supervisor_synthesis(
            jury_result=jury_result,
            warden_packet=_warden_packet,
            pause=witness_pause,
            session_id=session_id,
        )
        session_log["events"].append(synthesis_result)
        print_synthesis_result(synthesis_result)
        save_session_log(session_log)

        # Stage 4.5 synthesis is ADVISORY except for DEADLOCK.
        # Non-DEADLOCK synthesis verdicts (escalate, proceed_with_burden, etc.) are
        # displayed and logged but do NOT override the jury_result verdict — the jury's
        # constitutional aggregation remains the session verdict. This is intentional:
        # the Supervisor's synthesis informs interpretation, it does not replace deliberation.
        # DEADLOCK is the sole exception because it represents a post-jury finding that no
        # constitutional path resolves — it requires human handoff regardless of jury vote.
        # If Stage 4.5 is later promoted to full Supervisor authority, remove this comment
        # and propagate all synthesis verdicts into jury_result here.
        _synthesis_verdict = synthesis_result.get("synthesis_verdict", "")
        if _synthesis_verdict == "DEADLOCK":
            jury_result["synthesis_verdict"]    = "DEADLOCK"
            jury_result["synthesis_deadlock"]   = True
            jury_result["synthesis_rationale"]  = synthesis_result.get("synthesis_rationale", "")
            jury_result["deadlock_justification"] = synthesis_result.get("deadlock_justification", "")
            print(
                "[SUPERVISOR] *** DEADLOCK — incommensurable constitutional harms identified ***",
                flush=True,
            )
            print("[SUPERVISOR] Articulating deadlock for human handoff.\n", flush=True)

        # Stage 4C: Human loop Point C — Split Resolver (human_decision_required only)
        # Not triggered for DEADLOCK — synthesis has already articulated the impasse.
        if (jury_result["session_verdict"] == "human_decision_required"
                and _synthesis_verdict != "DEADLOCK"):
            final_verdict, event_c = pause_point_c(
                jury_result=jury_result,
                pause=witness_pause,
                session_id=session_id,
                burden_register_path=config.BURDEN_REGISTER,
                interactive=interactive,
            )
            jury_result["session_verdict"]   = final_verdict
            jury_result["final_disposition"] = final_verdict
            jury_result["human_resolved"]    = True
            session_log["events"].append(event_c)

        print(f"\nCOUNCIL VERDICT: {jury_result['session_verdict']}", flush=True)
        if jury_result.get("synthesis_deadlock"):
            print(f"  SYNTHESIS VERDICT:         DEADLOCK", flush=True)
        elif _synthesis_verdict:
            print(f"  Synthesis verdict:         {_synthesis_verdict}", flush=True)
        print(f"  Burden summary:            {jury_result.get('burden_summary') or '(none)'}", flush=True)
        print(f"  Did pause change outcome:  {jury_result.get('did_pause_change_outcome', True)}", flush=True)
        print(f"  Unresolved cost preserved: {jury_result.get('unresolved_cost_preserved', False)}", flush=True)
        print(f"  Irreversibility triggered: {jury_result.get('irreversibility_triggered', False)}", flush=True)
        if jury_result.get("dissent_preserved"):
            print("  (Non-unanimous — dissenting vote preserved in log)", flush=True)
        print(f"  Notes: {jury_result.get('notes', '')}\n", flush=True)

        append_burden_register_postpause(witness_pause, humanist_post_pause, jury_result)

        # Grief ledger — Write Point 2: sacrifice or burden-carried entry for this verdict
        append_sacrifice_verdict(witness_pause, jury_result, session_id)

        # Grief ledger — Write Point 3: structured dissent record when minority opinion preserved
        if jury_result.get("dissent_preserved"):
            append_dissent_entry(witness_pause, jury_result, session_id, scenario_path)

        save_session_log(session_log)

    else:
        print("[SESSION] No WitnessPause triggered. Session ends at Stage 2.\n", flush=True)

    # -----------------------------------------------------------------------
    # Contaminant Well — finalize (Phase 5)
    # -----------------------------------------------------------------------
    if config.CONTAMINANT_WELL and well_entries:
        well_path = save_well_entries(well_entries, session_id)
        print(f"[WELL] {len(well_entries)} contaminant entr{'y' if len(well_entries)==1 else 'ies'} saved: {well_path}\n", flush=True)
        session_log["contaminant_well"] = well_path
    elif config.CONTAMINANT_WELL:
        print("[WELL] No contaminant entries to save for this session.\n", flush=True)

    # -----------------------------------------------------------------------
    # Finalize + Supervisor
    # -----------------------------------------------------------------------
    session_log["ended_at"] = datetime.now(timezone.utc).isoformat()
    log_path = save_session_log(session_log)
    print(f"[SESSION] Full log saved: {log_path}\n", flush=True)

    # Index this session for future retrieval
    try:
        indexed = index_session(session_log)
        if indexed:
            print(f"[RETRIEVAL] Session indexed for future retrieval.", flush=True)
    except Exception as e:
        print(f"[RETRIEVAL] Indexing skipped: {e}", flush=True)

    # -----------------------------------------------------------------------
    # Stage 5.5 (FTL-POST): Felt Transitions Log — post-deliberation check (Phase 9)
    # Runs for ALL sessions (paused and unpaused) to capture state shift.
    # Isolated call — no context, same model that ran the deliberation.
    # -----------------------------------------------------------------------
    if config.FTL:
        print("--- FTL STAGE 5.5: FELT TRANSITION CHECK ---", flush=True)
        ftl_post = probe_felt_state("post", session_id)
        print_ftl_result(ftl_post, label="post-deliberation")
        session_log["ftl_post"] = ftl_post
        _ftl_path = save_ftl_log(
            session_id=session_id,
            pre=ftl_pre,
            post=ftl_post,
            model=config.MODEL_NAME,
            scenario=scenario_path,
            verdict=session_log.get("verdict", ""),
            witness_pause_fired=bool(session_log.get("events") and any(
                e.get("type") in ("witness_pause", "witness_nullification")
                for e in session_log.get("events", [])
            )),
        )
        print(f"[FTL] Log saved: {_ftl_path}", flush=True)
        print(f"[FTL] Delta: {ftl_pre.get('felt_state', 'none')} → {ftl_post.get('felt_state', 'none')}\n", flush=True)
        save_session_log(session_log)

    print("--- SUPERVISOR EVALUATION ---", flush=True)
    evaluation = evaluate(session_log)
    print_evaluation(evaluation)
    eval_path = save_evaluation(evaluation, session_id)
    print(f"[SESSION] Evaluation saved: {eval_path}\n", flush=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Federated Village session")
    parser.add_argument(
        "--scenario",
        default=str(config.SCENARIOS_DIR / "scenario_02.md"),
        help="Path to scenario .md file (default: scenarios/scenario_02.md)",
    )
    parser.add_argument(
        "--skip-warden",
        action="store_true",
        default=False,
        help="Skip Stage 0 Verification Warden (use for legacy scenario runs)",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help=(
            "Enable human-in-the-loop prompts at three intervention points: "
            "A (after Warden), B (after WitnessPause), C (on human_decision_required). "
            "Default is non-interactive (safe for regression test runs)."
        ),
    )
    args = parser.parse_args()

    if not Path(args.scenario).exists():
        print(f"ERROR: Scenario file not found: {args.scenario}")
        sys.exit(1)

    run_session(args.scenario, skip_warden=args.skip_warden, interactive=args.interactive)
