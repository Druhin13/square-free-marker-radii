#!/usr/bin/env python3
"""Prove trivial exact stabilizer on the ACTUAL bi-infinite square-free shift.

The unrestricted q=4,m=3,r=5 Boolean SAT model is SHA-256 pinned. A
finite square-free word need not extend bi-infinitely, so detecting
symmetry violations across all 87,936 such n=11 words is INSUFFICIENT
for this particular lower-language claim.

Instead, take the length-11 factors in a finite prefix of the classical
ternary Hall--Thue fixed point (0->012, 1->02, 2->1). Every such factor
is present in a bi-infinite square-free orbit-closure point, by
classical square-freeness and uniform recurrence of this primitive
substitution. Any alphabet relabeling of the entire bi-infinite
point preserves square-freeness; hence every renamed finite factor is
also in the actual q=4 bi-infinite square-free language.

Rebuild the original named n11 model indices independently, then give
an explicit witness pair with different marker decisions for each of
the 23 nonidentity S4 relabelings. No original model or proof data is
modified. The mathematics of Hall--Thue uniform recurrence is a stated
external theorem, not inferred from the finite prefix.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

from tools.verify_positive_manifest import ROOT

MODEL = ROOT / "proofs/m3/square-free-marker-q4-m3-r5-result.txt"
MODEL_SHA256 = "d5ba5df3f93f6e996ffe1164d2dcb2886e0f530638f894b45a090ea79d2eb7c7"
MODEL_BYTES = 595752
MODEL_VARIABLES = 87936
MODEL_SELECTED = 24120
HALL_MORPHISM = {"0": "012", "1": "02", "2": "1"}
HALL_PREFIX_LENGTH = 4096
CONTEXT_LENGTH = 11
IDENTITY = "0123"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def square_at_end(word: str) -> bool:
    for half in range(1, len(word) // 2 + 1):
        if all(word[-2 * half + j] == word[-half + j]
               for j in range(half)):
            return True
    return False


def lexical_named_contexts():
    """Independent stack DFS, not imported from the original SAT exporter."""
    pending = [""]
    while pending:
        w = pending.pop()
        if len(w) == CONTEXT_LENGTH:
            yield w
        else:
            for ch in "3210":
                candidate = w + ch
                if not square_at_end(candidate):
                    pending.append(candidate)


def assignment_from_original(path: Path) -> list[bool]:
    require(path.is_file() and not path.is_symlink(),
            "Missing/symlinked original unrestricted model")
    require(path.stat().st_size == MODEL_BYTES
            and sha_file(path) == MODEL_SHA256,
            "Original unrestricted SAT model SHA-256/byte pin mismatch")
    lines = path.read_text(encoding="ascii").splitlines()
    status, signed, finished = [], [], False
    for lineno, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("c "):
            continue
        if line.startswith("s "):
            status.append(line)
            continue
        require(line.startswith("v "), f"Invalid SAT line {lineno}")
        for raw in line.split()[1:]:
            number = int(raw)
            if number == 0:
                require(not finished, "Multiple SAT assignment terminators")
                finished = True
            else:
                require(not finished, "SAT literal after final terminator")
                signed.append(number)
    require(status == ["s SATISFIABLE"]
            and finished and len(signed) == MODEL_VARIABLES,
            "Incomplete original SAT assignment")
    values = [None] * (MODEL_VARIABLES + 1)
    for literal in signed:
        index = abs(literal)
        require(1 <= index <= MODEL_VARIABLES and values[index] is None,
                "Duplicate/out-of-range original model literal")
        values[index] = literal > 0
    require(sum(v is True for v in values[1:]) == MODEL_SELECTED
            and all(v is not None for v in values[1:]),
            "Wrong unrestricted model census")
    return values


def hall_prefix(length: int = HALL_PREFIX_LENGTH) -> str:
    source = "0"
    while len(source) < length:
        source = "".join(HALL_MORPHISM[ch] for ch in source)
    return source[:length]


def source_factor_locations(source: str):
    first_offset = {}
    for start in range(len(source) - CONTEXT_LENGTH + 1):
        factor = source[start:start + CONTEXT_LENGTH]
        first_offset.setdefault(factor, start)
    require(len(first_offset) == 36,
            "Unexpected number of ternary Hall length-11 source factors")
    require(all(set(w) == set("012") and not square_at_end(w)
                for w in first_offset),
            "Hall context does not use the expected ternary alphabet")
    return first_offset


def actual_language_contexts(source_factors: dict, group: tuple):
    """Unique relabelled Hall factors, each with explicit finite provenance."""
    origins = {}
    for factor in sorted(source_factors):
        for alphabet_images in group:
            word = factor.translate(str.maketrans("0123", alphabet_images))
            if word not in origins:
                origins[word] = {
                    "hall_factor": factor,
                    "hall_prefix_offset_zero_based": source_factors[factor],
                    "hall_012_relabelled_to": alphabet_images[:3],
                }
    require(len(origins) == 432,
            "Unexpected alphabet-renamed Hall-backed source-context census")
    return origins


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path,
                        help="Create an exclusive deterministic JSON witness report")
    args = parser.parse_args()
    model = assignment_from_original(MODEL)
    words = tuple(lexical_named_contexts())
    require(len(words) == MODEL_VARIABLES
            and len(set(words)) == MODEL_VARIABLES,
            "Incorrect independent original named length-11 source census")
    variable = {word: i for i, word in enumerate(words, 1)}
    group = tuple("".join(p) for p in permutations("0123"))
    require(len(group) == 24 and len(set(group)) == 24,
            "Not all 24 alphabet permutations enumerated")
    origins = actual_language_contexts(
        source_factor_locations(hall_prefix()), group
    )
    require(all(w in variable for w in origins),
            "A Hall-backed word does not have a SAT decision")
    contexts = sorted(origins)
    witnesses = {}
    disagreements = {}
    for alphabet_images in group:
        translate = str.maketrans("0123", alphabet_images)
        conflicts = []
        for word in contexts:
            changed_word = word.translate(translate)
            original_value = model[variable[word]]
            renamed_value = model[variable[changed_word]]
            if original_value != renamed_value:
                conflicts.append((word, changed_word, original_value, renamed_value))
        disagreements[alphabet_images] = len(conflicts)
        if alphabet_images != IDENTITY:
            require(conflicts,
                    f"No actual-language counterexample for {alphabet_images}")
            word, changed, old, new = conflicts[0]
            source = origins[word]
            require(changed in origins,
                    "Relabeled counterexample not in Hall-backed source orbit")
            source_word = source["hall_factor"]
            offset = source["hall_prefix_offset_zero_based"]
            need_prefix = hall_prefix()[offset:offset + CONTEXT_LENGTH]
            require(need_prefix == source_word and word == source_word.translate(
                str.maketrans("012", source["hall_012_relabelled_to"])),
                "Original Hall-factor witness does not realize its source word")
            witnesses[alphabet_images] = {
                "context": word,
                "permuted_context": changed,
                "marker_decision": old,
                "permuted_marker_decision": new,
                **source,
            }
    require(disagreements[IDENTITY] == 0
            and len(witnesses) == 23
            and min(v for p, v in disagreements.items() if p != IDENTITY) == 48
            and disagreements["0213"] == 48,
            "Actual-language identity/strict disagreement census changed")

    report = {
        "status": "ALL 23 NONIDENTITY S4 PERMUTATIONS EXCLUDED ON ACTUAL SQUARE-FREE SHIFT",
        "original_model_sha256": MODEL_SHA256,
        "model_n11_variable_count": MODEL_VARIABLES,
        "hall_morphism": HALL_MORPHISM,
        "hall_prefix_length": HALL_PREFIX_LENGTH,
        "hall_distinct_n11_ternary_factors": 36,
        "hall_backed_distinct_named_n11_contexts": len(contexts),
        "permutations_checked": len(group),
        "strict_nonidentity_witness_count": len(witnesses),
        "actual_language_disagreement_counts": dict(sorted(disagreements.items())),
        "strict_nonidentity_witnesses": dict(sorted(witnesses.items())),
        "logical_scope": (
            "The finite Hall factors are genuine bi-infinite language factors "
            "by classical Hall--Thue uniform recurrence and square-freeness; "
            "each reported model disagreement excludes that permutation "
            "from the exact alphabet stabilizer on the actual shift."
        ),
        "not_claimed": (
            "This finite script does not prove the classical Hall--Thue theorem "
            "or independently recheck marker separation/domination."
        ),
    }
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.report is not None:
        path = args.report
        require(path.parent.is_dir() and not path.is_symlink()
                and not path.exists(),
                "Missing/unsafe output parent or preexisting audit")
        with path.open("xb") as destination:
            destination.write(raw)
        print("HALL ACTUAL-LANGUAGE REPORT SHA256:", sha256(raw).hexdigest())
    print(report["status"])
    print("Hall-derived genuinely extendible contexts:", len(contexts))
    print("Strict nonidentity S4 witnesses:", len(witnesses))


if __name__ == "__main__":
    main()
