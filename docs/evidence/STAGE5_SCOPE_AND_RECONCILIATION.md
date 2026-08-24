# Etapa 5 — Reconciliação, auditoria e evidências

## Escopo autoritativo

Esta etapa cobre exclusivamente o Viewport/HUD e o Mask Viewer, conforme o texto autoritativo do plano e a baseline final encadeada. O pacote não antecipa funcionalidades das Etapas 6–14 e não altera o produto para acomodar auditorias históricas.

No Viewport/HUD foram verificados: Lit/X-Ray, zoom, pan, snap, grade, gizmo, seleção, coordenadas do cursor/transformação, estado persistente na QStatusBar, mensagem temporária, compactação responsiva e não sobreposição com a área útil do viewport.

No Mask Viewer foram verificados: abertura, imagem original, Sobel, Canny, Laplacian, reset, preenchimento/centralização, foco, mouse real, teclado real, ROI, estados inválidos, feedback de erro, clipping e geometria nas resoluções 1280x720, 1366x768 e 1920x1080.

## Reconciliação aplicada

1. O HUD mantém o estado global na barra inferior e o detalhe completo no tooltip/status do viewport; em larguras compactas os rótulos são abreviados sem desaparecer.
2. O estado de pan passou a ser exposto explicitamente no detalhe do viewport, fechando a lacuna entre a implementação e a matriz de evidências.
3. O Mask Viewer normaliza imagens grayscale, BGR e BGRA/RGBA antes de construir o QImage e desacopla a memória do QImage do buffer temporário. Isso evita interpretação incorreta de canais e lifetime inválido.
4. A auditoria independente mede geometrias no mesmo sistema de coordenadas, referencia cada captura por SHA-256 e inclui capturas negativas de estado sem imagem.

## Evidência executada

O auditor independente é `scripts/audit_stage5_contract.py`. Ele executa o Qt real no backend Windows, cria fixtures determinísticas, percorre 3 resoluções, 4 estados de viewport, 4 modos do Mask Viewer, interações de mouse/teclado/ROI e valida a auditoria visual. O snapshot é gerado por `scripts/generate_stage5_snapshot.py` e permanece vinculado ao snapshot pai da Etapa 4 e ao manifesto `FINAL_TARGET`.

Artefatos principais:

- `artifacts/stage5-snapshot-20260824/stage5-contract-audit.json`
- `artifacts/stage5-snapshot-20260824/raw-captures/manifest.json`
- `artifacts/stage5-snapshot-20260824/visual-audit/visual-audit-report.json`
- `artifacts/stage5-snapshot-20260824/full-suite-junit.xml`
- `artifacts/stage5-snapshot-20260824/stage5-report.json`
- `artifacts/stage5-snapshot-20260824/stage5-manifest.json`

## Critério de decisão

`REVIEW_REQUIRED` é o resultado correto antes da revisão humana. A Etapa 5 só poderá ser declarada formalmente concluída após: auditoria independente PASS, suíte completa sem falhas/erros, validação dos hashes e da cadeia, aprovação humana explícita, commit do escopo e revalidação no SHA final. A auditoria visual automatizada não substitui a revisão humana das capturas.

## Limites declarados

- A matriz de DPI é gate específico da Etapa 9; esta etapa prova as três resoluções lógicas requeridas.
- A matemática profissional do gizmo permanece no escopo da Etapa 6; aqui são provados visibilidade, estado e não sobreposição.
- Logs de fallback GPU não foram mascarados: o processamento continua pelo caminho CPU explicitamente reportado e os comportamentos observáveis foram auditados nesse caminho.
