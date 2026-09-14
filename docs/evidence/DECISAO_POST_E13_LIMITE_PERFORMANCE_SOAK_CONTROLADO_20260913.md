# Decisão e autorização — limite estrutural e soak controlado pós-E13

**ID:** `DECISAO-POST-E13-LIMITE-PERFORMANCE-SOAK-CONTROLADO-20260913`
**Data:** 2026-09-13
**Checkout auditado:** `5c85abe3c2c3127a00e985df3c6a617649bea5c`
**Governança relida:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**SHA-256 da governança nesta etapa:** `D933DB005B7110C391CF776CDA3014CE348D61A91A5E9902AEEA619185EC3EA0`

## Decisões humanas recebidas

### 1. Limite estrutural de responsividade

**Decisão:** `APPROVED_BY_OWNER` — limite aceito formalmente para este ciclo.

O relatório corrente mediu a matriz completa com `26/26` workloads, zero erros de
operação e zero falhas de determinismo. Na carga de `512` objetos únicos em
`1920×1080`, o p95 residual ficou entre `249,28 ms` e `398,73 ms`, depois de
redução de `61,72%`–`71,51%` contra o r5. A medição normativa continua registrada
como `FAIL` no relatório; esta decisão não a converte em `PASS`, não reduz
thresholds e não autoriza afirmar meta de 60 FPS nessa escala. Ela encerra apenas
o gate de decisão de otimização deste ciclo, sem alteração de código.

Fonte: `artifacts/audit-post-e13-performance-20260913-r9/o2-after-isolation-cache-fix-clean.json`
SHA-256: `3F7E6DEE0EC8088C69E452EC089B616AA59BCD0A7DDD7A30A36C3504A57531A8`

### 2. Soak de memória/GPU e diagnósticos Unity

**Decisão:** `AUTHORIZED_CONTROLLED_ENVIRONMENT` — executar qualificação
dedicada em ambiente isolado, usando Docker Desktop e, quando indispensável para
Unity nativo, uma sandbox/VM Windows dedicada.

O escopo autorizado é:

- soak prolongado da memória no caminho real do editor (`QApplication`,
  `SceneAuthoringSession` e `SceneAuthoringViewport`), com fonte montada como
  somente leitura e saída isolada;
- instrumentação GPU somente quando houver contador real e identificável; se o
  caminho `QGraphicsView` não expuser telemetria GPU, o resultado deve permanecer
  `NOT_APPLICABLE` ou `PENDING_EVIDENCE`, sem valor inventado;
- qualificação de licensing e shutdown do Unity apenas em ambiente dedicado,
  com logs e estado de processo preservados, sem executar Unity, `-quit`,
  encerramento de processo ou shutdown do sistema neste host;
- nenhuma repetição do teste definitivo de symlink, que já está qualificado e só
  deve ser reexecutado após mudança relevante em seu contrato, guard, runner,
  dependências, digest ou evidência.

## Critérios de fechamento

O soak de memória só poderá ser promovido a `PASS` se o runner registrar o número
de iterações, observações inicial/final/pico, zero erro de operação, determinismo
preservado e hashes dos artefatos. A observação continua sendo evidência de
estabilidade do ciclo; não será descrita como prova isolada de ausência de leak.

A qualificação GPU só poderá ser `PASS` se medir o caminho que se pretende
qualificar e registrar dispositivo, backend, contador e método. Ausência de
contador será uma limitação explícita.

A qualificação Unity só poderá declarar ambiente limpo ou shutdown limpo com uma
execução real dentro do ambiente controlado autorizado. A classificação dos logs
históricos permanece válida, mas não substitui essa execução; sinais como Code 10,
token, Curl, `abort_threads` e `MemoryLeaks` devem continuar visíveis.

## Estado desta decisão

- aceite formal do limite estrutural: `PASS`;
- autorização do ambiente dedicado: `PASS`;
- soak controlado de memória/GPU: `IN_PROGRESS`;
- Unity licensing/shutdown limpo: `PENDING_EVIDENCE` até existir runtime Unity
  controlado executável e licenciado;
- checkpoint de retorno preservado: tag `checkpoint/post-e13-pre-gizmo-20260912`;
- nenhum artefato histórico foi removido.
