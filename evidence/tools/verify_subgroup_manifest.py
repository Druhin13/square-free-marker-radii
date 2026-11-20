#!/usr/bin/env python3
"""Check the exact imported subgroup proof Git blobs independently.

The original lower-bound auditors separately SHA-256 pin their source data,
verify every finite-source extension witness, and replay DRAT. This validator
checks archive identities, exact sizes, pathname safety, and the three
integrated verification records stored alongside their proof inputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "artifacts/subgroup-manifest.json"
GROUP_COUNTS = {"cycle012": 6, "normal-v4": 8, "intransitive-v4": 9}
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def verify_registry(path: Path = REGISTRY) -> tuple[int, int]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or symlinked subgroup registry")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("archive_count") != 23:
        raise ValueError("Unexpected subgroup proof registry schema or count")
    rows = data.get("archives")
    if not isinstance(rows, list) or len(rows) != 23:
        raise ValueError("Subgroup proof archive must have 23 paths")
    observed, total, counts = set(), 0, dict.fromkeys(GROUP_COUNTS, 0)
    for row in rows:
        raw = row.get("relative_path")
        if not isinstance(raw, str) or "\\" in raw or raw in observed:
            raise ValueError("Invalid/duplicate subgroup archive path")
        rel = PurePosixPath(raw)
        parts = rel.parts
        if (rel.is_absolute() or rel.as_posix() != raw
                or any(p in (".", "..", "") for p in parts)
                or len(parts) != 4 or parts[:2] != ("proofs", "m3")
                or parts[2] not in GROUP_COUNTS):
            raise ValueError("Unsafe subgroup archive path: " + raw)
        observed.add(raw)
        counts[parts[2]] += 1
        size, expected = row.get("size_bytes"), row.get("git_blob_sha1")
        if (type(size) is not int or size <= 0
                or not isinstance(expected, str) or not GIT_SHA.fullmatch(expected)):
            raise ValueError("Invalid size/Git blob SHA in subgroup registry")
        target = ROOT / raw
        for part in (ROOT / "proofs", ROOT / "proofs/m3", target.parent):
            if not part.is_dir() or part.is_symlink():
                raise ValueError("Missing or symlinked parent directory: " + str(part))
        if not target.is_file() or target.is_symlink() or target.stat().st_size != size:
            raise ValueError("Missing/unsafe or wrong-size proof file: " + raw)
        digest = hashlib.sha1()
        digest.update(b"blob " + str(size).encode("ascii") + b"\0")
        with target.open("rb") as source:
            for chunk in iter(lambda: source.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError("Git source blob does not match: " + raw)
        total += size
    if counts != GROUP_COUNTS:
        raise ValueError("Unexpected subgroup archive directory counts: " + str(counts))
    return len(rows), total


if __name__ == "__main__":
    count, size = verify_registry()
    print(f"SUBGROUP ARCHIVE SOURCE-BLOB INTEGRITY PASSED: {count} files, {size} bytes")
    print("NOTE: mathematical verification requires source realization and standalone DRAT replay.")
