# NeoEng-D-Trace — Evidência de auditoria da baseline P2D-03

**Status:** RECORDED — auditoria factual concluída para abertura da decisão
**Data:** 29/08/2026 (UTC-03)
**Etapa:** P2D-03 — navegação, seleção e produtividade
**Baseline auditada:** `3c09f37c140f8a807b8b9006aa095db37729129b`
**Branch:** `modernization/multiaxis-ui`

## 1. Escopo e método

Esta auditoria foi somente de leitura. O objetivo foi verificar o que existe na implementação atual do editor profissional antes de autorizar qualquer alteração de código.

Foram inspecionados:

- `src/ui/scenario_editor_window.py`;
- `src/ui/scene_authoring_viewport.py`;
- `src/core/scene_authoring_model.py`;
- `src/core/scene_authoring_session.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/ui/scene_authoring_group_stack.py`;
- `src/ui/scene_authoring_layer_stack.py`;
- testes do modelo profissional, viewport, transformações e persistência;
- o documento normativo e o plano vigente.

O `src/ui/canvas_view.py` foi consultado somente para separar funcionalidades legadas, principalmente nudge, wheel zoom, fit e atalhos. Nenhuma capacidade legada foi contada como capacidade profissional.

## 2. Prova compacta do checkpoint

Comandos executados na raiz do repositório:

```text
git branch --show-current
modernization/multiaxis-ui

git rev-parse HEAD
3c09f37c140f8a807b8b9006aa095db37729129b

git rev-parse origin/modernization/multiaxis-ui
3c09f37c140f8a807b8b9006aa095db37729129b

git rev-list --left-right --count origin/modernization/multiaxis-ui...HEAD
0 0

git status --short --untracked-files=no
<vazio>
```

O checkpoint estava alinhado e com tracked tree limpo antes da criação desta evidência e da decisão. A última requalificação aceita de P2D-02 registrou `1779 passed / 2 skipped / 0 failed`, auditoria Qt Windows/offscreen com exit 0 e tracked tree limpo após commit.

## 3. Evidência de capacidades existentes

### 3.1 Seleção e edição

- `SceneSelection` em `src/core/scene_authoring_model.py:38-54` garante IDs únicos e exige que `primary` pertença à seleção.
- `SceneAuthoringModel.set_selection` em `src/core/scene_authoring_model.py:122-130` rejeita IDs desconhecidos.
- `SceneAuthoringViewport._object_pressed` em `src/ui/scene_authoring_viewport.py:666-678` implementa clique simples e alternância com `ControlModifier`.
- `SceneObjectGraphicsItem` em `src/ui/scene_authoring_viewport.py:56-127` recebe mouse press/move/release e emite os eventos para o viewport.
- `SceneAuthoringViewport._refresh_selection` em `src/ui/scene_authoring_viewport.py:570-572` atualiza o estilo visual dos objetos selecionados.
- `SceneAuthoringViewport._refresh_gizmo` em `src/ui/scene_authoring_viewport.py:574-595` cria o gizmo para o objeto primary.
- `SceneAuthoringGroupStack` e `SceneAuthoringLayerStack` selecionam grupo, objetos do grupo ou objetos da layer por meio da sessão.

### 3.2 Transformações, bloqueios e histórico

- `SceneAuthoringModel.translate_selected` em `src/core/scene_authoring_model.py:198-228` traduz a seleção e preserva posições relativas.
- `SceneAuthoringModel.transform_selected` em `src/core/scene_authoring_model.py:230-295` aplica translação, rotação e escala uniforme ao redor do centro da seleção.
- O viewport implementa gestos de mouse e gizmo em `src/ui/scene_authoring_viewport.py:700-815`.
- `SceneAuthoringModel._assert_editable` em `src/core/scene_authoring_model.py:111-120` rejeita objeto, layer ou grupo bloqueado.
- `SceneAuthoringSession` registra snapshots, gestos, undo e redo em `src/core/scene_authoring_session.py:100-167` e `src/core/scene_authoring_session.py:332-347`.
- `remove_object` existe no modelo/sessão e é exposto pelo inspector para o objeto primary em `src/ui/scene_authoring_inspector.py:512-515`.

## 4. Gaps comprovados para P2D-03

### 4.1 Operações que não estão no viewport profissional

Não foram encontrados no `SceneAuthoringViewport`:

- `keyPressEvent` ou `keyReleaseEvent` para nudge e atalhos;
- operação de duplicate;
- integração com `QClipboard` ou payload de copy/paste;
- marquee/rubber-band de seleção;
- select-all;
- `wheelEvent` ou comando de zoom do viewport profissional;
- pan explícito;
- fit selection ou fit all.

O viewport usa `setDragMode(QGraphicsView.DragMode.NoDrag)` em `src/ui/scene_authoring_viewport.py:295-297`. Isso confirma que nenhuma seleção por área é fornecida pelo modo padrão do `QGraphicsView`.

### 4.2 Limites da seleção atual

O comportamento atual do clique de objeto considera `ControlModifier`; não há contrato implementado para Shift/Alt. Também não há handler explícito de clique vazio no viewport profissional que limpe a seleção. Portanto, esses comportamentos não podem ser tratados como resolvidos por inferência do Qt.

### 4.3 Navegação atual

O viewport constrói `OrthographicCamera` e projeta posições em `src/ui/scene_authoring_viewport.py:376-424`, mas isso não constitui uma UX de navegação. `set_preview_enabled` altera projeção e scene rect; não há comandos profissionais conectados para zoom, pan ou fit.

### 4.4 Separação do legado

O `CanvasView` legado possui `_nudge_selected_with_gizmo`, `wheelEvent`, `fit_to_window` e `keyPressEvent`, mas esses métodos operam sobre o modelo legado `Scene`, `CommandManager` e ferramentas de imagem. Eles não são chamados pelo `ScenarioEditorWindow` para o viewport profissional e não satisfazem P2D-03.

## 5. Testes já existentes e limite da cobertura

Há cobertura existente para:

- invariantes básicas de seleção do modelo profissional em `tests/test_stage2_scene_authoring_model.py`;
- projeção e seleção/transformação do viewport em `tests/test_stage4_professional_scene_authoring.py`;
- gizmo e undo/redo do fluxo profissional em `tests/test_stage6_professional_gizmo.py` e `tests/test_transform_gesture.py`;
- persistência V2 e validação de referências em `tests/test_stage5_scene_authoring_persistence.py`.

Os testes legados de seleção, nudge, fit e atalhos não são evidência de P2D-03. A cobertura de P2D-03 ainda precisa ser criada para domínio, sessão, Qt real, foco, modifiers, clipboard, marquee, navegação, estados visuais e fluxo da usuária.

## 6. Conclusão factual

Na baseline `3c09f37c140f8a807b8b9006aa095db37729129b`, o editor profissional já possui composição por objetos, seleção básica, transformação com mouse/gizmo, bloqueios, grupos/camadas e histórico transacional. Ele ainda não possui o conjunto verificável de produtividade exigido por P2D-03.

Conclusão: **P2D-03 deve ser aberta como etapa ativa de contrato/auditoria; implementação de código ainda não está autorizada por esta evidência.**

O resultado foi incorporado à decisão formal `DECISAO_P2D_03_NAVEGACAO_SELECAO_PRODUTIVIDADE_2026-08-29.md`. Não houve alteração de código de produto durante a auditoria.
