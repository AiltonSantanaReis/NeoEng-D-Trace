# E08 — Composição 2.5D, iluminação, sombras e FX reais

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E08_CONTRATO_RENDERER_25D_FX_2026-09-08.md`.
Dependência técnica: E07 checkpoint `d35bc84`.

## Estado dos lotes

- E08-A — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: plano de composição e fronteira de backend.
- E08-B — `IN_PROGRESS`: câmera e paralaxe profissional.
- E08-C — `PLANNED`: materiais, normal maps, luzes e sombras.
- E08-D — `PLANNED`: partículas, shaders e pós-processamento.
- E08-E — `PLANNED`: determinismo temporal e matriz de destino.

Nenhum efeito visual será declarado suportado antes de saída observável,
comparação, teste de falha e captura real do binário. Symlink e revisão humana
ficam reservados à auditoria final.

## Análise de impacto E08-A

- módulos: `src/core`, `src/ui/canvas_view.py`, schema V2 apenas quando um
  parâmetro autoral precisar persistência, e testes de composição;
- contratos preservados: V1/V2 existentes, viewport autoral, seleção,
  `position.z`, parallax atual e fallback raster;
- risco principal: alterar o caminho de preview e regressar cenas antigas;
- proteção: plano de renderização puro, testes de ordenação/cache/resize e
  comparação do preview antigo antes de habilitar o novo caminho;
- rollback: feature flag local e fallback raster, sem modificar documentos
  legados.

## Checkpoint técnico E08-A

- Build r28: `release/e08-renderer-20260908-r28`.
- Source commit: `2bd85fc52bf76edcbe0626718eaea839997e8e44`.
- Binário: SHA-256 `7F4F8E95DB57C7E6713CDAA9AA3F7E43A1CAD73F767809EC0FCBBC2567CF0199`.
- Arquivo portátil: SHA-256 `d58e581129fe9382f31ad71c17997771001ccb73212b8a2d3e6062d77e5fed2e`.
- Smoke portátil: `SUCCESS`, 11 checks.
- Suíte oficial: `2051 passed, 2 skipped, 1 warning`.
- Capturas e hashes: `docs/evidence/E08_A_R28_CAPTURAS_MANIFESTO.json`.
- Preview real: `RENDERER RASTER | NATIVE | PREVIEW | 8 PASSES | R1`, controles
  desabilitados e status `Scenario preview — read-only`.
- Retorno real à autoria: `RENDERER RASTER | NATIVE | AUTHORING | 8 PASSES | R1`,
  controles reativados e status `Scenario authoring`.
- Inspeção visual: português preservado, HUD legível, sem clipping observável,
  viewport e inspector estáveis na superfície 3866×2090.

E08-A está selado apenas como checkpoint técnico; E08-B permanece ativo. Symlink
e revisão humana continuam pendentes por autorização e serão executados somente
na auditoria final do Plano Mestre.

## E08-B — contrato de câmera/paralaxe em execução

### Escopo e critérios rastreáveis

- [x] Separar a matemática da câmera do widget Qt e preservar os campos
  legados de profundidade/força.
- [x] Persistir `scroll_x`, `scroll_y`, `offset_x`, `offset_y` e os quatro
  flags de repetição/espelhamento com defaults retrocompatíveis.
- [x] Propagar os novos campos por schema V2, bridge, preview determinístico e
  viewport profissional.
- [x] Expor a edição no inspetor com limites, labels explícitos e operação
  transacional Undo/Redo.
- [x] Cobrir movimento negativo, zoom, âncoras, round-trip, variantes de tile,
  limites inválidos e proteção contra aplicação dupla.
- [ ] Executar suíte oficial, estática, build limpa e captura real do binário
  após o lote; estes gates ainda estão pendentes neste commit de implementação.

### Semântica aprovada

`scroll_x/y` são fatores assinados independentes em `[-4, 4]`; offsets são
finitos em unidades de mundo; repetição/espelhamento são metadados persistidos
que geram variantes determinísticas para o renderer sem reinterpretar `z`.
Defaults (`1, 1, 0, 0, false, false, false, false`) preservam a projeção
anterior. Positivos em `offset_x/y` deslocam o conteúdo para a direita/baixo.

### Estado da implementação

- Commit de implementação: `PENDENTE — lote em execução`.
- Teste focado preliminar: `47 passed` (E08-B, câmera legado, inspector/viewport e E08-A).
- Limitação declarada: captura/build oficial ainda não foram refeitas; não há
  checkpoint técnico E08-B nem afirmação de suporte de atlas/alpha nesta fase.
- Symlink e revisão humana: `DEFERRED_UNTIL_FINAL_AUDIT`, sem reexecução.
