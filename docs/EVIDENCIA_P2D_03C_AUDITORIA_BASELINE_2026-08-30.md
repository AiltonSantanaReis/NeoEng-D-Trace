# NeoEng-D-Trace — Evidência da auditoria baseline P2D-03C

**Sublote:** P2D-03C — navegação do viewport e revisão de estados visuais<br>\r\n**Status:** `ACTIVE / AUDITORIA BASELINE — contrato pendente de aceite`<br>\r\n**Data:** 30/08/2026 (UTC-03)<br>\r\n**Checkpoint auditado:** `78f773583b0277fa9b970d1f849538b4fa3fdcc6`<br>\r\n**Branch:** `modernization/multiaxis-ui`<br>\r\n**Ambiente de referência:** Windows, Python `.venv\\Scripts\\python.exe` 3.11.9, PySide6 6.10.1, pytest 9.1.1

Esta auditoria foi executada em modo somente leitura. Ela abre a base factual do
P2D-03C e não autoriza implementação de código, alteração de schema, alteração
do editor legado, alteração de baseline ou operação remota.

## 1. Prova compacta do checkpoint

Comandos executados na raiz do repositório:

```text
git rev-parse HEAD
78f773583b0277fa9b970d1f849538b4fa3fdcc6

git branch --show-current
modernization/multiaxis-ui

git status --short --untracked-files=no
<vazio>

git diff --check
<sem saída; exit 0>
```

O tracked tree estava limpo. O histórico recente confirma que P2D-03A e
P2D-03B estão fechadas e que nenhuma alteração de produto foi feita para abrir
P2D-03C.

## 2. Fronteira auditada

O alvo é exclusivamente o fluxo profissional:

```text
ScenarioEditorWindow
  -> SceneAuthoringViewport
  -> SceneAuthoringSession
  -> SceneAuthoringModel
  -> SceneAuthoringDocumentV2 / OrthographicCamera
```

Foram inspecionados:

- `src/ui/scenario_editor_window.py`;
- `src/ui/scene_authoring_viewport.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/core/scene_authoring_session.py`;
- `src/core/scene_authoring_model.py`;
- `src/core/scene_authoring_preview.py`;
- `src/core/parallax_camera.py`;
- `src/core/scene_authoring_bridge.py`;
- `src/persistence/scene_authoring_schema.py`;
- testes profissionais existentes de viewport, câmera, preview, persistência e
  separação do editor.

`src/ui/canvas_view.py` e seus testes foram considerados apenas como legado e
referência de não-regressão. Zoom, pan e fit do `CanvasView` não contam como
implementação do P2D-03C.

## 3. Constatações factuais

### 3.1 Câmera e projeção já existentes

1. `SceneAuthoringDocumentV2` já possui `camera` com `position` e `zoom`.
   `SceneCameraAuthoringRecord` valida números finitos e zoom positivo.
2. `SceneAuthoringModel.set_camera()` e
   `SceneAuthoringSession.set_camera()` já atualizam a câmera por operação
   transacional.
3. O inspector profissional já possui `Camera X`, `Camera Y`, `Camera Zoom` e
   `Apply Camera`; esse caminho é coberto por testes de câmera/parallax.
4. `OrthographicCamera.project()` e `unproject()` já implementam projeção e
   inversão determinísticas, incluindo a atenuação de parallax por camada.
5. `SceneAuthoringPreviewFrame` já calcula uma representação determinística de
   objetos e sockets para preview.

Esses fatos comprovam infraestrutura de projeção, mas não comprovam uma UX de
navegação do viewport.

### 3.2 Gaps de navegação no viewport profissional

1. `SceneAuthoringViewport` configura `AnchorUnderMouse` e
   `AnchorViewCenter`, mas isso apenas define âncoras do `QGraphicsView`; não
   implementa zoom.
2. O viewport usa `setDragMode(QGraphicsView.DragMode.NoDrag)`.
3. Não existe `wheelEvent()` no viewport profissional.
4. Não existe pan explícito por middle-button, botão dedicado ou gesto de
   teclado.
5. `set_preview_enabled()` ajusta o `sceneRect` e alterna a projeção; não é um
   comando de navegação iniciado pela usuária.
6. Em authoring, `_project_position()` retorna coordenadas do mundo sem aplicar
   a câmera; em preview, aplica `OrthographicCamera` e parallax. A diferença
   deve ser tratada explicitamente no contrato, não por inferência.
7. Não existem métodos de fit selection ou fit all no viewport.

