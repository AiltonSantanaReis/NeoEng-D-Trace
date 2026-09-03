# Reconciliação formal caso a caso e auditoria de manifests — 2026-09-01

## Estado formal

- Identificador: `P2D-COMP-01/LEGACY-26-RECON`.
- HEAD avaliado: `eaa28b9a75194d25741323b4b72911426a740349`.
- Status: `ACEITO NO ESCOPO DE EQUIVALÊNCIA FORMAL`; integração permanece pendente dos gates residuais explicitamente registrados.
- Este adendo é uma nova evidência da revisão atual. O relatório preliminar da
  rodada anterior permanece preservado; nenhum snapshot histórico foi reescrito.
- O artefato `formal_reconciliation.json` registra `accepted=true` somente
  para o contrato atual e mantém `historical_runner.accepted=false` como
  resultado histórico imutável.

## Regras consultadas

Antes da classificação foram consultados `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`,
`docs/evidence/README.md`, este plano, o runner histórico e os registros
históricos em modo somente leitura. Aplicaram-se as regras de classificação
conservadora, parada por divergência não explicada, preservação de snapshots,
proibição de skips/xfails e exigência de objetos reais nos contratos aplicáveis.

## Resultados de execução utilizados

- Runner histórico: `196 testes, 26 falhas, 0 erros, 0 skips`; reconciliação
  exata `accepted=false`, `15/27 matched`, `11 unexpected`, `12 missing`.
- Substitutos nativos rerun nesta revisão candidata: `42 passed in 2.72s`, com `0` falhas,
  `0` erros e `0` skips. A execução usou Scene/CommandManager/CanvasView/Qt,
  QImage/ndarray, OpenCV, solver, cache e worker reais conforme o contrato.
- O hash SHA-256 do summary sanitizado do pacote anterior é `5cc67c3eeb9f301830e2881743ca6e779a6e35785764dc87f343dd765b74b46c`;
  o hash do summary bruto da execução histórica é registrado como
  `75b9724a8c1782a8f0b8dd53c88f8bb4f2b51a2aa83156eb8e99aa1545744c5`.
- Suíte oficial local: `1925 passed, 2 skipped, 1 warning` em `52.21s`.
  Os dois skips são preexistentes em `tests/test_integration_sync.py` e
  ocorreram porque o processo não possui o privilégio Windows de criar
  symlink; eles não foram adicionados pela candidata e permanecem não cobertos.
- Cobertura oficial: `coverage.xml` com `92.7%` de linhas e `85.16%` de
  branches; `tools/check_coverage_policy.py coverage.xml` passou.
- Black, isort, flake8, mypy e compilação passaram. Bandit no nível oficial da
  CI (`-lll`) passou; o scan amplo registrou 18 achados baixos preexistentes,
  sem severidade média/alta. Pip-audit não encontrou vulnerabilidades e marcou
  explicitamente o pacote local como não publicado/não auditável.
- Benchmarks reais P2D-05 O1 e O2 retornaram `PASS`; timeout/stale-result/
  end-to-end passou em duas repetições independentes.

## Decisão individual dos 27 IDs

A tabela abaixo é derivada do registro completo em
`docs/evidence/artifacts/legacy-26-formal-review-20260901/case_decisions.json`.
`NO_CHANGE` significa que não foi demonstrado defeito remanescente no contrato
atual; não significa apagar a divergência histórica. `CORRIGIDO` significa que
a correção do defeito específico foi demonstrada no código e no teste real.

