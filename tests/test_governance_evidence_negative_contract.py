from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.collect_evidence_package import EvidenceError, parse_junit
from scripts.validate_evidence_registry import ContractError, validate_registry


class GovernanceEvidenceNegativeContractTests(unittest.TestCase):
    def test_unapproved_skips_fail_the_official_input(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            junit = Path(temporary) / "junit.xml"
            junit.write_text(
                '<testsuite tests="1"><testcase classname="contract" name="skipped">'
                "<skipped /></testcase></testsuite>",
                encoding="utf-8",
            )
            with self.assertRaises(EvidenceError):
                parse_junit(junit, set())

    def test_duplicate_ids_fail_without_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry.yaml"
            registry.write_text(
                "ids:\n  - id: REQ-F01-GOV-ID-REGISTRY\n"
                "  - id: REQ-F01-GOV-ID-REGISTRY\n",
                encoding="utf-8",
            )
            with self.assertRaises(ContractError):
                validate_registry(registry)


if __name__ == "__main__":
    unittest.main()
