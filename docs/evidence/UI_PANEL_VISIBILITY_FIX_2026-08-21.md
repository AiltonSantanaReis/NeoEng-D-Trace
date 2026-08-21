# Correção de visibilidade dos painéis da MainWindow — 2026-08-21

## Escopo

Correção da responsividade da MainWindow nas larguras 1920, 1366 e 1280, com foco em evitar que o `QStackedWidget`, os `QSplitter` e os painéis laterais sejam reduzidos a zero durante redimensionamento nativo do Windows. O contrato do auditor visual também foi corrigido para registrar o tamanho físico de modais Qt em DPI elevado.

Esta evidência não aprova release, push, PR ou merge. Ela registra somente a validação local desta correção.

## Proveniência

- Branch: `Ailton/fix/ui-panel-visibility`
- Commits da correção de UI: `ffb8cf9`, `d09a4cd`
- Commit do contrato do auditor: `bec1348`
- Build oficial usada na validação do executável: commit `d09a4cd1660f944aef6ef001477d7f0c5a2270d5`
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

O script oficial `scripts/build_windows.ps1` foi executado em worktree limpo a partir do commit `d09a4cd`. O validador oficial retornou `SUCCESS` nos 11 checks: CLI, projeto versionado, processamento headless, JSON, GLB, perfis Godot/Unity, GLB dos perfis, abertura/fechamento da GUI e diretório de estado do usuário.

Artefatos da build final local (`release-stage9-ui-fix-final-20260821-103934`):

- `release-manifest.json`: `ed6f0a1c8270e2576a089d94ed95adb4eb8546e858e763c1a362c4ac2c6c29ba`
- `NeoEng-D-Trace.exe`: `a28f9fc8f95b789a3dc832eaecfbc4dd6facf10ee34fca9273c4cf5dc523be9d`
- `NeoEng-D-Trace-CLI.exe`: `545078dc9f01b128f9514b54fe0712a56d7e9488423280247a599dfffc9be94f`
- `NeoEng-D-Trace-0.3.0-win64-portable.zip`: `341054c1f1f87d0670fdc69254ba48ee85a731bb86537e9dddb8d94d1e62f0d8`

## Captura e auditoria visual

O auditor nativo do projeto criou um fixture real, carregou o projeto, selecionou objeto, exercitou o gizmo, alternou as resoluções e disparou a mensagem real de validação `No collision shapes registered. Use Auto-Generate first.`.

Manifesto da auditoria nativa regenerada:

- `source-native-ui-audit-rerun/manifest.json`: `50fef8e8a20ffaaa687bcbb2efd6cc777704a181783aff0303c48cb9981daa42`
- As geometrias registram `panel_stack` visível em todas as três resoluções.
- Em 1920×1080, `side_panel` e `collision_panel` ficaram visíveis no desktop.
- Em 1366×768 e 1280×720, o `compact_panel_tabs` ficou visível com largura 460 e o painel lateral ficou selecionável.
- A mensagem de validação foi capturada nas três resoluções.

O auditor Pillow/OpenCV verificou decodificação, dimensões, transparência determinística, SHA-256, clipping, geometria Qt, sobreposição, paleta escura e geração de anotações:

- Status: `PASS`
- Achados: `0`
- `source-native-ui-visual-audit-final/visual-audit-report.json`: `498761bcd5e3d0189dcccc8ceb1eb89538651927131e98598e601b29b79346bd`

A revisão visual humana das capturas carregadas confirmou: canvas não coberto pelos painéis, painéis laterais presentes, tabs Objects/Layers/Groups/Collision visíveis nas capturas nativas lógicas compactas, gizmo sobre o objeto e modal de validação legível.

## Limitações declaradas

- A captura direta do executável empacotado com projeto carregado não foi considerada prova: a automação do diálogo nativo do Windows permaneceu não determinística sob as janelas existentes no desktop. As capturas empacotadas sem projeto e o validador oficial da build são válidos; o estado carregado foi comprovado pelo auditor Qt nativo, que usa o contrato real da MainWindow e projeto fixture.
- Nenhum push, PR ou merge foi realizado nesta execução.
- Os diretórios locais de build e capturas permanecem não rastreados para preservar os artefatos brutos; eles não foram incluídos neste commit.
