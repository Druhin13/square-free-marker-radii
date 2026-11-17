#!/usr/bin/env python3
"""Independent verification of a radius-5 SAT assignment for q=4,m=3.

First, checks the complete CaDiCaL assignment against every one of
4,991,520 clauses in the pinned 143 MB DIMACS file, streaming the file.
Second, independently enumerates all quaternary square-free factors
of lengths 11,12,13,15 and checks the marker-rule conditions DIRECTLY:
  - distance-one markers cannot both be present;
  - distance-two markers cannot both be present;
  - each five-consecutive-position window has a marker.

No imports from CNF exporter, CNF auditor, SAT solver, or any other
research script. Requires only Python standard library.

From repository root after CaDiCaL reports SAT:
    python3 -m scripts.verify_marker_m3_r5_sat_witness

Inputs default to:
    experiments/m3/kbl-q4-m3-r5.cnf
    /tmp/kbl-m3-r5-result.txt

Output (local, not automatically committed):
    experiments/m3/kbl-q4-m3-r5-sat-verification.json

If this check passes, the assignment provides a sufficient radius-5
marker rule on ALL bi-infinite quaternary square-free inputs. Together
with the independently archived radius-4 impossibility proof, this
establishes the exact minimum symmetric radius of 5 for m=3.

This does not establish publication novelty or a general m asymptotic.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CNF = ROOT / "experiments/m3/kbl-q4-m3-r5.cnf"
DEFAULT_MODEL = Path("/tmp/kbl-m3-r5-result.txt")
DEFAULT_REPORT = ROOT / "experiments/m3/kbl-q4-m3-r5-sat-verification.json"

EXPECTED_CNF_SHA = "02bdd92ab8271228b79f3c1b9d095bedc5fcce7564afdcb003ae56ac1c4897d7"
VARIABLES = 87936
PACKING_ADJACENT = 230520
PACKING_DISTANCE_TWO = 604608
PACKING = PACKING_ADJACENT + PACKING_DISTANCE_TWO
DOMINATION = 4156392
CLAUSES = PACKING + DOMINATION


def require(test, reason):
    if not test:
        raise ValueError(reason)


def parse_complete_sat_model(path):
    raw = path.read_bytes()
    statuses = []
    signed = []
    saw_final_zero = False
    for lineno, line in enumerate(raw.decode("ascii").splitlines(), 1):
        strip = line.strip()
        if not strip or strip.startswith("c "):
            continue
        if strip.startswith("s "):
            require(not statuses, f"Duplicate SAT status at {lineno}")
            statuses.append(strip)
        elif strip.startswith("v "):
            require(not saw_final_zero,
                    f"Extra assignment line after final zero at {lineno}")
            for token in strip.split()[1:]:
                literal = int(token)
                if literal == 0:
                    require(not saw_final_zero, "Multiple assignment terminators")
                    saw_final_zero = True
                else:
                    require(not saw_final_zero,
                            "Additional assignment literals after zero")
                    signed.append(literal)
        else:
            raise ValueError(f"Unexpected SAT witness line {lineno}: {strip[:90]}")

    require(statuses == ["s SATISFIABLE"],
            f"Expected exactly 's SATISFIABLE', found {statuses}")
    require(saw_final_zero, "Missing final DIMACS zero in model")
    require(len(signed) == VARIABLES,
            f"Expected {VARIABLES} assignments, got {len(signed)}")

    assignment = [None] * (VARIABLES + 1)
    for lit in signed:
        index = abs(lit)
        require(1 <= index <= VARIABLES, f"Out-of-range variable: {lit}")
        require(assignment[index] is None, f"Duplicate assignment for {index}")
        assignment[index] = lit > 0
    require(all(value is not None for value in assignment[1:]),
            "Some SAT variables were not assigned")
    return assignment, sha256(raw).hexdigest()


def independently_squarefree(length):
    """Iterative lexicographic DFS with symbol-by-symbol square checking."""
    pending = [()]
    while pending:
        prefix = pending.pop()
        if len(prefix) == length:
            yield prefix
            continue
        for symbol in (3, 2, 1, 0):
            candidate = prefix + (symbol,)
            n = len(candidate)
            valid = True
            for period in range(1, n // 2 + 1):
                first = n - 2 * period
                match = True
                for j in range(period):
                    if candidate[first + j] != candidate[first + period + j]:
                        match = False
                        break
                if match:
                    valid = False
                    break
            if valid:
                pending.append(candidate)


def check_every_dimacs_clause(path, assignment):
    started = perf_counter()
    h = sha256()
    count = 0
    with path.open("rb") as stream:
        header = stream.readline()
        h.update(header)
        require(header == f"p cnf {VARIABLES} {CLAUSES}\n".encode("ascii"),
                "Unexpected original DIMACS header")
        for raw in stream:
            h.update(raw)
            count += 1
            fields = raw.split()
            require(fields and fields[-1] == b"0" and len(fields) >= 2,
                    f"Malformed DIMACS clause at index {count}")
            numbers = [int(v) for v in fields[:-1]]
            require(0 not in numbers and all(
                1 <= abs(n) <= VARIABLES for n in numbers
            ), f"Invalid literal at clause {count}")
            if count <= PACKING:
                require(len(numbers) == 2 and all(n < 0 for n in numbers),
                        f"Unexpected binary-packing clause at {count}")
            else:
                require(len(numbers) == 5 and all(n > 0 for n in numbers),
                        f"Unexpected positive-domination clause at {count}")
            if not any(assignment[abs(n)] == (n > 0) for n in numbers):
                raise ValueError(
                    f"SAT assignment falsifies original clause #{count}: {numbers}"
                )
    require(count == CLAUSES,
            f"Expected {CLAUSES} clauses, checked {count}")
    digest = h.hexdigest()
    require(digest == EXPECTED_CNF_SHA,
            f"Original CNF SHA-256 differs: {digest}")
    print("PHASE 1/2 PASSED: complete DIMACS model check")
    print("  Clauses satisfied:", count)
    print("  CNF SHA256:", digest)
    print(f"  Elapsed seconds: {perf_counter() - started:.2f}")
    return digest


def check_squarefree_marker_semantics(assignment):
    started = perf_counter()
    contexts = list(independently_squarefree(11))
    require(len(contexts) == VARIABLES,
            f"Unexpected independent 11-factor count: {len(contexts)}")
    variable = {word: i for i, word in enumerate(contexts, 1)}
    del contexts

    adjacent = 0
    for w in independently_squarefree(12):
        adjacent += 1
        if assignment[variable[w[:11]]] and assignment[variable[w[1:]]]:
            raise ValueError(f"Adjacent marker conflict on factor {w}")
    require(adjacent == PACKING_ADJACENT,
            f"Unexpected 12-factor census: {adjacent}")

    distance_two = 0
    for w in independently_squarefree(13):
        distance_two += 1
        if assignment[variable[w[:11]]] and assignment[variable[w[2:]]]:
            raise ValueError(f"Distance-two marker conflict on factor {w}")
    require(distance_two == PACKING_DISTANCE_TWO,
            f"Unexpected 13-factor census: {distance_two}")

    domination = 0
    for w in independently_squarefree(15):
        domination += 1
        if not any(assignment[variable[w[i:i+11]]] for i in range(5)):
            raise ValueError(f"Unmarked five-position window on factor {w}")
    require(domination == DOMINATION,
            f"Unexpected 15-factor census: {domination}")

    print("PHASE 2/2 PASSED: independent sliding-block semantics")
    print("  Length-11 contexts:", VARIABLES)
    print("  Length-12 separation windows:", adjacent)
    print("  Length-13 separation windows:", distance_two)
    print("  Length-15 domination windows:", domination)
    print(f"  Elapsed seconds: {perf_counter() - started:.2f}")
    return {"contexts": VARIABLES, "adjacent_windows": adjacent,
            "distance_two_windows": distance_two, "domination_windows": domination}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cnf", type=Path, default=DEFAULT_CNF)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    started = perf_counter()
    assignment, model_sha = parse_complete_sat_model(args.model)
    selected = sum(assignment[1:])
    print("q=4, m=3, r=5 — INDEPENDENT SAT WITNESS VERIFICATION",
          flush=True)
    print("SAT model SHA256:", model_sha, flush=True)
    print("Assigned variables:", VARIABLES, flush=True)
    print("Selected length-11 contexts:", selected, flush=True)

    cnf_sha = check_every_dimacs_clause(args.cnf, assignment)
    counts = check_squarefree_marker_semantics(assignment)

    report = {
        "status": "INDEPENDENT SAT VERIFICATION PASSED",
        "parameters": {"q": 4, "m": 3, "r": 5,
                       "model": "shift-equivariant symmetric sliding-block",
                       "separation": 3, "domination_radius": 2},
        "cnf_sha256": cnf_sha,
        "sat_assignment_sha256": model_sha,
        "assigned_variables": VARIABLES,
        "selected_contexts": selected,
        "cnf_clauses_satisfied": CLAUSES,
        "independent_semantics": counts,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("ALL TWO PHASES PASSED")
    print("SAT upper bound CERTIFIED: r_min(4,3) <= 5")
    print("With archived radius-4 UNSAT theorem: EXACT r_min(4,3) = 5")
    print("Verification report:", args.report)
    print("Verification report SHA256:",
          sha256(args.report.read_bytes()).hexdigest())
    print(f"Total elapsed seconds: {perf_counter() - started:.2f}")
    print("Novelty and asymptotic bounds: NOT ESTABLISHED")


if __name__ == "__main__":
    main()
