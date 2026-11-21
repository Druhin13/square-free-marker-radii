#!/usr/bin/env python3
"""Check exactly the three original positive subgroup model/report Git blobs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "artifacts/subgroup-positive-manifest.json"
EXPECTED_PATHS = {
    "proofs/m3/square-free-marker-q4-m3-r5-swap01-result.txt",
    "proofs/m3/double01-23/square-free-marker-m3-r5-double01-23-result.txt",
    "proofs/m3/double01-23/square-free-marker-m3-r5-double01-23-sat-audit.json",
}


def verify_registry(path: Path = REGISTRY) -> tuple[int, int]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing/unsafe subgroup positive registry")
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("archives")
    if (data.get("schema_version") != 1 or data.get("archive_count") != 3
            or not isinstance(entries, list) or len(entries) != 3):
        raise ValueError("Positive model registry must specify exactly three archived inputs")
    paths = [row.get("relative_path") for row in entries]
    if set(paths) != EXPECTED_PATHS or len(set(paths)) != 3:
        raise ValueError("Unexpected/unsafe or duplicate positive archive path")
    total = 0
    for row in entries:
        size, git_hash = row.get("size_bytes"), row.get("git_blob_sha1")
        if (type(size) is not int or size <= 0
                or not isinstance(git_hash, str) or len(git_hash) != 40
                or any(c not in "0123456789abcdef" for c in git_hash)):
            raise ValueError("Malformed positive source byte/Git blob identity")
        path = ROOT / row["relative_path"]
        for parent in (ROOT / "proofs", ROOT / "proofs/m3", path.parent):
            if not parent.is_dir() or parent.is_symlink():
                raise ValueError("Missing/symlinked positive archive parent")
        if not path.is_file() or path.is_symlink() or path.stat().st_size != size:
            raise ValueError("Missing/symlinked or wrong-size positive proof archive")
        digest = hashlib.sha1()
        digest.update(b"blob " + str(size).encode("ascii") + b"\0")
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1 << 20), b""):
                digest.update(block)
        if digest.hexdigest() != git_hash:
            raise ValueError("Original positive Git proof blob mismatch")
        total += size
    return len(entries), total


if __name__ == "__main__":
    n, size = verify_registry()
    print(f"POSITIVE INVOLUTION ORIGINAL BLOB INTEGRITY PASSED: {n} files, {size} bytes")
