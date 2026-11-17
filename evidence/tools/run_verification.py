#!/usr/bin/env python3
"""Publication verification driver for the fixed q=4, marker-spacing m=3 theorem.

  python3 tools/run_verification.py --quick
  python3 tools/run_verification.py --full --checker /path/to/drat-trim

Both modes REQUIRE all 21 original proof files to pass their exact SHA-256
pins before any mathematical audit. Quick mode independently regenerates
the corrected complete Hall-tail certificate, verifies it with a SECOND
algorithm, and independently recomputes every nine-color source conflict.
Full mode additionally verifies the original radius-four/strict-radius-five
theorem and radius-six original full-CNF and reduced-core DRAT traces with
an independent external DRAT-trim checker.

Generated reports are written under a NEW auto-cleaned temporary directory.
Source proof files are never changed or regenerated. Report digest equality
is required for each deterministic certificate.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PROOFS = ROOT / "proofs/m3"
FULL_S4 = PROOFS / "s4-r6-ten-core"
CORRECTED = PROOFS / "s4-r6-full-tail-repair"
COLORING = PROOFS / "s4-L14-nine-color"

EXPECTED_REPORTS = {
    "repaired_hall": (11964, "04f08bace9f5bf2d67daa7c7e69997f2c4171db10112ea2030fef50e64ed6ade"),
    "independent_hall": (3112, "2bf307c5523870fee6f81f53d06ce1f16441d03236e98d8d02f1be37536ca57c"),
    "nine_color": (1440, "c0a0996a8c1a87db12fa42b1f188a18a85d5309cdc47c45a50d3180bb3e430de"),
    "s4_radius6": (14722, "aafc0b76e69e1c465b459bb610a771da292902c2fef30079b582117b2c21ffb7"),
}


def verify(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def signature(path: Path) -> tuple[int, str]:
    verify(path.is_file() and not path.is_symlink(),
           f"Missing/unsafe verification output: {path}")
    digest = sha256()
    size = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return size, digest.hexdigest()


def call(command: list[str], title: str) -> None:
    print(f"\n=== {title} ===", flush=True)
    print("Command:", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    verify(result.returncode == 0,
           f"{title} exited with status {result.returncode}")


def expect_report(path: Path, report: str) -> None:
    size, digest = signature(path)
    expected = EXPECTED_REPORTS[report]
    verify((size, digest) == expected,
           f"{report} report not byte-identical: actual {(size, digest)}; "
           f"expected {expected}")
    print(f"BYTE-IDENTICAL {report}: {size} bytes, SHA256 {digest}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--quick", action="store_true",
                       help="certificate SHA checks, complete Hall-tail repairs, independent nine-color graph audit")
    modes.add_argument("--full", action="store_true",
                       help="quick audits PLUS unrestricted radius4/5 and full-S4 radius6 DRAT checks")
    parser.add_argument("--checker", type=Path,
                        help="compiled, source-pinned DRAT-trim executable (required for --full)")
    options = parser.parse_args()
    verify(sys.version_info >= (3, 9), "Python 3.9+ required")
    verify(not options.full or options.checker is not None,
           "Full reproduction requires --checker /path/to/drat-trim")
    if options.checker is not None:
        checker = options.checker.expanduser().resolve(strict=True)
        verify(checker.is_file() and os.access(checker, os.X_OK),
               "DRAT checker must be an executable regular file")
    else:
        checker = None

    python = sys.executable
    print("SQUARE-FREE MARKER SYMMETRY — REPRODUCIBILITY AUDIT", flush=True)
    print("Scope: q=4, m=3, separation >=3, domination <=2", flush=True)
    print("Mode:", "FULL" if options.full else "QUICK", flush=True)

    call([python, "-B", str(ROOT / "tools/verify_manifest.py"), "--full"],
         "All 21 original proof SHA-256 pins")

    with tempfile.TemporaryDirectory(prefix="squarefree-marker-verify-") as temp:
        out = Path(temp)
        repaired = out / "repaired-complete-hall.json"
        independent = out / "independent-complete-hall.json"
        colors = out / "independent-nine-color.json"
        radius6 = out / "independent-radius-six.json"

        call([
            python, "-B", "-m",
            "scripts.verify_m3_s4_r6_full_tail_completion",
            "--report", str(repaired)
        ], "Ten repaired complete Hall-tail source certificates")
        expect_report(repaired, "repaired_hall")

        call([
            python, "-B", "-m",
            "scripts.audit_m3_s4_r6_full_tail_completion_independent",
            "--repair", str(repaired),
            "--report", str(independent)
        ], "Independently recheck ten complete Hall-tail source certificates")
        expect_report(independent, "independent_hall")

        call([
            python, "-B", "-m",
            "scripts.audit_m3_s4_L14_conflict_graph_independent",
            "--archive-dir", str(COLORING.relative_to(ROOT)),
            "--coloring-sha",
            "bd45025e9d58523711e966664f2cc922f0566546a820184e98ce48e386701525",
            "--manifest-sha",
            "cd48e13fdcc4c5cb3380eea9715142c2d10617ce56439ee92e7d71a5f084ea14",
            "--report", str(colors)
        ], "Independently recompute nine-color original factor conflicts")
        expect_report(colors, "nine_color")

        if options.full:
            assert checker is not None
            call([
                python, "-B", "-m", "scripts.verify_exact_radius_m3",
                "--checker", str(checker)
            ], "Unrestricted exact marker radius five (radius4 DRAT + radius5 SAT)")

            call([
                python, "-B", "-m",
                "scripts.verify_m3_r6_s4_ten_clause_biinfinite_obstruction",
                "--archive-dir", str(FULL_S4.relative_to(ROOT)),
                "--checker", str(checker),
                "--complete-tail-audit", str(independent),
                "--report", str(radius6)
            ], "Original full-S4 radius-six source-factor + DRAT audit")
            expect_report(radius6, "s4_radius6")

    call([python, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
         "Ordered-color marker locality and registry regression tests")
    print(
        "\nPUBLICATION REPRODUCTION PASSED — "
        + ("COMPLETE proof suite" if options.full else "quick corrected-Hall and color-graph suite"),
        flush=True,
    )
    print("Scope caveat: classical Hall–Thue infinite-word facts and the")
    print("standalone separator-extension proof are mathematical ingredients.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as error:
        print("PUBLICATION REPRODUCTION FAILED:", error, file=sys.stderr)
        raise SystemExit(1)
