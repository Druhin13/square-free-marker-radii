#!/usr/bin/env python3
"""Step358: independently audit entire full-S4 L14 graph coloring certificate.

This stand-alone verifier DOES NOT import Step357 generator or Step348
preflight, and uses different (integer-tuples, recursive named-factor
DFS) original factor enumeration:

(1) Pin actual user-observed Step357 coloring+manifest SHA256s plus
    independently verified 2793-byte Step348 source theorem preflight.
(2) Enumerate ALL 1,585,128 originally NAMED squarefree length14
    factors to reconstruct the exact lexicographic original n14
    canonical S4 decision vertex indices, proving all 66,047 pattern
    orbits enumerated and each orbit consists of exactly 24 namings.
(3) Independently enumerate EVERY original S4-canonical squarefree
    source factor length15 (173,183) and length16 (453,998). For EACH
    length15 source check colors of n14 windows displaced by one differ;
    for EACH length16 source check displacement-two n14 window colors
    differ. Reconstruct exact undirected edge count, graph maximum
    degree, and edge source-row counts without generator adjacency.
(4) Recheck C used consecutive color IDs, exact color histogram,
    manifest metadata, unchanged source SHAs, and conservative
    radius bound 2*C+13. Then and ONLY THEN the standard greedy
    ordered-color MIS construction gives a valid full-S4-invariant
    bi-infinite squarefree marker rule with spacing>=3 and domination
    radius<=2 at that sufficient symmetric radius.

This certifies a constructive UPPER bound only; it says nothing about
the minimal possible radius, higher-radius obstructions, arbitrary m,
finite-file CDC or novelty.

Run only after Step357 and provide the TWO user-observed SHA256 pins:
  python3 -B -m scripts.audit_m3_s4_L14_conflict_graph_independent \
      --coloring-sha <SHA256> --manifest-sha <SHA256>

Save ONE exclusive report:
  /tmp/kbl-m3-s4-L14-coloring-audit.json

Step360 immutable replay after verified four-file Git archiving:
  python3 -B -m scripts.audit_m3_s4_L14_conflict_graph_independent \
      --coloring-sha bd45025e9d58523711e966664f2cc922f0566546a820184e98ce48e386701525 \
      --manifest-sha cd48e13fdcc4c5cb3380eea9715142c2d10617ce56439ee92e7d71a5f084ea14 \
      --archive-dir proofs/m3/s4-L14-nine-color \
      --report /tmp/kbl-m3-s4-L14-coloring-clean-proofSHA-audit.json

This optional mode pins all FOUR archived inputs (including the
independent original audit), then independently recomputes the exact
original deterministic 1440-byte report using ONLY archived input files.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = Path("/tmp/kbl-m3-r6-s4-orbit-preflight.json")
COLORING = ROOT / "experiments/m3/kbl-q4-m3-s4-L14-coloring.json"
MANIFEST = Path("/tmp/kbl-m3-s4-L14-coloring-export.json")
AUDIT = Path("/tmp/kbl-m3-s4-L14-coloring-audit.json")
PREFLIGHT_SHA = "d58cd38c36ceb8ee68461968f7995fb57bf21205a85205b39f18b01f488e2be0"

SOURCE = {14:66047, 15:173183, 16:453998}
NAMED14 = 1585128
VERTICES = SOURCE[14]


def assert_true(ok, message):
    if not ok:
        raise AssertionError(message)


def file_signature(path):
    hashvalue = sha256()
    nbytes = 0
    with path.open("rb") as source:
        while True:
            block = source.read(1 << 20)
            if not block:
                break
            nbytes += len(block)
            hashvalue.update(block)
    return hashvalue.hexdigest(), nbytes


def check_path(path, expected):
    assert_true(path.is_file() and not path.is_symlink(),
                f"Unsafe/missing source artifact: {path}")
    signature = file_signature(path)
    assert_true(signature[0] == expected,
                f"Source SHA256 mismatch: {path}, got {signature[0]}")
    return signature[1]


def newly_completed_square(word):
    """Integer-specific explicit index comparisons of all square periods."""
    n = len(word)
    for period in range(1, n//2 + 1):
        start = n - 2*period
        if all(word[start+j] == word[start+period+j]
               for j in range(period)):
            return True
    return False


def named_original_squarefree(n):
    """Independent recursive lexicographic DFS over named letters 0..3."""
    word = []
    def recurse():
        if len(word) == n:
            yield tuple(word)
            return
        for new in (0,1,2,3):
            word.append(new)
            if not newly_completed_square(word):
                yield from recurse()
            word.pop()
    yield from recurse()


def s4_pattern(word):
    """Canonical map with independent 4-element lookup table."""
    translated = [-1] * 4
    next_digit = 0
    norm = []
    for symbol in word:
        if translated[symbol] == -1:
            translated[symbol] = next_digit
            next_digit += 1
        norm.append(translated[symbol])
    return tuple(norm)


def canonical_original_factors(n):
    """Independent recursive RGS factor traversal, integer tuple form."""
    word = [0]
    def recurse(maximum):
        if len(word) == n:
            yield tuple(word)
            return
        for digit in range(min(3,maximum+1)+1):
            word.append(digit)
            if not newly_completed_square(word):
                yield from recurse(max(maximum, digit))
            word.pop()
    yield from recurse(0)


def verify_vertex_indices():
    ids = {}
    named_count=0
    for source in named_original_squarefree(14):
        named_count += 1
        if source == s4_pattern(source):
            assert_true(source not in ids,
                        "Canonical named source duplicated")
            ids[source] = len(ids)
    assert_true(named_count == NAMED14 and len(ids)==VERTICES and
                named_count == len(ids)*24,
                "Independent n14 named/canonical orbit counts incorrect")
    # Require a distinct factor-generation implementation to arrive
    # at precisely the same lexicographic vertex ordering.
    for ordinal, word in enumerate(canonical_original_factors(14)):
        assert_true(ids.get(word) == ordinal,
                    f"Canonical n14 original factor rank discrepancy {ordinal}")
    print("PHASE 1/4 PASSED: all 1,585,128 original named n14 words")
    print("  66,047 full-S4 orbit vertex IDs, exactly 24 names per orbit",
          flush=True)
    return ids


def verify_graph_edges(ids, color):
    edges=set()
    family_count={}
    for length,delta in ((15,1),(16,2)):
        count=0
        for source in canonical_original_factors(length):
            left = ids[s4_pattern(source[:14])]
            right = ids[s4_pattern(source[delta:delta+14])]
            assert_true(left != right,
                        f"Self-loop in independently generated source length {length}")
            assert_true(color[left] != color[right],
                        f"COLORING INVALID: length {length} "
                        f"source ordinal {count}, endpoints {left}/{right}, "
                        f"shared color {color[left]}")
            edges.add((min(left,right),max(left,right)))
            count += 1
        assert_true(count == SOURCE[length],
                    f"Original source factor census failed n{length}: {count}")
        family_count[str(length)] = count
        print(f"  ORIGINAL n{length}: {count} conflict sources, "
              "ALL endpoints properly colored", flush=True)
    deg = [0] * VERTICES
    for a,b in edges:
        deg[a] += 1
        deg[b] += 1
    print("PHASE 2/4 PASSED: exhaustive original S4 "
          "distance-one/two edge color audit", flush=True)
    return family_count, len(edges), max(deg)


def sha_argument(value):
    return len(value)==64 and all(ch in "0123456789abcdef" for ch in value)


def configure_archive_sources(directory_string, coloring_sha, manifest_sha):
    """Use ONLY four SHA-pinned archived inputs from a clean Git checkout."""
    global PREFLIGHT, COLORING, MANIFEST

    relative=Path(directory_string)
    assert_true(relative == Path("proofs/m3/s4-L14-nine-color"),
                "Archive mode requires canonical four-file proof path")
    folder=ROOT / relative
    assert_true(
        folder.is_dir() and not folder.is_symlink() and
        not (ROOT / "proofs").is_symlink() and
        not (ROOT / "proofs/m3").is_symlink(),
        "Missing/unsafe immutable coloring archive")
    expected={
        "kbl-m3-r6-s4-orbit-preflight.json":(PREFLIGHT_SHA,2793),
        "kbl-q4-m3-s4-L14-coloring.json":(coloring_sha,463685),
        "kbl-m3-s4-L14-coloring-export.json":(manifest_sha,665),
        "kbl-m3-s4-L14-coloring-audit.json":(
          "c0a0996a8c1a87db12fa42b1f188a18a85d5309cdc47c45a50d3180bb3e430de",1440),
    }
    assert_true({p.name for p in folder.iterdir()}==set(expected),
                "Unexpected files in four-file immutable coloring archive")
    for name,(expected_sha,size) in expected.items():
        path=folder/name
        assert_true(check_path(path,expected_sha)==size,
                    f"Immutable coloring source has wrong size: {name}")
    PREFLIGHT=folder/"kbl-m3-r6-s4-orbit-preflight.json"
    COLORING=folder/"kbl-q4-m3-s4-L14-coloring.json"
    MANIFEST=folder/"kbl-m3-s4-L14-coloring-export.json"
    print("ARCHIVE MODE: FOUR immutable original S4 coloring sources SHA PINNED")
    print("  Original independent audit SHA:",
          expected["kbl-m3-s4-L14-coloring-audit.json"][0],flush=True)


def main():
    global AUDIT
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument("--coloring-sha", required=True)
    args.add_argument("--manifest-sha", required=True)
    args.add_argument("--archive-dir", default=None,
                      help="Read only exact four-file immutable coloring archive")
    args.add_argument("--report", default=str(AUDIT),
                      help="New exclusive output audit report file")
    opts=args.parse_args()

    assert_true(sha_argument(opts.coloring_sha) and
                sha_argument(opts.manifest_sha),
                "Coloring/manifest SHA arguments must be exact lowercase SHA256")
    if opts.archive_dir is not None:
        configure_archive_sources(opts.archive_dir,
                                  opts.coloring_sha,opts.manifest_sha)
    AUDIT=Path(opts.report)
    assert_true(AUDIT.parent.is_dir() and not AUDIT.exists() and
                not AUDIT.is_symlink(),
                "Refusing missing-parent/overwrite/symlink independent audit output")
    started=perf_counter()
    print("STEP358 — INDEPENDENT COMPLETE S4 L14 CONFLICT GRAPH COLOR AUDIT",
          flush=True)

    source_size=check_path(PREFLIGHT,PREFLIGHT_SHA)
    assert_true(source_size==2793, "Step348 canonical source report byte count changed")
    coloring_bytes=check_path(COLORING,opts.coloring_sha)
    manifest_bytes=check_path(MANIFEST,opts.manifest_sha)

    data=json.loads(COLORING.read_bytes())
    manifest=json.loads(MANIFEST.read_bytes())
    assert_true(
        data["status"] ==
          "S4 LENGTH14 CONFLICT GRAPH COLORING CANDIDATE - INDEPENDENT AUDIT PENDING"
        and data["parameters"] == {
            "q":4, "m":3, "full_alphabet_group":"S4",
            "source_pattern_length":14,
            "conflicts_at_source_displacements":[1,2],
        }
        and data["preflight_sha256"] == PREFLIGHT_SHA
        and data["vertex_source_order"] ==
            "lexicographic first-appearance restricted-growth squarefree length14 factors"
        and data["original_canonical_source_counts"] ==
            {str(n):SOURCE[n] for n in (14,15,16)}
        and data["vertex_count"] == VERTICES,
        "Generator output metadata scope/census inconsistent")

    color=data["vertex_colors_zero_based_lex_order"]
    assert_true(type(color) is list and len(color)==VERTICES and
                all(type(c) is int and 0 <= c < VERTICES for c in color),
                "Malformed color assignment array")
    C=data["color_count"]
    assert_true(type(C) is int and C > 0 and
                set(color)==set(range(C)),
                "Wrong color_count or nonconsecutive color values")
    ids=verify_vertex_indices()
    family_count, edge_count, maxdegree=verify_graph_edges(ids,color)

    assert_true(
        data["edge_source_rows"] == family_count
        and data["unique_undirected_edges"] == edge_count
        and data["graph_max_degree"] == maxdegree,
        "Independent graph census does not match generator report")
    assert_true(data["color_histogram"] ==
                {str(k):v for k,v in sorted(Counter(color).items())},
                "Color population histogram mismatch")
    assert_true(data["chosen_algorithm"] in
                ("largest_degree_first","smallest_last") and
                data["algorithm_color_counts"][data["chosen_algorithm"]] == C
                and C == min(data["algorithm_color_counts"].values()),
                "Algorithm/number of colors metadata mismatch")
    assert_true(data["conservative_full_S4_marker_radius_upper_candidate"]
                == 2*C+13,
                "Derived conservative marker radius formula mismatch")
    print("PHASE 3/4 PASSED: independent exact color count,"
          " degree, histogram and conservative MIS radius formula",
          flush=True)

    assert_true(
        manifest == {
            "status":"STEP357 S4 GRAPH COLORING GENERATOR COMPLETE - EXTERNAL AUDIT PENDING",
            "coloring_relative_path":"experiments/m3/kbl-q4-m3-s4-L14-coloring.json",
            "coloring_sha256":opts.coloring_sha,
            "coloring_bytes":coloring_bytes,
            "preflight_sha256":PREFLIGHT_SHA,
            "vertices":VERTICES,
            "source_rows":family_count,
            "unique_edges":edge_count,
            "algorithm":data["chosen_algorithm"],
            "colors":C,
            "candidate_marker_radius_upper":2*C+13,
            "interpretation":"Generator result only; separate independent exhaustive audit required.",
        }, "Manifest does not exactly match independently recovered graph data")
    assert_true(check_path(PREFLIGHT,PREFLIGHT_SHA)==source_size and
                check_path(COLORING,opts.coloring_sha)==coloring_bytes and
                check_path(MANIFEST,opts.manifest_sha)==manifest_bytes,
                "Original graph source changed while auditing")
    print("PHASE 4/4 PASSED: exact source SHA pins and manifest unchanged",
          flush=True)

    report={
        "status":"INDEPENDENT S4 LENGTH14 CONFLICT COLORING FULL AUDIT 4/4 PASSED",
        "model":{"q":4,"m":3,"group":"S4","factor_length":14},
        "assumptions": (
            "L14 S4 orbit-period square obstruction; complete original "
            "n15/n16 squarefree source conflict enumeration; standard "
            "deterministic color-round maximal independent set."
        ),
        "original_source_preflight_sha256":PREFLIGHT_SHA,
        "coloring_sha256":opts.coloring_sha,
        "coloring_bytes":coloring_bytes,
        "generator_manifest_sha256":opts.manifest_sha,
        "generator_manifest_bytes":manifest_bytes,
        "original_named_squarefree_n14":NAMED14,
        "full_S4_n14_vertex_orbits":VERTICES,
        "original_source_orbits":family_count,
        "unique_undirected_conflicts":edge_count,
        "graph_max_degree":maxdegree,
        "proper_color_count":C,
        "conservative_valid_S4_symmetric_marker_radius_upper":2*C+13,
        "source_orbit_rows_verifiably_no_loops":True,
        "EVERY_source_conflict_color_inequality_checked":True,
        "conclusion": (
            "Verified proper full-S4-invariant coloring by C colors of "
            "all squarefree length14 factor orbits. Standard color-round "
            "greedy maximal independent set yields a radius at most "
            "2*C+13 marker rule on all bi-infinite quaternary squarefree "
            "words with separation>=3 and domination<=2. No novelty claimed."
        ),
    }
    raw=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode("ascii")
    with AUDIT.open("xb") as file:
        file.write(raw)
    assert_true(file_signature(AUDIT)==(sha256(raw).hexdigest(),len(raw)),
                "Exclusive audit report byte integrity changed")
    print("INDEPENDENT S4 LENGTH14 CONFLICT COLORING FULL AUDIT 4/4 PASSED")
    print("  S4 length14 factor vertex count:",VERTICES)
    print("  Independently verified original source rows:",family_count)
    print("  Independently verified undirected conflicts:",edge_count)
    print("  Independent proper colors:",C)
    print("  VERIFIED CONSTRUCTIVE S4 MARKER RADIUS r <=",2*C+13)
    print("  Audit:",AUDIT)
    print("  Audit bytes:",len(raw))
    print("  Audit SHA256:",sha256(raw).hexdigest())
    print(f"  Elapsed seconds: {perf_counter()-started:.2f}")
    print("This is an upper bound, not a radius-optimality theorem.")


if __name__=="__main__":
    main()
