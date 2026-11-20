"""Check original ten-clause witnesses and independently recorded extensions."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'proofs/m3/s4-r6-full-tail-certificates/kbl-m3-r6-s4-ten-core-full-tail-completions.json'
CORE=ROOT/'proofs/m3/s4-r6-ten-core/core.cnf'

class SourceCertificateTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(DATA.read_text('utf-8'))
        rows=CORE.read_text('ascii').splitlines()
        assert rows[0]=='p cnf 25192 10'
        cls.clauses=[list(map(int,row.split()))[:-1] for row in rows[1:]]

    def test_one_to_one_original_core_sources(self):
        self.assertEqual(len(self.clauses),10)
        self.assertEqual(self.data['source_count'],10)
        certs=self.data['certificates']
        self.assertEqual(len(certs),10)
        self.assertEqual([x['source_number'] for x in certs],list(range(1,11)))
        for cert,clause in zip(certs,self.clauses):
            original=cert['original_core_clause']
            self.assertEqual(sorted(original),sorted(clause))
            self.assertEqual(len(original),len(set(original)))
            self.assertEqual(len(clause),len(set(clause)))

    def test_full_witnesses_cover_source_and_both_margins(self):
        self.assertEqual(self.data['replaced_right_padding_count'],6)
        for c in self.data['certificates']:
            word=c['original_source_word']
            witness=c['new_full_finite_squarefree_witness']
            zeros=[i for i,ch in enumerate(witness) if ch=='0']
            self.assertEqual(len(word),c['source_factor_length'])
            self.assertIn(word,witness)
            self.assertEqual(zeros,c['zero_positions_in_witness'])
            self.assertEqual(zeros[-1]-zeros[0],c['separator_span_D'])
            self.assertEqual(witness.split('0',1)[0],c['left_full_zero_free_extremity'])
            self.assertEqual(witness.rsplit('0',1)[-1],c['right_full_zero_free_extremity'])
            self.assertTrue(witness.endswith(c['corrected_right_padding']))
            self.assertGreaterEqual(zeros[0],c['separator_span_D']-1)
            self.assertGreaterEqual(len(witness)-1-zeros[-1],c['separator_span_D']-1)

if __name__=='__main__':unittest.main()
