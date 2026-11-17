#!/usr/bin/env python3
"""Independent INTEGRATED verification of the C3 radius-five obstruction.

This does not import ANY certificate constructor, earlier factor auditor,
SAT model checker or finite-extension verifier.

The requested theorem concerns ONE shared shift-equivariant Boolean local
marker rule of symmetric radius r=5 for EVERY bi-infinite quaternary
square-free word, with separation >=3 and domination radius <=2, and
invariant under the alphabet 3-cycle (0 1 2) fixing 3.

For each one of the exactly 12,747 original-core clauses, independently:
  1. reconstruct the named square-free factor and cyclic orbit-variable
     marker clause (the core formula itself is SHA-256 pinned);
  2. audit a CONCRETE finite square-free extension witness, either from
     the previously certified 12,720 candidates or the newly discovered
     27, with explicit Hall-Thue ternary exterior tails, verified
     normalized alphabet mapping, safe separator margins and embedding;
  3. verify the original standalone DRAT-trim UNSAT refutation directly
     against the 12,747-clause, 29,312-variable core (ASCII proof -I).

Why this is a theorem conditional on classical math:
  Hall-Thue's ternary square-free morphic word is uniformly recurrent,
  and its factors have compatible one-sided infinite square-free tails.
  The FINITE SEPARATOR LEMMA: if a finite square-free word has a
  distinguished symbol 3 with first/last occurrences distance D and
  >=D-1 three-free positions on each side, and both exterior ternary
  blocks are Hall-Thue-extendible, then it admits a bi-infinite square-
  free extension by attaching separate ternary Hall-Thue tails.
  For one occurrence of 3 no safety margin is needed. An external-
  double-separator witness uses a fourth letter absent in the target,
  and satisfies the same lemma with D=n+1.
  Thus EVERY refuted original core clause is required on the actual
  bi-infinite square-free subshift, not just all finite squarefree words.

The computer checks the finite premises and propositional proof; it
does NOT mechanically reprove Hall-Thue's classical theorem. This
establishes only the fixed q=4,m=3,r=5 and C3-invariance impossibility
statement, NOT arbitrary radii, asymptotic m bounds, CDC streaming
locality, or publication novelty.

Input source artifacts stay unchanged and SHA-pinned. A new small
local JSON report is written once with exclusive create, after ALL
phases succeed. For clean-checkout reproduction, add the six source
artifacts to proofs/m3/cycle012/ via the separately verified archiver,
then run with `--archive-dir proofs/m3/cycle012` and a NEW `--report`
path to read the unchanged five original SHA-pinned inputs from Git.

Run:
    python3 -B -m scripts.verify_m3_r5_cycle012_biinfinite_obstruction \
        --checker /tmp/kbl-drat-trim/drat-trim
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import subprocess
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
CORE = Path("/tmp/kbl-m3-r5-cycle012-core.cnf")
PROOF = Path("/tmp/kbl-m3-r5-cycle012-core-lemmas.drat")
SOURCES = Path("/tmp/kbl-m3-r5-cycle012-core-factor-map.json")
FIRST = Path("/tmp/kbl-m3-r5-cycle012-core-extension-triage.json")
SECOND = Path("/tmp/kbl-m3-r5-cycle012-extra-extensions.json")
OUTPUT = Path("/tmp/kbl-m3-r5-cycle012-global-obstruction-audit.json")
SHA_PINS = {
    CORE: "4c3eb47253ff81c9375a7e062ea3baa3d906cbe6d9966d80598d37f0a63a1ae6",
    PROOF: "50dec59d3452e1868c6a79dd0795f1639f6e12df1934e54da3b1ef4f2754d2ad",
    SOURCES: "a94ac1bab1e4458148a50c406ba2fbc639e4077b545af523f1383f8eb3d59381",
    FIRST: "ea09a3a96b6a967935939a248b49cf81c188b16c1c23e77598e57197aacefe55",
    SECOND: "47a9e079f2e0ff2c5ea8f32999d5cd5bcebab09b01086c49131b266dda3a6b1a",
}
Q = 4
CONTEXT_LENGTH = 11
VARS = 29312
CLAUSES = 12747
OLD = 12720
NEW = 27
MORPHISM = {"0": "012", "1": "02", "2": "1"}
CYCLE = str.maketrans("0123", "1203")
CYCLE2 = str.maketrans("0123", "2013")
SOURCE_CLASSES = {12: 2920, 13: 5464, 15: 4363}
CONSTRUCTION_CLASSES = {
    "hall": 13,
    "single-separator": 25,
    "multi-separator": 6,
    "padded-multi-separator": 12676,
    "external-double-separator": 22,
    "expanded-multi-separator": 5,
}


def check(test, message):
    if not test:
        raise AssertionError(message)


def sha_file(path):
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def squarefree(word):
    """Full independent square-substring check, not just suffixes."""
    for i in range(len(word)):
        for d in range(1, (len(word)-i)//2+1):
            if word[i:i+d] == word[i+d:i+2*d]:
                return False
    return True


def orbit(word):
    return min(word, word.translate(CYCLE), word.translate(CYCLE2))


def context_variables():
    """Iterative lexicographic DFS, independently reconstructing orbit IDs."""
    queue = [""]
    ids = {}
    full = 0
    while queue:
        word = queue.pop()
        if len(word) == CONTEXT_LENGTH:
            full += 1
            if orbit(word) == word:
                ids[word] = len(ids) + 1
            continue
        for letter in "3210":
            extended = word + letter
            n = len(extended)
            if all(extended[n-2*d:n-d] != extended[n-d:n]
                   for d in range(1, n//2+1)):
                queue.append(extended)
    check(full == 87936 and len(ids) == VARS,
          f"Unexpected original/orbit context census: {full}, {len(ids)}")
    return ids


def factor_clause(word, ids):
    n = len(word)
    check(n in SOURCE_CLASSES and squarefree(word),
          f"Bad finite source factor: {word!r}")
    if n == 15:
        literals = [ids[orbit(word[k:k+CONTEXT_LENGTH])] for k in range(5)]
    else:
        shift = n - CONTEXT_LENGTH
        literals = [
            -ids[orbit(word[:CONTEXT_LENGTH])],
            -ids[orbit(word[shift:shift+CONTEXT_LENGTH])],
        ]
    return tuple(sorted(set(literals)))


def read_core():
    lines = CORE.read_text(encoding="ascii").splitlines()
    check(lines and lines[0] == f"p cnf {VARS} {CLAUSES}",
          "Pinned reduced core has wrong DIMACS header")
    clauses = []
    for i, raw in enumerate(lines[1:], 1):
        tokens = [int(item) for item in raw.split()]
        check(len(tokens) >= 2 and tokens[-1] == 0
              and all(0 < abs(value) <= VARS for value in tokens[:-1]),
              f"Malformed original core clause {i}")
        literals = tuple(sorted(tokens[:-1]))
        check(len(literals) == len(set(literals)),
              f"Original core clause {i} has repeated literals")
        check(all(x > 0 for x in literals) or
              all(x < 0 for x in literals),
              f"Unexpected mixed-sign original core clause {i}")
        clauses.append(literals)
    check(len(clauses) == CLAUSES and len(set(clauses)) == CLAUSES,
          "Wrong original-core clause count or duplicates")
    return clauses


def hall_catalog(lengths):
    """Generate independent explicit Hall-Thue factor orbit membership."""
    text = "0"
    while len(text) < 32768:
        text = "".join(MORPHISM[x] for x in text)
    text = text[:32768]
    check(squarefree(text[:180]), "Hall-Thue finite sanity check failed")
    labels = [dict(zip("012", seq)) for seq in permutations("012")]
    result = {0: {""}}
    for n in sorted(lengths):
        if n == 0:
            continue
        check(1 <= n <= 15, f"Unexpected Hall exterior length {n}")
        values = set()
        for i in range(len(text)-n+1):
            value = text[i:i+n]
            for mapping in labels:
                renamed = "".join(mapping[x] for x in value)
                values.add(renamed)
                values.add(renamed[::-1])
        result[n] = values
    return result


def source_projection(record):
    return {
        key: record[key]
        for key in ("original_zero_based_clause_index",
                    "factor_length", "factor", "clause")
    }


def validate_partition(original, old, new, core, ids):
    check(original.get("core_clause_count") == CLAUSES
          and original.get("required_symmetry") == "(0 1 2)",
          "Original finite factor manifest metadata mismatch")
    all_sources = original.get("entries")
    check(isinstance(all_sources, list) and len(all_sources) == CLAUSES,
          "Original factor manifest count mismatch")
    actual_core = set(core)
    source = {}
    families = Counter()
    for item in all_sources:
        word = item["factor"]
        clause = tuple(item["clause"])
        check(item["factor_length"] == len(word)
              and set(word) <= set("0123")
              and clause == factor_clause(word, ids)
              and clause in actual_core and clause not in source,
              f"Original factor/quotient clause mismatch: {word}")
        source[clause] = source_projection(item)
        families[len(word)] += 1
    check(set(source) == actual_core and families == SOURCE_CLASSES,
          "Incomplete original core source factor coverage")

    check(old.get("source_manifest_sha256") == SHA_PINS[SOURCES]
          and old.get("total_core_factors") == CLAUSES
          and old.get("certified_candidate_count") == OLD
          and old.get("unresolved_count") == NEW,
          "Initial candidate triage metadata mismatch")
    check(new.get("source_core_factor_map_sha256") == SHA_PINS[SOURCES]
          and new.get("source_extension_triage_sha256") == SHA_PINS[FIRST]
          and new.get("source_unresolved_count") == NEW
          and new.get("new_candidate_count") == NEW
          and new.get("still_unresolved_count") == 0,
          "Additional 27-factor search metadata mismatch")
    old_candidates = old["candidates"]
    old_excluded = old["unresolved"]
    new_candidates = new["new_candidates"]
    check(len(old_candidates) == OLD and len(old_excluded) == NEW
          and len(new_candidates) == NEW and new["still_unresolved"] == [],
          "Source witness partitions have wrong lengths")

    def checked_source(item):
        clause = tuple(item["clause"])
        check(clause in source and source_projection(item) == source[clause],
              f"Certificate references an unrecognized source clause: {clause}")
        return clause

    known = {checked_source(item) for item in old_candidates}
    omitted = {checked_source(item) for item in old_excluded}
    appended = {checked_source(item) for item in new_candidates}
    check(len(known) == OLD and len(omitted) == NEW
          and len(appended) == NEW and not known.intersection(omitted)
          and appended == omitted and known | appended == actual_core,
          "Final 12,747-source-clause certificate partition incomplete")
    return old_candidates, new_candidates


def finite_certificate(record, hall):
    word = record["factor"]
    kind = record["kind"]
    mapping_pairs = record.get("source_to_normalized")
    check(isinstance(mapping_pairs, list)
          and all(isinstance(pair, list) and len(pair) == 2
                  and all(isinstance(item, str) and len(item) == 1
                          for item in pair)
                  for pair in mapping_pairs),
          f"Malformed original alphabet mapping: {word}")
    mapping = dict(mapping_pairs)
    check(len(mapping) == len(mapping_pairs)
          and set(mapping) == set(word)
          and len(set(mapping.values())) == len(mapping),
          f"Non-bijective alphabet mapping for {word}")
    is_ternary = kind in ("hall", "external-double-separator")
    check((set(mapping.values()) == set("012") and len(set(word)) == 3)
          if is_ternary else
          (set(mapping.values()) == set("0123") and len(set(word)) == 4),
          f"Invalid alphabet relabeling for construction {kind}: {word}")

    norm = "".join(mapping[x] for x in word)
    witness = record.get("finite_witness")
    offset = record.get("offset")
    check(isinstance(witness, str)
          and set(witness) <= set("0123")
          and type(offset) is int and 0 <= offset <= len(witness)-len(norm)
          and norm == record.get("normalized_factor")
          and witness[offset:offset+len(norm)] == norm,
          f"Invalid source factor embedding for {word}")
    check(squarefree(witness),
          f"Finite witness is NOT squarefree for {word}")

    if kind == "hall":
        check(record.get("separator") is None
              and witness == norm and offset == 0
              and "3" not in witness and witness in hall[len(witness)],
              f"Hall-Thue direct certificate failed: {word}")
        return

    check(record.get("separator") == "3",
          f"Expected distinguished separator 3 for {word}")
    positions = [i for i, letter in enumerate(witness) if letter == "3"]
    check(positions, f"Separator 3 missing from witness for {word}")
    left, right = witness[:positions[0]], witness[positions[-1]+1:]
    check(len(left) in hall and left in hall[len(left)]
          and len(right) in hall and right in hall[len(right)],
          f"Hall-Thue exterior membership failed for {word}")

    if kind == "external-double-separator":
        n = len(norm)
        check("3" not in norm and len(positions) == 2
              and positions == [n, 2*n+1]
              and len(left) == n and len(right) == n
              and offset == n+1
              and witness == left + "3" + norm + "3" + right,
              f"External two-separator construction has wrong geometry for {word}")
        return

    check(len(positions) == norm.count("3"),
          f"Padding introduced additional distinguished symbols for {word}")
    if kind == "single-separator":
        check(len(positions) == 1 and witness == norm and offset == 0,
              f"Single separator construction invalid for {word}")
        return

    check(kind in ("multi-separator", "padded-multi-separator",
                   "expanded-multi-separator"),
          f"Unknown multi-separator construction type: {kind}")
    check(len(positions) >= 2,
          f"Multi-separator construction requires multiple 3s for {word}")
    span = positions[-1] - positions[0]
    check(len(left) >= span - 1 and len(right) >= span - 1,
          f"Insufficient D-1 safety margins for {word}")
    if kind == "multi-separator":
        check(witness == norm and offset == 0,
              f"Unpadded multi-separator has extraneous padding: {word}")
    else:
        check(offset > 0 or len(witness) > offset + len(norm),
              f"Padded multi-separator is not actually padded: {word}")


def main():
    global CORE, PROOF, SOURCES, FIRST, SECOND, OUTPUT, SHA_PINS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=Path, required=True,
                        help="Path to independently compiled DRAT-trim")
    parser.add_argument("--archive-dir", type=Path,
                        help="Read the five SHA-pinned core/proof/manifests "
                             "from a committed archive instead of /tmp")
    parser.add_argument("--report", type=Path,
                        help="New local audit report output path (must not exist)")
    args = parser.parse_args()

    # Keep the independent mathematical audit unchanged. Rebind ONLY
    # source paths while preserving the same per-file cryptographic pins.
    if args.archive_dir is not None:
        archive = args.archive_dir.resolve()
        original_pins_by_name = {
            path.name: digest for path, digest in SHA_PINS.items()
        }
        CORE = archive / CORE.name
        PROOF = archive / PROOF.name
        SOURCES = archive / SOURCES.name
        FIRST = archive / FIRST.name
        SECOND = archive / SECOND.name
        SHA_PINS = {
            path: original_pins_by_name[path.name]
            for path in (CORE, PROOF, SOURCES, FIRST, SECOND)
        }
        OUTPUT = Path("/tmp/kbl-m3-r5-cycle012-archived-audit.json")

    if args.report is not None:
        OUTPUT = args.report.resolve()
    start = perf_counter()
    check(not OUTPUT.exists(),
          f"Refusing to overwrite pre-existing audit report: {OUTPUT}")
    for path, expected in SHA_PINS.items():
        check(path.is_file(), f"Missing proof artifact {path}")
        got = sha_file(path)
        check(got == expected,
              f"SHA mismatch for {path}: {got}, expected {expected}")
    check(args.checker.is_file(), "Independent DRAT checker binary absent")
    print("C3 q4,m3,r5 — INTEGRATED BI-INFINITE OBSTRUCTION VERIFIER",
          flush=True)
    print("PHASE 1/4 PASSED: exact SHA-256 identity of five proof artifacts",
          flush=True)

    ids = context_variables()
    core_clauses = read_core()
    source = json.loads(SOURCES.read_text(encoding="utf-8"))
    early = json.loads(FIRST.read_text(encoding="utf-8"))
    additional = json.loads(SECOND.read_text(encoding="utf-8"))
    early_recs, additional_recs = validate_partition(
        source, early, additional, core_clauses, ids
    )
    print("PHASE 2/4 PASSED: 87,936 original contexts, 29,312 C3 orbits,")
    print("  12,747 original square-free core source factors independently")
    print("  reconstructed and partitioned 12,720 + 27 without gaps",
          flush=True)

    records = early_recs + additional_recs
    lengths = {0}
    for item in records:
        finite = item["finite_witness"]
        spots = [j for j, c in enumerate(finite) if c == "3"]
        lengths.add(len(finite) if not spots else spots[0])
        if spots:
            lengths.add(len(finite)-1-spots[-1])
    # The direct Hall cases have witness length <=15.  In separator
    # cases these are precisely the two full ternary exterior lengths.
    hall = hall_catalog(lengths)
    hist = Counter()
    families = Counter()
    for index, item in enumerate(records, 1):
        finite_certificate(item, hall)
        hist[item["kind"]] += 1
        families[item["factor_length"]] += 1
        if index % 2500 == 0:
            print(f"  Finite extension witnesses verified: {index}/{CLAUSES}",
                  flush=True)
    check(hist == CONSTRUCTION_CLASSES,
          f"Unexpected independently verified construction counts {hist}")
    check(families == SOURCE_CLASSES,
          f"Unexpected independently verified source family counts {families}")
    print("PHASE 3/4 PASSED: ALL 12,747 finite squarefree factor extension")
    print("  witnesses meet Hall-Thue and separator conditions")
    print("  Constructions:", dict(sorted(hist.items())))
    print("  Source families:", dict(sorted(families.items())), flush=True)

    result = subprocess.run(
        [str(args.checker), str(CORE), str(PROOF), "-I"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False, timeout=120,
    )
    check(result.returncode == 0,
          f"DRAT checker failed, exit {result.returncode}: {result.stdout[-1000:]}")
    check(any(line.strip() == "s VERIFIED"
              for line in result.stdout.splitlines()),
          "DRAT checker did not return exact 's VERIFIED'")
    print("PHASE 4/4 PASSED: direct STANDALONE independently verified UNSAT")
    print("  Core clauses:", CLAUSES)
    print("  DRAT checker exit code:", result.returncode)
    print("  DRAT exact result: s VERIFIED")
    for line in result.stdout.splitlines():
        if "clauses in core" in line or "resolution steps" in line:
            print(" ", line.strip())
    print("  C3-invariant radius-5 marker assignment: CONTRADICTION",
          flush=True)

    report = {
        "status": "FULL FINITE AND DRAT CHECKS PASSED",
        "scope": "q4,m3,r5 single-C3-invariant shift-equivariant Boolean marker rule",
        "mathematical_inputs": [
            "classical squarefree uniformly recurrent Hall-Thue ternary morphism",
            "finite separator lemma with D-1 Hall-extendible ternary exteriors",
        ],
        "input_sha256": {p.name: digest for p, digest in SHA_PINS.items()},
        "original_core_clauses": CLAUSES,
        "old_certificate_records": len(early_recs),
        "new_certificate_records": len(additional_recs),
        "construction_classes": dict(sorted(hist.items())),
        "factor_length_classes": dict(sorted(families.items())),
        "original_named_length11_contexts": 87936,
        "orbit_length11_contexts": VARS,
        "checked_unsat_proof": "s VERIFIED",
        "checker_exit_code": result.returncode,
        "global_theorem": (
            "No radius-5 marker rule invariant under any chosen alphabet "
            "3-cycle on the bi-infinite quaternary squarefree subshift "
            "satisfies separation>=3 and domination<=2"
        ),
        "not_claimed": [
            "minimum radius for 3-cycle-invariant rules at r>=6",
            "generalization in m",
            "unrestricted CDC/O(m) edit-locality",
            "publication novelty",
        ],
    }
    raw = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with OUTPUT.open("xb") as output:
        output.write(raw)
    print("ALL FOUR PHASES PASSED")
    print("COMPUTER-ASSISTED THEOREM (Hall-Thue + finite-separator lemma):")
    print("  No q4,m3,r5 single-C3-invariant marker rule exists on ALL")
    print("  bi-infinite quaternary square-free words.")
    print("  By alphabet conjugacy: ANY single 3-cycle is excluded.")
    print("  The unrestricted exact radius remains 5; a single transposition")
    print("  is compatible, while single 4-cycles are separately excluded.")
    print("  No minimum C3-invariant radius or novelty is established.")
    print("  Audit report:", OUTPUT)
    print("  Audit report SHA-256:", sha256(raw).hexdigest())
    print("  Audit report bytes:", len(raw))
    print(f"  Elapsed seconds: {perf_counter()-start:.2f}")


if __name__ == "__main__":
    main()
