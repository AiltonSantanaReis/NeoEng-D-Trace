# Reconciliação formal — 26 falhas legadas — 2026-09-01

## Estado

- Identificador: `P2D-COMP-01/LEGACY-26-RECON`
- Fase: `5 — reconciliação formal`
- Status: `EM EXECUÇÃO — BLOQUEADA; reconciliação não aceita`
- Branch: `fix/legacy-27-functional-regressions`
- HEAD testado: `eaa28b9a75194d25741323b4b72911426a740349`
- Commit da origem legada: `cf749564ab5d961772d66dc363d0e990cebf8da3`

Este documento registra uma execução de reconciliação, não encerra a etapa e não
autoriza commit, push, merge ou avanço global. As classificações da matriz são
provisórias até a revisão formal. `quality/legacy_tests/manifest.json`,
`quality/legacy_tests/reconciliation.json` e os snapshots históricos foram
somente lidos.

## Regras consultadas

Antes da execução foram consultados, no branch testado:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `tools/run_legacy_tests.py`;
5. `quality/legacy_tests/manifest.json`;
6. `quality/legacy_tests/reconciliation.json`;
7. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
8. `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
9. `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md` e
   `docs/DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`.

Hashes confirmados na entrada:

- `quality/legacy_tests/manifest.json` SHA-256:
  `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a`;
- `quality/legacy_tests/reconciliation.json` SHA-256:
  `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493`.

## Execuções e entradas

Runner histórico integral, sem alteração de snapshots:

```powershell
.\.venv\Scripts\python.exe tools\run_legacy_tests.py --group all --timeout-seconds 120 --output <RUN_TMP>
```

O runner selecionou `24` arquivos e executou `196` testes. O resultado bruto
foi `26 falhas, 0 erros e 0 skips`; o processo retornou falha. O `summary.json`
bruto original, antes da sanitização de caminhos locais, tem SHA-256
`75b9724a8c1782a8f0b8dd53c88f8bb4f2b51a2aa83156eb8e99aa1545744c5`.

Os logs e JUnit foram copiados para
`docs/evidence/artifacts/legacy-26-phase5-20260901/`. Caminhos locais e o
identificador do usuário foram substituídos por `<REPO_ROOT>`, `<RUN_TMP>` e
`<PYTHON_RUNTIME>`; nenhum teste, traceback, mensagem ou resultado foi removido.
O manifest desse pacote contém os hashes dos 52 arquivos sanitizados (runner,
suíte substituta e reconciliação formal) e passou
no gate de evidências.

Contratos substitutos reais executados:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_legacy_phase1_contracts.py tests\test_legacy_phase2_contracts.py tests\test_legacy_phase3_contracts.py tests\test_legacy_phase4_contracts.py
```

Resultado: `42 passed in 2.86s`, sem skip ou xfail; o JUnit confirma
`tests=42`, `failures=0`, `errors=0`, `skipped=0`. Os testes usam as fixtures
concretas previstas: `Scene`, `CommandManager`, `CanvasView`, `QApplication`,
`QImage`, `ndarray`, solver, cache, worker e sinais Qt reais quando aplicável.

## Resultado do reconciliador histórico

O `quality/legacy_tests/reconciliation.json` permaneceu intocado e continua
reportando:

- `status=failed`, `accepted=false`;
- `expected_failures=27`;
- `matched_failures=15/27`;
- `11` assinaturas atuais diferentes das esperadas;
- `12` assinaturas esperadas ausentes.

O caso histórico `#10` passou e permanece como não regressão. O caso `#25`
também passou após a correção cycle-safe do snapshot. Eles não integram os 26
casos falhos desta etapa, mas continuam registrados para impedir regressão.

## Matriz caso a caso

`PASS` na coluna de substituto significa que o contrato atual foi exercitado
com dados/objetos reais. `CANDIDATO_NO_CHANGE` não é aceite final: indica que a
divergência histórica tem uma explicação técnica sustentada pelo substituto,
mas ainda requer revisão formal e reconciliação independente.

O registro machine-readable desta análise, com os 27 IDs esperados, a observação
do runner histórico e a decisão pendente por caso, está em
`docs/evidence/artifacts/legacy-26-phase5-20260901/case_reconciliation.json`.

