# Evidência — Encerramento pós-merge da Etapa 6

## Identificação

- data: 10 de agosto de 2026;
- risco: `R-005 — Exportação de colisão inconsistente`;
- commit funcional: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98`;
- commit documental pré-merge: `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR funcional: `#33`;
- merge na `main`: `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- sistema local: Windows 11;
- Python: 3.11.9;
- dependências: `poetry.lock` vigente.

## Resultado funcional comprovado

Toolbar, painel de física e metadados genéricos usam o contrato
`neoeng-d-trace-collisions` schema v1. A exportação valida referências,
coordenadas finitas, cardinalidade, vértices distintos e área antes de gravar.
O TXT é derivado do mesmo documento canônico e usa substituição atômica.

## Validação local

- testes focais: `32 passed`;
- suíte funcional pré-merge: `542 passed`, `0 failed`, `0 skipped`;`r`n- suíte local do pacote de fechamento: `543 passed`, `0 failed`, `0 skipped`;
- cobertura combinada de linhas e branches: `62.45%`;
- `src/exporters/collision_exporter.py`: `84%`;
- `src/exporters/json_exporter.py`: `93%`;
- `src/ui/main_window.py`: `76%`;
- mypy: zero erros em 66 arquivos;
- Flake8, Black, isort e compilação: aprovados;
- pip-audit: nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- Bandit de alta severidade: zero achados;
- suíte legada: 196 executados, 26 divergências previstas reconciliadas,
  zero inesperadas e zero ausentes;
- busca por referências proibidas e caminhos locais rastreados: zero achados.

## CI da PR

- execução: `31431473940`;
- Linux `93595656414`: `success`, zero anotações;
- Windows `93595656546`: `success`, zero anotações;
- artefato Windows `9079343426`:
  `sha256:d2261a1940427ebca93309570856b5ffb325dad770a75bba355355fe58b57186`;
- artefato Linux `9079311956`:
  `sha256:528cc9a240ad60bb837f51934a76797c3bf1e01d3ee72bfd58b62666e92e5cff`.

## CI pós-merge

- execução: `31431739320`;
- Linux `93596534789`: `success`, zero anotações;
- Windows `93596534725`: `success`, zero anotações;
- artefato Windows `9079450269`:
  `sha256:d5788a961a0d9f12087fe23f872d504b597a5cd598186ff26d0462cfb7ff88ca`;
- artefato Linux `9079413130`:
  `sha256:6712365efa8c02ce275f32674ae3d9d2efea8b75963387d7ef2c16f7b4a7ef27`.

## Limitações e riscos residuais

- perfis específicos das engines permanecem para a Etapa 10;
- auto-interseção e propriedades geométricas amplas permanecem nas Etapas 8 e 9;
- `R-003` e as metas finais de cobertura permanecem abertos;
- CLI integral permanece em `R-006`/Etapa 7;
- build standalone, instalador e aprovação de release permanecem bloqueados.

## Decisão

O commit funcional, a PR, o merge e o CI pós-merge estão ligados por
identificadores verificáveis. O contrato inconsistente que definia `R-005`
foi substituído por uma autoridade única e coberto por testes positivos,
negativos, de round-trip, de UI e de falha atômica.

**ETAPA 6 FORMALMENTE CONCLUÍDA NO ESCOPO APROVADO.**

```text
R005_CLOSED=YES
STAGE6_COMPLETED=YES
STAGE7_STARTED=NO
RELEASE_APPROVED=NO
```
