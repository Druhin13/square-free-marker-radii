#!/usr/bin/env python3
"""Standalone finite-certificate verification for square-free marker radii.

All 52 registered proof objects are checked before and after each family.
The classical Hall--Thue and separator lemmas are NOT machine-formalized.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CASES = ("main", "subgroups", "swap", "double", "exact", "trust", "lrat")


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def ensure_portable_root(root):
    need(all((root / p).is_dir() for p in ("artifacts", "proofs", "tools", "scripts")),
         "Missing original source directories")


def original_proof_paths():
    entries = (
        ("artifacts/manifest.json", "artifacts", "relative_path", 21),
        ("artifacts/subgroup-manifest.json", "archives", "relative_path", 23),
        ("artifacts/subgroup-positive-manifest.json", "archives", "relative_path", 3),
        ("artifacts/exact-symmetry-addendum-manifest.json", "files", "path", 5),
    )
    result = set()
    for filename, key, field, count in entries:
        manifest = ROOT / filename
        need(manifest.is_file() and not manifest.is_symlink(), "Unsafe registry")
        rows = json.loads(manifest.read_text(encoding="utf-8")).get(key)
        need(isinstance(rows, list) and len(rows) == count, "Registry count drift")
        for entry in rows:
            path = entry[field]
            need(isinstance(path, str) and path.startswith("proofs/m3/")
                 and "\\" not in path and not path.startswith("/")
                 and all(x not in ("", ".", "..") for x in path.split("/"))
                 and path not in result, "Unsafe or duplicate proof registry entry")
            result.add(path)
    need(len(result) == 52, "Incomplete proof paths")
    return result


def verify_origins():
    from tools.verify_manifest import verify_registry as main_registry
    from tools.verify_subgroup_manifest import verify_registry as subgroup_registry
    from tools.verify_positive_manifest import verify_registry as positive_registry
    from tools.verify_exact_symmetry_addendum import check_manifest
    m, mbytes = main_registry(ROOT / "artifacts/manifest.json", True)
    s, sbytes = subgroup_registry()
    p, pbytes = positive_registry()
    e = check_manifest()
    need((m, s, p, len(e["files"])) == (21, 23, 3, 5), "Registry validation failed")
    paths = original_proof_paths()
    present = {str(p.relative_to(ROOT)) for p in (ROOT / "proofs").rglob("*") if p.is_file()}
    need(present == paths, "Missing/unregistered proof file")
    size = 0
    for item in paths:
        file = ROOT / item
        need(file.is_file() and not file.is_symlink(), "Unsafe proof file")
        size += file.stat().st_size
    need(size == 115720144 and mbytes+sbytes+pbytes <= size,
         "Source proof byte count changed")
    return {"proof_count": 52, "proof_bytes": size, "registries_valid": True}


def execute(cmd, label, env):
    run = subprocess.run(cmd, cwd=ROOT, env=env, text=True,
                         capture_output=True, timeout=1500, check=False)
    if run.returncode:
        raise RuntimeError(label + " failed (exit " + str(run.returncode)
                           + "):\n" + (run.stdout+"\n"+run.stderr)[-1400:])


def replay(case, env):
    required = set()
    if case in ("main", "subgroups", "lrat"):
        required.update(("git", "cc"))
    if case == "lrat":
        required.add("gcc")
    if case == "exact":
        required.update(("gcc", "g++"))
    for command in required:
        need(shutil.which(command) is not None, "Missing build command "+command)
    py = sys.executable
    if case in ("main", "subgroups", "lrat"):
        drat = ROOT / ".build/drat-trim/drat-trim"
        if not drat.exists():
            execute(["bash", "tools/build_drat_trim.sh"], "Pinned DRAT checker build", env)
        need(drat.is_file() and not drat.is_symlink(), "Unsafe DRAT checker")
    if case == "lrat":
        cake = ROOT / ".build/cake_lpr/cake_lpr"
        if not cake.exists():
            execute(["bash", "tools/build_cake_lpr.sh"], "Pinned CakeML checker build", env)
        need(cake.is_file() and not cake.is_symlink(), "Unsafe CakeML checker")
    steps = {
        "main": [[py, "-B", "tools/run_verification.py", "--full",
                  "--checker", ".build/drat-trim/drat-trim"]],
        "subgroups": [[py, "-B", "-m", "tools.run_subgroup_verification",
                       "--checker", ".build/drat-trim/drat-trim"]],
        "swap": [[py, "-B", "-m", "tools.run_positive_verification", "--case", "swap"]],
        "double": [[py, "-B", "-m", "tools.run_positive_verification", "--case", "double"]],
        "exact": [
            [py, "-B", "tools/verify_exact_symmetry_addendum.py"],
            *[[py, "-B", "tools/run_named_positive_audit.py", "--case", x]
              for x in ("s4", "a4", "s3", "v4i")],
            [py, "-B", "-m", "tools.verify_exact_stabilizers"],
            [py, "-B", "-m", "tools.verify_hall_actual_language_stabilizer"],
        ],
        "trust": [[py, "-B", "-m", "tools.audit_theorem_trust_boundaries"]],
        "lrat": [
            [py, "-B", "-m", "tools.verify_secondary_lrat",
             "--drat-trim", ".build/drat-trim/drat-trim",
             "--cake-lpr", ".build/cake_lpr/cake_lpr"],
            [py, "-B", "-m", "tools.verify_secondary_lrat_radius4",
             "--drat-trim", ".build/drat-trim/drat-trim",
             "--cake-lpr", ".build/cake_lpr/cake_lpr"],
            *[[py, "-B", "-m", "tools.verify_secondary_lrat_subgroups",
               "--case", group, "--drat-trim", ".build/drat-trim/drat-trim",
               "--cake-lpr", ".build/cake_lpr/cake_lpr"]
              for group in ("cycle012", "normal-v4", "intransitive-v4")],
        ],
    }
    completed = []
    for index, cmd in enumerate(steps[case], 1):
        execute(cmd, case+" step "+str(index), env)
        completed.append(case+":"+str(index))
    return completed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case", choices=(*CASES, "all"), required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    output = args.report.resolve()
    need(not output.exists() and not output.is_symlink(), "Refusing to overwrite report")
    ensure_portable_root(ROOT)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    original = verify_origins()
    cases = CASES if args.case == "all" else (args.case,)
    complete = {}
    for case in cases:
        complete[case] = replay(case, env)
        need(verify_origins() == original, "Registered proofs altered after replay")
    result = {
        "status": "PORTABLE FINITE-CERTIFICATE REPRODUCTION PASSED",
        "families_passed": list(complete),
        "steps_by_family": complete,
        "original_proofs": original,
        "source_changed": False,
        "self_contained_certificate_inputs": True,
        "human_infinite_word_proof_formalized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print("PASS: portable proof families "+", ".join(cases))
    print("All 52 registered proof objects remain unchanged during verification")
    return 0


if __name__ == "__main__":
    sys.exit(main())
