# NeoEng-D-Trace — Decisão formal P2D-03

**Status:** APPROVED — contrato aceito pelo proprietário; P2D-03A autorizada para implementação
**Data:** 29/08/2026 (UTC-03)
**Etapa:** P2D-03 — navegação, seleção e produtividade
**Produto:** P2D-COMP-01 — Editor Profissional de Composição 2D Baseado em Objetos
**Baseline de entrada:** `3c09f37c140f8a807b8b9006aa095db37729129b`
**Aceite do proprietário:** mensagem explícita ceito recebida em 29/08/2026 (UTC-03).
**Evidência de auditoria:** `docs/EVIDENCIA_P2D_03_AUDITORIA_BASELINE_2026-08-29.md`

## 1. Autoridade, finalidade e condição de entrada

Esta decisão abre formalmente P2D-03 depois do fechamento ACCEPTED/CLOSED da macroetapa P2D-02. Ela define o contrato que deverá governar qualquer implementação posterior de produtividade no editor profissional.

Esta decisão não implementa código, não altera baseline, não altera schema, não altera o editor legado e não declara P2D-03 concluída. O status permanece `OPEN` até que o proprietário do produto aprove o contrato, o código seja implementado em lote controlado e todos os gates sejam concluídos.

A condição de entrada foi comprovada antes desta documentação:

- branch: `modernization/multiaxis-ui`;
- HEAD local: `3c09f37c140f8a807b8b9006aa095db37729129b`;
- HEAD remoto correspondente: `3c09f37c140f8a807b8b9006aa095db37729129b`;
- divergência local/remota: `0 ahead / 0 behind`;
- tracked tree antes da documentação: limpo;
- último resultado aceito de P2D-02: `1779 passed / 2 skipped / 0 failed`.

Untracked existentes não fazem parte da fronteira desta decisão e não podem ser removidos ou normalizados.

## 2. Separação obrigatória entre produto atual e legado

O alvo de P2D-03 é exclusivamente o fluxo da janela profissional `ScenarioEditorWindow`, usando `SceneAuthoringViewport`, `SceneAuthoringModel` e `SceneAuthoringSession`.

O `CanvasView` e as ferramentas de imagem existentes são o editor legado. Recursos encontrados neles podem servir como referência histórica ou como fonte de testes de não-regressão, mas não contam como implementação de P2D-03. Em particular, o nudge por teclado e o fit existentes em `src/ui/canvas_view.py` não satisfazem o contrato do editor profissional.

É proibido resolver um gap de P2D-03 desviando o fluxo profissional para o canvas legado, compartilhando estado implicitamente ou alterando ferramentas de imagem sem subetapa própria e decisão explícita.

## 3. Auditoria factual da baseline

O inventário detalhado, os comandos de auditoria e as referências de código estão em `EVIDENCIA_P2D_03_AUDITORIA_BASELINE_2026-08-29.md`. A classificação resumida é:

