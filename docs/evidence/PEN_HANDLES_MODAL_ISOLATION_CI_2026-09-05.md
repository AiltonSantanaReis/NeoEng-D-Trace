# Evidência — isolamento de modal residual e CI da Caneta

ID: EVID-PEN-HANDLES-MODAL-ISOLATION-20260905
Lote: PEN-HANDLES-20260905
Estado: IN_PROGRESS / BLOCKED
Data: 2026-09-05
Branch: Ailton/pen-handles-quantization-20260905
SHA auditado: fd4a67e0d2bf60f07b710c002c0be88eeee94424
Commit: `test: isolate residual Qt modals between cases`
PR: #171, ainda sem merge

## Objetivo e escopo

Registrar a correção da causa imediata observada na divergência Linux do teste
P2D-05: um `QMessageBox` modal residual permanecia ativo na `QApplication` entre
casos, fazendo o fluxo de rejeição por STATUS falhar na asserção de que nenhum
modal deveria estar ativo. A proteção foi adicionada exclusivamente ao harness
em `tests/conftest.py`: antes de cada teste, um modal residual é fechado, os
eventos de destruição adiados são processados e a ausência de modal ativo é
verificada. A asserção do teste funcional permanece intacta; nenhum modal
criado durante o teste é removido para fabricar `PASS`.

Não houve alteração no produto, no validador Bézier, na quantização, nos
snapshots legados ou nos thresholds. O baseline foi atualizado apenas para o
digest do arquivo de harness alterado.

## Diagnóstico preservado

O CI anterior `33987643808`, no SHA `dea93f8`, falhou no Linux em
`tests/test_p2d05_status_notice.py::test_new_pen_inherits_active_language_and_preserves_rejected_path[pt]`:
`QApplication.activeModalWidget()` retornou `QMessageBox`. O job Windows do
mesmo run passou. Essa falha histórica não foi apagada nem reclassificada.

Durante a requalificação local, o comando monolítico Linux-like executado no
Windows também terminou com `Windows fatal exception: access violation` em
`test_stage5_viewport_hud.py::test_status_indicator_fits_resolutions_without_legacy_hud`.
Esse comando não é o gate oficial Windows; o projeto usa shards isolados para
evitar abortos nativos cumulativos de Qt. O fato foi preservado como
`DIAGNOSTIC_ONLY`, sem declarar estabilidade do comando monolítico.

## Ambiente e entradas

- Windows 11 convidado em VMware; `platform win32`, Python 3.11.9.
- PySide6 6.10.1, pytest 9.1.1, pytest-cov 7.1.0, Poetry 2.4.1.
- `QT_QPA_PLATFORM=offscreen` nos testes Qt; isso não é auditoria nativa de
  cliques do SO.
- Checkout limpo antes da qualificação do SHA `fd4a67e...`.
- A validação Linux foi executada pelo runner GitHub Actions no mesmo SHA.

## Comandos executados

```text
python -m pytest tests/test_p2d05_status_notice.py -q -rs
python -m pytest tests/test_error_presentation_contract.py tests/test_error_presentation_gizmo_contract.py tests/test_error_presentation_layers_panel_contract.py tests/test_error_presentation_side_panel_contract.py tests/test_functional_user_flows.py tests/test_pen_creation_gestures.py -q -rs
python -m compileall -q -f app.py src tests pack_for_ai.py tools
flake8 src tests tools app.py pack_for_ai.py
black --check --diff src tests tools app.py pack_for_ai.py
isort --check-only --diff src tests tools app.py pack_for_ai.py
mypy src
pip-audit
bandit -q -r src -lll
python scripts/audit_stage4b5_quality.py --output <receipt>
python tools/run_windows_coverage_shards.py --output <receipt>
python tools/check_coverage_policy.py <receipt>/coverage.xml
python tools/baseline_integrity.py --verify --git-blob
python tools/evidence_integrity.py --require-tracked --git-blob
```

CI remoto completo:

- [run 33990872253](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33990872253)
- [job Linux 101372756689](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33990872253/job/101372756689)
- [job Windows 101372756798](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33990872253/job/101372756798)

## Resultados observados

| Critério | Resultado |
|---|---|
| Teste P2D-05 focado local | PASS — 14 testes |
| Conjunto focado relacionado | PASS — 86 testes |
| Runner Windows local no SHA | PASS — 196/196 arquivos, 2019 testes, 0 falhas, 0 erros, 2 skips previstos |
| Cobertura Windows local | PASS — 92,73% linhas e 85,18% branches; política aprovada |
| Estática local | PASS — compileall, Flake8, Black, isort e mypy |
| Segurança local | PASS — Bandit e pip-audit; pacote local não existe no PyPI e foi listado como não auditável |
| Stage 4B.5 local | PASS |
| Baseline/evidências locais | PASS — 3262 arquivos e 135 manifestos |
| CI Linux remoto | PASS — todos os passos oficiais, incluindo suíte completa, cobertura, integridade e Stage 4B.5 |
| CI Windows remoto | PASS — todos os passos oficiais, incluindo shards, cobertura, gate legado e integridade |

O recibo local final do runner Windows foi mantido fora do repositório para
não poluir a árvore. Seus arquivos principais foram:

| Recibo | Bytes | SHA-256 |
|---|---:|---|
| `summary.json` | 165217 | `bcf6ff2650b6cd0fc6f9f86d93573a57334a198b2546b940401145b65d319e54` |
| `coverage.xml` | 1202892 | `84331d38eb8237f19c37f9b9075d619895c77de7843628d7ca3edffd4387a4f4` |

## Limitações e decisão

- A auditoria nativa de cliques do SO no executável portátil continua
  `PENDING_EVIDENCE/BLOCKED`; Qt/offscreen, QTest e smoke de GUI não a
  substituem.
- Os dois skips continuam sendo os contratos históricos de symlink
  condicionados ao privilégio do runner Windows. A prova VMware autorizada
  permanece separada e não é requalificada por este commit.
- O CI verde comprova o SHA `fd4a67e` na PR #171, não autoriza merge automático.
- O lote global permanece `IN_PROGRESS / BLOCKED` até a auditoria nativa e a
  decisão formal correspondente. Nenhuma tag ou release foi criada.

Decisão: `PASS` para a correção do isolamento e para os gates CI do SHA
auditado; `BLOCKED` para a conclusão/publicação do lote enquanto a auditoria
nativa de cliques permanecer pendente.
