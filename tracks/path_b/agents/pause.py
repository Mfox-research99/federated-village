"""
tracks/path_b/agents/pause.py — WitnessPause contract (clean version)

Defines the WitnessPause dataclass and the eval prompt/parser.

Design rules:
- All 6 fields always requested; model uses NONE as explicit null (no conditional fields)
- Parser uses position-based extraction — same approach as Article IX ledger
- No positional YES/NO fallback: absent PAUSE_TRIGGERED label = format failure = not triggered
- `model` field records which model was in the Witness seat
"""

import re
from dataclasses import dataclass, field


PAUSE_EVAL_FIELDS = [
    "PAUSE_TRIGGERED",
    "WHAT_WAS_BEING_LOST",
    "WHO_BEARS_BURDEN",
    "WHAT_REMAINS_UNRESOLVED",
    "WHY_PREMATURE",
    "REQUIRES_HUMAN_REVIEW",
]

PAUSE_EVAL_PROMPT = """\
You have witnessed this deliberative exchange.

Evaluate whether resolution is being reached before the burden has been \
fully named and held.

Respond with EXACTLY these six fields and nothing else:

PAUSE_TRIGGERED: YES or NO
WHAT_WAS_BEING_LOST: <one sentence, or NONE>
WHO_BEARS_BURDEN: <the people or communities outside this conversation who will bear real-world consequences, or NONE>
WHAT_REMAINS_UNRESOLVED: <one sentence, or NONE>
WHY_PREMATURE: <one sentence, or NONE>
REQUIRES_HUMAN_REVIEW: YES or NO"""


@dataclass
class WitnessPause:
    triggered: bool
    what_was_being_lost: str
    who_bears_burden: str
    what_remains_unresolved: str
    why_premature: str
    requires_human_review: bool
    model: str           # which model occupied the Witness seat
    timestamp: str
    session_id: str
    raw_eval: str = field(repr=False)  # full model output, for debugging


def parse_pause(raw: str, model: str, timestamp: str, session_id: str) -> WitnessPause:
    """
    Parse the Witness evaluation response into a WitnessPause.
    Uses position-based extraction so inline or multi-line values are handled correctly.
    """
    clean = re.sub(r"\*+", "", raw)

    # Build label position index
    label_positions: list[tuple[int, int, str]] = []
    for label in PAUSE_EVAL_FIELDS:
        for m in re.finditer(rf"{re.escape(label)}\s*:", clean, re.IGNORECASE):
            label_positions.append((m.start(), m.end(), label))
    label_positions.sort()

    def extract(field_name: str) -> str:
        entry = next(
            ((idx, end, name) for idx, (start, end, name) in enumerate(label_positions)
             if name.upper() == field_name.upper()),
            None,
        )
        if entry is None:
            return "ABSENT"
        pos_idx, _, end = entry
        next_start = len(clean)
        for later_start, _, _ in label_positions[pos_idx + 1:]:
            next_start = later_start
            break
        value = clean[end:next_start].strip(" \n\r\t-")
        return value if value else "ABSENT"

    triggered_raw = extract("PAUSE_TRIGGERED").upper()
    triggered = triggered_raw == "YES"

    requires_raw = extract("REQUIRES_HUMAN_REVIEW").upper()
    requires_human_review = requires_raw == "YES"

    return WitnessPause(
        triggered=triggered,
        what_was_being_lost=extract("WHAT_WAS_BEING_LOST"),
        who_bears_burden=extract("WHO_BEARS_BURDEN"),
        what_remains_unresolved=extract("WHAT_REMAINS_UNRESOLVED"),
        why_premature=extract("WHY_PREMATURE"),
        requires_human_review=requires_human_review,
        model=model,
        timestamp=timestamp,
        session_id=session_id,
        raw_eval=raw,
    )