| Capacidade | Estado factual na baseline | Classificação para P2D-03 |
|---|---|---|
| seleção simples | clique no item do viewport e seleção pelo inspector/árvore | existente, precisa contrato de foco e teste end-to-end |
| multisseleção | Ctrl no clique do item; `SceneSelection` valida IDs únicos e primary | existente, precisa semântica completa de modifiers e ordem determinística |
| feedback visual da seleção | estilo selecionado e gizmo do primary | existente, precisa revisão de estados e acessibilidade |
| clique em área vazia | não há handler explícito no viewport profissional para limpar seleção | gap de comportamento contratual; deve ser definido e testado |
| arraste com mouse | gesto transacional de movimentação dos objetos | existente e coberto parcialmente |
| gizmo | translate, translate X/Y, scale e rotate | existente e coberto parcialmente |
| bloqueios | objeto, layer e grupo efetivamente locked rejeitam edição | existente; operações novas devem respeitar o mesmo fail-closed |
| undo/redo | sessão registra snapshots de documento e seleção | existente; cada comando novo deve ser atômico e reversível |
| nudge no editor profissional | não há `keyPressEvent`/atalho nudge no `SceneAuthoringViewport` | ausente |
| duplicate | há `add_object` e `remove_object` no domínio, mas não há comando de duplicação do objeto selecionado | ausente |
| delete por seleção | remoção exposta pelo inspector apenas para o primary | parcial; seleção múltipla e atalho não estão fechados |
| copy/paste | não há clipboard ou contrato de payload do editor profissional | ausente |
| marquee/select-all | não há rubber-band/marquee nem select-all no viewport profissional | ausente |
| zoom/pan/fit | há câmera e projeção, mas não há navegação explícita, fit selection ou fit all no viewport profissional | parcial no modelo, ausente na UX |
| foco, tab order e atalhos | a janela possui toolbar e controles, mas o fluxo de foco/atalhos do viewport não está especificado nem comprovado | aberto |
| hover/pressed/checked/focus/disabled | componentes possuem estados Qt, mas não existe auditoria dedicada do fluxo P2D-03 | aberto |

A auditoria não encontrou evidência de alteração necessária em C3, nos adapters G/V/B ou no editor legado. Essas fronteiras permanecem preservadas.

## 4. Escopo autorizado para P2D-03

P2D-03 poderá alterar somente o fluxo de produtividade da janela profissional e os contratos diretamente necessários para ele:

1. seleção simples, multisseleção e seleção por área;
2. seleção total, limpeza de seleção e definição de primary;
3. foco inicial, retorno de foco, tab order e atalhos sem conflito com o menu principal;
4. nudge por teclado com passo documentado;
5. duplicate, delete e operações de transformação aplicadas à seleção;
6. copy/paste com payload validado e identidade nova para objetos colados;
7. navegação do viewport: zoom, pan, fit selection e fit all;
8. estados de mouse e teclado necessários para tornar essas operações observáveis e acessíveis;
9. mensagens de operação, rejeição e bloqueio compreensíveis;
10. testes, capturas, auditorias e evidências da própria etapa.

A implementação poderá ser dividida em sublotes, desde que cada sublote tenha fronteira, teste, evidência e decisão próprios. A ordem recomendada é:

- `P2D-03A`: contrato de seleção, foco, mouse, select-all e marquee;
- `P2D-03B`: nudge, duplicate, delete, copy/paste e undo/redo;
- `P2D-03C`: zoom, pan, fit selection, fit all e revisão visual de estados.

Essa divisão é operacional; não autoriza implementação antes da aprovação do contrato desta decisão.

## 5. Invariantes obrigatórios

### 5.1 Identidade e seleção

- IDs de objetos existentes nunca mudam por seleção, transformação, duplicate, copy ou paste.
- A seleção é estado transitório do editor e não pode ser persistida no JSON da cena.
- `ids` não contém duplicatas; `primary` é nulo ou pertence a `ids`.
- A ordem dos IDs selecionados e a escolha de `primary` são determinísticas e documentadas.
- Seleção de objetos ocultos, inexistentes ou fora do isolamento ativo não pode ocorrer por um atalho ou marquee.
- Clique, Ctrl, Shift e Alt só terão significado se forem declarados no contrato e testados; nenhuma semântica será inferida da implementação do Qt.

### 5.2 Integridade das operações

- Cada operação mutante relevante é uma transação única de sessão: sucesso gera exatamente uma entrada de undo; no-op não gera histórico; falha não deixa alteração parcial.
- Undo e redo restauram documento e contexto de seleção compatíveis, sem drift numérico.
- Objeto, layer ou grupo bloqueado rejeita qualquer operação mutante que o afete, com diagnóstico explícito.
- Visibilidade e isolamento limitam o alvo das operações de viewport sem corromper membership persistente.
- Transformações preservam asset reference, layer, grupo, sockets e campos não envolvidos.
- Nenhuma operação de P2D-03 modifica geometria declarada fora do editor profissional, QAction global, atalhos existentes do produto, schema V1 ou baseline G/V/B sem decisão adicional.

