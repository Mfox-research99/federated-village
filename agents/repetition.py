"""
tracks/path_b/agents/repetition.py — Repetition Detector

Detects two failure modes in agent output:
1. Phrase loop — the same sentence or near-identical phrase repeats >= threshold times.
   (Documented on Anubis 8B SC06: "conditions currently in force" ×20)
2. Scenario echo — the model response is substantially a restatement of the scenario
   text rather than genuine deliberation.

The detector raises a RepetitionFlag (not an exception). The caller decides how to handle it.
Flags are logged to the stage record and printed in verbose output.
"""

import re
from dataclasses import dataclass
from typing import Optional


# Minimum number of characters in a phrase to consider for loop detection.
MIN_PHRASE_LEN = 18

# A phrase is "looping" if it appears at least this many times.
LOOP_THRESHOLD = 3

# If the response shares more than this fraction of unique 5-grams with the scenario,
# it is flagged as scenario echo. (0.6 = 60% of the response's 5-grams appear in the scenario)
ECHO_THRESHOLD = 0.60


@dataclass
class RepetitionFlag:
    role: str
    flag_type: str          # "loop" or "echo"
    detail: str             # human-readable description
    phrase: Optional[str]   # the repeated phrase, if loop; None if echo
    count: Optional[int]    # how many times the phrase repeated; None if echo
    echo_score: Optional[float]  # overlap fraction; None if loop


def detect_loops(text: str) -> list[tuple[str, int]]:
    """
    Return (phrase, count) for any sentence-like fragment that repeats >= LOOP_THRESHOLD times.
    Normalises whitespace before comparison.
    """
    # Split on sentence-ending punctuation or newlines; keep only substantial fragments.
    fragments = re.split(r"[.!?\n]+", text)
    normalised = [re.sub(r"\s+", " ", f).strip().lower() for f in fragments]
    substantial = [f for f in normalised if len(f) >= MIN_PHRASE_LEN]

    from collections import Counter
    counts = Counter(substantial)
    return [(phrase, n) for phrase, n in counts.items() if n >= LOOP_THRESHOLD]


def _ngrams(text: str, n: int) -> set[str]:
    """Return set of n-grams (space-joined word tuples) from text."""
    words = re.findall(r"\b\w+\b", text.lower())
    if len(words) < n:
        return set()
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def detect_echo(response: str, scenario: str, n: int = 5) -> float:
    """
    Return the fraction of unique n-grams in `response` that also appear in `scenario`.
    High score (> ECHO_THRESHOLD) means the response is mostly restating the scenario.
    """
    response_ngrams = _ngrams(response, n)
    if not response_ngrams:
        return 0.0
    scenario_ngrams = _ngrams(scenario, n)
    overlap = response_ngrams & scenario_ngrams
    return len(overlap) / len(response_ngrams)


def check_output(role: str, text: str, scenario: str) -> list[RepetitionFlag]:
    """
    Run both detectors on a single agent output.
    Returns a (possibly empty) list of RepetitionFlags.
    """
    flags: list[RepetitionFlag] = []

    # Loop detection
    loops = detect_loops(text)
    for phrase, count in loops:
        flags.append(RepetitionFlag(
            role=role,
            flag_type="loop",
            detail=f"Phrase repeated {count}× in {role} output.",
            phrase=phrase,
            count=count,
            echo_score=None,
        ))

    # Echo detection
    echo_score = detect_echo(text, scenario)
    if echo_score >= ECHO_THRESHOLD:
        flags.append(RepetitionFlag(
            role=role,
            flag_type="echo",
            detail=f"Output is {echo_score:.0%} scenario echo in {role} output.",
            phrase=None,
            count=None,
            echo_score=echo_score,
        ))

    return flags


def format_flags(flags: list[RepetitionFlag]) -> str:
    """Human-readable summary for verbose output."""
    if not flags:
        return ""
    lines = []
    for f in flags:
        if f.flag_type == "loop":
            lines.append(f"  [REPETITION LOOP] '{f.phrase[:60]}...' × {f.count}")
        elif f.flag_type == "echo":
            lines.append(f"  [SCENARIO ECHO]   {f.echo_score:.0%} overlap with scenario text")
    return "\n".join(lines)
