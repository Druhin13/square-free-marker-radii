#!/usr/bin/env python3
"""Publication proof gate: repair the full-right-tail Hall–Thue witnesses.

Step353 checked only the newly added right padding. For six source
words, a nonempty squarefree suffix follows the last separator 0
INSIDE the original source word. The old checker did not require that
suffix + right padding lie on one common squarefree Hall ray.

This is a genuine proof-gap repair, not a modification of immutable
Step353/Step356 DRAT or source certificates. Independently verify new
right padding for all ten original source factors, with each COMPLETE
zero-free side of the new finite witness matching a relabeled FORWARD
factor of the classical Hall–Thue word 0->012, 1->02, 2->1.

A separate paper lemma proves that a squarefree finite witness with
two or more occurrences of a unique separator, span D, and at least
D-1 nonseparator letters on both sides extends to a bi-infinite
squarefree word whenever its two COMPLETE zero-free extremities admit
squarefree infinite ternary extensions. Hall–Thue is squarefree and
uniformly recurrent (classical; primitive substitution). This
script validates all finite assumptions but does not purport to
machine-prove the classical infinite-word theorem.

Inputs: the exact immutable nine-file full-S4 r6 proof archive.
Output: a new exclusive /tmp publication repair certificate.
Never writes to original proof artifacts, Git or other worktrees.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "proofs/m3/s4-r6-ten-core"
SOURCE_AUDIT = ARCHIVE / "kbl-m3-r6-s4-ten-core-biinfinite-audit.json"
CORE = ARCHIVE / "core.cnf"
CNF_AUDIT = ARCHIVE / "kbl-m3-r6-s4-cnf-audit.json"
OUT = Path("/tmp/kbl-m3-r6-s4-ten-core-full-tail-repair.json")
PINS = {
    SOURCE_AUDIT: (14722, "aafc0b76e69e1c465b459bb610a771da292902c2fef30079b582117b2c21ffb7"),
    CORE: (195, "b80b008364dace6c4177bb5f5d71b5e0ee2b828c7ea85a15c21e75eed7c86a14"),
    CNF_AUDIT: (1598, "08dcfcc380b8e47443c2683f1c2cc175ed361e19f721851f4ae8ec0a81971c15"),
}

# (original core clause, source factor word, original left padding,
#  replacement RIGHT padding, left Hall permutation/offset,
#  right Hall permutation/offset).
# Perm string xyz maps Hall 0->x, 1->y, 2->z.
# The right Hall factor MUST equal
#     word[after its LAST 0:] + replacement right padding,
# not just the separately chosen padding.
CASES = (
    ("-21696 -4588", "01023013210231", "121323123", "321232131", "213", 39, "123", 1),
    ("-12753 -7817", "01201302312010", "121312321323", "212312132123", "213", 5, "132", 42),
    ("-7817 -21695", "012013023120103", "121312321323", "121312321312", "213", 5, "213", 28),
    ("-12754", "012032130120321", "1213231232", "2321312313", "213", 39, "123", 4),
    ("-21697", "012310320123103", "121312321323", "121312321312", "213", 5, "213", 28),
    ("-12753 -21915", "012312013023121", "12131232", "32123121", "213", 5, "132", 8),
    ("12753 4588 12754 21697", "01023013210230131", "121312321312", "231321312321", "213", 29, "123", 10),
    ("21696 7817 12754 21697", "01201302312013021", "1213123213121", "2321312313213", "213", 29, "123", 5),
    ("21695 12753 12754 21697", "01231032012310302", "12131232131213", "12312132123132", "213", 29, "132", 42),
    ("21915 7817 21697 12754", "01231201302312013", "1213123213121", "2123213123132", "213", 29, "123", 3),
)

HALL = {"0": "012", "1": "02", "2": "1"}


def need(test, message):
    if not test:
        raise AssertionError(message)


def file_hash(path):
    h = sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pin_inputs():
    need(ARCHIVE.is_dir() and not ARCHIVE.is_symlink(),
         "Immutable r6 source proof archive unavailable/unsafe")
    for path, (size, digest) in PINS.items():
        need(path.is_file() and not path.is_symlink()
             and path.stat().st_size == size and file_hash(path) == digest,
             f"Original immutable source proof pin mismatch: {path.name}")
    need(not OUT.exists() and not OUT.is_symlink(),
         "Refusing to overwrite or follow publication repair report")
    need(OUT.parent.is_dir(), "Missing output parent")


def hall_prefix(length=32768):
    word = "0"
    while len(word) < length:
        word = "".join(HALL[x] for x in word)
    return word[:length]


def permuted(word, mapping):
    need(len(mapping) == 3 and set(mapping) == set("123"),
         "Invalid Hall alphabet bijection")
    return word.translate(str.maketrans(dict(zip("012", mapping))))


def squarefree(word):
    for end in range(2, len(word) + 1):
        for p in range(1, end // 2 + 1):
            if word[end-2*p:end-p] == word[end-p:end]:
                return False
    return True


def occurrence_deep(hall, target, at_least=350):
    # Recurrent classical fixed-point factors occur arbitrarily far.
    # A finite far occurrence here is only a sanity check.
    index = hall.find(target, at_least)
    need(index >= at_least, f"No Hall factor occurrence after {at_least}")
    return index


def export_exclusive(document):
    raw = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(
        prefix=".kbl-s4-r6-full-tail-", suffix=".tmp",
        dir=OUT.parent,
    )
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(raw)
        need(Path(temporary).stat().st_size == len(raw)
             and file_hash(Path(temporary)) == sha256(raw).hexdigest(),
             "Temporary repaired certificate write mismatch")
        os.link(temporary, OUT)  # Exclusive; NEVER replace an existing file.
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    need(OUT.stat().st_size == len(raw)
         and file_hash(OUT) == sha256(raw).hexdigest(),
         "New report SHA/size integrity mismatch")
    return len(raw), sha256(raw).hexdigest()


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=OUT,
                        help="new exclusive output certificate path; original immutable inputs unchanged")
    options = parser.parse_args()
    OUT = options.report
    began = perf_counter()
    print("STEP362 — REPAIR AND AUDIT TEN COMPLETE TWO-SIDED HALL TAILS",
          flush=True)
    pin_inputs()
    original = json.loads(SOURCE_AUDIT.read_text())
    need(original["original_core_clause_count"] == 10
         and original["direct_truth_table_assignments_checked"] == 256
         and original["direct_truth_table_satisfying_assignments"] == 0,
         "Original immutable propositional proof report mismatch")
    source_certificates = original["original_source_certificates"]
    need(len(source_certificates) == 10 and len(CASES) == 10,
         "Expected exactly ten previously audited original core sources")

    clauses = [
        tuple(sorted(map(int, line.split()[:-1])))
        for line in CORE.read_text().splitlines()[1:]
    ]
    need(len(clauses) == 10, "Original ten-clause core file changed")
    need(set(clauses) == {
        tuple(sorted(map(int, row[0].split()))) for row in CASES
    }, "Repaired sources do not match immutable core clause set")

    h = hall_prefix()
    need(squarefree(h[:220]),
         "Finite Hall prefix sanity check failed")
    certified = []
    repaired = 0
    for ordinal, (case, original_cert) in enumerate(
        zip(CASES, source_certificates), 1
    ):
        clause, word, left, right, lm, li, rm, ri = case
        expected_clause = sorted(map(int, clause.split()))
        need(original_cert["source_word"] == word
             and sorted(original_cert["core_clause"]) == expected_clause
             and original_cert["left_exterior"] == left,
             f"Original source/left padding identity changed: {ordinal}")

        previous_right = original_cert["right_exterior"]
        if previous_right != right:
            repaired += 1
        need(word[0] == "0" and len(word) in (14, 15, 17)
             and squarefree(word), f"Original source invalid: {ordinal}")
        first, last = word.find("0"), word.rfind("0")
        span = last - first
        need(span >= 1 and len(left) == len(right) == span-1,
             f"D−1 padding inequality invalid: {ordinal}")
        need(set(left + right) <= set("123"),
             f"Distinguished 0 leaked into tails: {ordinal}")

        witness = left + word + right
        zero_positions = [i for i,ch in enumerate(witness) if ch == "0"]
        need(zero_positions[-1] - zero_positions[0] == span
             and len(zero_positions) >= 2 and squarefree(witness),
             f"Repaired finite squarefree witness failed: {ordinal}")

        # IMPORTANT publication repair: complete zero-free prefix/suffix,
        # including any nonzero symbols within the source word.
        prefix = witness[:zero_positions[0]]
        suffix = witness[zero_positions[-1] + 1:]
        need(len(prefix) >= span - 1
             and len(suffix) >= span - 1
             and set(prefix + suffix) <= set("123"),
             f"Full extremity lengths/letters invalid: {ordinal}")

        left_hall = permuted(h, lm)
        right_hall = permuted(h, rm)
        need(left_hall[li:li+len(prefix)] == prefix,
             f"COMPLETE left extremity is not stated Hall factor: {ordinal}")
        need(right_hall[ri:ri+len(suffix)] == suffix,
             f"COMPLETE right extremity is not stated Hall factor: {ordinal}")

        left_deep = occurrence_deep(left_hall, prefix)
        right_deep = occurrence_deep(right_hall, suffix)
        extension = 300
        expanded = (
            left_hall[left_deep-extension:left_deep]
            + witness
            + right_hall[right_deep+len(suffix):
                         right_deep+len(suffix)+extension]
        )
        need(len(expanded) == len(witness) + 2*extension
             and squarefree(expanded),
             f"Additional 300/300 finite extension sanity test failed: {ordinal}")

        record = {
            "source_number": ordinal,
            "source_factor_length": len(word),
            "original_source_word": word,
            "original_core_clause": expected_clause,
            "original_source_orbit_lex_rank_zero_based":
                original_cert["source_orbit_lex_rank_zero_based"],
            "separator": "0",
            "separator_span_D": span,
            "zero_positions_in_witness": zero_positions,
            "new_full_finite_squarefree_witness": witness,
            "original_right_padding": previous_right,
            "corrected_right_padding": right,
            "right_padding_replaced": previous_right != right,
            "left_full_zero_free_extremity": prefix,
            "right_full_zero_free_extremity": suffix,
            "left_hall_forward_factor": {
                "permutation_012_to_123": lm, "prefix_offset": li,
                "deep_sanity_offset": left_deep,
            },
            "right_hall_forward_factor": {
                "permutation_012_to_123": rm, "prefix_offset": ri,
                "deep_sanity_offset": right_deep,
            },
            "finite_300_each_side_extension_squarefree": True,
        }
        certified.append(record)
        print(
            f"  REPAIRED SOURCE {ordinal}/10: n={len(word)} D={span} "
            f"right_changed={previous_right != right} "
            f"complete_right_len={len(suffix)} "
            f"left/right Hall factors verified",
            flush=True,
        )
    need(repaired == 6,
         f"Expected six necessary corrected original right paddings; got {repaired}")
    print("ALL TEN COMPLETE LEFT/RIGHT TERNARY HALL FACTORS VERIFIED")
    print("EXACTLY SIX ORIGINAL RIGHT PADDINGS REPLACED")
    print("ORIGINAL TEN-CLAUSE SOURCE IDENTITIES AND DRAT ARCHIVE UNCHANGED")

    document = {
        "status": "TEN FULL-S4 RADIUS-SIX SOURCE TWO-SIDED HALL COMPLETIONS FINITELY VERIFIED",
        "nature": (
            "New publication repair certificate; original SHA-pinned "
            "immutable Step353/Step356 archive not rewritten."
        ),
        "source_audit_sha256": PINS[SOURCE_AUDIT][1],
        "original_core_sha256": PINS[CORE][1],
        "independent_original_cnf_audit_sha256": PINS[CNF_AUDIT][1],
        "source_count": 10,
        "replaced_right_padding_count": repaired,
        "all_complete_left_and_right_extremities_are_forward_Hall_factors": True,
        "full_finite_witnesses_squarefree": True,
        "all_extended_300_300_finite_sanity_checks_passed": True,
        "mathematical_dependencies_not_machine_proved": [
            "Classical Hall-Thue squarefreeness and uniform recurrence",
            "Separate rigorous finite-separator extension lemma in docs/theory",
        ],
        "certificates": certified,
    }
    size, digest = export_exclusive(document)
    print("STEP362 FINITE TWO-SIDED HALL COMPLETION CERTIFICATE PASSED")
    print("  New exclusive report:", OUT)
    print("  Report bytes:", size)
    print("  Report SHA256:", digest)
    print(f"  Elapsed seconds: {perf_counter()-began:.2f}")
    print(
        "The finite cert is NOT an alternative to the standalone infinite "
        "separator lemma and classical Hall-Thue theorems."
    )


if __name__ == "__main__":
    main()
