"""Contracts that prevent current-state documentation from regressing."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_readme_reports_versioned_project_and_current_stage():
    text = _text("README.md")
    assert ".ndtproj" in text
    assert "schema v1" in text
    assert "R-004" in text
    assert "Pacote 5C" in text
    assert "formato de projeto versionado, autosave" not in text


def test_package_5c_evidence_does_not_repeat_false_bezier_limitation():
    text = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "SceneObjectRecord.beziers" in text
    assert "round-trip" in text
    assert "pontos de controle não eram persistidos estava incorreta" in text
    assert "não são persistidos pelo formato atual" not in text


def test_live_documents_identify_current_main_pr_and_gate():
    expected_main = "ee38a2f1dc85093e34140ddd087312629b4ecb43"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/evidence/README.md",
    ):
        text = _text(relative)
        assert expected_main in text
        assert "#27" in text
        assert "R-004" in text


def test_superseded_documents_have_historical_classification():
    for relative in (
        "docs/MATRIZ_FUNCIONALIDADES.md",
        "docs/ESTRATEGIA_GITHUB.md",
        "docs/PLANO_DE_DESENVOLVIMENTO.md",
    ):
        assert "CLASSIFICAÇÃO DOCUMENTAL" in _text(relative)[:900]
    assert "Nota de continuidade" in _text("docs/PLANO_RENOMEACAO.md")[:900]


def test_governance_requires_sha_bound_ci_and_historical_snapshots():
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    assert "CI de um SHA anterior" in policy
    assert "snapshots históricos" in policy
    assert "Head SHA testado" in template
    assert "Toda afirmação de CI identifica o SHA" in template


def test_live_documents_describe_post_v31_review_state_without_stale_gates():
    stale_phrases = (
        "Pacote 5C: em correção e revalidação",
        "correção local deve ser revalidada",
        "próximo gate: correção incremental, reconciliação documental",
        "que deve permanecer draft até novo gate completo",
    )
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/evidence/README.md",
    ):
        text = _text(relative)
        for phrase in stale_phrases:
            assert phrase not in text, (relative, phrase)
    assert "APPROVED_FOR_DIFF_REVIEW_ONLY" in _text("README.md")
    evidence_index = _text("docs/evidence/README.md")
    assert "corrector v3.1" in evidence_index
    assert "corrector v3.2: bloqueado no dry-run pelo mypy" in evidence_index
    assert "corrector v3.3" in evidence_index
    assert "corrector v3.4" in evidence_index
    assert "corrector v3.5" in evidence_index
    assert "corrector v3.6" in evidence_index
    assert (
        "corrector v3.7: bloqueado no dry-run antes de escrever arquivos"
        in evidence_index
    )
    assert "corrector v3.8" in evidence_index
    assert "corrector v3.9" in evidence_index
    assert "corrector v4.0" in evidence_index
    assert "corrector v4.1" in evidence_index


def test_package_5c_evidence_records_v3_through_v40_truthfully():
    text = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "v3: bloqueado no dry-run por trailing whitespace documental" in text
    assert (
        "v3.1: gate Windows aprovado com 48 testes focais, 6 documentais e 460 totais"
        in text
    )
    assert "v3.2: bloqueado no dry-run pelo mypy" in text
    assert "v3.3: gate Windows aprovado com 50 testes focais" in text
    assert "9 documentais, 465 totais" in text
    assert "relatório permanente ainda exibia 48/6/460" in text
    assert "v3.4: gate Windows aprovado com 59 testes focais" in text
    assert "10 documentais, 475 totais" in text
    assert "v3.5: gate Windows aprovado com 67 testes focais" in text
    assert "11 documentais, 484 totais" in text
    assert "v3.6: gate Windows aprovado com 71 testes focais" in text
    assert "12 documentais, 489 totais" in text
    assert "v3.7: bloqueado no dry-run com 1 falha e 76 aprovações focais" in text
    assert "v3.8: gate Windows aprovado com 77 testes focais" in text
    assert "13 documentais, 496 totais e 66% de cobertura" in text
    assert "v3.9: gate Windows aprovado com 80 testes focais" in text
    assert "14 documentais, 500 totais e 66% de cobertura" in text
    assert "v4.0: gate Windows aprovado com 89 testes focais" in text
    assert "15 documentais, 510 totais e 66% de cobertura" in text
    assert "v4.1: linha corretiva atual" in text
    assert "Resultados da validação local v4.1" in text
    assert "Resultados da validação local v3\n" not in text


def test_evidence_policy_requires_complete_untracked_scope():
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    assert "git diff` não inclui arquivos untracked" in policy
    assert "snapshots integrais de todos os arquivos do escopo" in policy
    assert "Arquivos novos/untracked estão presentes integralmente" in template
    assert "métricas do relatório permanente" in policy
    assert "Undo, Redo, Escape" in policy
    assert "Gestos contínuos foram testados" in template


def test_reconciled_documents_have_one_terminal_newline_without_blank_eof():
    files = (
        "README.md",
        "CHANGELOG.md",
        ".github/pull_request_template.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md",
        "docs/MATRIZ_FUNCIONALIDADES.md",
        "docs/ESTRATEGIA_GITHUB.md",
        "docs/PLANO_DE_DESENVOLVIMENTO.md",
        "docs/PLANO_RENOMEACAO.md",
        "docs/evidence/README.md",
        "docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md",
    )
    for relative in files:
        data = (ROOT / relative).read_bytes()
        assert data.endswith(b"\n"), relative
        assert not data.endswith(b"\n\n"), relative


def test_package_5c_current_metrics_are_bound_to_the_v41_execution():
    text = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    patterns = (
        r"testes focais do Pacote 5C: `(?:\{\{PACKAGE_TARGETED_TESTS\}\}|\d+) passed`",
        r"testes de contrato documental: `(?:\{\{DOCUMENTATION_TESTS\}\}|\d+) passed`",
        r"suíte completa: `(?:\{\{FULL_TESTS\}\}|\d+) passed`",
        r"cobertura global exibida: `(?:\{\{COVERAGE_PERCENT\}\}|\d+)%`",
    )
    for pattern in patterns:
        assert re.search(pattern, text), pattern
    assert "v3.3 tenha passado com 50 testes focais, 9 documentais e 465 totais" in text
    assert (
        "v3.1: gate Windows aprovado com 48 testes focais, 6 documentais e 460 totais"
        in text
    )


def test_bezier_polygon_invariant_is_governed_and_reported():
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "Invariante do polígono Bézier amostrado" in policy
    assert "orientação anti-horária" in policy
    assert "área zero" in policy
    assert "não pode substituir o último estado válido" in policy
    assert "polígono Bézier amostrado foi normalizado" in template
    assert "rejeição de área zero, auto-interseção" in evidence
    assert "prévia inválida restrita aos nós visuais" in evidence
    assert "revisão pós-v3.4" in evidence


def test_deterministic_polygon_fallback_is_governed_and_reported():
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "não pode depender de Shapely" in policy
    assert "contatos de extremidade" in policy
    assert "sobreposição colinear" in policy
    assert "terminal duplicado" in policy
    assert "sem decisão condicionada a Shapely opcional" in template
    assert "revisão pós-v3.5" in evidence
    assert "validação determinística inclusiva" in evidence
    assert "curva fechada válida" in evidence


def test_numeric_domain_and_optional_dependency_independence_are_governed():
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "única autoridade de validade" in policy
    assert "não representáveis" in policy
    assert "aritmética de área não finita" in policy
    assert "sem decisão condicionada a Shapely opcional" in evidence
    assert "OverflowError" in evidence
    assert "Coordenadas Bézier não representáveis" in template
    assert "revisão pós-v3.6" in evidence
    focal_test = _text("tests/test_stage_5_package_5c_bezier_history.py")
    assert '"Polygon", unexpected_polygon_call, raising=False' in focal_test


def test_unrepresentable_bezier_conversion_is_centralized_and_reported():
    core = _text("src/core/bezier_geometry.py")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    assert "except (OverflowError, TypeError, ValueError) as exc" in core
    assert "coordinates must be finite and representable" in core
    assert "amostragem da cena e exportação de sprite" in evidence
    assert "conversão numérica central" in policy


def test_stable_cubic_and_opt_in_repair_are_governed_and_reported():
    core = _text("src/core/bezier_geometry.py")
    scene = _text("src/models/scene.py")
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "_stable_lerp" in core
    assert "_evaluate_canonical_cubic" in core
    assert "_BERNSTEIN_COMPATIBILITY_LIMIT" in core
    assert "De Casteljau" in core
    assert "if self.auto_repair" in scene
    assert "reparo geométrico é estritamente opt-in" in policy
    assert "avaliação cúbica deve preservar finitude" in policy
    assert "sem alterar o arredondamento histórico" in policy
    assert (
        "avaliação cúbica preservou o resultado e o arredondamento histórico"
        in template
    )
    assert "reparo de polígonos foi estritamente opt-in" in template
    assert "revisão pós-gate reproduziu duas falhas adicionais" in evidence
    assert "v4.0: gate Windows aprovado com 89 testes focais" in evidence


def test_handle_index_type_contract_is_strict_and_reported():
    core = _text("src/core/bezier_geometry.py")
    commands = _text("src/core/commands.py")
    policy = _text("docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md")
    template = _text(".github/pull_request_template.md")
    evidence = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "isinstance(handle_index, bool)" in core
    assert "not isinstance(handle_index, int)" in core
    assert "isinstance(self.handle_index, bool)" in commands
    assert "handle_index must be an integer" in commands
    assert "inteiro estrito e não booleano" in policy
    assert "valores não hashable" in policy
    assert "índice de handle exigiu inteiro estrito" in template
    assert "O gate Windows v4.0 passou com 89 testes focais" in evidence
    assert "O v4.1 exige um inteiro estrito e não booleano" in evidence
