# Evidência — Encerramento pós-merge da Etapa 7 — PR #166 — 03/09/2026

**Status do gate pós-merge:** `PASS`

**Estado da Etapa 7:** `APROVADO NO ESCOPO DA PR #166`

**Estado do plano global:** `IN_PROGRESS`

**Release e tag:** `BLOCKED` — não fazem parte deste encerramento.

## Objetivo e escopo

Este snapshot registra a validação pós-merge da correção das regressões legadas
e da estabilização do runner Windows. O escopo é a PR `#166`, integrada no
merge commit `8a97ae14e8f84eb86fcacfaefed61f014830fbf9`, e não uma aprovação
global do produto ou da release.

O snapshot comprova que o commit-fonte `c6a2d18f9c6bcd48dba65b0df333a813ad6b86b3`
foi integrado em `main` e que o workflow oficial passou novamente nos jobs
Linux e Windows. O relatório pré-merge da candidata e a falha Windows
anterior continuam preservados, sem reclassificação retroativa.

## Regras e fontes consultadas

Antes deste registro foram relidas:

- `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`;
- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
- `docs/POLITICA_NAO_REGRESSAO.md`;
- `docs/evidence/README.md`;
- `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
- `docs/ADR_WINDOWS_COVERAGE_SHARD_RUNNER_2026-09-03.md`;
- `.github/workflows/ci.yml` e os validadores executados pelo workflow.

As regras aplicadas foram: preservar snapshots, distinguir commit-fonte de
commit testado, exigir evidência rastreável, manter o gate formal histórico
fail-closed e não transformar este encerramento em aprovação de release.

## Identificação e proveniência

- PR: `#166`;
- branch de origem: `fix/legacy-27-functional-regressions`;
- commit-fonte da PR: `c6a2d18f9c6bcd48dba65b0df333a813ad6b86b3`;
- base da PR: `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`;
- merge commit em `main`: `8a97ae14e8f84eb86fcacfaefed61f014830fbf9`;
- evento do CI pós-merge: `push` em `main`;
- run pós-merge: `33794660766`;
- job Linux: `100779319495`;
- job Windows: `100779319836`.

Ao contrário do checkout `pull_request` anterior, o run pós-merge testou
diretamente o merge commit `8a97ae14e8f84eb86fcacfaefed61f014830fbf9`.
O artefato formal registrou `tested_commit` e `source_head_commit` iguais a
esse merge commit; não há ambiguidade de proveniência neste snapshot.

## Ambiente e comandos oficiais

O workflow executou a instalação a partir do lock com Poetry `2.4.1` e Python
`3.11`. O Windows registrou `Python 3.11.9` em `Windows-10-10.0.26100-SP0`;
o Linux registrou CPython `3.11.16`. A validação Windows usou o runner
versionado por subprocesso por arquivo, sem filtros de seleção.

Foram executados pelo workflow, entre outros, os seguintes gates:

- verificação da baseline Git-blob;
- `tools/evidence_integrity.py --require-tracked --git-blob`;
- lock, compilação, lint, formatação, isort e mypy;
- pip-audit e Bandit;
- suíte integral com cobertura Linux;
- `tools/run_windows_coverage_shards.py` no Windows;
- `tools/check_coverage_policy.py`;
- `scripts/audit_stage4b5_quality.py`;
- `tools/run_formal_legacy_gate.py --group all`.

## Resultados pós-merge

### Linux

- job `100779319495`: `SUCCESS`;
- suíte: `1919 passed`, 1 warning, em `71.55s`;
- cobertura: `23890/25799` linhas (`92.60%`) e
  `6665/7838` branches (`85.03%`);
- baseline: `3213` arquivos verificados;
- evidência: `130` manifestos validados;
- política de cobertura, Stage 4B.5, tipos, segurança e árvore limpa:
  `PASS`.

### Windows 11 / runner oficial

- job `100779319836`: `SUCCESS`;
- runner: `ACCEPTED`, `189/189` arquivos;
- totais: `1919` testes, `0` falhas, `0` erros e `0` skips;
- duração do runner: `307.25s`;
- cobertura: `23890/25799` linhas (`92.60%`) e
  `6666/7838` branches (`85.05%`);
