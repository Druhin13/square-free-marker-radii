"""Guard the short four-cycle witness printed in the subgroup theorem.

This is an independent manuscript-to-certificate regression, not a
replacement for the Hall--Thue infinite-extension lemma or for the
original full four-cycle verifier.
"""
import re
import unittest
from pathlib import Path

from scripts import verify_m3_r5_s4_elementary_obstruction as original

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper/main.tex"
EXPECTED_G = str.maketrans("0123", "2031")


def printed_proof():
    manuscript = PAPER.read_text(encoding="utf-8")
    start = r"\begin{lemma}[A short four-cycle obstruction]"
    if manuscript.count(start) != 1:
        raise AssertionError("Missing/duplicated four-cycle lemma")
    remainder = manuscript.split(start, 1)[1]
    if remainder.count(r"\end{proof}") < 1:
        raise AssertionError("Missing four-cycle proof ending")
    return remainder.split(r"\end{proof}", 1)[0]


def squarefree(word):
    return all(
        word[i:i+p] != word[i+p:i+2*p]
        for i in range(len(word))
        for p in range(1, (len(word)-i)//2 + 1)
    )


class ManuscriptFourCycleWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = printed_proof()
        cls.words = dict(re.findall(
            r"\b([WZ])=\\texttt\{([0-3]+)\}", cls.source
        ))

    def test_printed_factors_match_original_immutable_verifier(self):
        self.assertEqual(self.words, {"W": original.W, "Z": original.Z})
        self.assertEqual((len(self.words["W"]), len(self.words["Z"])), (15, 23))
        self.assertTrue(squarefree(self.words["W"]))
        self.assertTrue(squarefree(self.words["Z"]))
        self.assertEqual(self.words["Z"][3:18], self.words["W"])

    def test_complete_separator_ends_and_margins(self):
        word = self.words["Z"]
        marks = [i for i, c in enumerate(word) if c == "3"]
        self.assertEqual(marks, [7, 10, 15])
        distance = marks[-1]-marks[0]
        self.assertEqual(distance, 8)
        self.assertEqual((len(word[:marks[0]]), len(word[marks[-1]+1:])),
                         (distance-1, distance-1))
        self.assertEqual(word[:marks[0]], "1210120")
        self.assertEqual(word[marks[-1]+1:], "2101202")

    def test_orbit_relation_and_printed_representatives(self):
        windows = [self.words["W"][i:i+11] for i in range(5)]
        self.assertEqual(len(windows), 5)
        self.assertEqual(windows[0], "01203213012")
        self.assertEqual(windows[1], "12032130120")
        for i in range(3):
            self.assertEqual(windows[i].translate(EXPECTED_G), windows[i+2])
        # The original certificate is a different implementation of
        # the same finite witness; preserve source/data agreement.
        self.assertEqual(windows[0], original.EXPECTED_A)

    def test_proof_text_names_both_first_windows(self):
        self.assertIn(r"\texttt{01203213012}", self.source)
        self.assertIn(r"\texttt{12032130120}", self.source)


if __name__ == "__main__":
    unittest.main()
