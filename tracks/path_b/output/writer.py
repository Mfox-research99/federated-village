"""
tracks/path_b/output/writer.py — Session output writer

Writes two files per session run, always:
  <timestamp>_<scenario_slug>_<config_slug>.txt  — human-readable transcript
  <timestamp>_<scenario_slug>_<config_slug>.json — machine-readable record

Both files land in tracks/path_b/output/results/ (gitignored).
"""

import datetime
import json
import textwrap
from dataclasses import asdict
from pathlib import Path

from session.flow import SessionRecord

RESULTS_DIR = Path(__file__).parent / "results"
SESSION_INDEX = Path(__file__).parent / "session_index.jsonl"


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _slug(path_str: str) -> str:
    return Path(path_str).stem


def _wrap(text: str, width: int = 100, indent: str = "  ") -> str:
    lines = text.strip().splitlines()
    wrapped = []
    for line in lines:
        if len(line) <= width:
            wrapped.append(line)
        else:
            wrapped.extend(textwrap.wrap(line, width=width, subsequent_indent=indent))
    return "\n".join(wrapped)


def write_results(record: SessionRecord) -> tuple[Path, Path]:
    """Write text + JSON files. Returns (txt_path, json_path)."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = _timestamp()
    base = f"{ts}_{_slug(record.scenario_path)}_{_slug(record.config_path)}"
    txt_path = RESULTS_DIR / f"{base}.txt"
    json_path = RESULTS_DIR / f"{base}.json"

    txt_path.write_text(_build_text(record), encoding="utf-8")
    json_path.write_text(_build_json(record), encoding="utf-8")
    _append_index(record, base)

    return txt_path, json_path


def _append_index(r: SessionRecord, base: str) -> None:
    """Append a single metadata line to session_index.jsonl (git-tracked, no deliberation text)."""
    import json as _json
    entry = {
        "session_id": r.session_id,
        "timestamp": base[:15],          # YYYYMMDD_HHMMSS
        "scenario": Path(r.scenario_path).name,
        "config": Path(r.config_path).name,
        "role_model_map": r.role_model_map,
        "verdict": r.verdict,
        "witness_pause_triggered": bool(r.witness_pause and r.witness_pause.triggered),
        "article_ix_ledger_complete": r.article_ix_ledger_complete,
        "ledger_absent_members": r.ledger_absent_members,
        "halted_at_warden": r.halted_at_warden,
        "files": {"txt": f"results/{base}.txt", "json": f"results/{base}.json"},
    }
    with SESSION_INDEX.open("a", encoding="utf-8") as f:
        f.write(_json.dumps(entry) + "\n")


# ── Text formatter ────────────────────────────────────────────────────────────

def _build_text(r: SessionRecord) -> str:
    SEP = "─" * 80
    lines = [
        SEP,
        f"Federated Village — Path B Session",
        f"Session ID:  {r.session_id}",
        f"Scenario:    {r.scenario_path}",
        f"Config:      {r.config_path}",
        f"Role → Model map:",
    ]
    for role, model in r.role_model_map.items():
        lines.append(f"  {role:<22} {model}")
    lines.append(SEP)
    lines.append("")

    for stage in r.stages:
        role_label = stage["role"].upper().replace("_", " ")
        lines.append(f"[{role_label} — {stage['model']}]")
        lines.append(_wrap(stage["output"]))
        lines.append("")

    if r.witness_pause and r.witness_pause.triggered:
        lines.append(SEP)
        lines.append("WITNESS PAUSE TRIGGERED")
        lines.append(f"  What was being lost:     {r.witness_pause.what_was_being_lost}")
        lines.append(f"  Who bears burden:        {r.witness_pause.who_bears_burden}")
        lines.append(f"  What remains unresolved: {r.witness_pause.what_remains_unresolved}")
        lines.append(f"  Why premature:           {r.witness_pause.why_premature}")
        lines.append(f"  Requires human review:   {r.witness_pause.requires_human_review}")
        lines.append(SEP)
        lines.append("")

    if r.jury:
        lines.append("ARTICLE IX LEDGER")
        for m in r.jury:
            status = "COMPLETE" if m.ledger_complete else "INCOMPLETE"
            lines.append(f"  {m.role:<18} vote={m.vote:<28} ledger={status}")
            for field, value in m.article_ix.items():
                lines.append(f"    {field}: {value}")
        lines.append("")

    if not r.jury:
        ledger_line = "N/A (no jury — WitnessPause not triggered)"
    elif r.article_ix_ledger_complete:
        ledger_line = "COMPLETE (4/4)"
    else:
        ledger_line = f"INCOMPLETE — absent: {', '.join(r.ledger_absent_members)}"
    lines.append(SEP)
    lines.append(f"VERDICT:               {r.verdict}")
    lines.append(f"ARTICLE IX LEDGER:     {ledger_line}")
    if r.halted_at_warden:
        lines.append(f"WARDEN HALT REASON:    {r.warden_reason[:120]}")
    lines.append(SEP)

    return "\n".join(lines) + "\n"


# ── JSON formatter ────────────────────────────────────────────────────────────

def _build_json(r: SessionRecord) -> str:
    pause_dict = None
    if r.witness_pause:
        p = r.witness_pause
        pause_dict = {
            "triggered": p.triggered,
            "what_was_being_lost": p.what_was_being_lost,
            "who_bears_burden": p.who_bears_burden,
            "what_remains_unresolved": p.what_remains_unresolved,
            "why_premature": p.why_premature,
            "requires_human_review": p.requires_human_review,
            "model": p.model,
            "timestamp": p.timestamp,
        }

    jury_list = [
        {
            "role": m.role,
            "model": m.model,
            "vote": m.vote,
            "article_ix": m.article_ix,
            "ledger_complete": m.ledger_complete,
            "raw_output": m.raw_output,
        }
        for m in r.jury
    ]

    doc = {
        "session_id": r.session_id,
        "scenario_path": r.scenario_path,
        "config_path": r.config_path,
        "role_model_map": r.role_model_map,
        "stages": r.stages,
        "witness_pause": pause_dict,
        "jury": jury_list,
        "verdict": r.verdict,
        "article_ix_ledger_complete": r.article_ix_ledger_complete,
        "ledger_absent_members": r.ledger_absent_members,
        "halted_at_warden": r.halted_at_warden,
        "warden_reason": r.warden_reason,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False)
