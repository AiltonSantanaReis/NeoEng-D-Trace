# Evidência — Fase 4 — imagem, bordas, cache e assincronia

## Identificação

- Projeto: `NeoEng-D-Trace`
- Identificador: `P2D-COMP-01/LEGACY-26-RECON`
- Fase: `4 — imagem, edge map, cache, solver e ponte Qt`
- Data da coleta: `2026-09-01` (`America/Sao_Paulo`)
- Branch: `fix/legacy-27-functional-regressions`
- HEAD de entrada: `eaa28b9a75194d25741323b4b72911426a740349`
- Status: `VALIDAÇÃO STAGED CONCLUÍDA — COMMIT E RECONCILIAÇÃO DO MANIFEST PENDENTES`

Este documento registra o início verificável da Fase 4. Ele não declara
encerramento da fase, reconciliação global, aprovação do `P2D-COMP-01`, merge,
push ou release. O contrato novo e este relatório ainda não tinham blob
staged; por isso o contrato, o relatório e o baseline foram revisados e estão
no lote staged da Fase 4, mas ainda não foram commitados nem promovidos.

## Regras e governança consultadas

Antes de qualquer decisão ou edição foram relidos:

1. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
2. `docs/POLITICA_NAO_REGRESSAO.md`;
3. `docs/evidence/README.md`;
4. `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
5. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
6. `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`;
7. `quality/legacy_tests/manifest.json`;
8. `quality/legacy_tests/reconciliation.json`;
9. `tools/run_legacy_tests.py`;
10. evidências rastreadas das Fases 0, 1, 2 e 3.

Foram aplicadas as regras de imutabilidade dos snapshots históricos, ausência
de `skip`/`xfail` novo, proibição de substituir protocolos reais por mocks,
preservação de estado em erro, timeout explícito, descarte de respostas stale,
não alteração de exportadores e bloqueio de qualquer decisão desconhecida.

## Gate de entrada e fronteira

| Verificação | Resultado |
|---|---|
| HEAD/branch | Confirmados acima |
| Diff rastreado da produção na entrada | Vazio; após a correção: `src/tools/magnetic_lasso.py` modificado |
| `quality/legacy_tests` desde a âncora `3c287ac73925ef0ef33404da63de7401dee43913` | Vazio |
| Manifest histórico SHA-256 | `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` |
| Reconciliação histórica SHA-256 | `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493` |
| Integridade de evidências | `Evidence integrity passed: 121 manifests validated.` |
| Integridade da baseline | `Baseline verified: 3115 files` |
| Itens não rastreados preexistentes | `3331` no total; `55` manifests; preservados |
| Manifest novo não rastreado | Nenhum criado para maquiar resultado; o inventário preexistente foi preservado |

Nenhum snapshot, manifest histórico, reconciliação ou regra foi editado.
Nenhum arquivo não rastreado foi removido, limpo ou incorporado por inferência.

## Objetivo e escopo

A Fase 4 cobre os casos legados `#17`, `#18`, `#19`, `#20`, `#21`, `#22` e
`#27`, com separação entre:

- conversão de imagem real `ndarray`/`QImage`;
- construção, hit e invalidação do edge map/cache;
- solver determinístico NumPy/OpenCV;
- worker e sinais Qt reais;
- cancelamento, geração, stale e ordem de entrega;
- fechamento válido e fail-closed;
- fluxo end-to-end com `Scene`, `CommandManager`, `CanvasView`, imagem e
  histórico reais.

A alteração de produção foi limitada ao defeito close-safe reproduzido por
`CanvasView` real e resultado tardio. Os arquivos controlados nesta coleta são:

- `src/tools/magnetic_lasso.py`;
- `tests/test_legacy_phase4_contracts.py`;
- `docs/evidence/FASE4_IMAGEM_BORDAS_CACHE_ASSINCRONIA_2026-09-01.md`.

## Caracterização histórica preservada

