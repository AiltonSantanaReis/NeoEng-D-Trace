# Decisão P2D-03B — Operações de edição, histórico e clipboard

**Status:** ACCEPTED / CLOSED — implementação e qualificação aprovadas pelo proprietário
**Data:** 29/08/2026 (UTC-03)
**Etapa:** P2D-03B
**Baseline de entrada:** `24a3178d52f1096e55c73b40daf196bccfe0d8cc`
**Branch:** `modernization/multiaxis-ui`
**Rollback de entrada:** retornar ao commit de entrada, sem alterar C3, o editor legado ou os artefatos remotos.

## 1. Finalidade

Definir, antes de qualquer código, o contrato verificável para tornar o editor profissional de composição 2D produtivo em operações de edição: nudge por teclado, duplicate, delete, copy/paste e undo/redo.

Este documento registrou a proposta de engenharia e a condição de autorização. O proprietário registrou o aceite explícito na seção 9; a implementação permanece limitada à fronteira aprovada. Se qualquer escolha for rejeitada posteriormente, a decisão deverá ser atualizada antes de nova mutação.

## 2. Fonte da decisão e separação de produto

O alvo é exclusivamente `ScenarioEditorWindow` → `SceneAuthoringViewport` → `SceneAuthoringSession` → `SceneAuthoringModel`.

`CanvasView`, `Scene`, `CommandManager` e ferramentas de imagem são legado. Capacidades equivalentes encontradas ali não contam como implementação de P2D-03B e não serão alteradas neste sublote.

P2D-03A está `ACCEPTED / CLOSED` e permanece congelada. P2D-03C (zoom, pan, fit e revisão visual de estados) não será implementada neste sublote.

## 3. Auditoria factual da baseline

Na baseline de entrada, a sessão já fornece:

- `apply()` transacional com snapshot profundo do documento e da seleção;
- rollback automático quando a operação lança exceção;
- uma entrada de undo por mudança real, sem histórico para no-op;
- `undo()` e `redo()` que restauram documento e seleção;
- `translate_selected()` e `transform_selected()` no domínio;
- rejeição fail-closed de objeto, layer ou grupo bloqueado;
- `add_object()` e `remove_object()` unitários;
- seleção por clique, Ctrl, Shift, marquee, clique vazio e Ctrl+A do P2D-03A.

Não existe no fluxo profissional:

- nudge conectado a `keyPressEvent`;
- duplicate de seleção;
- remoção por seleção múltipla e tecla Delete;
- clipboard Qt ou payload versionado;
- comandos de edição que preservem explicitamente identidade, grupos e referências;
- contrato de atalhos para undo/redo no viewport.

## 4. Escopo autorizado

### 4.1 Incluído

1. APIs de domínio/sessão para operações atômicas sobre a seleção.
2. Nudge de uma ou várias unidades de mundo, respeitando o snap existente.
3. Duplicate da seleção, com IDs novos e seleção exclusiva dos duplicados.
4. Delete da seleção, com pré-validação de todos os alvos.
5. Copy/paste por payload estrito, versionado e seguro.
6. Undo/redo dessas operações no histórico profissional.
7. Atalhos e mensagens somente quando o viewport profissional tiver foco.
8. Testes de domínio, sessão, Qt, bloqueios, falhas, persistência e não-regressão.

### 4.2 Explicitamente fora

- zoom, pan, fit selection, fit all e auditoria dedicada de estados visuais — P2D-03C;
- edição de vértices, colisão, máscaras, tilemap, NavMesh, entidades, iluminação ou VFX;
- alteração de schema, sem migração formal própria;
- alteração de `QAction` global, menus principais, `CanvasView` ou atalhos de campos de texto;
- criação automática de assets, layers ou grupos ausentes durante paste;
- clipboard com bytes de assets, caminhos absolutos, scripts ou referências externas resolvíveis;
- push, tag, merge, release ou limpeza de untracked.

## 5. Contrato proposto para aceite