| Caso | Falha/assinatura histórica esperada | Contrato substituto real executado | Resultado | Classificação corrente |
|---:|---|---|---|---|
| 1 | `Triangulation did not preserve polygon geometry` | `test_phase2_case_01_valid_l_decomposes_without_losing_area` + rejeição da auto-interseção em `test_phase2_case_02_self_intersection_remains_rejected` | PASS | CANDIDATO_NO_CHANGE — fixture histórica inválida |
| 2 | `Triangulation did not preserve polygon geometry` | `test_phase2_case_02_triangulation_preserves_valid_l_geometry` em ambas as orientações + rejeição explícita | PASS | CANDIDATO_NO_CHANGE — fixture histórica inválida |
| 3 | `dtype('float32')` | `test_phase2_case_03_sobel_contract_is_float32_finite_and_unclipped` | PASS | CANDIDATO_NO_CHANGE — contrato atual float32 |
| 4 | `1 != 2` | `test_phase2_case_04_rotated_atlas_preserves_rect_and_derivable_uv` | PASS | CANDIDATO_NO_CHANGE — atlas único/rotação atuais |
| 5 | `Invalid polygon` | `test_phase2_case_05_real_bezier_history_round_trips_valid_geometry` + rejeição de Bézier inválida | PASS | CANDIDATO_NO_CHANGE — fixture colinear |
| 6 | assinatura mudou; expectativa histórica sobre `QMessageBox.warning` | `test_phase3_case_06_lasso_native_gesture_is_one_reversible_creation` + preservação em rejeição | PASS | CANDIDATO_NO_CHANGE — fixture/manager histórico incompleto |
| 7 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_07_08_pen_native_double_click_preserves_bezier_history` | PASS | CANDIDATO_NO_CHANGE — fixture/manager histórico incompleto |
| 8 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_07_08_pen_native_double_click_preserves_bezier_history` | PASS | CANDIDATO_NO_CHANGE — fixture/manager histórico incompleto |
| 9 | assinatura mudou; expectativa histórica sobre `QMessageBox.warning` | `test_phase3_cases_09_10_polygonal_lasso_closes_and_rejects_without_loss` | PASS | CANDIDATO_NO_CHANGE — eventos/Scene históricos incompatíveis |
| 10 | assinatura esperada sobre `QMessageBox.warning`; falha não reproduzida no runner | `test_phase3_cases_09_10_polygonal_lasso_closes_and_rejects_without_loss` | PASS | CANDIDATO_NO_CHANGE — entrada histórica ausente nesta execução; contrato equivalente coberto |
| 11 | assinatura mudou; expectativa histórica sobre `QMessageBox.warning` | `test_phase3_cases_11_12_shape_native_gesture_is_reversible` + caso degenerado fail-closed | PASS | CANDIDATO_NO_CHANGE — parent/Scene históricos incompletos |
| 12 | assinatura mudou; expectativa histórica sobre `QMessageBox.warning` | `test_phase3_cases_11_12_shape_native_gesture_is_reversible` + caso degenerado fail-closed | PASS | CANDIDATO_NO_CHANGE — parent/Scene históricos incompletos |
| 13 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order` | PASS | CANDIDATO_NO_CHANGE — Scene parcial histórica |
| 14 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order` | PASS | CANDIDATO_NO_CHANGE — Scene parcial histórica |
| 15 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order` | PASS | CANDIDATO_NO_CHANGE — Scene parcial histórica |
| 16 | assinatura mudou; expectativa histórica sobre `QMessageBox.critical` | `test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order` | PASS | CANDIDATO_NO_CHANGE — Scene parcial histórica |
| 17 | `assert None is not None` | `test_phase4_case_17_accepts_real_ndarray_and_qimage` | PASS | CANDIDATO_NO_CHANGE — imagem Mock histórica |
| 18 | `assert None is not None` | `test_phase4_case_18_cache_hit_and_invalidation_are_observable` | PASS | CANDIDATO_NO_CHANGE — imagem/cache histórico inválido |
| 19 | `assert 1 == 2` | `test_phase4_case_19_worker_delivers_real_success_and_error` + `test_phase4_cases_19_20_stale_result_cannot_overwrite_new_preview` | PASS | CANDIDATO_NO_CHANGE — resolução síncrona histórica |
| 20 | `assert 0 > 0` | `test_phase4_case_20_preview_is_delivered_by_real_qt_worker` + cancelamento/timeout/resposta tardia | PASS | CANDIDATO_NO_CHANGE — verificação prematura histórica |
| 21 | `Expected 'execute' to have been called once` | `test_phase4_case_21_real_double_click_closes_and_invalid_path_stays_out` | PASS | CANDIDATO_NO_CHANGE — caminho/manager históricos inválidos |
| 22 | `assert 0 > 0` | `test_phase4_case_22_solver_is_fail_closed_without_image_and_works_with_edges` | PASS | CANDIDATO_NO_CHANGE — edge map histórico ausente |
| 23 | `assert 4 >= 8` | `test_phase2_case_23_min_points_is_explicit_and_default_stays_permissive` | PASS | CANDIDATO_NO_CHANGE — expectativa default obsoleta |
| 24 | `1.5 != 1.0` | `test_phase2_case_24_reset_view_uses_real_fit_and_center` | PASS | CANDIDATO_NO_CHANGE — fit/center atual |
| 25 | `maximum recursion depth exceeded` | `test_phase3_cases_13_16_real_tools_restore_full_sequence_in_order` | PASS | CANDIDATO_NO_CHANGE — falha histórica com assinatura alterada; fixture Mock recursiva |
| 26 | `assert 0 == 1` | `test_phase3_case_26_rectangle_round_trip_and_history_use_real_scene` | PASS | CANDIDATO_NO_CHANGE — Fake Scene histórica |
| 27 | `assert 0 == 1` | `test_phase4_case_27_end_to_end_real_image_worker_cache_scene_history` | PASS | CANDIDATO_NO_CHANGE — pipeline histórico falso/incompleto |

## Conclusão desta rodada

Esta rodada demonstra que os 27 IDs esperados foram analisados: 26 produziram
falha no runner histórico, 15 coincidiram com a assinatura preservada, 11
tiveram assinatura alterada e o caso 10 não falhou nessa execução. Os contratos
substitutos reais passaram, mas isso ainda não produz `accepted=true`. A
divergência do reconciliador histórico permanece visível e precisa ser
transformada em decisão formal de harness, nunca em alteração dos snapshots.

Os gates da fronteira staged ao final da rodada foram:

- `evidence_integrity.py --require-tracked --git-blob`: `122 manifests validated`;
- `baseline_integrity.py --verify --git-blob`: `Baseline verified: 3168 files`;
- privacidade dos logs copiados: caminhos locais não encontrados após sanitização;
- snapshots legados: hashes preservados.

O manifest não rastreado preexistente do workspace ainda não foi incorporado nem
removido; sua propriedade, escopo e tratamento continuam uma pendência formal.
O próximo trabalho autorizado é revisar esta matriz, executar o teste do
contrato de reconciliação substituto e produzir a decisão `accepted=true` ou
`BLOCKED` com cada divergência residual. Commit, push, merge e avanço global
continuam proibidos.
