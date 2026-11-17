#!/usr/bin/env python3
"""Reproduce the exact minimum symmetric marker radius r=5 for q=4,m=3.

The theorem concerns one shared, shift-equivariant Boolean sliding-block
rule on ALL bi-infinite square-free quaternary words with marker separation
at least 3 and domination distance at most 2.

Lower bound: archived, independently checked DRAT refutation of the
24,292-clause radius-4 core, every clause independently certified to
occur on a bi-infinite square-free word (Hall–Thue + separator lemma).

Upper bound: archived complete CaDiCaL SAT assignment on the 87,936
square-free length-11 contexts, independently checked directly against
ALL square-free length-12 (distance-one packing), length-13 (distance-two
packing), and length-15 (five-marker domination) windows. No full
143MB radius-5 DIMACS file is required to verify the upper bound.

Run after archiving the model under proofs/m3/:
    python3 -m scripts.verify_exact_radius_m3 \
        --checker /tmp/kbl-drat-trim/drat-trim

One external binary proof checker (DRAT-trim) is required for the
lower bound. The SAT upper-bound audit is pure standard-library Python.
This is not a proof of any asymptotic rate or publication novelty.
"""
import argparse
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from scripts import verify_m3_radius4_lower_bound as lower
from scripts import verify_marker_m3_r5_sat_witness as upper

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "proofs/m3"
MODEL_PATH = ARCHIVE / "kbl-q4-m3-r5-result.txt"
MODEL_SHA256 = "d5ba5df3f93f6e996ffe1164d2dcb2886e0f530638f894b45a090ea79d2eb7c7"
EXPECTED_SELECTED = 24120
EXPECTED_VARIABLES = 87936


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checker",
        type=Path,
        required=True,
        help="Path to compiled DRAT-trim checker (supports binary-proof -i)",
    )
    args = parser.parse_args()
    if not args.checker.is_file():
        parser.error(f"DRAT checker not found: {args.checker}")
    started = perf_counter()

    print("EXACT RADIUS q=4, m=3: INTEGRATED ARCHIVED VERIFIER", flush=True)
    print("PHASE 1/5: pinned radius-4 lower-bound proof files", flush=True)
    lower.verify_pins()

    print("PHASE 2/5: independent original core factor extensions", flush=True)
    lower.audit_easy()

    print("PHASE 3/5: independent additional core factor extensions", flush=True)
    lower.audit_remaining()

    print("PHASE 4/5: direct independent radius-4 UNSAT refutation", flush=True)
    lower.verify_drat(args.checker)

    print("PHASE 5/5: archived radius-5 SAT assignment and direct semantics",
          flush=True)
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Archived SAT model missing: {MODEL_PATH}. "
            "Copy independently checked /tmp/kbl-m3-r5-result.txt "
            "before invoking this verifier."
        )
    assignment, got_hash = upper.parse_complete_sat_model(MODEL_PATH)
    if got_hash != MODEL_SHA256:
        raise ValueError(
            f"Archived radius-5 SAT model SHA256 mismatch: "
            f"{got_hash} != {MODEL_SHA256}"
        )
    if len(assignment) != EXPECTED_VARIABLES + 1:
        raise ValueError("Archived model has incorrect assignment length")
    selected = sum(assignment[1:])
    if selected != EXPECTED_SELECTED:
        raise ValueError(
            f"Expected {EXPECTED_SELECTED} selected contexts, got {selected}"
        )
    counts = upper.check_squarefree_marker_semantics(assignment)
    if counts != {
        "contexts": EXPECTED_VARIABLES,
        "adjacent_windows": 230520,
        "distance_two_windows": 604608,
        "domination_windows": 4156392,
    }:
        raise ValueError(f"Unexpected semantic census: {counts}")

    print("  Model SHA256:", got_hash)
    print("  Full assigned contexts:", EXPECTED_VARIABLES)
    print("  Selected contexts:", selected)
    print()
    print("ALL FIVE PHASES PASSED")
    print("CERTIFIED EXACT THEOREM: r_min(q=4,m=3) = 5")
    print("Scope: quaternary bi-infinite square-free words, one shared")
    print("shift-equivariant Boolean symmetric-radius sliding-block rule,")
    print("marker separation >=3 and domination distance <=2")
    print("No full radius-5 CNF required to reproduce the theorem")
    print(f"Total verification time (seconds): {perf_counter()-started:.2f}")
    print("No asymptotic or publication novelty claim")


if __name__ == "__main__":
    main()