| Caso | Resultado histórico | Substituto | Decisão formal |
|---:|---|---|---|
| 1 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_01_valid_l_decomposes_without_losing_area; tests/test_legacy_phase2_contracts.py::test_phase2_case_02_self_intersection_remains_rejected) | NO_CHANGE |
| 2 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_02_triangulation_preserves_valid_l_geometry; tests/test_legacy_phase2_contracts.py::test_phase2_case_02_self_intersection_remains_rejected) | NO_CHANGE |
| 3 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_03_sobel_contract_is_float32_finite_and_unclipped) | NO_CHANGE |
| 4 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_04_rotated_atlas_preserves_rect_and_derivable_uv) | NO_CHANGE |
| 5 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_05_real_bezier_history_round_trips_valid_geometry; tests/test_legacy_phase2_contracts.py::test_phase2_case_05_invalid_bezier_is_rejected_without_history) | NO_CHANGE |
| 6 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_case_06_lasso_native_gesture_is_one_reversible_creation; tests/test_legacy_phase3_contracts.py::test_phase3_case_06_lasso_rejection_preserves_preview_and_history) | NO_CHANGE |
| 7 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_07_08_pen_native_double_click_preserves_bezier_history) | NO_CHANGE |
| 8 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_07_08_pen_native_double_click_preserves_bezier_history) | NO_CHANGE |
| 9 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_09_10_polygonal_lasso_closes_and_rejects_without_loss) | NO_CHANGE |
| 10 | passed / missing_expected_failure | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_09_10_polygonal_lasso_closes_and_rejects_without_loss) | NO_CHANGE |
| 11 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_11_12_shape_native_gesture_is_reversible; tests/test_legacy_phase3_contracts.py::test_phase3_cases_11_12_degenerate_gesture_is_fail_closed) | NO_CHANGE |
| 12 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_11_12_shape_native_gesture_is_reversible; tests/test_legacy_phase3_contracts.py::test_phase3_cases_11_12_degenerate_gesture_is_fail_closed) | NO_CHANGE |
| 13 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order) | NO_CHANGE |
| 14 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order) | NO_CHANGE |
| 15 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order) | NO_CHANGE |
| 16 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order) | NO_CHANGE |
| 17 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_17_accepts_real_ndarray_and_qimage) | NO_CHANGE |
| 18 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_18_cache_hit_and_invalidation_are_observable) | NO_CHANGE |
| 19 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_19_worker_delivers_real_success_and_error; tests/test_legacy_phase4_contracts.py::test_phase4_cases_19_20_stale_result_cannot_overwrite_new_preview) | NO_CHANGE |
| 20 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_20_preview_is_delivered_by_real_qt_worker; tests/test_legacy_phase4_contracts.py::test_phase4_case_20_cancel_discards_pending_result_without_history; tests/test_legacy_phase4_contracts.py::test_phase4_cases_19_20_stale_result_cannot_overwrite_new_preview; tests/test_legacy_phase4_contracts.py::test_phase4_real_segment_timeout_cancels_and_discards_late_result) | NO_CHANGE |
| 21 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_21_real_double_click_closes_and_invalid_path_stays_out) | NO_CHANGE |
| 22 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_22_solver_is_fail_closed_without_image_and_works_with_edges) | NO_CHANGE |
| 23 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_23_min_points_is_explicit_and_default_stays_permissive) | NO_CHANGE |
| 24 | failed / matched | passed (tests/test_legacy_phase2_contracts.py::test_phase2_case_24_reset_view_uses_real_fit_and_center) | NO_CHANGE |
| 25 | failed / unexpected_signature | passed (tests/test_legacy_phase3_contracts.py::test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order) | CORRIGIDO |
| 26 | failed / matched | passed (tests/test_legacy_phase3_contracts.py::test_phase3_case_26_rectangle_round_trip_and_history_use_real_scene) | NO_CHANGE |
| 27 | failed / matched | passed (tests/test_legacy_phase4_contracts.py::test_phase4_case_27_end_to_end_real_image_worker_cache_scene_history) | NO_CHANGE |

### Caso #10

O #10 não produziu falha no runner atual. Continua no inventário como não
regressão e não foi apagado nem convertido em aceite histórico.

### Caso #25

O código atual contém `_freeze_state` cycle-safe desde `96ab35d`. O teste
nativo real confirmou undo/redo com metadata cíclica. A falha atual do runner
é `assert None is not None`, causada pelo caminho histórico com `Mock` que
não pode ser desempacotado; portanto o caso não é contado como passado. A
decisão `CORRIGIDO` é limitada ao defeito cycle-safe; a divergência do fixture
continua explícita.

## Auditoria individual dos 63 manifests

O registro completo por arquivo está em
`docs/evidence/artifacts/legacy-26-formal-review-20260901/untracked_manifest_audit.json`.
Cada entrada contém caminho, família, proprietário operacional autorizado,
origem classificada sem inventar o criador, escopo, bytes, SHA-256, referências,
tratamento e decisão no novo
`docs/evidence/artifacts/legacy-26-formal-review-20260901/manifest_resolution.json`.
Os arquivos originais não foram reescritos, normalizados, movidos, excluídos ou
adicionados automaticamente ao índice.

- Observados: 63/63.
- JSON válido: 63; inválido: 0.
- CRLF: 9; LF: 54.
- Grupos de SHA-256 duplicados: 7; arquivos dentro desses grupos: 34.
- Manifests contendo referência textual à fase corrente: 0.
- Casos que exigem revisão pelos padrões de privacidade rastreados: 0.

Os 63 foram formalmente classificados como pertencentes ao escopo operacional
do custodiante atual sob autorização explícita, fora do pacote atual de
reconciliação, com tratamento `PRESERVE_UNMODIFIED_OUTSIDE_SCOPE`. A identidade
do criador e o evento exato de criação continuam declarados como não provados.
Vinte e seis manifests possuem referências declaradas completas, 34 são
manifests de metadados sem referências de artefato, 1 é o manifest de
dependências Unity não aplicável e 2 manifests históricos de release declaram,
sem remoção, 353 referências ausentes cada. Isso é uma limitação registrada,
não uma ocultação.

## Decisão global e consequência

O gate formal atual está `accepted=true` no escopo
`formal_equivalence_current_contract`, com 27/27 decisões e 63/63 manifests
resolvidos formalmente. A reconciliação histórica exata continua
`accepted=false` por preservação obrigatória dos snapshots. A Fase 7 local
foi executada, mas a integração permanece bloqueada até resolver a capacidade
de symlink dos 2 testes preexistentes e obter confirmação de CI/empacotamento no
candidato final. Commit, push, merge, tag e release continuam proibidos enquanto
esse bloqueio não for encerrado.

## Referências de integridade

- `quality/legacy_tests/manifest.json` preservado: SHA-256
  `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a`.
- `quality/legacy_tests/reconciliation.json` preservado: SHA-256
  `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493`.
- Gate formal atual:
  `docs/evidence/artifacts/legacy-26-formal-review-20260901/formal_reconciliation.json`,
  `accepted=true`.
- Resolução dos manifests:
  `docs/evidence/artifacts/legacy-26-formal-review-20260901/manifest_resolution.json`,
  `63/63`, sem alteração dos fontes.
- O próximo passo é remover a limitação de symlink ou obter execução autorizada
  equivalente dos dois testes, repetir a suíte completa e confirmar CI/
  empacotamento; somente depois reavaliar integração.
