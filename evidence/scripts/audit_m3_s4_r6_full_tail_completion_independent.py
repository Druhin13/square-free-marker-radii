#!/usr/bin/env python3
"""Independent audit of the complete full-S4 radius-six source tails.

Does not import the source-tail certificate generator. Uses a separate
integer-based square detector, independent Hall factor construction,
and the hash-identified core proof archive to cross-check every
completed source factor and clause. This independently validates all the FINITE
hypotheses of the separately written two-sided separator-extension
lemma; no finite computation proves classical infinite Hall–Thue facts.

All three source inputs and the complete-extremity certificate are
SHA-256/length pinned. The --completion option accepts a certificate
from a separate checked-out evidence repository. Only the new --report path
is written, exclusively; no Git write or file overwrites.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / "proofs/m3/s4-r6-ten-core"
DEFAULT_COMPLETION = Path("/tmp/square-free-marker-m3-r6-s4-ten-core-full-tail-completions.json")
DEFAULT_REPORT = Path("/tmp/square-free-marker-m3-r6-s4-full-tail-independent-audit.json")

PINS = {
    "core.cnf": (195, "b80b008364dace6c4177bb5f5d71b5e0ee2b828c7ea85a15c21e75eed7c86a14"),
    "square-free-marker-m3-r6-s4-cnf-audit.json": (1598, "08dcfcc380b8e47443c2683f1c2cc175ed361e19f721851f4ae8ec0a81971c15"),
    "square-free-marker-m3-r6-s4-ten-core-biinfinite-audit.json": (14722, "aafc0b76e69e1c465b459bb610a771da292902c2fef30079b582117b2c21ffb7"),
}
COMPLETION_PIN = (11966, "46978c02d61491302a647baba418e9dad1921a069fce8ed08fce21af346d7699")

def require(value, what):
    if not value:
        raise AssertionError(what)

def signature(file):
    h = sha256()
    n = 0
    with file.open("rb") as inp:
        while True:
            block = inp.read(1 << 20)
            if not block:
                break
            n += len(block)
            h.update(block)
    return n, h.hexdigest()

def pin(file, expectation):
    require(file.is_file() and not file.is_symlink(),
            "Missing or symlinked artifact: " + str(file))
    require(signature(file) == expectation,
            "Wrong byte count or SHA256: " + str(file))

def independent_is_squarefree(s):
    # Separate implementation: integer conversion and elementwise comparison
    # at every possible square-ending index; no substring slicing equality.
    word = [ord(c) for c in s]
    for ending in range(2, len(word)+1):
        for period in range(1, ending//2+1):
            begin = ending - 2*period
            if all(word[begin+k] == word[begin+period+k]
                   for k in range(period)):
                return False
    return True

def hall_word(needed=32768):
    images = ("012", "02", "1")
    letters = [0]
    while len(letters) < needed:
        letters = [int(ch) for symbol in letters
                   for ch in images[symbol]]
    return tuple(letters[:needed])

def rename(hall, permutation):
    require(type(permutation) is str and set(permutation) == set("123")
            and len(permutation) == 3,
            "Not a Hall alphabet permutation")
    return "".join(permutation[symbol] for symbol in hall)

def assert_clauses(core):
    rows = core.read_text(encoding="ascii").splitlines()
    require(len(rows) == 11 and rows[0].startswith("p cnf 25192 10"),
            "Original ten-source CNF header wrong")
    out = []
    for line in rows[1:]:
        numbers = tuple(map(int, line.split()))
        require(numbers[-1] == 0 and 0 not in numbers[:-1],
                "Malformed original core clause")
        out.append(tuple(sorted(numbers[:-1])))
    require(len(out) == 10 and len(set(out)) == 10,
            "Nonunique original CNF source clauses")
    return set(out)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--completion", type=Path, default=DEFAULT_COMPLETION)
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    opts = p.parse_args()
    print("INDEPENDENT FULL-TAIL S4 RADIUS-SIX AUDIT",
          flush=True)

    require(ORIGINAL.is_dir() and not ORIGINAL.is_symlink(),
            "Immutable lower-bound archive missing/unsafe")
    for filename, signature_expected in PINS.items():
        pin(ORIGINAL / filename, signature_expected)
    pin(opts.completion, COMPLETION_PIN)
    require(opts.report.parent.is_dir() and not opts.report.is_symlink()
            and not opts.report.exists(),
            "Refusing missing/unsafe or pre-existing audit report output")

    core_clauses = assert_clauses(ORIGINAL / "core.cnf")
    old = json.loads(
        (ORIGINAL / "square-free-marker-m3-r6-s4-ten-core-biinfinite-audit.json").read_bytes())
    completion = json.loads(opts.completion.read_bytes())

    require(old["original_core_clause_count"] == 10
            and old["direct_truth_table_assignments_checked"] == 256
            and old["direct_truth_table_satisfying_assignments"] == 0
            and len(old["original_source_certificates"]) == 10,
            "Immutable original contradiction metadata mismatch")
    require(completion["status"] ==
            "TEN FULL-S4 RADIUS-SIX SOURCE TWO-SIDED HALL COMPLETIONS FINITELY VERIFIED"
            and completion["source_count"] == 10
            and completion["replaced_right_padding_count"] == 6
            and completion["source_audit_sha256"] == PINS[
               "square-free-marker-m3-r6-s4-ten-core-biinfinite-audit.json"][1]
            and completion["original_core_sha256"] == PINS["core.cnf"][1]
            and completion["independent_original_cnf_audit_sha256"] ==
               PINS["square-free-marker-m3-r6-s4-cnf-audit.json"][1]
            and len(completion["certificates"]) == 10,
            "Complete-extremity certificate scope/lineage mismatch")

    hall = hall_word()
    require(independent_is_squarefree(
            "".join(str(c) for c in hall[:220])),
            "Finite Hall-prefix sanity check failed")

    corrected = 0
    factors = []
    seen_sources = set()

    for index, (cert, original) in enumerate(zip(
        completion["certificates"],
        old["original_source_certificates"]), 1):

        source = cert["original_source_word"]
        witness = cert["new_full_finite_squarefree_witness"]
        original_clause = tuple(sorted(original["core_clause"]))
        cert_clause = tuple(sorted(cert["original_core_clause"]))

        require(cert["source_number"] == index
                and cert_clause == original_clause
                and cert_clause in core_clauses
                and source == original["source_word"]
                and cert["source_factor_length"] == len(source)
                and cert["original_source_orbit_lex_rank_zero_based"] ==
                   original["source_orbit_lex_rank_zero_based"],
                f"Immutable factor/core source identity mismatch #{index}")
        require(original_clause not in seen_sources,
                "Duplicate original CNF source")
        seen_sources.add(original_clause)

        left = original["left_exterior"]
        original_right = original["right_exterior"]
        new_right = cert["corrected_right_padding"]

        require(cert["original_right_padding"] == original_right
                and cert["right_padding_replaced"] ==
                   (original_right != new_right),
                f"Right padding lineage mismatch #{index}")

        if original_right != new_right:
            corrected += 1

        require(witness == left + source + new_right
                and independent_is_squarefree(source)
                and independent_is_squarefree(witness),
                f"Completed word is not the declared squarefree source extension #{index}")

        zeros = [i for i, ch in enumerate(witness) if ch == "0"]
        require(len(zeros) >= 2 and zeros[0] == len(left)
                and cert["zero_positions_in_witness"] == zeros,
                f"Separator-position mismatch #{index}")
        d = zeros[-1] - zeros[0]
        require(d == cert["separator_span_D"]
                and len(left) >= d-1 and len(new_right) >= d-1,
                f"Separator span / D-1 margins wrong #{index}")

        ltail = witness[:zeros[0]]
        rtail = witness[zeros[-1]+1:]
        require(ltail == cert["left_full_zero_free_extremity"]
                and rtail == cert["right_full_zero_free_extremity"]
                and set(ltail+rtail) <= set("123")
                and len(ltail) >= d-1 and len(rtail) >= d-1,
                f"COMPLETE zero-free extremity mismatch #{index}")

        lr = cert["left_hall_forward_factor"]
        rr = cert["right_hall_forward_factor"]
        ls = rename(hall, lr["permutation_012_to_123"])
        rs = rename(hall, rr["permutation_012_to_123"])
        li = lr["prefix_offset"]
        ri = rr["prefix_offset"]
        require(type(li) is int and type(ri) is int and li >= 0 and ri >= 0
                and ls[li:li+len(ltail)] == ltail
                and rs[ri:ri+len(rtail)] == rtail,
                f"Complete extremities not forward Hall factors #{index}")

        # Recompute the independently named long finite-extension check:
        ld = lr["deep_sanity_offset"]
        rd = rr["deep_sanity_offset"]
        require(type(ld) is int and type(rd) is int
                and ld >= 300 and rd >= 300
                and ls[ld:ld+len(ltail)] == ltail
                and rs[rd:rd+len(rtail)] == rtail,
                f"Declared far Hall occurrences invalid #{index}")
        glued = (ls[ld-300:ld] + witness +
                 rs[rd+len(rtail):rd+len(rtail)+300])
        require(len(glued) == len(witness)+600
                and independent_is_squarefree(glued)
                and cert["finite_300_each_side_extension_squarefree"] is True,
                f"300+300 extra finite squarefree sanity test failed #{index}")
        factors.append({
            "source_ordinal": index,
            "source_length": len(source),
            "separator_span": d,
            "complete_prefix_length": len(ltail),
            "complete_suffix_length": len(rtail),
            "original_right_padding_replaced": original_right != new_right,
        })
        print(f"  VERIFIED SOURCE {index}/10: "
              f"length={len(source)} D={d} "
              f"full right length={len(rtail)}", flush=True)

    require(seen_sources == core_clauses and corrected == 6,
            "Original contradiction source set/replacement count incomplete")
    for filename, expectation in PINS.items():
        pin(ORIGINAL / filename, expectation)
    pin(opts.completion, COMPLETION_PIN)

    output = {
        "status": "INDEPENDENT FULL-TAIL S4 RADIUS-SIX COMPLETION AUDIT PASSED",
        "original_cnf_core_sha256": PINS["core.cnf"][1],
        "original_source_audit_sha256": PINS[
            "square-free-marker-m3-r6-s4-ten-core-biinfinite-audit.json"][1],
        "original_cnf_source_audit_sha256": PINS[
            "square-free-marker-m3-r6-s4-cnf-audit.json"][1],
        "repaired_certificate_sha256": COMPLETION_PIN[1],
        "repaired_certificate_bytes": COMPLETION_PIN[0],
        "source_count": 10,
        "replaced_right_padding_count": corrected,
        "all_original_core_sources_preserved": True,
        "all_complete_extremities_match_forward_Hall_factors": True,
        "all_finite_repaired_witnesses_squarefree": True,
        "all_300_plus_300_extensions_squarefree": True,
        "proof_scope": "Finite certificates verified. The standalone separator lemma and classical squarefree uniformly recurrent Hall-Thue word yield bi-infinite extension.",
        "sources": factors,
    }
    raw = (json.dumps(output, indent=2, sort_keys=True)+"\n").encode("ascii")
    with opts.report.open("xb") as dest:
        dest.write(raw)
    require(signature(opts.report) == (len(raw), sha256(raw).hexdigest()),
            "Independent audit report write integrity mismatch")
    print("ALL TEN COMPLETE TWO-SIDED HALL SOURCE CERTIFICATES INDEPENDENTLY AUDITED")
    print("  Report bytes:", len(raw))
    print("  Report SHA-256:", sha256(raw).hexdigest())
    print("  Report:", opts.report)
    print("The infinite extension uses the separately proved separator lemma and classical Hall–Thue theorem.")

if __name__ == "__main__":
    main()
