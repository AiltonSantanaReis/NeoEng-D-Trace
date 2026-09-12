# E05 — Colisores próprios de cenário

Status: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

Contrato ativo: `docs/DECISAO_E05_CONTRATO_COLLIDERS_2026-09-08.md`. A etapa
depende do checkpoint técnico E04 (`4a09aa5`) e permanece no mesmo worktree e
linha de continuidade.

## Metas rastreáveis

- E05-A: modelo versionado de coleção/camada física e validação canônica;
- E05-B: comandos transacionais para criar, editar, mover, duplicar, remover e
  alternar overlay;
- E05-C: formas caixa, círculo, polígono, segmento/cadeia e trigger, com
  categorias/máscaras e vínculo local opcional;
- E05-D: persistência, teste mínimo real de overlap/trigger e compatibilidade;
- E05-E: UI do cenário, capturas reais, negativos e destino representativo.

Symlink e revisão humana continuam reservados à auditoria final do plano.

## Evidência técnica r15

- Commit de origem: `79d768ab5b97403294a3f013c6c92aea15dd4ce5` na branch
  `Ailton/e05-colliders-20260908`.
- Build oficial: `release/e05-colliders-20260908-r15`; binário SHA-256
  `A9E9EF4142A46B706F74A5B3B54A0508768C35DEE389124A8034AD1CC2774F29`;
  smoke `SUCCESS` com 11 verificações; archive SHA-256
  `5267B370B0547C6C3DA1B0E5AC59497728AD13ED2ABBBBB154CE3B40A11EC201`.
- Suite focada E05 + separação do editor: `29 passed`.
- Suite oficial anterior ao pacote: `2033 passed, 2 skipped, 1 warning`;
  os dois skips continuam registrados como limitação de privilégio local.
- Estática já executada no lote: `compileall`, `mypy src`, Black/isort no
  escopo E05, diff-check e validação do registro central.
- Captura real do binário: manifesto
  `docs/evidence/E05_R15_CAPTURAS_MANIFESTO.json`. O fluxo observou criação
  de caixa e círculo, listagem independente e tradução PT-BR no editor real.
- Persistência, overlap, trigger, Undo/Redo e rejeições canônicas foram
  verificados pelo conjunto focado; a captura visual registra os estados
  pós-ação, mas não reclassifica a captura automatizada como revisão humana.

O checkpoint técnico não encerra o aceite final do plano: symlink e revisão
humana continuam `PENDING_EVIDENCE` para E13/auditoria final.
