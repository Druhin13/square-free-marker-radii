"""Negative controls for the standalone archive packaging validator."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
from zipfile import ZipFile, ZipInfo

from tools.verify_distribution_archive import validate_archive


class ArchivePackagingTests(unittest.TestCase):
    def make_archive(self, path: Path, entries: dict[str, bytes],
                     *, duplicate: bool = False, symlink: bool = False):
        with ZipFile(path, "w") as archive:
            digest_lines = []
            for name, payload in entries.items():
                info = ZipInfo(name)
                info.create_system = 3
                info.external_attr = ((stat.S_IFLNK if symlink else stat.S_IFREG)
                                      | 0o644) << 16
                archive.writestr(info, payload)
                digest_lines.append(f"{sha256(payload).hexdigest()}  {name}")
            if duplicate:
                info = ZipInfo(next(iter(entries)))
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="Duplicate name:")
                    archive.writestr(info, b"duplicate")
            archive.writestr("SHA256SUMS", "\n".join(digest_lines) + "\n")

    def check_rejection(self, name: str, *, duplicate=False, symlink=False):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "candidate.zip"
            self.make_archive(path, {name: b"research data"},
                              duplicate=duplicate, symlink=symlink)
            with self.assertRaises(ValueError):
                validate_archive(path, expected_proofs=None, require_workflow=False)

    def test_valid_minimal_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "candidate.zip"
            self.make_archive(path, {"README.md": b"test"})
            report = validate_archive(path, expected_proofs=0, require_workflow=False)
            self.assertEqual(report["checksum_entries"], 1)

    def test_rejects_root_git_directory(self):
        self.check_rejection(".git/config")

    def test_rejects_nested_git_directory(self):
        self.check_rejection("evidence/.git/HEAD")

    def test_rejects_path_traversal(self):
        self.check_rejection("../README.md")

    def test_rejects_symlink(self):
        self.check_rejection("evidence/link", symlink=True)

    def test_rejects_duplicate_paths(self):
        self.check_rejection("README.md", duplicate=True)


if __name__ == "__main__":
    unittest.main()
