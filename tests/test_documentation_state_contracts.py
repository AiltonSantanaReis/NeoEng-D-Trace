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
    assert "docs/evidence/**" in workflow
    assert (
        "docs/evidence/ETAPA_2_INVENTARIO_FUNCIONAL_CARACTERIZACAO.md" not in workflow
    )
    assert "retention-days: 30" in workflow
    assert workflow.count("actions/checkout@v7") == 2
    assert workflow.count("fetch-depth: 0") == 1
    assert workflow.count("actions/setup-python@v7") == 2
    assert workflow.count("actions/upload-artifact@v7") == 2
    assert "GitHub Security Advisory" in security
    expected_failures = reconciliation["expected_failures"]
    failure_ids = {item["id"] for item in expected_failures}
    assert len(failure_ids) == len(expected_failures)
    assert {
        "test_convex_decomp::tests.test_convex_decomp.TestConvexDecomp::"
        "test_convex_decompose_l_shape",
        "test_convex_decomp::tests.test_convex_decomp.TestConvexDecomp::"
        "test_ear_clipping_concave_l_shape",
    } <= failure_ids
    for item in expected_failures:
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


def test_stage6_closure_is_bound_to_merge_and_postmerge_ci():
    merge_commit = "73a128ec44cde17867bbac6a7854ce86a43aba5a"
    postmerge_ci = "31431739320"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert merge_commit in value, relative
        assert postmerge_ci in value, relative
        assert "R-005" in value, relative
        assert "Etapa 6" in value, relative

    closure = _text("docs/evidence/ETAPA_6_ENCERRAMENTO_POS_MERGE.md")
    for marker in (
        "3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98",
        "321ccf3a692c7c1916eeeb61e7a041ee8bcef035",
        merge_commit,
        "31431473940",
        postmerge_ci,
        "9079413130",
        "9079450269",
        "R005_CLOSED=YES",
        "STAGE6_COMPLETED=YES",
        "STAGE7_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert marker in closure

    premerge = _text("docs/evidence/ETAPA_6_EXPORTACAO_COLISOES.md")
    assert "APROVADO LOCALMENTE / NÃO INTEGRADO" in premerge
    assert "R-005` permanece aberto" in premerge


def test_critical_coverage_evidence_keeps_residual_risk_open():
    evidence = _text("docs/evidence/COBERTURA_MODULOS_CRITICOS_2026-08-10.md")
    for marker in (
        "4f53a0d7df25ba6de7b2dd5759b4abc4be5e5b5e",
        "589 passed",
        "67.51%",
        "src/launcher.py` | 18% | 18%",
        "R-003` permanece aberto",
        "não aprova release",
        "APROVADO LOCALMENTE / NÃO INTEGRADO",
    ):
        assert marker in evidence

    index = _text("docs/evidence/README.md")
    assert "COBERTURA_MODULOS_CRITICOS_2026-08-10.md" in index
    assert "R-003` permanece aberto" in index


def test_stage7_cli_evidence_is_premerge_and_keeps_risk_open():
    contract = _text("docs/CONTRATO_CLI.md")
    evidence = _text("docs/evidence/ETAPA_7_CLI_PRE_MERGE.md")
    index = _text("docs/evidence/README.md")

    for marker in (
        "| `0` |",
        "| `1` |",
        "| `2` |",
        "--image` e `--project`",
        "não é uma transação conjunta",
    ):
        assert marker in contract

    for marker in (
        "a940ef13018aabc430126db3fd705b521fc1be06",
        "620 passed",
        "68.53%",
        "src/launcher.py`: `85%",
        "R-006` permanece aberto",
        "APROVADO LOCALMENTE / NÃO INTEGRADO",
    ):
        assert marker in evidence

    assert "ETAPA_7_CLI_PRE_MERGE.md" in index
    assert "Etapa 9: CONCLUÍDA" in index
    assert "R-008`: ENCERRADO NO ESCOPO APROVADO" in index


def test_stage8_geometry_evidence_is_premerge_and_keeps_risk_open():
    evidence = _text("docs/evidence/ETAPA_8_BEZIER_GEOMETRIA_PRE_MERGE.md")
    for marker in (
        "d11cd3dc0bd0063e325a53dd30fc439feda9dd24",
        "660 passed",
        "661 passed",
        "27/27",
        "95.59%",
        "93.29%",
        "`R-007`: aberto até merge",
        "APROVADO LOCALMENTE / NÃO INTEGRADO",
        "RELEASE_APPROVED=NO",
    ):
        assert marker in evidence


def test_stage8_closure_is_bound_to_merge_and_postmerge_ci():
    merge_commit = "fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e"
    postmerge_ci = "31441024001"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert merge_commit in value, relative
        assert postmerge_ci in value, relative
        assert "R-007" in value, relative
        assert "Etapa 8" in value, relative

    closure = _text("docs/evidence/ETAPA_8_ENCERRAMENTO_POS_MERGE.md")
    for marker in (
        "d11cd3dc0bd0063e325a53dd30fc439feda9dd24",
        "23d467f37b39e97251e589b544b84f29bcb18fee",
        merge_commit,
        "31440755594",
        postmerge_ci,
        "9082863959",
        "9082897744",
        "R007_CLOSED=YES",
        "STAGE8_COMPLETED=YES",
        "STAGE9_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert marker in closure


def test_stage7_closure_is_bound_to_merge_and_postmerge_ci():
    merge_commit = "99326f2d7ccf7046e401d90830feb8a5d33e9f9a"
    postmerge_ci = "31437000772"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert merge_commit in value, relative
        assert postmerge_ci in value, relative
        assert "R-006" in value, relative
        assert "Etapa 7" in value, relative

    closure = _text("docs/evidence/ETAPA_7_ENCERRAMENTO_POS_MERGE.md")
    for marker in (
        "a940ef13018aabc430126db3fd705b521fc1be06",
        "51e55a37021c506471111ef1f4e7bc9abe67c65d",
        merge_commit,
        "31436763095",
        postmerge_ci,
        "9081388807",
        "9081419753",
        "R006_CLOSED=YES",
        "STAGE7_COMPLETED=YES",
        "STAGE8_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert marker in closure

    premerge = _text("docs/evidence/ETAPA_7_CLI_PRE_MERGE.md")
    assert "APROVADO LOCALMENTE / NÃO INTEGRADO" in premerge
    assert "R-006` permanece aberto" in premerge


def test_stage9_closure_is_bound_to_merge_and_postmerge_ci():
    merge_commit = "76dd6b7ca3e7da08fab653d66ae29a33a839baf3"
    postmerge_ci = "31445518755"
    for relative in (
        "README.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert merge_commit in value, relative
        assert postmerge_ci in value, relative
        assert "R-008" in value, relative
        assert "Etapa 9" in value, relative

    closure = _text("docs/evidence/ETAPA_9_ENCERRAMENTO_POS_MERGE.md")
    for marker in (
        "28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76",
        "86cfb6b0cf43613417b12b3366f423216bd1e036",
        merge_commit,
        "31445205968",
        postmerge_ci,
        "9084385461",
        "9084401751",
        "R008_CLOSED=YES",
        "STAGE9_COMPLETED=YES",
        "STAGE10_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert marker in closure

    assert "31444322950" in closure
    assert "31444483410" in closure
    assert "não aprova release" in closure


def test_stage10_remote_evidence_history_is_preserved_without_overstatement():
    for relative in (
        "README.md",
        "CHANGELOG.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
        "docs/evidence/ETAPA_10_EXPORTADORES_ENGINES.md",
    ):
        value = _text(relative)
        assert "#42" in value, relative
        assert "31450335289" in value, relative
        assert "31451363518" in value, relative
        assert "31452032479" in value, relative
        assert "31457937902" in value, relative
        assert "9b22bdc54b13992658172d4748bfab44f3127c8e" in value, relative
        assert "31463873481" in value, relative
        assert "#43" in value, relative
        assert "31464786333" in value, relative
        assert "f8caec3e7156d308f03046f81d2c89996f959466" in value, relative
        assert "31469610508" in value, relative
        assert "rejeitad" in value, relative
        assert "aceit" in value, relative

    evidence = _text("docs/evidence/ETAPA_10_EXPORTADORES_ENGINES.md")
    assert "CONCLUÍDO NO ESCOPO APROVADO" in evidence
    assert "Release permanece **NÃO APROVADA**" in evidence

    correction = _text("docs/evidence/ETAPA_10_CORRECAO_COBERTURA_POS_MERGE.md")
    for expected in (
        "31463873481",
        "93692633942",
        "93692634029",
        "9090792550",
        "9090816311",
        "8.581/11.634",
        "8.582/11.634",
        "test_manager_normalizes_reverse_broadphase_pair_order",
        "730 passed",
        "31464786333",
        "#43",
        "f8caec3e7156d308f03046f81d2c89996f959466",
        "31469610508",
        "NÃO APROVADA",
    ):
        assert expected in correction

    closure = _text("docs/evidence/ETAPA_10_ENCERRAMENTO_POS_MERGE.md")
    for expected in (
        "31463873481",
        "31464786333",
        "93695329283",
        "93695329206",
        "9091131139",
        "9091140223",
        "31469610508",
        "93709824327",
        "93709824406",
        "9092862008",
        "9092878881",
        "730 passed",
        "8.582/11.634",
        "2.146/3.706",
        "45",
        "1.410",
        "CORRECTIVE_PR_MERGED=YES",
        "POST_MERGE_CI_STATUS=SUCCESS",
        "STAGE10_COMPLETED=YES",
        "STAGE11_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in closure


def test_stage11_package_1_is_local_partial_and_keeps_r003_open():
    evidence = _text("docs/evidence/ETAPA_11_COBERTURA_UI_PACOTE_1.md")
    for expected in (
        "5e88c8d548e2b60612601f83e1bf24aeb91081bb",
        "742 passed",
        "8.831/11.632",
        "2.247/3.704",
        "MODULES_BELOW_30_LINES=0",
        "MODULES_BELOW_30_BRANCHES=0",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
        "APROVADO LOCALMENTE / NÃO INTEGRADO",
        "31473415874",
        "93721601195",
        "93721601233",
        "9094281869",
        "9094317936",
        "1.412 payloads",
    ):
        assert expected in evidence


def test_stage11_packages_and_closure_are_preserved():
    evidence = _text("docs/evidence/ETAPA_11_COBERTURA_UI_PACOTE_2.md")
    for expected in (
        "33a807ca41c549c283cad13250ca54b7e2bb6e0b",
        "c9bafdd75a74a8dae39d814fd6b0ccf35a2f9f96",
        "753 passed",
        "31476442683",
        "93731130311",
        "93731130325",
        "9095447008",
        "9095475339",
        "1.413 payloads",
        "9.314/11.632",
        "2.453/3.704",
        "76,73%",
        "1.155 linhas",
        "696 ramos",
        "MODULES_BELOW_30_LINES=0",
        "MODULES_BELOW_30_BRANCHES=0",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
        "APROVADO LOCAL E NO CI PRÉ-MERGE / NÃO INTEGRADO",
    ):
        assert expected in evidence

    package_3 = _text("docs/evidence/ETAPA_11_COBERTURA_UI_PACOTE_3.md")
    for expected in (
        "075b5b0231ca0aeb8a26d6253e847619d70211cf",
        "762 passed",
        "9.747/11.632",
        "2.606/3.704",
        "80,55%",
        "722 linhas",
        "543 ramos",
        "2a1a9f2ad1f1e59cbcebb0f485632fa9e7478b78",
        "31479113082",
        "93739699296",
        "93739699345",
        "9096506966",
        "9096572715",
        "1.414 payloads",
        "PRE_MERGE_CI_STATUS=ACCEPTED",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in package_3

    package_4 = _text("docs/evidence/ETAPA_11_COBERTURA_NUMERICA_PACOTE_4.md")
    for expected in (
        "427cc803c7923970b9fd89752c0247f75b4f94c6",
        "779 passed",
        "10.007/11.628",
        "2.715/3.700",
        "83,00%",
        "459 linhas",
        "430 ramos",
        "b74d118129e9835ea21656ad21fd722673aa3b74",
        "31481664506",
        "93747777463",
        "93747777515",
        "9097517771",
        "9097494245",
        "1.415 payloads",
        "PRE_MERGE_CI_STATUS=ACCEPTED",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in package_4

    package_5 = _text("docs/evidence/ETAPA_11_COMANDOS_PAINEIS_PACOTE_5.md")
    for expected in (
        "eed019ff8046d667988352df0aef93e129275919",
        "810 passed",
        "10.257/11.628",
        "2.862/3.700",
        "85,59%",
        "209 linhas",
        "283 ramos",
        "07c5b78b4fc7e17676dcb42b4048f1a91273fd68",
        "31483687046",
        "93754111444",
        "93754111445",
        "9098343972",
        "9098267096",
        "1.415 payloads",
        "PRE_MERGE_CI_STATUS=ACCEPTED",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in package_5

    package_6 = _text("docs/evidence/ETAPA_11_METAS_FINAIS_PACOTE_6.md")
    for expected in (
        "d5a7b8559927dca130d6d47409988da07ef1dd7e",
        "877 passed",
        "10.787/11.628",
        "3.147/3.700",
        "90,91%",
        "31488173784",
        "93768251593",
        "93768251612",
        "9100022150",
        "9099983296",
        "1.418 payloads",
        "COVERAGE_TARGETS_MET=YES",
        "PRE_MERGE_CI_STATUS=ACCEPTED",
        "R003_CLOSED=NO",
        "STAGE11_COMPLETED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in package_6

    postmerge = _text("docs/evidence/ETAPA_11_ENCERRAMENTO_POS_MERGE.md")
    for expected in (
        "3cd1616fed60101bbd809f530667227a5006c409",
        "2a38b89e542390b3b4396a88d9a416f3695caadc",
        "31489594270",
        "93772672006",
        "93772672083",
        "9100512735",
        "9100539788",
        "31491221322",
        "93777947832",
        "93777947784",
        "9101145671",
        "9101167058",
        "89d13d7e3ee7a4cd926912aed8e3ae7e3d5505bb",
        "a22a90088220e586c3382c3ed5dc1075a3ff7e6b",
        "31495971632",
        "93793644185",
        "93793644105",
        "9103009810",
        "9103050616",
        "877 passed",
        "10.787/11.628",
        "3.147/3.700",
        "90,91%",
        "1.417 payloads",
        "R003_CLOSURE_RECOMMENDED=YES",
        "R003_CLOSED=YES",
        "STAGE11_COMPLETED=YES",
        "STAGE12_STARTED=YES",
        "STAGE12_COMPLETED=NO",
        "R012_CLOSED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in postmerge

    for relative in (
        "README.md",
        "CHANGELOG.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert "Etapa 11" in value, relative
        assert "877" in value, relative
        assert "90,91%" in value, relative
        assert "R-003" in value, relative
        assert "R-012" in value, relative
        assert "release" in value.lower(), relative
        assert "não aprovada" in value.lower(), relative


def test_stage12_premerge_evidence_preserves_historical_open_state():
    evidence = _text("docs/evidence/ETAPA_12_SEGURANCA_LIMITES_PRE_MERGE.md")
    for expected in (
        "a22a90088220e586c3382c3ed5dc1075a3ff7e6b",
        "2e9cad4cb7879aa7ceb8ee0a1e096b738674a984",
        "da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f",
        "a42b54b07d8e9e10feb8d283adc664b52f9d25d3",
        "4a55943f102c569d6175da84aec74d127e69697b",
        "31684136128",
        "94396143432",
        "94396143273",
        "9174746367",
        "9174781465",
        "928 passed",
        "11.174/12.040",
        "3.309/3.892",
        "85,02%",
        "90,91%",
        "73",
        "196",
        "27/27",
        "R-012",
        "ABERTO",
        "APROVADO TECNICAMENTE PRÉ-MERGE",
        "NÃO APROVADA",
    ):
        assert expected in evidence

    assert "Commit técnico: `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f`" in evidence
    assert "worktree limpa" in evidence
    assert "1.419" in evidence
    assert "zero referência proibida ou caminho pessoal" in evidence
    assert "Etapa 12: NÃO CONCLUÍDA" in evidence


def test_stage12_closure_is_bound_to_merge_and_postmerge_ci():
    closure = _text("docs/evidence/ETAPA_12_ENCERRAMENTO_POS_MERGE.md")
    for expected in (
        "#49",
        "03b4cd2fc57e2f9187836e5a0ffc89ee08e18fba",
        "872bf079d228d13d0203d22b844052b1f920e99b",
        "31685608005",
        "31686321925",
        "94403113721",
        "94403113862",
        "9175582216",
        "9175617872",
        "928 passed",
        "929",
        "326",
        "11.174/12.040",
        "3.309/3.892",
        "1.419",
        "R012_CLOSED=YES",
        "STAGE12_COMPLETED=YES",
        "STAGE13_STARTED=NO",
        "RELEASE_APPROVED=NO",
    ):
        assert expected in closure

    for relative in (
        "README.md",
        "CHANGELOG.md",
        "docs/PLANO_MESTRE_ESTABILIZACAO.md",
        "docs/MATRIZ_RISCOS_ESTABILIZACAO.md",
        "docs/MATRIZ_FUNCIONALIDADES_ATUAL.md",
        "docs/evidence/README.md",
    ):
        value = _text(relative)
        assert "928" in value, relative
        assert "872bf079d228d13d0203d22b844052b1f920e99b" in value, relative
        assert "31686321925" in value, relative
        assert "R-012" in value, relative
        assert "encerrado" in value.lower(), relative
        assert "release" in value.lower(), relative
        assert "não aprovada" in value.lower(), relative
