#!/usr/bin/env python3
"""P1.1: second, formally verified checker on small original S4 UNSAT core.

Pinned DRAT-trim is a FORMAT CONVERTER from DRAT into LRAT; success of
this converter is not proof. Separately compiled CakeML/HOL4-backed
cake_lpr must validate the resulting LRAT against the SHA-pinned CNF.
The invalid-proof negative control must not be accepted. The program
does not claim any of the large subgroup/radius-4 proofs are checked.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
CNF = ROOT / "proofs/m3/s4-r6-ten-core/core.cnf"
DRAT = ROOT / "proofs/m3/s4-r6-ten-core/core-lemmas.drat"
PINS = {
    CNF: (195, "b80b008364dace6c4177bb5f5d71b5e0ee2b828c7ea85a15c21e75eed7c86a14"),
    DRAT: (222, "16c6f25a8d3136a0b6ed916c639c17d99080263ea40008b51666dfc62287a700"),
}
DRAT_REV = "effa1dcce85c878236f8313133dff1a2b766cd7c"
CAKE_REV = "033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def identity(path):
    require(path.is_file() and not path.is_symlink(),
            f"Unsafe/missing source: {path}")
    raw = path.read_bytes()
    return len(raw), sha256(raw).hexdigest()


def checked_call(argv, description):
    proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=120)
    print(description + ":", "exit", proc.returncode)
    print((proc.stdout + proc.stderr)[-2500:])
    require(proc.returncode == 0, description + " failed")
    return proc.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drat-trim", type=Path, required=True)
    parser.add_argument("--cake-lpr", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    converter = args.drat_trim.resolve(strict=True)
    checker = args.cake_lpr.resolve(strict=True)
    require(all(p.is_file() and not p.is_symlink() for p in (converter, checker)),
            "Missing or symlinked checker binary")
    for path, expected in PINS.items():
        require(identity(path) == expected,
                f"Original source certificate identity mismatch: {path}")

    with tempfile.TemporaryDirectory(prefix="verified-lrat-pilot-") as temp:
        path = Path(temp) / "original-ten-core.lrat"
        log = checked_call([str(converter), str(CNF), str(DRAT), "-L", str(path)],
                           "Convert original DRAT to LRAT")
        require("s VERIFIED" in log.splitlines(),
                "Converter did not report verified DRAT")
        require(path.is_file() and path.stat().st_size > 0,
                "No derived LRAT output")
        result = checked_call([str(checker), "--CML_HEAP_SIZE=256", "--CML_STACK_SIZE=256", str(CNF), str(path)],
                              "Independently validate LRAT with CakeML")
        require("s VERIFIED UNSAT" in result.splitlines(),
                "Verified proof checker did not certify UNSAT")
        invalid = Path(temp) / "empty-invalid.lrat"
        invalid.write_bytes(b"")
        bad = subprocess.run([str(checker), "--CML_HEAP_SIZE=256", "--CML_STACK_SIZE=256", str(CNF), str(invalid)],
                             cwd=ROOT, text=True, capture_output=True, timeout=120)
        require("s VERIFIED UNSAT" not in bad.stdout + bad.stderr,
                "Fail-open: checker accepted an empty proof")
        size, digest = identity(path)
        report = {
            "case": "original ten-clause radius-six full-S4 obstruction",
            "status": "CAKEML VERIFIED-LRAT PILOT PASSED",
            "cnf_sha256": PINS[CNF][1],
            "drat_sha256": PINS[DRAT][1],
            "drat_converter_revision": DRAT_REV,
            "cake_lpr_revision": CAKE_REV,
            "lrat_size_bytes": size,
            "lrat_sha256": digest,
            "independent_checker_output": "s VERIFIED UNSAT",
            "invalid_proof_rejected": True,
            "scope_limit": "Not a check of radius-4 or subgroup large UNSAT proofs",
        }
        if args.report:
            require(args.report.parent.is_dir() and
                    not args.report.exists() and not args.report.is_symlink(),
                    "Unsafe/preexisting report")
            with args.report.open("x", encoding="utf8") as f:
                json.dump(report, f, sort_keys=True, indent=2)
                f.write("\n")
        print(report["status"])


if __name__ == "__main__":
    main()
