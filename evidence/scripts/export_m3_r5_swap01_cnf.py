#!/usr/bin/env python3
"""Stream a q=4,m=3,r=5 SAT encoding invariant under ONE transposition.

Symmetry imposed: alphabet swap (0 1), fixing 2 and 3. Any satisfying
assignment gives a symmetric-radius-5 marker predicate fixed by that
single involution. It does NOT need to respect the other 22 nonidentity
permutations of S4.

The finite CNF is complete for ALL quaternary square-free words, not
only words currently known to have bi-infinite extensions.

For the canonical orbit representative, choose lexicographically smaller
of w and swap_01(w). All length >= 11 square-free words have at least
three distinct symbols, so every orbit under this transposition has
exactly two words. We use exactly one representative of every orbit.
There is no expensive clause deduplication: duplicate CNF clauses are
legitimate, with precise deterministic census checks.

CAUTION: An independently verified SAT witness is sufficient for the
bi-infinite marker upper bound; UNSAT of this finite-factor encoding
does not yet establish bi-infinite nonexistence without extension
certificates for a sufficient UNSAT core.

Run from repo root:
    python3 -m scripts.export_m3_r5_swap01_cnf

Writes locally (untracked, not committed):
    experiments/m3/kbl-q4-m3-r5-swap01.cnf
"""
from hashlib import sha256
import os
from pathlib import Path
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments/m3/kbl-q4-m3-r5-swap01.cnf"
TOTAL = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
REPRESENTATIVES = {n: count // 2 for n, count in TOTAL.items()}
CLAUSES = sum(REPRESENTATIVES[n] for n in (12, 13, 15))


def swap01(word):
    return tuple(1 if c == 0 else 0 if c == 1 else c for c in word)


def is_suffix_square(word):
    n = len(word)
    for k in range(1, n // 2 + 1):
        if word[n-2*k:n-k] == word[n-k:]:
            return True
    return False


def squarefree_words(length):
    prefix = []

    def recurse():
        if len(prefix) == length:
            yield tuple(prefix)
            return
        for c in range(4):
            prefix.append(c)
            if not is_suffix_square(prefix):
                yield from recurse()
            prefix.pop()

    yield from recurse()


def orbit_rep(word):
    alternative = swap01(word)
    return alternative if alternative < word else word


def file_digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    start = perf_counter()
    names = []
    for word in squarefree_words(11):
        if word == orbit_rep(word):
            names.append(word)
    if len(names) != REPRESENTATIVES[11]:
        raise ValueError(f"Wrong orbit-variable census {len(names)}")
    ids = {word: i for i, word in enumerate(names, 1)}
    del names

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".swap01-", suffix=".tmp",
                                     dir=OUT.parent)
    counts = {12: 0, 13: 0, 15: 0}
    units = {12: 0, 13: 0, 15: 0}
    digest = sha256()

    def emit(stream, values):
        raw = (" ".join(map(str, sorted(set(values)))) + " 0\n").encode("ascii")
        stream.write(raw)
        digest.update(raw)

    try:
        with os.fdopen(fd, "wb", buffering=1024 * 1024) as out:
            header = f"p cnf {REPRESENTATIVES[11]} {CLAUSES}\n".encode("ascii")
            out.write(header)
            digest.update(header)

            for length in (12, 13, 15):
                for word in squarefree_words(length):
                    if word != orbit_rep(word):
                        continue
                    if length in (12, 13):
                        jump = 1 if length == 12 else 2
                        a = ids[orbit_rep(word[:11])]
                        b = ids[orbit_rep(word[jump:jump+11])]
                        clause = (-a, -b)
                    else:
                        clause = tuple(ids[orbit_rep(word[i:i+11])]
                                       for i in range(5))
                    if len(set(clause)) == 1:
                        units[length] += 1
                    emit(out, clause)
                    counts[length] += 1

        for length in (12, 13, 15):
            if counts[length] != REPRESENTATIVES[length]:
                raise ValueError(f"Bad length-{length} orbit count: {counts[length]}")
        result_digest = digest.hexdigest()
        if OUT.exists():
            old_digest = file_digest(OUT)
            if result_digest != old_digest:
                raise ValueError("Existing file differs; refusing to overwrite. "
                                 f"Expected {result_digest}; found {old_digest}")
            state = "EXISTING FILE MATCHES"
        else:
            os.replace(temporary, OUT)
            temporary = None
            state = "NEW LOCAL FILE GENERATED"
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)

    print("q=4,m=3,r=5 — SINGLE TRANSPOSITION (0 1) QUOTIENT CNF")
    print("Full original square-free factor census:", TOTAL)
    print("Half-sized orbit census:", {11: REPRESENTATIVES[11], **counts})
    print("Quotient variables:", len(ids))
    print("Clauses per factor length:", counts)
    print("Unit clauses per factor length:", units)
    print("Total clauses (duplicates permitted):", CLAUSES)
    print("CNF SHA-256:", result_digest)
    print("File size (bytes):", OUT.stat().st_size)
    print("File:", OUT.relative_to(ROOT))
    print("Output status:", state)
    print(f"Elapsed seconds: {perf_counter()-start:.2f}")
    print("SAT/UNSAT not yet determined.")
    print("UNSAT alone cannot exclude swap01 invariance on the infinite subshift.")


if __name__ == "__main__":
    main()
