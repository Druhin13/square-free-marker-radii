#!/usr/bin/env python3
"""Independent tiny C4 radius-six obstruction audit for q=4, marker gap 3.

All eleven source factors and complete zero-free exteriors are checked
against FORWARD ternary Hall--Thue factors (no reversal-closure assumption).
The source-derived clauses are matched to the supplied A..I labels and all
2^9 Boolean assignments are rejected. Classical Hall--Thue squarefreeness
and uniform recurrence + the separator-extension lemma are mathematical
premises, not conclusions of this finite computation.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "proofs/m3/exact-symmetry/c4_radius6_core.json"
PIN = "b5667eb7e6607bdf3c68848ed65fe06363a9753b8a35d4e97a6ffbca629eeb4d"


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def squarefree(word):
    n = len(word)
    for pos in range(n):
        for d in range(1, (n - pos) // 2 + 1):
            if word[pos:pos + d] == word[pos + d:pos + 2 * d]:
                return False
    return True


def hall(n=50000):
    word = "0"
    morph = {"0": "012", "1": "02", "2": "1"}
    while len(word) < n:
        word = "".join(morph[c] for c in word)
    return word[:n]


def finite_forward_factors(lengths):
    word = hall()
    result = {length: {} for length in lengths}
    for length in lengths:
        if length == 0:
            result[length][""] = ("012", 0)
            continue
        for start in range(len(word) - length + 1):
            original = word[start:start + length]
            for perm in permutations("012"):
                images = "".join(perm)
                relabeled = original.translate(str.maketrans("012", images))
                result[length].setdefault(relabeled, (images, start))
    return result


def c4_orbit(context):
    current = context
    images = [current]
    relabel = str.maketrans("0123", "1230")
    for _ in range(3):
        current = current.translate(relabel)
        images.append(current)
    return min(images)


def derived_clause(word):
    context = 13
    windows = [c4_orbit(word[d:d + context]) for d in range(len(word) - 12)]
    if len(word) == 14:
        return frozenset({(windows[0], False), (windows[1], False)})
    if len(word) == 15:
        return frozenset({(windows[0], False), (windows[2], False)})
    if len(word) == 17:
        return frozenset((w, True) for w in windows)
    raise AssertionError("Unexpected source length")


def main():
    require(SOURCE.is_file() and not SOURCE.is_symlink(), "Missing/unsafe C4 core")
    require(sha256(SOURCE.read_bytes()).hexdigest() == PIN, "Core SHA mismatch")
    rows = json.loads(SOURCE.read_text("utf-8"))
    require(isinstance(rows, list) and len(rows) == 11, "Expected 11 clauses")
    lengths = set()
    for row in rows:
        Z, separator = row["Z"], str(row["separator"])
        positions = [i for i,c in enumerate(Z) if c == separator]
        require(len(positions) >= 2, "Expected multi-separator witness")
        lengths.add(positions[0])
        lengths.add(len(Z) - positions[-1] - 1)
    hall_factors = finite_forward_factors(lengths)
    logical_clauses, certificate_margins, occur = [], [], {}
    for idx, row in enumerate(rows, start=1):
        word, extended, offset = row["source"], row["Z"], row["offset"]
        sep = str(row["separator"])
        require(len(word) in (14,15,17) and
                all(c in "0123" for c in extended + word),
                f"Source {idx}: invalid length or alphabet")
        require(squarefree(word) and squarefree(extended),
                f"Source {idx}: square in finite source or witness")
        require(extended[offset:offset + len(word)] == word,
                f"Source {idx}: source not present at supplied offset")
        positions = [i for i,c in enumerate(extended) if c == sep]
        left_end, right_begin = positions[0], positions[-1]
        span = right_begin-left_end
        left = extended[:left_end]
        right = extended[right_begin + 1:]
        require(left_end >= span - 1 and len(right) >= span - 1,
                f"Source {idx}: insufficient complete exterior margins")
        digits = "".join(d for d in "0123" if d != sep)
        canonical = str.maketrans(digits, "012")
        LF, RF = left.translate(canonical), right.translate(canonical)
        require(LF in hall_factors[len(LF)] and
                RF in hall_factors[len(RF)],
                f"Source {idx}: exterior is not a FORWARD Hall factor")
        logical_clauses.append(derived_clause(word))
        certificate_margins.append({"row":idx,"source_length":len(word),
                                    "span":span,"left_margin":len(left),
                                    "right_margin":len(right),
                                    "forward_hall_left":hall_factors[len(LF)][LF],
                                    "forward_hall_right":hall_factors[len(RF)][RF]})
    variables = sorted({v for row in logical_clauses for v,_ in row})
    require(len(variables) == 9, "Expected nine distinct orbit variables")
    signatures = {
        variable: tuple(idx for idx, row in enumerate(logical_clauses, 1)
                        if any(v==variable for v,_ in row))
        for variable in variables
    }
    declared = {label:tuple(idx for idx,row in enumerate(rows,1)
                            if any(lit.lstrip("-")==label for lit in row["clause"]))
                for label in "ABCDEFGHI"}
    require(len(set(declared.values())) == 9 and
            set(declared.values()) == set(signatures.values()),
            "Declared nine-label clause signatures mismatch source orbits")
    by_sig = {sig:letter for letter,sig in declared.items()}
    letter_for = {var:by_sig[sig] for var,sig in signatures.items()}
    reconstructed = [
        {(letter_for[var],positive) for var,positive in clause}
        for clause in logical_clauses]
    declared_clauses = [
        {(lit.lstrip("-"), not lit.startswith("-")) for lit in row["clause"]}
        for row in rows]
    require(reconstructed == declared_clauses,
            "Source-derived clauses disagree with signed A..I annotations")
    for truth in product((False,True),repeat=len(variables)):
        values = dict(zip(variables,truth))
        if all(any(values[var]==sign for var,sign in clause)
               for clause in logical_clauses):
            raise AssertionError("An assignment satisfies the C4 core")
    report = {"status":"C4 RADIUS SIX SOURCE-BACKED CORE CHECKED",
              "original_c4_core_sha256":PIN,
              "source_count":len(rows),"orbit_variables":len(variables),
              "Boolean_assignments_refuted":512,
              "forward_Hall_only":True,
              "complete_extremities":certificate_margins,
              "labelled_clauses_reconstructed":True,
              "mathematical_inputs":["classical ternary Hall--Thue squarefreeness",
                                     "classical Hall--Thue uniform recurrence",
                                     "proved multiple-separator finite-to-bi-infinite lemma"]}
    print(json.dumps(report,sort_keys=True,indent=2))
    return report

if __name__ == "__main__":
    main()
