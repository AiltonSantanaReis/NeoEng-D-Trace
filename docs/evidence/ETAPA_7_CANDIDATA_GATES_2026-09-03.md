# Evidência — candidata limpa para CI e empacotamento — 03/09/2026

## Identificação

- Estado: `PARCIAL / BLOQUEADO`; esta evidência não declara aprovação, integração ou release.
- Revisão-fonte validada: `d6e02cd9ee3445a02ef21faefb4c05d17e0d0fad`.
- Branch: `fix/legacy-27-functional-regressions`.
- Escopo: árvore Git limpa para repetir os gates locais e o build portátil no SHA acima.
- Rollback do checkpoint: revert do commit `d6e02cd`; rollback funcional da etapa: `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`.
- Regras consultadas antes desta decisão: `docs/POLITICA_NAO_REGRESSAO.md`, `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`, `docs/evidence/README.md`, este plano, `tools/run_legacy_tests.py` e os registros históricos protegidos.

## Objetivo e fronteira

Repetir em checkout limpo os gates locais da candidata, confirmar a capacidade de empacotamento portátil e consolidar a prova anterior de symlink no VMware. A validação não altera snapshots históricos, `quality/legacy_tests/manifest.json`, `quality/legacy_tests/reconciliation.json` ou os artefatos não rastreados preexistentes.

## Ambiente e entradas

- Host local: `win32`; Python `3.11.9`; Poetry `2.4.1`; pytest `9.1.1`; PyInstaller `6.22.0`.
- `QT_QPA_PLATFORM=offscreen`; dependências instaladas exclusivamente de `poetry.lock`.
- Checkout limpo no início e no fim; `artifacts/evidence/F02/BUILD-F02-GOVERNANCE-20260824-4E05A34/manifest.json` não estava presente na árvore limpa.
- `poetry.lock`: `200096` bytes; SHA-256 `05632587b9ddf365415401c063aa544b447b0430a0426a61762e129d3691b756`.
- Fixture `tests/fixtures/release_smoke.ndtproj`: `759` bytes; SHA-256 `f5578ddafc093c84fc513059e6704e15a8b259bbb087fbe0e21fe580d2d20b59`.
- Prova VMware relacionada: ZIP-base `64977183` bytes, SHA-256 `5668b579260ff0e098e407f9c5a588d2113cfd5cd37f6cf7a763d7a331545e8e`; patch `621637` bytes, SHA-256 `ed477bb5c6d204005fa684b866886456bce9d5010d25cc47fb49eebde4f5950d`.

## Comandos executados

```text
poetry env use 3.11
poetry check --lock --strict
poetry sync --no-interaction --no-ansi
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools/check_coverage_policy.py coverage.xml
poetry run python scripts/audit_stage4b5_quality.py --output <diretorio-temporário>
poetry run python tools/run_legacy_tests.py --group all --output <diretorio-temporário>
python tools/baseline_integrity.py --verify --git-blob
python tools/evidence_integrity.py --require-tracked --git-blob
.\scripts\build_windows.ps1 -OutputRoot release
```

## Resultados comprovados

- Gates estáticos: passaram; `pip-audit` informou não haver vulnerabilidades conhecidas e registrou apenas que o pacote local `neoeng-d-trace (0.3.0)` não está publicado no PyPI.
- Suíte oficial: `1911` coletados, `1909 passed`, `2 skipped`, `1 warning`, código `0`; cobertura total `90.82%`, com branches, acima dos limiares exigidos. Os dois skips são os contratos de symlink condicionados à capacidade da plataforma local.
- Política de cobertura: passou (`linhas >= 90%`, `branches >= 85%`, módulos mensuráveis >= 30%).
- Auditoria Stage 4B.5: `PASS`; determinismo, bytes de artefatos e limites de benchmark passaram.
- Baseline: `Baseline verified: 3182 files`.
- Integridade: `Evidence integrity passed: 124 manifests validated`.
- Empacotamento: build PyInstaller concluído; smoke `SUCCESS` com `11` checks; manifesto portátil com `314` arquivos e `source_commit` igual ao SHA validado.
- ZIP portátil: `124181819` bytes; SHA-256 `1559638225fe9e664ba5ebbc5d023b2ec4565b9d8dfb268fae5207c05401e33e`.
- Runner legado integral: código `1`; `196` testes, `26` falhas, `0` erros, `0` skips; reconciliação `15/27 matched`, `11 unexpected`, `12 missing`, `accepted=false`.

## Evidências relacionadas

- Symlink VMware: `docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md` e `docs/evidence/artifacts/symlink-vmware-2026-09-02/`; essa prova é de capacidade real no Windows 11/VMware com Developer Mode `1`, mas sua proveniência é o ZIP/patch e não um SHA Git próprio.
- Reconciliação formal atual: `docs/evidence/artifacts/legacy-26-formal-review-20260901/formal_reconciliation.json`, aceita somente no contrato atual; o runner histórico permanece separado e imutável.
- As saídas brutas locais de pytest, auditoria e PyInstaller não foram copiadas para o repositório porque contêm caminhos do host; este relatório conserva os resultados normalizados, hashes e limitações.

## Falhas, warnings e causa

1. O runner legado reproduziu a divergência histórica já registrada: os snapshots preservados continuam produzindo `26` falhas e a assinatura atual diverge em `11` IDs, enquanto `12` expectativas não são observadas. Não foi feita alteração de teste, expectativa, skip, xfail, filtro ou threshold.
2. O PyInstaller emitiu o warning `Hidden import "tzdata" not found` e outros imports condicionais/ opcionais ausentes; o smoke passou, mas o warning permanece uma limitação explícita.
3. A suíte registrou um `DeprecationWarning` do construtor `QMouseEvent`; não afetou o código de saída.

Esses fatos mantêm o bloqueio de integração. A falha histórica é conhecida e formalmente classificada, mas o workflow oficial ainda executa o runner como passo obrigatório; portanto, este resultado não é CI verde.

## Decisão formal

`CANDIDATA_LOCAL=PARCIAL`

`SYMLINK_VMWARE=PASS_ESCOPADO`

`PACKAGE_LOCAL=PASS_TECNICO`

`LEGACY_RUNNER=BLOCKED_ACCEPTED_FALSE`

`CI_REMOTO=NAO_EXECUTADO`

`MERGE=PROIBIDO`

`TAG_RELEASE=PROIBIDO`

O commit foi preservado como checkpoint reversível. A decisão profissional segura é não fazer merge, tag ou release e não publicar este SHA enquanto o gate legado obrigatório continuar retornando código `1`; a publicação só deve ocorrer após decisão explícita para esse gate e nova execução integral na mesma revisão. A prova de symlink é necessária e suficiente apenas para o escopo de capacidade real no VMware, não para aprovação global.
