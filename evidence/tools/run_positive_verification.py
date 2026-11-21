#!/usr/bin/env python3
"""Clean-checkout complete SAT witness and all-named-factor symmetry audit.

One selectable positive radius-five subgroup case per process, with isolated
original generator / independent byte auditor / witness checker processes.
CNFs are generated in a fresh, automatically removed .build temp folder;
the historical CaDiCaL signed SAT models remain the exact Git archive bytes.
No SAT solver, network fetch, external source tree, or /tmp artifact is needed.

Does not claim that either positive witness is invariant under both
involutions simultaneously, nor that an exact larger-symmetry optimum
has been obtained.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile

from tools.verify_positive_manifest import ROOT, verify_registry

CASES = {
    "swap": "square-free-marker-q4-m3-r5-swap01.cnf",
    "double": "square-free-marker-q4-m3-r5-double01-23.cnf",
}


def invoke(case: str, stage: str, cnf: Path, report: Path | None = None) -> None:
    command = [
        sys.executable, "-B", "-m", "tools.invoke_positive_stage",
        "--case", case, "--stage", stage, "--cnf", str(cnf),
    ]
    if report is not None:
        command += ["--report", str(report)]
    print(f"\n=== {case} / {stage} ===", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, required=True)
    args = parser.parse_args()
    count, size = verify_registry()
    print(f"ORIGINAL POSITIVE WITNESSES: {count} Git blobs, {size} bytes", flush=True)
    temp_root = ROOT / ".build"
    if temp_root.is_symlink():
        raise ValueError("Unsafe build directory symlink")
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="square-free-marker-positive-", dir=temp_root) as tmp:
        cnf = Path(tmp) / CASES[args.case]
        report = Path(tmp) / "fresh-double-sat-audit.json"
        invoke(args.case, "export", cnf)
        if not cnf.is_file() or cnf.is_symlink():
            raise ValueError("Expected newly generated finite-factor CNF")
        invoke(args.case, "audit", cnf)
        invoke(args.case, "witness", cnf, report if args.case == "double" else None)
        if args.case == "double":
            original = ROOT / (
                "proofs/m3/double01-23/"
                "square-free-marker-m3-r5-double01-23-sat-audit.json"
            )
            actual = report.read_bytes()
            if actual != original.read_bytes():
                raise ValueError("Double-transposition audited SAT report differs from source")
            print("ORIGINAL REPORT REPLAYED BYTE-IDENTICALLY: "
                  + sha256(actual).hexdigest(), flush=True)
    print("FULL POSITIVE SAT WITNESS REPRODUCTION PASSED: " + args.case)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("POSITIVE SAT PROOF REPLAY FAILED:", error, file=sys.stderr)
        raise SystemExit(1)
