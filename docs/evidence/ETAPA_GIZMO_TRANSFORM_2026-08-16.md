# Evidência — Gizmo contextual 2D

## Escopo

Implementação do gizmo 2D inspirado na referência visual anexada, sem simular
um eixo 3D inexistente no canvas: X/Y e XY para translação, anel Rz para
rotação, alças X/Y para escala não uniforme, anel central para translação
livre e alça interna para escala uniforme. A profundidade Z permanece como
metadado explícito no feedback.

O gizmo usa o pivô persistido de um objeto único e o centro geométrico de uma
seleção múltipla. A transformação é transacional, preserva polígonos,
Béziers, colisão simples e partes compostas, e gera uma única entrada de
Undo/Redo.

## Provas executadas

Com o ambiente local do projeto e sem alterar regras de teste:

- `python -m py_compile` dos módulos alterados: aprovado.
- `pytest tests/test_transform_preview_regression.py tests/test_reference_gizmo.py tests/test_transform_gesture.py -q`: `9 passed`.
- `pytest tests/test_stage_5_package_3a_gizmo_gesture.py tests/test_stage_11_canvas_export_branch_coverage.py tests/test_critical_ui_coverage.py -q`: `33 passed`.
- `pytest tests/test_selection_invariants.py tests/test_stage_5_package_5a_creation_commands.py tests/test_stage_5_package_4a_object_deletion_paths.py -q`: `42 passed`.
- Capturador oficial `scripts/audit_ui_capture.py`: executado nas resoluções 1920×1080, 1366×768 e 1280×720; cada resolução produziu os estados sem projeto, projeto com painéis, validação, modal real e feedback do gizmo.

## Artefatos

O conjunto final está em `docs/evidence/artifacts/ui-audit-gizmo-v4/` e seu
`manifest.json` registra tamanho, SHA-256, resolução efetiva e a mensagem real
de validação: `No collision shapes registered. Use Auto-Generate first.`

## Inspeção visual

- O gizmo aparece sobre o pivô do objeto, não no canto fixo anterior.
- X vermelho, Y verde orientado para cima, anel ciano Rz e núcleo ciano são
  distinguíveis no tema escuro.
- Nas três resoluções, o gizmo não invade os painéis laterais.
- O feedback ativo foi ajustado para duas linhas e largura limitada ao canvas;
  a captura 1280×720 mantém margem interna e não corta o painel.

Limitação observada e não mascarada: neste ambiente Qt `offscreen`, o banco de
fontes retornou zero famílias, portanto a captura rasteriza textos como
quadrados. Isso impede certificar a forma dos glifos tipográficos neste modo;
as dimensões, margens, cores e ausência de sobreposição foram verificadas. A
validação tipográfica final requer execução em uma sessão Qt com fontes
disponíveis.

## Decisão

As provas funcionais e geométricas desta etapa estão aprovadas. Push, merge e
integração final ainda não foram realizados; dependem da suíte completa e da
revisão final do diff.
