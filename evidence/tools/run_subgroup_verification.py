#!/usr/bin/env python3
"""Reproduce the archived radius-five subgroup obstructions from a clean checkout.

Required: the existing source-pinned DRAT-trim checker built with
`bash tools/build_drat_trim.sh`. All reports are generated under a
fresh temporary directory and compared byte-for-byte to the immutable
published SHA-pinned audit reports. Does not alter registered certificates.

This suite proves the C3, both V4, and elementary 4-cycle *obstructions*.
It does NOT prove the two positive C2 existence claims, nor does it
mechanize the classical Hall-Thue squarefreeness/recurrence theorem or
the paper's finite-separator lemma.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile

from tools.verify_subgroup_manifest import ROOT, verify_registry

CASES = (
    (
        "cycle012",
        "scripts.verify_m3_r5_cycle012_biinfinite_obstruction",
        "kbl-m3-r5-cycle012-global-obstruction-audit.json",
    ),
    (
        "normal-v4",
        "scripts.verify_m3_r5_normal_v4_biinfinite_obstruction",
        "kbl-m3-r5-normal-v4-biinfinite-obstruction-audit.json",
    ),
    (
        "intransitive-v4",
        "scripts.verify_m3_r5_intransitive_v4_biinfinite_obstruction",
        "kbl-m3-r5-intransitive-v4-biinfinite-obstruction-audit.json",
    ),
)


def checked_call(args: list[str], name: str) -> None:
    print("\n=== " + name + " ===", flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=Path, required=True,
                        help="pinned and executable DRAT-trim binary")
    args = parser.parse_args()
    checker = args.checker.expanduser().resolve(strict=True)
    if not checker.is_file() or checker.is_symlink() or not checker.stat().st_mode & 0o111:
        raise ValueError("The independent DRAT checker must be a regular executable file")
    count, size = verify_registry()
    print(f"SUBGROUP PROOF SOURCE IDENTITY: {count} original blobs, {size} bytes",
          flush=True)
    checked_call(
        [sys.executable, "-B", "-m",
         "scripts.verify_m3_r5_s4_elementary_obstruction"],
        "Single 4-cycle hand-checkable obstruction",
    )
    with tempfile.TemporaryDirectory(prefix="kbl-subgroup-proof-") as tmp:
        for group, module, report in CASES:
            folder = ROOT / "proofs/m3" / group
            output = Path(tmp) / report
            checked_call([
                sys.executable, "-B", "-m", module,
                "--checker", str(checker),
                "--archive-dir", str(folder),
                "--report", str(output),
            ], group + " bi-infinite source-factor + DRAT proof")
            published = folder / report
            expected = published.read_bytes()
            actual = output.read_bytes()
            if actual != expected:
                raise RuntimeError("Replayed report differs from registered proof certificate: " + report)
            print(f"BYTE-IDENTICAL: {report} ({len(actual)} bytes; "
                  f"SHA256 {sha256(actual).hexdigest()})", flush=True)
    print("\nSUBGROUP OBSTRUCTION ARCHIVE REPRODUCTION PASSED", flush=True)
    print("Scope: this job covers only negative subgroup obstructions.")
    print("Positive single-involution SAT witnesses run in separate, independently checked CI jobs.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("SUBGROUP OBSTRUCTION ARCHIVE REPRODUCTION FAILED:", exc, file=sys.stderr)
        raise SystemExit(1)