- baseline: `3213` arquivos verificados;
- evidência: `130` manifestos validados;
- política de cobertura, Stage 4B.5 e árvore limpa: `PASS`.

### Symlink e reconciliação legada

O JUnit Windows `039-test_integration_sync.xml` registrou `31` testes,
`0` falhas, `0` erros e `0` skips, incluindo os contratos
`test_plan_rejects_symlink_escape` e `test_plan_rejects_symlink_destination`.
Isso confirma o comportamento no commit integrado; a prova VMware do ZIP/patch
reconstruído permanece registrada separadamente e não é promovida a prova de
outro SHA.

O gate formal retornou `accepted=true` para o contrato atual e preservou o
resultado histórico bruto:

- histórico: `196` testes, `26` falhas, `0` erros, `0` skips, retorno `1`;
- reconciliação: `15` falhas exatas, `11` assinaturas divergentes,
  `12` ausências esperadas e `1` observação corrente ausente;
- substitutos: `42` testes, `0` falhas, `0` erros e `0` skips;
- snapshots legados: preservados byte a byte.

As `11` assinaturas e `12` ausências continuam sendo uma reconciliação formal
do contrato atual; não são apresentadas como aprovação do runner histórico.

## Artefatos remotos e hashes

Os artefatos externos do run foram preservados por ID e digest no pacote
`docs/evidence/artifacts/etapa7-post-merge-pr166-2026-09-03/`:

- Linux `validation-linux-python-3.11`: ID `9908775913`,
  `75858` bytes, digest
  `sha256:07398be2486114d9f3b87ed15bf8ba7f76c4f81657112279274bb79964d20bcb`;
- Windows `validation-windows-python-3.11`: ID `9909082655`,
  `63227454` bytes, digest
  `sha256:e6daf3250469a13e548fc14d4df6b4a08ffd0591ef730fa9f7411e68be62682a`;
- resumo Windows: `152985` bytes, SHA-256
  `20d9f0924375eb679238b1e66142890712010250d2d05fceb3e2f711dc02121f`;
- gate formal: `10743` bytes, SHA-256
  `bf7a68da069627348469ba37a15ee88a9e481040de8d729a38c0b98ab8e464d0`;
- JUnit de sincronização Windows: `4218` bytes, SHA-256
  `49aa9c07e80787a780c0417290c604cbe28db1cdb996a37f983f8ae1c2345612`;
- cobertura Linux: `1157539` bytes, SHA-256
  `49c5458dd509da069aaf6702a5e1b18ea13d61fb4115902d3c236143cc2f1c66`;
- cobertura Windows: `1184094` bytes, SHA-256
  `cdbe2eff22499a2ef77dc478434354c174fdac9c7bdb1032b361e7bcca240a62`.

O índice local registra os hashes e tamanhos do conteúdo versionado e os
digests dos artefatos externos. O validador de evidências deve continuar sendo
executado no commit que incorporar este snapshot.

## Limitações e rollback

- o runner histórico permanece `accepted=false` por preservação dos snapshots;
- a evidência VMware é scoped à reconstrução identificada do ZIP/patch e não
  substitui o CI do merge commit;
- este encerramento não valida engines externas, assinatura de código ou
  publicação de release;
- o plano global permanece `IN_PROGRESS` para escopos fora da PR `#166`;
- rollback técnico, se necessário, é reversível por `git revert -m 1
  8a97ae14e8f84eb86fcacfaefed61f014830fbf9`, após revisão e novo CI.

## Decisão

`POST_MERGE_GATE=PASS`

`PR_166_MERGED=YES`

`STAGE_7_CLOSED_IN_SCOPE=YES`

`GLOBAL_PLAN_CLOSED=NO`

`RELEASE_APPROVED=NO`

**Etapa 7 encerrada e aprovada somente no escopo técnico da PR #166.**
O merge e o CI pós-merge foram comprovados; nenhuma conclusão de release ou
aprovação global é derivada deste snapshot.
