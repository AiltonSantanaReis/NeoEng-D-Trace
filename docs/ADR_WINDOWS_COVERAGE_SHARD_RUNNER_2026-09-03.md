# ADR — Runner Windows de cobertura por subprocessos

**ID:** ADR-WIN-COVERAGE-SHARDS-2026-09-03
**Status:** `ACTIVE — INTEGRATED IN MAIN`
**Data:** 2026-09-03
**Escopo:** execução oficial do job Windows do CI; não altera o produto, o
threshold, a suíte histórica ou os snapshots legados.

## Dependências normativas

- [Governança de integridade](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md);
- [Política de qualidade e evidências](POLITICA_QUALIDADE_E_EVIDENCIAS.md);
- [Plano de correção das falhas legadas](PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md), Fase 7;
- [Matriz de riscos](MATRIZ_RISCOS_ESTABILIZACAO.md), R-009;
- [Workflow oficial](../.github/workflows/ci.yml).

## Contexto e evidência de diagnóstico

Na candidata anterior, a execução única do pacote completo no Windows 11 com
PySide6, `QT_QPA_PLATFORM=offscreen` e cobertura de branches abortou o processo
Python durante a sequência de módulos Qt, com violação de acesso/abort nativo.
Execuções focadas passaram, mas isso não prova estabilidade; a política exige
tratar o comportamento como falha até a causa operacional ser isolada.

Uma execução diagnóstica posterior, sem alteração da suíte, executou os 188
arquivos oficiais em processos independentes, acumulou a mesma cobertura e
obteve `1914` testes, `0` falhas, `0` erros e `2` skips. O relatório permanente
da candidata que contém essa execução deve registrar o hash do commit, ambiente,
comando e limitações; esta ADR não transforma a saída externa do diagnóstico em
evidência de integração remota.

## Decisão

O job Windows utilizará `tools/run_windows_coverage_shards.py`. O executor:

1. descobre todos os arquivos top-level `tests/test_*.py` em ordem determinística;
2. inicia um subprocesso Python/pytest novo para cada arquivo;
3. mantém `--cov=src`, `--cov-branch` e o threshold previamente definido em 90%;
4. usa `--cov-append` somente após o primeiro shard;
5. gera JUnit e log por shard e um `summary.json` externo;
6. gera `coverage.xml` e aplica `--cov-fail-under=90` apenas no último shard;
7. falha fechado em erro, timeout, abort nativo, JUnit ausente ou cobertura final ausente;
8. não usa `-k`, `--ignore`, skip adicional, `xfail`, `continue-on-error` ou
   redução de escopo.

O Linux mantém o executor único atual. O runner legado continua sendo chamado
separadamente pelo gate formal e os snapshots `quality/legacy_tests/manifest.json`
e `quality/legacy_tests/reconciliation.json` não são tocados.


## Atualização de verificação pré-merge — 04/09/2026

O CI remoto da PR `#168`, run `33863522514`, confirmou os jobs Linux e
Windows sobre o HEAD documental `ac96825fa36edf686a173f7fad9e51d9ff41705d`.
Todos os passos do runner Windows, inclusive os shards de cobertura e a
política de cobertura, passaram. Naquele estado pré-merge, a decisão permanecia
`CANDIDATE ONLY`; a confirmação remota não autorizava merge, tag ou release.

## Comparação e impacto


Antes, o job Windows fazia uma única chamada `pytest` para a suíte inteira e
produzia `coverage.xml` na raiz. Depois, a mesma seleção oficial é distribuída
por arquivo em subprocessos isolados; a saída é `${RUNNER_TEMP}/windows-coverage`
e o gate de política aponta para o XML final desse diretório. O custo é maior
tempo de inicialização, compensado pela eliminação do estado Qt compartilhado
que causou o abort observado. O resultado permanece bloqueado até o CI remoto
confirmar o SHA candidato.

## Atualização pós-merge — 04/09/2026

A PR `#168` integrou a decisão desta ADR em `main` pelo merge commit
`9a25f0be0ea47a092e90c0194797ddcaf33a7dcf`. O CI pós-merge
`33871734689` confirmou o runner Windows de cobertura e a política de
cobertura como `PASS`. A decisão permanece ativa no código integrado; tag e
release continuam fora do escopo desta ADR.

## Verificação e aprovação

- testes unitários do construtor, descoberta e leitura JUnit: incluídos no lote;
- prova diagnóstica integral dos 188 shards: registrada separadamente, sem
  alterar snapshots;
- gates completos, empacotamento e CI remoto: obrigatórios antes de merge/tag/
  release;
- aprovação operacional: solicitação explícita do proprietário em 2026-09-03;
  isso autorizou a candidata técnica; a integração posterior da PR `#168` está
  registrada no adendo pós-merge.
