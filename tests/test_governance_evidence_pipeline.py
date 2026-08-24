from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.collect_evidence_package import run as collect_run
from scripts.validate_evidence_registry import ContractError, validate_document_index, validate_registry


class GovernanceEvidencePipelineTests(unittest.TestCase):
    def test_canonical_registry_and_document_index(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        registry = workspace / "docs" / "REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml"
        index = workspace / "docs" / "INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md"
        self.assertEqual(validate_registry(registry)["status"], "PASS")
        self.assertEqual(validate_document_index(index, workspace)["status"], "PASS")

    def test_duplicate_declared_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry.yaml"
            registry.write_text(
                "ids:\n  - id: MOD-RENDER-CORE\n  - id: MOD-RENDER-CORE\n",
                encoding="utf-8",
            )
            with self.assertRaises(ContractError):
                validate_registry(registry)

    def test_official_package_is_created_from_canonical_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            source = workspace / "source"
            source.mkdir()
            registry = source / "registry.yaml"
            registry.write_text(
                "ids:\n"
                "  - id: REQ-F02-EVIDENCE-AUTOMATION\n"
                "  - id: FEAT-QA-EVIDENCE-PACKAGE\n"
                "  - id: TEST-QA-EVIDENCE-MANIFEST\n"
                "  - id: EVID-F02-AUTOMATION-MANIFEST\n",
                encoding="utf-8",
            )
            traceability = source / "traceability.json"
            traceability.write_text(
                json.dumps(
                    {
                        "requirements": [
                            {
                                "requirement_id": "REQ-F02-EVIDENCE-AUTOMATION",
                                "feature_ids": ["FEAT-QA-EVIDENCE-PACKAGE"],
                                "test_ids": ["TEST-QA-EVIDENCE-MANIFEST"],
                                "evidence_ids": ["EVID-F02-AUTOMATION-MANIFEST"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            junit = source / "junit.xml"
            junit.write_text('<testsuite tests="1"><testcase name="pass" /></testsuite>', encoding="utf-8")
            fallback = source / "fallback.json"
            fallback.write_text(json.dumps({"backend": "CPU-EXPLICIT", "used": False}), encoding="utf-8")
            performance = source / "performance.json"
            performance.write_text(
                json.dumps({"frame_time_ms": [1.0, 2.0, 3.0], "minimum_samples": 3}),
                encoding="utf-8",
            )
            sample = source / "sample.txt"
            sample.write_text("sample", encoding="utf-8")
            output = workspace / "artifacts" / "BUILD-F02-AUDIT-TEST"
            with patch("scripts.collect_evidence_package.git_commit", return_value="b" * 40):
                result = collect_run(
                    [
                        "--workspace", str(workspace),
                        "--phase", "F02",
                        "--output", str(output),
                        "--registry", str(registry),
                        "--traceability", str(traceability),
                        "--junit", str(junit),
                        "--fallback-report", str(fallback),
                        "--performance", str(performance),
                        "--source", str(sample),
                        "--official",
                    ]
                )
            self.assertEqual(result, 0)
            report = json.loads((output / "package-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["phase"], "F02")


if __name__ == "__main__":
    unittest.main()
