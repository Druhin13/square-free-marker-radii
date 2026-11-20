"""Ensure the distributed evidence tree contains only research-facing material."""
from __future__ import annotations
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
PROOFS = ROOT / "proofs"

# These are publication-process markers, not technical terms such as
# pending DFS queues, source extension checks, or mathematical provenance.
UNPUBLISHED = re.compile(
    r"(?i)(?:step[0-9]{2,}|(?:independent|external) audit pending|"
    r"private (?:branch|ci|review|repo)|publication repair|"
    r"not yet (?:public|released)|worktree)"
)


class PublicDistributionSurface(unittest.TestCase):
    def test_no_staging_or_document_workflow_directories(self):
        for path in (
            ROOT / ".github", ROOT / "paper", ROOT / "preprint",
            ROOT / "review", ROOT / "release_drafts",
            ROOT / ".git", REPO / "paper", REPO / "preprint",
            REPO / "review", REPO / "release_drafts",
        ):
            with self.subTest(path=path):
                self.assertFalse(path.exists() or path.is_symlink())
        self.assertEqual(
            sorted(p.name for p in (REPO / ".github/workflows").iterdir()),
            ["verify-evidence.yml"],
        )

    def test_certificate_metadata_is_free_of_publication_process_markers(self):
        proof_json = sorted(PROOFS.rglob("*.json"))
        self.assertGreater(len(proof_json), 15)
        for path in proof_json:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.is_symlink())
                content = path.read_text("utf-8")
                self.assertIsNone(UNPUBLISHED.search(content))
                self.assertNotIn("s4-r6-full-tail-repair", str(path))

    def test_unrelated_terminology_is_absent_from_sources_and_certificates(self):
        unrelated = re.compile(r"(?i)\bCDC\b|edit[- ]locality|edit-churn|publication novelty")
        for folder, glob in ((PROOFS, "*.json"), (ROOT / "scripts", "*.py")):
            for path in folder.rglob(glob):
                with self.subTest(path=path.relative_to(ROOT)):
                    self.assertIsNone(unrelated.search(path.read_text("utf-8")))
        for filename in ("replay_c03_positive_generation.py",
                         "replay_c03_unrestricted_r5_generation.py"):
            content = (ROOT / "scripts" / filename).read_text("utf-8")
            self.assertNotIn('"public_release"', content)
            self.assertNotIn('"public_release_or_submission"', content)

    def test_standalone_radius_four_auditors_use_distributed_inputs(self):
        from scripts import audit_m3_r4_easy_core_independent as easy
        from scripts import audit_m3_r4_remaining_core_independent as remaining
        for path in (easy.SOURCE_CORE, easy.SUB_CNF, easy.WITNESSES,
                     remaining.CORE, remaining.EASY, remaining.MANIFEST):
            with self.subTest(path=path):
                self.assertTrue(path.is_file() and not path.is_symlink())
                self.assertTrue(path.is_relative_to(ROOT / "proofs"))

    def test_no_dangling_document_reference_or_branch_status(self):
        for folder in (ROOT / "scripts", ROOT / "tools", PROOFS):
            for path in folder.rglob("*"):
                if path.suffix not in (".py", ".json"):
                    continue
                with self.subTest(path=path.relative_to(ROOT)):
                    body = path.read_text("utf-8")
                    self.assertNotIn("docs/theory", body)
                    self.assertNotIn("research-branch", body)
        licenses = (REPO / "LICENSE.md").read_text("utf-8")
        third_party = (REPO / "THIRD_PARTY_NOTICES.md").read_text("utf-8")
        self.assertIn("`LICENSE-MIT.txt`", licenses)
        self.assertIn("Nathan Wetzler", third_party)

    def test_verifier_defaults_do_not_point_to_unshipped_experiments(self):
        for path in (ROOT / "scripts").glob("*.py"):
            with self.subTest(path=path.name):
                source = path.read_text("utf-8")
                self.assertNotIn('ROOT / "experiments/m3/', source)
                self.assertNotIn('ROOT/"experiments/m3/', source)

    def test_public_guides_have_no_staging_or_placeholder_language(self):
        for name in ("README.md", "REPRODUCING.md", "PROVENANCE.md", "LICENSE.md"):
            with self.subTest(name=name):
                content = (REPO / name).read_text("utf-8")
                self.assertIsNone(UNPUBLISHED.search(content))
                self.assertNotRegex(content, r"(?i)\b(?:TBD|FIXME|TODO)\b")


if __name__ == "__main__":
    unittest.main()
