# Etapa 0 — Baseline visual e contrato de escopo — 2026-08-21

## Decisão

**APROVADO somente para caracterização reproduzível da baseline.** Este relatório não aprova implementação, release, PR, merge ou suporte adicional.

- HEAD observado: `5879d189ccddb92645699ab8ee5f7cb0fc08e83f`
- Branch: `Ailton/fix/ui-panel-visibility`
- Worktree limpo: `false`
- Auditor automático: **PASS**, 0 findings
- Revisão visual do agente: **COMPLETED**
- Confirmação humana independente: **NOT_CONFIRMED**

## Escopo executado

A aplicação real foi capturada nas resoluções lógicas 1920×1080, 1366×768 e 1280×720 nos estados `sem_projeto`, `projeto_paineis`, `validacao_janela`, `validacao_modal` e `gizmo_feedback`. O fluxo usou a `MainWindow`, fixture de projeto, seleção real, transação de gizmo e mensagem real do `CollisionPanel`.

A captura nativa registrou tamanhos físicos distintos sob DPI elevado; esses bytes não foram normalizados nem substituídos por capturas antigas.

## Auditoria automática

O auditor Pillow/OpenCV verificou: decodificação por Pillow e OpenCV, dimensões, transparência, hashes SHA-256, clipping, geometrias Qt, sobreposição, paleta QSS escura e geração de anotações.

- Manifesto bruto: `raw-captures/manifest.json`
- Relatório visual: `visual-audit/visual-audit-report.json`
- Findings automáticos: `0`
- Índice completo: `artifact-index.json`

## Observações visuais reais da baseline

1. Barra esquerda com botões predominantemente textuais e bordas laranjas espessas; candidato à Etapa 3.
2. Barra superior com agrupamento visual inconsistente e excesso de texto; candidato à Etapa 4.
3. Indicador `VIEW/ZOOM` permanece dentro do viewport; candidato à Etapa 5.
4. Painéis estão legíveis nesta execução e não apresentaram clipping automático, mas a densidade/hierarquia visual permanece candidata à Etapa 7.
5. O DPI local produz diferença entre tamanho lógico e físico; deve ser coberto pela Etapa 9.

Essas observações são findings de design e baseline, não foram removidas para obter `PASS` e não significam que o auditor geométrico falhou.

## Limitações e regra de não extrapolação

- A árvore possui artefatos locais não rastreados de execuções anteriores; eles foram preservados.
- A automação não prova intenção estética nem substitui confirmação humana independente.
- Nenhuma alteração de código, QSS, contrato ou comportamento foi feita na Etapa 0.
- Os hashes e métricas pertencem somente ao HEAD e aos bytes desta execução.

## Reprodução

Consultar `stage0-baseline-report.json` para os comandos exatos, ambiente, estados, tamanhos, hashes e decisões. Não reutilizar estes resultados para aprovar um SHA diferente.
