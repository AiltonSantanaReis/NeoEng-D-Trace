# Evidência pré-merge — Etapa 9: colisão estática e APIs

## Identificação

- data: 10 de agosto de 2026;
- branch: `etapa-9-arquitetura-apis`;
- commit técnico testado: `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- estado: **APROVADO LOCALMENTE / NÃO INTEGRADO**;
- `R-008`: aberto até merge e CI pós-merge aprovados;
- release: **NÃO APROVADA**.

## Escopo confrontado

O contrato de produto exige criação, validação, visualização e teste de
sobreposição estática. Física dinâmica, gravidade, corpos e simulação avançada
estão explicitamente fora da versão 1.0. A auditoria, portanto, não converteu o
produto em motor de física: removeu promessas inertes e consolidou o contrato
real de colisão estática.

## Falhas reproduzidas antes da correção

| Caso | Resultado anterior |
|---|---|
| IDs `int` e `str` no mesmo broadphase | `TypeError: '<' not supported between instances of 'int' and 'str'` |
| callback registrado + `step(0.1)` | um passo e um resultado, mas zero callbacks |
| vértice `NaN` | retornava `(False, None)` em vez de rejeitar a entrada |
| vértice consecutivo duplicado | retornava colisão e MTV |
| quadrado dentro da região vazia de um polígono em L | falso positivo `(True, ...)` |
| MTV de dois quadrados sobrepostos | vetor apontava o primeiro polígono para dentro da colisão |

## Causa raiz

1. `UniformGridBroadPhase` ordenava identificadores com `<`, presumindo tipos
   comparáveis.
2. `PhysicsManager` anunciava gravidade, backend, passo fixo e callbacks sem
   implementar esses contratos.
3. SAT era aplicado diretamente a formas côncavas, embora o algoritmo fosse
   válido apenas para polígonos convexos.
4. As entradas não passavam por validação geométrica canônica.
5. A orientação do MTV usava o sentido centro A → centro B, oposto ao vetor
   necessário para retirar A de B.
6. Implementações de SAT, broadphase, decomposição e gerência estavam
   distribuídas sob fronteiras contraditórias de `collision` e `physics`.

## Implementação

- `src.collision` tornou-se a única API pública de colisão estática;
- `StaticCollisionManager` registra cópias imutáveis, valida forma, posição,
  identificador e tamanho da grade, preserva substituição atômica e ordena
  resultados pela ordem de registro;
- formas côncavas são trianguladas para decisão exata de sobreposição; nesses
  casos o retorno não inventa um MTV global a partir de uma colisão parcial;
- formas convexas mantêm MTV, agora orientado para retirar o primeiro polígono;
- `src.core.convex_decomp` contém a decomposição geométrica canônica;
- `src.collision.broadphase` contém o broadphase canônico;
- os cinco módulos de `src.physics` ficaram sem classes ou funções próprias e
  preservam somente reexportações históricas testadas;
- a UI usa “colisão estática”/“forma de colisão” em vez de apresentar o recurso
  como física dinâmica;
- a auditoria AST encontrou somente `format_metadata` repetido entre perfis de
  exportação, interface intencional com implementações específicas por destino.

## Ambiente

- Windows NT `10.0.26200.0`;
- Python `3.11.9`;
- Poetry `2.4.1`;
- pip `26.2.1`;
- SHA-256 de `pyproject.toml`:
  `c882aba9fd677fc138ab9948d776a9b7d26b3f9d7a755f495e39d2b71fd7260a`;
- SHA-256 de `poetry.lock`:
  `b7e94da9a7074347d5a4432cc68ae1f59953af60d1aa62dc970ee7f98579d7b7`.

## Comandos executados

```text
python -m compileall -q src tests tools app.py pack_for_ai.py
python -m flake8 src tests tools app.py pack_for_ai.py
python -m black --check --diff src tests tools app.py pack_for_ai.py
python -m isort --check-only --diff src tests tools app.py pack_for_ai.py
python -m mypy src
python -m pip_audit
python -m bandit -q -r src -lll
python -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml -q
python tools/run_legacy_tests.py --group all
```

## Resultados locais finais

- testes novos da Etapa 9: `39` coletados;
- suíte oficial: `701 passed`, zero falhas, zero erros, zero ignorados;
- suíte histórica: `196` executados;
- reconciliação histórica: `27/27`, zero inesperadas e zero ausentes;
- cobertura global: `73.65%` de linhas e `57.65%` de branches;
- cobertura combinada informada pelo pytest-cov: `69.79%`;
- `src/collision/broadphase.py`: `89%` combinado;
- `src/collision/manager.py`: `94%` combinado;
- `src/collision/sat2d.py`: `95%` combinado;
- `src/core/convex_decomp.py`: `95%` combinado;
- adaptadores em `src/physics`: `100%` combinado;
- mypy: zero erros em `69` arquivos-fonte;
- Flake8, Black, isort, compileall e Bandit: aprovados;
- `pip-audit`: nenhuma vulnerabilidade conhecida nas dependências auditáveis;
  o pacote local não existe no índice público e foi explicitamente informado
  como não auditável pelo nome de distribuição;
- varredura de referências proibidas e caminhos de máquina: zero ocorrências.

## Limitações e riscos residuais

- as metas globais de `90%` de linhas e `85%` de branches não foram atingidas;
  `R-003` permanece aberto para a Etapa 11;
- a API canônica cobre sobreposição estática, não física dinâmica, por decisão de
  produto;
- validações reais em Godot e Unity pertencem à Etapa 10 e não foram inferidas;
- limites operacionais, refatoração Qt ampla, autosave, build, instalador e
  candidato de release permanecem nas Etapas 12–14;
- nenhum resultado local substitui CI de PR e CI pós-merge em Linux e Windows.

## Primeira execução de CI da PR

O run `31444322950` falhou antes da instalação e dos testes nos jobs Linux
`93635193540` e Windows `93635193483`. A causa comum foi o manifesto de baseline
não regenerado após os arquivos intencionais da etapa. A falha não foi tratada
como teste aprovado: o pacote corretivo executa `--write`, confirma `--verify`
localmente e exige nova execução integral dos dois jobs.

## Decisão pré-merge

- `TECHNICAL_COMMIT_TESTED=YES`
- `LOCAL_GATES_STATUS=SUCCESS`
- `PR_CI_EXECUTED=NO`
- `POST_MERGE_CI_EXECUTED=NO`
- `R008_CLOSED=NO`
- `STAGE9_COMPLETED=NO`
- `RELEASE_APPROVED=NO`

**Etapa 9 aprovada localmente para submissão à PR.** O encerramento de `R-008`
e a conclusão da etapa dependem de integração e CI pós-merge aprovados no SHA
resultante.
