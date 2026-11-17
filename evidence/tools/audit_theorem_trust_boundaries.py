#!/usr/bin/env python3
"""P1.5: audit theorem-to-source trust boundaries, not formalize infinite math.

The large UNSAT and positive tables are checked by SEPARATE workflows.
This gate cross-checks original sources, actual vs finite word language,
the classical substitution's primitivity, all radius-four source kinds,
the expected proof entrypoints, and four adversarial C4 source changes.
It explicitly does not assert that a Python script proves Hall--Thue.
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

WORKFLOWS={
 ".github/workflows/manuscript-draft.yml": (
    "tools/run_verification.py --full",
    "tools.run_subgroup_verification",
    "tools.run_positive_verification --case swap",
    "tools.run_positive_verification --case double",
    "tools.verify_hall_actual_language_stabilizer",
 ),
 ".github/workflows/exact-symmetry-addendum.yml": (
    "tools/verify_exact_symmetry_addendum.py",),
 ".github/workflows/named-positive-rules.yml": (
    "tools/run_named_positive_audit.py",
    "case: [s4, a4, s3, v4i]"),
 ".github/workflows/verified-lrat-radius4.yml": (
    "tools/verify_secondary_lrat_radius4.py", "tools/build_cake_lpr.sh"),
 ".github/workflows/verified-lrat-subgroups.yml": (
    "tools.verify_secondary_lrat_subgroups",
    "case: [cycle012, normal-v4, intransitive-v4]"),
}

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
    easy=json.loads((ROOT/"proofs/m3/kbl-q4-m3-r4-easy-core-witnesses.json")
                    .read_text("utf-8"))
    rest=json.loads((ROOT/"proofs/m3/kbl-q4-m3-r4-remaining-core-extensions.json")
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
        with tempfile.TemporaryDirectory(prefix="kbl-c4-mutants-") as d:
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

def publication_contract():
    tex=(ROOT/"paper/main.tex").read_text("utf-8")
    labels=(
       "prop:finite-clauses","lem:single-separator","lem:separator",
       "lem:tenclauses","lem:fourcycle","thm:subgroup",
       "lem:new-c4-r6","thm:exact-subgroup-radii",
       "cor:exact-stabilizers","thm:main","tab:c4-core",
    )
    need(all(tex.count("\\label{"+label+"}")==1 for label in labels),
         "Missing or repeated theorem proof boundary labels")
    need("r_{\\Sym}(4,3)=7" in tex and
         "r_{\\mathrm{all}}(4,3)=5" in tex and
         "\\Lang_n(\\Xsf)" in tex,
         "Exact theorem or actual source-language caveat missing")
    hooks={}
    for file,needles in WORKFLOWS.items():
        path=ROOT/file
        need(path.is_file() and not path.is_symlink(),
             "Required checker workflow missing")
        content=path.read_text("utf-8")
        need(all(x in content for x in needles),
             "A theorem-critical checker has lost its CI entrypoint: "+file)
        hooks[file]=list(needles)
    return {"manuscript_labels":list(labels),
            "workflow_commands_present":hooks,
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
      "theorem_and_CI_static_contract":publication_contract(),
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
