# Evidência — Etapa 4B.4: exportação de cenário e consumidores

## Identificação

- Escopo: exportação runtime JSON determinística do sidecar `.ndtscenario.json`,
  ação de exportação na interface e consumo real da hierarquia/metadata por
  Godot e Unity.
- Commit técnico publicado: `456a967`.
- Correção de fechamento publicada: `c888c0d`.
- Branch: feature branch (identifier omitted by repository hygiene gate).
- Estado: **APROVADO NO ESCOPO 4B.4 / ETAPA 4B.5 AINDA PENDENTE**.
- Artefatos: `docs/evidence/artifacts/stage4b4-engine-validation-2026-08-18/`.

## Contrato entregue

O exportador produz o formato `neoeng-d-trace-scenario-runtime`, versão 1,
com `generator`, hash do sidecar de origem, referência hash-bound do projeto,
câmera, ordem das camadas, visibilidade, IDs de objetos e os três parâmetros
de parallax. A serialização é UTF-8, canônica, determinística e salva por
substituição atômica.

O sidecar v1 e o schema do projeto não foram alterados. A profundidade de
parallax continua separada de `SceneObject.position.z` e de `z_depth` dos
manifestos de sprites.

Na interface, `Scenario > Export Runtime JSON` usa a mesma fonte de estado
validado da autoria e recebe o ID estável `scenario.export`; fica desabilitado
sem projeto carregado. O menu do addon Godot também expõe a validação do export.

Os consumidores não inventam recursos de sprite: Godot cria uma hierarquia
`Node2D` com metadata de cenário; Unity cria uma hierarquia de `GameObject`
com componentes de metadata. O primeiro MVP não declara runtime de parallax,
criação de sprites ou importação de texturas a partir deste export.

## Testes Python e gates

Ambiente local: Windows, Python 3.11.9, PySide6, Godot 4.7 e Unity
6000.5.7f1.

```text
pytest -q --tb=short                                      1320 passed, 2 skipped, 10 warnings
pytest --cov=src --cov-branch --cov-fail-under=90 ...       1320 passed, 2 skipped, 10 warnings
check_coverage_policy.py coverage.xml                      PASS
black/isort/flake8                                          PASS
mypy (4 arquivos Python)                                    Success: no issues found
Bandit no produto                                          nenhum achado
```

O XML de cobertura registrou 16.164 linhas, 14.988 cobertas (92,72%) e
5.162 branches, 4.393 cobertos (85,10%). O relatório total exibido pelo
pytest foi 90,88%; o gate separado de branches permaneceu acima de 85%.
Os dois skips continuam sendo os testes históricos condicionais de symlink;
não foram criados, removidos ou usados para fabricar aprovação.

Testes negativos adicionados cobrem formato, versão, chaves, hashes, câmera,
camadas, referências duplicadas, parallax fora do intervalo, destino ausente e
entrada de documento inválida. A suíte focal da etapa terminou com 28 passed.

## Execução real Godot/Unity

O harness reproduzível é `scripts/audit_stage4b4_engines.py`. Ele cria fixtures
temporárias, copia somente fontes dos adaptadores, executa os processos reais,
sanitiza logs de host antes de persistir os artefatos e calcula o índice SHA-256.

O relatório final `engine-report.json` registrou:

| Consumidor | Payload válido | Payload inválido | Resultado |
|---|---:|---:|---|
| Godot importador headless | exit 0 | exit 1 | PASS |
| Godot Editor com addon habilitado | exit 0 | — | PASS |
| Unity Editor batch | exit 0 | exit 1 | PASS |

Os logs positivos registraram `SCENARIO_ENGINE_STAGE4B4=SUCCESS`, duas camadas,
uma referência de objeto, metadata-only e preservação dos valores de parallax.
Os logs negativos falharam pelos contratos esperados: o Godot reportou campos
obrigatórios ausentes e o Unity reportou export runtime incompatível.

O export usado nos dois consumidores tem SHA-256
`75ba287e57a77e86b5383030da2ae9a5cf62e753e29f7e833b371f2b8e24bfdc`.
O índice contém 7 arquivos de evidência; sua verificação independente encontrou
zero divergências de hash e zero caminhos absolutos locais. O teste de
privacidade do repositório passou depois da sanitização dos identificadores
LicenseClient, PIDs, IDs de sessão/máquina e endpoints emitidos pelo Unity.

## Limites declarados

Esta etapa não implementa partículas, shaders, DoF, streaming, runtime completo,
criação automática de sprites/AtlasTexture/PolygonCollider2D ou
`PolygonCollider2D` a partir do cenário. Essas capacidades permanecem fora do
MVP e não são apresentadas como PASS. O Unity recebe e materializa metadata de
cenário; não é classificado como falha por não possuir um runtime de parallax
automático neste contrato.

## Decisão

**APROVADO NO ESCOPO DA ETAPA 4B.4.** Exportação, ação de UI, adaptadores fonte,
testes positivos/negativos, execução real Godot/Unity, sanitização, hashes e
regressão foram comprovados. A Etapa 4B geral não está encerrada: a Etapa 4B.5
de benchmark, determinismo ampliado, revisão, CI e merge permanece pendente.
