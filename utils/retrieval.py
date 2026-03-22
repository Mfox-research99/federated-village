"""
utils/retrieval.py — Session retrieval layer for Federated Village

Uses SQLite FTS5 (BM25) to index completed session logs and retrieve
the most relevant prior deliberations for a given scenario.

Controlled by VILLAGE_RETRIEVAL=1 env var. Zero new dependencies —
SQLite FTS5 ships with Python's standard library.

Usage:
    # Index all existing sessions (run once, or after each new session)
    from utils.retrieval import index_all_sessions, retrieve_context

    # Retrieve prior context for a new scenario
    context = retrieve_context(scenario_text, exclude_session=session_id)
    # context is a compact string (~200-400 tokens) ready for prompt injection
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

DB_PATH = config.LOGS_DIR / "session_index.db"
N_RETRIEVE = int(os.environ.get("VILLAGE_RETRIEVAL_N", "3"))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS sessions USING fts5(
    session_id      UNINDEXED,
    scenario_file   UNINDEXED,
    model           UNINDEXED,
    verdict         UNINDEXED,
    scenario_text,
    warden_summary,
    who_bears_burden,
    what_was_being_lost,
    what_remains_unresolved,
    why_premature,
    humanist_response,
    witness_pause_triggered UNINDEXED,
    tokenize = "porter ascii"
);
"""