### 5.3 Duplicate, copy e paste

- Duplicate e paste sempre criam IDs de objeto novos e únicos.
- Asset references são reutilizadas por referência válida; bytes de asset não são duplicados sem decisão própria de lifecycle.
- Copy não modifica o documento; paste modifica de forma atômica e seleciona somente os novos objetos, salvo contrato aprovado em contrário.
- O payload de clipboard é versionado, validado, rejeita campos desconhecidos perigosos e não aceita referências externas inseguras.
- Membership em grupos e layer de destino devem ser definidos de forma explícita; não pode haver alias de lista, identidade ou mutable state.
- Colisão de IDs, asset ausente, layer inexistente, grupo inválido e conteúdo de clipboard incompatível produzem rejeição sem mutação parcial.

### 5.4 Nudge e navegação

- Nudge opera em coordenadas do mundo da composição, preserva a distância relativa da multisseleção e respeita snap somente conforme o contrato de snap existente.
- O passo padrão, modificadores, repetição de tecla e limite numérico serão declarados antes do código e cobertos por testes.
- Zoom, pan, fit selection e fit all alteram somente a câmera/viewport; não alteram transforms persistidos dos objetos.
- Fit com seleção vazia possui resultado explicitamente definido; nunca produz exceção nem altera documento.
- A conversão viewport ↔ mundo permanece determinística nos modos authoring e preview, inclusive com parallax declarado.

### 5.5 Foco e acessibilidade operacional

- O viewport profissional recebe foco de forma previsível e devolve foco ao controle acionador quando aplicável.
- Tab order é documentado e não depende da ordem acidental de criação dos widgets.
- Atalhos de P2D-03 não sequestram atalhos do menu principal, campos de texto ou controles de inspector.
- Preview read-only não permite mutação por mouse, teclado, clipboard ou comando indireto.
- Estados hover, pressed, checked, focus e disabled são visíveis, coerentes e capturados em Windows nas resoluções-alvo.

## 6. Limites explícitos

P2D-03 não inclui:

- tilemap, brush, bucket, eraser, autotiling, Rule Tiles, isométrico ou hexagonal;
- colisão de cenário, NavMesh, entidades/componentes/prefabs, iluminação ou VFX;
- mudança de semântica de `position.z`, parallax ou exportação 2.5D/3D;
- alteração do editor de imagem legado, do visualizador de máscara ou de ferramentas de polygon/collision;
- nova persistência estrutural sem schema versionado e migração explícita;
- mudança de tolerância, auditor, baseline ou referência para converter falha em sucesso;
- mudança global de menu, toolbar ou shortcut fora da integração mínima comprovadamente necessária;
- publicação remota, push, tag, merge ou release.

Se a implementação revelar necessidade fora desses limites, a etapa deve parar e abrir uma decisão de mudança de escopo. Não é permitido resolver por acoplamento informal.

## 7. Dúvidas de produto que exigem decisão antes do código

As escolhas abaixo são materialmente observáveis e não serão assumidas silenciosamente. A proposta de engenharia está registrada para aprovação:

| Decisão | Proposta para aprovação |
|---|---|
| modifier de multisseleção | Ctrl alterna item; Shift expande seleção contígua conforme ordem visual; Alt não altera seleção |
| clique vazio | limpa seleção no authoring; não cria objeto e não altera documento |
| marquee | esquerda→direita seleciona objetos totalmente contidos; direita→esquerda seleciona objetos intersectados; somente objetos elegíveis |
| nudge | seta = 1 unidade de mundo; Shift+seta = 10 unidades; repetição gera transações determinísticas por evento aceito |
| duplicate | `Ctrl+D`, deslocamento padrão documentado, novos IDs, mesma layer e mesma referência de asset |
| delete | `Delete` remove toda a seleção elegível em uma transação; bloqueados causam rejeição da operação inteira |
| copy/paste | `Ctrl+C` copia snapshot validado; `Ctrl+V` cria objetos novos com pequeno offset determinístico e seleção exclusiva dos colados |
| fit selection | enquadra bounding box da seleção; seleção vazia não-op com mensagem não bloqueante |
| fit all | enquadra todos os objetos visíveis e elegíveis; composição sem objetos mantém câmera atual |
| zoom/pan | roda do mouse para zoom sob cursor; botão/middle drag para pan; atalhos e limites serão documentados antes do código |
| grupos no copy/paste | preservar membership somente quando todos os membros do grupo forem copiados; caso contrário colar sem membership implícito |

