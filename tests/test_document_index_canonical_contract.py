from __future__ import annotations

import unittest
from pathlib import Path

from scripts.validate_evidence_registry import (
    validate_document_index,
    validate_registry,
)


class CanonicalDocumentIndexContractTests(unittest.TestCase):
    def test_canonical_index_points_to_canonical_registry(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        index = workspace / "docs" / "INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md"
        registry = (
            workspace
            / "docs"
            / "REGISTRO_IDS_PRODUTO_PROFISSIONAL_CANONICO_2026-08-24.yaml"
        )
        index_report = validate_document_index(index, workspace)
        registry_report = validate_registry(registry)
        self.assertEqual(index_report["status"], "PASS")
        self.assertEqual(registry_report["status"], "PASS")
        text = index.read_text(encoding="utf-8")
        self.assertIn(registry.name, text)
        self.assertIn("INDICE_DOCUMENTAL_ATIVO_2026-08-24.md", text)
        self.assertIn("INDICE_DOCUMENTAL_ATIVO_2026-08-24.md` | ATIVO |", text)
        self.assertIn(
            "REGISTRO_IDS_PRODUTO_PROFISSIONAL_2026-08-24.yaml` | ATIVO |", text
        )
        self.assertNotIn("SUPERSEDED", text.split("## 3.")[0])


if __name__ == "__main__":
    unittest.main()
