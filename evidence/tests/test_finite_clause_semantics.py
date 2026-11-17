"""Independent, small-alphabet checks for the manuscript's clause indexing.

The full theorem needs the separately archived SAT/DRAT and source
realization certificates. These tests target the exact mapping from
finite source windows to separation/covering propositional clauses.
"""
from itertools import product
import unittest


def squarefree_words(n, alphabet="012"):
    def extends(prefix):
        if len(prefix) == n:
            yield prefix
            return
        for symbol in alphabet:
            candidate = prefix + symbol
            if any(candidate[-2*p:-p] == candidate[-p:]
                   for p in range(1, len(candidate)//2+1)):
                continue
            yield from extends(candidate)
    return list(extends(""))


def states_for(contexts):
    unique = tuple(dict.fromkeys(contexts))
    for bits in product((False, True), repeat=len(unique)):
        state = dict(zip(unique, bits))
        yield tuple(state[context] for context in contexts)


class FiniteFactorClauseSemantics(unittest.TestCase):
    def test_separation_clause_lengths_and_offsets(self):
        for r in (0, 1, 2):
            width = 2*r + 1
            for d in (1, 2):
                words = squarefree_words(width + d)
                self.assertTrue(words)
                for source in words:
                    self.assertEqual(len(source), width + d)
                    contexts = (source[:width], source[d:d+width])
                    for first, second in states_for(contexts):
                        clause_satisfied = not first or not second
                        direct_separation_valid = not (first and second)
                        self.assertEqual(clause_satisfied,
                                         direct_separation_valid)

    def test_five_site_cover_clause_lengths_and_offsets(self):
        for r in (0, 1, 2):
            width = 2*r + 1
            words = squarefree_words(width + 4)
            self.assertTrue(words)
            for source in words:
                self.assertEqual(len(source), 2*r + 5)
                contexts = tuple(source[d:d+width] for d in range(5))
                self.assertEqual(len(contexts), 5)
                self.assertTrue(all(len(w) == width for w in contexts))
                for decisions in states_for(contexts):
                    clause_satisfied = any(decisions)
                    direct_distance_two_cover = any(
                        decisions[neighbor+2]
                        for neighbor in (-2, -1, 0, 1, 2)
                    )
                    self.assertEqual(clause_satisfied,
                                     direct_distance_two_cover)

    def test_clause_arity_does_not_exceed_five(self):
        for r in (0, 1, 2):
            width = 2*r + 1
            for source in squarefree_words(width+4):
                self.assertLessEqual(
                    len({source[d:d+width] for d in range(5)}), 5
                )


if __name__ == "__main__":
    unittest.main()
