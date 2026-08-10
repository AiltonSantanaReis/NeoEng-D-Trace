"""Contracts that prevent current-state documentation from regressing."""

import json
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
    assert "encerramento formal condicionado" not in text
    assert "foi corrigido localmente e aguarda CI" not in text
    assert "Actions atuais ainda referenciam" not in text


def test_package_5c_evidence_does_not_repeat_false_bezier_limitation():
    text = _text("docs/evidence/ETAPA_5_PACOTE_5C_BEZIER_RESIDUAL_COMMANDS.md")
    assert "SceneObjectRecord.beziers" in text
    assert "round-trip" in text
    assert "pontos de controle não eram persistidos estava incorreta" in text
    assert "não são persistidos pelo formato atual" not in text


def test_live_documents_identify_final_main_and_closed_stage():
    expected_main = "574be9bd0268e70c384903f93f16cf6e73aa57a2"
    merged_head = "956db473a88641bfdcfbd49ed122479f3fa2c51d"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert expected_main in value
        assert merged_head in value
        assert "#28" in value
        assert "R-004" in value
        assert "31425585259" in value
        assert "Etapa 6" in value

    closure = _text("docs/evidence/ETAPA_5_ENCERRAMENTO_POS_MERGE.md")
    assert expected_main in closure
    assert merged_head in closure
    assert "31425585259" in closure
    assert "9077091136" in closure
    assert "9077113199" in closure
    assert "R004_CLOSED=YES" in closure
    assert "STAGE5_COMPLETED=YES" in closure
    assert "STAGE6_STARTED=NO" in closure

    premerge = _text("docs/evidence/ETAPA_5_PACOTE_5C_VALIDACAO_PRE_MERGE.md")
    assert "9bf83af0d58b5984ccfefc59a543428379b02632" in premerge
    assert "31115744015" in premerge
    assert "8973550294" in premerge
    assert "8973729078" in premerge
    assert "R-004`, aberto" in premerge
    assert "Ready for review exige autorização separada" in premerge


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


def test_live_documents_describe_postmerge_state_without_stale_gates():
    stale_phrases = (
        "`main` integrada até o Pacote 5B",
        "Pacote 5C na PR `#27`, draft e não integrado",
        "Pacote 5C: PR `#27`, draft e não integrado",
        "Pacote 5C permanece não integrado",
        "A PR `#27` contém trabalho ainda não integrado",
        "reconciliação documental deve gerar novo HEAD",
        "novo CI Linux/Windows antes de Ready",
    )
    ci_markers = {
        "README.md": "CI pós-merge `Private validation` `#84`",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md": "CI pós-merge da `main`",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md": "CI pós-merge `#84`",
        "docs/evidence/README.md": "CI pós-merge `#84`",
    }
    for relative, ci_marker in ci_markers.items():
        value = _text(relative)
        for phrase in stale_phrases:
            assert phrase not in value, (relative, phrase)
        assert "574be9bd0268e70c384903f93f16cf6e73aa57a2" in value
        assert "956db473a88641bfdcfbd49ed122479f3fa2c51d" in value
        if relative != "docs/evidence/README.md":
            assert "APPROVED_FOR_DIFF_REVIEW_ONLY" not in value
        assert ci_marker in value, (relative, ci_marker)

    evidence_index = _text("docs/evidence/README.md")
    for version in (
        "v3.1",
        "v3.2",
        "v3.3",
        "v3.4",
        "v3.5",
        "v3.6",
        "v3.7",
        "v3.8",
        "v3.9",
        "v4.0",
        "v4.1",
    ):
        assert f"corrector {version}" in evidence_index
    assert "ETAPA_5_PACOTE_5C_VALIDACAO_PRE_MERGE.md" in evidence_index
    assert "ETAPA_5_ENCERRAMENTO_POS_MERGE.md" in evidence_index
    assert "## Histórico dos correctors do Pacote 5C" in evidence_index
    assert "gate vigente naquele snapshot pré-commit" in evidence_index
    assert "- gate vigente: somente uma evidência v4.1" not in evidence_index

    premerge = _text("docs/evidence/ETAPA_5_PACOTE_5C_VALIDACAO_PRE_MERGE.md")
    assert "COMMIT, PUSH E NOVO CI" in premerge
    assert "EXIGEM AUTORIZAÇÃO ESPECÍFICA" in premerge
    assert "AUTORIZADA SOMENTE A" not in premerge


