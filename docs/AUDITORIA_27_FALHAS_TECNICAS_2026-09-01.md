# Auditoria técnica das 27 falhas legadas — 2026-09-01

## Escopo e evidência

A reprodução foi executada no branch `fix/legacy-27-functional-regressions`, sobre o commit base `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`, usando o comando canônico:

```text
.\.venv\Scripts\python.exe tools\run_legacy_tests.py --group all
```

Baseline bruta: 196 testes, 27 falhas, 0 erros e 0 skips. A reconciliação anterior marcou 27/27 assinaturas, mas isso apenas confirma divergências históricas; não confirma correção do produto.

Os contratos atuais substitutos foram executados com 163 passados após as correções desta branch. A reprodução legada final registrou 26 falhas, 0 erros e 0 skips em 196 testes; um dos 27 casos históricos passou, e os demais divergiram agora sem o `TypeError` secundário de Qt e sem recursão infinita no congelamento de estado. O relatório bruto final está em `%TEMP%\neoeng-legacy-27-final-20260901\summary.json`.

## Correções de produto aplicadas

- `src/core/commands.py`: `_freeze_state` passou a detectar ciclos no caminho ativo, manter referências compartilhadas acíclicas com a semântica anterior, ordenar coleções por representação estável e ignorar somente `cmd`/`_listeners` nos objetos reais; em `unittest.mock`, também ignora os internals privados do mock. Isso impede recursão infinita sem descartar estado privado legítimo; não transforma um mock em `Scene`.
- `src/tools/base_tool.py`: diálogos usam o parent apenas quando ele é realmente `QWidget`. Em adapters headless, a operação preserva `_last_error` e registra no logger sem abrir modal. Exceções de comando continuam sendo falhas e agora recebem traceback no log.
- `src/tools/pen_tool.py`: os caminhos de erro e rejeição usam o mesmo tratamento seguro, preservando o símbolo `QMessageBox` para compatibilidade de módulo e o comportamento visual quando há QWidget real.
- `src/tools/magnetic_lasso.py`: a imagem é buscada pelo primeiro adapter que realmente fornece um getter chamável; o fallback para `model.get_image()` não é escondido por um atributo dinâmico `scene`. As mensagens headless usam o mesmo caminho não modal.
- Nenhuma alteração foi feita para mudar o contrato de float32 do Sobel, remover a rotação do atlas, aceitar geometria inválida, restaurar zoom 1:1 ou elevar artificialmente o número padrão de pontos da curvatura.

## Matriz dos 27 casos

