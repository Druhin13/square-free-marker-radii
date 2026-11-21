#!/usr/bin/env python3
"""Audit finite-certificate semantics and mathematical trust boundaries.

This verifier checks original source certificates, the classical
substitution's finite sanity conditions, radius-four source classes,
certificate-family entry points, and adversarial four-cycle mutations.
It does not claim that a finite computation proves Hall--Thue.
"""
from __future__ import annotations
from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import json
from pathlib import Path
import tempfile
import argparse

from tools.verify_manifest import verify_registry as original_registry
from tools.verify_subgroup_manifest import verify_registry as subgroup_registry
from tools.verify_positive_manifest import verify_registry as positive_registry
from tools.verify_exact_symmetry_addendum import check_manifest
from tools import verify_new_c4_core as c4

ROOT=Path(__file__).resolve().parent.parent


def need(ok,msg):
    if not ok: raise ValueError(msg)

def squarefree(w):
    return all(w[i:i+d]!=w[i+d:i+2*d]
       for i in range(len(w)) for d in range(1,(len(w)-i)//2+1))

def hall_premise_sanity():
    substitution={"0":"012","1":"02","2":"1"}
    images=dict(substitution)
    for _ in range(2):
        images={ch:"".join(substitution[c] for c in word)
                for ch,word in images.items()}
    need(all(set(word)==set("012") for word in images.values()),
         "Hall substitution lacks elementary primitivity witness")
    prefix="0"
    while len(prefix)<1024:
        prefix="".join(substitution[ch] for ch in prefix)
    need(squarefree(prefix[:1024]),"Finite Hall prefix is not square-free")
    stuck="010201030102010"
    need(squarefree(stuck) and
         all(not squarefree(a+stuck) and not squarefree(stuck+a)
             for a in "0123"),
         "Incorrect nonextendible finite-only source example")
    # Explicit negative margin control: D=2, a=0=D-2:
    # the center 3031 is square-free, but prepending 0 makes square 0303.
    need(squarefree("3031") and not squarefree("03031"),
         "Separator D-1 margin sharpness example changed")
    return {
        "substitution":substitution,
        "third_iterate_contains_all_letters":True,
        "finite_prefix_length":1024,
        "nonextendible_finite_source":stuck,
        "D_minus_two_margin_negative_control":"0 + 3031 yields square 0303",
        "infinite_Hall_theorem_NOT_proved_by_prefix_check":True,
    }

def radius_four_source_census():
    easy=json.loads((ROOT/"proofs/m3/square-free-marker-q4-m3-r4-easy-core-witnesses.json")
                    .read_text("utf-8"))
    rest=json.loads((ROOT/"proofs/m3/square-free-marker-q4-m3-r4-remaining-core-extensions.json")
                    .read_text("utf-8"))
    first=Counter(row["kind"] for row in easy["certificates"])
    later=Counter(row["kind"] for row in rest["candidate_certificates"])
    need(first=={
        "hall":101,"single-separator":5801,
        "double-separator-with-margins":6079},
        "Radius-four original first-source partition changed")
    need(later=={
        "multi-separator":12233,
        "external-double-separator":78},
        "Radius-four original remaining-source partition changed")
    need(rest.get("unresolved")==[] and
         len(easy["certificates"])+len(rest["candidate_certificates"])==24292,
         "Some original radius-four clauses lack extension certificates")
    return {"easy":dict(sorted(first.items())),
            "remaining":dict(sorted(later.items())),
            "unresolved":0,"clauses":24292}

def c4_semantic_negative_controls():
    original_source=c4.SOURCE
    original_pin=c4.PIN
    archive=json.loads(original_source.read_text("utf-8"))
    with redirect_stdout(io.StringIO()):
        result=c4.main()
    need(result.get("source_count")==11 and
         result.get("Boolean_assignments_refuted")==512,
         "Original eleven-source C4 auditor no longer passes")

    def bad_source(rows):
        rows[0]["source"]="3"*len(rows[0]["source"])
    def wrong_clause(rows):
        x=rows[0]["clause"][0]
        rows[0]["clause"][0]=x[1:] if x.startswith("-") else "-"+x
    def wrong_offset(rows):
        rows[0]["offset"]+=1
    def missing_exterior(rows):
        w=rows[0]["Z"]
        rows[0]["Z"]=str(rows[0]["separator"])+w[1:]

    mutants={"invalid_source":bad_source,"incorrect_clause":wrong_clause,
             "bad_source_offset":wrong_offset,
             "inadequate_full_exterior":missing_exterior}
    rejected={}
    try:
        with tempfile.TemporaryDirectory(prefix="square-free-marker-c4-mutants-") as d:
            for name,mutate in mutants.items():
                rows=deepcopy(archive)
                mutate(rows)
                raw=(json.dumps(rows,sort_keys=True)+"\n").encode("utf-8")
                path=Path(d)/(name+".json")
                path.write_bytes(raw)
                # In this test ONLY, re-pin the TEMPORARY mutant so that
                # the semantic checker (not just the SHA gate) must reject it.
                c4.SOURCE=path
                c4.PIN=sha256(raw).hexdigest()
                try:
                    with redirect_stdout(io.StringIO()):
                        c4.main()
                except (AssertionError, ValueError, KeyError, TypeError) as error:
                    rejected[name]=type(error).__name__
                else:
                    raise ValueError("FAIL-OPEN C4 source checker: "+name)
    finally:
        c4.SOURCE,c4.PIN=original_source,original_pin
    need(len(rejected)==4,"Some C4 mutant controls were skipped")
    return {"original_source_count":11,"truth_assignments_refuted":512,
            "semantically_rejected_mutants":rejected,
            "production_proof_inputs_unchanged":True}

def verification_contract():
    """Check source entry points and public CI wiring, not workflow outcomes.

    Semantic validity is established separately by the independent certificate
    validators and the adversarial controls above.
    """
    import reproduce
    families=("main", "subgroups", "swap", "double", "exact", "trust", "lrat")
    need(reproduce.CASES==families,"Certificate-family interface changed")
    source=(ROOT/"reproduce.py").read_text("utf-8")
    required=(
        "tools/run_verification.py", "tools.run_subgroup_verification",
        "tools.run_positive_verification", "tools/verify_exact_symmetry_addendum.py",
        "tools.verify_exact_stabilizers", "tools.audit_theorem_trust_boundaries",
        "tools.verify_secondary_lrat", "tools.verify_secondary_lrat_radius4",
        "tools.verify_secondary_lrat_subgroups",
    )
    need(all(name in source for name in required),
         "Missing a certificate-family verification entry point")
    workflow=ROOT.parent/".github/workflows/verify-evidence.yml"
    need(workflow.is_file() and not workflow.is_symlink(),
         "Missing public verification workflow")
    ci=workflow.read_text("utf-8")
    require=("pull_request:", "permissions:", "contents: read",
             "sha256sum --check --strict SHA256SUMS",
             "matrix:", "case: [main, subgroups, swap, double, exact, trust, lrat]",
             "python3 -B reproduce.py --case")
    need(all(token in ci for token in require),
         "Public verification workflow entry points changed")
    return {"reproduction_families":list(families),
            "source_entrypoints_present":len(required),
            "read_only_ci_entrypoints_present":True,
            "static_presence_is_not_green_CI":True}

EXTERNAL_PREMISES=[
 "Square-freeness of the exact infinite Hall--Thue fixed point",
 "Primitive substitution => uniform recurrence and two-sided orbit closure",
 "Reversal and alphabet relabeling preserve whole-word square-freeness",
 "Single-separator gluing with COMPLETE square-free zero-free rays",
 "Multiple-separator gluing with D-1 margins on COMPLETE zero-free rays",
 "Each finite negative clause is required by its genuinely bi-infinite source",
 "The implication from verified UNSAT of necessary clauses to no valid rule",
 "The finite-window implication from a valid finite-source marker table",
 "Conjugacy of subgroups preserves marker-rule validity",
 "Krieger-marker existence for compact zero-dimensional aperiodic quotient",
]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    a,main_bytes=original_registry(ROOT/"artifacts/manifest.json",True)
    b,sub_bytes=subgroup_registry()
    c,pos_bytes=positive_registry()
    exact=check_manifest()
    need((a,b,c,len(exact["files"]))==(21,23,3,5),
         "Theorem proof registry counts disagree")
    report={
      "status":"THEOREM TRUST-BOUNDARY AUDIT PASSED",
      "pinned_proof_registry_counts":{"main":a,"subgroup_negative":b,
            "subgroup_positive":c,"exact_addendum":len(exact["files"])},
      "pinned_proof_registry_bytes":{"main":main_bytes,
          "subgroup_negative":sub_bytes,"subgroup_positive":pos_bytes},
      "radius_four_source_classes":radius_four_source_census(),
      "hall_and_separator_sanity_not_a_formal_proof":hall_premise_sanity(),
      "four_cycle_semantic_negative_controls":c4_semantic_negative_controls(),
      "verifier_entrypoint_contract":verification_contract(),
      "unmechanized_mathematical_premises":EXTERNAL_PREMISES,
      "scope_note":"Does not formally prove the Hall--Thue infinite fixed point, "
       "two separator lemmas, all source mappings, or paper originality. "
       "Source-level checks and complete CI workflows remain separate."
    }
    if args.report is not None:
        target=args.report
        need(target.parent.is_dir() and not target.exists()
             and not target.is_symlink(),"Report path missing or preexisting")
        with target.open("x",encoding="utf8") as f:
            json.dump(report,f,indent=2,sort_keys=True)
            f.write("\n")
    print(report["status"])
    print("Archived proof inputs:",a,b,c,len(exact["files"]))
    print("Radius-four source clauses:",report["radius_four_source_classes"]["clauses"])
    print("Semantic C4 controls rejected:",
          len(report["four_cycle_semantic_negative_controls"]["semantically_rejected_mutants"]))
    print("Classical infinite-word premises remain MATHEMATICAL, not executable")
if __name__=="__main__":
    main()
