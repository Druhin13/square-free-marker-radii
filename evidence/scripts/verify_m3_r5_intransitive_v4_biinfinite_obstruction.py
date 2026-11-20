#!/usr/bin/env python3
"""Independent intransitive-V4 bi-infinite obstruction audit.

Fixed q=4,m=3,r=5, H=< (01),(23) >, separation>=3, domination<=2.

This standalone verifier imports NO other research generator, source mapper,
candidate constructor, extension auditor, SAT model checker or SAT solver.

Four independent audit phases:
  (1) Cryptographically pin all EIGHT exact source/proof artifacts and an
      independent DRAT-trim executable (the latter must be executable).
  (2) Re-enumerate original length-11 H-orbit contexts (21,984) and all
      original named length-12/13/15 squarefree source factors, verify all
      original 26,819 core source-factor clause identities and their
      lexicographic source ranks, source partition, and an independently checked source report.
  (3) Recheck ALL 26,814 + 5 finite Hall-Thue/separator witnesses, including
      complete finite squarefreeness, original factor embedding, letter
      bijections, true Hall-Thue factor membership under permutation and
      reversal, no added separators, and D-1 safety margins.
  (4) Replay the exact 26,819-source standalone optimized ASCII DRAT proof
      against the same original SHA-pinned core, requiring exit=0, exact
      's VERIFIED' and original artifacts unchanged.

Mathematical assumptions NOT proved by Python: the classical squarefree
uniform recurrence of the ternary Hall-Thue fixed point, and the finite
separator D-1 safety-margin lemma. Under those premises, independently
certified bi-infinite occurrence of every source implies that the
independently DRAT-refuted finite-factor core supplies a contradiction
for any H-invariant shift-equivariant radius-five Boolean marker rule
on the true bi-infinite quaternary squarefree subshift.

This calculation does not address arbitrary radii, other parameters,
or non-H-invariant rules.

All inputs untouched. Creates exactly ONE new deterministic JSON report
using exclusive creation. Optional --archive-dir rebinds the exact pinned
filenames to a separate immutable proof archive (for clean reproduction).

Usage from the evidence directory:
  python3 -B -m scripts.verify_m3_r5_intransitive_v4_biinfinite_obstruction \
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

CORE = Path("/tmp/kbl-m3-r5-intransitive-v4-core.cnf")
DRAT = Path("/tmp/kbl-m3-r5-intransitive-v4-core-lemmas.drat")
ORIGIN = Path("/tmp/kbl-m3-r5-intransitive-v4-core-factor-map.json")
EARLY = Path("/tmp/kbl-m3-r5-intransitive-v4-core-extension-triage.json")
EXTRAS = Path("/tmp/kbl-m3-r5-intransitive-v4-extra-extensions.json")
EXTRA_AUDIT = Path("/tmp/kbl-m3-r5-intransitive-v4-extra-extensions-audit.json")
CERTIFIED_SUBSET = Path("/tmp/kbl-m3-r5-intransitive-v4-extendible-only.cnf")
SAT_AUDIT = Path("/tmp/kbl-m3-r5-intransitive-v4-certified-only-sat-audit.json")
DEFAULT_REPORT = Path("/tmp/kbl-m3-r5-intransitive-v4-biinfinite-obstruction-audit.json")

EXPECTED_SHA = {
    CORE: "e5707d9aa7f077c05d8775552ea9566e5eaa7a4885d8b5c99f6b69e27c9d8db9",
    DRAT: "6806854a58c47d7444648b1df49cbfe8b718ad9c9b7c8a5c01308a4f36231c08",
    ORIGIN: "0e74186db840c89fca385168cd0118e9a24bd4b29920aadea53878dde0feb080",
    EARLY: "b3f803c02971d8b1d25cc183f7eed02b0603ac602bb36e1dd0560be5efdaa4bb",
    EXTRAS: "560cf9b55b4ebd97790bdc8c367e5e7047088261b85c952fed19b803f90eaf32",
    EXTRA_AUDIT: "d8b4ceb8140e5952d2bfdb955d00a3237f45ab837db7cd4b81959567fd68900e",
    CERTIFIED_SUBSET: "8584532defcb1d487f0653f2b83d3148f2165a50ff3dec5d89bbec58e4e69fde",
    SAT_AUDIT: "72bc9f64c27db433878fc2405c4ba1f132e9cacf3c79f191d19f19e86ad21762",
}
Q, M, R = 4, 3, 5
VARS = 21984
CORE_ROWS = 26819
OLD_ROWS = 26814
NEW_ROWS = 5
FAMILY = {12: 5967, 13: 10578, 15: 10274}
ORBIT_COUNTS = {11: 21984, 12: 57630, 13: 151152, 15: 1039098}
NAMED_COUNTS = {11: 87936, 12: 230520, 13: 604608, 15: 4156392}
KINDS = {
    "hall": 12,
    "single-separator": 31,
    "multi-separator": 80,
    "padded-multi-separator": 26691,
    "external-double-separator": 3,
    "expanded-padded-multi-separator": 2,
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


def h_firsts(word):
    a = next((letter for letter in word if letter in "01"), None)
    b = next((letter for letter in word if letter in "23"), None)
    require(a is not None and b is not None,
            "Source/context missing one invariant alphabet block")
    return a, b


def orbit_normal(word):
    """H=< (01),(23) >: normalize FIRST encountered letter per block."""
    a, b = h_firsts(word)
    flip_a = int(a == "1")
    flip_b = int(b == "3")
    return "".join(str(int(letter) ^ (flip_a if letter in "01" else flip_b))
                   for letter in word)


def enumerate_orbit_ids():
    ids = {}
    count = 0
    for word in squarefree_named_words(11):
        count += 1
        if h_firsts(word) == ("0", "2"):
            require(orbit_normal(word) == word,
                    "Incorrect intransitive-H canonical n11 context")
            ids[word] = len(ids) + 1
    require(count == NAMED_COUNTS[11] and len(ids) == VARS,
            f"Incorrect n11/H quotient count: {count}/{len(ids)}")
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


def validate_sources(origin, early, extras, extra_audit, sat_audit,
                     core, subset, ids):
    require(origin.get("subgroup") ==
            "intransitive V4 = {e,(01),(23),(01)(23)}" and
            origin.get("core_clause_count") == CORE_ROWS and
            origin.get("full_clause_count") == 1247880 and
            origin.get("input_sha256", {}).get(CORE.name) == EXPECTED_SHA[CORE],
            "Unexpected original H source identity or CNF hash")
    origin_entries = origin.get("entries")
    require(isinstance(origin_entries, list) and
            len(origin_entries) == CORE_ROWS,
            "Incomplete named-original source provenance")
    exact_core = set(core)
    mapped = {}
    ranks = {12: {}, 13: {}, 15: {}}
    family = Counter()
    for entry in origin_entries:
        word = entry["factor"]
        n = entry["factor_length"]
        row = entry["original_zero_based_clause_index"]
        rank = entry["factor_orbit_index"]
        clause = tuple(entry["clause"])
        require(n in FAMILY and type(word) is str and
                len(word) == n and set(word) <= set("0123") and
                squarefree(word) and h_firsts(word) == ("0", "2") and
                orbit_normal(word) == word and
                type(rank) is int and type(row) is int and
                FIRST[n] <= row < LAST[n] and
                row == FIRST[n]+rank,
                f"Bad original squarefree H source index: {word!r}")
        require(clause == clause_from_original_factor(word, ids) and
                clause in exact_core and clause not in mapped and
                rank not in ranks[n],
                f"Wrong original source-H clause mapping: {word}")
        mapped[clause] = source_identity(entry)
        ranks[n][rank] = word
        family[n] += 1
    require(len(mapped) == CORE_ROWS and set(mapped) == exact_core and
            family == Counter(FAMILY),
            "Original core source records do not cover full UNSAT core")
    for n in (12, 13, 15):
        total = 0
        orbits = 0
        selected = 0
        for word in squarefree_named_words(n):
            total += 1
            if h_firsts(word) != ("0", "2"):
                continue
            if orbits in ranks[n]:
                require(ranks[n][orbits] == word,
                        f"Original H source rank n={n}, orbit={orbits} wrong")
                selected += 1
            orbits += 1
        require(total == NAMED_COUNTS[n] and
                orbits == ORBIT_COUNTS[n] and
                selected == len(ranks[n]),
                f"Original independent n{n} squarefree/H factor census invalid")
        print(f"  n{n}: named={total}, H-orbits={orbits}, "
              f"source-ranks={selected}", flush=True)

    old = early.get("candidates")
    unresolved = early.get("unresolved")
    appended = extras.get("candidates")
    require(early.get("source_manifest_sha256") == EXPECTED_SHA[ORIGIN] and
            early.get("candidate_count") == OLD_ROWS and
            early.get("unresolved_count") == NEW_ROWS and
            isinstance(old, list) and len(old) == OLD_ROWS and
            isinstance(unresolved, list) and len(unresolved) == NEW_ROWS and
            isinstance(appended, list) and len(appended) == NEW_ROWS and
            extras.get("new_candidate_count") == NEW_ROWS and
            extras.get("early_certified_source_count") == OLD_ROWS and
            extras.get("unresolved_after_candidate_construction") == 0 and
            extras.get("subgroup") ==
            "intransitive V4 = {e,(01),(23),(01)(23)}" and
            all(extras.get("input_sha256", {}).get(path.name) ==
                EXPECTED_SHA[path]
                for path in (ORIGIN, EARLY, SAT_AUDIT, CORE, CERTIFIED_SUBSET)),
            "Old/new source certificate partition metadata mismatch")
    old_keys = {tuple(r["clause"]) for r in old}
    missing_keys = {tuple(r["clause"]) for r in unresolved}
    appended_keys = {tuple(r["clause"]) for r in appended}
    audited_keys = {tuple(r["clause"]) for r in
                    sat_audit.get("excluded_diagnostics", [])}
    require(len(old_keys) == OLD_ROWS and old_keys == set(subset) and
            len(missing_keys) == len(appended_keys) ==
            len(audited_keys) == NEW_ROWS and
            missing_keys == appended_keys == audited_keys and
            old_keys.isdisjoint(missing_keys) and
            old_keys | missing_keys == exact_core and
            sat_audit.get("excluded_source_clauses") == NEW_ROWS and
            sat_audit.get("excluded_violated") == 1 and
            sat_audit.get("excluded_satisfied") == 4,
            "Exact SAT/original-old-new core clause partition mismatch")
    for group in (old, unresolved, appended,
                  sat_audit["excluded_diagnostics"]):
        for item in group:
            key = tuple(item["clause"])
            require(key in mapped and source_identity(item) == mapped[key],
                    "Original H source identity differs in supplied manifests")

    audit_items = extra_audit.get("new_certified_source_factors")
    require(extra_audit.get("status") ==
            "ALL THREE INTRANSITIVE V4 NEW SOURCE EXTENSION AUDIT PHASES PASSED" and
            extra_audit.get("complete_core_source_partition") is True and
            extra_audit.get("new_source_witnesses_independently_audited") ==
            NEW_ROWS and
            extra_audit.get("previous_source_witnesses_independently_audited") ==
            OLD_ROWS and
            isinstance(audit_items, list) and len(audit_items) == NEW_ROWS and
            all(extra_audit.get("input_sha256", {}).get(path.name) ==
                EXPECTED_SHA[path]
                for path in (ORIGIN, EARLY, SAT_AUDIT, CORE,
                             CERTIFIED_SUBSET, DRAT, EXTRAS)),
            "Independent additional source audit report mismatch")
    certified_new = {(item["factor"],item["factor_length"],
                      item["original_zero_based_clause_index"],
                      item["factor_orbit_index"],tuple(item["clause"]))
                     for item in audit_items}
    constructed_new = {(item["factor"],item["factor_length"],
                        item["original_zero_based_clause_index"],
                        item["factor_orbit_index"],tuple(item["clause"]))
                       for item in appended}
    require(certified_new == constructed_new and
            len(certified_new) == NEW_ROWS,
            "Additional checker certified five different original sources")
    require(len(old)+len(appended) == CORE_ROWS,
            "Old plus new source witness list does not cover core")
    print("PHASE 2/4 PASSED: complete original source-factor/quotient identity")
    print(f"  Original clauses: {CORE_ROWS}, earlier witnesses {OLD_ROWS}, "
          f"new witnesses {NEW_ROWS}", flush=True)
    return old, appended, family

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
        require(1 <= length <= 40,
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


def normalize_source(record):
    pairs = record.get("source_to_normalized")
    require(isinstance(pairs, list) and
            all(isinstance(pair, list) and len(pair) == 2 and
                all(type(x) is str and len(x) == 1 for x in pair)
                for pair in pairs),
            f"Malformed source letter mapping: {record['factor']}")
    table = dict(pairs)
    require(len(table) == len(pairs) and
            len(set(table.values())) == len(table),
            "Source-to-normalized map not injective")
    kind = record["kind"]
    if kind == "hall":
        require(set(table) == set(record["factor"]) and
                set(table.values()) == set("012") and
                len(set(record["factor"])) == 3,
                "Invalid original three-letter Hall normalization")
    elif kind == "external-double-separator":
        require(len(table) == 4 and set(table) == set("0123") and
                set(table.values()) == set("0123") and
                len(set(record["factor"])) == 3,
                "External witness alphabet map must be four-letter bijection")
        missing = set("0123") - set(record["factor"])
        require(len(missing) == 1 and
                record.get("unused_original_symbol") == next(iter(missing)) and
                table[next(iter(missing))] == "3",
                "External witness did not map unused original letter to 3")
    else:
        require(len(table) == 4 and set(table) == set("0123") and
                set(table.values()) == set("0123") and
                len(set(record["factor"])) == 4,
                "Four-letter original witness normalization invalid")
        if kind == "expanded-padded-multi-separator":
            require(record.get("distinguished_original_symbol") in
                    record["factor"] and
                    table[record["distinguished_original_symbol"]] == "3",
                    "New expanded padding incorrectly chose separator")
    normalized = "".join(table[ch] for ch in record["factor"])
    require(normalized == record.get("normalized_factor"),
            "Original-to-normalized factor mapping incorrect")
    return normalized


def validate_witness(record, hall):
    kind = record["kind"]
    word = record["factor"]
    n = record["factor_length"]
    require(kind in KINDS and n in FAMILY and len(word) == n and
            squarefree(word),
            f"Invalid original source witness kind/factor {word}")
    normalized = normalize_source(record)
    witness = record.get("finite_witness")
    offset = record.get("offset")
    require(type(witness) is str and
            set(witness) <= set("0123") and
            type(offset) is int and
            0 <= offset <= len(witness)-n and
            witness[offset:offset+n] == normalized and
            squarefree(witness),
            f"Original source factor not embedded into finite squarefree word {word}")
    if kind == "hall":
        require(offset == 0 and witness == normalized and
                record.get("separator") is None and
                "3" not in witness and
                witness in hall[len(witness)],
                f"Hall-only source factor membership failed: {word}")
        return
    require(record.get("separator") == "3",
            f"Invalid distinguished separator for {word}")
    positions = [i for i, char in enumerate(witness) if char == "3"]
    require(positions, f"Missing distinguished separator for {word}")
    expected_positions = [
        offset+i for i,ch in enumerate(normalized) if ch == "3"]
    left = witness[:positions[0]]
    right = witness[positions[-1]+1:]
    require(left in hall.get(len(left), set()) and
            right in hall.get(len(right), set()),
            f"Exterior Hall-Thue finite-factor membership invalid: {word}")
    if kind == "external-double-separator":
        require(len(positions) == 2 and
                positions == [n, 2*n+1] and
                "3" not in normalized and
                len(witness) == 3*n+2 and
                offset == n+1 and
                record.get("first_separator_index") == n and
                record.get("last_separator_index") == 2*n+1 and
                record.get("separator_span") == n+1 and
                len(left) == len(right) == n and
                record.get("left_hall_factor") == left and
                record.get("right_hall_factor") == right and
                witness == left+"3"+normalized+"3"+right,
                f"External double separator geometry incorrect: {word}")
        return
    require(positions == expected_positions,
            f"Padding inserted unintended distinguished separators: {word}")
    if kind == "single-separator":
        require(len(positions) == 1 and
                offset == 0 and witness == normalized,
                f"Invalid single separator source: {word}")
        return
    require(len(positions) >= 2,
            f"Multiple separator witness has too few separators: {word}")
    d = positions[-1]-positions[0]
    require(len(left) >= d-1 and len(right) >= d-1,
            f"Finite-separator D-1 margins invalid: {word}")
    if kind == "multi-separator":
        require(offset == 0 and witness == normalized,
                f"Invalid unpadded multiple-separator witness: {word}")
    elif kind == "padded-multi-separator":
        require(offset > 0 or offset+n < len(witness),
                f"Earlier padded witness has no padding: {word}")
    elif kind == "expanded-padded-multi-separator":
        require(record.get("first_separator_index") == positions[0] and
                record.get("last_separator_index") == positions[-1] and
                record.get("separator_span") == d and
                record.get("left_hall_factor") == left and
                record.get("right_hall_factor") == right and
                (offset > 0 or offset+n < len(witness)),
                f"Expanded padding separator certificate metadata mismatch: {word}")
        added = record.get("additional_exterior_margin")
        require(type(added) is int and 0 <= added <= 8 and
                len(left) == max(d-1, normalized.index("3"))+added and
                len(right) ==
                max(d-1, n-1-normalized.rindex("3"))+added,
                f"Expanded Hall padding length/geometry mismatch: {word}")
    else:
        raise AssertionError(f"Unexpected finite witness kind: {kind}")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checker", type=Path, required=True,
                        help="independent DRAT-trim executable")
    parser.add_argument("--archive-dir", type=Path,
                        help="optional archive containing all pinned filenames")
    parser.add_argument("--report", type=Path,
                        help="new report path; must not already exist")
    args = parser.parse_args()
    start = perf_counter()
    report_path = args.report or DEFAULT_REPORT
    require(not report_path.exists() and not report_path.is_symlink(),
            f"Refusing to overwrite report: {report_path}")
    if args.archive_dir:
        mapped_paths = {src: args.archive_dir / src.name
                        for src in EXPECTED_SHA}
    else:
        mapped_paths = {src: src for src in EXPECTED_SHA}
    require(args.checker.is_file() and
            not args.checker.is_symlink() and
            args.checker.stat().st_mode & 0o111,
            "Independent DRAT checker absent, unsafe or not executable")
    for src, pin in EXPECTED_SHA.items():
        path = mapped_paths[src]
        require(path.is_file() and not path.is_symlink(),
                f"Missing / symlink archive or local proof artifact: {path}")
        got = hash_path(path)
        require(got == pin,
                f"SHA-256 mismatch {path}: got {got}, wanted {pin}")
        print("  SHA-PINNED:", path.name, got, flush=True)
    print("PHASE 1/4 PASSED: exact eight source/proof SHA-256 identities",
          flush=True)

    core = parse_dimacs(mapped_paths[CORE], CORE_ROWS)
    subset = parse_dimacs(mapped_paths[CERTIFIED_SUBSET], OLD_ROWS)
    ids, named = enumerate_orbit_ids()
    sources = json.loads(mapped_paths[ORIGIN].read_bytes())
    early = json.loads(mapped_paths[EARLY].read_bytes())
    extras = json.loads(mapped_paths[EXTRAS].read_bytes())
    extra_audit = json.loads(mapped_paths[EXTRA_AUDIT].read_bytes())
    sat_audit = json.loads(mapped_paths[SAT_AUDIT].read_bytes())
    old, new, family = validate_sources(
        sources, early, extras, extra_audit, sat_audit,
        core, subset, ids
    )

    lengths = {0}
    for rec in old + new:
        witness = rec["finite_witness"]
        separators = [i for i,c in enumerate(witness) if c == "3"]
        if separators:
            lengths.add(separators[0])
            lengths.add(len(witness)-separators[-1]-1)
        else:
            lengths.add(len(witness))
    hall = hall_catalog(lengths)
    kind_counts, family_counts = Counter(), Counter()
    for idx, rec in enumerate(old + new, 1):
        validate_witness(rec, hall)
        kind_counts[rec["kind"]] += 1
        family_counts[rec["factor_length"]] += 1
        if idx % 5000 == 0:
            print(f"  Independently checked full finite source witnesses: "
                  f"{idx}/{CORE_ROWS}", flush=True)
    require(kind_counts == Counter(KINDS) and
            family_counts == Counter(FAMILY) and
            sum(kind_counts.values()) == CORE_ROWS,
            f"Original extension witness census incomplete: {kind_counts}")
    print("PHASE 3/4 PASSED: ALL 26,819 original H finite source")
    print("  factors independently Hall-Thue/separator extendible")
    print("  Construction histogram:", dict(sorted(kind_counts.items())))
    print("  Source family counts:", dict(sorted(family_counts.items())),
          flush=True)

    drat = subprocess.run(
        [str(args.checker),str(mapped_paths[CORE]),str(mapped_paths[DRAT]),"-I"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, check=False, timeout=120
    )
    require(drat.returncode == 0,
            f"Standalone independent DRAT-trim failed exit {drat.returncode}: "
            f"{drat.stdout[-1600:]}")
    require(any(line.strip() == "s VERIFIED"
                for line in drat.stdout.splitlines()),
            "Standalone independent DRAT checker not s VERIFIED")
    for source, pin in EXPECTED_SHA.items():
        path = mapped_paths[source]
        require(hash_path(path) == pin,
                f"Input/proof mutated during integrated audit: {path.name}")
    print("PHASE 4/4 PASSED: independent standalone optimized DRAT proof")
    print("  on exactly the 26,819 source-certified H core clauses")
    print("  Checker exit:", drat.returncode)
    print("  Checker exact status: s VERIFIED")
    for row in drat.stdout.splitlines():
        if "clauses in core" in row or "resolution steps" in row:
            print(" ",row.strip())
    report = {
        "status": "ALL FOUR INTRANSITIVE V4 BI-INFINITE OBSTRUCTION AUDIT PHASES PASSED",
        "q":Q, "m":M, "r":R,
        "intransitive_v4_group": "{e,(01),(23),(01)(23)}",
        "marker_separation": "at least 3",
        "marker_domination": "within distance 2",
        "mathematical_inputs": [
            "classical squarefree uniformly recurrent Hall-Thue ternary fixed point",
            "finite-separator lemma with D-1 Hall-extendible ternary exterior margins",
        ],
        "sha256_inputs": {src.name: pin for src,pin in EXPECTED_SHA.items()},
        "original_named_n11_contexts": named,
        "intransitive_v4_context_orbit_variables": len(ids),
        "verified_original_core_clauses": CORE_ROWS,
        "verified_earlier_extension_witnesses": len(old),
        "verified_extra_extension_witnesses": len(new),
        "construction_histogram": dict(sorted(kind_counts.items())),
        "factor_length_histogram": dict(sorted(family_counts.items())),
        "independent_drat_checker_exit": drat.returncode,
        "independent_drat_status": "s VERIFIED",
        "fixed_parameter_theorem": (
            "No shared shift-equivariant radius-five Boolean marker rule "
            "on the bi-infinite quaternary squarefree subshift, with "
            "separation>=3 and domination<=2, is invariant under the "
            "intransitive Klein-four subgroup {e,(01),(23),(01)(23)}."
        ),
        "not_claimed": [
            "higher radius or arbitrary (q,m)",
            "non-H-invariant marker rules",
        ]
    }
    raw = (json.dumps(report, sort_keys=True, indent=2)+"\n").encode()
    with report_path.open("xb") as output:
        output.write(raw)
    print("ALL FOUR INTRANSITIVE V4 BI-INFINITE OBSTRUCTION AUDIT PHASES PASSED")
    print("COMPUTER-ASSISTED CONDITIONAL THEOREM:")
    print("  No q4,m3,r5 intransitive-V4-invariant shared radius-5")
    print("  marker rule exists on bi-infinite quaternary squarefree")
    print("  sequences with separation >=3 and domination <=2.")
    print("  (Assumes classical Hall-Thue + finite-separator lemma.)")
    print("  Integrated audit:",report_path)
    print("  Audit bytes:",len(raw))
    print("  Audit SHA-256:",sha256(raw).hexdigest())
    print(f"  Elapsed seconds: {perf_counter()-start:.2f}")
    print("No claim about arbitrary m or higher radii.")


if __name__ == "__main__":
    main()
