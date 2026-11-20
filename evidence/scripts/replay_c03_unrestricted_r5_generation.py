#!/usr/bin/env python3
"""C03 new unrestricted-r5 SAT discovery on original, exactly reproduced CNF.

Not archival solver provenance. Generates only disposable source/model files,
checks original historic bytes are unchanged, then independently checks
the new CaDiCaL model against all 4,991,520 clauses and all named words.
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

from scripts.export_c03_unrestricted_r5_cnf import (
    generate, EXPECTED_SHA256, EXPECTED_BYTES, VARIABLES, CLAUSES,
)
from scripts.replay_c03_solver_metadata import (
    info, original_hash, time_stats, version_metadata,
)
from tools.verify_positive_manifest import ROOT, verify_registry

EXPECTED_SOLVER_BINARY_SHA256 = (
    "7b73df0a6d9cf3c751a1948300e5baff8e82c4d39bcd88f0c063b5f5cfb8b33e"
)
ARCHIVE = ROOT / "proofs/m3/kbl-q4-m3-r5-result.txt"
EXPECTED_ARCHIVE_SHA256 = (
    "d5ba5df3f93f6e996ffe1164d2dcb2886e0f530638f894b45a090ea79d2eb7c7"
)
EXPECTED_ARCHIVE_BYTES = 595752
SOLVER_TIMEOUT = 2400
CHECKER_TIMEOUT = 1800


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def check_original_archive() -> tuple[int, str, str]:
    require(ARCHIVE.is_file() and not ARCHIVE.is_symlink(),
            "Missing/unsafe original unrestricted r5 model")
    identity = original_hash(ARCHIVE)
    require(identity[0] == EXPECTED_ARCHIVE_BYTES
            and identity[1] == EXPECTED_ARCHIVE_SHA256,
            "Original unrestricted r5 SAT model byte identity mismatch")
    return identity


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report_path = args.report.resolve()
    require(report_path.parent.is_dir() and not report_path.exists()
            and not report_path.is_symlink(), "Refuse existing report")

    original = check_original_archive()
    positive_manifest = verify_registry()
    solver = args.solver.resolve()
    solver_id = version_metadata(solver)
    require(solver_id["binary_sha256"] == EXPECTED_SOLVER_BINARY_SHA256,
            "Installed solver differs from pinned C03 version")

    cpus = sorted(os.sched_getaffinity(0))
    require(cpus, "No allowed CPU affinity")
    cpu = cpus[0]
    temp_root = ROOT / ".build"
    require(not temp_root.is_symlink(), "Unsafe .build symlink")
    temp_root.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="kbl-c03-r5-unrestricted-",
                                     dir=temp_root) as tmp:
        work = Path(tmp)
        cnf = work / "exact-original-r5.cnf"
        model = work / "fresh-r5-positive-model.txt"
        timing = work / "solver.time"
        independent_report = work / "fresh-independent-model-audit.json"

        generation = generate(cnf)
        require(generation["sha256"] == EXPECTED_SHA256
                and generation["bytes"] == EXPECTED_BYTES
                and generation["variables"] == VARIABLES
                and generation["clauses"] == CLAUSES,
                "Original input exact CNF reconstruction failed")

        command = [
            "/usr/bin/time", "-v", "-o", str(timing),
            "/usr/bin/taskset", "-c", str(cpu), str(solver),
            "--seed=0", "-w", str(model), str(cnf),
        ]
        started = perf_counter()
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True,
            check=False, timeout=SOLVER_TIMEOUT,
        )
        outer_seconds = round(perf_counter() - started, 3)
        # CaDiCaL can write its status/model only to the -w output file.
        # Exit code 10 plus the independently parsed COMPLETE SAT model is
        # the meaningful success contract, not a stdout status string.
        require(result.returncode == 10,
                "Unrestricted SAT search failed / exit code "
                + str(result.returncode) + " / stderr "
                + result.stderr[-700:])
        require(timing.is_file(), "Missing GNU time output")
        resources = time_stats(timing.read_text("utf-8"))

        require(model.is_file() and not model.is_symlink()
                and model.stat().st_size > 0,
                "Fresh unrestricted SAT model absent")
        fresh_size, fresh_sha, _ = original_hash(model)
        check = [
            sys.executable, "-B", "-m",
            "scripts.verify_marker_m3_r5_sat_witness",
            "--cnf", str(cnf), "--model", str(model),
            "--report", str(independent_report),
        ]
        check_started = perf_counter()
        subprocess.run(check, cwd=ROOT, check=True, timeout=CHECKER_TIMEOUT)
        independent_seconds = round(perf_counter()-check_started, 3)

        require(independent_report.is_file()
                and not independent_report.is_symlink(),
                "Independent checker did not produce report")
        checked = json.loads(independent_report.read_text("utf-8"))
        require(checked["status"] == "INDEPENDENT SAT VERIFICATION PASSED"
                and checked["cnf_sha256"] == EXPECTED_SHA256
                and checked["sat_assignment_sha256"] == fresh_sha
                and checked["assigned_variables"] == VARIABLES
                and checked["cnf_clauses_satisfied"] == CLAUSES,
                "Independent unrestricted r5 checker report inconsistency")
        require(checked["independent_semantics"] == {
            "contexts": 87936,
            "adjacent_windows": 230520,
            "distance_two_windows": 604608,
            "domination_windows": 4156392,
        }, "Independent named-word source census mismatch")
        require(original_hash(cnf)[:2] == (EXPECTED_BYTES, EXPECTED_SHA256),
                "CNF changed during solver/checker run")
        require(original_hash(model)[:2] == (fresh_size, fresh_sha),
                "Fresh SAT model changed during checker")
        require(check_original_archive() == original
                and verify_registry() == positive_manifest,
                "One of the archived original SAT proof models was modified")
        checker_report_sha256 = sha256(independent_report.read_bytes()).hexdigest()
        selected = checked["selected_contexts"]
        # The 143MB CNF and fresh model are deleted with the temporary root.

    payload = {
        "status": "PASS: NEW UNRESTRICTED r5 SAT SEARCH + EXACT CNF AND DIRECT NAMED FACTOR CHECK",
        "scope": "controlled 2026 fresh search; not historical generator provenance",
        "started_utc": stamp,
        "fresh_solver_result": "SAT",
        "solver": solver_id,
        "solver_options": ["--seed=0", "-w <temporary-model>", "<exact-original-CNF>"],
        "cpu_affinity": "one allowed logical CPU",
        "selected_cpu": cpu,
        "environment": info(),
        "input": generation,
        "fresh_model_sha256": fresh_sha,
        "fresh_model_bytes": fresh_size,
        "selected_contexts": selected,
        "solver_usage": resources,
        "orchestrator_solver_wall_seconds": outer_seconds,
        "independent_full_named_source_check_seconds": independent_seconds,
        "independent_check_report_sha256": checker_report_sha256,
        "historic_unrestricted_model_sha256": EXPECTED_ARCHIVE_SHA256,
        "historic_unrestricted_model_unchanged": True,
        "three_archived_positive_subgroup_objects_unchanged": True,
        "fresh_model_retained": False,
        "fresh_cnf_retained": False,
        "historical_generation_timings_or_settings_recovered": False,
    }
    with report_path.open("x", encoding="utf-8") as output:
        json.dump(payload, output, sort_keys=True, indent=2)
        output.write("\n")
    print("C03 FRESH UNRESTRICTED r5 SAT SEARCH + INDEPENDENT AUDIT PASSED")
    print("Input SHA-256:", EXPECTED_SHA256)
    print("Fresh model SHA-256:", fresh_sha)
    print("Only compact JSON provenance retained; original 52 proof objects untouched")


if __name__ == "__main__":
    main()
