#!/usr/bin/env python3
"""Construct an S4-invariant factor coloring and radius bound.

Construct the ORIGINAL full finite-squarefree length14 equality-pattern
conflict graph under alphabet-renaming S4. Vertices: all 66,047
restricted-growth squarefree length14 factors (lex order). For EACH
canonical length15 source add the undirected edge between its two
length14 windows separated by 1; for EACH canonical length16 source
add the edge between its two length14 windows separated by 2.

All S4 original sources are covered by the canonical factors. The
previous independently verified L14 orbit-period lemma proves no edge
is a loop on ANY squarefree input. Finite over-approximation is safe
for upper bounds, even when a finite factor fails bi-infinite
extension. Count duplicate source edges but retain every source family
row in the independent auditor.

Try deterministic largest-degree-first AND smallest-last/degeneracy
greedy colorings, choose the lower color count (ties prefer first).
A proper C-coloring makes S4-invariant length14 factor labels a
distance-two proper coloring of every bi-infinite squarefree word.
Selecting a maximal independent subset of the distance-two path by
ordered color rounds gives markers at gaps [3,5] using conservative
symmetric radius r <= 2*C+13. This is a standard construction, not a
novel greedy-coloring theorem.

This generator is NOT independent proof verification. A separate
auditor MUST reconstruct the 66,047 vertex indices and check EVERY
n15/n16 original source conflict before promoting ANY numeric bound.

The published coloring and its independent audit are included under
proofs/m3/s4-L14-nine-color/. To reproduce the independent graph check,
run tools/run_verification.py --quick from evidence/. This optional
coloring generator requires separate source preflight and output paths;
its original generation defaults are not part of the distributed archive.
"""
from collections import Counter
from hashlib import sha256
import heapq
import json
import os
from pathlib import Path
import tempfile
from time import perf_counter

ROOT = Path(__file__).resolve().parent.parent
PREFLIGHT = Path("/tmp/kbl-m3-r6-s4-orbit-preflight.json")
PRE_SHA = "d58cd38c36ceb8ee68461968f7995fb57bf21205a85205b39f18b01f488e2be0"
COLORING = ROOT / ".build/kbl-q4-m3-s4-L14-coloring.json"
MANIFEST = Path("/tmp/kbl-m3-s4-L14-coloring-export.json")
COUNTS = {14: 66047, 15: 173183, 16: 453998}
N = COUNTS[14]


def need(flag, why):
    if not flag:
        raise AssertionError(why)


def sha_file(path):
    digest = sha256()
    with path.open("rb") as reader:
        for data in iter(lambda: reader.read(1 << 20), b""):
            digest.update(data)
    return digest.hexdigest()


