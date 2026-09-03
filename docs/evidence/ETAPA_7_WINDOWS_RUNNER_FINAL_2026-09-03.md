# Evidência — Etapa 7 — validação final do runner Windows

**Status local:** `PASS_LOCAL`
**Integração:** `BLOCKED`
**Data:** 2026-09-03
**Commit-fonte testado:** `55110c03a84a560823586d34e12e514592e6948b`
**Branch:** `fix/legacy-27-functional-regressions`

## Objetivo e decisão

Esta é a execução final da candidata técnica após o commit documental
`55110c0`. Ela valida a árvore limpa, o runner Windows/Qt definido na ADR,
as 11 assinaturas divergentes e as 12 ausências históricas, a preservação dos
snapshots, cobertura, qualidade, segurança, Stage 4B.5, symlink e
empacotamento. Não reescreve o relatório intermediário de `8e0ada3` e não
autoriza merge, tag ou release.

Decisão: os gates locais exigidos passaram no SHA final e a candidata está apta
somente ao push técnico previsto na seção 10.1 do plano. O CI remoto ainda não
foi executado, e portanto a integração permanece `BLOCKED`.

## Ambiente e comandos

- Windows `win32`, build reportado `10.0.26200`, Python `3.11.9`;
- Poetry `2.4.1`, pytest `9.1.1`, pytest-cov `7.1.0`, PyInstaller `6.22.0`;
- `QT_QPA_PLATFORM=offscreen`, dependências sincronizadas pelo lock;
- comandos completos, hashes e referências externas em
  `docs/evidence/artifacts/windows-runner-final-2026-09-03/final-execution-summary.json`.

## Runner/CI e cobertura

O runner oficial versionado executou cada arquivo top-level `tests/test_*.py`
em subprocesso próprio, sem `-k`, `--ignore` ou redução de escopo, com JUnit
por shard, cobertura acumulada, timeout e falha fechada. No SHA final:

| Arquivos | Testes | Falhas | Erros | Skips | Resultado |
|---:|---:|---:|---:|---:|---|
| 189/189 | 1918 | 0 | 0 | 2 | `ACCEPTED` |

A política de cobertura passou com `23887/25798` linhas (`92,59%`) e
`6664/7838` branches (`85,02%`). Os dois skips são exclusivamente os testes
condicionais de symlink, que registraram `WinError 1314` neste host.

## Reconciliação e snapshots

O gate formal aceitou o contrato atual sem falsificar o histórico:

- runner histórico bruto: `196` testes, `26` falhas, `0` erros, `0` skips,
  retorno `1`;
- `15` assinaturas históricas exatas;
- `11` assinaturas divergentes formalmente classificadas;
- `12` ausências históricas preservadas na reconciliação;
- `1` observação atual ausente, mantida como não regressão;
- `42` substitutos reais: `0` falhas, `0` erros e `0` skips.

`quality/legacy_tests/manifest.json` e
`quality/legacy_tests/reconciliation.json` não foram editados. Os hashes
canônicos e brutos dos snapshots permanecem os registrados no contrato atual e
no pacote formal. O detalhe das 27 decisões está em
`quality/legacy_tests/current_contract.json` e no resumo final hashado.

## Demais gates

- lock/instalação: `PASS`;
- compileall, Flake8, Black, isort, mypy e Bandit: `PASS`;
- pip-audit: nenhuma vulnerabilidade conhecida; o pacote local não publicado
  no PyPI foi explicitamente não auditável;
- Stage 4B.5: `PASS`, determinismo e entrada inalterada;
- baseline: `PASS`, `3196 files` contra blobs Git;
- evidence integrity: `PASS`, `125 manifests` rastreados;
- empacotamento: `SUCCESS`, `11` smoke checks, `314` arquivos, ZIP de
  `124181833` bytes, SHA-256
  `de3c8f4a3b3e7550e4ea9f1e868e2f25a3dea06b1f9e3fead11d80c5907daf93`.

## Symlink e limitações

No checkout final, o comando
`poetry run pytest tests\test_integration_sync.py -k symlink -q -rs`
terminou com `2 skipped, 29 deselected`, ambos por `WinError 1314`. A prova
autorizada no Windows 11/VMware com Developer Mode permanece válida como
`PASS_SCOPED`: `2 passed, 0 skipped` na reconstrução ZIP/patch identificada no
relatório `ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`. Ela não é promovida a prova
do SHA `55110c0`.

O CI remoto não foi executado porque o SHA final ainda não foi publicado. Os
logs brutos de shards, JUnit, relatório formal e Stage 4B.5 permanecem fora da
árvore; seus tamanhos e hashes estão no resumo final e o índice declara essa
limitação.

## Decisão formal

`PASS_LOCAL / BLOCKED_REMOTE`: a candidata técnica passou nos gates locais
requeridos, preservou o histórico e está apta ao push técnico controlado para
disparar CI. Merge, tag, release e qualquer declaração global de `APROVADO`,
`CONCLUÍDO`, `INTEGRADO` ou `PRONTO` continuam proibidos até a confirmação
remota e o fechamento dos critérios restantes.
