# Evidência — Etapa 4B.1: schema lateral versionado

## Identificação

- Escopo: documento lateral de cenário versionado para autoria de câmera/parallax.
- Commit técnico testado: `0290f60e5c7186c42e02402d119fc37a27edbacd`.
- Base do incremento: `b1757f8cda3f7b7b7897d2519848a3087db74850`.
- Estado: **APROVADO NO ESCOPO DO SCHEMA LATERAL / NÃO INTEGRADO À UI, AO PREVIEW OU AOS EXPORTADORES**.
- A identificação literal da branch de trabalho não é persistida por causa do gate de higiene de referências do repositório.

## Contrato implementado

O novo formato é `neoeng-d-trace-scenario`, versão `1`, com extensão recomendada
`.ndtscenario.json`. Ele é separado do `.ndtproj` e contém somente:

- metadados estáveis do cenário;
- referência explícita ao projeto v1 (`neoeng-d-trace-project`, versão `1`);
- SHA-256 dos bytes exatos do `.ndtproj`;
- posição e zoom da câmera de autoria;
- camadas de cenário com IDs de objetos, visibilidade e parâmetros de parallax.

`depth`, `translation_strength` e `zoom_strength` seguem o intervalo inclusivo
`[0, 1]`. O zoom deve ser finito e positivo. A referência lateral não altera o
schema do projeto v1, `SceneObject.position.z`, `z_depth`, canvas, gizmo ou
exportadores existentes.

## Garantias de leitura e escrita

- modelos Pydantic estritos, imutáveis e com campos desconhecidos rejeitados;
- IDs de camadas e referências de objetos únicos e limitados pelos tetos
  operacionais existentes do projeto;
- rejeição de BOM UTF-8, UTF-8 inválido, JSON inválido, chaves duplicadas,
  constantes não finitas, versão/formato desconhecidos e arquivos acima do
  limite;
- serialização UTF-8 determinística, ordenada e com newline final;
- SHA-256 determinístico do payload canônico do cenário;
- hash do projeto limitado ao teto de leitura e rejeição de extensão diferente
  de `.ndtproj`;
- escrita por `AtomicOutputTransaction`, com preservação do sidecar anterior
  quando o replace falha e limpeza dos temporários;
- verificação opcional do hash do projeto no carregamento.

## Ambiente e comandos reais

- Sistema: Windows 10.0.26200.
- Python: 3.11.9.
- Poetry: 2.4.1.

Comandos executados sem modificar regras, skips, xfails ou asserções:

```text
poetry check --lock --strict
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest -q tests/test_scenario_schema_io.py --cov=src.persistence.scenario_schema --cov=src.persistence.scenario_io --cov-branch --cov-report=term-missing
poetry run pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools/check_coverage_policy.py coverage.xml
poetry run python tools/baseline_integrity.py --verify
```

## Resultados observados

- Testes focais do schema/I/O: **29 passed, 0 failed, 0 skipped**.
- Cobertura focada: `scenario_schema.py` **100%** de linhas e branches;
  `scenario_io.py` **100%** de linhas e branches.
- Suíte completa: **1270 passed, 2 skipped, 10 warnings**.
- Cobertura global: `14011/15103` linhas (`92,77%`) e `4162/4880`
  branches (`85,29%`); cobertura combinada reportada pelo projeto: **90,94%**.
- Política de cobertura: aprovada.
- Lockfile, compileall, flake8, Black, isort e mypy (99 arquivos): aprovados.
- `pip-audit`: nenhum advisory conhecido; o pacote local foi reportado como
  não auditável por não estar publicado no PyPI.
- Bandit: nenhum achado no nível configurado.
- Baseline: verificação executada após a atualização final dos arquivos.

Os dois skips são os testes condicionais históricos de symlink já existentes no
repositório; não foram introduzidos nem usados para obter aprovação.

## Evidência de não mutação e rollback

Os testes criam `.ndtproj` temporário real, calculam o SHA-256 dos bytes, salvam
o sidecar, carregam com verificação do projeto, alteram o projeto e confirmam a
rejeição por hash divergente. Também confirmam que o projeto e o sidecar não são
alterados pelo carregamento ou pela falha controlada de replace. Em falhas de
stage/replace, não permanecem temporários `.neoeng-*`.

Não há captura visual nem teste real de Godot/Unity nesta unidade: preview,
overlays, painel, persistência completa, exportação e consumidores de engine
estão fora do escopo 4B.1 e permanecem etapas posteriores do plano.

## Arquivos e hashes

O manifesto `docs/evidence/artifacts/stage4b1-scenario-schema-2026-08-18/manifest.json`
registra os bytes efetivamente revisados. Os hashes são dos arquivos presentes no
commit técnico; o manifesto e este relatório serão incluídos no commit
 documental posterior.

## Decisão

**APROVADO NO ESCOPO DA ETAPA 4B.1.** O contrato lateral versionado, seus
limites, hash, round-trip, validações negativas e rollback estão implementados e
comprovados. A Etapa 4B geral continua aberta: não iniciar preview/UI/exportação
antes das etapas seguintes e seus próprios gates.