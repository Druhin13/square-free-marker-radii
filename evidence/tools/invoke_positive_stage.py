#!/usr/bin/env python3
"""Isolated CLI adaptor for the original, unchanged subgroup SAT verifier scripts.

Runs precisely one original generator, independent auditor, or original-model
semantics verifier in a fresh Python process. Only the *path variables* are
rebound; the original finite-certificate verification algorithms are unchanged.
"""
from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path

from tools.verify_positive_manifest import ROOT

MODULES = {
    "swap": {
        "export": "scripts.export_m3_r5_swap01_cnf",
        "audit": "scripts.audit_m3_r5_swap01_cnf_independent",
        "witness": "scripts.verify_m3_r5_swap01_sat_witness",
    },
    "double": {
        "export": "scripts.export_m3_r5_double01_23_cnf",
        "audit": "scripts.audit_m3_r5_double01_23_cnf_independent",
        "witness": "scripts.verify_m3_r5_double01_23_sat_witness",
    },
}
MODELS = {
    "swap": ROOT / "proofs/m3/square-free-marker-q4-m3-r5-swap01-result.txt",
    "double": ROOT / "proofs/m3/double01-23/square-free-marker-m3-r5-double01-23-result.txt",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=MODULES, required=True)
    parser.add_argument("--stage", choices=("export", "audit", "witness"), required=True)
    parser.add_argument("--cnf", type=Path, required=True)
    parser.add_argument("--report", type=Path,
                        help="Required only for double-transposition witness")
    args = parser.parse_args()
    module = import_module(MODULES[args.case][args.stage])
    if args.stage == "export":
        setattr(module, "OUT" if args.case == "swap" else "OUTPUT", args.cnf)
    else:
        setattr(module, "CNF", args.cnf)
    if args.stage == "witness":
        setattr(module, "MODEL", MODELS[args.case])
        if args.case == "double":
            if args.report is None:
                parser.error("double witness requires --report")
            setattr(module, "REPORT", args.report)
    module.main()


if __name__ == "__main__":
    main()