### 5.1 Seleção e elegibilidade

- Cada operação captura a seleção canônica no instante do comando.
- IDs inexistentes, duplicados ou seleção com `primary` inválido são rejeitados pelo domínio.
- Visibility e isolamento limitam a geração de seleção no viewport; uma seleção feita explicitamente por árvore/inspector continua sendo a seleção do comando.
- Objeto, layer ou grupo bloqueado torna a operação mutante inelegível. A operação inteira falha antes da primeira alteração.
- Seleção vazia é no-op, sem alteração de documento e sem entrada de histórico.
- Preview é somente leitura: nudge, duplicate, delete, paste e comandos indiretos não mutam documento nem histórico.

### 5.2 Atomicidade e histórico

- Cada nudge aceito, duplicate, delete e paste produz exatamente uma entrada de undo.
- Copy e seleção não produzem entrada de undo.
- No-op não produz entrada de undo.
- Qualquer rejeição restaura documento, seleção e contadores de histórico ao estado anterior.
- Undo e redo restauram documento e seleção exatos, sem drift numérico e sem alias de listas/objetos mutáveis.
- Um novo comando após undo limpa o redo conforme o contrato já existente da sessão.

### 5.3 Nudge

- Setas movem a seleção em coordenadas do mundo: esquerda `(-1, 0)`, direita `(1, 0)`, cima `(0, -1)`, baixo `(0, 1)`.
- `Shift+seta` usa 10 unidades de mundo.
- Outros modifiers não alteram o passo. `Alt` não é usado.
- Cada evento de tecla aceito é uma transação própria; auto-repeat do sistema equivale a eventos independentes e determinísticos.
- A distância relativa entre objetos é preservada.
- O snap existente continua sendo aplicado pelo domínio exatamente como em `translate_selected()`; o nudge não cria uma política paralela de arredondamento.
- Se o snap tornar o resultado idêntico, o evento é no-op, sem histórico, com mensagem não bloqueante.
- Upstream de câmera/parallax não altera a direção no mundo: em preview, o viewport converte somente a apresentação.

### 5.4 Duplicate

- Atalho: `Ctrl+D`, quando o viewport profissional possui foco.
- Offset inicial proposto: `(16, 16)` unidades de mundo, aplicado igualmente a todos os selecionados.
- O offset é aplicado sobre uma cópia profunda do transform e passa pelo snap existente quando este estiver habilitado.
- Cada duplicado mantém `asset_id`, `layer_id`, transform não envolvido, visibilidade, lock e demais campos do objeto de origem.
- Cada duplicado recebe um ID novo, não vazio, válido e não usado no documento.
- Alocação proposta: base determinística derivada do ID de origem com sufixo `__copy`; em colisão, sufixo numérico crescente, sempre respeitando o limite do schema.
- A ordem dos novos objetos segue a ordem visual determinística da seleção.
- Duplicate não modifica membership dos grupos existentes: os novos objetos começam sem membership implícito. Isso evita inserir cópias em grupos dos originais sem uma ação explícita de grupo.
- A seleção final contém exclusivamente os duplicados; o `primary` é o último duplicado na ordem do documento.
- Se qualquer origem estiver bloqueada ou qualquer novo registro não puder ser validado, nenhum duplicado é publicado.

### 5.5 Delete

- Atalho: `Delete`, quando o viewport profissional possui foco.
- Remove todos os objetos selecionados numa única transação.
- Antes de remover, todos os objetos são validados contra lock de objeto, layer e grupo.
- A remoção atualiza membership de grupos somente para retirar IDs removidos; não remove grupos vazios automaticamente.
- A seleção final fica vazia.
- Seleção vazia é no-op. Qualquer bloqueio rejeita a seleção inteira e mantém documento, seleção e histórico intactos.
- O inspector poderá continuar expondo remoção, mas seu fluxo deve delegar a mesma operação de seleção múltipla; não haverá regra paralela para o `primary`.

