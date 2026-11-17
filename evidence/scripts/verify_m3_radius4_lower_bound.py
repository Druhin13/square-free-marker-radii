#!/usr/bin/env python3
"""Verify the archived q=4,m=3 radius-4 lower-bound certificate.

The verified proof establishes that no shift-equivariant Boolean marker
rule with symmetric radius <=4 can give both marker separation >=3 and
domination distance <=2 on every bi-infinite square-free quaternary word.

Requires:
  Python 3 standard library
  The five files in proofs/m3/ documented in
  docs/theory/quaternary-m3-radius4-certified-lower-bound.md
  A compiled DRAT-trim binary supporting binary-proof flag -i

From repository root, after archiving proof artifacts:
  python3 -m scripts.verify_m3_radius4_lower_bound \
    --checker /tmp/kbl-drat-trim/drat-trim

This invokes TWO independently implemented factor/certificate auditors,
directly checks all five archived file hashes, and verifies a DRAT trace
against the EXACT archived core CNF. The Hall-Thue infinite-extension
theorem and the generalized finite-separator lemma are mathematical
assumptions/proofs rather than solver computations.
"""
import argparse
from hashlib import sha256
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "proofs/m3"

REQUIRED = {
    "kbl-q4-m3-r4-core.cnf":
        "a2f66feec531e8cd08abe79f9a619eb0177129c482577521d735b133060467f3",
    "kbl-q4-m3-r4-core-direct-proof.drat":
        "35b9366639739e68e0134b27638c1042251fd5fd32774d8d8cfa040e2d53faf7",
    "kbl-q4-m3-r4-easy-core.cnf":
        "925d9b7e28384bca92f29818b97a24d37b8aabe19b39d65041c4b7ca7ca5a833",
    "kbl-q4-m3-r4-easy-core-witnesses.json":
        "e07105792b091aaad3080b58a9fc016febd3786d7f620c3b961884c8ed4cc277",
    "kbl-q4-m3-r4-remaining-core-extensions.json":
        "870e27d7af896aa12d2ad075a9a06007bfbf310f4a0090bb0a6d30085e9123e3",
}


def verify_pins():
    print("PHASE 1/4: SHA-256 archive integrity")
    for name, expected in REQUIRED.items():
        path = ARCHIVE / name
        if not path.is_file():
            raise FileNotFoundError(f"Required proof artifact absent: {path}")
        got = sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise ValueError(f"Hash mismatch for {name}: {got}; expected {expected}")
        print(f"  VERIFIED {name}: {got}")


def audit_easy():
    print("PHASE 2/4: independent audit of original easy-factor extensions")
    import scripts.audit_m3_r4_easy_core_independent as auditor
    # Reconfigure input paths, not methods or expected digests. The
    # independent auditor retains its complete separate enumeration.
    auditor.SOURCE_CORE = ARCHIVE / "kbl-q4-m3-r4-core.cnf"
    auditor.SUB_CNF = ARCHIVE / "kbl-q4-m3-r4-easy-core.cnf"
    auditor.WITNESSES = ARCHIVE / "kbl-q4-m3-r4-easy-core-witnesses.json"
    auditor.main()


def audit_remaining():
    print("PHASE 3/4: independent audit of remaining 12,311 extensions")
    import scripts.audit_m3_r4_remaining_core_independent as auditor
    auditor.CORE = ARCHIVE / "kbl-q4-m3-r4-core.cnf"
    auditor.EASY = ARCHIVE / "kbl-q4-m3-r4-easy-core.cnf"
    auditor.MANIFEST = ARCHIVE / "kbl-q4-m3-r4-remaining-core-extensions.json"
    auditor.main()


def verify_drat(checker):
    print("PHASE 4/4: direct DRAT verification of archived UNSAT core")
    cmd = [
        str(checker),
        str(ARCHIVE / "kbl-q4-m3-r4-core.cnf"),
        str(ARCHIVE / "kbl-q4-m3-r4-core-direct-proof.drat"),
        "-i",
    ]
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, check=False)
    print(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"DRAT-trim failed with exit code {result.returncode}")
    if not any(line.strip() == "s VERIFIED"
               for line in result.stdout.splitlines()):
        raise RuntimeError("DRAT-trim did not report exact 's VERIFIED'")
    print("VERIFIED: exact 24,292-clause core refutation")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=Path, required=True,
                        help="Path to a compiled DRAT-trim binary")
    args = parser.parse_args()

    if not args.checker.is_file():
        parser.error(f"DRAT checker not found: {args.checker}")

    verify_pins()
    audit_easy()
    audit_remaining()
    verify_drat(args.checker)
    print()
    print("ALL FOUR PHASES PASSED")
    print("COMPUTER-ASSISTED THEOREM: r_min(q=4,m=3) >= 5")
    print("SCOPE: bi-infinite square-free quaternary inputs, shift-equivariant")
    print("Boolean symmetric-radius marker rules; separation>=3, domination<=2")
    print("NOT established: matching radius-5 upper bound or novelty")


if __name__ == "__main__":
    main()
