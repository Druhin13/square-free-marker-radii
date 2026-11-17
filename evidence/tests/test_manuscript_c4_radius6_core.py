"""Cross-check the printed eleven C4 radius-six clauses with pinned sources.

The table is human-readable but theorem-critical: a typo in a source
or signed clause must fail the manuscript CI. This regression checks
exact source and propositional content, independent from the source
realization, orbit reconstruction and exhaustive rule auditors.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper/main.tex"
SOURCE = ROOT / "proofs/m3/exact-symmetry/c4_radius6_core.json"

ROW = re.compile(
    r"^\s*(\d+)\s*&\s*\\texttt\{([0-3]+)\}\s*&\s*\$([^$]+)\$\\\\\s*$",
    re.MULTILINE,
)
NAME = re.compile(r"^[A-I]$")


def table_rows():
    paper = PAPER.read_text(encoding="utf-8")
    label = r"\label{tab:c4-core}"
    if paper.count(label) != 1:
        raise ValueError("Missing/duplicated C4 source-table label")
    start = r"\section{The eleven-source radius-six four-cycle core}"
    if paper.count(start) != 1:
        raise ValueError("Missing/duplicated C4 source appendix")
    section = paper.split(start, 1)[1].split(label, 1)[0]
    return ROW.findall(section)


def parse_clause(source):
    terms = []
    for token in source.split(r"\vee"):
        token = token.strip().replace(" ", "")
        negative = token.startswith(r"\neg")
        if negative:
            token = token[len(r"\neg"):]
        if not NAME.fullmatch(token):
            raise ValueError("Unexpected C4 literal: " + token)
        terms.append(("-" if negative else "") + token)
    if len(terms) != len(set(terms)):
        raise ValueError("Duplicate C4 literal in print")
    return terms


class ManuscriptC4Core(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = table_rows()
        cls.cert = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_all_eleven_rows_match_the_original_source_and_clauses(self):
        self.assertEqual(len(self.rows), 11)
        self.assertEqual(len(self.cert), 11)
        for ordinal, (printed, data) in enumerate(zip(self.rows, self.cert), 1):
            row_id, word, clause_source = printed
            self.assertEqual(int(row_id), ordinal)
            self.assertEqual(word, data["source"])
            self.assertEqual(set(parse_clause(clause_source)), set(data["clause"]))
            self.assertIn(len(word), (14, 15, 17))
            self.assertEqual(data["Z"][data["offset"]:data["offset"]+len(word)], word)

    def test_hand_checkable_contradiction_is_complete(self):
        clauses = [set(parse_clause(c)) for _, _, c in self.rows]
        for values in product((False, True), repeat=9):
            assignment = dict(zip("ABCDEFGHI", values))
            satisfied = all(any(
                (not assignment[term[1:]]) if term.startswith("-")
                else assignment[term]
                for term in clause
            ) for clause in clauses)
            self.assertFalse(satisfied, "Printed core must have no satisfying assignment")


if __name__ == "__main__":
    unittest.main()
