#!/usr/bin/env python3
"""Independently certify a double-transposition-invariant radius-five marker.

This standalone audit does not import the SAT generator, quotient auditor,
solver integration or any existing marker witness verifier.

Mathematical goal: one shared shift-equivariant Boolean local rule of
radius r=5 on EVERY bi-infinite quaternary square-free sequence, invariant
under the single double transposition (0 1)(2 3), with marker separation
at least 3 and domination distance at most 2.

1. SHA-pin the independently reconstructed FULL finite-word quotient CNF
   from its published encoding; independently parse a complete, uniquely signed
   43,968-variable CaDiCaL SAT model.
2. Check all 2,495,760 literal clauses in exact pinned quotient CNF.
3. Independently enumerate ALL ORIGINAL NAMED finite square-free words
   of lengths 11, 12, 13, 15, construct the variable indices using a
   stack DFS, check distance-one and distance-two marker separation in
   EVERY n12 and n13 named factor and five-center domination in EVERY
   n15 named factor, and check involution invariance for each n11 factor.
   The generator only enumerated quotient orbit representative clauses;
   this verifier tests the original unquotiented words directly.

This works for the actual bi-infinite square-free subshift because the
named finite-word set checked is a SUPERSET of its legal finite factors.
No Hall-Thue extension theorem or UNSAT reasoning is required for SAT
existence. It does not establish a larger stabilizer, minimal radius
subject to symmetry beyond the known unrestricted minimum,
or other marker parameters.

The public reproduction driver supplies an isolated generated quotient CNF,
the registered model, and an exclusive temporary report path. From evidence/:
    python3 -B reproduce.py --case double --report ../kbl-double.json

Standalone use of this component requires the same explicit input paths;
its generation-time defaults are not distributed proof files.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / ".build/kbl-q4-m3-r5-double01-23.cnf"
MODEL = Path("/tmp/kbl-m3-r5-double01-23-result.txt")
REPORT = Path("/tmp/kbl-m3-r5-double01-23-sat-audit.json")
CNF_PIN = "f44a5b98e0b47bac8d7ae988ddcd96dc5f8ed66500cad29ae0613a8a670889ff"
VARS = 43968
TOTAL_CLAUSES = 2495760
ORIGINAL = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
QUOTIENT = {n: k // 2 for n, k in ORIGINAL.items()}


def require(truth, error):
    if not truth:
        raise AssertionError(error)


def sha_file(path):
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def double_swap(word):
    """Independently specify (0 1)(2 3), fixing no alphabet symbol."""
    return tuple((1, 0, 3, 2)[x] for x in word)


def canonical(word):
    counterpart = double_swap(word)
    return word if word < counterpart else counterpart


def ends_with_square(word):
    length = len(word)
    for period in range(1, length // 2 + 1):
        base = length - 2 * period
        if all(word[base + j] == word[base + period + j]
               for j in range(period)):
            return True
    return False


def named_words(length):
    """Iterative lexicographic DFS independent of recursive exporter."""
    stack = [()]
    while stack:
        prefix = stack.pop()
        if len(prefix) == length:
            yield prefix
            continue
        for symbol in (3, 2, 1, 0):
            child = prefix + (symbol,)
            if not ends_with_square(child):
                stack.append(child)


def signed_model():
    require(MODEL.is_file(), f"Expected CaDiCaL SAT model not found: {MODEL}")
    raw = MODEL.read_bytes()
    result_digest = sha256(raw).hexdigest()
    statuses = []
    assigned = [None] * (VARS + 1)
    count = 0
    final_zero = False
    for line_number, source in enumerate(raw.splitlines(), 1):
        line = source.strip()
        if not line or line.startswith(b"c "):
            continue
        if line.startswith(b"s "):
            require(not statuses, "Repeated solver status line")
            statuses.append(line)
            continue
        require(line.startswith(b"v "),
                f"Unexpected CaDiCaL output line {line_number}: {line[:100]!r}")
        require(not final_zero, "Model continues after terminating zero")
        for raw_lit in line.split()[1:]:
            signed = int(raw_lit)
            if signed == 0:
                require(not final_zero, "Duplicate zero in model")
                final_zero = True
                continue
            require(not final_zero, "Nonzero model literal after terminating zero")
            index = abs(signed)
            require(1 <= index <= VARS, f"Out-of-range SAT model literal {signed}")
            require(assigned[index] is None,
                    f"Duplicate SAT assignment for variable {index}")
            assigned[index] = signed > 0
            count += 1
    require(statuses == [b"s SATISFIABLE"],
            f"Expected exact CaDiCaL 's SATISFIABLE', got {statuses}")
    require(final_zero, "Missing SAT model trailing zero")
    require(count == VARS and all(x is not None for x in assigned[1:]),
            f"Incomplete or invalid assignment: {count}/{VARS}")
    return assigned, result_digest


def check_quotient(assignment):
    require(CNF.is_file(), f"Missing independently audited CNF: {CNF}")
    digest = sha_file(CNF)
    require(digest == CNF_PIN,
            f"Independently audited original finite CNF SHA mismatch: {digest}")
    total = 0
    with CNF.open("rb") as stream:
        header = stream.readline()
        require(header == f"p cnf {VARS} {TOTAL_CLAUSES}\n".encode("ascii"),
                f"Unexpected DIMACS header {header[:100]!r}")
        for raw in stream:
            total += 1
            literals = raw.split()
            require(len(literals) >= 2 and literals[-1] == b"0",
                    f"Malformed DIMACS row {total}")
            satisfied = False
            for token in literals[:-1]:
                lit = int(token)
                require(lit != 0 and abs(lit) <= VARS,
                        f"Invalid literal in CNF row {total}")
                if assignment[abs(lit)] == (lit > 0):
                    satisfied = True
            require(satisfied, f"FALSIFIED finite quotient CNF clause {total}")
    require(total == TOTAL_CLAUSES, f"CNF clause count {total} unexpected")
    print("PHASE 2/4 PASSED: every independently audited quotient clause TRUE")
    print("  Clauses satisfied:", total, flush=True)


def reconstruct_orbits():
    seen = 0
    ids = {}
    for word in named_words(11):
        seen += 1
        mate = double_swap(word)
        require(mate != word, "Unexpected fixed context for double transposition")
        if word < mate:
            ids[word] = len(ids) + 1
    require(seen == ORIGINAL[11] and len(ids) == VARS,
            f"Original/orbit contexts mismatch {seen}, {len(ids)}")
    print("PHASE 3/4 PASSED: independently reconstructed n11 named contexts")
    print("  Named n11 contexts:", seen)
    print("  Double-transposition orbit variables:", len(ids), flush=True)
    return ids


def check_all_named_factors(assignment, ids):
    histogram = Counter()
    for n in (12, 13, 15):
        count = 0
        for source in named_words(n):
            count += 1
            if n in (12, 13):
                stride = n - 11
                left = ids[canonical(source[:11])]
                right = ids[canonical(source[stride:stride+11])]
                require(not (assignment[left] and assignment[right]),
                        f"Packing violation in n={n} NAMED word: {source}")
            else:
                require(any(assignment[ids[canonical(source[k:k+11])]]
                            for k in (0, 1, 2, 3, 4)),
                        f"Domination violation in n=15 NAMED word: {source}")
        require(count == ORIGINAL[n],
                f"Wrong independent n{n} named-word census: {count}")
        histogram[n] = count
        print(f"  ORIGINAL named factors n={n}: {count} all checked", flush=True)

    symmetry_count = 0
    for word in named_words(11):
        symmetry_count += 1
        transformed = double_swap(word)
        require(
            assignment[ids[canonical(word)]] ==
            assignment[ids[canonical(transformed)]],
            f"Double-transposition invariance FAILS for {word}"
        )
    require(symmetry_count == ORIGINAL[11],
            f"Invariance named-word census wrong: {symmetry_count}")
    print("PHASE 4/4 PASSED: ALL original finite-factor marker constraints,")
    print("  plus (0 1)(2 3) symmetry on every named length-11 context")
    print("  Original factor census:", dict(sorted(histogram.items())))
    print("  Invariant named n11 contexts:", symmetry_count, flush=True)
    return dict(sorted(histogram.items())), symmetry_count


def main():
    started = perf_counter()
    require(not REPORT.exists(),
            f"Refusing to overwrite existing audit report: {REPORT}")
    print("q4 m3 r5 — INDEPENDENT DOUBLE TRANSPOSITION SAT RULE AUDIT",
          flush=True)
    assignment, model_hash = signed_model()
    print("PHASE 1/4 PASSED: complete, unique signed CaDiCaL SAT model")
    print("  Exact SAT model SHA-256:", model_hash)
    print("  Variables assigned:", VARS)
    marked = sum(assignment[1:])
    print("  Orbit classes marked:", marked, flush=True)

    check_quotient(assignment)
    ids = reconstruct_orbits()
    factors, symmetry = check_all_named_factors(assignment, ids)
    report = {
        "status": "ALL FOUR PHASES PASSED",
        "scope": "q4,m3,r5 shift-equivariant Boolean marker on all bi-infinite square-free inputs",
        "symmetry": "(0 1)(2 3)",
        "marker_separation": "at least 3",
        "marker_domination": "within 2",
        "cnf_sha256": CNF_PIN,
        "sat_model_sha256": model_hash,
        "context_orbit_variables": VARS,
        "marked_orbit_classes": marked,
        "complete_finite_factor_clauses_checked": TOTAL_CLAUSES,
        "all_named_factors_checked": factors,
        "original_named_context_symmetry_checked": symmetry,
        "finite_factor_coverage_is_superset_of_biinfinite_factors": True,
        "theorem": "exists a valid r5 marker rule invariant under any one double transposition, by alphabet conjugacy",
        "not_claimed": [
            "larger invariance subgroup V4",
            "full stabilizer of this particular model",
        ],
    }
    result = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with REPORT.open("xb") as stream:
        stream.write(result)
    print("ALL FOUR PHASES PASSED")
    print("CERTIFIED EXISTENCE: one shared symmetric-radius-five marker")
    print("  is invariant under (0 1)(2 3), works on ALL bi-infinite")
    print("  quaternary square-free sequences, separation>=3, domination<=2.")
    print("  By alphabet conjugacy, ANY single double transposition is compatible.")
    print("  Does not establish V4-invariance or larger stabilizer.")
    print("  Model SHA-256:", model_hash)
    print("  Local audit report:", REPORT)
    print("  Report SHA-256:", sha256(result).hexdigest())
    print("  Report size (bytes):", len(result))
    print(f"  Elapsed seconds: {perf_counter()-started:.2f}")


if __name__ == "__main__":
    main()
