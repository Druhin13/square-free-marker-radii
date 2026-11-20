#!/usr/bin/env python3
"""Reconstruct the exact original 87,936-variable unrestricted r5 DIMACS.

C03 experiment input only. Independent from historical original generators.
Enumerates *all* square-free quaternary words of lengths 11, 12, 13 and 15.
The output must byte-match the pre-existing 143,654,386-byte input SHA pin.
Only writes a NEW explicit path; never opens proof/ or artifact/ for writing.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
from time import perf_counter

FACTORS = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
VARIABLES = FACTORS[11]
CLAUSES = FACTORS[12] + FACTORS[13] + FACTORS[15]
EXPECTED_SHA256 = "02bdd92ab8271228b79f3c1b9d095bedc5fcce7564afdcb003ae56ac1c4897d7"
EXPECTED_BYTES = 143654386


def require(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def words(length: int):
    """Lexicographic DFS, reject a square as soon as it becomes a suffix."""
    prefix = []

    def recurse():
        if len(prefix) == length:
            yield bytes(prefix)
            return
        for letter in range(4):
            prefix.append(letter)
            n = len(prefix)
            valid = True
            for half in range(1, n // 2 + 1):
                if prefix[n - 2 * half:n - half] == prefix[n - half:n]:
                    valid = False
                    break
            if valid:
                yield from recurse()
            prefix.pop()

    yield from recurse()


def generate(path: Path) -> dict:
    require(path.parent.is_dir() and not path.parent.is_symlink(),
            "Output parent does not exist or is a symlink")
    require(not path.exists() and not path.is_symlink(),
            "Refuse to overwrite an existing CNF or symlink")
    started = perf_counter()
    variables = {w: i for i, w in enumerate(words(11), 1)}
    require(len(variables) == VARIABLES, "Wrong unrestricted context census")
    digest = sha256()
    by_length = {}

    with path.open("xb", buffering=1 << 20) as out:
        header = f"p cnf {VARIABLES} {CLAUSES}\n".encode("ascii")
        out.write(header)
        digest.update(header)

        for n in (12, 13, 15):
            count = 0
            for source in words(n):
                if n == 12:
                    literals = (-variables[source[:11]],
                                -variables[source[1:12]])
                elif n == 13:
                    literals = (-variables[source[:11]],
                                -variables[source[2:13]])
                else:
                    literals = tuple(variables[source[i:i+11]]
                                     for i in range(5))
                require(len(set(literals)) == len(literals),
                        "Duplicate context in unrestricted source")
                raw = (" ".join(str(lit) for lit in sorted(literals))
                       + " 0\n").encode("ascii")
                out.write(raw)
                digest.update(raw)
                count += 1
            require(count == FACTORS[n], f"Wrong length-{n} source count")
            by_length[str(n)] = count

    # This independently reproduces the precise original DIMACS order
    # (including sorted signed literals), not only a logically equivalent CNF.
    actual_sha256 = digest.hexdigest()
    require(actual_sha256 == EXPECTED_SHA256,
            f"Original SHA-256 pin mismatch: {actual_sha256}")
    require(path.stat().st_size == EXPECTED_BYTES,
            f"Original CNF byte count mismatch: {path.stat().st_size}")
    return {
        "variables": VARIABLES,
        "clauses": CLAUSES,
        "bytes": path.stat().st_size,
        "sha256": actual_sha256,
        "source_counts": by_length,
        "generation_wall_seconds": round(perf_counter() - started, 3),
        "matches_historic_original_cnf_sha256": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = generate(args.output.resolve())
    for key, value in report.items():
        print(f"C03 UNRESTRICTED CNF {key}: {value}", flush=True)
    print("EXACT ORIGINAL UNRESTRICTED r5 DIMACS RECONSTRUCTION PASSED")


if __name__ == "__main__":
    main()
