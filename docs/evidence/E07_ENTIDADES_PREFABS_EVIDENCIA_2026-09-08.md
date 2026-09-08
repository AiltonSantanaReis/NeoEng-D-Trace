# E07 — Entidades, componentes, hierarquia e prefabs

Status: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

Contrato ativo: `docs/DECISAO_E07_CONTRATO_ENTIDADES_PREFABS_2026-09-08.md`.
Dependência E06 confirmada no checkpoint técnico `df841ef`.

## Estado dos lotes

- E07-A — `IMPLEMENTED_TESTED`: modelo de entidade, componentes e instâncias.
- E07-B — `IMPLEMENTED_TESTED`: hierarquia espacial, grupos e validações.
- E07-C — `IMPLEMENTED_TESTED`: ciclo completo de prefab e persistência.

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

E07-C adiciona operações atômicas de criar prefab, instanciar, aplicar e
reverter override, atualizar a fonte preservando overrides e desvincular.
`EntityPrefabPanel` expõe o fluxo em português no inspector profissional;
testes Qt cobrem o percurso completo. Suíte oficial após a UI:
`2047 passed, 2 skipped, 1 warning`.

## Checkpoint técnico comprovado

- Build limpa r24: `release/e07-entities-20260908-r24`.
- Source commit: `7c44496a2e93ecfe54eb0612d8edbd389826d72b`.
- Binário: SHA-256 `AA335278578929CA5AAA7BAC73270C7752C7C711B4B922D2EE1F1D7790AF02A5`.
- Arquivo portátil: SHA-256 `281660a1c98751141ce1ddcb1898667f9a394e4d0da0490c94b9d4f293ace988`.
- Smoke portátil: `SUCCESS`, 11 checks.
- Captura real: `docs/evidence/E07_R24_CAPTURAS_MANIFESTO.json`.
- Fluxo visual do binário: entidade criada; prefab v1; instância criada; override
  `components.demo.value`; prefab atualizado para v2; instância desvinculada
  preservando `overrides=1`.
- Inspeção automatizada das imagens: interface em português, painel de entidades
  no topo, controles acessíveis, sem clipping observável e NavMesh ainda visível
  abaixo do painel.

Symlink e revisão humana permanecem pendentes por política autorizada e serão
executados somente na auditoria final do Plano Mestre.
