#!/usr/bin/env python3
"""Independently audit the one-transposition q4,m3,r5 quotient CNF.

Unlike the exporter, enumerate ALL named quaternary square-free words
using an iterative stack and an independent symbol-by-symbol square
predicate. Independently map each context to the lexicographically
minimal representative of its orbit under (0 1), and reconstruct the
COMPLETE original DIMACS byte stream without reading the exported
clauses into memory.

Do not import any of the model/quotient-generation scripts. Only Python
standard library is used. This auditor keeps 43,968 orbit-context IDs
in memory and streams more than 2.4 million clause lines to a SHA-256
hash. The export file is local and remains untracked.

From evidence/, run the reproducible three-stage workflow, which generates
the quotient CNF before invoking this independent auditor:
    python3 -B reproduce.py --case swap --report ../square-free-marker-swap.json

A passing audit establishes a correct COMPLETE finite-factor quotient,
not SAT/UNSAT nor an impossibility theorem on the infinite subshift.
"""
from hashlib import sha256
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / ".build/square-free-marker-q4-m3-r5-swap01.cnf"
ORIGINAL_FACTORS = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
HALF = {n: v // 2 for n, v in ORIGINAL_FACTORS.items()}
TOTAL_CLAUSES = HALF[12] + HALF[13] + HALF[15]


def ends_with_square(candidate):
    n = len(candidate)
    for period in range(1, n // 2 + 1):
        same = True
        start = n - 2 * period
        for j in range(period):
            if candidate[start+j] != candidate[start+period+j]:
                same = False
                break
        if same:
            return True
    return False


def every_squarefree_word(length):
    """Independent iterative lexicographic enumeration of named words."""
    pending = [()]
    while pending:
        prefix = pending.pop()
        if len(prefix) == length:
            yield prefix
            continue
        for symbol in (3, 2, 1, 0):
            candidate = prefix + (symbol,)
            if not ends_with_square(candidate):
                pending.append(candidate)


def permuted(word):
    """(01) acts on integers, fixing 2 and 3."""
    mapping = {0: 1, 1: 0, 2: 2, 3: 3}
    return tuple(mapping[c] for c in word)


def canonical(word):
    alternative = permuted(word)
    return min(word, alternative)


def stream_file_sha(path):
    digest = sha256()
    size = 0
    with path.open("rb") as input_file:
        while True:
            chunk = input_file.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def main():
    start = perf_counter()
    if not CNF.is_file():
        raise FileNotFoundError(CNF)

    context_ids = {}
    full_context_count = 0
    for word in every_squarefree_word(11):
        full_context_count += 1
        partner = permuted(word)
        if word == partner:
            raise ValueError("Unexpected fixed square-free length-11 word")
        if word <= partner:
            context_ids[word] = len(context_ids) + 1
    if full_context_count != ORIGINAL_FACTORS[11]:
        raise ValueError(f"Full length-11 census differs: {full_context_count}")
    if len(context_ids) != HALF[11]:
        raise ValueError(f"Wrong 2-orbit context count: {len(context_ids)}")
    print("Independent 11-symbol variable/orbit census PASSED", flush=True)

    h = sha256()
    line_count = 0

    def digest_line(text):
        nonlocal line_count
        h.update(text.encode("ascii"))
        line_count += 1

    digest_line(f"p cnf {HALF[11]} {TOTAL_CLAUSES}\n")
    all_counts = {}
    kept_counts = {}
    unit_counts = {}
    for length in (12, 13, 15):
        all_seen = 0
        kept = 0
        units = 0
        for word in every_squarefree_word(length):
            all_seen += 1
            partner = permuted(word)
            if partner == word:
                raise ValueError(f"Unexpected fixed word length {length}")
            if word > partner:
                continue
            kept += 1

            if length in (12, 13):
                offset = 1 if length == 12 else 2
                left = context_ids[canonical(word[:11])]
                right = context_ids[canonical(word[offset:offset+11])]
                literals = {-left, -right}
            else:
                literals = {
                    context_ids[canonical(word[offset:offset+11])]
                    for offset in (0, 1, 2, 3, 4)
                }
            units += len(literals) == 1
            digest_line(" ".join(str(x) for x in sorted(literals)) + " 0\n")

        if all_seen != ORIGINAL_FACTORS[length]:
            raise ValueError(f"Wrong complete n={length} factor count {all_seen}")
        if kept != HALF[length]:
            raise ValueError(f"Wrong n={length} orbit count {kept}")
        all_counts[length] = all_seen
        kept_counts[length] = kept
        unit_counts[length] = units
        print(f"Independent n={length} complete factor and quotient census PASSED",
              flush=True)

    if line_count != TOTAL_CLAUSES + 1:
        raise ValueError(f"Wrong DIMACS line count: {line_count}")
    expected_sha = h.hexdigest()
    actual_sha, actual_size = stream_file_sha(CNF)
    if expected_sha != actual_sha:
        raise ValueError("Independent DIMACS SHA-256 mismatch: "
                         f"reconstructed={expected_sha}; actual={actual_sha}")
    with CNF.open("rb") as stream:
        header = stream.readline().decode("ascii")
    if header != f"p cnf {HALF[11]} {TOTAL_CLAUSES}\n":
        raise ValueError("Unexpected DIMACS header")

    print("INDEPENDENT SINGLE-TRANSPOSITION QUOTIENT AUDIT PASSED")
    print("Full square-free factor counts:", {11: full_context_count, **all_counts})
    print("Two-element orbit counts:", {11: len(context_ids), **kept_counts})
    print("Quotient variables:", len(context_ids))
    print("Unit clauses per length:", unit_counts)
    print("Clauses (including duplicates):", TOTAL_CLAUSES)
    print("Exact reconstructed CNF SHA256:", actual_sha)
    print("File size (bytes):", actual_size)
    print(f"Elapsed seconds: {perf_counter()-start:.2f}")
    print("SAT/UNSAT has not been tested.")
    print("UNSAT requires infinite-factor extension before a theorem.")


if __name__ == "__main__":
    main()
