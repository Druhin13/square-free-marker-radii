#!/usr/bin/env python3
"""Independent byte-for-byte finite-factor CNF audit for (01)(23).

Independently enumerates *all* named quaternary square-free words of
lengths 11,12,13,15 using a stack rather than the generating script's
recursive DFS. Uses direct per-character square-suffix comparisons and
an independent alphabet permutation (0 1)(2 3), reconstructing every
one of the 2,495,760 clauses as an exact deterministic byte stream.

NO import from the formula generator or other marker modules.
A passing audit establishes correctness of a complete finite-factor
SAT quotient, NOT satisfiability or a bi-infinite impossibility theorem.

    python3 -B -m scripts.audit_m3_r5_double01_23_cnf_independent
"""
from hashlib import sha256
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / "experiments/m3/kbl-q4-m3-r5-double01-23.cnf"
EXPECTED_NAMED = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
EXPECTED_ORBITS = {11: 43968, 12: 115260, 13: 302304, 15: 2078196}
EXPECTED_CLAUSES = (
    EXPECTED_ORBITS[12] + EXPECTED_ORBITS[13] + EXPECTED_ORBITS[15]
)


def require(condition, msg):
    if not condition:
        raise ValueError(msg)


def square_ending_here(word):
    n = len(word)
    for p in range(1, n // 2 + 1):
        same = True
        for j in range(p):
            if word[n-2*p+j] != word[n-p+j]:
                same = False
                break
        if same:
            return True
    return False


def named_words(n):
    """Independent stack DFS in full quaternary lexicographic order."""
    pending = [()]
    while pending:
        prefix = pending.pop()
        if len(prefix) == n:
            yield prefix
            continue
        for letter in (3, 2, 1, 0):
            trial = prefix + (letter,)
            if not square_ending_here(trial):
                pending.append(trial)


def other_color(word):
    """Explicit coordinate involution, with no fixed alphabet symbol."""
    p = {0: 1, 1: 0, 2: 3, 3: 2}
    return tuple(p[value] for value in word)


def key(word):
    permuted = other_color(word)
    return word if word <= permuted else permuted


def actual_file_hash():
    digest = sha256()
    byte_count = 0
    with CNF.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1 << 20), b""):
            digest.update(chunk)
            byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def main():
    start = perf_counter()
    require(CNF.is_file(), f"Missing untracked source CNF: {CNF}")

    ids = {}
    named_contexts = 0
    for word in named_words(11):
        named_contexts += 1
        transformed = other_color(word)
        require(transformed != word,
                f"Unexpected fixed legal n11 factor: {word}")
        if word < transformed:
            ids[word] = len(ids) + 1
    require(named_contexts == EXPECTED_NAMED[11]
            and len(ids) == EXPECTED_ORBITS[11],
            f"Wrong n11 original/orbit census: {named_contexts}, {len(ids)}")
    print("PHASE 1/3 PASSED: all named 11-factors / involution orbit indices",
          flush=True)

    digest = sha256()
    lines = 0

    def update_line(text):
        nonlocal lines
        digest.update(text.encode("ascii"))
        lines += 1

    update_line(f"p cnf {EXPECTED_ORBITS[11]} {EXPECTED_CLAUSES}\n")
    orbit_hist = {}
    reduction_hist = {}
    unit_hist = {}
    for n in (12, 13, 15):
        named_count = 0
        orbit_count = 0
        shortened_count = 0
        unit_count = 0
        for word in named_words(n):
            named_count += 1
            alternative = other_color(word)
            require(word != alternative,
                    f"Unexpected fixed legal n{n} factor: {word}")
            if word > alternative:
                continue
            orbit_count += 1
            if n == 12 or n == 13:
                offset = n - 11
                values = [
                    -ids[key(word[:11])],
                    -ids[key(word[offset:offset+11])],
                ]
            else:
                values = [
                    ids[key(word[offset:offset+11])]
                    for offset in range(5)
                ]
            clause = set(values)
            shortened_count += len(clause) < len(values)
            unit_count += len(clause) == 1
            update_line(
                " ".join(str(value) for value in sorted(clause)) + " 0\n"
            )

        require(named_count == EXPECTED_NAMED[n]
                and orbit_count == EXPECTED_ORBITS[n],
                f"Wrong n{n} factor/orbit census: {named_count}, {orbit_count}")
        orbit_hist[n] = orbit_count
        reduction_hist[n] = shortened_count
        unit_hist[n] = unit_count
        print(
            f"  n={n}: named={named_count}, orbits={orbit_count}, "
            f"shortened={shortened_count}, units={unit_count}",
            flush=True
        )

    require(lines == EXPECTED_CLAUSES + 1,
            f"Bad total number of reconstructed DIMACS lines: {lines}")
    expected_digest = digest.hexdigest()
    actual_digest, size = actual_file_hash()
    require(actual_digest == expected_digest,
            "INDEPENDENT BYTE-EXACT CNF SHA256 MISMATCH: "
            f"expected {expected_digest}, actual {actual_digest}")
    with CNF.open("rb") as stream:
        require(stream.readline() ==
                f"p cnf {EXPECTED_ORBITS[11]} {EXPECTED_CLAUSES}\n".encode("ascii"),
                "Unexpected CNF DIMACS header")
    print("PHASE 2/3 PASSED: all named factors and quotient clause census")
    print("PHASE 3/3 PASSED: byte-exact SHA-256 reconstruction of full CNF")
    print("INDEPENDENT DOUBLE-TRANSPOSITION FINITE-QUOTIENT AUDIT PASSED")
    print("  Original named contexts:", named_contexts)
    print("  Orbit variables:", len(ids))
    print("  Orbit clauses by source length:", orbit_hist)
    print("  Shortened clauses:", reduction_hist)
    print("  Unit clauses:", unit_hist)
    print("  Total clauses:", EXPECTED_CLAUSES)
    print("  Independently reconstructed SHA-256:", actual_digest)
    print("  Source file bytes:", size)
    print(f"  Elapsed seconds: {perf_counter()-start:.2f}")
    print("No SAT/UNSAT or bi-infinite theorem has been asserted.")


if __name__ == "__main__":
    main()
