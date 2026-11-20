#!/usr/bin/env python3
"""Hash-pin and independently reproduce the exact-symmetry certificate family.

No external SAT solver, network dependency, historical generator, or
previous verifier implementation is required. The input tables are
owner-supplied research data, not a different human author's work. Proves candidate marker validity on ALL
finite square-free words by H-orbit-representative enumeration, checks
11 bi-infinite-source-backed C4 radius-six contradiction clauses, then
independently enumerates the 30 subgroup classes. Mathematical use of
Hall--Thue requires its classical squarefreeness/uniform recurrence theorem.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "artifacts/exact-symmetry-addendum-manifest.json"
EXPECTED = {
    "s4":(7,"S4",47142,{"16":453998,"17":1190259,"19":8180124}),
    "a4":(6,"A4",13611,{"14":132094,"15":346366,"17":2380518}),
    "s3":(6,"S3",27586,{"14":264188,"15":692732,"17":4761036}),
    "v4i":(6,"V4i",41760,{"14":396282,"15":1039098,"17":7141554}),
}
EXPECTED_PATHS={
    f"proofs/m3/exact-symmetry/{case}_radius{radius}_selected_contexts.txt"
    for case,(radius,_,_,_) in EXPECTED.items()
} | {"proofs/m3/exact-symmetry/c4_radius6_core.json"}

def require(ok,reason):
    if not ok:raise ValueError(reason)

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def check_manifest():
    require(MANIFEST.is_file() and not MANIFEST.is_symlink(),"Missing/unsafe manifest")
    manifest=json.loads(MANIFEST.read_text("utf-8"))
    require(manifest.get("schema_version")==1,"Unsupported source registry schema")
    rows=manifest.get("files",[])
    require(len(rows)==5 and {e["path"] for e in rows}==EXPECTED_PATHS,
            "Unapproved proof input paths")
    for row in rows:
        require(re.fullmatch(r"[a-f0-9]{64}",row["sha256"]) is not None,
                "Bad SHA pin")
        p=ROOT/row["path"]
        require(p.is_file() and not p.is_symlink() and
                p.stat().st_size==row["bytes"] and sha(p)==row["sha256"],
                "Proof input original SHA/size mismatch: "+row["path"])
    for case,(r,g,n,counts) in EXPECTED.items():
        x=manifest["cases"][case]
        require((x["radius"],x["group"],x["selected"],x["checks"]) ==
                (r,g,n,counts),"Archive metadata unexpected for "+case)
    return manifest


def run():
    manifest=check_manifest()
    gpp=shutil.which("g++")
    require(gpp is not None,"C++ compiler g++ is needed for independent exhaustive check")
    with tempfile.TemporaryDirectory(prefix="kbl-exact-radius-") as temp:
        exe=Path(temp)/"verify_rules"
        subprocess.run([gpp,"-std=c++17","-O2","-Wall","-Wextra","-Werror",
                        "-pedantic",str(ROOT/"tools/verify_exact_symmetry_rules.cpp"),
                        "-o",str(exe)],cwd=ROOT,check=True)
        for case,(radius,group,selected,count) in EXPECTED.items():
            filename=ROOT/f"proofs/m3/exact-symmetry/{case}_radius{radius}_selected_contexts.txt"
            print("\n=== INDEPENDENT EXHAUSTIVE RULE VERIFICATION:",case,"===",flush=True)
            subprocess.run([str(exe),str(radius),group,str(filename)],cwd=ROOT,check=True)
        print("\n=== INDEPENDENT SOURCE-CLAUSE LOWER BOUND ===",flush=True)
        subprocess.run(["python3","-B",str(ROOT/"tools/verify_new_c4_core.py")],cwd=ROOT,check=True,
                       stdout=subprocess.DEVNULL)
        print("C4 radius-six: 11 genuine-source clauses, 9 orbit variables, 512 assignments refuted",flush=True)
        print("\n=== ALL THIRTY S4 SUBGROUPS ===",flush=True)
        subprocess.run(["python3","-B",str(ROOT/"tools/verify_exact_symmetry_subgroups.py")],cwd=ROOT,check=True)
    print("\nALL OWNER-SUPPLIED EXACT-SYMMETRY PROOF INPUTS HASH-PINNED AND CHECKED",flush=True)

if __name__ == "__main__":
    run()
