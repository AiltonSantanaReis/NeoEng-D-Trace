# Evidência — Etapas 1 e 2: contrato de integração e manifesto

## Identificação

- Commit testado: `d3d708006db0068d0d08fbbcc0bac05b81a2239c`
- Branch: desenvolvimento local (nome omitido por higiene do repositório)
- Data: 2026-08-16
- Escopo: contrato comum e manifesto dos futuros adaptadores source-only

## Ambiente

- Sistema operacional: Windows
- Python: 3.11.9
- Dependências: Poetry e lockfile do projeto
- Engines Godot/Unity: não executadas nesta etapa; não são declaradas integradas

## Objetivo e escopo

Foi implementado o contrato versionado `neoeng-d-trace-engine-integration` v1
para conectar o JSON de metadados do D-Trace a futuros adaptadores Godot e
Unity. O contrato exige engine suportada, versão do gerador, referência relativa
segura, hash SHA-256 da imagem, hash canônico dos metadados, política de
sincronização unidirecional, diretório de geração, sufixo de override e
`destructive_update: false`.

A gravação do manifesto é determinística e atômica. A etapa não implementa
importadores, recursos nativos, sincronização de overrides ou execução dentro
das engines.

## Entradas e artefatos reais

A auditoria reproduzível foi executada por
`scripts/audit_integration_manifest.py`, usando uma imagem PNG RGBA real e uma
cena real do modelo `Scene` com o objeto `hero` e polígono retangular.

- `docs/evidence/artifacts/integration-manifest/source.png` — SHA-256
  `33b2adecef77add7cad5d25d50dfbea47acf84250d0d578807a97d3768fed416`
- `docs/evidence/artifacts/integration-manifest/godot.integration.json` — SHA-256
  `b6cfdd82821c4be89153ad6c930fff0468f41d10fc13d70165b7254e1561dbea`
- `docs/evidence/artifacts/integration-manifest/unity.integration.json` — SHA-256
  `723a360b115814751afb4c60bcdfef2fbd7d53a30fba0e1f5a3f8474d3f842f8`
- Hash canônico do payload de metadados: `2b8f5247344d1a7e3086f08b162f6f26f88135a96d50f8c4cff0a128c9f0cbf0`
- Índice dos artefatos: `docs/evidence/artifacts/integration-manifest/artifact-index.json`

## Comandos executados

- `poetry run pytest -q tests/test_integration_manifest.py tests/test_json_exporter_contract.py tests/test_stage_10_engine_profiles.py`
- `poetry run pytest -q --disable-warnings --cov=src --cov-branch --cov-report=xml:coverage.xml`
- `poetry run python tools/check_coverage_policy.py coverage.xml`
- `poetry run black --check --diff src/exporters/integration_manifest.py tests/test_integration_manifest.py scripts/audit_integration_manifest.py`
- `poetry run isort --check-only --diff src/exporters/integration_manifest.py tests/test_integration_manifest.py scripts/audit_integration_manifest.py`
- `poetry run flake8 src/exporters/integration_manifest.py tests/test_integration_manifest.py scripts/audit_integration_manifest.py`
- `poetry run mypy src`
- `poetry run python -m compileall -q src scripts`
- `poetry run bandit -q -r src scripts`
- `poetry run pip-audit`
- `poetry run python tools/baseline_integrity.py --verify`
- `poetry run python scripts/audit_integration_manifest.py`

## Resultados

- Testes focados: `25 passed` no contrato; o conjunto de regressão associado
  totalizou `39 passed` antes da expansão dos cenários negativos.
- Suíte completa: `1105 passed`, `10 warnings`, `0 failed`.
- Cobertura: `92,58%` de linhas (`13097/14147`) e `85,17%` de branches
  (`3872/4546`); política aprovada.
- Formatação, imports, lint, mypy e compilação: aprovados.
- Dependências: pip-audit sem vulnerabilidades conhecidas; o pacote local do
  projeto não é publicado no índice e foi apenas reportado como não auditável.
- Bandit: somente 10 alertas `B110` de baixa severidade em código legado,
  sem ocorrência nova no código desta etapa; o comando concluiu sem falha.
- Baseline: verificada com `606` arquivos.
- Reprodutibilidade: execução do script produziu novamente os hashes listados.

## Falhas encontradas e correções

- A primeira execução encontrou duas falhas reais: referência vazia com mensagem
  inconsistente e caminho Windows com unidade não rejeitado. A validação foi
  corrigida e os cenários passaram.
- A política de cobertura inicialmente caiu para `84,80%` de branches. Foram
  adicionados casos negativos reais para entradas inválidas e corrigida a ordem
  de validação dos hashes; a política terminou aprovada em `85,17%`.
- A verificação inicial da baseline listou arquivos novos como inesperados antes
  do versionamento. Após indexação e atualização controlada da baseline, a
  verificação passou.

## Limitações e riscos residuais

- Nenhuma engine Godot ou Unity foi executada; portanto não há evidência de
  importação de Sprite2D, CollisionPolygon2D, Sprite, PolygonCollider2D,
  pivôs, Inspector, UPM, overrides ou atualização automática.
- As etapas 3 a 10 do plano permanecem não iniciadas. O risco R-017 permanece
  aberto.
- Não houve push, PR ou merge nesta etapa local; o commit acima identifica apenas
  o estado técnico comprovado no workspace.

## Decisão

**PARCIAL** — etapas 1 e 2 aprovadas localmente; integração nativa Godot/Unity
**NÃO TESTADA** e não declarada como funcional.