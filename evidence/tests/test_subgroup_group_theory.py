"""Finite-group regression for the radius-five subgroup reduction.

These group-theoretic checks do not replace SAT models, bi-infinite
source-realization certificates, or standalone DRAT proofs.
"""
import itertools
import unittest

IDENTITY = (0, 1, 2, 3)
PERMS = tuple(itertools.permutations(range(4)))


def compose(a, b):
    return tuple(a[b[i]] for i in range(4))


def inverse(a):
    return tuple(a.index(i) for i in range(4))


def generated_subgroup(elements):
    group = set(elements) | {IDENTITY}
    while True:
        products = {compose(a, b) for a in group for b in group}
        if products.issubset(group):
            return frozenset(group)
        group.update(products)


def all_subgroups():
    groups = {frozenset({IDENTITY})}
    for p in PERMS:
        for group in list(groups):
            groups.add(generated_subgroup(set(group) | {p}))
    return groups


def order(p):
    product = IDENTITY
    for n in range(1, 25):
        product = compose(product, p)
        if product == IDENTITY:
            return n
    raise AssertionError("Expected an element of S4")


def conjugate(group, p):
    q = inverse(p)
    return frozenset(compose(compose(p, g), q) for g in group)


class GroupStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = all_subgroups()
        normal = generated_subgroup({(1, 0, 3, 2), (2, 3, 0, 1)})
        intransitive = generated_subgroup({(1, 0, 2, 3), (0, 1, 3, 2)})
        cls.v4_conjugates = {
            conjugate(group, p)
            for group in (normal, intransitive) for p in PERMS
        }

    def test_exact_subgroup_census(self):
        self.assertEqual(len(PERMS), 24)
        self.assertEqual(len(self.groups), 30)
        counts = {n: sum(len(g) == n for g in self.groups)
                  for n in (1, 2, 3, 4, 6, 8, 12, 24)}
        self.assertEqual(counts, {
            1: 1, 2: 9, 3: 4, 4: 7, 6: 4, 8: 3, 12: 1, 24: 1
        })

    def test_all_klein_four_conjugates_included(self):
        self.assertEqual(len(self.v4_conjugates), 4)
        self.assertTrue(self.v4_conjugates.issubset(self.groups))

    def test_larger_groups_contain_known_obstructions(self):
        for g in self.groups:
            if len(g) <= 2:
                continue
            has_3_or_4 = any(order(p) in (3, 4) for p in g)
            has_v4 = any(v.issubset(g) for v in self.v4_conjugates)
            self.assertTrue(has_3_or_4 or has_v4, g)

    def test_single_involutions_are_nine_order_two_groups(self):
        order_two = [g for g in self.groups if len(g) == 2]
        self.assertEqual(len(order_two), 9)
        nonidentity = [next(iter(g - {IDENTITY})) for g in order_two]
        self.assertEqual(sum(sum(p[i] != i for i in range(4)) == 2
                             for p in nonidentity), 6)
        self.assertEqual(sum(sum(p[i] != i for i in range(4)) == 4
                             for p in nonidentity), 3)


if __name__ == "__main__":
    unittest.main()
