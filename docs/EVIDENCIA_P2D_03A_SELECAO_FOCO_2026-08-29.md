# NeoEng-D-Trace — Evidência P2D-03A

**Sublote:** P2D-03A — seleção, foco, mouse, select-all e marquee
**Status:** ACCEPTED / CLOSED — owner approval received
**Data:** 29/08/2026 (UTC-03)
**Baseline de entrada:** `fdc74f12e75764c9936eaf30b2198b08338a84dc`
**Branch:** `modernization/multiaxis-ui`
**Ambiente:** Windows, Python `.venv\Scripts\python.exe` 3.11, PySide6 6.10.1, pytest 9.1.1

Este documento registra a implementação e a qualificação técnica do primeiro
sublote de P2D-03. Ele não encerra P2D-03 e não substitui a revisão humana do
proprietário. A baseline C3, os adapters G/V/B, o editor legado, o schema e as
referências históricas permanecem fora da alteração.

## 1. Fronteira exata

Arquivos de produto e verificação alterados neste sublote:

- `src/ui/scene_authoring_viewport.py`
- `src/ui/scenario_editor_window.py`
- `scripts/audit_p2d_03a_selection.py`
- `tests/test_p2d_03a_professional_selection.py`
- `tests/test_stage3_professional_scene_editor.py`
- este documento de evidência.

O diretório de saída do auditor não faz parte do changeset de código; ele é
evidência local reproduzível:

`docs/evidence/artifacts/p2d-03a-selection-20260829-r3/`

O primeiro diretório de execução, preservado e não reutilizado, foi:

`docs/evidence/artifacts/p2d-03a-selection-20260829/`

Ele foi classificado como tentativa inválida do auditor porque o critério
esperado para `Shift+C` ignorava corretamente o primary `B`. Nenhum resultado
de produto foi mascarado ou descartado.

## 2. Comportamento implementado

### 2.1 Seleção e foco

- O `SceneAuthoringViewport` possui `StrongFocus`.
- A janela profissional posiciona o foco inicial no viewport após sua abertura.
- O ciclo de reabertura reinicializa a marca de foco inicial.
- Clique em objeto mantém o caminho de seleção e gesto existente.
- Clique sobre qualquer item gráfico existente, inclusive item de objeto ou
  gizmo, é delegado ao fluxo QGraphicsView anterior; isso preserva o drag,
  transformação e interação já existentes.
- Clique em área vazia limpa a seleção no authoring e não cria objeto.
- `Ctrl` alterna um objeto na seleção.
- `Shift` seleciona o intervalo contíguo entre o primary atual e o objeto
  clicado, na ordem visual determinística.
- `Alt` não introduz semântica adicional de seleção.
- `Escape` cancela um marquee em andamento e restaura seleção/primary prévios;
  sem marquee, limpa a seleção.

### 2.2 Marquee e select-all

- Arraste da esquerda para a direita seleciona somente objetos totalmente
  contidos no retângulo.
- Arraste da direita para a esquerda seleciona objetos que intersectam o
  retângulo.
- O marquee considera somente objetos materializados no viewport, portanto
  respeita visibilidade e isolamento já aplicados pela sincronização do
  authoring.
- `Ctrl+A` seleciona todos os objetos visíveis em ordem determinística.
- A seleção continua transitória; nenhum campo do documento persistente é
  alterado por seleção, clique vazio, marquee ou select-all.
- O desenho do marquee é somente uma camada visual temporária no viewport.

## 3. Correção regressiva aplicada durante a qualificação

A primeira execução da suíte completa após a implementação encontrou uma
regressão real no teste de drag existente: o handler novo capturava também
cliques sobre objetos e impedia o `SceneObjectGraphicsItem` de iniciar seu
gesto. A correção foi restrita à fronteira de eventos: `itemAt()` delega o
clique sobre item gráfico ao fluxo anterior; somente o fundo vazio inicia
marquee.

O teste regressivo voltou a passar antes da execução dos gates finais. Nenhuma
alteração foi feita no modelo, na sessão, no schema ou no editor legado para
contornar a falha.

## 4. Matriz requisito → implementação → teste → evidência