def test_stage5_closure_report_is_complete_and_final():
    text = _text("docs/evidence/ETAPA_5_ENCERRAMENTO_POS_MERGE.md")
    for marker in (
        "Cadeia funcional comprovada",
        "CI pós-merge histórico",
        "Limitações e riscos residuais",
        "ETAPA 5 FORMALMENTE ENCERRADA",
        "LOCAL_REMEDIATION_COMPLETE=YES",
        "DOCUMENTATION_PACKAGE_PREPARED=YES",
        "COMMIT_CREATED=YES",
        "PUSH_EXECUTED=YES",
        "PR_CREATED=YES",
        "PR_NUMBER=28",
        "PR_DRAFT=NO",
        "PR_MERGED=YES",
        "PR_CI_EXECUTED=YES",
        "PR_CI_STATUS=SUCCESS",
        "POST_MERGE_CI_EXECUTED=YES",
        "POST_MERGE_CI_STATUS=SUCCESS",
        "R004_CLOSED=YES",
        "RELEASE_APPROVED=NO",
        "STAGE5_COMPLETED=YES",
        "STAGE6_STARTED=NO",
        "31422901244",
        "31423386971",
        "31425585259",
        "93569241989",
        "93569242024",
        "93576381868",
        "93576382048",
    ):
        assert marker in text

    patterns = (
        r"testes documentais: `(?:\{\{DOCUMENTATION_TESTS\}\}|\d+) passed`",
        r"suíte completa: `(?:\{\{FULL_TESTS\}\}|\d+) passed`",
        r"cobertura combinada: `(?:\{\{COVERAGE_PERCENT\}\}|\d+(?:\.\d+)?)%`",
        r"baseline: `(?:\{\{BASELINE_COUNT\}\}|\d+)` arquivos",
    )
    for pattern in patterns:
        assert re.search(pattern, text), pattern


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
        "docs/evidence/ETAPA_5_PACOTE_5C_VALIDACAO_PRE_MERGE.md",
        "docs/evidence/ETAPA_5_ENCERRAMENTO_POS_MERGE.md",
        "docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "SECURITY.md",
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
        r"cobertura global exibida: `(?:\{\{COVERAGE_PERCENT\}\}|\d+(?:\.\d+)?)%`",
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


def test_audit_remediation_and_security_gates_are_fail_closed():
    audit = _text("docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md")
    matrix = _text("docs/MATRIZ_FUNCIONALIDADES_ATUAL.md")
    workflow = _text(".github/workflows/ci.yml")
    pyproject = _text("pyproject.toml")
    mypy_config = _text("mypy.ini")
    security = _text("SECURITY.md")
    reconciliation = json.loads(_text("quality/legacy_tests/reconciliation.json"))

    assert "ETAPA 5 FORMALMENTE ENCERRADA" in audit
    assert "Esta decisão não aprova release" in audit
    assert "Matriz funcional atual" in matrix
    assert "Build Windows/instalador | NÃO INICIADO" in matrix
    assert 'Pillow = "12.3.0"' in pyproject
    assert "[tool.mypy]" not in pyproject
    assert "check_untyped_defs = True" in mypy_config
    assert "warn_unused_configs = True" in mypy_config
    assert "poetry run pip-audit" in workflow
    assert "poetry run bandit -q -r src -lll" in workflow
    assert "--cov-branch --cov-fail-under=62" in workflow
    assert "Run reconciled preserved legacy suite" in workflow
    assert "retention-days: 30" in workflow
    assert workflow.count("actions/checkout@v7") == 2
    assert workflow.count("actions/setup-python@v7") == 2
    assert workflow.count("actions/upload-artifact@v7") == 2
    assert "GitHub Security Advisory" in security
    assert len(reconciliation["expected_failures"]) == 26
    for item in reconciliation["expected_failures"]:
        assert item["message_contains"]
        assert item["rationale"]
        assert item["replacement_tests"]


def test_live_closure_claims_only_proven_merge_and_not_release():
    closure = _text("docs/evidence/ETAPA_5_ENCERRAMENTO_POS_MERGE.md")
    assert "PR_CI_EXECUTED=YES" in closure
    assert "PR_CI_STATUS=SUCCESS" in closure
    assert "PR_MERGED=YES" in closure
    assert "POST_MERGE_CI_EXECUTED=YES" in closure
    assert "POST_MERGE_CI_STATUS=SUCCESS" in closure
    assert "R004_CLOSED=YES" in closure
    assert "STAGE5_COMPLETED=YES" in closure
    assert "STAGE6_STARTED=NO" in closure
    assert "RELEASE_APPROVED=NO" in closure
    assert re.search(r"projeto não está\s+aprovado para release", closure)
