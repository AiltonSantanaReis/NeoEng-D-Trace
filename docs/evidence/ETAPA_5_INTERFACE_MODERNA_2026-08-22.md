# Etapa 5 — Viewport e HUD da interface moderna

Estado: **implementação concluída localmente; aguardando commit, PR, CI e merge**
Data da execução: 2026-08-22
Branch de trabalho: Ailton/interface-stage5-viewport-hud
HEAD de referência da execução: 8441bf7710b96752fa8e766469900e224cd497d5

## Objetivo e referência visual

A referência aprovada para a interface moderna estabelece um viewport central limpo, com informação operacional discreta e sem uma faixa textual permanente competindo com o conteúdo, o gizmo ou os painéis. O estado de visualização/zoom foi tratado como informação de aplicação e movido para a QStatusBar, preservando o canvas para imagem, overlays e interação.

A alteração não mistura o editor principal com o editor de cenário, não modifica a matemática do gizmo e não remove os controles Lit/X-Ray, Fit ou 1:1.

## Implementação

- CanvasView.viewport_state_changed emite o estado canônico de modo e zoom.
- viewport_state_text() centraliza a representação VIEW: ... | ZOOM: ....
- set_view_mode, set_zoom, fit_to_window e centralização de polígono atualizam o estado observável.
- MainWindow.viewport_status é um QLabel permanente da status bar, com nome acessível, tooltip, largura mínima e estilo derivado dos tokens do tema.
- A pintura normal do MainWindow não chama mais a faixa HUD flutuante do canvas.
- _draw_hud permanece somente como helper opt-in de compatibilidade para callers isolados; ele não é invocado pelo fluxo principal.
- Gizmo, overlays de colisão, X-Ray e painéis laterais permanecem nos contratos existentes.

## Evidências reproduzíveis

Auditor versionado: scripts/audit_stage5_viewport_hud.py.

Artefatos gerados pelo auditor:

- docs/evidence/artifacts/ui-modernization-stage5-20260822/windows-captures/
- docs/evidence/artifacts/ui-modernization-stage5-20260822/windows-visual-audit/
- docs/evidence/artifacts/ui-modernization-stage5-20260822/functional-captures/
- docs/evidence/artifacts/ui-modernization-stage5-20260822/stage5-viewport-hud-report.json

Resultado do auditor completo no backend Qt Windows real:

- decision=PASS
- qt_platform=windows
- visual_findings=0
- functional_failures=0
- functional states=12 (4 estados em cada uma das 3 resoluções)
- windows-captures/manifest.json SHA-256: 4c39ebc724b57242fde9791392e0fcd153f1cec406af430151b2f49dcd459b60

Resoluções reais capturadas:

- 1920×1080
- 1366×768
- 1280×720

Estados funcionais exercitados:

- Lit + 1:1
- X-Ray 1
- Fit
- X-Ray 1 + 1:1

O auditor Pillow/OpenCV validou, nos PNGs versionados no pacote de evidência, decodificação dupla, dimensões, transparência, SHA-256, clipping, geometria Qt, sobreposição e paleta do tema. As imagens anotadas estão em windows-visual-audit/.

## Revisão visual humana

A captura Windows de 1280×720 com projeto carregado foi inspecionada visualmente. O texto da status bar está legível e permanece no rodapé; o canvas não contém a faixa HUD antiga; o gizmo permanece dentro do viewport; a barra esquerda e o painel direito não cobrem o indicador. A captura Windows de 1920×1080 também foi inspecionada para confirmar o mesmo arranjo em área ampla.

O capturador headless existente também foi executado e retornou zero achados estruturais. Entretanto, o backend headless local não registrou famílias em QFontDatabase e exibiu tofu nas imagens; por isso ele não foi usado como prova tipográfica. A comprovação visual final desta etapa usa as capturas do backend Windows real.

## Testes executados

- ..venvScriptspython.exe -m pytest -q tests/test_stage5_viewport_hud.py tests/test_stage4_ui_top_toolbar.py tests/test_ui_defect_regressions.py --tb=short
  - 10 passed
- ..venvScriptspython.exe -m py_compile scripts/audit_stage5_viewport_hud.py
  - PASS
- ..venvScriptspython.exe scripts/audit_stage5_viewport_hud.py
  - PASS, conforme campos acima
- git diff --check
  - PASS

## Limitações declaradas

- Esta evidência comprova a etapa localmente no backend Windows real. Ainda não comprova CI, PR, merge ou estado pós-merge.
- A ausência de fontes no backend headless é uma limitação do ambiente de captura; não foi mascarada nem corrigida por alteração de regra.
- A Etapa 5 não altera o gizmo profissional nem os painéis laterais; esses itens continuam nos gates das etapas correspondentes.

## Decisão

A implementação da Etapa 5 está completa e comprovada localmente. O próximo gate legítimo é a revisão do diff, inclusão explícita dos arquivos novos, atualização do baseline/manifests contra os blobs Git e somente então commit, validação pós-commit, push, PR, CI, merge autorizado e validação pós-merge.