#!/usr/bin/env python3
"""Read-only integrity and layout audit for an exported evidence ZIP.

Run this against a standalone distribution archive, not against the Git
checkout. In particular, the checkout's root .git directory is expected;
a distributed archive must never contain Git metadata.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import re
import stat
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

HEX_SHA256 = re.compile(r"[0-9a-f]{64}")


def validate_member_path(name: str, mode: int) -> None:
    path = PurePosixPath(name)
    components = name.split("/")
    if (not name or name.startswith("/") or name.endswith("/")
            or "\\" in name or "\x00" in name
            or any(part in ("", ".", "..", ".git") for part in components)
            or path.as_posix() != name):
        raise ValueError(f"Unsafe distribution entry path: {name!r}")
    file_type = stat.S_IFMT(mode)
    if file_type not in (0, stat.S_IFREG):
        raise ValueError(f"Nonregular distribution entry: {name!r}")


def validate_archive(path: Path, *, expected_proofs: int | None = 52,
                     require_workflow: bool = True) -> dict:
    """Validate ZIP structure and all archived hashes without extracting files."""
    with ZipFile(path) as archive:
        members = archive.infolist()
        names = set()
        for member in members:
            name = member.filename
            validate_member_path(name, member.external_attr >> 16)
            if name in names:
                raise ValueError(f"Duplicate entry: {name}")
            if member.flag_bits & 1:
                raise ValueError(f"Encrypted entry: {name}")
            names.add(name)
        if "SHA256SUMS" not in names:
            raise ValueError("SHA256SUMS is missing")
        lines = archive.read("SHA256SUMS").decode("utf-8").splitlines()
        checksums = {}
        for line in lines:
            if "  " not in line:
                raise ValueError("Malformed checksum line")
            digest, name = line.split("  ", 1)
            if not HEX_SHA256.fullmatch(digest) or name in checksums:
                raise ValueError("Invalid or duplicate checksum entry")
            validate_member_path(name, stat.S_IFREG)
            checksums[name] = digest
        if set(checksums) != names - {"SHA256SUMS"}:
            raise ValueError("Manifest/file-list mismatch")
        for name, expected_hash in checksums.items():
            h = sha256()
            with archive.open(name) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(block)
            if h.hexdigest() != expected_hash:
                raise ValueError(f"Checksum mismatch: {name}")
        proofs = [n for n in names if n.startswith("evidence/proofs/")]
        if expected_proofs is not None and len(proofs) != expected_proofs:
            raise ValueError(f"Expected {expected_proofs} proof objects; found {len(proofs)}")
        if require_workflow:
            found = {n for n in names if n.startswith(".github/workflows/")}
            if found != {".github/workflows/verify-evidence.yml"}:
                raise ValueError("Unexpected release workflow set")
    return {"file_count": len(names), "checksum_entries": len(checksums),
            "proof_objects": len(proofs)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    result = validate_archive(args.archive)
    print("PASS: distribution archive integrity and structure:", result)


if __name__ == "__main__":
    main()
