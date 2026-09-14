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

- **Memória longa:** `PASS` no ambiente controlado; o relatório dedicado registra
  26 workloads, 250 ciclos por workload e observações de RSS/private.
- **GPU/janela nativa:** o workload CUDA dedicado está `PASS` no escopo
  controlado, mas o contador de frames/GPU do caminho
  `QGraphicsView` continua `NOT_APPLICABLE`; não há equivalência de renderer ou
  FPS declarada.
- **Equivalência runtime:** permanece separada das medições estruturais e não
  é concluída por CuPy ou pelo smoke portátil.

O CuPy foi medido e classificado como opcional, mas o perfil causal aponta
reconstrução/snapshot/repintura do viewport, não um hot spot demonstrado no
kernel X-Ray. As alterações de logging CuPy e retry do atlas não mudam esse
caminho; por isso não há rerun de desempenho artificial nesta etapa.

## Decisões que estavam abertas antes da qualificação controlada

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

O gate de memória longa permanece `PASS` para o ambiente controlado qualificado.
O gate do workload GPU dedicado também é `PASS` no escopo CUDA controlado: a
qualificação em container sem rede executou 36.408 operações em 20 segundos,
coletou 38 amostras reais e observou até 91% de utilização na RTX 3070 Ti, sem
erros. O contador de frames/GPU do `QGraphicsView` continua `NOT_APPLICABLE`,
porque o caminho do editor é offscreen/software e não oferece essa métrica; isso
não é uma aprovação de equivalência visual ou de FPS do editor. O limite
estrutural medido continua `FAIL` no relatório e aceito formalmente como decisão
de escopo.

## Resultado corrente após o r16

O r16 foi concluído em Windows Sandbox descartável após login e confirmação
manual do proprietário. Unity `6000.5.7f1` foi o editor efetivamente executado;
`6000.6` não apareceu no mount persistente e não é atribuído a este resultado.
O processo iniciou sem timeout, executou o método do pacote e retornou `0`.

O relatório `package-report.json` registra `com.neoeng.dtrace` `0.3.0`,
`SourcePolicy=source-only` e `7/7` checks aprovados. Portanto, o gate de
execução real e o contrato do pacote são `PASS` no escopo controlado.

O gate de licensing limpo permanece `BLOCKED`: `Unity Personal`/`Unlimited` foi
resolvido, mas `Code 10`, token indisponível, WMI e `Curl error 42` foram
observados e preservados. O gate de shutdown limpo do Unity também permanece
`BLOCKED`: houve quit de batchmode, saída de batchmode e retorno `0`, porém o
marcador textual `Shut down.` não apareceu e havia 29 entradas de processos
compatíveis antes do descarte, sem nomes individualizados. O shutdown/descarte
da Sandbox é `PASS` somente no escopo da VM descartável; a segurança do host é
`PASS`, pois nenhuma operação perigosa foi executada nativamente.

O relatório detalhado, os hashes e a regra de não repetição estão em
`docs/evidence/EVD_POST_E13_UNITY_R16_RESULTADO_20260914.md`.

Assim, esta evidência geral permanece `IN_PROGRESS`. As únicas lacunas técnicas
reais desta frente são licensing limpo e shutdown limpo do Unity; a importação
nativa do asset 3D destinado ao Unity é uma pendência separada do relatório do
asset e não foi mascarada por este r16.
