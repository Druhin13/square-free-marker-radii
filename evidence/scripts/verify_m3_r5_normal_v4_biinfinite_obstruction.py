#!/usr/bin/env python3
"""INTEGRATED normal-V4 q=4,m=3,r=5 BI-INFINITE obstruction verifier.

No imports from the marker CNF exporter, core provenance constructor,
Hall-Thue candidate generators, prior extension verifiers or SAT tools.

Independently and exhaustively checks on SHA-256-pinned inputs:
  1. Exact original independently DRAT-verified 53,487-clause CNF,
     optimized standalone ASCII DRAT, named squarefree source manifest,
     old 53,476 candidate witnesses, new 11 external-double-separator
     witnesses and the independent additional-witness audit.
  2. All 87,936 named length-11 squarefree words and the 21,984
     quotient context IDs under K={e,(01)(23),(02)(13),(03)(12)};
     all 53,487 original source factor-to-clause mappings and
     exactly 53,476+11 disjoint witness-source records.
  3. Every old and new finite witness independently, including
     squarefreeness, alphabet bijection, factor embedding, Hall-Thue
     ternary factor membership under relabeling/reversal, and the
     D-1 separator safety criterion.  For external double separators,
     explicitly check the two separators, span n+1 and n-long tails.
  4. On those *same* original 53,487 clauses, launch independent
     DRAT-trim with the already SHA-pinned optimized ASCII proof:
         drat-trim core.cnf core-lemmas.drat -I
     Require process exit code 0 and an exact 's VERIFIED' line.

Under two classical mathematical inputs (not reproved by this program):
    * Hall-Thue's ternary fixed point is squarefree and uniformly
      recurrent, so each listed factor extends to a suitable infinite
      ternary tail;
    * the finite-separator lemma, with D-1 ternary safety margins,
      ensures bi-infinite squarefreeness of the resulting word.
An individually extendible factor provides a necessary marker clause
for the TRUE bi-infinite squarefree shift; a verified UNSAT refutation
of the complete supported original core then excludes a radius-five
normal-V4-invariant Boolean marker rule with separation at least 3
and domination radius at most 2.

This calculation does not establish results for other subgroup types,
radius >5 or other marker parameters.

All input files remain unchanged; on complete success only one NEW
deterministic JSON report is created (exclusive create).  Can read
SHA-pinned archives for standalone reproduction, if available.

Usage:
    python3 -B -m scripts.verify_m3_r5_normal_v4_biinfinite_obstruction \\
      --checker /tmp/square-free-marker-drat-trim/drat-trim
"""
import argparse
from collections import Counter
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import subprocess
from time import perf_counter

CORE = Path("/tmp/square-free-marker-m3-r5-normal-v4-core.cnf")
DRAT = Path("/tmp/square-free-marker-m3-r5-normal-v4-core-lemmas.drat")
ORIGIN = Path("/tmp/square-free-marker-m3-r5-normal-v4-core-factor-map.json")
EARLY = Path("/tmp/square-free-marker-m3-r5-normal-v4-core-extension-triage.json")
EXTRAS = Path("/tmp/square-free-marker-m3-r5-normal-v4-extra-extensions.json")
EXTRA_AUDIT = Path("/tmp/square-free-marker-m3-r5-normal-v4-extra-extensions-audit.json")
CERTIFIED_SUBSET = Path("/tmp/square-free-marker-m3-r5-normal-v4-extendible-only.cnf")
DEFAULT_REPORT = Path("/tmp/square-free-marker-m3-r5-normal-v4-biinfinite-obstruction-audit.json")

