#!/usr/bin/env python3
"""Independently audit the easy-extendible m=3,r=4 core subformula.

No imports from the exporter, original SAT instance generator, or triage
module. Checks every retained clause against the archived candidate
witness and a fresh Hall-Thue orbit catalogue, checks squarefreeness,
the separator lemmas' preconditions, and compares DIMACS bytes exactly.

    python3 -m scripts.audit_m3_r4_easy_core_independent

The audit does NOT conclude UNSAT. A separate SAT solver, and DRAT-trim
when UNSAT, are needed.
"""
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_CORE = Path("/tmp/kbl-m3-r4-core3.cnf")
SUB_CNF = ROOT / "experiments/m3/kbl-q4-m3-r4-easy-core.cnf"
WITNESSES = ROOT / "experiments/m3/kbl-q4-m3-r4-easy-core-witnesses.json"
CORE_HASH = "a2f66feec531e8cd08abe79f9a619eb0177129c482577521d735b133060467f3"
FULL_HASH = "bffb20dd55f501abe4e79249216b4836762579552cdf03ccff5b5c32120418d2"


def squarefree(word):
    n = len(word)
    for a in range(n):
        for period in range(1, (n-a)//2+1):
            if all(word[a+j] == word[a+period+j] for j in range(period)):
                return False
    return True


def lex_factors(n):
    result = [()]
    for _ in range(n):
        next_items = []
        for prefix in result:
            for symbol in range(4):
                child = prefix + (symbol,)
                if squarefree(child):
                    next_items.append(child)
        result = next_items
    return result


def hall_factors():
    phi = ("012", "02", "1")
    thue = "0"
    while len(thue) < 12000:
        thue = "".join(phi[int(char)] for char in thue)
    thue = thue[:12000]
    perms = list(permutations(range(3)))
    catalog = {0: {()}}
    for length in range(1,14):
        values = set()
        for i in range(len(thue)-length+1):
            factor = thue[i:i+length]
            for perm in perms:
                mapped = tuple(perm[int(c)] for c in factor)
                values.add(mapped)
                values.add(mapped[::-1])
        catalog[length] = values
    return catalog


def clauses_from_cnf(path, header, count):
    raw = path.read_bytes()
    lines = raw.decode("ascii").splitlines()
    if not lines or lines[0] != header:
        raise ValueError(f"Bad DIMACS header: {path}")
    clauses = []
    for line in lines[1:]:
        if not line or line.startswith("c"):
            continue
        nums = tuple(map(int,line.split()))
        if len(nums) < 2 or nums[-1] != 0 or 0 in nums[:-1]:
            raise ValueError(f"Malformed DIMACS clause in {path}")
        clause = tuple(sorted(nums[:-1]))
        if len(set(clause)) != len(clause):
            raise ValueError(f"Duplicate literal in {path}")
        if any(not 1 <= abs(x) <= 12768 for x in clause):
            raise ValueError(f"Out-of-range literal in {path}")
        clauses.append(clause)
    if len(clauses) != count or len(set(clauses)) != count:
        raise ValueError(f"Clause count/duplicates wrong in {path}")
    return clauses, sha256(raw).hexdigest()


def audit_certificate(record, ids, hall):
    source = record["word"]
    role = record["role"]
    kind = record["kind"]
    sep = record["separator"]
    if len(source) != (11 if role == "packing" else 13):
        raise ValueError(f"Wrong factor length: {source}")
    if set(source) - set("0123"):
        raise ValueError(f"Invalid symbols in {source}")
    w = tuple(int(c) for c in source)
    if not squarefree(w):
        raise ValueError(f"Non-square-free witness: {source}")

    decisions = [ids[w[i:i+9]] for i in range(len(w)-8)]
    clause = tuple(sorted(record["clause"]))
    if role == "packing":
        valid = {
            tuple(sorted((-decisions[i],-decisions[j])))
            for i,j in ((0,1),(0,2),(1,2))
        }
        if len(clause) != 2 or clause not in valid:
            raise ValueError(f"Not a packing clause for witness {source}")
    elif role == "domination":
        expected = tuple(sorted(decisions))
        if len(clause) != 5 or len(set(expected)) != 5 or clause != expected:
            raise ValueError(f"Not a domination clause for witness {source}")
    else:
        raise ValueError(f"Unknown clause role {role}")

    alphabet = sorted(set(w))
    if kind == "hall":
        if sep is not None or len(alphabet) != 3:
            raise ValueError(f"Invalid Hall witness metadata: {source}")
        renaming = {c: i for i,c in enumerate(alphabet)}
        normalized = tuple(renaming[c] for c in w)
        if normalized not in hall[len(w)]:
            raise ValueError(f"Not a Hall orbit word: {source}")
    elif kind in ("single-separator","double-separator-with-margins"):
        if not isinstance(sep,int) or sep not in alphabet or len(alphabet) != 4:
            raise ValueError(f"Invalid separator metadata: {source}")
        positions = [i for i,x in enumerate(w) if x == sep]
        expected_occurrences = 1 if kind == "single-separator" else 2
        if len(positions) != expected_occurrences:
            raise ValueError(f"Incorrect separator multiplicity: {source}")
        remaining = sorted(set(w)-{sep})
        renaming = {c: i for i,c in enumerate(remaining)}
        left = tuple(renaming[c] for c in w[:positions[0]])
        right = tuple(renaming[c] for c in w[positions[-1]+1:])
        if left not in hall[len(left)] or right not in hall[len(right)]:
            raise ValueError(f"Hall exterior mismatch: {source}")
        if expected_occurrences == 2:
            d = positions[1]-positions[0]
            if positions[0] < d-1 or len(w)-positions[1]-1 < d-1:
                raise ValueError(f"Double-separator safety margins fail: {source}")
    else:
        raise ValueError(f"Unknown constructive witness type: {kind}")
    return clause


def main():
    core, got_core_hash = clauses_from_cnf(
        SOURCE_CORE, "p cnf 12768 24292", 24292
    )
    if got_core_hash != CORE_HASH:
        raise ValueError(f"Source core hash mismatch: {got_core_hash}")
    result, result_sha = clauses_from_cnf(
        SUB_CNF, "p cnf 12768 11981", 11981
    )
    if not set(result) <= set(core):
        raise ValueError("Subformula has clauses missing from verified core")
    histogram = Counter(map(len,result))
    if histogram != {2:9075, 5:2906}:
        raise ValueError(f"Unexpected kept clause histogram: {histogram}")

    data = json.loads(WITNESSES.read_text(encoding="utf-8"))
    if (data.get("source_core_sha256") != CORE_HASH or
        data.get("source_cnf_sha256") != FULL_HASH or
        data.get("subformula_sha256") != result_sha):
        raise ValueError("Witness manifest references different formulas")
    certs = data["certificates"]
    if len(certs) != 11981:
        raise ValueError(f"Expected 11981 certificates, got {len(certs)}")

    contexts = lex_factors(9)
    if len(contexts) != 12768:
        raise ValueError("Unexpected context count")
    ids = {w: i+1 for i,w in enumerate(contexts)}
    hall = hall_factors()
    seen = set()
    kinds = Counter()

    for record in certs:
        clause = audit_certificate(record, ids, hall)
        if clause not in result or clause in seen:
            raise ValueError(f"Invalid/duplicate certificate for clause {clause}")
        seen.add(clause)
        kinds[record["kind"]] += 1
    if seen != set(result):
        raise ValueError("Missing certificate for one or more subformula clauses")

    ordered = sorted(seen, key=lambda c: (len(c), c))
    constructed = (
        f"p cnf 12768 {len(ordered)}\n" +
        "".join(" ".join(map(str,c)) + " 0\n" for c in ordered)
    ).encode("ascii")
    if constructed != SUB_CNF.read_bytes():
        raise ValueError("Byte-for-byte DIMACS reproduction failed")

    print("INDEPENDENT EASY-EXTENDIBLE SUBFORMULA AUDIT PASSED")
    print("Subformula SHA256:", result_sha)
    print("Certificates SHA256:", sha256(WITNESSES.read_bytes()).hexdigest())
    print("Certified packing clauses:", histogram[2])
    print("Certified domination clauses:", histogram[5])
    print("Total certified core constraints:", len(seen))
    print("Certificate types:", dict(sorted(kinds.items())))
    print("Subset of verified third UNSAT core: YES")
    print("Explicit finite-factor extension conditions: VERIFIED")
    print("SAT/UNSAT of certified subset: NOT YET DETERMINED")
    print("No r>=5 lower-bound claim")


if __name__ == "__main__":
    main()