| Requisito | Implementação | Teste automatizado | Evidência de fluxo |
|---|---|---|---|
| foco forte e foco inicial | `SceneAuthoringViewport` e `ScenarioEditorWindow.showEvent` | `test_window_binds_professional_editor_only_after_saved_project` | `00-initial-focus.png`, `initial_focus=true` |
| clique simples e Ctrl | `_object_pressed` e `_set_selection` | `test_selection_modifiers_are_deterministic` | `01-click-a.png` |
| Shift por ordem visual | `_visible_object_ids` + anchor primary | `test_selection_modifiers_are_deterministic` | `02-ctrl-shift-selection.png`, resultado `[b,c]` |
| clique vazio | `mousePressEvent` no fundo | `test_empty_click_clears_selection...` | `05-empty-click.png`, seleção vazia |
| cancelamento por Escape | `keyPressEvent` e `_clear_marquee` | `test_empty_click_clears_selection...` | estado restaurado no teste |
| marquee containment | `_apply_marquee_selection` esquerda→direita | `test_marquee_uses_containment...` | `03-marquee-contained.png`, `[a]` |
| marquee intersection | `_apply_marquee_selection` direita→esquerda | `test_marquee_uses_containment...` | `04-marquee-intersected.png`, `[b]` |
| elegibilidade por visibilidade | filtro pelo conjunto materializado | 	est_hidden_objects_are_not_reintroduced... | seleção oculta não reintroduzida |
| Ctrl+A | `_select_all_visible` + `keyPressEvent` | `test_marquee_modifier_and_select_all_contract` | `06-select-all.png`, `[a,b,c]` |
| preservação de drag existente | delegação de `itemAt()` | `test_viewport_inspector_and_drop_import_are_interactive` | suíte Stage 3 |

## 5. Execuções e resultados

### 5.1 Sintaxe e higiene

Comandos:

```text
.\.venv\Scripts\python.exe -m py_compile src\ui\scene_authoring_viewport.py src\ui\scenario_editor_window.py tests\test_p2d_03a_professional_selection.py tests\test_stage3_professional_scene_editor.py scripts\audit_p2d_03a_selection.py
git diff --check
```

Resultado: `py_compile=0`, `git diff --check=0`.

### 5.2 Testes focused

```text
.\.venv\Scripts\python.exe -m pytest -q tests\test_p2d_03a_professional_selection.py tests\test_stage4_professional_scene_authoring.py tests\test_stage6_professional_gizmo.py tests\test_transform_gesture.py tests\test_stage3_professional_scene_editor.py
```

Resultado final após a correção e a limpeza do teste obsoleto: `42 passed`,
`0 failed`, `0 warnings`.

### 5.3 Suíte integral

```text
.\.venv\Scripts\python.exe -m pytest -q
```

Resultado final: `1784 passed, 2 skipped, 0 failed`.

Os dois skips são preexistentes e não foram criados, alterados ou ocultados
por este sublote.

### 5.4 Auditoria automatizada do fluxo Qt real

```text
$env:QT_QPA_PLATFORM = 'windows'
$env:PYTHONPATH = (Resolve-Path .).Path
.\.venv\Scripts\python.exe scripts\audit_p2d_03a_selection.py --output docs\evidence\artifacts\p2d-03a-selection-20260829-r3
```

Resultado: `AUDIT_EXIT=0`.

O auditor usou a janela `ScenarioEditorWindow` visível e eventos `QTest`, não
chamadas internas como substituto do fluxo de usuário. O relatório registra:

- `initial_focus=true`;
- `click_a=[a]`;
- `ctrl_shift_selection=[b,c]`;
- `marquee_left_to_right=[a]`;
- `marquee_right_to_left=[b]`;
- `empty_click_selection=[]`;
- `select_all=[a,b,c]`;
- janela lógica `1280×820`;
- captura física `2560×1640`;
- `device_pixel_ratio=2.0`.

Capturas geradas:

```text
00-initial-focus.png
01-click-a.png
02-ctrl-shift-selection.png
03-marquee-contained.png
04-marquee-intersected.png
05-empty-click.png
06-select-all.png
```

