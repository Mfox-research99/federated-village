"""
utils/hash_chain.py — Phase 3 crypt hash utilities

Hash A: Burden register hash chain
  Each entry appended to memory/burden_register.txt also appends a SHA-256
  hash to memory/burden_register_hashes.txt. The hash is computed as:
    sha256(previous_hash + entry_content)
  where previous_hash is "GENESIS" for the first entry.

  This creates a tamper-evident chain: any modification or deletion of an entry
  breaks all subsequent hashes and is detectable by verify_burden_register.py.

Hash B: Session log content hash
  When a session log JSON is saved, SHA-256 of the canonical JSON content
  (excluding the content_hash field itself) is computed and stored as
  session_log["content_hash"]. The supervisor verifies this hash before
  evaluating — a tampered log is flagged.

Hash C: Evaluation cross-reference
  Each evaluation log JSON records the session_content_hash of the session
  it evaluated, creating a verifiable chain:
    evaluation → session (via session_content_hash) → burden register (via hash chain)
"""

import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


# ---------------------------------------------------------------------------
# Hash A: Burden register hash chain
# ---------------------------------------------------------------------------

def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_last_hash(hashes_path: Path) -> str:
    """Return the last hash in the chain file, or 'GENESIS' if empty/absent."""
    if not hashes_path.exists() or hashes_path.stat().st_size == 0:
        return "GENESIS"
    lines = hashes_path.read_text(encoding="utf-8").strip().split("\n")
    # Each line: "{index}:{hash}"
    last_line = lines[-1].strip()
    if ":" in last_line:
        return last_line.split(":", 1)[1].strip()
    return last_line  # bare hash fallback


def _read_entry_count(hashes_path: Path) -> int:
    if not hashes_path.exists() or hashes_path.stat().st_size == 0:
        return 0
    lines = [l for l in hashes_path.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
    return len(lines)


def compute_entry_hash(entry_content: str, hashes_path: Path = None) -> str:
    """
    Compute the hash for a new burden register entry.
    hash = sha256(previous_hash + entry_content)
    """
    if hashes_path is None:
        hashes_path = Path(config.BURDEN_REGISTER_HASHES)
    prev_hash = _read_last_hash(hashes_path)
    return sha256_hex(prev_hash + entry_content)


def append_entry_hash(entry_content: str, hashes_path: Path = None) -> str:
    """
    Compute and append the hash for a new burden register entry.
    Returns the computed hash.
    """
    if hashes_path is None:
        hashes_path = Path(config.BURDEN_REGISTER_HASHES)
    hashes_path.parent.mkdir(exist_ok=True)

    entry_index = _read_entry_count(hashes_path) + 1
    entry_hash  = compute_entry_hash(entry_content, hashes_path)

    with open(hashes_path, "a", encoding="utf-8") as f:
        f.write(f"{entry_index}:{entry_hash}\n")

    return entry_hash


# ---------------------------------------------------------------------------
# Hash B: Session log content hash
# ---------------------------------------------------------------------------

def compute_session_hash(session_log: dict) -> str:
    """
    Compute SHA-256 of the canonical session log JSON (content_hash field excluded).
    Uses sort_keys=True for deterministic serialization.
    """
    log_without_hash = {k: v for k, v in session_log.items() if k != "content_hash"}
    canonical = json.dumps(log_without_hash, sort_keys=True, default=str)
    return sha256_hex(canonical)


def verify_session_hash(session_log: dict) -> tuple:
    """
    Verify the content_hash field of a session log.
    Returns (is_valid: bool, stored_hash: str, computed_hash: str).
    If content_hash is absent, returns (None, None, None) — hash not present, not a failure.
    """
    stored_hash = session_log.get("content_hash")
    if stored_hash is None:
        return None, None, None
    computed = compute_session_hash(session_log)
    return computed == stored_hash, stored_hash, computed


# ---------------------------------------------------------------------------
# Hash C: Evaluation cross-reference
# ---------------------------------------------------------------------------

def get_session_content_hash(session_log: dict) -> str:
    """
    Return the session log's content_hash for embedding in the evaluation log.
    Returns empty string if absent.
    """
    return session_log.get("content_hash", "")
