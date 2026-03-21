"""
verify_burden_register.py — Phase 3 crypt hash A integrity check

Verifies the SHA-256 hash chain of memory/burden_register.txt against
the companion chain file memory/burden_register_hashes.txt.

Each entry in burden_register.txt ends with a HASH: line computed as:
  sha256(previous_hash + entry_content_without_hash_line)

The companion file memory/burden_register_hashes.txt stores:
  {entry_index}:{hash}
one per line.

Usage:
  python verify_burden_register.py
  python verify_burden_register.py --verbose
"""

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_entries(register_text: str) -> list:
    """
    Split burden register text into individual entries.
    Each entry ends with a line containing only '---'.
    """
    entries = []
    current = []
    for line in register_text.split("\n"):
        current.append(line)
        if line.strip() == "---":
            entry_text = "\n".join(current).strip()
            if entry_text and entry_text != "---":
                entries.append(entry_text)
            current = []
    # Capture any trailing content without a final '---'
    if current:
        remainder = "\n".join(current).strip()
        if remainder:
            entries.append(remainder)
    return entries


def entry_content_without_hash(entry_text: str) -> str:
    """Strip the HASH: line from an entry before computing the hash."""
    lines = [l for l in entry_text.split("\n") if not l.startswith("HASH:")]
    return "\n".join(lines).strip()


def verify(verbose: bool = False) -> bool:
    register_path = Path(config.BURDEN_REGISTER)
    hashes_path   = Path(config.BURDEN_REGISTER_HASHES)

    if not register_path.exists():
        print("SKIP: burden_register.txt does not exist.")
        return True

    if not hashes_path.exists():
        print("SKIP: burden_register_hashes.txt does not exist.")
        print("      (Run a session to initialize the hash chain.)")
        return True

    register_text = register_path.read_text(encoding="utf-8")
    hashes_text   = hashes_path.read_text(encoding="utf-8")

    entries = parse_entries(register_text)
    stored_hashes = [
        line.split(":", 1)[1].strip()
        for line in hashes_text.strip().split("\n")
        if ":" in line and line.strip()
    ]

    if not entries:
        print("SKIP: No entries found in burden register.")
        return True

    if len(entries) != len(stored_hashes):
        print(
            f"FAIL: Entry/hash count mismatch — "
            f"{len(entries)} entries in register, {len(stored_hashes)} hashes stored."
        )
        return False

    prev_hash = "GENESIS"
    all_ok = True

    for i, (entry, stored_hash) in enumerate(zip(entries, stored_hashes)):
        content = entry_content_without_hash(entry)
        expected_hash = sha256_hex(prev_hash + content)

        if expected_hash != stored_hash:
            print(f"FAIL: Entry {i+1} hash mismatch — chain broken at entry {i+1}.")
            if verbose:
                print(f"  Expected: {expected_hash}")
                print(f"  Stored:   {stored_hash}")
                print(f"  Content preview: {content[:120]}...")
            all_ok = False
        else:
            if verbose:
                print(f"  [OK] Entry {i+1}: {stored_hash[:16]}...")

        prev_hash = stored_hash

    if all_ok:
        print(
            f"PASS: Burden register integrity verified — "
            f"{len(entries)} entries, chain intact."
        )
    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify burden register SHA-256 hash chain integrity"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show per-entry hash check results",
    )
    args = parser.parse_args()
    ok = verify(args.verbose)
    sys.exit(0 if ok else 1)