| # | Caso | Diagnóstico verificável | Decisão |
|---:|---|---|---|
| 1 | `convex_decompose_l_shape` | Fixture de sete vértices tem auto sobreposição; triangulação preservadora rejeita a geometria. | Não corrigir afrouxando validação. Cobertura substituta rejeita fixture inválido e valida L válido. |
| 2 | `ear_clipping_concave_l_shape` | Mesma auto sobreposição; aceitar produziria triângulos incorretos. | Manter rejeição estrita; usar triangulação válida e independente da orientação. |
| 3 | `edge_utils.test_sobel_magnitude` | Expectativa histórica exige float64; pipeline aprovado usa float32 sem clipping. | Não alterar dtype; contrato atual cobre precisão operacional, finitude e ausência de clipping. |
| 4 | `exporters.test_atlas_rotation` | Expectativa histórica exige dois atlas porque rotação não existia; implementação atual acomoda os dois sprites em um. | Não regredir rotação; contrato atual verifica dimensões físicas e metadados. |
| 5 | `handle_move_undo_redo` | Fixture cria polígono colinear de três pontos; `Scene` rejeita corretamente. | Não aceitar polígono inválido; histórico Bézier é coberto com geometria válida. |
| 6 | `lasso.test_mouse_release_commits_selection` | Canvas/Scene são `Mock`; o manager mock não retorna `CommandResult`. Após a correção, a seleção é preservada em vez de limpa após commit não confirmado. | Não fabricar sucesso; modernizar fixture para CanvasView/Scene reais. |
| 7 | `pen.test_commit_selection_valid` | Modelo usa `Mock` sem manager válido; criação não pode ser confirmada. | Manter falha visível e estado; testar com Scene/CommandManager reais. |
| 8 | `pen.test_double_click_commit` | Mesmo fixture sem contrato de manager; nós permanecem para recuperação quando o commit falha. | Preservar estado; substituir fixture. |
| 9 | `polygonal_lasso.test_double_click_commits_selection_with_enough_vertices` | Mock de Qt/Scene não representa o caminho de criação atual. | Substituir por teste com objetos reais, sem limpar seleção em falha. |
| 10 | `polygonal_lasso.test_commit_selection_converts_to_integers` | Mesmo desacoplamento do contrato de comando. | Manter normalização e validar via CommandManager real. |
| 11 | `rect_selection.test_mouse_release_commits_selection` | Fixture usa Mock como parent e Scene; commit não é confirmado. | Não adicionar compatibilidade fictícia; usar CanvasView/Scene reais. |
| 12 | `ellipse_selection.test_mouse_release_commits_selection` | Mesma causa do retângulo. | Mesma decisão. |
| 13 | integração `lasso_tool_with_commands` | `Scene` é Mock parcial; snapshot/execução exige campos e métodos reais. | Não alterar comando para aceitar objeto incompleto; usar Scene real. |
| 14 | integração `polygonal_lasso_with_commands` | Mesmo protocolo de Scene incompleto. | Mesma decisão. |
| 15 | integração `ellipse_tool_with_commands` | Mesmo protocolo de Scene incompleto. | Mesma decisão. |
| 16 | integração `multiple_operations_undo_redo` | Stack usa manager real sobre Scene falso; não há mutação/seleção compatível. | Validar sequência com objetos reais; não simular undo/redo parcial. |
| 17 | `magnetic.test_get_image_array` | Mock genérico apenas imita QImage; adapter atual aceita ndarray ou QImage real. | Não aceitar Mock como imagem; usar QImage/ndarray reais. |
| 18 | `magnetic.test_compute_edge_map` | Sem imagem válida não há cache de bordas determinístico. | Preservar fail-closed; testar cache com imagem real. |
| 19 | `magnetic.test_mouse_press_computes_path_between_anchors` | Fixture depende de imagem falsa e pressupõe resolução síncrona; pipeline atual não pode confirmar segmento sem cache. | Não remover assincronia/validação; testar entrega determinística do engine. |
| 20 | `magnetic.test_mouse_move_updates_preview` | Preview é separado e pode ser assíncrono; fixture verifica antes da entrega e sem imagem válida. | Testar worker/ponte ou solver determinístico, não estado prematuro. |
| 21 | `magnetic.test_double_click_closes_selection` | Caminho legado não forma polígono fechado válido sob o sanitizador estrito e o manager é Mock. | Não executar comando inválido; testar fechamento com caminho válido. |
| 22 | `magnetic.test_compute_magnetic_path_with_edge_map` | Edge map não é construído de Mock; solver retorna vazio corretamente. | Manter rejeição sem cache válido; usar imagem real. |
| 23 | `mask_utils_curvature.test_circle_contour` | Expectativa histórica exige `>=8` pontos por padrão; contrato atual torna piso explícito via `min_points=8`. | Não aumentar simplificação padrão artificialmente; cobrir piso opt-in. |
| 24 | `mask_viewer.test_reset_view` | Expectativa histórica exige zoom 1.0; contrato atual preenche e centraliza viewport. | Não regressar reset; manter teste de fill/center. |
| 25 | integração `pen_tool_with_commands` | Grafo interno recursivo de Mock causava `RecursionError`; correção tornou serialização finita, mas o fake Scene continua inválido. | Defeito real de robustez corrigido; não adaptar comando ao Mock. |
| 26 | integração `rect_tool_with_commands` | Fake Scene não implementa mutação, seleção e retorno exigidos pelo comando. | Modernizar fixture; não fazer fallback que bypassa histórico. |
| 27 | integração `magnetic_lasso_with_commands` | Caminho síncrono falso, imagem ausente e Scene incompleta não representam pipeline validado. | Testar engine/imagem/Scene reais; não fabricar objeto no mapa do Mock. |

## Resultado da auditoria

Os 27 itens não são 27 bugs de produto equivalentes. Há seis causas de conflito explícitas com contratos atuais ou fixtures geométricos inválidos, cobrindo sete ocorrências (#1, #2, #3, #4, #5, #23 e #24; #1 e #2 compartilham a mesma causa), dezessete ocorrências de fixtures/API históricos incompletos (#6–#22), e três integrações com protocolo de `Scene` incompleto ou serialização problemática (#25–#27). Foram corrigidos dois pontos reais de robustez: a recursão do snapshot (#25) e o tratamento de diagnóstico Qt, que mascarava a exceção original durante adapters headless. Os demais casos continuam falhando de forma visível porque o harness legado não fornece os objetos, imagens ou entrega assíncrona exigidos pelo contrato atual.

A reconciliação histórica deve permanecer falhando enquanto registrar assinaturas antigas que foram corretamente substituídas por falhas visíveis/estado preservado. Atualizar essa reconciliação ou os snapshots só deve ocorrer em uma mudança formal de harness, com testes reais equivalentes e revisão explícita; não é parte deste patch e não foi feito para obter pass.

Não há decisão de merge neste ponto: a suíte oficial, cobertura, lint, formatação, import ordering, mypy, auditoria de dependências, Bandit e baseline passaram. O gate de evidências do workspace permanece bloqueado por um `manifest.json` não rastreado pré-existente. O runner legado final tem 26 falhas restantes; a reconciliação ainda espera 27, com 15 correspondências, 11 assinaturas alteradas e 12 esperadas ausentes. Falta a revisão formal do harness/reconciliação; nenhum merge foi feito.
