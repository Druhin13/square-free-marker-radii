#!/usr/bin/env python3
"""P1.3: CakeML independent checks of original C3 and both V4 UNSAT cores.

These exact archived DRAT/CNF files are never regenerated or modified.
Source-pinned DRAT-trim converts each original proof to LRAT; the
separate, formally verified CakeML checker must certify UNSAT.
Infinite-word source realization remains the responsibility of
the original source-level proof audits and separator lemmas.
"""
from __future__ import annotations
import argparse
from hashlib import sha1
import json
from pathlib import Path
import subprocess
import tempfile

from tools.verify_secondary_lrat_radius4 import audited_run, identity, require

ROOT = Path(__file__).resolve().parent.parent
CASES = {
    "cycle012": {
        "prefix": "kbl-m3-r5-cycle012", "variables": 29312, "clauses": 12747,
        "cnf": (266512, "4c3eb47253ff81c9375a7e062ea3baa3d906cbe6d9966d80598d37f0a63a1ae6", "72e7c712879860ad7ca38805a338f56b2b15da9c"),
        "drat": (404191, "50dec59d3452e1868c6a79dd0795f1639f6e12df1934e54da3b1ef4f2754d2ad", "9d39056d3f2c0f5f1a40e1e7bedc8173e284f447"),
    },
    "normal-v4": {
        "prefix": "kbl-m3-r5-normal-v4", "variables": 21984, "clauses": 53487,
        "cnf": (1119417, "1b8e67aa86f661ac6a9d369e6298357ab0541af58287152f9a498844a678d729", "0f8a537965bbd71a6f457ba72c75c8dcceea224c"),
        "drat": (2257720, "215a9ac707124910261a23749bccfff6771edea3f0a63b9b6b6eb361919b91e3", "8714e8ce3fb5cf29c51fcf69afcaac407dc8d46e"),
    },
    "intransitive-v4": {
        "prefix": "kbl-m3-r5-intransitive-v4", "variables": 21984, "clauses": 26819,
        "cnf": (549604, "e5707d9aa7f077c05d8775552ea9566e5eaa7a4885d8b5c99f6b69e27c9d8db9", "38346b36d0c53d0c8d1e0de53af9d30e633aabe4"),
        "drat": (1063898, "6806854a58c47d7444648b1df49cbfe8b718ad9c9b7c8a5c01308a4f36231c08", "f7fe863713a4b9f8ff3a2b3478938de733b8bd35"),
    },
}
DRAT_REV = "effa1dcce85c878236f8313133dff1a2b766cd7c"
CAKE_REV = "033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2"


def checked_identity(path: Path, expected: tuple):
    size, digest = identity(path)
    require((size, digest) == expected[:2],
            f"Original archived size/SHA-256 mismatch: {path}")
    git = sha1()
    git.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as source:
        for part in iter(lambda: source.read(1 << 20), b""):
            git.update(part)
    require(git.hexdigest() == expected[2],
            f"Original Git-blob SHA-1 mismatch: {path}")
    return {"size_bytes": size, "sha256": digest,
            "original_git_blob_sha1": git.hexdigest()}


def check_cnf(path: Path, variables: int, expected_clauses: int):
    count = 0
    header = None
    with path.open("r", encoding="ascii") as source:
        for lineno, raw in enumerate(source, 1):
            row = raw.strip()
            if not row or row.startswith("c"):
                continue
            if header is None:
                header = row.split()
                require(header == ["p", "cnf", str(variables),
                                   str(expected_clauses)],
                        f"Wrong original DIMACS header: {path}")
                continue
            clause = [int(x) for x in row.split()]
            require(clause and clause[-1] == 0 and 0 not in clause[:-1],
                    f"Malformed source clause line {lineno}")
            require(all(1 <= abs(x) <= variables for x in clause[:-1]),
                    f"Out-of-range original variable at line {lineno}")
            count += 1
    require(count == expected_clauses,
            f"Wrong original clause count {count}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", choices=tuple(CASES), required=True)
    p.add_argument("--drat-trim", type=Path, required=True)
    p.add_argument("--cake-lpr", type=Path, required=True)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    spec = CASES[args.case]
    folder = ROOT / "proofs/m3" / args.case
    cnf = folder / (spec["prefix"] + "-core.cnf")
    drat = folder / (spec["prefix"] + "-core-lemmas.drat")
    original_cnf = checked_identity(cnf, spec["cnf"])
    original_drat = checked_identity(drat, spec["drat"])
    check_cnf(cnf, spec["variables"], spec["clauses"])

    converter = args.drat_trim.resolve(strict=True)
    checker = args.cake_lpr.resolve(strict=True)
    require(all(x.is_file() and not x.is_symlink()
                and (x.stat().st_mode & 0o111)
                for x in (converter, checker)), "Unsafe checker binary")

    with tempfile.TemporaryDirectory(prefix="kbl-r5-subgroup-lrat-") as tmp:
        scratch = Path(tmp)
        output = scratch / "original.lrat"
        converted = audited_run(
            [str(converter), str(cnf), str(drat), "-I",
             "-L", str(output)], "drat_to_lrat", scratch)
        require("s VERIFIED" in converted["stdout"].splitlines(),
                "DRAT converter did not report verification")
        require(output.is_file() and not output.is_symlink()
                and 0 < output.stat().st_size <= 512 * 1024 * 1024,
                "Derived LRAT missing or too large")
        lrat_bytes, lrat_sha256 = identity(output)

        verified = audited_run(
            [str(checker), "--CML_HEAP_SIZE=2048",
             "--CML_STACK_SIZE=512", str(cnf), str(output)],
            "independent_verified_check", scratch)
        require("s VERIFIED UNSAT" in verified["stdout"].splitlines(),
                "Separate CakeML checker did not certify UNSAT")

        bad = scratch / "invalid-empty.lrat"
        bad.write_bytes(b"")
        negative = subprocess.run(
            [str(checker), "--CML_HEAP_SIZE=256", "--CML_STACK_SIZE=256",
             str(cnf), str(bad)], cwd=ROOT, text=True,
            capture_output=True, timeout=120, check=False)
        require("s VERIFIED UNSAT" not in
                (negative.stdout + negative.stderr).splitlines(),
                "FAIL OPEN: empty LRAT was accepted")

        report = {
            "status": "INDEPENDENT CAKEML VERIFIED ORIGINAL SUBGROUP UNSAT",
            "case": args.case,
            "original_variables": spec["variables"],
            "original_clauses": spec["clauses"],
            "original_cnf": original_cnf,
            "original_drat": original_drat,
            "drat_to_lrat_revision": DRAT_REV,
            "cake_lpr_revision": CAKE_REV,
            "derived_lrat_size_bytes": lrat_bytes,
            "derived_lrat_sha256": lrat_sha256,
            "conversion_usage": converted["resource_usage"],
            "verified_checking_usage": verified["resource_usage"],
            "proof_check_result": "s VERIFIED UNSAT",
            "invalid_proof_rejected": True,
            "scope": (
                "Propositional unsatisfiability only. Original source "
                "extension/encoding audits remain separately necessary."
            ),
        }
        if args.report:
            out = args.report
            require(out.parent.is_dir() and not out.exists()
                    and not out.is_symlink(), "Unsafe report path")
            with out.open("x", encoding="utf8") as f:
                json.dump(report, f, sort_keys=True, indent=2)
                f.write("\n")
        print(report["status"], args.case, flush=True)


if __name__ == "__main__":
    main()
