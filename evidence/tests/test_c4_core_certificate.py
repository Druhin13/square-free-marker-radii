"""Independent exhaustive propositional check of the 11-source C4 core."""
import itertools
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'proofs/m3/exact-symmetry/c4_radius6_core.json'

def squarefree(word):
    return all(word[i:i+p]!=word[i+p:i+2*p]
               for i in range(len(word))
               for p in range(1,(len(word)-i)//2+1))

class FourCycleCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(SOURCE.read_text('utf-8'))

    def test_sources_are_explicit_squarefree_factors(self):
        self.assertEqual(len(self.rows),11)
        for row in self.rows:
            word,extension=row['source'],row['Z']
            self.assertIn(len(word),(14,15,17))
            self.assertEqual(extension[row['offset']:row['offset']+len(word)],word)
            self.assertTrue(squarefree(word))
            self.assertTrue(squarefree(extension))
            self.assertGreaterEqual(row['offset'],0)
            self.assertIn(row['separator'],range(4))

    def test_core_uses_nine_variables_and_has_no_satisfying_assignment(self):
        clauses=[row['clause'] for row in self.rows]
        variables=set('ABCDEFGHI')
        self.assertEqual({lit.lstrip('-') for c in clauses for lit in c},variables)
        for clause in clauses:
            self.assertEqual(len(set(clause)),len(clause))
        for bits in itertools.product((False,True),repeat=9):
            assignment=dict(zip('ABCDEFGHI',bits))
            self.assertFalse(all(any(
                (not assignment[lit[1:]]) if lit.startswith('-')
                else assignment[lit] for lit in clause
            ) for clause in clauses))

if __name__=='__main__':unittest.main()