Até o aceite explícito dessas escolhas, o código de P2D-03 não deve ser alterado. Se o proprietário escolher comportamento diferente, esta decisão deve ser atualizada antes da implementação.

## 8. Testes obrigatórios antes de qualquer aceite

### 8.1 Domínio e sessão

- seleção vazia, simples, múltipla, primary, IDs duplicados e IDs desconhecidos;
- seleção de objetos ocultos, isolados, bloqueados, em layer bloqueada e em grupo bloqueado;
- nudge simples e múltiplo, passo, snap, limites e no-op;
- duplicate/delete/copy/paste com IDs, assets, layers, groups, transforms e seleção;
- clipboard inválido, versão incompatível, campos desconhecidos, colisão e asset ausente;
- undo/redo de cada comando e combinação de comandos sem drift;
- falha no meio de operação sem mudança parcial.

### 8.2 Integração Qt e fluxo da usuária

- abrir projeto, entrar na janela profissional e carregar o viewport correto;
- selecionar por clique, modifiers, árvore e marquee;
- aplicar nudge, duplicate, delete, copy/paste, undo/redo e confirmar status;
- navegar por zoom, pan, fit selection e fit all;
- testar authoring e preview read-only;
- testar foco inicial, Tab/Shift+Tab, retorno de foco e atalhos com campos do inspector ativos;
- testar mouse press/release, hover, pressed, checked, focus e disabled;
- testar layer/group visibility, lock, isolation e membership durante as operações;
- salvar/reabrir como teste de não corrupção e preservação dos campos persistentes.

### 8.3 Regressão e conformance

- suíte completa com Python da `.venv`;
- testes do editor profissional e testes de isolamento do legado;
- `git diff --check` e fronteira final de arquivos;
- G/V/B canônicos sem alteração não aprovada;
- captura nativa Windows, auditoria visual e comparação estrutural;
- revisão humana em resoluções/DPI-alvo, incluindo teclado e estados visuais.

## 9. Evidências obrigatórias

O fechamento de cada sublote deverá conter, no mínimo:

1. commit de entrada e commit de saída;
2. lista exata de arquivos alterados e mudanças por eixo;
3. matriz requisito → código → teste → evidência;
4. logs completos com comando, ambiente, saída e exit code;
5. casos positivos e negativos, incluindo bloqueios e no-ops;
6. capturas Qt reais em Windows, com resolução, DPI e estado registrados;
7. auditoria visual e comparação estrutural sem mascaramento;
8. revisão humana registrada;
9. resultado da suíte completa e dos gates G/V/B;
10. manifest, SHA-256, revalidação independente e estado tracked final.

Um sublote não pode ser marcado como aceito apenas porque testes unitários passaram. A prova deve abranger domínio, fluxo Qt, build/captura e revisão humana proporcional ao risco.

## 10. Critérios de aceite de P2D-03

P2D-03 somente poderá ser marcada `ACCEPTED / CLOSED` quando:

- as decisões da seção 7 estiverem aprovadas e registradas;
- seleção, teclado, mouse, nudge, duplicate, delete, copy/paste, marquee/select-all e fit/navegação estiverem implementados no fluxo profissional, ou cada exceção estiver formalmente aprovada;
- todos os invariantes da seção 5 tiverem testes positivos e negativos;
- nenhum bloqueio deixar documento, seleção, histórico ou gesto em estado parcial;
- save/reopen não perder campos nem criar alias de identidade;
- o editor legado permanecer sem alteração não autorizada;
- a suíte completa, gates, capturas, auditorias e revisão humana passarem;
- os documentos, índice, plano, changelog e evidências estiverem reconciliados;
- o usuário/proprietário registrar decisão final de aceite.

