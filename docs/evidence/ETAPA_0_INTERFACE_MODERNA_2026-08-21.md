# Etapa 0 — Baseline visual e contrato de escopo — 2026-08-21

## Estado formal

**APROVADO somente para caracterização reproduzível da baseline.** Não é aprovação de implementação, release, PR ou merge.

- SHA do código sob teste: `5879d189ccddb92645699ab8ee5f7cb0fc08e83f`
- Branch: `Ailton/fix/ui-panel-visibility`
- Worktree durante a captura: `false`
- Auditor Pillow/OpenCV: **PASS**; findings: **0**
- Revisão visual do agente: **COMPLETED**
- Confirmação humana independente: **NOT_CONFIRMED**

## Escopo e execução real

A `MainWindow` real foi executada em Windows com `QT_QPA_PLATFORM=windows` e capturada nas resoluções lógicas 1920×1080, 1366×768 e 1280×720. Para cada resolução foram gerados os estados `sem_projeto`, `projeto_paineis`, `validacao_janela`, `validacao_modal` e `gizmo_feedback`.

O fluxo exercitou fixture de projeto, seleção real de objeto, transação real do gizmo e mensagem real do `CollisionPanel`: `No collision shapes registered. Use Auto-Generate first.`

## Auditoria automática e artefatos

O auditor verificou decodificação Pillow/OpenCV, dimensões, transparência, SHA-256, clipping, geometrias Qt, sobreposição, paleta QSS escura e PNGs anotados.

- Pacote: `artifacts/ui-modernization-stage0-20260821/`
- Manifesto de capturas: `artifacts/ui-modernization-stage0-20260821/raw-captures/manifest.json`
- SHA-256 do manifesto: `50fef8e8a20ffaaa687bcbb2efd6cc777704a181783aff0303c48cb9981daa42`
- Relatório visual: `artifacts/ui-modernization-stage0-20260821/visual-audit/visual-audit-report.json`
- SHA-256 do relatório visual: `498761bcd5e3d0189dcccc8ceb1eb89538651927131e98598e601b29b79346bd`
- Índice de artefatos: `artifacts/ui-modernization-stage0-20260821/artifact-index.json`
- Testes dos auditores: `10 passed`
- Suíte integral: `1576 passed, 2 skipped`
- Scripts de auditoria: compilação `py_compile` aprovada
- Índice: `38 files`, verificado byte a byte

## Findings de qualidade visual da baseline

Os findings abaixo são observações de design para etapas futuras, não foram ocultados para obter `PASS`:

1. Barra esquerda com botões predominantemente textuais e bordas laranjas espessas — Etapa 3.
2. Barra superior com agrupamento visual inconsistente e excesso de texto — Etapa 4.
3. Indicador `VIEW/ZOOM` dentro do viewport, a revisar contra gizmo e conteúdo — Etapa 5.
4. Painéis legíveis nesta execução e sem clipping automático; densidade e hierarquia ainda devem ser modernizadas — Etapa 7.
5. DPI local de 200% produz diferença entre tamanho lógico e físico; ambos foram preservados — Etapa 9.

O auditor automático encontrou zero violações geométricas ou de bytes. Isso não significa que a interface esteja visualmente concluída.

## Limitações

- A árvore local contém diretórios de builds/capturas não rastreados de execuções anteriores; foram preservados e não entram neste commit.
- A inspeção visual do agente não substitui confirmação humana independente quando exigida.
- Nenhum código, QSS, contrato, teste ou regra foi alterado na Etapa 0.
- Os resultados pertencem ao SHA do código sob teste e aos bytes do pacote identificados acima; não devem ser reutilizados para outro SHA sem rerun.

## Reprodução

Com o repositório configurado, executar os comandos registrados em `artifacts/ui-modernization-stage0-20260821/stage0-baseline-report.json`. O relatório é fail-closed: ausência de artefato, divergência de hash ou alteração de SHA exige nova execução.