### 3.3 Fit parcialmente exposto, mas não conectado

1. `SceneAuthoringInspector` cria `fit_button` com o rótulo `Fit Selection`.
2. O botão emite `request_fit`.
3. `ScenarioEditorWindow` não conecta `request_fit` a nenhum método do viewport.
4. Não há ação, botão ou executor correspondente a `Fit All`.

Conclusão: o controle visual de `Fit Selection` é uma superfície órfã e não
constitui capacidade funcional disponível para a usuária.

### 3.4 Estados visuais e acessibilidade operacional

1. `SceneAuthoringViewport` possui `StrongFocus` e recebe foco inicial no
   `showEvent()` da janela profissional.
2. O viewport já possui estados de seleção dos objetos e estados de hover dos
   handles do `SceneTransformGizmo`.
3. `SceneObjectGraphicsItem` aceita hover, mas não possui tratamento visual
   dedicado de hover; sua pintura diferencia principalmente selecionado/não
   selecionado.
4. As ações `Overlay`, `Preview` e `Authoring` são checkable; preview/authoring
   são exclusivos por `QActionGroup`.
5. Inspector, ações de salvar/recarregar/exportar e undo/redo são habilitados ou
   desabilitados conforme projeto, modo e histórico.
6. Não existe, até este checkpoint, uma matriz de evidência que capture de modo
   dedicado hover, pressed, checked, focus e disabled do fluxo P2D-03C.
7. Não há `setTabOrder()` explícito na `ScenarioEditorWindow`; a ordem de foco
   não deve ser considerada contratada pela ordem incidental de criação.

### 3.5 Cobertura de testes existente

A cobertura atual comprova, entre outros pontos, projeção, câmera editável,
preview read-only, seleção, gizmo, persistência e separação do legado. Não foram
encontrados testes específicos para:

- wheel zoom ancorado sob o cursor;
- pan e seus limites;
- fit selection;
- fit all;
- inversão viewport ↔ mundo depois de zoom/pan/fit;
- ausência de alteração em transforms, seleção, dirty state e histórico durante
  navegação, caso essa seja a decisão aprovada;
- matriz de estados hover/pressed/checked/focus/disabled do fluxo profissional;
- comportamento em authoring e preview nas resoluções e DPI de evidência.

## 4. Classificação dos findings

| ID | Finding | Eixo | Severidade | Estado |
|---|---|---:|---:|---|
| P2D-03C-F01 | Não existe zoom explícito no viewport profissional | B/V | Alta | Aberto |
| P2D-03C-F02 | Não existe pan explícito no viewport profissional | B/V | Alta | Aberto |
| P2D-03C-F03 | `Fit Selection` é emitido, mas não possui consumidor | B | Alta | Aberto |
| P2D-03C-F04 | `Fit All` não existe | B | Alta | Aberto |
| P2D-03C-F05 | authoring e preview usam projeções diferentes e não há contrato de navegação comum | B/V | Alta | Aberto |
| P2D-03C-F06 | Estados visuais do sublote não possuem auditoria dedicada | V/B | Média | Aberto |
| P2D-03C-F07 | Tab order não está explicitamente contratado | B | Média | Aberto |

Nenhum finding exige alterar C3, G/V/B canônicos, schema V1 ou o editor legado.

## 5. Fronteiras que permanecem imutáveis

- C3 e todos os artefatos selados permanecem imutáveis.
- P2D-03A e P2D-03B permanecem `ACCEPTED / CLOSED`.
- O schema V1 não será alterado.
- Não haverá alteração do `CanvasView`, ferramentas de imagem, visualizador de
  máscara ou menu/toolbar global.
- Não haverá alteração de transforms persistidos dos objetos como efeito de
  navegação.
- Não haverá inclusão de tilemap, colisão, NavMesh, entidades, iluminação, VFX,
  2.5D ou 3D.
- Não haverá mudança de tolerância, auditor, referência ou baseline para criar
  aprovação artificial.
- Push, tag, merge, release ou limpeza de untracked continuam proibidos sem
  autorização explícita.

## 6. Conclusão da auditoria

P2D-03C possui gaps reais, localizados e implementáveis no fluxo profissional.
O próximo artefato obrigatório é a decisão específica com contrato, invariantes,
limites, testes e evidências. Até o aceite explícito dessa decisão, a linguagem
correta é:

> **P2D-03C aberta — auditoria baseline concluída; contrato em aprovação; código pendente.**

Não houve mutação de código de produto nesta auditoria.
