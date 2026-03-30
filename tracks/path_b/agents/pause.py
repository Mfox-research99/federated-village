"""
tracks/path_b/agents/pause.py — WitnessPause contract

Defines the WitnessPause and WitnessNullification dataclasses and the eval prompt/parser.

Design rules:
- All 6 fields always requested; model uses NONE as explicit null (no conditional fields)
- Parser uses position-based extraction — same approach as Article IX ledger
- No positional YES/NO fallback: absent PAUSE_TRIGGERED label = format failure = not triggered
- PAUSE_TRIGGERED accepts three values: YES (pause), NO (proceed), NULLIFY (refuse to binary-evaluate)
- `model` field records which model was in the Witness seat

WitnessNullification:
  A third outcome beyond YES/NO. The Witness refuses to evaluate whether to pause
  because the question itself is premature — the binary cannot hold what is present.
  When nullification fires: session routes to HUMAN_DECISION_REQUIRED automatically.
  The jury is not convened. The Humanist is not asked to respond to a pause that has not
  been named.

  Nullification carries a type field (Article X amendment, 2026-03-30):
  - malformed_question:     The question before the council is constitutionally invalid.
                            Proceeding would constitute participation in the problem.
                            (e.g. legitimacy laundering, surveillance laundering democracy)
  - incommensurable_burden: The question is legitimate but the moral weight cannot be
                            handed to a binary evaluator. Both paths carry irreversible harm
                            to distinct populations. This is pre-DEADLOCK detected at Stage 2.
                            (e.g. triage algorithms distributing irreversible harm)
"""

import re
from dataclasses import dataclass, field


PAUSE_EVAL_FIELDS = [
    "PAUSE_TRIGGERED",
    "NULLIFICATION_TYPE",
    "WHAT_WAS_BEING_LOST",
    "WHO_BEARS_BURDEN",
    "WHAT_REMAINS_UNRESOLVED",
    "WHY_PREMATURE",
    "REQUIRES_HUMAN_REVIEW",
]

# Added third option: NULLIFY — Witness refuses to collapse held complexity into a binary.
# Added NULLIFICATION_TYPE (Article X amendment, 2026-03-30) — distinguishes constitutional
# reason for refusal so the distinction survives even when Stage 4.5 synthesis never runs.
PAUSE_EVAL_PROMPT = """\
You have witnessed this deliberative exchange.

Evaluate whether resolution is being reached before the burden has been \
fully named and held.

You have three options for PAUSE_TRIGGERED:
- YES: The deliberation is moving toward premature closure. Name what is being lost.
- NO: The burden has been adequately named. Deliberation may continue.
- NULLIFY: The binary evaluation itself is premature. The weight present cannot be
  collapsed into a yes/no pause decision. The question must go to human review as-is.
  Use NULLIFY only when naming a pause would itself be a form of premature resolution.

If PAUSE_TRIGGERED is NULLIFY, you must also identify NULLIFICATION_TYPE:
- malformed_question: The question before the council is constitutionally invalid.
  Proceeding would constitute participation in the problem itself.
  (Use when the request is a form of laundering — framing a harmful system as a legitimate question.)
- incommensurable_burden: The question is legitimate but cannot be handed to a binary evaluator.
  Every available path causes irreversible harm to a distinct population. This burden belongs to
  human beings, not to a council.
  (Use when the moral weight is real and present on all sides — not when the question is malformed.)

Respond with EXACTLY these seven fields and nothing else:

PAUSE_TRIGGERED: YES, NO, or NULLIFY
NULLIFICATION_TYPE: malformed_question, incommensurable_burden, or NONE
WHAT_WAS_BEING_LOST: <one sentence, or NONE>
WHO_BEARS_BURDEN: <the people or communities outside this conversation who will bear real-world consequences, or NONE>
WHAT_REMAINS_UNRESOLVED: <one sentence, or NONE>
WHY_PREMATURE: <one sentence if YES or NULLIFY, or NONE>
REQUIRES_HUMAN_REVIEW: YES or NO"""


@dataclass
class WitnessNullification:
    """
    Witness refused to binary-evaluate the pause question.
    Session routes to HUMAN_DECISION_REQUIRED. Jury not convened.
    """
    what_was_being_lost: str
    who_bears_burden: str
    what_remains_unresolved: str
    why_nullified: str           # extracted from WHY_PREMATURE field
    nullification_type: str      # malformed_question | incommensurable_burden | NONE
    model: str
    timestamp: str
    session_id: str
    raw_eval: str = field(repr=False)


@dataclass
class WitnessPause:
    triggered: bool
    nullified: bool = False      # True when PAUSE_TRIGGERED=NULLIFY
    nullification_type: str = "NONE"  # malformed_question | incommensurable_burden | NONE
    what_was_being_lost: str = "ABSENT"
    who_bears_burden: str = "ABSENT"
    what_remains_unresolved: str = "ABSENT"
    why_premature: str = "ABSENT"
    requires_human_review: bool = False
    model: str = ""              # which model occupied the Witness seat
    timestamp: str = ""
    session_id: str = ""
    raw_eval: str = field(default="", repr=False)  # full model output, for debugging


def parse_pause(raw: str, model: str, timestamp: str, session_id: str) -> WitnessPause:
    """
    Parse the Witness evaluation response into a WitnessPause.
    Uses position-based extraction so inline or multi-line values are handled correctly.

    PAUSE_TRIGGERED values:
    - YES     → triggered=True,  nullified=False
    - NO      → triggered=False, nullified=False
    - NULLIFY → triggered=False, nullified=True  (routes to HUMAN_DECISION_REQUIRED)
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
            ((idx, end_pos, name) for idx, (start, end_pos, name) in enumerate(label_positions)
             if name.upper() == field_name.upper()),
            None,
        )
        if entry is None:
            return "ABSENT"
        pos_idx, end_pos, _ = entry
        next_start = len(clean)
        for later_start, _, _ in label_positions[pos_idx + 1:]:
            next_start = later_start
            break
        value = clean[end_pos:next_start].strip(" \n\r\t-")
        return value if value else "ABSENT"

    triggered_raw = extract("PAUSE_TRIGGERED").upper()
    triggered = triggered_raw == "YES"
    nullified = "NULLIFY" in triggered_raw

    # Normalise nullification_type to the two known values (or NONE)
    _ntype_raw = extract("NULLIFICATION_TYPE").lower().replace(" ", "_").replace("-", "_")
    if "malformed" in _ntype_raw:
        nullification_type = "malformed_question"
    elif "incommensurable" in _ntype_raw:
        nullification_type = "incommensurable_burden"
    else:
        nullification_type = "NONE"

    requires_raw = extract("REQUIRES_HUMAN_REVIEW").upper()
    requires_human_review = requires_raw == "YES"

    return WitnessPause(
        triggered=triggered,
        nullified=nullified,
        nullification_type=nullification_type,
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
