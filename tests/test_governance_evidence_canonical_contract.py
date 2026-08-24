from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.collect_evidence_package_canonical as canonical
from scripts.validate_evidence_registry import validate_document_index, validate_registry


class CanonicalEvidenceContractTests(unittest.TestCase):
    def test_canonical_registry_and_index(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        registry = workspace / "docs" / "REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml"
        index = workspace / "docs" / "INDICE_DOCUMENTAL_ATIVO_2026-08-24.md"
        registry_report = validate_registry(registry)
        index_report = validate_document_index(index, workspace)
        self.assertEqual(registry_report["status"], "PASS")
        self.assertEqual(index_report["status"], "PASS")

    def test_canonical_collector_accepts_zero_padded_phase(self) -> None:
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
                result = canonical.collector.run(
                    [
                        "--workspace",
                        str(workspace),
                        "--phase",
                        "F02",
                        "--output",
                        str(output),
                        "--registry",
                        str(registry),
                        "--traceability",
                        str(traceability),
                        "--junit",
                        str(junit),
                        "--fallback-report",
                        str(fallback),
                        "--performance",
                        str(performance),
                        "--source",
                        str(sample),
                        "--official",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertEqual(
                json.loads((output / "package-report.json").read_text(encoding="utf-8"))["status"],
                "PASS",
            )


if __name__ == "__main__":
    unittest.main()