Comando exato:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe tools\run_legacy_tests.py --file test_magnetic_lasso.py --file test_tools_integrated.py --timeout-seconds 120
```

Resultado bruto do runner:

```text
[FAILED] test_magnetic_lasso.py: tests=15 failures=6 errors=0 skipped=0
[FAILED] test_tools_integrated.py: tests=7 failures=7 errors=0 skipped=0
Reconciliation: failed matched=8/13 unexpected=5 missing=5
```

Totais: `22 testes`, `13 falhas`, `0 erros`, `0 skips`; o runner retornou `1`.
O relatório bruto permanece local em `%TEMP%\neoeng-d-trace-legacy-tests\20260901T180317Z\summary.json`;
SHA-256: `4D93ADDAC5A3F74C98C77C6B19D0D82D6C7D87F418782269BF9BDF26063169D1`.

As seis falhas do snapshot magnetic foram:

| Caso | Assinatura preservada | Interpretação |
|---:|---|---|
| #17 | `assert None is not None` em `_get_image_array` | `Mock` não é `QImage`/`ndarray` real |
| #18 | edge map `None` | cache não é construído de imagem falsa |
| #19 | um anchor em vez de dois | fixture espera resolução síncrona inexistente |
| #20 | preview vazio | fixture verifica antes da entrega assíncrona |
| #21 | `execute` chamado zero vezes | caminho legado não é anel válido sob sanitização estrita |
| #22 | caminho vazio | não há edge map válido para o solver |

O caso #27, em `test_tools_integrated.py`, permaneceu visível como falha de
mutação porque a fixture histórica usa `Mock` em vez do protocolo de
`Scene`/manager real. A reconciliação continua rejeitada e não foi editada.

## Substituto nativo executável

Arquivo: `tests/test_legacy_phase4_contracts.py`.

| Atributo | Valor |
|---|---:|
| SHA-256 | `84ED0686806BFC312B130A0E7EA210237B7B4DE8C0E119F328304734D48244D5` |
| Bytes | `17121` |
| Linhas | `541` |
| Mocks genéricos | `0` |
| `sleep`/timeout arbitrário | `0` |
| `skip`/`xfail` | `0` |

O teste usa `Scene`, `CommandManager`, `CanvasView`, `QApplication`,
`QImage`, `QMouseEvent`, `QThreadPool`, `_MagneticPathWorker`, sinais Qt e
OpenCV/NumPy reais. A espera usa `QEventLoop`/`QTimer` com prazo explícito;
um timeout de espera é falha do teste, não skip.

A cobertura por caso é:

- #17: ndarray real, QImage real, conversão e tipo inválido explícito;
- #18: cache miss, hit por identidade/hash, mutação no mesmo buffer,
  substituição no mesmo caminho e remoção;
- #19: worker real em `QThreadPool`, sucesso com endpoints e erro de entrada
  inválida, sem fabricar `CommandResult`;
- #20: preview entregue pelo worker Qt, cancelamento antes da entrega e
  descarte sem histórico;
- #20/timeouts: deadline real de segmento, Event cooperativo, payload tardio
  cancelado e preservação de Scene, seleção, preview e histórico;
- #19/#20: resposta stale/out-of-order não sobrescreve preview novo;
- #21: double-click Qt real fecha anel válido; polígono colinear permanece
  fora da cena e do histórico;
- #22: ausência de imagem retorna vazio fail-closed; edge map real permite
  solver com endpoints preservados;
- #27: imagem real → cache → eventos Qt → workers → Scene → CommandManager →
  undo/redo, com um objeto e uma entrada de histórico.

## Resultados executados

Focal pós-implementação, três execuções independentes:

```text
11 passed in 1.50s
11 passed in 1.48s
11 passed in 1.45s
```

Regressão relacionada:

O comando combinado dos snapshots históricos e do contrato substituto foi:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q quality\legacy_tests\tests\test_magnetic_lasso.py quality\legacy_tests\tests\test_tools_integrated.py tests\test_legacy_phase4_contracts.py
```

Resultado bruto: `20 passed, 13 failed` em `33` testes. As `13` falhas são
somente as assinaturas históricas já preservadas: `6` em Magnetic Lasso e `7`
em ferramentas integradas. Os `11` contratos nativos da Fase 4 passaram no
mesmo processo; nenhum snapshot foi modificado.

A suíte atual completa foi executada separadamente:

```text
1924 passed, 2 skipped, 1 warning in 48.76s
```

Os `2 skipped` e o warning são preexistentes em outros testes; não foram
introduzidos pelo contrato ou pela correção da Fase 4.

A primeira verificação da baseline staged retornou falha explícita: `Unexpected`
para o relatório e o teste novos, e `Changed` para os quatro arquivos alterados.
A correção foi regenerar `baseline_manifest.json` com `--write --git-blob` sobre
os mesmos bytes staged e incluí-lo no lote. Isso atualiza metadado da baseline
atual deliberadamente alterada; não altera snapshot histórico nem critério de
aceite.

Repetição final dos gates após a implementação:

- `py_compile`: exit `0`.
- `evidence_integrity.py --require-tracked --git-blob`: `121 manifests validated`.
- `baseline_integrity.py --verify --git-blob`: `Baseline verified: 3117 files`.
- Imutabilidade histórica desde a âncora: `git diff --quiet` passou.
- `git diff --check`: passou; o aviso de normalização CRLF/LF é informativo.
- Contratos nativos focais: `11 passed in 1.49s`.
- Regressão relacionada: `20 passed, 13 failed`; as 13 falhas são históricas e reproduzíveis.
- Suíte completa: `1924 passed, 2 skipped, 1 warning in 48.76s`.

## Correção close-safe baseada em reprodução

A caracterização anterior usou `CanvasView` real, `DeferredDelete` real e um
resultado de preview com geração vigente. Antes da correção, o callback tardio
atingia `canvas_view.update()` após a destruição e a reprodução passou ao
capturar `RuntimeError`. Após a correção, a mesma caracterização foi convertida
em contrato positivo e passou sem exceção.

A alteração de produção:

- conecta `MagneticLassoTool` ao sinal `QWidget.destroyed` quando o canvas é
  realmente um `QWidget`;
- invalida revisão, requests enfileirados, busy state e referências de cursor
  no descarte;
- descarta o resultado tardio antes de consultar imagem ou chamar o widget;
- impede que `cancel()` atualize um canvas já destruído.

O contrato verifica adicionalmente que Scene, histórico e preview não sofrem
mutação após o fechamento. Nenhum Mock genérico foi usado para esse fluxo.

## Auditoria formal do requisito de timeout

Na entrada, a inspeção dos settings, do worker, da ponte e das regras encontrou somente
`preview_interval_ms`, limites de busca e prazos dos harnesses de teste. Não
existia então um orçamento temporal de produção, watchdog, sinal de timeout ou
política definida para cancelar uma busca que exceda esse orçamento. O prazo
de `QEventLoop` usado nos testes é um limite de espera explícito: se a entrega
não ocorrer, o teste falha; ele não inventa um timeout de produto.

A análise de entrada rejeitava implementar um valor arbitrário ou reutilizar
`preview_interval_ms` como prazo do worker sem decisão de produto.
Na entrada, o requisito estava `BLOQUEADO`, com falha explícita e sem skip.
A decisão formal abaixo define orçamento, cancelamento, estado preservado,
mensagem e observabilidade antes da nova execução dos gates.

## Medição real e aprovação inicial dos deadlines

A medição foi executada depois do gate de entrada, com QApplication real em
modo offscreen, QThreadPool real, worker de produção, OpenCV/NumPy e imagem
sintética determinística. Foram coletadas cinco amostras por finalidade e
imagem; p95 é o percentil empírico da amostra, não uma garantia estatística
de produção. Cada entrega teve guard de 15.000 ms por QEventLoop/QTimer.

| Imagem / SHA-256 | Edge cache max/p95 ms | Solver max/p95 ms | Worker max/p95 ms | Entrega Qt max/p95 ms |
|---|---:|---:|---:|---:|
| 160x160 / 48aadc208b98817d49dde6ee25f16ca079f3be697dd125b225cb35c372149ca3 | 22.792 / 22.792 | 170.512 / 170.512 | 172.422 / 172.422 | 169.464 / 169.464 |
| 512x512 / 51b2c242ae5b70193cab0d345fe0d73416e9a3a5b4f910cb3b1bedd51bc466b4 | 5.497 / 5.497 | 1395.224 / 1395.224 | 1458.584 / 1458.584 | 1410.252 / 1410.252 |
| 1024x1024 / 6810f2f5fca82a581cb566aae39cf6d0b4c01a09929b12519882c65f4fa72d83 | 19.115 / 19.115 | 2387.253 / 2387.253 | 2359.486 / 2359.486 | 2411.620 / 2411.620 |

A coleta orientada por finalidade registrou os seguintes máximos/p95:

| Imagem | prepare ms | preview ms | segment ms | finish ms |
|---|---:|---:|---:|---:|
| 160x160 | 1.661 / 1.661 | 18.735 / 18.735 | 182.603 / 182.603 | 179.730 / 179.730 |
| 512x512 | 5.838 / 5.838 | 110.855 / 110.855 | 1561.716 / 1561.716 | 1399.083 / 1399.083 |
| 1024x1024 | 18.342 / 18.342 | 171.447 / 171.447 | 2406.380 / 2406.380 | 2420.974 / 2420.974 |

A decisão de engenharia registrada para esta implementação é: prepare=100 ms,
preview=500 ms, segment=5.000 ms e finish=5.000 ms. Os valores têm margem
aproximada de 2x sobre o pior observado da finalidade correspondente em
1024x1024; são defaults iniciais medidos, sujeitos a telemetria posterior,
não uma alegação de p99. Os clamps aceitos são prepare 20–5.000 ms, preview
50–10.000 ms e segment/finish 50–30.000 ms.

