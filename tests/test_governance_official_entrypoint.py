from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.collect_official_evidence_package import clean_worktree


class OfficialEvidenceEntrypointTests(unittest.TestCase):
    def test_dirty_worktree_is_not_eligible_for_official_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            dirty = subprocess.CompletedProcess(
                args=["git", "status", "--porcelain"], returncode=0, stdout=" M src/example.py\n", stderr=""
            )
            with patch("scripts.collect_official_evidence_package.subprocess.run", return_value=dirty):
                self.assertFalse(clean_worktree(workspace))

    def test_clean_worktree_is_eligible_for_official_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            clean = subprocess.CompletedProcess(
                args=["git", "status", "--porcelain"], returncode=0, stdout="", stderr=""
            )
            with patch("scripts.collect_official_evidence_package.subprocess.run", return_value=clean):
                self.assertTrue(clean_worktree(workspace))


if __name__ == "__main__":
    unittest.main()
