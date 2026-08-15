import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stage14_postmerge_closure_preserves_audited_truth() -> None:
    evidence = (
        ROOT / "docs" / "evidence" / "ETAPA_14_ENCERRAMENTO_POS_MERGE.md"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (ROOT / "docs" / "evidence" / "ETAPA_14_ENCERRAMENTO_POS_MERGE.json").read_text(
            encoding="utf-8"
        )
    )

    for marker in (
        "PR integrada mais recente: `#58`",
        "f15193a55d1a5de0c7031f5bab656107302eee1b",
        "31905237922",
        "982 passed",
        "raw_test_status=failed",
        "27 falhas brutas",
        "STAGE14_COMPLETED=YES",
        "RELEASE_APPROVED=NO",
        "R-014",
        "R-015",
        "R-016",
    ):
        assert marker in evidence

    assert manifest["decision"]["stage_completed"] is True
    assert manifest["decision"]["release_approved"] is False
    assert manifest["post_merge_ci"]["head_sha"] == manifest["merge_commit"]
    assert manifest["legacy"]["raw_test_status"] == "failed"
    assert manifest["legacy"]["matched_expected_failures"] == 27
    assert manifest["legacy"]["unexpected_failures"] == 0
    assert manifest["legacy"]["missing_expected_failures"] == 0
    assert manifest["validation"]["coverage"]["pointwise_identical"] is True


def test_release_roadmap_defers_signature_without_approving_release() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    risks = (ROOT / "docs" / "MATRIZ_RISCOS_ESTABILIZACAO.md").read_text(
        encoding="utf-8"
    )
    checklist = (ROOT / "docs" / "CHECKLIST_RELEASE_PUBLICA.md").read_text(
        encoding="utf-8"
    )

    assert "primeiras releases" in readme
    assert "sem assinatura" in readme
    assert "RELEASE_APPROVED=NO" in readme
    assert "R-014 | ABERTO / DEFERIDO PARA FUTURAS BUILDS/RELEASES OFICIAIS" in risks
    assert "futuras builds/releases oficiais" in checklist
    assert "NÃO APROVADA" in checklist