## Contrato de timeout e cancelamento implementado

Cada worker recebe um Event próprio e expõe cancel(). O worker verifica o
evento antes/depois da preparação e durante a busca A*, Dijkstra ou refinamento
periódico; o payload inclui cancelled e elapsed_ms. A ferramenta arma um QTimer
single-shot por request e seleciona o deadline pelo propósito prepare, preview,
segment ou finish.

Ao expirar, o fluxo cancela cooperativamente todos os workers, interrompe o
timer, incrementa a revisão, descarta request ativo/enfileirado, libera busy e
preserva anchors, último preview válido, Scene e CommandManager. O erro fica
registrado como purpose: Timeout after N ms e a notificação visual é aberta
de forma não bloqueante para não travar o event loop que precisa entregar a
resposta tardia. A resposta posterior continua stale por revisão/cancelled e
não pode mutar o estado.

O caminho síncrono para adapters que não são QWidget não foi alterado. Nenhum
worker foi forçado a terminar, nenhum snapshot histórico foi modificado e
nenhum skip/xfail/mock genérico foi introduzido.

## Testes reais de timeout e resposta tardia

O teste test_phase4_real_segment_timeout_cancels_and_discards_late_result usa
Scene, CanvasView, CommandManager, QApplication, QThreadPool, QTimer,
QMessageBox não bloqueante, ndarray 1024x1024 e solver de produção. Ele
observa o timeout de 50 ms, confirma revisão/busy/âncoras/preview/histórico,
confirma Event sinalizado, aguarda o payload tardio real e exige
cancelled=True e elapsed_ms >= 50 ms. A resposta tardia é verificada novamente
após a remoção do worker. O teste de fechamento continua cobrindo
DeferredDelete/QWidget.destroyed e descarte fail-closed.

## Classificação da Fase 4 — registro da entrada (preservado)

- `CORRIGIDO/NO_CHANGE`: conversão de imagem, cache, solver, worker, sinais,
  cancelamento, stale/out-of-order, fechamento fail-closed e end-to-end dos
  casos `#17`, `#18`, `#19`, `#20`, `#21`, `#22` e `#27`.
- `BLOQUEADO`: timeout de worker de produção sem contrato temporal aprovado.
- `NÃO ENCERRADA`: a saída obrigatória da Fase 4 exige solver, cache, worker e
  integração aprovados, mas também exige tratar explicitamente timeout.
- `NÃO AUTORIZADO`: commit, push, merge ou declaração de aprovação global antes
  da decisão e implementação verificável do timeout.

Os arquivos de teste e evidência continuam sem conteúdo staged/rastreado até o
gate formal de staging. A integridade do Git-blob e a auditoria do manifest
não rastreado devem ser executadas novamente nesse gate; não há incorporação
automática por inferência.

## Estado atual da Fase 4

A implementação de deadlines, watchdog por request, cancelamento cooperativo
e teste de resposta tardia foi aplicada. Compilação, gates de evidência/baseline,
imutabilidade histórica, diff-check, suíte completa e três focais passaram.
O staging seletivo e a baseline da mesma fronteira também passaram. O fechamento
formal ainda depende da reconciliação do manifest não rastreado e do commit;
a Fase 5 não foi iniciada.

## Auditoria de consistência do pacote

A auditoria do gate detectou que uma versão inicial deste relatório afirmava
cobertura do caso `#27`, embora o arquivo de teste então coletasse somente oito
casos e não contivesse a função correspondente. A inconsistência foi corrigida
antes desta consolidação: o caso foi incorporado com fluxo real completo, o gate
passou a coletar dez testes, e o hash/bytes/linhas foram recalculados.

Uma execução preliminar apontou caminhos inexistentes em `tests\` e retornou
erro de coleta sem executar testes. Esse resultado não foi usado como evidência;
os caminhos reais em `quality\legacy_tests\tests\` foram então executados e
produziram o resultado combinado registrado acima.

Nenhuma falha histórica foi removida, reescrita ou convertida em skip/xfail.

## Inventário corrente do manifest não rastreado

Após os gates, o inventário local retornou `3332` itens não rastreados e `63`
caminhos terminados em `manifest.json`; nenhum desses manifests possui timestamp
de `2026-09-01` na coleta corrente. A diferença em relação ao registro de entrada
`3331`/`55` não será normalizada por inferência: permanece item de reconciliação
formal antes do staging, sem remoção, sobrescrita ou incorporação automática.
