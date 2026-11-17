#!/usr/bin/env python3
"""C03: apply an unchanged independent positive verifier to a NEW SAT model.

This adapter only redirects file paths to a disposable controlled replay.
It does not change a historical verifier, alter the original pinned SAT model,
or equate fresh search with the historical model-generation experiment.
"""
from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

MODULES = {
    "swap": "scripts.verify_m3_r5_swap01_sat_witness",
    "double": "scripts.verify_m3_r5_double01_23_sat_witness",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=tuple(MODULES), required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--audit-report", type=Path)
    args = parser.parse_args()

    for name, file in (("CNF", args.cnf), ("model", args.model)):
        if not file.is_file() or file.is_symlink():
            parser.error("Missing or symlinked fresh " + name + " input")
    if args.case == "double":
        if args.audit_report is None:
            parser.error("Double-transposition witness requires --audit-report")
        if args.audit_report.exists() or args.audit_report.is_symlink():
            parser.error("Refusing preexisting fresh audit report")
    elif args.audit_report is not None:
        parser.error("Single-transposition witness does not take an audit report")

    verifier = import_module(MODULES[args.case])
    verifier.CNF = args.cnf.resolve()
    verifier.MODEL = args.model.resolve()
    if args.case == "double":
        verifier.REPORT = args.audit_report.resolve()
    # This verifies every CNF clause and every named original finite factor;
    # it does not rely on identity of this new model with the historical one.
    verifier.main()
    print("C03 NEW POSITIVE MODEL INDEPENDENT SEMANTIC AUDIT PASSED:", args.case)


if __name__ == "__main__":
    main()