### 5.6 Copy/paste

- Atalhos: `Ctrl+C` e `Ctrl+V`, somente quando o viewport profissional possui foco.
- Copy não altera documento, seleção ou histórico.
- O payload usa MIME próprio versionado, por exemplo `application/x-neoeng-d-trace-scene-objects;version=1`, contendo JSON UTF-8 estrito.
- O payload contém somente identificador de formato, versão, objetos selecionados em ordem determinística e relações de grupo declaradas. Não contém bytes de asset, caminho absoluto, código executável ou seleção persistida como estado da cena.
- O `asset_id` e `layer_id` são referências declarativas. Paste rejeita o payload inteiro se qualquer asset ou layer não existir no documento de destino; não cria dependências implicitamente.
- Campos desconhecidos, versão incompatível, JSON inválido, IDs vazios/duplicados, transform não finito, referência ausente ou relação de grupo inválida produzem rejeição sem mutação parcial.
- Paste cria novos IDs usando o mesmo allocator determinístico de duplicate.
- Offset aceito: `(16, 16)` unidades de mundo, sempre relativo aos transforms copiados.
- Paste preserva `asset_id`, `layer_id`, transform, visibilidade, lock e campos autorizados do objeto. Não copia bytes nem altera assets.
- A seleção final contém exclusivamente os objetos colados; `primary` é o último na ordem do documento.
- Membership de grupo é preservado somente quando todos os membros diretos daquele grupo estão no payload. Nesse caso é criado um grupo clonado com novo ID e membros remapeados; se a relação hierárquica pai não estiver integralmente representada, o grupo colado torna-se raiz. Se algum membro do grupo não estiver no payload, os objetos colados ficam sem membership implícito.
- Colar repetidamente é permitido: cada operação aloca IDs novos e cria uma entrada de undo independente.

### 5.7 Undo/redo e atalhos

- `Ctrl+Z` e `Ctrl+Y` serão reconhecidos pelo viewport apenas enquanto ele ou um controle de edição do viewport possuir foco.
- Campos editáveis do inspector conservam o comportamento nativo de copiar/colar/undo e não serão sequestrados pelos atalhos do viewport.
- Toolbar/inspector e teclado chamam as mesmas APIs da sessão; não haverá caminho de mutação paralelo.
- Após undo/redo, o viewport sincroniza itens, gizmo, seleção e estado visual sem recriar IDs.

### 5.8 Mensagens de operação

As mensagens devem ser curtas, objetivas e acionáveis. O mínimo esperado é:

- sucesso: `Moved N object(s)`, `Duplicated N object(s)`, `Deleted N object(s)`, `Copied N object(s)`, `Pasted N object(s)`;
- no-op: `No objects selected` ou `No movement after snap`;
- bloqueio: identificar objeto, layer ou grupo responsável;
- paste inválido: informar formato/versão/referência que falhou, sem traceback modal para erro de entrada controlado;
- preview: `Preview mode is read-only`.

As traduções PT/EN e a captura visual serão fechadas na qualificação do sublote, sem alterar a semântica.

## 6. Invariantes que não podem regredir

- IDs existentes nunca mudam.
- Seleção continua transitória e não é persistida no JSON.
- Asset references, layers, groups, sockets e campos não envolvidos permanecem intactos.
- O schema V1 continua legível e sem alteração implícita.
- O editor legado não é tocado.
- C3 e os gates G/V/B permanecem imutáveis.
- Nenhuma operação publica estado parcialmente validado.
- A operação falha fechada; não há fallback silencioso para layer, asset, ID ou grupo.

## 7. Testes obrigatórios antes de aceite

### 7.1 Domínio e sessão