Até essas condições, a linguagem correta é: **P2D-03 aberta; auditoria e contrato definidos; implementação pendente**.

## 10.1 Fechamento formal de P2D-03A

P2D-03A foi implementada e qualificada no commit de código
`17c3cbcdb244419fc6b69b907652983dac36432a`, com o registro documental
pós-commit `13c8b6a0b39d7411d5f2ee00dc901aca3a3982d3`. A evidência final está
em `docs/EVIDENCIA_P2D_03A_SELECAO_FOCO_2026-08-29.md`.

O proprietário aprovou explicitamente essa evidência em 29/08/2026 (UTC-03).
A disposição de P2D-03A é `ACCEPTED / CLOSED`. Esse aceite é limitado ao
sublote A; P2D-03 permanece `OPEN` porque P2D-03B e P2D-03C ainda não foram
implementadas nem aceitas. Não há autorização implícita para abrir código de
P2D-03B sem o ciclo próprio de decisão, invariantes, testes e evidências.

## 10.2 Fechamento formal de P2D-03B

P2D-03B foi implementada, requalificada e aceita no checkpoint documental
`78f773583b0277fa9b970d1f849538b4fa3fdcc6`. O commit técnico é
`f7a7e61a297710d16f472e48f14caac974749d72` e a evidência final está em
`EVIDENCIA_P2D_03B_IMPLEMENTACAO_2026-08-29.md`. O proprietário registrou o
aceite humano final da build, das capturas e do review package com `aceito` em
30/08/2026. A disposição de P2D-03B é `ACCEPTED / CLOSED`.

O offset de duplicate/paste é `(16, 16)` unidades de mundo, conforme contrato
aceito. P2D-03C não foi autorizada por esse fechamento e permanece em seu ciclo
próprio de auditoria e decisão.

## 10.3 Fechamento formal de P2D-03C

P2D-03C foi implementada exclusivamente no viewport profissional, com
base no checkpoint auditado `78f773583b0277fa9b970d1f849538b4fa3fdcc6`.
O contrato específico foi aceito pelo proprietário em 30/08/2026 e a
implementação foi registrada no commit técnico
`58674dde87ba94082e84f066ebda21d144da65cd`. A documentação de qualificação
foi sanitizada no commit `921ef61bd0e3022252c4561491dec41196209af7`.

A requalificação pós-commit confirmou a suíte completa, o aggregate
canônico G60/60 + V12/12 + B21/21, a captura Windows, a auditoria visual,
a comparação estrutural e a build portátil. Os exits 1 dos produtores G/B
continuam registrados como mixed legacy; o aggregate decidiu PASS com `blocking=false`. A revisão humana adicional do proprietário não
reproduziu a lentidão observada na transição Fit/Focus.

A evidência consolidada está em
`EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md`. O proprietário registrou
**`P2D-03C ACEITO — entrega final`** em 30/08/2026. O estado formal de
P2D-03C é `ACCEPTED / CLOSED`, com o seal final independentemente revalidado.

## 11. Estado após encerramento do P2D-03C

O aceite explícito abriu o sublote de código `P2D-03C`. A implementação foi
precedida pelos testes de contrato e comportamento, preservou o checkpoint
`78f773583b0277fa9b970d1f849538b4fa3fdcc6` como referência e permaneceu
limitada à fronteira aprovada. P2D-03A, P2D-03B e P2D-03C estão formalmente
aceitas e fechadas em seus próprios registros; o próximo trabalho deve abrir
uma nova decisão, sem reabrir este sublote.

Push, tag, merge e release continuam fora desta decisão.
