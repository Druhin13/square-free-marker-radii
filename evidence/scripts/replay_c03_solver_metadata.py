#!/usr/bin/env python3
"""C03 fresh SAT solver replay; not historical generation timing.

Runs an explicitly identified installed CaDiCaL binary on an unchanged
registered CNF, pins it to one allowed CPU, records GNU time and system
metadata, and checks its new DRAT proof using source-pinned DRAT-trim.
The fresh proof stays in a temporary directory and is NEVER committed
or uploaded. Only a small provenance JSON summary is written; original proofs remain untouched.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1, sha256
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CASES = {
    "r4": ("proofs/m3/square-free-marker-q4-m3-r4-core.cnf", 12768, 24292, "artifacts/manifest.json", "artifacts", "sha256"),
    "c3": ("proofs/m3/cycle012/square-free-marker-m3-r5-cycle012-core.cnf", 29312, 12747, "artifacts/subgroup-manifest.json", "archives", "git_blob_sha1"),
    "normal-v4": ("proofs/m3/normal-v4/square-free-marker-m3-r5-normal-v4-core.cnf", 21984, 53487, "artifacts/subgroup-manifest.json", "archives", "git_blob_sha1"),
    "intransitive-v4": ("proofs/m3/intransitive-v4/square-free-marker-m3-r5-intransitive-v4-core.cnf", 21984, 26819, "artifacts/subgroup-manifest.json", "archives", "git_blob_sha1"),
}
EXPECTED_PACKAGE = "1.7.4-1"
SOLVER_TIMEOUT = 240
CHECKER_TIMEOUT = 240


def require(ok, message):
    if not ok:
        raise ValueError(message)


def original_hash(file):
    size = file.stat().st_size
    s = sha256()
    b = sha1()
    b.update(b"blob " + str(size).encode("ascii") + b"\0")
    with file.open("rb") as handle:
        for block in iter(lambda: handle.read(1<<17), b""):
            s.update(block)
            b.update(block)
    return (size, s.hexdigest(), b.hexdigest())


def verify_original(case):
    rel, variables, clauses, filename, key, kind = CASES[case]
    source = ROOT / rel
    require(source.is_file() and not source.is_symlink(), "Missing original CNF")
    manifest = json.loads((ROOT / filename).read_text("utf-8"))
    path_key = "relative_path"
    size_key = "size_bytes"
    hits = [r for r in manifest[key] if r[path_key] == rel]
    require(len(hits) == 1, "Original CNF not uniquely registered")
    size, sha, blob = original_hash(source)
    require(hits[0][size_key] == size, "Original input CNF size mismatch")
    require(hits[0][kind] == (sha if kind == "sha256" else blob),
            "Original CNF digest pin mismatch")
    with source.open("rt", encoding="ascii") as stream:
        header = next(line.strip() for line in stream if line.strip()
                      and not line.startswith("c "))
    require(header == f"p cnf {variables} {clauses}",
            "Wrong source DIMACS variable/clause declaration")
    return source, {"variables":variables, "clauses":clauses,
                    "bytes":size, "sha256":sha, "pin_type":kind}


def safe_command(argv, timeout, cwd):
    result = subprocess.run(argv, cwd=cwd, capture_output=True,
                            text=True, check=False, timeout=timeout)
    return result


def version_metadata(solver):
    require(solver.is_file() and not solver.is_symlink()
            and os.access(solver, os.X_OK), "Missing/unsafe solver executable")
    raw = subprocess.check_output(
        ["dpkg-query", "-W", "-f=${Version}", "cadical"],
        text=True, timeout=15).strip()
    require(raw == EXPECTED_PACKAGE, "Unexpected CaDiCaL package version: "+raw)
    revision = safe_command([str(solver), "--version"], 30, ROOT)
    require(revision.returncode == 0 and revision.stdout.strip(),
            "Solver --version cannot be verified")
    build = safe_command([str(solver), "--build"], 30, ROOT)
    require(build.returncode == 0, "Solver build flag failed")
    return {"name":"CaDiCaL", "ubuntu_package_version":raw,
            "reported_version":revision.stdout.strip(),
            "binary_sha256":original_hash(solver)[1],
            "build_info":build.stdout.strip()[:5000],
            "command_flags":["single pinned CPU via taskset", "default solver options"],
            "historical_generator_identified":False}


def info():
    mem = Path("/proc/meminfo")
    cpu = Path("/proc/cpuinfo")
    max_cgroup = Path("/sys/fs/cgroup/memory.max")
    model = "unknown"
    if cpu.exists():
        for line in cpu.read_text("utf-8").splitlines():
            if line.lower().startswith("model name"):
                model = line.split(":",1)[-1].strip()
                break
    ram = "unknown"
    if mem.exists():
        for line in mem.read_text("utf-8").splitlines():
            if line.startswith("MemTotal:"):
                ram = line.split(":",1)[-1].strip()
                break
    return {
        "platform":platform.platform(),
        "kernel":platform.release(),
        "machine":platform.machine(),
        "cpu_model":model,
        "logical_cpu_count":os.cpu_count(),
        "physical_memory_reported":ram,
        "cgroup_memory_max":max_cgroup.read_text("utf-8").strip()
                             if max_cgroup.exists() else "unavailable",
        "runner_class":"GitHub Actions ubuntu-24.04",
    }


def time_stats(s):
    matches = dict(re.findall(r"^\s*([^\n:]+):\s*([^\n]*)\s*$", s, re.MULTILINE))
    for name in ("User time (seconds)","System time (seconds)",
                 "Maximum resident set size (kbytes)"):
        require(name in matches, "Missing GNU time measurement: "+name)
    # GNU time's elapsed label contains colons and varies slightly; keep
    # the raw line, rather than silently inventing a converted number.
    elapsed = next((line.split("):",1)[-1].strip()
                    for line in s.splitlines()
                    if "Elapsed (wall clock) time" in line), None)
    require(elapsed is not None, "Missing wall-clock measurement")
    return {"elapsed_hms":elapsed,
            "user_seconds":float(matches["User time (seconds)"]),
            "system_seconds":float(matches["System time (seconds)"]),
            "peak_rss_kib":int(matches["Maximum resident set size (kbytes)"])}


def run_case(case, solver, checker):
    source, core = verify_original(case)
    solver_info = version_metadata(solver)
    require(checker.is_file() and not checker.is_symlink()
            and os.access(checker, os.X_OK), "Missing/unsafe DRAT checker")
    original = original_hash(source)
    allowed = sorted(os.sched_getaffinity(0))
    require(allowed, "No legal CPU affinity available")
    cpu = allowed[0]
    started = datetime.now(timezone.utc).isoformat()
    with tempfile.TemporaryDirectory(prefix="square-free-marker-fresh-c03-unsat-") as td:
        work = Path(td)
        output = work/"fresh-UNSAT.drat"
        timing = work/"solve.time"
        argv = ["/usr/bin/time", "-v", "-o", str(timing),
                "/usr/bin/taskset", "-c", str(cpu),
                str(solver), str(source), str(output)]
        elapsed_start = perf_counter()
        answer = safe_command(argv, SOLVER_TIMEOUT, ROOT)
        elapsed_outer = perf_counter() - elapsed_start
        require(answer.returncode == 20, "Fresh solver did not exit UNSAT/20")
        require("s UNSATISFIABLE" in answer.stdout,
                "Fresh SAT solver did not report UNSAT")
        require(timing.is_file(), "Missing solver resource capture")
        measures = time_stats(timing.read_text("utf-8"))
        require(output.is_file() and output.stat().st_size > 0,
                "Missing fresh nonempty DRAT proof")
        proof_size, proof_sha, _ = original_hash(output)
        verify = safe_command([str(checker), str(source), str(output)],
                              CHECKER_TIMEOUT, ROOT)
        require(verify.returncode == 0 and
                "s VERIFIED" in (verify.stdout + "\n" + verify.stderr),
                "Fresh DRAT was not accepted by independent pinned checker")
        require(original_hash(source) == original,
                "Original source CNF changed during fresh run")
    return {
        "status":"NEW CONTROLLED SOLVER REPLAY + INDEPENDENT DRAT CHECK PASSED",
        "historical_runtime_measured":False,
        "case":case, "source_cnf":core,
        "solver":solver_info,
        "checker":{"name":"DRAT-trim","executable_sha256":original_hash(checker)[1],
                   "source_revision":"effa1dcce85c878236f8313133dff1a2b766cd7c"},
        "fresh_proof_bytes":proof_size,"fresh_proof_sha256":proof_sha,
        "solver_exit_code":answer.returncode,
        "cpu_affinity_pinned_to_one_allowed_cpu":True,
        "cpu_id_within_runner_affinity_set":cpu,
        "started_utc":started,
        "solver_usage":measures,
        "orchestrator_elapsed_seconds":round(elapsed_outer,3),
        "environment":info(),
        "original_input_unchanged":True,
        "fresh_proof_archived":False,
        "new_public_artifact":False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(CASES), required=True)
    parser.add_argument("--solver", type=Path, required=True)
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    require(shutil.which("dpkg-query") is not None
            and shutil.which("taskset") is not None
            and Path("/usr/bin/time").is_file(),
            "Missing reproducible Ubuntu benchmarking dependencies")
    output = args.report.resolve()
    require(output.parent.is_dir() and not output.exists()
            and not output.is_symlink(), "Refuse preexisting benchmark report")
    payload = run_case(args.case, args.solver.resolve(), args.checker.resolve())
    with output.open("x", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    print(payload["status"] + " case=" + args.case)
    print("No historical solver timing inferred; no fresh DRAT stored")


if __name__ == "__main__":
    main()
