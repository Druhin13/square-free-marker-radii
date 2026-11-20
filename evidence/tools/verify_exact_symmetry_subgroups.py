#!/usr/bin/env python3
"""Independent enumeration of all 30 S4 subgroups for the proposed radii.

This only checks the finite group reduction; existence/nonexistence
of the five model/obstruction prototypes is certified separately.
"""
from __future__ import annotations
from itertools import permutations
import json

P = tuple(permutations(range(4)))
E = (0, 1, 2, 3)

def multiply(a,b):
    return tuple(a[b[i]] for i in range(4))

def inverse(g):
    return tuple(g.index(i) for i in range(4))

def subgroup(generators):
    G = set(generators) | {E}
    while True:
        expanded = G | {multiply(x,y) for x in G for y in G}
        if expanded == G:
            return frozenset(G)
        G = expanded

def conjugate(H,g):
    return frozenset(multiply(multiply(g,x),inverse(g)) for x in H)


def main():
    groups = {frozenset({E})}
    for p in P:
        for H in tuple(groups):
            groups.add(subgroup(H|{p}))
    assert len(groups) == 30
    A4 = subgroup({(1,2,0,3),(1,0,3,2)})
    S3 = subgroup({(1,2,0,3),(1,0,2,3)})
    V4i = subgroup({(1,0,2,3),(0,1,3,2)})
    C4 = subgroup({(1,2,3,0)})
    assert len(A4) == 12 and len(S3) == 6 and len(V4i) == 4 and len(C4) == 4
    classes = {5:[],6:[],7:[]}
    for H in groups:
        contains_c4 = any(conjugate(C4,g)<=H for g in P)
        if len(H) <= 2:
            radius = 5
        elif contains_c4:
            radius = 7
        else:
            radius = 6
            assert any(H <= conjugate(prototype,g)
                       for prototype in (A4,S3,V4i) for g in P), (
                           "Non-four-cycle subgroup misses all upper-bound prototypes",H)
        classes[radius].append(H)
    assert {r:len(v) for r,v in classes.items()} == {5:10,6:13,7:7}
    report={"status":"COMPLETE 30-SUBGROUP S4 REDUCTION PASSED",
            "subgroup_count":len(groups),
            "subgroups_by_exact_radius":{str(r):len(v) for r,v in classes.items()},
            "group_orders_by_exact_radius":{
                str(r):{str(order):sum(len(h)==order for h in v)
                        for order in sorted({len(h) for h in v})}
                for r,v in classes.items()},
            "mathematical_premises":["verified C4 radius-6 obstruction",
                "verified A4/S3/V4i radius-6 upper bounds",
                "verified S4 radius-7 upper bound",
                "original smaller-radius certificates"]}
    print(json.dumps(report,indent=2,sort_keys=True))
    return report

if __name__=='__main__':
    main()