Todos os sete PNGs foram decodificados com o mesmo tamanho físico. O hash do
estado inicial é igual ao hash do estado após clique vazio, demonstrando que
essa ação não deixa delta visual persistente quando a seleção já está vazia.
Os marquees produziram deltas localizados nos objetos esperados:

- containment: bbox `(546,726)-(742,921)`;
- intersection: bbox `(746,726)-(942,921)`.

O auditor estrutural não substitui a inspeção visual humana. Clipping, clareza
óptica e preferência visual continuam sujeitos à revisão do proprietário.

## 6. Invariantes preservados

- Nenhum ID de objeto foi alterado.
- Nenhum asset, layer, group, socket ou transform persistente é alterado por
  seleção.
- Nenhuma mutação foi adicionada a `Ctrl+A`, clique vazio ou marquee.
- O drag/transform existente continuou passando no teste Stage 3.
- Nenhum schema, exportador, QAction global, atalho do menu principal,
  `CanvasView`, visualizador de máscara ou ferramenta de imagem foi alterado.
- Não houve alteração nos adapters ou baselines G/V/B.
- Nenhuma tolerância ou auditor anterior foi alterado.

## 7. Limites e itens deliberadamente não implementados

Este sublote não implementa nudge, duplicate, delete, copy/paste, undo/redo
novo, zoom, pan, fit, hover dedicado ou estados de inspector. Esses itens
permanecem nos sublotes P2D-03B/P2D-03C conforme a decisão formal. Não há
alteração em tilemap, colisão, NavMesh, entidades, iluminação ou VFX.

O retorno de foco a um controle acionador foi classificado como `N/A` para a
janela top-level profissional: não existe popup ou controle acionador interno
que abra esse editor e exija restauração de foco. O foco inicial e o ciclo de
reabertura foram comprovados; qualquer integração futura com comando/popup
deverá abrir decisão própria se criar um novo requisito de retorno.

## 8. Requalificação pós-commit

O changeset de produto foi commitado localmente em:

`17c3cbcdb244419fc6b69b907652983dac36432a`

A conferência pós-commit confirmou:

- branch `modernization/multiaxis-ui`;
- `git diff-tree` com exatamente os seis arquivos listados neste documento;
- `git status --short --untracked-files=no` vazio;
- `git diff HEAD^ HEAD --check` sem erro;
- suíte integral pós-commit: `1784 passed, 2 skipped, 0 failed`.

A auditoria do fluxo Qt foi repetida contra esse commit, sem reutilizar somente
os artefatos pré-commit:

```text
QT_QPA_PLATFORM=windows
.\.venv\Scripts\python.exe scripts\audit_p2d_03a_selection.py --output docs\evidence\artifacts\p2d-03a-selection-20260829-r5
POSTCOMMIT_AUDIT_EXIT=0
```

O relatório pós-commit está em
`docs/evidence/artifacts/p2d-03a-selection-20260829-r5/report.json` e contém
os mesmos resultados determinísticos da evidência pré-commit: foco inicial
verdadeiro, `[a]` no clique simples, `[b,c]` no fluxo Ctrl/Shift, `[a]` no
marquee de contenção, `[b]` no marquee de interseção, seleção vazia no clique
vazio e `[a,b,c]` no Ctrl+A. As sete capturas pós-commit foram produzidas em
janela lógica `1280×820`, pixels `2560×1640`, com DPR da janela `2.0`.

Este registro não autoriza push, tag, merge ou release. A revisão humana do
proprietário foi concluída e o aceite está registrado na seção 9.
## 9. Decisão atual

P2D-03A está **ACCEPTED / CLOSED**. O proprietário aprovou explicitamente a
evidência deste sublote em 29/08/2026 (UTC-03), com a declaração:

> A evidência está aprovada.

O aceite cobre a implementação de seleção, foco, mouse, select-all e marquee,
os testes, o auditor Qt/Windows, a requalificação pós-commit e os artefatos
referenciados neste documento. Ele não encerra P2D-03: nudge, duplicate,
delete, copy/paste, undo/redo novo, zoom, pan e fit continuam reservados aos
sublotes P2D-03B/P2D-03C.

Não há autorização de push, tag, merge ou release neste documento.
