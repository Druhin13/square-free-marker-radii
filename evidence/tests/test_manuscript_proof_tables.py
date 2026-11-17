"""Cross-check the *printed* source-witness tables against immutable proof data.

This is a manuscript/regression audit, not a replacement for the
independently run finite-to-infinite source verifiers.
"""
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/"proofs/m3/s4-r6-full-tail-repair/kbl-m3-r6-s4-ten-core-full-tail-repair.json"
CORE=ROOT/"proofs/m3/s4-r6-ten-core/core.cnf"
PAPER=ROOT/"paper/main.tex"

SOURCE_ROW=re.compile(
    r"^\s*(\d+)\s*&\s*(\d+)\s*&\s*\\texttt\{([0-3]+)\}\\\\\s*$",
    re.MULTILINE,
)
PADDING_ROW=re.compile(
    r"^\s*(\d+)\s*&\s*\\texttt\{([1-3]+)\}\s*&\s*\\texttt\{([1-3]+)\}\\\\\s*$",
    re.MULTILINE,
)


def manuscript_tables():
    source=PAPER.read_text(encoding="utf-8")
    appendix=source.split("\\appendix",1)
    if len(appendix)!=2:
        raise ValueError("Missing unique manuscript appendix")
    if appendix[1].count("\\label{tab:sources}")!=1:
        raise ValueError("Source table anchor missing or repeated")
    if appendix[1].count("\\label{tab:pads}")!=1:
        raise ValueError("Padding table anchor missing or repeated")
    first,rest=appendix[1].split("\\label{tab:sources}",1)
    _unused,second=rest.split("\\label{tab:pads}",1)
    return SOURCE_ROW.findall(first),PADDING_ROW.findall(_unused)


def signed_core():
    lines=CORE.read_text(encoding="ascii").splitlines()
    if lines[0]!="p cnf 25192 10":
        raise ValueError("Unexpected original reduced core header")
    return [list(map(int,row.split()))[:-1] for row in lines[1:]]


class ManuscriptSourceTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.source_rows,cls.pad_rows=manuscript_tables()

    def test_exact_ten_original_source_words_and_separator_distances(self):
        self.assertEqual(len(self.source_rows),10)
        self.assertEqual(
            [int(row[0]) for row in self.source_rows],
            list(range(1,11)),
        )
        expected=[
            (str(c["source_number"]),str(c["separator_span_D"]),
             c["original_source_word"])
            for c in self.data["certificates"]
        ]
        self.assertEqual(self.source_rows,expected)

    def test_all_twenty_printed_appendices_match_completed_witnesses(self):
        self.assertEqual(len(self.pad_rows),10)
        self.assertEqual(
            [int(row[0]) for row in self.pad_rows],
            list(range(1,11)),
        )
        for row,certificate in zip(self.pad_rows,self.data["certificates"]):
            number,left,right=row
            source=certificate["original_source_word"]
            witness=certificate["new_full_finite_squarefree_witness"]
            self.assertEqual(number,str(certificate["source_number"]))
            self.assertTrue(witness.startswith(left+source))
            self.assertEqual(witness,left+source+right)
            self.assertEqual(right,certificate["corrected_right_padding"])
            # The *whole* exterior, not only the appended padding,
            # is what the mathematical extension lemma actually needs.
            self.assertEqual(
                witness.split("0",1)[0],
                certificate["left_full_zero_free_extremity"],
            )
            self.assertEqual(
                witness.rsplit("0",1)[-1],
                certificate["right_full_zero_free_extremity"],
            )

    def test_original_propositional_core_clause_identity(self):
        clauses=signed_core()
        self.assertEqual(len(clauses),10)
        # DIMACS disjunctions are independent of literal ordering.
        # Keep the exact ORIGINAL source-clause row and signed literal
        # multiset identity; do not allow source-row reordering or
        # duplicate literal deletion to hide a mismatch.
        certified=[
            c["original_core_clause"] for c in self.data["certificates"]
        ]
        self.assertEqual(
            [tuple(sorted(row)) for row in certified],
            [tuple(sorted(row)) for row in clauses],
        )
        for row in certified + clauses:
            self.assertEqual(len(row),len(set(row)))

    def test_all_repaired_witness_source_sizes(self):
        self.assertEqual(self.data["source_count"],10)
        self.assertEqual(self.data["replaced_right_padding_count"],6)
        for c in self.data["certificates"]:
            word=c["original_source_word"]
            self.assertEqual(len(word),c["source_factor_length"])
            zeros=[i for i,ch in enumerate(
                c["new_full_finite_squarefree_witness"]
            ) if ch=="0"]
            self.assertEqual(zeros,c["zero_positions_in_witness"])
            self.assertEqual(
                zeros[-1]-zeros[0],
                c["separator_span_D"],
            )
            self.assertGreaterEqual(
                zeros[0],
                c["separator_span_D"]-1,
            )
            self.assertGreaterEqual(
                len(c["new_full_finite_squarefree_witness"])-1-zeros[-1],
                c["separator_span_D"]-1,
            )


if __name__=="__main__":
    unittest.main()
