#!/usr/bin/env python3
"""Independently SHA/Git-blob-pin and audit three exact radius-five stabilizers.

Original model validity and SAT constraints are separately certified. Here
we check all 87,936 named n=11 square-free contexts under all 24 alphabet
permutations using fresh (not imported) lexical context/orbit indexing.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
from tools.verify_positive_manifest import ROOT, verify_registry

ROOT_MODEL = ROOT / "proofs/m3/square-free-marker-q4-m3-r5-result.txt"
SWAP_MODEL = ROOT / "proofs/m3/square-free-marker-q4-m3-r5-swap01-result.txt"
DOUBLE_MODEL = ROOT / "proofs/m3/double01-23/square-free-marker-m3-r5-double01-23-result.txt"
ORIGINAL_SHA = "d5ba5df3f93f6e996ffe1164d2dcb2886e0f530638f894b45a090ea79d2eb7c7"
DOUBLE_SHA = "a3acf3c855420b8578c9882e2aab367de959a33093640084a62b3aa522b7d9be"
EXPECTED = (
    ("unrestricted", ROOT_MODEL, 87936, 24120, {"0123"}),
    ("transposition", SWAP_MODEL, 43968, 11889, {"0123", "1023"}),
    ("double-transposition", DOUBLE_MODEL, 43968, 12095, {"0123", "1032"}),
)

def need(ok, message):
    if not ok:
        raise AssertionError(message)

def digest(path):
    h = sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1 << 20), b""):
            h.update(data)
    return h.hexdigest()

def suffix_square(word):
    return any(word[-2*p:-p] == word[-p:]
               for p in range(1, len(word)//2 + 1))

def named11():
    def rec(prefix):
        if len(prefix) == 11:
            yield prefix
            return
        for symbol in "0123":
            word = prefix + symbol
            if not suffix_square(word):
                yield from rec(word)
    return tuple(rec(""))

def model(path, n):
    need(path.is_file() and not path.is_symlink(),
         "Missing/unsafe signed SAT model")
    raw = path.read_text("ascii")
    status, values, ended = [], [], False
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("c "):
            continue
        if line.startswith("s "):
            status.append(line)
            continue
        need(line.startswith("v "), "Unexpected CaDiCaL line")
        for field in line.split()[1:]:
            lit = int(field)
            if lit == 0:
                need(not ended, "Multiple SAT terminators")
                ended = True
            else:
                need(not ended, "SAT variables after terminator")
                values.append(lit)
    need(status == ["s SATISFIABLE"] and ended and len(values) == n,
         "Incomplete signed SAT model")
    out = [None] * (n+1)
    for lit in values:
        index = abs(lit)
        need(1 <= index <= n and out[index] is None,
             "Invalid/duplicate SAT variable")
        out[index] = lit > 0
    need(all(value is not None for value in out[1:]),
         "Incomplete signed variable assignment")
    return out

def decisions(contexts, assignment, label):
    if label == "unrestricted":
        return assignment[1:]
    perm = "1023" if label == "transposition" else "1032"
    translate = str.maketrans("0123", perm)
    def canonical(w):
        return min(w, w.translate(translate))
    representatives = sorted({canonical(w) for w in contexts})
    need(len(representatives) == 43968, "Wrong orbit-variable census")
    ids = {w: i for i,w in enumerate(representatives,1)}
    return [assignment[ids[canonical(w)]] for w in contexts]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        help="A new, exclusively created deterministic JSON report")
    args = parser.parse_args()
    require_count, _ = verify_registry()
    need(require_count == 3 and ROOT_MODEL.stat().st_size == 595752
         and digest(ROOT_MODEL) == ORIGINAL_SHA and digest(DOUBLE_MODEL) == DOUBLE_SHA,
         "SHA-256/Git blob data identity mismatch")
    contexts = named11()
    need(len(contexts) == 87936 and len(set(contexts)) == 87936,
         "Original named length-11 square-free census mismatch")
    ids = {w:i for i,w in enumerate(contexts)}
    group = tuple("".join(x) for x in permutations("0123"))
    need(len(group) == 24, "S4 permutation census mismatch")
    results = {}
    for label,path,n,selected,expected in EXPECTED:
        flags = model(path, n)
        need(sum(flags[1:]) == selected, "Unexpected SAT marked census")
        observed = decisions(contexts, flags, label)
        differences = {}
        for permutation in group:
            action = str.maketrans("0123", permutation)
            differences[permutation] = sum(
                bit != observed[ids[word.translate(action)]]
                for word,bit in zip(contexts, observed))
        exact = {p for p,d in differences.items() if d == 0}
        need(exact == expected, f"Wrong exact stabilizer: {label}: {exact}")
        if label == "unrestricted":
            other = {p:n for p,n in differences.items() if p != "0123"}
            need(min(other.values()) == 10528 and other["0213"] == 10528,
                 "Unrestricted nearest nonidentity mismatch not 10,528")
        results[label] = {
            "original_model_sha256": digest(path),
            "variables": n,
            "marked_variables": selected,
            "contexts_tested": len(contexts),
            "permutations_tested": len(group),
            "exact_stabilizer_images": sorted(exact),
            "permutation_decision_disagreements": dict(sorted(differences.items())),
        }
        print("EXACT STABILIZER VERIFIED:", label, sorted(exact), flush=True)
    report = {
        "status": "ALL THREE RADIUS-FIVE EXACT STABILIZERS VERIFIED",
        "scope": "q4 m3 r5 marker decision, input alphabet S4 action",
        "mathematical_input": "Each model's marker validity is separately source-certified",
        "results": results,
    }
    raw = (json.dumps(report,sort_keys=True,indent=2)+"\n").encode()
    if args.report:
        need(args.report.parent.is_dir() and not args.report.exists()
             and not args.report.is_symlink(), "Unsafe existing report path")
        with args.report.open("xb") as f:
            f.write(raw)
        print("Report SHA256:",sha256(raw).hexdigest(),flush=True)
    print(report["status"],flush=True)

if __name__ == "__main__":
    main()
