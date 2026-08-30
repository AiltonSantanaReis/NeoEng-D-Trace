# Evidência P2D-03B — Auditoria da baseline de operações de edição

**Status:** RECORDED — auditoria concluída; contrato posteriormente aceito pelo proprietário
**Data:** 29/08/2026 (UTC-03)
**Etapa:** P2D-03B
**Baseline auditada:** `24a3178d52f1096e55c73b40daf196bccfe0d8cc`
**Branch:** `modernization/multiaxis-ui`
**Escopo:** somente leitura; nenhum arquivo de produto foi alterado nesta auditoria.

## 1. Prova do checkpoint

Executado na raiz do repositório da branch auditada:

```text
git rev-parse HEAD
24a3178d52f1096e55c73b40daf196bccfe0d8cc

git branch --show-current
modernization/multiaxis-ui

git status --short --untracked-files=no
<vazio>

git diff --check
<sem saída; exit 0>
```

O checkout de entrada estava com tracked tree limpo. Untracked legítimos foram deliberadamente excluídos da prova de fronteira e não foram removidos.

## 2. Arquivos e APIs inspecionados

- `src/core/scene_authoring_session.py`;
- `src/core/scene_authoring_model.py`;
- `src/persistence/scene_authoring_schema.py`;
- `src/ui/scene_authoring_viewport.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/ui/scenario_editor_window.py`;
- `src/ui/scene_authoring_groups.py`;
- testes profissionais de seleção, gizmo, histórico e persistência;
- decisão e evidência de P2D-03 e evidência aceita de P2D-03A.

O `CanvasView` foi consultado apenas para separar o legado. Nudge, fit, wheel e atalhos daquele fluxo não foram contados como capacidade P2D-03B.

## 3. Fatos comprovados

### 3.1 Segurança transacional existente

`SceneAuthoringSession.apply()` captura snapshot profundo, executa a operação, restaura o snapshot quando há exceção, registra somente mudanças reais e limpa redo após nova mutação. `undo()` e `redo()` restauram documento e seleção.

### 3.2 Modelo existente

`SceneAuthoringModel` possui `add_object`, `remove_object`, `translate_selected`, `transform_selected` e `update_transform`. O schema valida referências de asset/layer, IDs únicos, membership de grupos e, no V2, ciclos de hierarquia.

`_assert_editable()` rejeita objeto bloqueado, layer bloqueada e grupo efetivamente bloqueado. A remoção unitária retira o ID dos grupos, mas não existe operação profissional de remoção da seleção múltipla.

### 3.3 Viewport existente

`SceneAuthoringViewport` possui foco forte, seleção P2D-03A, gestos de arraste e gizmo, além de wrappers de undo/redo. Seu `keyPressEvent` atual trata somente Ctrl+A e Escape. Não há handlers profissionais para nudge, duplicate, Delete ou clipboard.

Não foram encontradas integrações `QClipboard`, MIME de cena, `wheelEvent`, pan, fit, ou `QAction`/shortcut de edição no viewport profissional.

### 3.4 Janela e inspector

`ScenarioEditorWindow` expõe ações de salvar, recarregar, exportar, undo/redo, preview e authoring, mas não declara atalhos de edição. O inspector possui `Delete Selected`, porém chama `remove_object(primary.id)`, portanto atua somente no objeto primary.

Os atalhos devem ser contextuais para não sequestrar Ctrl+C/V/Z/Y de campos de texto do inspector.

## 4. Gaps e riscos que o contrato resolve

| Gap | Risco se implementado sem contrato | Regra proposta |
|---|---|---|
| nudge inexistente | alterar coordenadas no espaço errado ou criar histórico excessivo | passo explícito em mundo, um evento/uma transação, snap existente |
| duplicate inexistente | IDs duplicados, cópia em grupo errado ou seleção ambígua | allocator novo, offset explícito, sem membership implícito |
| delete unitário | remoção parcial quando um membro está bloqueado | preflight de toda seleção e rollback atômico |
| clipboard inexistente | paths/bytes inseguros, payload incompatível ou alias mutável | MIME versionado, JSON estrito, somente referências válidas |
| grupos em paste | inserir cópia no grupo original ou perder hierarquia silenciosamente | clone somente com conjunto completo; caso parcial fica sem membership |
| atalhos | conflito com QLineEdit/spinbox e menu principal | contexto de foco do viewport |
| undo/redo | drift, seleção incorreta ou caminho paralelo | uma API de sessão compartilhada por UI e teclado |

## 5. Estado da decisão

A auditoria confirmou a base reutilizável e registrou a condição de entrada antes do código. O contrato específico está em `DECISAO_P2D_03B_OPERACOES_EDICAO_UNDO_CLIPBOARD_2026-08-29.md`; o proprietário o aceitou explicitamente com `P2D-03B ACEITO — contrato de operações, histórico e clipboard`. Este documento permanece como registro factual da baseline, não como evidência de fechamento da implementação.

Na execução desta auditoria não houve alteração em C3, baseline G/V/B, editor legado, schema, build ou artefato remoto.