def creates_square(word):
    n = len(word)
    for p in range(1, n // 2 + 1):
        if word[-2*p:-p] == word[-p:]:
            return True
    return False


def canonical_sources(length):
    """Direct lex DFS in restricted-growth orbit normal form."""
    stack = [("0", 0)]
    while stack:
        word, maximum = stack.pop()
        if len(word) == length:
            yield word
            continue
        for digit in range(min(3, maximum+1), -1, -1):
            expanded = word + str(digit)
            if not creates_square(expanded):
                stack.append((expanded, max(maximum, digit)))


def canonical(word):
    mapping = {}
    normalized = []
    for ch in word:
        if ch not in mapping:
            mapping[ch] = str(len(mapping))
        normalized.append(mapping[ch])
    return "".join(normalized)


def greedy_color(adjacency, sequence):
    color = [-1] * N
    largest = -1
    for vertex in sequence:
        used = {color[neighbor] for neighbor in adjacency[vertex]
                if color[neighbor] >= 0}
        proposed = 0
        while proposed in used:
            proposed += 1
        color[vertex] = proposed
        if proposed > largest:
            largest = proposed
    need(all(c >= 0 for c in color), "Greedy failed to assign every vertex")
    return color, largest + 1


def smallest_last_order(adjacency):
    """Deterministic exact smallest-current-degree graph removal."""
    degree = [len(row) for row in adjacency]
    heap = [(degree[v], v) for v in range(N)]
    heapq.heapify(heap)
    active = bytearray(b"\x01") * N
    removed = []
    maximum_removal_degree = 0
    while len(removed) < N:
        current_degree, vertex = heapq.heappop(heap)
        if not active[vertex] or current_degree != degree[vertex]:
            continue
        active[vertex] = 0
        removed.append(vertex)
        maximum_removal_degree = max(maximum_removal_degree, current_degree)
        for neighbor in adjacency[vertex]:
            if active[neighbor]:
                degree[neighbor] -= 1
                heapq.heappush(heap, (degree[neighbor], neighbor))
    return reversed(removed), maximum_removal_degree


def exclusive_write(path, payload):
    """Write immutable new file via temporary and exclusive link."""
    need(path.parent.is_dir(), f"Missing output directory: {path.parent}")
    need(not path.exists() and not path.is_symlink(),
         f"Refusing overwrite/symlink of output: {path}")
    descriptor, temp = tempfile.mkstemp(
        prefix=".pending-s4-color-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as writer:
            writer.write(payload)
        need(sha_file(Path(temp)) == sha256(payload).hexdigest() and
             Path(temp).stat().st_size == len(payload),
             "Temporary output integrity mismatch")
        os.link(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    need(path.is_file() and not path.is_symlink() and
         path.stat().st_size == len(payload) and
         sha_file(path) == sha256(payload).hexdigest(),
         "Final exclusive output integrity mismatch")


def main():
    began = perf_counter()
    print("FULL S4 LENGTH14 CONFLICT-GRAPH COLORING PRE-FLIGHT",
          flush=True)
    need(PREFLIGHT.is_file() and not PREFLIGHT.is_symlink() and
         sha_file(PREFLIGHT) == PRE_SHA,
         "Orbit-period preflight SHA mismatch")
    need(COLORING.parent.is_dir() and not COLORING.parent.is_symlink(),
         "Missing/unsafe existing experiments/m3 directory")
    need(not COLORING.exists() and not COLORING.is_symlink() and
         not MANIFEST.exists() and not MANIFEST.is_symlink(),
         "New candidate coloring or manifest already exists")

    factors = list(canonical_sources(14))
    need(len(factors) == N and
         all(x == canonical(x) for x in factors) and
         len(set(factors)) == N, "Original n14 S4 factor census mismatch")
    ids = {word: i for i, word in enumerate(factors)}
    print("PHASE 1/3 PASSED: all 66,047 canonical S4 "
          "length14 squarefree vertex patterns", flush=True)

    adjacency = [set() for _ in range(N)]
    source_rows = {}
    total_nonloop = 0
    for length, jump in ((15, 1), (16, 2)):
        original_count = 0
        for source in canonical_sources(length):
            a = ids[canonical(source[:14])]
            b = ids[canonical(source[jump:jump+14])]
            need(a != b,
                 f"L14 orbit-color collision at source length {length}: "
                 f"{source}")
            adjacency[a].add(b)
            adjacency[b].add(a)
            original_count += 1
        need(original_count == COUNTS[length],
             f"n{length} original canonical source census mismatch")
        total_nonloop += original_count
        source_rows[str(length)] = original_count
        print(f"  n{length}: {original_count} original source orbit rows",
              flush=True)

    edge_count = sum(map(len, adjacency)) // 2
    need(sum(map(len, adjacency)) == 2*edge_count and edge_count > 0,
         "Malformed undirected S4 conflict graph")
    degrees = [len(row) for row in adjacency]
    print("PHASE 2/3 PASSED: all original n15/n16 source conflicts inserted")
    print("  Undirected distinct edges:", edge_count)
    print("  Max degree:", max(degrees),
          "original source rows:", total_nonloop, flush=True)

    largest_order = sorted(range(N), key=lambda v: (-degrees[v], v))
    largest_colors, largest_count = greedy_color(adjacency, largest_order)
    smallest_order, degeneracy = smallest_last_order(adjacency)
    smallest_colors, smallest_count = greedy_color(adjacency, smallest_order)

    candidates = (
        ("largest_degree_first", largest_colors, largest_count),
        ("smallest_last", smallest_colors, smallest_count),
    )
    choice, colors, C = min(candidates, key=lambda x: x[2])
    need(all(colors[v] != colors[w]
             for v in range(N) for w in adjacency[v]),
         "Own coloring generator failed explicit proper-coloring check")
    need(set(colors) == set(range(C)),
         "Chosen coloring has unused or sparse color identifiers")
    conservative_r = 2*C+13
    print("PHASE 3/3 PASSED: original graph proper-coloring sanity checked")
    print("  Largest degree first C:", largest_count)
    print("  Smallest last C:", smallest_count,
          "degeneracy:", degeneracy)
    print("  Chosen algorithm:", choice, "colors:", C)
    print("  CONSERVATIVE RADIUS BOUND CANDIDATE r <=", conservative_r,
          flush=True)

    payload = {
        "status": "S4 LENGTH14 CONFLICT GRAPH COLORING ASSIGNMENT",
        "parameters": {
            "q": 4, "m": 3, "full_alphabet_group": "S4",
            "source_pattern_length": 14,
            "conflicts_at_source_displacements": [1, 2],
        },
        "preflight_sha256": PRE_SHA,
        "original_canonical_source_counts":
            {str(length): COUNTS[length] for length in (14, 15, 16)},
        "vertex_source_order": "lexicographic first-appearance restricted-growth squarefree length14 factors",
        "vertex_count": N,
        "edge_source_rows": source_rows,
        "unique_undirected_edges": edge_count,
        "graph_max_degree": max(degrees),
        "graph_degeneracy": degeneracy,
        "algorithm_color_counts": {
            "largest_degree_first": largest_count,
            "smallest_last": smallest_count,
        },
        "chosen_algorithm": choice,
        "color_count": C,
        "color_histogram": {
            str(k): v for k,v in sorted(Counter(colors).items())
        },
        "conservative_full_S4_marker_radius_upper_candidate": conservative_r,
        "vertex_colors_zero_based_lex_order": colors,
        "claim_limit": (
            "This color table is validated by an independent enumeration of "
            "source factors and conflict edges; the coloring method is "
            "a standard greedy construction."
        ),
    }
    raw = (json.dumps(payload, sort_keys=True, indent=2)+"\n").encode("ascii")
    exclusive_write(COLORING, raw)

    manifest = {
        "status": "S4 LENGTH14 COLORING CONSTRUCTION DATA",
        "coloring_relative_path": str(COLORING.relative_to(ROOT)),
        "coloring_sha256": sha256(raw).hexdigest(),
        "coloring_bytes": len(raw),
        "preflight_sha256": PRE_SHA,
        "vertices": N,
        "source_rows": source_rows,
        "unique_edges": edge_count,
        "algorithm": choice,
        "colors": C,
        "candidate_marker_radius_upper": conservative_r,
        "interpretation": "Constructed coloring data; correctness is independently checked by the exhaustive graph verifier.",
    }
    encoded = (json.dumps(manifest, sort_keys=True, indent=2)+"\n").encode()
    exclusive_write(MANIFEST, encoded)

    print("CANDIDATE GENERATED; RADIUS IMPROVEMENT REQUIRES INDEPENDENT VERIFICATION")
    print("  Coloring:", COLORING.relative_to(ROOT))
    print("  Coloring bytes:", len(raw))
    print("  Coloring SHA-256:", sha256(raw).hexdigest())
    print("  Manifest:", MANIFEST)
    print("  Manifest bytes:", len(encoded))
    print("  Manifest SHA-256:", sha256(encoded).hexdigest())
    print("  Vertex count:", N, "edge count:", edge_count)
    print("  Proper colors (generator only):", C)
    print("  Candidate r_S4(4,3) <=", conservative_r)
    print(f"  Elapsed seconds: {perf_counter()-began:.2f}")
    print("  Next: independent n15/n16 original factor conflict audit.")


if __name__ == "__main__":
    main()
