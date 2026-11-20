#!/usr/bin/env python3
"""C03: fresh controlled positive SAT search, not original solver provenance.

Regenerates one invariant finite-word CNF, audits its exact bytes using the
pre-existing independent generator audit, solves afresh with a pinned CaDiCaL,
and runs an existing, independently written named-factor witness checker on
the NEW signed SAT model. All large data and new models are temporary.
Only a compact success report is generated.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter

from scripts.replay_c03_solver_metadata import (
    info, original_hash, time_stats, version_metadata,
)
from tools.verify_positive_manifest import ROOT, verify_registry

CASES = {
    "swap": {
        "cnf_sha256": "6b5ace8de69b932d0e346a540edd96168d3fd6f806588cbff56d26faa66d0a15",
        "variables": 43968,
        "clauses": 2495760,
        "symmetry": "(0 1)",
    },
    "double": {
        "cnf_sha256": "f44a5b98e0b47bac8d7ae988ddcd96dc5f8ed66500cad29ae0613a8a670889ff",
        "variables": 43968,
        "clauses": 2495760,
        "symmetry": "(0 1)(2 3)",
    },
}
PINNED_CADICAL_SHA256 = "7b73df0a6d9cf3c751a1948300e5baff8e82c4d39bcd88f0c063b5f5cfb8b33e"
STAGE_TIMEOUT = 1800
SOLVER_TIMEOUT = 2700
WITNESS_TIMEOUT = 2100


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def checked(argv: list[str], timeout: int, *, capture: bool = False):
    return subprocess.run(argv, cwd=ROOT, check=True, timeout=timeout,
                          text=True, capture_output=capture)


def check_cnf(path: Path, case: str) -> dict:
    spec = CASES[case]
    require(path.is_file() and not path.is_symlink(),
            "Fresh generated CNF missing or symlinked")
    size, digest, _ = original_hash(path)
    require(digest == spec["cnf_sha256"],
            "Fresh generated CNF differs from original independently audited encoding")
    with path.open("rt", encoding="ascii") as src:
        header = next((line.strip() for line in src
                       if line.strip() and not line.startswith("c ")), "")
    require(header == "p cnf {} {}".format(spec["variables"], spec["clauses"]),
            "Wrong finite-word CNF variables/clauses")
    return {"sha256": digest, "bytes": size,
            "variables": spec["variables"], "clauses": spec["clauses"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output_report = args.report.resolve()
    require(output_report.parent.is_dir()
            and not output_report.exists() and not output_report.is_symlink(),
            "Refuse preexisting or unsafe benchmark output")

    count, archive_bytes = verify_registry()
    require(count == 3, "Original signed SAT-model archive registry changed")
    solver = args.solver.resolve()
    solver_data = version_metadata(solver)
    require(solver_data["binary_sha256"] == PINNED_CADICAL_SHA256,
            "Solver executable differs from separately recorded C03 negative replay")
    allowed = sorted(os.sched_getaffinity(0))
    require(allowed, "No allowed CPU affinity")
    cpu = allowed[0]
    now = datetime.now(timezone.utc).isoformat()
    spec = CASES[args.case]
    timings = {}
    fresh_audit_sha256 = None

    # Original frozen generators print OUT.relative_to(ROOT); use an untracked,
    # automatically deleted directory *under* the repo, not /tmp.
    temp_root = ROOT / ".build"
    require(not temp_root.is_symlink(), "Unsafe .build temp root symlink")
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kbl-c03-fresh-positive-",
                                     dir=temp_root) as temp:
        work = Path(temp)
        cnf = work / ("finite-" + args.case + ".cnf")
        model = work / ("fresh-" + args.case + ".model")
        timing_file = work / "solver.time"
        independent_audit = work / "fresh-model-audit.json"

        stage = [sys.executable, "-B", "-m", "tools.invoke_positive_stage",
                 "--case", args.case, "--cnf", str(cnf)]
        start = perf_counter()
        checked(stage + ["--stage", "export"], STAGE_TIMEOUT)
        timings["cnf_export_wall_seconds"] = round(perf_counter()-start, 3)
        cnf_identity = check_cnf(cnf, args.case)

        start = perf_counter()
        checked(stage + ["--stage", "audit"], STAGE_TIMEOUT)
        timings["independent_cnf_audit_wall_seconds"] = round(perf_counter()-start, 3)
        require(check_cnf(cnf, args.case) == cnf_identity,
                "Independent auditor changed finite CNF")

        solve_cmd = ["/usr/bin/time", "-v", "-o", str(timing_file),
                     "/usr/bin/taskset", "-c", str(cpu), str(solver),
                     "--seed=0", "-w", str(model), str(cnf)]
        start = perf_counter()
        solver_result = subprocess.run(
            solve_cmd, cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=SOLVER_TIMEOUT,
        )
        timings["solver_orchestrator_wall_seconds"] = round(
            perf_counter()-start, 3)
        require(solver_result.returncode == 10,
                "Fresh solver failed to report SAT/exit 10; return code="
                + str(solver_result.returncode)
                + "; stderr tail=" + solver_result.stderr[-500:])
        require(timing_file.is_file(), "Missing independent GNU time report")
        timings["solver_gnu_time"] = time_stats(
            timing_file.read_text(encoding="utf-8"))
        require(model.is_file() and not model.is_symlink()
                and model.stat().st_size > 0,
                "Fresh solver did not write a nonempty signed model")
        model_size, model_sha, _ = original_hash(model)

        witness_cmd = [
            sys.executable, "-B", "-m",
            "scripts.verify_c03_fresh_positive_model",
            "--case", args.case, "--cnf", str(cnf),
            "--model", str(model),
        ]
        if args.case == "double":
            witness_cmd += ["--audit-report", str(independent_audit)]
        start = perf_counter()
        checked(witness_cmd, WITNESS_TIMEOUT)
        timings["independent_model_audit_wall_seconds"] = round(
            perf_counter()-start, 3)
        if args.case == "double":
            require(independent_audit.is_file()
                    and not independent_audit.is_symlink(),
                    "Fresh double-transposition audit report missing")
            fresh_audit_sha256 = original_hash(independent_audit)[1]

        require(check_cnf(cnf, args.case) == cnf_identity,
                "Finite CNF changed after solver/checker")
        require(original_hash(model)[:2] == (model_size, model_sha),
                "New SAT model changed after independent audit")
        require(verify_registry() == (count, archive_bytes),
                "Original signed SAT archive was modified during fresh search")
        # The model, CNF, detailed audit and time raw output are deleted here.

    report = {
        "status": "PASS: FRESH SAT SEARCH AND INDEPENDENT FULL NAMED-FACTOR AUDIT",
        "scope": "controlled positive-model generation replay; not historical generation",
        "case": args.case, "symmetry": spec["symmetry"],
        "fresh_sat_model_sha256": model_sha,
        "fresh_sat_model_bytes": model_size,
        "fresh_independent_double_audit_sha256": fresh_audit_sha256,
        "finite_cnf": cnf_identity,
        "solver": solver_data,
        "solver_options": ["--seed=0", "-w <temporary-model>", "<generated-pinned-CNF>"],
        "runner_cpu_affinity": "one allowed logical CPU",
        "runner_cpu_id": cpu,
        "started_utc": now,
        "environment": info(),
        "measurement": timings,
        "original_archive_three_files_unchanged": True,
        "fresh_model_archived": False,
        "historical_generation_metadata_recovered": False,
        "claims_all_positive_rule_searches_reproduced": False,
    }
    with output_report.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print("C03 FRESH POSITIVE GENERATION REPLAY PASSED:", args.case)
    print("Fresh SAT model SHA-256:", model_sha)
    print("Original source archived files untouched; large temporary data removed")
    print("This is a 2026 fresh solver experiment, NOT historical runtime evidence")


if __name__ == "__main__":
    main()
