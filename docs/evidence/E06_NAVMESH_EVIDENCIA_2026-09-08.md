# E06 — NavMesh 2D

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E06_CONTRATO_NAVMESH_2026-09-08.md`. O lote inicia
com modelo fonte separado do bake, caminho determinístico em superfície 2D,
persistência versionada e negativos canônicos. O conjunto focado E06 passou
`7 passed`; a regressão completa passou `2040 passed, 2 skipped, 1 warning`.
Mypy focado passou para `navmesh_2d.py`, `navmesh_io.py` e
`navmesh_panel.py`; compileall e diff-check também passaram. Build e captura
real serão registrados antes do checkpoint técnico.
