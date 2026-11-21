#!/usr/bin/env python3
"""P1.4: independently audit every NAMED quaternary source, no orbit pruning.

Unlike tools/verify_exact_symmetry_rules.cpp, this verifier is C11 and
expands each marker table into a direct bitset of named-word decisions.
The verifier itself enumerates all square-free strings over 0,1,2,3,
without any symmetry reduction. In particular it tests 196,322,976
full length-19 words for the exact radius-seven S4 upper bound.

Checks the original SHA-256 pinned table, independent counts, known
invalid all-zero/all-one rules, and writes an exclusive verification report.
No original source table is altered.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from time import perf_counter

ROOT=Path(__file__).resolve().parent.parent
MANIFEST=ROOT/"artifacts/exact-symmetry-addendum-manifest.json"
CASES={
  "s4": {"radius":7,"group":24,"selected":47142,
         "len_counts":{"16":10895952,"17":28566216,"19":196322976},
         "sha256":"acfb277e3a960e83b7f490c9d34eb74d084791e5106b9d696010b8b7facdb354","bytes":754272},
  "a4": {"radius":6,"group":12,"selected":13611,
         "len_counts":{"14":1585128,"15":4156392,"17":28566216},
         "sha256":"a01bb64155b5300b3595d53cbd8d80fe32a5424dc75c629f397bdebfc412070d","bytes":190554},
  "s3": {"radius":6,"group":6,"selected":27586,
         "len_counts":{"14":1585128,"15":4156392,"17":28566216},
         "sha256":"f57833f190d9f8e60e32e59244ef27634b7478d947237115b1061317c082f3d2","bytes":386204},
  "v4i": {"radius":6,"group":4,"selected":41760,
         "len_counts":{"14":1585128,"15":4156392,"17":28566216},
         "sha256":"8e9963948203f991a1563c076e7b9ec5b6189537ebb58961580a8ced094b1ae2","bytes":584640},
}
EXPECTED_RESULT=re.compile(
    r"^VERIFIED_NAMED case=(\w+) radius=(\d+) group_order=(\d+) "
    r"selected_orbits=(\d+) expanded_decisions=(\d+) "
    r"length(\d+)=(\d+) length(\d+)=(\d+) length(\d+)=(\d+)$"
)

def require(ok,reason):
    if not ok:raise RuntimeError(reason)

def identity(path):
    require(path.is_file() and not path.is_symlink(),"Missing original source table")
    data=path.read_bytes()
    return {"size_bytes":len(data),"sha256":sha256(data).hexdigest()}

def execute(argv,timeout):
    start=perf_counter()
    proc=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True,
                        check=False,timeout=timeout)
    return proc,round(perf_counter()-start,3)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case",choices=tuple(CASES),required=True)
    ap.add_argument("--report",type=Path)
    args=ap.parse_args()
    spec=CASES[args.case]
    original=ROOT/f"proofs/m3/exact-symmetry/{args.case}_radius{spec['radius']}_selected_contexts.txt"
    match=identity(original)
    require((match["size_bytes"],match["sha256"])==
            (spec["bytes"],spec["sha256"]),"Original model byte/hash pin mismatch")
    manifest=json.loads(MANIFEST.read_text(encoding="utf8"))
    named_path=str(original.relative_to(ROOT))
    require(sum(row["path"]==named_path and row["bytes"]==spec["bytes"]
                and row["sha256"]==spec["sha256"]
                for row in manifest["files"])==1,
            "Original independent registry does not match verified source")

    cc=shutil.which("gcc")
    require(cc is not None,"gcc required for separate C11 exhaustive verifier")
    with tempfile.TemporaryDirectory(prefix="square-free-marker-named-positive-") as temp:
        exe=Path(temp)/"verify_named_words"
        build=subprocess.run([cc,"-O3","-std=c11","-Wall","-Wextra",
                              "-Werror","-pedantic",
                              str(ROOT/"tools/verify_named_positive_rules.c"),
                              "-o",str(exe)],
                             cwd=ROOT,capture_output=True,text=True,timeout=120)
        require(build.returncode==0,"Independent C11 compiler failed: "+build.stderr[-3000:])
        result,seconds=execute([str(exe),args.case,str(original),"valid"],840)
        require(result.returncode==0,"Independent named-word proof failed: "+
                (result.stdout+result.stderr)[-1800:])
        lines=result.stdout.strip().splitlines()
        require(len(lines)==1,"Unexpected named-word verification output")
        parsed=EXPECTED_RESULT.fullmatch(lines[0])
        require(parsed is not None,"Malformed named-word verifier output")
        case,radius,group,selected,expanded,n1,c1,n2,c2,n3,c3=parsed.groups()
        expected=spec["len_counts"]
        require(case==args.case and int(radius)==spec["radius"] and
                int(group)==spec["group"] and int(selected)==spec["selected"] and
                int(expanded)==spec["group"]*spec["selected"],
                "Independent named rule expansion census mismatch")
        actual={n1:int(c1),n2:int(c2),n3:int(c3)}
        require(actual==expected,"Full named square-free factor census mismatch")
        controls={}
        for kind,expected_error in (("none","RULE_FAILURE covering"),
                                    ("all","RULE_FAILURE distance1")):
            bad,bad_seconds=execute([str(exe),args.case,str(original),kind],60)
            require(bad.returncode!=0 and expected_error in bad.stderr,
                    f"FAIL OPEN on known-invalid {kind} marker rule")
            controls[kind]={"rejected":True,"reason":expected_error,
                            "elapsed_seconds":bad_seconds}
        report={
            "status":"INDEPENDENT FULL NAMED-SOURCE POSITIVE RULE VERIFICATION PASSED",
            "case":args.case,"radius":spec["radius"],
            "group_order":spec["group"],
            "selected_orbit_contexts":spec["selected"],
            "expanded_named_marked_contexts":int(expanded),
            "original_model":match,
            "named_squarefree_source_words_verified_by_length":actual,
            "full_named_enumeration_no_group_orbit_pruning":True,
            "distinct_implementation":"C11 bitset over all named contexts; direct finite-string recursion",
            "no_solver_or_original_verifier_called":True,
            "wall_seconds":seconds,
            "known_invalid_controls":controls,
            "scope_note":(
                "This is a second finite-source checker for packing and covering "
                "against every named square-free word. Its proof of the infinite "
                "marker property uses the usual finite-window argument. "
                "It is not a formally verified implementation."
            )
        }
        if args.report:
            output=args.report
            require(output.parent.is_dir() and not output.exists()
                    and not output.is_symlink(),"Report path missing or exists")
            with output.open("x",encoding="utf-8") as dest:
                json.dump(report,dest,indent=2,sort_keys=True)
                dest.write("\n")
        print(lines[0])
        print("KNOWN-INVALID POSITIVE-RULE CONTROLS REJECTED: all-zero and all-one")
        print(f"Elapsed independent named-word check: {seconds:.3f}s")
        print(report["status"])

if __name__=="__main__":
    main()
