# E07 — Entidades, componentes, hierarquia e prefabs

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E07_CONTRATO_ENTIDADES_PREFABS_2026-09-08.md`.
Dependência E06 confirmada no checkpoint técnico `df841ef`.

## Estado dos lotes

- E07-A — `IMPLEMENTED_TESTED`: modelo de entidade, componentes e instâncias.
- E07-B — `IMPLEMENTED_TESTED`: hierarquia espacial, grupos e validações.
- E07-C — `PLANNED`: ciclo completo de prefab e persistência.

Nenhuma alegação funcional é feita antes dos testes focados, suíte oficial,
estática, build limpa e captura real do binário. Symlink e revisão humana ficam
reservados à auditoria final.

E07-A já possui contrato V2 persistente com ID estável, transformação, camada,
visibilidade/lock, componentes tipados/versionados e `instance_of` opcional.
Os negativos de IDs duplicados, componente duplicado, versão inválida, camada
inexistente, origem inexistente e auto-instância estão cobertos. Testes focados
e regressão relevante passaram; a suíte oficial atual está em `2043 passed,
2 skipped, 1 warning`. Mypy do schema e compileall passaram. Build e captura
real permanecem pendentes até E07-A/B/C formarem o fluxo executável completo.

E07-B acrescenta `parent_entity_id` como relação espacial independente de
membership em grupos, valida ciclos e referências inexistentes no schema e
expõe operação transacional `set_entity_parent` no modelo Qt-independent.
Suíte oficial após esta extensão: `2044 passed, 2 skipped, 1 warning`.
