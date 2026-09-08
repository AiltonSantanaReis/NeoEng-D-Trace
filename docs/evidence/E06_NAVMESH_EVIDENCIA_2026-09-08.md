# E06 — NavMesh 2D

Status: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

Contrato ativo: `docs/DECISAO_E06_CONTRATO_NAVMESH_2026-09-08.md`. O lote inicia
com modelo fonte separado do bake, caminho determinístico em superfície 2D,
persistência versionada e negativos canônicos. O conjunto focado E06 passou
`7 passed`; a regressão completa passou `2040 passed, 2 skipped, 1 warning`.
Mypy focado passou para `navmesh_2d.py`, `navmesh_io.py` e
`navmesh_panel.py`; compileall e diff-check também passaram. Build e captura
real foram concluídos no binário oficial r22. O manifesto canônico está em
`docs/evidence/E06_R22_CAPTURAS_MANIFESTO.json`.

Evidência final do checkpoint técnico:

- branch/commit do binário: `Ailton/e06-navmesh-20260908` /
  `3eba4cc461386f4a37bd03e0597400eb6feb68bf`;
- build: `release/e06-navmesh-20260908-r22`, smoke `SUCCESS` em 11 checks;
- binário SHA-256: `F704E4CAA552B352718FAC0AFC970B36226DAF9EBA14CB61F63F524FF4D3D7C3`;
- arquivo portátil SHA-256:
  `E5E627F092F15B9AF0600FE235B5090B487EC872BA2070E1D548DD0AAE8415D6`;
- captura real: `artifacts/e06-navmesh-20260908/binary-capture-r22-final`;
- fluxo observado: projeto carregado, inspector visível, região e obstáculo
  criados, bake com caminho de 12 pontos, save do sidecar e reopen com estado
  de bake obsoleto corretamente comunicado;
- todos os hashes e limitações estão registrados no manifesto acima.

O checkpoint técnico está aprovado. Symlink e revisão humana continuam
adiados para a auditoria final conforme autorização e governança.
