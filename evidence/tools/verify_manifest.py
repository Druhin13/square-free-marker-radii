#!/usr/bin/env python3
"""Validate the publication's exact 21-file source-certificate registry.

By default only the registry structure is checked. Use --full to verify
all registered proof object bytes against their SHA-256 digests.

    python3 tools/verify_manifest.py
    python3 tools/verify_manifest.py --full

The --full mode requires each proof file and its parent directories to be
non-symlinks, every integrity status to be "verified", and byte-identical
SHA-256/size matches. It is a prerequisite, not a replacement for executing
the independent source/CNF/DRAT/graph verifiers.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "artifacts" / "manifest.json"
EXPECTED_PREFIX = "proofs/m3/"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def fail(message: str) -> None:
    raise ValueError(message)


def file_digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_safe_relative(raw: str) -> bool:
    if not isinstance(raw, str) or "\\" in raw or not raw.startswith(EXPECTED_PREFIX):
        return False
    path = PurePosixPath(raw)
    return (
        not path.is_absolute()
        and path.as_posix() == raw
        and all(part not in ("", ".", "..") for part in path.parts)
    )


def check_parents(path: Path) -> None:
    current = path.parent
    while current != ROOT:
        if not current.is_dir() or current.is_symlink():
            fail("Missing or symlinked certificate parent: " + str(current))
        if current == current.parent:
            fail("Certificate parent escaped the repository root")
        current = current.parent


def verify_registry(manifest_path: Path, full: bool) -> tuple[int, int]:
    if not manifest_path.is_file() or manifest_path.is_symlink():
        fail("Missing or symlinked publication registry")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        fail("Unexpected publication registry schema version")
    rows = data.get("artifacts")
    if not isinstance(rows, list) or data.get("artifact_count") != 21 or len(rows) != 21:
        fail("The fixed-parameter proof registry must contain exactly 21 entries")
    ids: set[str] = set()
    paths: set[str] = set()
    total = 0
    for i, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            fail(f"Artifact {i} is not an object")
        name = row.get("id")
        raw_path = row.get("relative_path")
        size = row.get("size_bytes")
        digest = row.get("sha256")
        status = row.get("integrity_status")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            fail(f"Invalid artifact ID #{i}")
        if name in ids:
            fail(f"Duplicate artifact ID: {name}")
        ids.add(name)
        if not is_safe_relative(raw_path) or raw_path in paths:
            fail(f"Unsafe or duplicate publication artifact path #{i}")
        paths.add(raw_path)
        if type(size) is not int or size <= 0:
            fail(f"Invalid byte count for {name}")
        if not isinstance(digest, str) or SHA_RE.fullmatch(digest) is None:
            fail(f"Invalid SHA-256 pin for {name}")
        if status != "verified":
            fail(f"Invalid or unverified integrity state for {name}")
        total += size

        if full:
            target = ROOT / raw_path
            check_parents(target)
            if not target.is_file() or target.is_symlink():
                fail(f"Missing or symlinked certificate: {raw_path}")
            if target.stat().st_size != size or file_digest(target) != digest:
                fail(f"SHA-256/size mismatch: {raw_path}")

    return len(rows), total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="require all proof files and verify sizes and SHA-256")
    args = parser.parse_args()
    try:
        count, total = verify_registry(DEFAULT_MANIFEST, args.full)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("PUBLICATION REGISTRY CHECK FAILED:", exc)
        return 1

    print(f"Publication proof entries: {count}")
    print(f"Total expected certificate bytes: {total}")
    if args.full:
        print("FULL SHA-256 CHECK PASSED — 21 proof objects verified")
        print("NOTE: full theorem replication also requires running independent verifiers.")
    else:
        print("CATALOG CHECK PASSED — metadata only; proof bytes and theorem verification NOT certified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