- nudge simples/múltiplo, direção, passo, Shift, snap, no-op e limites;
- duplicate com um/múltiplos objetos, ordem, IDs, offset, snap, seleção e campos preservados;
- delete simples/múltiplo, grupo, layer/group/object lock, seleção vazia e rollback;
- codec de clipboard válido, vazio, inválido, versão incompatível, campo desconhecido, asset/layer ausente, ID conflitante e grupo parcial/completo;
- copy sem mutação; paste com novos IDs, offset, seleção exclusiva e grupo remapeado;
- undo/redo isolado e combinado, redo invalidado por novo comando e ausência de drift;
- exceção injetada no meio da preparação com documento e seleção byte/estruturalmente equivalentes ao antes.

### 7.2 Qt/fluxo da usuária

- foco inicial no viewport, atalhos com viewport focado;
- foco em `QLineEdit`/spinbox do inspector preservando Ctrl+C/V/Z/Y nativos;
- nudge, duplicate, delete, copy/paste e undo/redo por teclado e por controles disponíveis;
- authoring mutável versus preview read-only;
- bloqueio, mensagem e seleção final após cada operação;
- save/reopen depois de duplicate/delete/paste;
- Windows nativo, DPI e resoluções-alvo, sem deslocamento de chrome ou painel.

### 7.3 Regressão/gates

- testes focados P2D-03B;
- suíte completa com `.venv` Python 3.11;
- `git diff --check`, fronteira exata de arquivos e protected/geometry-sensitive checks;
- G/V/B canônicos sem alteração não aprovada;
- captura Windows, auditoria visual, comparação estrutural e revisão humana;
- build portátil e smoke test, se a alteração atingir o pacote distribuível.

## 8. Evidência e critérios de aceite do sublote

O fechamento deverá conter commit de entrada/saída, lista exata de arquivos, matriz requisito→código→teste→evidência, logs completos, casos positivos/negativos, captura Windows, auditoria visual, comparação sem mascaramento, revisão humana, suíte completa, G/V/B, manifest/hash e tracked tree final limpo.

P2D-03B só poderá ser `ACCEPTED / CLOSED` quando todas as escolhas desta decisão estiverem aceitas, todos os testes obrigatórios passarem e nenhum bloqueio deixar mutação parcial. Antes do aceite, a linguagem correta era `P2D-03B em implementação e qualificação — fechamento pendente`; após o aceite humano final, a linguagem correta é `P2D-03B ACCEPTED / CLOSED`.

## 9. Aceite explícito do proprietário

O proprietário aceitou explicitamente os seguintes pontos, sem alteração formal:

1. offset `(16, 16)` para duplicate e paste;
2. duplicate sem membership implícito em grupos;
3. paste com clone de grupos somente quando o conjunto completo de membros diretos estiver presente;
4. clipboard próprio versionado, sem bytes/caminhos externos e com rejeição atômica;
5. `Ctrl+D`, `Delete`, `Ctrl+C`, `Ctrl+V`, `Ctrl+Z` e `Ctrl+Y` limitados ao contexto de foco do viewport.

Aceite registrado: **`P2D-03B ACEITO — contrato de operações, histórico e clipboard`**.

Este aceite autoriza a implementação limitada à fronteira desta decisão. O aceite não autoriza P2D-03C, alteração de schema, alteração do legado, push, tag, merge ou release.
## 10. Fechamento formal

O proprietário registrou o aceite humano final da build portátil, das capturas
Windows, dos fluxos de operação e do review package com a mensagem `aceito` em
30/08/2026. A implementação respeitou integralmente a fronteira desta decisão:
operações de edição, histórico e clipboard no editor profissional, sem alteração
do editor legado, do schema, de P2D-03A, de C3 ou de P2D-03C.

O commit técnico é `f7a7e61a297710d16f472e48f14caac974749d72`; a documentação de
qualificação pós-commit foi consolidada antes deste fechamento. Os testes,
auditorias, gates canônicos, build portátil, smoke test, review package e a
revisão humana estão registrados na evidência correspondente. P2D-03B está,
portanto, formalmente **ACCEPTED / CLOSED**.

Este fechamento não autoriza P2D-03C, push, tag, merge ou release.