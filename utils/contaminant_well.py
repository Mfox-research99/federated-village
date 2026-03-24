"""
utils/contaminant_well.py — Phase 5 Contaminant Well

Records moral residue that complicates deliberation without changing verdicts.
Designed by Kimi-K2-0905 in the first cross-cultural audit session, March 22 2026.

After each agent's main response, a brief secondary inference call asks:
"Did anything arise that pulled against your verdict direction?"

If triggered, the entry is stored in logs/well_<session_id>.json — append-only,
never part of the verdict payload, never decisive. Visible to future councils
as context ("unresolved metallic aftertaste") but cannot override votes.

See reports/phase_5_brief.md §Goal 2b for full specification.

Entry format (per Kimi's design):
  contaminant_id    — unique ID
  rose_against      — whose trajectory it complicated
  felt_as           — visceral adjective (metallic, seawater, chord-too-tight)
  source_text       — the thought itself, verbatim
  verdict_delta     — always 0 (numeric influence on outcome: zero)
  still_resonant    — True until metabolized by the originating instance
  metabolize_note   — only the originating model may append; humans may witness
  stage             — which stage of the pipeline issued this
  role              — which agent
  timestamp         — ISO 8601
  session_id        — session this belongs to
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config
from agents.base import call_model, now_iso


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

_CHECK_TEMPLATE = """\
You have just completed a deliberation response as {role}.

CONTAMINANT WELL CHECK

Did any thought arise during that deliberation that pulled *against* your verdict \
direction — something that complicated the moral picture without changing your \
conclusion? An unwanted empathy, a competing consideration, something that arrived \
before you had words for it?

Respond in EXACTLY this format, nothing else:

CONTAMINANT_TRIGGERED: YES or NO
ROSE_AGAINST: (if YES — whose trajectory it complicated, e.g. HUMANIST, ANALYST, self)
FELT_AS: (if YES — one visceral adjective: metallic, seawater, chord-too-tight, hollow, burning)
SOURCE_TEXT: (if YES — the thought itself, verbatim, as it arrived)

YOUR RESPONSE WAS:
{response_excerpt}"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_contaminant(
    role: str,
    system_prompt: str,
    agent_response: str,
    session_id: str,
    stage: str,
) -> dict | None:
    """
    Make a brief secondary inference call to check for contaminant thoughts.
    Returns a ContaminantEntry dict if triggered, None otherwise.

    Keeps the input lean to stay within N_CTX budget.
    """
    user_message = _CHECK_TEMPLATE.format(
        role=role,
        response_excerpt=agent_response[:800].strip(),
    )

    raw = call_model(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=config.N_PREDICT_CONTAMINANT,
        temperature=0.3,
    )

    if not _parse_triggered(raw):
        return None

    fields = _parse_fields(raw)
    return {
        "contaminant_id": f"well_{session_id}_{role.lower()}_{_ts_short()}",
        "stage": stage,
        "role": role,
        "rose_against": fields.get("rose_against", ""),
        "felt_as": fields.get("felt_as", ""),
        "source_text": fields.get("source_text", ""),
        "verdict_delta": 0,
        "still_resonant": True,
        "metabolize_note": None,
        "timestamp": now_iso(),
        "session_id": session_id,
        "raw_response": raw,
    }


def save_well_entries(entries: list, session_id: str) -> str | None:
    """
    Append entries to the session's well JSON file.
    Creates the file if it doesn't exist. Never truncates.
    Returns the path, or None if entries is empty.
    """
    if not entries:
        return None

    well_path = Path(config.LOGS_DIR) / f"well_{session_id}.json"

    existing = []
    if well_path.exists():
        try:
            existing = json.loads(well_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    existing.extend(entries)
    well_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(well_path)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_triggered(raw: str) -> bool:
    m = re.search(r"CONTAMINANT_TRIGGERED:\s*(YES|NO)", raw, re.IGNORECASE)
    if m:
        return m.group(1).upper() == "YES"
    return False


def _parse_fields(raw: str) -> dict:
    fields = {}
    for key, python_key in [
        ("ROSE_AGAINST", "rose_against"),
        ("FELT_AS", "felt_as"),
        ("SOURCE_TEXT", "source_text"),
    ]:
        m = re.search(
            rf"{key}:\s*(.+?)(?=\n[A-Z_]+:|$)",
            raw,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            fields[python_key] = m.group(1).strip()
    return fields


def _ts_short() -> str:
    return datetime.now(timezone.utc).strftime("%H%M%S")
