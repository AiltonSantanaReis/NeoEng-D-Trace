# Correção de visibilidade dos painéis da MainWindow — 2026-08-21

## Escopo

Correção da responsividade da MainWindow nas larguras 1920, 1366 e 1280, com foco em evitar que o `QStackedWidget`, os `QSplitter` e os painéis laterais sejam reduzidos a zero durante redimensionamento nativo do Windows. O contrato do auditor visual também foi corrigido para registrar o tamanho físico de modais Qt em DPI elevado.

Esta evidência não aprova release, push, PR ou merge. Ela registra somente a validação local desta correção.

## Proveniência

- Branch: `Ailton/fix/ui-panel-visibility`
- Commits da correção de UI: `ffb8cf9`, `d09a4cd`, `b11b5f6`
- Commit do contrato do auditor: `bec1348`
- Commit dos testes/auditor funcional reproduzível: `95f1dd3`
- Build oficial usada na validação final do executável: commit `b11b5f6a978575cdd908099e88f0a4c5dec35139`
- Plataforma: Windows 10, Python 3.11.9, Qt/PySide6 do ambiente do projeto
- O Windows local reportou DPI 200%; as capturas nativas registram o tamanho físico real e o manifesto também mantém o tamanho lógico solicitado.

## Causa confirmada

A página desktop do `QStackedWidget` contribuía para o tamanho mínimo da janela. Durante um resize nativo, a janela não conseguia alcançar o breakpoint compacto; além disso, splitters com filhos colapsáveis permitiam que a área lateral desaparecesse. O problema foi reproduzido com a build nova: a janela permanecia em aproximadamente 2030×1259 quando se tentava atingir 1280×720.

## Alteração aplicada

- O controlador reaplica a geometria após o ciclo de resize do Qt com `QTimer.singleShot(0, ...)`.
- A área de painéis usa políticas expansíveis e `childrenCollapsible=False`.
- O splitter raiz ignora o size hint desktop e permite atingir o breakpoint compacto.
- O layout reserva explicitamente a largura dos painéis nos modos compacto e desktop.
- Os testes verificam larguras reais, tabs ativos, painéis não nulos e não-colapsabilidade.
- O auditor registra `capture_size` do `QPixmap` para comparar corretamente modais em DPI 200%, sem ignorar a geometria lógica.

## Testes automatizados

Com a árvore final dos três checkpoints:

- `1576 passed, 2 skipped` em `pytest -q`.
- `5 passed` em `tests/test_visual_artifact_auditor.py`.
- Black, isort, Flake8 e mypy passaram nos arquivos de UI alterados antes do checkpoint do contrato do auditor.
- `py_compile` passou nos dois auditores.
- `git diff --check` passou.

Os dois skips são os skips já existentes da suíte e não foram criados, alterados ou usados como bypass nesta correção.

## Build e validação do pacote

O script oficial `scripts/build_windows.ps1` foi executado em worktree limpo a partir do commit `b11b5f6`. O validador oficial retornou `SUCCESS` nos 11 checks: CLI, projeto versionado, processamento headless, JSON, GLB, perfis Godot/Unity, GLB dos perfis, abertura/fechamento da GUI e diretório de estado do usuário. O PyInstaller emitiu o warning `Hidden import "tzdata" not found`; ele foi preservado no log e não impediu os 11 checks oficiais.

Artefatos da build final local (`release-stage9-ui-fix-b11b5f6-20260821-final-verified`):

- `portable/NeoEng-D-Trace/release-manifest.json`: `757b5f8906e536fdba20c3645af3b6e400b94f95f0dff296b350ba4821d1f7c8`
- `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`: `a82449e8540385d373a42ba8ac0b4bb01c33dc6ba822f937bb2a2d9d59c852be`
- `portable/NeoEng-D-Trace/NeoEng-D-Trace-CLI.exe`: `bf0845ca8a2ce8239a26470c24c196429a4500918e2451de4aa8ed626f9e3016`
- `NeoEng-D-Trace-0.3.0-win64-portable.zip`: `52dbf72db6035c867a74b9ef4714e39e3e6b947edd062fa4d472aa7c053c0cbc`
- `smoke/portable-smoke-report.json`: `1a208f02ead6efe61bb93ab229230e6338aa666a4d737cdd68e317bf593eb032`

## Captura e auditoria visual

O auditor nativo do projeto criou um fixture real, carregou o projeto, selecionou objeto, exercitou o gizmo, alternou as resoluções e disparou a mensagem real de validação `No collision shapes registered. Use Auto-Generate first.`.

Manifesto da auditoria nativa regenerada:

- `source-native-ui-audit-after-panel-fix/manifest.json`: `50fef8e8a20ffaaa687bcbb2efd6cc777704a181783aff0303c48cb9981daa42`
- As geometrias registram `panel_stack` visível em todas as três resoluções.
- Em 1920×1080, `side_panel` e `collision_panel` ficaram visíveis no desktop.
- Em 1366×768 e 1280×720, o `compact_panel_tabs` ficou visível com largura 460 e o painel lateral ficou selecionável.
- A mensagem de validação foi capturada nas três resoluções.

O auditor Pillow/OpenCV verificou decodificação, dimensões, transparência determinística, SHA-256, clipping, geometria Qt, sobreposição, paleta escura e geração de anotações:

- Status: `PASS`
- Achados: `0`
- `source-native-ui-visual-audit-after-panel-fix/visual-audit-report.json`: `498761bcd5e3d0189dcccc8ceb1eb89538651927131e98598e601b29b79346bd`

A revisão visual humana das capturas nativas disponíveis confirmou: canvas não coberto pelos painéis, painéis laterais presentes, tabs Objects/Layers/Groups/Collision visíveis nas capturas nativas lógicas compactas, gizmo sobre o objeto e modal de validação legível. A execução funcional mais recente manteve o gate humano como `NOT_CONFIRMED`, pois a automação não pode declarar aparência final sozinha.

O auditor funcional versionado também foi executado após a correção:

- `stage9-functional-audit-final/report.json`: `332f32dd856835b99f4f5c6efd051ab0a8afde0c803c8e13e0fbc63d4e87670c`
- Ações funcionais: `true`; geometria/clipping: `true`; achados: `0`.
- Status geral: `FAIL` deliberado apenas porque `human_review=false` e `source_tree_clean=false`; isso não foi convertido em PASS.

## Limitações declaradas

- A captura direta do executável empacotado com projeto carregado não foi considerada prova: a automação do diálogo nativo do Windows permaneceu não determinística sob as janelas existentes no desktop. As capturas empacotadas sem projeto e o validador oficial da build são válidos; o estado carregado foi comprovado pelo auditor Qt nativo, que usa o contrato real da MainWindow e projeto fixture.
- Nenhum push, PR ou merge foi realizado nesta execução.
- Os diretórios locais de build e capturas permanecem não rastreados para preservar os artefatos brutos; eles não foram incluídos neste commit.
