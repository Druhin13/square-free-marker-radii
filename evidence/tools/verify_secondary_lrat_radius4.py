#!/usr/bin/env python3
"""P1.2: independently verify the exact archived unrestricted radius-four core.

The original 24,292-clause DIMACS and historical 1,450,181-byte DRAT
remain byte-identical. Source-pinned DRAT-trim only translates DRAT
to LRAT, while the separately verified CakeML cake_lpr executable
must independently accept the derived LRAT against the original CNF.

No new SAT search, new core, or source realization claim is made here.
Successful LRAT checking certifies propositional unsatisfiability;
the existing, independently checked extension/encoding arguments
remain separate mathematical obligations.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / "proofs/m3/kbl-q4-m3-r4-core.cnf"
DRAT = ROOT / "proofs/m3/kbl-q4-m3-r4-core-direct-proof.drat"
DRAT_SOURCE_REV = "effa1dcce85c878236f8313133dff1a2b766cd7c"
CAKE_SOURCE_REV = "033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2"

# Original unchanged data, independently recorded in artifacts/manifest.json.
PINS = {
    CNF: (485473, "a2f66feec531e8cd08abe79f9a619eb0177129c482577521d735b133060467f3"),
    DRAT: (1450181, "35b9366639739e68e0134b27638c1042251fd5fd32774d8d8cfa040e2d53faf7"),
}
EXPECTED_VARIABLES = 12768
EXPECTED_CLAUSES = 24292
MAX_DERIVED_LRAT_BYTES = 512 * 1024 * 1024
MAX_STAGE_SECONDS = 900


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def identity(path: Path) -> tuple[int, str]:
    require(path.is_file() and not path.is_symlink(),
            f"Original proof file missing or a symlink: {path}")
    digest = sha256()
    count = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            count += len(block)
            digest.update(block)
    return count, digest.hexdigest()


def preflight_cnf(path: Path) -> None:
    count = 0
    header = None
    with path.open("rt", encoding="ascii") as f:
        for lineno, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("c"):
                continue
            if header is None:
                header = stripped.split()
                require(header == ["p", "cnf", str(EXPECTED_VARIABLES),
                                   str(EXPECTED_CLAUSES)],
                        "Original core DIMACS header mismatch")
                continue
            row = [int(n) for n in stripped.split()]
            require(row and row[-1] == 0 and 0 not in row[:-1],
                    f"Malformed DIMACS clause at line {lineno}")
            require(all(0 < abs(x) <= EXPECTED_VARIABLES for x in row[:-1]),
                    f"Out-of-range variable at line {lineno}")
            count += 1
    require(count == EXPECTED_CLAUSES,
            f"Expected exactly {EXPECTED_CLAUSES} core clauses, saw {count}")


def audited_run(argv: list[str], label: str, scratch: Path,
                timeout: int = MAX_STAGE_SECONDS) -> dict:
    """Save complete stdout, GNU-time accounting and fail closed on errors."""
    process_log = scratch / (label + ".log")
    measurements = scratch / (label + ".time")
    cmd = ["/usr/bin/time", "-f",
           "wall_seconds=%e\nmax_rss_kib=%M\nuser_cpu_seconds=%U\nsystem_cpu_seconds=%S",
           "-o", str(measurements), *argv]
    print(f"{label}: started", flush=True)
    with process_log.open("wb") as out:
        try:
            completed = subprocess.run(cmd, stdout=out,
                                       stderr=subprocess.STDOUT,
                                       cwd=ROOT, timeout=timeout,
                                       check=False)
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{label}: exceeded {timeout} seconds") from None

    raw = process_log.read_bytes()
    log_text = raw.decode("utf-8", errors="replace")
    print(f"{label}: exit={completed.returncode}, log tail:", flush=True)
    print(log_text[-1800:], flush=True)
    require(completed.returncode == 0,
            f"{label}: subprocess failed (exit {completed.returncode})")
    measurement = {}
    for line in measurements.read_text(encoding="ascii").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            measurement[key] = float(value)
    require({"wall_seconds", "max_rss_kib", "user_cpu_seconds",
             "system_cpu_seconds"} <= measurement.keys(),
            f"{label}: missing GNU time accounting")
    print(f"{label}: {measurement}", flush=True)
    return {"stdout": log_text, "resource_usage": measurement}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drat-trim", type=Path, required=True)
    parser.add_argument("--cake-lpr", type=Path, required=True)
    parser.add_argument("--report", type=Path,
                        help="New exclusive JSON report path")
    args = parser.parse_args()

    drat_trim = args.drat_trim.resolve(strict=True)
    cake_lpr = args.cake_lpr.resolve(strict=True)
    for checker in (drat_trim, cake_lpr):
        require(checker.is_file() and not checker.is_symlink()
                and bool(checker.stat().st_mode & 0o111),
                "Proof converter/checker must be a regular executable")
    for source, expected in PINS.items():
        require(identity(source) == expected,
                f"Original source proof digest/byte count mismatch: {source}")
    preflight_cnf(CNF)

    with tempfile.TemporaryDirectory(prefix="kbl-r4-verified-lrat-") as tmp:
        scratch = Path(tmp)
        lrat = scratch / "radius4-original-converted.lrat"
        conversion = audited_run(
            [str(drat_trim), str(CNF), str(DRAT), "-L", str(lrat)],
            "drat_translation", scratch,
        )
        require("s VERIFIED" in conversion["stdout"].splitlines(),
                "DRAT converter did not report a verified proof")
        require(lrat.is_file() and not lrat.is_symlink()
                and 0 < lrat.stat().st_size <= MAX_DERIVED_LRAT_BYTES,
                "Missing, zero-length or excessively large LRAT output")
        lrat_size, lrat_digest = identity(lrat)
        print(f"Derived LRAT: {lrat_size} bytes, SHA256 {lrat_digest}",
              flush=True)

        verification = audited_run(
            [str(cake_lpr), "--CML_HEAP_SIZE=2048",
             "--CML_STACK_SIZE=512", str(CNF), str(lrat)],
            "formally_verified_check", scratch,
        )
        require("s VERIFIED UNSAT" in verification["stdout"].splitlines(),
                "Independent CakeML checker failed to certify UNSAT")

        bad_lrat = scratch / "empty-invalid.lrat"
        bad_lrat.write_bytes(b"")
        negative = subprocess.run(
            [str(cake_lpr), "--CML_HEAP_SIZE=256",
             "--CML_STACK_SIZE=256", str(CNF), str(bad_lrat)],
            cwd=ROOT, capture_output=True, text=True,
            timeout=120, check=False,
        )
        require("s VERIFIED UNSAT" not in
                (negative.stdout + negative.stderr).splitlines(),
                "FAIL OPEN: empty invalid proof was accepted")
        print("Negative control: invalid LRAT was not accepted", flush=True)

        report = {
            "status": "INDEPENDENT VERIFIED LRAT UNRESTRICTED RADIUS-FOUR CORE PASSED",
            "case": "q=4 marker separation=3, unrestricted radius four",
            "input_core_cnf_sha256": PINS[CNF][1],
            "input_core_drat_sha256": PINS[DRAT][1],
            "core_variables": EXPECTED_VARIABLES,
            "core_clauses": EXPECTED_CLAUSES,
            "drat_trim_converter_revision": DRAT_SOURCE_REV,
            "cake_lpr_verified_checker_revision": CAKE_SOURCE_REV,
            "lrat_derived_bytes": lrat_size,
            "lrat_derived_sha256": lrat_digest,
            "conversion_usage": conversion["resource_usage"],
            "verified_checking_usage": verification["resource_usage"],
            "verification_result": "s VERIFIED UNSAT",
            "negative_control_rejected": True,
            "scope_note": (
                "Only the original core's propositional UNSAT is newly "
                "checked by a second, formally verified checker. "
                "Source realizability and SAT clause derivations are "
                "separate existing proof obligations."
            ),
        }
        if args.report is not None:
            path = args.report
            require(path.parent.is_dir() and not path.exists()
                    and not path.is_symlink(),
                    "Report destination already exists or is unsafe")
            with path.open("x", encoding="utf-8") as out:
                json.dump(report, out, indent=2, sort_keys=True)
                out.write("\n")
        print(report["status"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
