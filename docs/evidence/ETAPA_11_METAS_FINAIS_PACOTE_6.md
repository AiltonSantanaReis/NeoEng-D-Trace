# Etapa 11 — metas finais de cobertura — Pacote 6

Data da validação: 11 de agosto de 2026.

Estado: **PACOTE TÉCNICO PRÉ-MERGE ACEITO; INTEGRAÇÃO PENDENTE**.

## Objetivo e escopo

O Pacote 6 atinge as metas quantitativas da Etapa 11 sem alterar código de
produção. Foram adicionados 67 testes comportamentais e de ramos para:

- modelo de cena e invariantes de mutação;
- janela principal, persistência, exportação e caminhos Qt opcionais;
- laço magnético síncrono e assíncrono, incluindo canvas Qt real offscreen;
- caneta Bézier, edição persistente, comandos e renderização offscreen;
- painel de colisões, rollback de cache e exportação atômica de sprites.

Arquivos adicionados:

- `tests/test_stage_11_scene_branch_coverage.py` — 14 testes;
- `tests/test_stage_11_main_window_branch_coverage.py` — 19 testes;
- `tests/test_stage_11_magnetic_lasso_branch_coverage.py` — 12 testes;
- `tests/test_stage_11_pen_tool_branch_coverage.py` — 15 testes;
- `tests/test_stage_11_collision_sprite_branch_coverage.py` — 7 testes.

O commit técnico validado é
`d5a7b8559927dca130d6d47409988da07ef1dd7e`. A base integrada permanece
`5e88c8d548e2b60612601f83e1bf24aeb91081bb`; a PR `#45` continua draft e não
foi mesclada.

## Resultados locais reproduzíveis

Ambiente: Windows, Python 3.11.9, Qt offscreen.

