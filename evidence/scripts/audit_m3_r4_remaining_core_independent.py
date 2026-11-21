#!/usr/bin/env python3
"""Independently audit all additional m=3,r=4 third-core extension candidates.

Uses previously developed INDEPENDENT finite-witness and clause checker
only; does not import the new bulk constructor or its search routines.

Every new candidate must match a missing original core clause and pass
independent checks for the finite factor, normalization, square-freeness,
Hall-Thue factor membership, and generalized separator safety margins.
The 11,981 earlier certificates are audited separately.

From the evidence/ directory (all input certificates are included):
    python3 -B -m scripts.audit_m3_r4_remaining_core_independent

Do NOT claim a stronger radius lower bound from a partial coverage result.
Even 100% coverage still requires direct DRAT checking of the exact
third-core CNF and preservation of all certificate files.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from scripts.audit_m3_r4_violation_extensions_independent import (
    check_record, contexts9, hall_catalog,
)
from scripts.audit_m3_r4_easy_core_independent import clauses_from_cnf

ROOT=Path(__file__).resolve().parent.parent
CORE=ROOT/"proofs/m3/square-free-marker-q4-m3-r4-core.cnf"
EASY=ROOT/"proofs/m3/square-free-marker-q4-m3-r4-easy-core.cnf"
MANIFEST=ROOT/"proofs/m3/square-free-marker-q4-m3-r4-remaining-core-extensions.json"

CORE_SHA="a2f66feec531e8cd08abe79f9a619eb0177129c482577521d735b133060467f3"
EASY_SHA="925d9b7e28384bca92f29818b97a24d37b8aabe19b39d65041c4b7ca7ca5a833"


def require(test,reason):
    if not test:
        raise ValueError(reason)


def main():
    core,core_sha=clauses_from_cnf(CORE,"p cnf 12768 24292",24292)
    easy,easy_sha=clauses_from_cnf(EASY,"p cnf 12768 11981",11981)
    require(core_sha==CORE_SHA and easy_sha==EASY_SHA,
            "Third core or easy subformula hash mismatch")
    core=set(core)
    easy=set(easy)
    require(easy<=core,"Easy clauses not contained in certified finite core")
    remaining=core-easy
    require(Counter(map(len,remaining))=={2:5292,5:7019},
            "Unexpected missing-core clause classes")

    raw=MANIFEST.read_bytes()
    data=json.loads(raw.decode("utf-8"))
    require(data.get("source_core_sha256")==CORE_SHA and
            data.get("source_easy_sha256")==EASY_SHA and
            data.get("total_missing_clauses")==12311,
            "Extension manifest references unexpected core/easy formula")
    candidates=data.get("candidate_certificates")
    unresolved=data.get("unresolved")
    require(isinstance(candidates,list) and isinstance(unresolved,list),
            "Malformed certificate or unresolved list")
    require(len(candidates)+len(unresolved)==12311,
            "Manifest does not partition all 12311 missing clauses")

    index=contexts9()
    hall=hall_catalog()
    checked=set()
    roles=Counter()
    kinds=Counter()
    for item in candidates:
        clause,role,source=check_record(item,index,hall)
        require(clause in remaining and clause not in checked,
                "Candidate is duplicated or not a missing core clause")
        checked.add(clause)
        roles[role]+=1
        kinds[item["kind"]]+=1

    unresolved_roles=Counter()
    for item in unresolved:
        clause=tuple(sorted(item["clause"]))
        role=item["role"]
        require(clause in remaining and clause not in checked,
                "Unresolved item repeated or outside missing core")
        require(role==("packing" if len(clause)==2 else "domination"),
                "Unresolved role disagrees with clause type")
        checked.add(clause)
        unresolved_roles[role]+=1

    require(checked==remaining,
            "Manifest does not cover the missing-core clause set")
    require(roles["packing"]+unresolved_roles["packing"]==5292,
            "Packing core clause partition mismatch")
    require(roles["domination"]+unresolved_roles["domination"]==7019,
            "Domination core clause partition mismatch")

    require(not unresolved,
            "Unresolved radius-four core clauses remain: proof of full source realization is INCOMPLETE")

    print("INDEPENDENT BULK RADIUS-4 EXTENSION AUDIT PASSED")
    print("Third core SHA256:",CORE_SHA)
    print("Easy CNF SHA256:",EASY_SHA)
    print("Candidate manifest SHA256:",sha256(raw).hexdigest())
    print("New audited packing certificates:",roles["packing"],"/5292")
    print("New audited domination certificates:",roles["domination"],"/7019")
    print("New audited certificates total:",len(candidates))
    print("Construction types:",dict(sorted(kinds.items())))
    print("Unresolved clauses:",len(unresolved))
    print("Certified core clauses altogether:",len(easy)+len(candidates),"/24292")
    print("Every missing core clause accounted for: YES")
    print("FULL CORE HAS FINITE EXTENSION CERTIFICATES: YES")
    print("NEXT: independently re-audit the easy certificates and directly")
    print("verify a DRAT refutation on this EXACT 24292-clause core.")
    print("NO r>=5 CLAIM FROM THIS SCRIPT ALONE")


if __name__=="__main__":
    main()
