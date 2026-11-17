"""Check publication-facing metadata without implying a public release.

MSC codes are verified against official MSC2020 classifications.
The arXiv abstract metadata limit is 1,920 characters, so keep the
manuscript's abstract below that limit even before a submission.
"""
from pathlib import Path
import re
import unittest

TEX = (Path(__file__).resolve().parent.parent/"paper/main.tex").read_text(encoding="utf-8")


class PublicationMetadata(unittest.TestCase):
    def test_title_precise_and_release_unapproved(self):
        self.assertIn(
            r"\title{The Exact Locality Cost of Alphabet\\Symmetry in Square-Free Marker Rules}",
            TEX,
        )
        self.assertRegex(TEX, r"\\author\{\s*\}")
        self.assertIn("The source and proof archive\nis currently private", TEX)

    def test_abstract_within_arxiv_limit_and_exact_scope(self):
        abstracts = re.findall(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", TEX, re.S)
        self.assertEqual(len(abstracts), 1)
        self.assertLessEqual(len(abstracts[0].strip()), 1920)
        for phrase in (
            "least symmetric coding radius is five",
            "raises it to seven",
            "30 subgroups",
            "bi-infinite square-free sources",
            "extension",
            "independently checked",
            "exact",
            "fixed-parameter",
        ):
            self.assertIn(phrase, abstracts[0])

    def test_keywords_and_msc_classification(self):
        self.assertEqual(TEX.count(r"\textbf{Keywords.}"), 1)
        self.assertEqual(TEX.count(r"\textbf{2020 Mathematics Subject Classification.}"), 1)
        self.assertIn("Primary 37B10; Secondary 68R15, 68R07.", TEX)

    def test_certificates_pinned_not_falsely_available(self):
        self.assertIn(r"\texttt{artifacts/manifest.json}", TEX)
        self.assertIn(r"\path{artifacts/exact-symmetry-addendum-manifest.json}", TEX)
        self.assertIn(r"\texttt{59a7075f75b4}", TEX)
        self.assertIn("no assigned public archive DOI", TEX)
        self.assertIn("licensing review", TEX)

    def test_output_example_not_misrepresented_as_rule(self):
        self.assertIn(r"$\{8k,8k+3:k\in\mathbb Z\}$", TEX)
        self.assertIn("only an illustrative marker pattern", TEX)


if __name__ == "__main__":
    unittest.main()