Comando oficial:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
```

Resultado final após baseline rastreado:

- `877 passed`;
- `10.787/11.628` linhas cobertas: `92,77%`;
- `3.147/3.700` branches cobertos: `85,05%`;
- cobertura combinada: `90,91%`;
- metas globais de 90% de linhas e 85% de branches atingidas;
- margem da meta de branches: 2 branches;
- baseline verificado: 318 arquivos.

Módulos diretamente priorizados no pacote:

| Módulo | Linhas | Branches | Cobertura reportada |
|---|---:|---:|---:|
| `src/models/scene.py` | 478/495 | 181/196 | 95% |
| `src/ui/main_window.py` | 642/645 | 119/124 | 99% |
| `src/tools/magnetic_lasso.py` | 731/770 | 221/274 | 92% |
| `src/tools/pen_tool.py` | 456/465 | 153/170 | 96% |
| `src/ui/collision_panel.py` | 158/158 | 38/38 | 100% |
| `src/exporters/sprite_exporter.py` | 117/122 | 45/48 | 95% |

## Portões complementares locais

- `poetry check --lock --strict`: aprovado;
- `compileall`: aprovado;
- `flake8`: aprovado;
- `black --check --diff`: 148 arquivos sem alteração necessária;
- `isort --check-only --diff`: aprovado;
- `mypy src`: zero problemas em 70 arquivos;
- `pip-audit`: nenhuma vulnerabilidade conhecida; o pacote local não publicado
  não é auditável no índice público e foi reportado como tal;
- `bandit -q -r src -lll`: zero achados de severidade alta;
- baseline: 318 arquivos verificados antes e depois da suíte;
- auditoria literal do diff preparado: nenhuma referência proibida e nenhum
  caminho pessoal local.

## Suíte legada preservada

A execução local completa registrou:

- 196 testes históricos;
- 27 falhas esperadas e exatamente reconciliadas;
- zero erros, zero ignorados;
- zero falhas inesperadas e zero falhas esperadas ausentes.

As falhas históricas não foram ocultadas nem convertidas em sucesso. O gate é a
reconciliação exata `27/27`.

## Transparência sobre iterações

Antes da aprovação final, ocorreram falhas controladas de desenvolvimento:

- 2 falhas iniciais no pacote da cena por dublê opcional e expectativa de
  reassociação de camada; ambas corrigidas no teste;
- 2 expectativas incorretas no texto de colisões e um bloqueio modal de menu Qt
  no pacote da janela; o menu foi substituído por dublê determinístico, mantendo
  a janela real;
- 2 erros de teardown por estados inválidos deliberados; os testes passaram a
  restaurar explicitamente o estado;
- 1 expectativa incorreta de deduplicação no pacote magnético;
- 2 falhas iniciais e 1 residual no pacote da caneta por hit-test de handle,
  nome real do enum e escopo do dublê de preview;
- 1 fixture RGBA transparente no pacote de sprites;
- primeira rodada estática rejeitada por um import não usado e duas linhas
  longas; segunda rodada rejeitada por uma linha em branco do Black;
- a primeira auditoria literal de caminhos usou regex inválida e foi descartada;
  a repetição com correspondência literal foi aprovada;
- a primeira espera do CI expirou localmente; o run permaneceu em execução e
  concluiu posteriormente com sucesso.

Nenhuma dessas execuções intermediárias foi usada para aprovar o pacote.

## CI técnico do Pacote 6 auditado

Run `31488173784`, ligado ao merge sintético
`040c22f376a067d1edbe2ae11d1f6e1015908c3d`, com pais:

- base `5e88c8d548e2b60612601f83e1bf24aeb91081bb`;
- HEAD técnico `d5a7b8559927dca130d6d47409988da07ef1dd7e`.

A árvore do merge sintético é idêntica à árvore do HEAD técnico.

Jobs:

- Linux `93768251593`: sucesso;
- Windows `93768251612`: sucesso;
- zero anotações reportadas pelos check-runs.

Os dois jobs registraram:

- `877 passed`;
- total `11.628` linhas, `841` ausentes, `3.700` branches e `477` branches
  parciais no relatório terminal;
- cobertura combinada `90,91%`;
- mypy sem problemas em 70 arquivos;
- nenhuma vulnerabilidade conhecida;
- baseline de 318 arquivos antes e depois da validação.

Artefatos oficiais:

- Windows `9100022150`, digest
  `sha256:912182799ec12f2560ea19fdcffe523caec74200314c12db00d3c20649b2c8e5`;
- Linux `9099983296`, digest
  `sha256:c0ce4a730f12830ef97591f4359dd3962a0d0332b7a0cff46ff57b7f85a5b9b3`.

Os ZIPs brutos baixados reproduziram exatamente esses digests. A cobertura XML
local, Linux e Windows coincidiu semanticamente:

- linhas: `10.787/11.628`;
- branches: `3.147/3.700`;
- hash semântico:
  `a960b781f6aaa498b08770ea5f16dcce68f9eee440a752e85c7c07d2ee05b5c1`.

A inspeção recursiva auditou 129 arquivos ZIP e 1.418 payloads, sendo 1.169
payloads textuais, sem referência proibida nem caminho pessoal local. O resumo
legado remoto confirmou 196 testes, reconciliação `27/27`, zero inesperadas,
zero ausentes e worktree limpa.

## CI documental final do Pacote 5

O run `31484936980`, ligado ao HEAD documental
`3316049050f54d5eb987a0a4e53e3f6e801d9acb`, também foi aceito antes deste
pacote. Linux `93758059365` e Windows `93758059453` aprovaram 810 testes,
baseline 313 e cobertura idêntica do Pacote 5. Os artefatos `9098756206` e
`9098776090` foram auditados recursivamente sem violações.

## Decisão e riscos

- as metas quantitativas de cobertura da Etapa 11 estão comprovadas;
- `R-003` permanece **ABERTO** até integração e CI pós-merge no SHA resultante;
- a Etapa 11 permanece em andamento até o fechamento pós-merge;
- `R-011` e `R-012` permanecem abertos para as Etapas 13 e 12;
- autosave, build, instalador e validações reais de release permanecem para as
  Etapas 13 e 14;
- release continua **NÃO APROVADA**.

## Marcadores auditáveis

```text
PACKAGE6_TECHNICAL_COMMIT=d5a7b8559927dca130d6d47409988da07ef1dd7e
PRE_MERGE_CI_RUN=31488173784
PRE_MERGE_CI_STATUS=ACCEPTED
LOCAL_TESTS_PASSED=877
LINE_COVERAGE=10787/11628
BRANCH_COVERAGE=3147/3700
COVERAGE_TARGETS_MET=YES
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