EXPECTED_SHA = {
    CORE: "1b8e67aa86f661ac6a9d369e6298357ab0541af58287152f9a498844a678d729",
    DRAT: "215a9ac707124910261a23749bccfff6771edea3f0a63b9b6b6eb361919b91e3",
    ORIGIN: "a6dc740e073adf3ba4dafb14f958997e32511f829e161867fd02799eaee10744",
    EARLY: "3b66c4b75cba46a597f6f666f81123eebd0d2d4a3dd949ce217b847cbf1ed704",
    EXTRAS: "9892679b2234d96a86b73d6cb264ae9511094f25a7aa187bb90f0d528332f201",
    EXTRA_AUDIT: "f12d5b8bf6b5ce97dff3770812af24d9dbd7901b5d1a8cbd4facaf43169ba375",
    CERTIFIED_SUBSET: "ed46e0bd9321d6df91ab14cb9dfad39dc78b6d1efd5b2fcab8728a4383b8f284",
}
Q, M, R = 4, 3, 5
VARS = 21984
CORE_ROWS = 53487
OLD_ROWS = 53476
NEW_ROWS = 11
FAMILY = {12: 11269, 13: 20376, 15: 21842}
KINDS = {
    "hall": 18,
    "single-separator": 30,
    "multi-separator": 25,
    "padded-multi-separator": 53403,
    "external-double-separator": 11,
}
FIRST = {12: 0, 13: 57630, 15: 208782}
LAST = {12: 57630, 13: 208782, 15: 1247880}
MORPHISM = {"0": "012", "1": "02", "2": "1"}


def require(ok, explanation):
    if not ok:
        raise AssertionError(explanation)