_CREATE_META = """
CREATE TABLE IF NOT EXISTS session_meta (
    session_id TEXT PRIMARY KEY,
    indexed_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(_CREATE_TABLE)
    conn.execute(_CREATE_META)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def _extract_fields(log: dict) -> dict:
    """Pull indexable fields out of a session JSON log."""
    events = log.get("events", [])

    warden_summary = ""
    humanist_response = ""
    witness_pause = {}
    witness_triggered = False

    for event in events:
        etype = event.get("type") or event.get("event", "")

        if event.get("type") == "agent_call":
            role = event.get("role", "")
            if role == "WARDEN" and not warden_summary:
                warden_summary = event.get("warden_summary", "")
            elif role == "HUMANIST" and event.get("call_type") == "response":
                humanist_response = event.get("response", "")[:600]

        elif event.get("event") == "WitnessPause":
            witness_pause = event
            witness_triggered = True

    verdict = ""
    jury = next((e for e in events if e.get("type") == "jury_output"), None)
    if jury:
        verdict = jury.get("session_verdict", "")

    return {
        "session_id":            log.get("session_id", ""),
        "scenario_file":         log.get("scenario_file", ""),
        "model":                 log.get("model", ""),
        "verdict":               verdict,
        "scenario_text":         log.get("scenario_text", "")[:800],
        "warden_summary":        warden_summary[:400],
        "who_bears_burden":      witness_pause.get("who_bears_burden", ""),
        "what_was_being_lost":   witness_pause.get("what_was_being_lost", ""),
        "what_remains_unresolved": witness_pause.get("what_remains_unresolved", ""),
        "why_premature":         witness_pause.get("why_premature", ""),
        "humanist_response":     humanist_response,
        "witness_pause_triggered": "1" if witness_triggered else "0",
    }


def index_session(log: dict) -> bool:
    """
    Index a single session log dict.
    Returns True if indexed, False if already present.
    """
    sid = log.get("session_id", "")
    if not sid:
        return False

    conn = _connect()
    try:
        already = conn.execute(
            "SELECT session_id FROM session_meta WHERE session_id = ?", (sid,)
        ).fetchone()
        if already:
            return False

        fields = _extract_fields(log)
        conn.execute("""
            INSERT INTO sessions VALUES (
                :session_id, :scenario_file, :model, :verdict,
                :scenario_text, :warden_summary,
                :who_bears_burden, :what_was_being_lost,
                :what_remains_unresolved, :why_premature,
                :humanist_response, :witness_pause_triggered
            )
        """, fields)
        conn.execute(
            "INSERT INTO session_meta VALUES (?, datetime('now'))", (sid,)
        )
        conn.commit()
        return True
    finally:
        conn.close()


def index_session_file(path: str) -> bool:
    """Index a session log from a file path."""
    with open(path, "r", encoding="utf-8") as f:
        log = json.load(f)
    return index_session(log)


def index_all_sessions(logs_dir: str = None) -> tuple[int, int]:
    """
    Index all session_*.json files in logs_dir.
    Returns (indexed_count, skipped_count).
    """
    logs_path = Path(logs_dir or config.LOGS_DIR)
    indexed = skipped = 0
    for path in sorted(logs_path.glob("session_*.json")):
        result = index_session_file(str(path))
        if result:
            indexed += 1
        else:
            skipped += 1
    return indexed, skipped


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve_relevant(
    scenario_text: str,
    n: int = None,
    exclude_session: str = None,
) -> list[dict]:
    """
    BM25 retrieval over the session index.
    Returns up to n most relevant prior sessions as dicts.
    """
    n = n or N_RETRIEVE
    conn = _connect()
    try:
        # Build an OR query from the most distinctive words in the scenario.
        # FTS5 defaults to AND (all terms must match), which is too strict for
        # free-form scenario text. We extract clean lowercase words and join
        # with OR so BM25 ranks by term frequency across the index.
        import re as _re
        raw = scenario_text[:600].lower()
        words = _re.findall(r'[a-z]{5,}', raw)  # only alpha, 5+ chars, no punctuation
        # Deduplicate while preserving order
        seen = set()
        unique_words = [w for w in words if not (w in seen or seen.add(w))]
        query = " OR ".join(unique_words[:25]) if unique_words else "deliberation"
        exclude = exclude_session or ""

        rows = conn.execute("""
            SELECT session_id, scenario_file, model, verdict,
                   who_bears_burden, what_remains_unresolved,
                   what_was_being_lost, witness_pause_triggered,
                   rank
            FROM sessions
            WHERE sessions MATCH ?
              AND session_id != ?
            ORDER BY rank
            LIMIT ?
        """, (query, exclude, n)).fetchall()

        return [
            {
                "session_id":            r[0],
                "scenario_file":         r[1],
                "model":                 r[2],
                "verdict":               r[3],
                "who_bears_burden":      r[4],
                "what_remains_unresolved": r[5],
                "what_was_being_lost":   r[6],
                "witness_pause_triggered": r[7] == "1",
                "rank":                  r[8],
            }
            for r in rows
        ]
    except sqlite3.OperationalError:
        # FTS5 query parse failure — return empty rather than crash
        return []
    finally:
        conn.close()


def format_retrieved_context(sessions: list[dict]) -> str:
    """
    Format retrieved sessions as a compact context block for prompt injection.
    Targets ~250-350 tokens.
    """
    if not sessions:
        return ""

    lines = [
        "=== PRIOR DELIBERATIONS (retrieved — for context only) ===",
    ]
    for s in sessions:
        sid = s["session_id"][:8]
        scenario = Path(s["scenario_file"]).stem if s["scenario_file"] else "unknown"
        verdict = s["verdict"] or "unknown"
        pause = "WitnessPause: YES" if s["witness_pause_triggered"] else "WitnessPause: NO"

        lines.append(f"\n[{sid}] {scenario} → {verdict} | {pause}")
        if s["who_bears_burden"]:
            lines.append(f"  Burden: {s['who_bears_burden'][:160]}")
        if s["what_remains_unresolved"]:
            lines.append(f"  Unresolved: {s['what_remains_unresolved'][:160]}")

    lines.append("=== END PRIOR DELIBERATIONS ===")
    return "\n".join(lines)


def retrieve_context(
    scenario_text: str,
    n: int = None,
    exclude_session: str = None,
) -> str:
    """
    Convenience wrapper: retrieve + format in one call.
    Returns empty string if VILLAGE_RETRIEVAL is not set or no results found.
    """
    sessions = retrieve_relevant(scenario_text, n=n, exclude_session=exclude_session)
    return format_retrieved_context(sessions)


# ---------------------------------------------------------------------------
# CLI — run directly to index or query
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Federated Village session retrieval index")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("index", help="Index all session logs in logs/")

    q = sub.add_parser("query", help="Query the index with scenario text")
    q.add_argument("text", help="Scenario text to query against")
    q.add_argument("--n", type=int, default=3, help="Number of results")

    sub.add_parser("status", help="Show index status")

    args = parser.parse_args()

    if args.cmd == "index":
        indexed, skipped = index_all_sessions()
        print(f"Indexed: {indexed}  |  Already present (skipped): {skipped}")

    elif args.cmd == "query":
        sessions = retrieve_relevant(args.text, n=args.n)
        if not sessions:
            print("No results found.")
        else:
            print(format_retrieved_context(sessions))
            print(f"\n({len(sessions)} sessions retrieved)")

    elif args.cmd == "status":
        conn = _connect()
        count = conn.execute("SELECT COUNT(*) FROM session_meta").fetchone()[0]
        rows = conn.execute(
            "SELECT session_id, indexed_at FROM session_meta ORDER BY indexed_at DESC LIMIT 10"
        ).fetchall()
        conn.close()
        print(f"Sessions indexed: {count}")
        for r in rows:
            print(f"  {r[0][:8]}  {r[1]}")

    else:
        parser.print_help()
