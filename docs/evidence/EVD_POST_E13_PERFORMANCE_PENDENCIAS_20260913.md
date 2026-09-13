# Evidência pós-E13 — pendências de desempenho estrutural

**ID da feature:** `AUD-POST-E13-PERFORMANCE-PENDENCIAS-20260913`
**Status:** `IN_PROGRESS`
**Data:** 2026-09-13
**Requisito:** `REQ-POST-E13-VIEWPORT-SCALE-20260913`
**Contrato:** `DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md`

## Resultado comprovado

A [auditoria de baseline](AUDITORIA_POST_E13_PERFORMANCE_BASELINE_20260913.md)
executou a matriz completa no relatório
`artifacts/audit-post-e13-performance-20260913-r9/o2-after-isolation-cache-fix-clean.json`
(SHA-256
`3F7E6DEE0EC8088C69E452EC089B616AA59BCD0A7DDD7A30A36C3504A57531A8`).
Foram observados `26/26` workloads, `0` erros de operação, `0` falhas de
determinismo e `20` observações de memória por workload.

Nas cargas de `512` objetos únicos em `1920×1080`, as correções anteriores
reduziram o p95 em `61,72%`–`71,51%` contra r5, mas o p95 residual ainda ficou
entre `249,28 ms` e `398,73 ms`. Portanto, a responsividade estrutural em alta
escala permanece `FAIL`; a redução não pode ser promovida a `PASS` por si só.

## Lacunas mantidas

- **Memória longa:** `PENDING_EVIDENCE`; as 20 observações curtas não são soak
  prolongado nem prova de estabilidade nativa.
- **GPU/janela nativa:** `PENDING_EVIDENCE`; o caminho `QGraphicsView` medido
  não fornece contador integrado e o benchmark não inventa um valor.
- **Equivalência runtime:** permanece separada das medições estruturais e não
  é concluída por CuPy ou pelo smoke portátil.

O CuPy foi medido e classificado como opcional, mas o perfil causal aponta
reconstrução/snapshot/repintura do viewport, não um hot spot demonstrado no
kernel X-Ray. As alterações de logging CuPy e retry do atlas não mudam esse
caminho; por isso não há rerun de desempenho artificial nesta etapa.

## Decisões isoladas no final

1. autorizar um novo contrato de desempenho para otimizar a reconstrução/
   snapshot residual, com perfil causal, equivalência visual/funcional,
   benchmark antes/depois e nova captura; ou aceitar formalmente o limite
   atual para este ciclo;
2. autorizar soak controlado de memória e instrumentação GPU/janela em ambiente
   dedicado, ou manter esses gates como `PENDING_EVIDENCE`.

Sem uma dessas decisões e seus testes correspondentes, esta evidência deve
permanecer `IN_PROGRESS`. Nenhum threshold foi reduzido e nenhum finding foi
apagado.

## Decisões recebidas em 2026-09-13

O responsável pelo projeto aceitou formalmente o limite estrutural medido para
este ciclo e autorizou ambiente dedicado para soak de memória/GPU e qualificação
de licensing/shutdown do Unity. A decisão está registrada em
`docs/evidence/DECISAO_POST_E13_LIMITE_PERFORMANCE_SOAK_CONTROLADO_20260913.md`.

O valor observado continua sendo `FAIL` no relatório r9; a aceitação é uma
decisão de escopo, não uma promoção artificial para `PASS`. Não haverá alteração
de threshold nem nova otimização estrutural nesta etapa. O gate de soak passa a
`IN_PROGRESS` e será fechado somente com evidência controlada, mantendo GPU e
Unity como `NOT_APPLICABLE`/`PENDING_EVIDENCE` quando a instrumentação ou o
runtime real não estiverem disponíveis.

## Resultado após a autorização formal

O soak controlado de memória foi concluído com `PASS` no relatório r2:
`26/26` workloads, `0` erros, `0` determinismos falsos, `250` ciclos por carga e
RSS/private observados em todas as cargas. A evidência completa, incluindo
limitações e hashes, está em
`docs/evidence/EVD_POST_E13_SOAK_MEMORIA_GPU_CONTROLADO_20260913.md`.

O gate de memória longa passa a `PASS` para o ambiente controlado qualificado.
O gate GPU deste caminho passa a `NOT_APPLICABLE`, pois a probe com
`--gpus all` não recebeu dispositivo NVIDIA e o `QGraphicsView` não expõe
contador GPU; isso não é uma aprovação de desempenho GPU. O limite estrutural
medido continua `FAIL` no relatório e `APPROVED_BY_OWNER` como decisão de escopo.

O gate restante desta frente é a execução real de licensing/shutdown do Unity em
ambiente Windows dedicado. A primeira tentativa controlada está registrada como
`BLOCKED` em
`docs/evidence/EVD_POST_E13_UNITY_CONTROLADO_SANDBOX_20260913.md`: uma VM
Windows Sandbox preexistente manteve o recurso ocupado, a fixture não foi
montada e nenhum Unity foi executado. A classificação de logs históricos
permanece `PASS` funcional com ambiente limpo/shutdown `PENDING_EVIDENCE`; não
houve execução nativa do Unity neste host.