def hash_path(path):
    h = sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def squarefree(word):
    """Explicitly test every square substring, not only suffixes."""
    for i in range(len(word)):
        for d in range(1, (len(word) - i) // 2 + 1):
            if word[i:i+d] == word[i+d:i+2*d]:
                return False
    return True


def squarefree_named_words(length):
    """Iterative DFS in alphabetical order, square-suffix prune."""
    todo = [""]
    while todo:
        prefix = todo.pop()
        if len(prefix) == length:
            yield prefix
            continue
        for char in "3210":
            test = prefix + char
            n = len(test)
            if all(test[n-2*d:n-d] != test[n-d:n]
                   for d in range(1, n // 2 + 1)):
                todo.append(test)


def orbit_normal(word):
    """V4 acts as bitwise-XOR translation on two-bit letter labels."""
    require(bool(word), "Cannot normalize an empty context")
    first = int(word[0])
    return "".join(str(first ^ int(c)) for c in word)


def enumerate_orbit_ids():
    ids = {}
    count = 0
    for word in squarefree_named_words(11):
        count += 1
        if word.startswith("0"):
            require(orbit_normal(word) == word,
                    "Incorrect normal-V4 canonical context")
            ids[word] = len(ids) + 1
    require(count == 87936 and len(ids) == VARS,
            f"Wrong n11 context orbit census {count}, {len(ids)}")
    return ids, count


def clause_from_original_factor(word, contexts):
    n = len(word)
    require(n in FAMILY and squarefree(word),
            f"Invalid original finite source word {word!r}")
    if n < 15:
        step = n - 11
        values = [
            -contexts[orbit_normal(word[:11])],
            -contexts[orbit_normal(word[step:step+11])],
        ]
    else:
        values = [
            contexts[orbit_normal(word[index:index+11])]
            for index in range(5)
        ]
    return tuple(sorted(set(values)))


def parse_dimacs(path, count):
    rows = []
    with path.open("rb") as source:
        require(source.readline() == f"p cnf {VARS} {count}\n".encode(),
                f"Unexpected pinned CNF header in {path.name}")
        for index, raw in enumerate(source, 1):
            tokens = [int(v) for v in raw.split()]
            require(len(tokens) >= 2 and tokens[-1] == 0,
                    f"Malformed DIMACS row {index} in {path.name}")
            literals = tuple(sorted(tokens[:-1]))
            require(len(literals) == len(set(literals)) and
                    all(0 < abs(lit) <= VARS for lit in literals) and
                    (all(lit < 0 for lit in literals) or
                     all(lit > 0 for lit in literals)),
                    f"Invalid source-clause literal(s) in row {index}")
            rows.append(literals)
    require(len(rows) == count and len(set(rows)) == count,
            f"Incorrect clause census/duplicates for {path}")
    return rows


def source_identity(record):
    return {key: record[key] for key in (
        "original_zero_based_clause_index",
        "factor_orbit_index",
        "factor_length",
        "factor",
        "clause",
    )}


def validate_sources(origin, early, extras, extra_audit, core, subset, ids):
    require(origin.get("subgroup") ==
            "normal V4 = {e,(01)(23),(02)(13),(03)(12)}" and
            origin.get("core_clause_count") == CORE_ROWS,
            "Source corpus group/count mismatch")
    origin_entries = origin.get("entries")
    require(isinstance(origin_entries, list) and
            len(origin_entries) == CORE_ROWS,
            "Original source provenance count mismatch")
    original_core = set(core)
    mapped = {}
    hist = Counter()
    for entry in origin_entries:
        n = entry["factor_length"]
        row = entry["original_zero_based_clause_index"]
        rank = entry["factor_orbit_index"]
        word = entry["factor"]
        literals = tuple(entry["clause"])
        require(n in FAMILY and len(word) == n and
                set(word) <= set("0123") and
                FIRST[n] <= row < LAST[n] and
                rank == row - FIRST[n],
                f"Original source length/ordinal mismatch {word!r}")
        require(literals == clause_from_original_factor(word, ids) and
                literals in original_core and literals not in mapped,
                f"Original factor-to-quotient marker clause mismatch {word}")
        mapped[literals] = source_identity(entry)
        hist[n] += 1
    require(hist == FAMILY and set(mapped) == original_core,
            f"Incomplete source length/quotient coverage: {hist}")

    old = early.get("candidates")
    unresolved = early.get("unresolved")
    appended = extras.get("candidates")
    require(isinstance(old, list) and len(old) == OLD_ROWS and
            isinstance(unresolved, list) and len(unresolved) == NEW_ROWS and
            isinstance(appended, list) and len(appended) == NEW_ROWS,
            "Wrong old/new witness-list cardinality")
    require(early.get("source_manifest_sha256") == EXPECTED_SHA[ORIGIN] and
            early.get("candidate_count") == OLD_ROWS and
            early.get("unresolved_count") == NEW_ROWS and
            extras.get("source_origin_sha256") == EXPECTED_SHA[ORIGIN] and
            extras.get("source_triage_sha256") == EXPECTED_SHA[EARLY] and
            extras.get("new_candidate_count") == NEW_ROWS and
            extras.get("unresolved_after_candidate_construction") == 0,
            "Old/new candidate provenance/metadata mismatch")

    old_set = {tuple(entry["clause"]) for entry in old}
    unresolved_set = {tuple(entry["clause"]) for entry in unresolved}
    appended_set = {tuple(entry["clause"]) for entry in appended}
    require(len(old_set) == OLD_ROWS and
            len(unresolved_set) == len(appended_set) == NEW_ROWS and
            unresolved_set == appended_set and
            not old_set.intersection(appended_set) and
            old_set | appended_set == original_core and
            old_set == set(subset),
            "Old/new candidate partition or certified-only CNF mismatch")
    for collection in (old, unresolved, appended):
        for entry in collection:
            key = tuple(entry["clause"])
            require(source_identity(entry) == mapped[key],
                    "Certified source record disagrees with original source")
    certified_extra = extra_audit.get("new_certified_source_factors")
    require(extra_audit.get("new_certificates_independently_checked") == NEW_ROWS and
            extra_audit.get("complete_original_core_source_partition") is True and
            isinstance(certified_extra, list) and
            len(certified_extra) == NEW_ROWS,
            "Independent additional-source report metadata mismatch")
    checked_extra = {
        (x["original_zero_based_clause_index"],
         x["factor_length"], x["factor"], tuple(x["clause"]))
        for x in certified_extra
    }
    new_details = {
        (x["original_zero_based_clause_index"],
         x["factor_length"], x["factor"], tuple(x["clause"]))
        for x in appended
    }
    require(checked_extra == new_details and len(checked_extra) == NEW_ROWS,
            "Additional source factors do not match originals")
    print("PHASE 2/4 PASSED: independent length-11 orbit IDs and complete")
    print("  53,487 original named squarefree source-factor clause identities")
    print("  Exact partition: 53,476 previously certified + 11 new")
    print("  Original source family census:", dict(sorted(hist.items())),
          flush=True)
    return old, appended, hist


def hall_catalog(lengths):
    """Independent explicit Hall-Thue factors, all 6 renamings and reversal."""
    text = "0"
    while len(text) < 32768:
        text = "".join(MORPHISM[c] for c in text)
    text = text[:32768]
    require(squarefree(text[:220]),
            "Classical Hall-Thue finite prefix failed basic squarefreeness")
    p = tuple(dict(zip("012", perm)) for perm in permutations("012"))
    result = {0: {""}}
    for length in sorted(set(lengths)):
        if length == 0:
            continue
        require(1 <= length <= 15,
                f"Unexpected Hall exterior factor length {length}")
        variants = set()
        factors = {text[i:i+length]
                   for i in range(len(text) - length + 1)}
        for frag in factors:
            for table in p:
                variant = "".join(table[ch] for ch in frag)
                variants.add(variant)
                variants.add(variant[::-1])
        result[length] = variants
    return result


def normalized_factor(record):
    pairs = record.get("source_to_normalized")
    require(isinstance(pairs, list) and
            all(isinstance(pair, list) and len(pair) == 2 and
                all(isinstance(x, str) and len(x) == 1 for x in pair)
                for pair in pairs),
            f"Bad source-to-normalized mapping for {record['factor']}")
    table = dict(pairs)
    require(len(table) == len(pairs) and
            len(set(table.values())) == len(table),
            f"Original alphabet map not injective: {record['factor']}")
    kind = record["kind"]
    if kind == "hall":
        require(set(table) == set(record["factor"]) and
                set(table.values()) == set("012") and
                len(set(record["factor"])) == 3,
                f"Invalid direct Hall renaming: {record['factor']}")
    elif kind == "external-double-separator":
        require(len(table) == 4 and set(table) == set("0123") and
                set(table.values()) == set("0123") and
                len(set(record["factor"])) == 3,
                f"Invalid external double separator full permutation")
        unused = set("0123") - set(record["factor"])
        require(len(unused) == 1 and
                record.get("unused_original_symbol") == next(iter(unused)) and
                table[next(iter(unused))] == "3",
                f"Absent original letter not mapped to 3")
    else:
        require(set(table) == set(record["factor"]) and
                set(table.values()) == set("0123") and
                len(set(record["factor"])) == 4,
                f"Invalid 4-letter separator normalization")
    value = "".join(table[ch] for ch in record["factor"])
    require(value == record.get("normalized_factor"),
            f"Normalized source mismatch: {record['factor']}")
    return value


def validate_finite_witness(record, hall):
    word = record["factor"]
    kind = record.get("kind")
    require(kind in KINDS and len(word) == record["factor_length"],
            f"Unknown witness type or length for {word}")
    norm = normalized_factor(record)
    witness = record.get("finite_witness")
    offset = record.get("offset")
    require(isinstance(witness, str) and
            set(witness) <= set("0123") and
            type(offset) is int and
            0 <= offset <= len(witness) - len(norm) and
            witness[offset:offset+len(norm)] == norm and
            squarefree(witness),
            f"Finite witness squarefreeness/embedding failure for {word}")

    if kind == "hall":
        require(witness == norm and offset == 0 and
                record.get("separator") is None and
                "3" not in witness and
                witness in hall[len(witness)],
                f"Direct Hall factor not certified for {word}")
        return
    require(record.get("separator") == "3",
            f"Missing distinguished separator 3 for {word}")
    positions = [i for i,c in enumerate(witness) if c == "3"]
    require(positions, f"Missing separator symbol in witness for {word}")
    left = witness[:positions[0]]
    right = witness[positions[-1]+1:]
    require(left in hall[len(left)] and right in hall[len(right)],
            f"Hall-Thue ternary exterior factor missing for {word}")

    if kind == "external-double-separator":
        n = len(word)
        require("3" not in norm and len(positions) == 2 and
                positions == [n, 2*n+1] and
                record.get("first_separator_index") == n and
                record.get("second_separator_index") == 2*n+1 and
                record.get("separator_span") == n+1 and
                record.get("offset") == n+1 and
                len(left) == len(right) == n and
                record.get("left_hall_factor") == left and
                record.get("right_hall_factor") == right and
                witness == left+"3"+norm+"3"+right,
                f"External double separator geometry failed for {word}")
        require(len(left) >= n and len(right) >= n,
                f"External separator exterior margin D-1 failed for {word}")
        return
    require(len(positions) == norm.count("3"),
            f"Padding introduced extra separator(s) for {word}")
    if kind == "single-separator":
        require(len(positions) == 1 and
                witness == norm and offset == 0,
                f"Single separator witness geometry failed for {word}")
        return
    require(kind in ("multi-separator","padded-multi-separator") and
            len(positions) >= 2,
            f"Invalid multiple-separator witness category {word}")
    span = positions[-1] - positions[0]
    require(len(left) >= span-1 and len(right) >= span-1,
            f"Finite separator lemma margins D-1 not satisfied for {word}")
    if kind == "multi-separator":
        require(witness == norm and offset == 0,
                f"Unpadded witness has unexpected padding: {word}")
    else:
        require(offset > 0 or len(witness) > offset+len(norm),
                f"Padded witness has no padding: {word}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker",type=Path,required=True,
                        help="independently built DRAT-trim executable")
    parser.add_argument("--archive-dir",type=Path,
                        help="directory containing exact SHA-pinned artifact filenames")
    parser.add_argument("--report",type=Path,
                        help="new local report path; file must not already exist")
    args = parser.parse_args()

    started = perf_counter()
    report_path = args.report or DEFAULT_REPORT
    require(not report_path.exists(), f"Refusing overwrite: {report_path}")

    if args.archive_dir is not None:
        paths = {original: args.archive_dir / original.name
                 for original in EXPECTED_SHA}
    else:
        paths = {original: original for original in EXPECTED_SHA}

    require(args.checker.is_file() and
            args.checker.stat().st_mode & 0o111,
            f"Expected executable independent checker: {args.checker}")
    for original, pin in EXPECTED_SHA.items():
        path = paths[original]
        require(path.is_file(), f"Missing exact artifact: {path}")
        got = hash_path(path)
        require(got == pin,
                f"SHA256 mismatch for {path}: observed={got}, expected={pin}")
        print("  SHA-PINNED:",path.name,got,flush=True)
    print("PHASE 1/4 PASSED: exact identity of all seven source/proof artifacts",
          flush=True)

    core_rows = parse_dimacs(paths[CORE], CORE_ROWS)
    certified_rows = parse_dimacs(paths[CERTIFIED_SUBSET], OLD_ROWS)
    ids, named = enumerate_orbit_ids()
    origin = json.loads(paths[ORIGIN].read_bytes())
    early = json.loads(paths[EARLY].read_bytes())
    extras = json.loads(paths[EXTRAS].read_bytes())
    extra_audit = json.loads(paths[EXTRA_AUDIT].read_bytes())
    old, new, family = validate_sources(
        origin, early, extras, extra_audit, core_rows, certified_rows, ids
    )

    hall_lengths={0}
    for record in old+new:
        finite=record["finite_witness"]
        positions=[i for i,c in enumerate(finite) if c=="3"]
        if positions:
            hall_lengths.add(positions[0])
            hall_lengths.add(len(finite)-positions[-1]-1)
        else:
            hall_lengths.add(len(finite))
    hall=hall_catalog(hall_lengths)
    histogram=Counter()
    census=Counter()
    for index, record in enumerate(old+new,1):
        validate_finite_witness(record,hall)
        histogram[record["kind"]]+=1
        census[record["factor_length"]]+=1
        if index%5000==0:
            print(f"  Independently checked finite source witnesses: "
                  f"{index}/{CORE_ROWS}",flush=True)
    require(histogram==KINDS and census==FAMILY,
            f"Wrong witness classes/families {histogram} {census}")
    print("PHASE 3/4 PASSED: EVERY original source factor has an independently")
    print("  checked finite Hall-Thue or safe-separator bi-infinite extension")
    print("  All witnessed source factors:",sum(histogram.values()))
    print("  Witness kinds:",dict(sorted(histogram.items())))
    print("  Source factor lengths:",dict(sorted(census.items())),flush=True)

    checker = subprocess.run(
        [str(args.checker),str(paths[CORE]),str(paths[DRAT]),"-I"],
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,check=False,timeout=120,
    )
    require(checker.returncode==0,
            f"DRAT-trim exit {checker.returncode}: {checker.stdout[-1400:]}")
    require(any(line.strip()=="s VERIFIED"
                for line in checker.stdout.splitlines()),
            "Independent DRAT-trim did not produce exact s VERIFIED")
    for source,pin in EXPECTED_SHA.items():
        require(hash_path(paths[source])==pin,
                f"Source/proof artifact mutated during audit: {source.name}")
    print("PHASE 4/4 PASSED: independently replayed optimized standalone")
    print("  UNSAT proof on exactly the 53,487 bi-infinitely supported clauses")
    print("  Independent checker exit:",checker.returncode)
    print("  Independent checker exact status: s VERIFIED")
    for line in checker.stdout.splitlines():
        if "clauses in core" in line or "resolution steps" in line:
            print(" ",line.strip())
    report={
        "status":"ALL FOUR NORMAL-V4 BI-INFINITE OBSTRUCTION AUDIT PHASES PASSED",
        "q":Q,"m":M,"r":R,
        "normal_v4_group":"{e,(01)(23),(02)(13),(03)(12)}",
        "marker_separation":"at least 3",
        "marker_domination":"within distance 2",
        "math_inputs":[
            "classical squarefree uniformly recurrent Hall-Thue ternary fixed point",
            "finite-separator lemma with D-1 Hall-extendible ternary exteriors",
        ],
        "sha256_inputs":{p.name:pin for p,pin in EXPECTED_SHA.items()},
        "original_named_n11_contexts":named,
        "normal_v4_context_orbit_variables":len(ids),
        "verified_original_core_clauses":CORE_ROWS,
        "verified_early_extension_witnesses":len(old),
        "verified_external_double_separator_witnesses":len(new),
        "construction_histogram":dict(sorted(histogram.items())),
        "factor_length_histogram":dict(sorted(census.items())),
        "independent_drat_checker_exit":checker.returncode,
        "independent_drat_status":"s VERIFIED",
        "fixed_parameter_theorem":(
            "No shared shift-equivariant radius-five marker rule on the "
            "bi-infinite quaternary squarefree subshift, with separation>=3 "
            "and domination<=2, is invariant under the normal Klein-four "
            "subgroup {e,(01)(23),(02)(13),(03)(12)}."
        ),
        "not_claimed":[
            "intransitive V4 obstruction or existence",
            "higher-radius normal-V4 results",
            "arbitrary m, generalization to other q",
        ],
    }
    raw=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode()
    with report_path.open("xb") as dst:
        dst.write(raw)
    print("ALL FOUR NORMAL-V4 INTEGRATED AUDIT PHASES PASSED")
    print("COMPUTER-ASSISTED THEOREM (classical Hall-Thue + finite separator):")
    print("  No q4,m3,r5 normal-V4-invariant radius-5 marker rule exists")
    print("  on ALL bi-infinite quaternary squarefree sequences, subject")
    print("  to separation >=3 and domination distance <=2.")
    print("  Audit report:",report_path)
    print("  Report SHA-256:",sha256(raw).hexdigest())
    print("  Audit report bytes:",len(raw))
    print(f"  Elapsed seconds: {perf_counter()-started:.2f}")
    print("No conclusion about intransitive V4 or other marker parameters.")

if __name__=="__main__":
    main()
