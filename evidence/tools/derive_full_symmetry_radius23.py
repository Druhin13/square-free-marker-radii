#!/usr/bin/env python3
"""Derived-radius-23 audit for the *original* full-S4 nine-color table.

This is an independent, separately identified mathematical dependency
calculation plus an actual-table sample-rule sanity check. The original
immutable coloring audit independently checks ALL finite source graph
edges; this tool DOES NOT re-check 627,159 conflicts nor mechanically
prove the rank-dependency lemma stated in the accompanying manuscript.

Outputs a local deterministic JSON verification report if --report is set.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLOR = ROOT / "proofs/m3/s4-L14-nine-color/square-free-marker-q4-m3-s4-L14-coloring.json"
AUDIT = ROOT / "proofs/m3/s4-L14-nine-color/square-free-marker-m3-s4-L14-coloring-audit.json"
COLOR_SHA = "ee755eff86ae9607037a1ee1a68322a73384cbc5e75b8d513a5ff2616747900d"
AUDIT_SHA = "e3ee9c81e8190ae537162ac58ffa5a51c30ae1a6a4393244d91a3c26d56c7370"
HALL = {"0":"012", "1":"02", "2":"1"}


def need(ok, msg):
    if not ok:
        raise AssertionError(msg)


def signature(path):
    need(path.is_file() and not path.is_symlink(), "Unsafe/missing source")
    return sha256(path.read_bytes()).hexdigest()


def square_suffix(word):
    return any(word[-2*p:-p] == word[-p:]
               for p in range(1,len(word)//2+1))


def canonical_word(word):
    seen = {}
    return "".join(str(seen.setdefault(ch,len(seen))) for ch in word)


def canonicals14():
    def extend(prefix,highest):
        if len(prefix) == 14:
            yield prefix
        else:
            for symbol in range(min(3,highest+1)+1):
                trial = prefix + str(symbol)
                if not square_suffix(trial):
                    yield from extend(trial,max(highest,symbol))
    yield from extend("0",0)


def hall_prefix(n=1200):
    word = "0"
    while len(word) < n:
        word = "".join(HALL[c] for c in word)
    return word[:n]


def evaluate_real_coloring(colors, indices):
    sample = hall_prefix()
    positions = tuple(range(6,len(sample)-7))
    labels = {
        i: colors[indices[canonical_word(sample[i-6:i+8])]]
        for i in positions
    }
    # Rank-by-rank marker selection, directly using the actual nine-color
    # certificate, not a synthetic modular color predicate.
    markers = set()
    for color in range(9):
        for i in positions:
            if labels[i] == color and not any(
                i+d in markers for d in (-2,-1,1,2)
            ):
                markers.add(i)
    chosen = sorted(markers)
    need(all(b-a>=3 for a,b in zip(chosen,chosen[1:])),
         "Actual color-table sample violates marker packing")
    for i in positions[2:-2]:
        need(any(i+d in markers for d in (-2,-1,0,1,2)),
             "Actual color-table sample violates marker covering")
    return {
        "ternary_hall_sample_symbols":len(sample),
        "available_length14_color_sites":len(positions),
        "sample_markers_selected":len(markers),
        "checked_interior_domination_sites":len(positions)-4,
        "verified_minimum_marker_spacing":min(
            (b-a for a,b in zip(chosen,chosen[1:])), default=None),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report",type=Path)
    args = parser.parse_args()
    need(signature(COLOR)==COLOR_SHA and signature(AUDIT)==AUDIT_SHA,
         "Immutable full-S4 coloring or independent original graph-audit pin mismatch")
    data = json.loads(COLOR.read_text("utf-8"))
    audited = json.loads(AUDIT.read_text("utf-8"))
    palette = data["vertex_colors_zero_based_lex_order"]
    need(isinstance(palette,list) and len(palette)==66047
         and set(palette)==set(range(9)) and
         dict(sorted(Counter(palette).items())) ==
             {int(k):v for k,v in data["color_histogram"].items()},
         "Original nine-color table/count mismatch")
    need(data["parameters"]["source_pattern_length"]==14
         and data["parameters"]["conflicts_at_source_displacements"]==[1,2]
         and audited["EVERY_source_conflict_color_inequality_checked"] is True
         and audited["proper_color_count"]==9
         and audited["unique_undirected_conflicts"]==627159,
         "Original independently checked graph-coloring premises mismatch")
    order = list(canonicals14())
    need(len(order)==66047 and len(set(order))==66047,
         "Independent lexical source order/census mismatch")
    indexed = {word:i for i,word in enumerate(order)}
    # The n14 window centered at i reads [i-6,i+7]. A rank can
    # descend at most eight times, each time moving at most two sites.
    # Therefore the composed Boolean marker decision reads [i-22,i+23].
    left,right = -6,7
    rounds = max(palette)
    max_move = max(data["parameters"]["conflicts_at_source_displacements"])
    footprint = [left-rounds*max_move,right+rounds*max_move]
    radius = max(-footprint[0],footprint[1])
    need((rounds,max_move,footprint,radius)==(8,2,[-22,23],23),
         "Derived color-rank radius geometry mismatch")
    sample = evaluate_real_coloring(palette,indexed)
    report = {
        "status":"DERIVED RADIUS-23 FOOTPRINT AND REAL NINE-COLOR SAMPLE VERIFIED",
        "original_coloring_sha256":COLOR_SHA,
        "original_independent_full_graph_audit_sha256":AUDIT_SHA,
        "certified_conflict_edges":627159,
        "color_classes":9,
        "input_length":14,
        "centered_input_offsets":[-6,7],
        "rank_decreasing_rounds":8,
        "maximum_position_jump_per_round":2,
        "derived_input_offsets":footprint,
        "symmetric_radius_upper_bound":radius,
        "original_audit_conservative_bound":audited[
            "conservative_valid_S4_symmetric_marker_radius_upper"],
        "actual_nine_color_model_sanity_check":sample,
        "caveat":"Properness is proved by pinned full graph audit; rank-dependency theorem is mathematical; sample is not a universal proof.",
    }
    raw=(json.dumps(report,indent=2,sort_keys=True)+"\n").encode()
    if args.report:
        need(args.report.parent.is_dir()
             and not args.report.exists() and not args.report.is_symlink(),
             "Unsafe/pre-existing derived report path")
        with args.report.open("xb") as f:
            f.write(raw)
        print("Derived audit SHA256:",sha256(raw).hexdigest())
    print(report["status"])
    print("Original graph bound:",report["original_audit_conservative_bound"])
    print("Derived centered-window symmetric radius:",radius)
    print("Source symbols required for marker at i: [i-22, i+23]")


if __name__ == "__main__":
    main()
