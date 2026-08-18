# Evidência — Etapa 4: modelo matemático de câmera e parallax

## Identificação

- Escopo: modelo matemático puro de câmera ortográfica, profundidade e parallax.
- Commit técnico testado: `f3a0eddd8c2e128a80d2b3a31bc690ec64e63b25`.
- Base funcional anterior: `1b56b558e234c1a64e309a9e5cc9765b782dab0a`.
- Estado da integração: **APROVADO NO ESCOPO DO MODELO / NÃO INTEGRADO**.
- A identificação literal da branch de trabalho não é persistida por causa do
  gate de higiene de referências do repositório.

## Ambiente

- Sistema operacional: Windows-10-10.0.26200-SP0.
- Python: 3.11.9.
- Poetry: 2.4.1.
- Lockfile: `poetry.lock`, 200096 bytes, SHA-256
  `05632587b9ddf365415401c063aa544b447b0430a0426a61762e129d3691b756`.

## Objetivo e escopo

O incremento implementa a primeira unidade funcional da sub-engine sem
acoplar o editor existente. `ParallaxLayer` usa profundidade normalizada
independente de `SceneObject.position.z` e de `z_depth` dos exportadores.
`OrthographicCamera` projeta e desprojeta pontos 2D em pixels de viewport,
com atenuação independente para deslocamento e delta de zoom.

O modelo é imutável, determinístico e não importa Qt, `Scene`, persistência,
exportadores ou qualquer runtime de engine. O schema de projeto v1, o canvas,
o gizmo, os menus e os consumidores Godot/Unity não foram alterados neste
incremento.

## Contrato matemático comprovado

- `depth` pertence a `[0, 1]`; profundidade 0 recebe o efeito completo quando
  as forças estão em 1, e profundidade 1 fica estacionária nesse limite.
- `translation_factor = 1 - depth * translation_strength`.
- `zoom_factor = 1 - depth * zoom_strength`.
- `effective_zoom = 1 + (camera.zoom - 1) * zoom_factor`.
- `screen = viewport_center + (world - camera.position * translation_factor)
  * effective_zoom`.
- `unproject` é a inversa da mesma expressão e foi validada por round-trip.
- Valores booleanos, não numéricos, não finitos, viewport não positivo, zoom
  não positivo e pontos que não possuem exatamente duas coordenadas são
  rejeitados antes de qualquer resultado.

## Entradas e hashes

O manifesto `docs/evidence/artifacts/stage4-parallax-camera-2026-08-18/manifest.json`
registra os arquivos efetivamente revisados:

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/core/parallax_camera.py` | 6602 | `2928c3be068c73e0255d6232233c9d0cf27e29f6388731f554c31a043b826a47` |
| `tests/test_stage4_parallax_camera.py` | 4379 | `acf8255fc49b2208f2d79b0d63824680d72f2a3843fffa2c8616e98f7e3cf5bd` |

## Comandos executados

```text
poetry check --lock --strict
poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run mypy src
poetry run pip-audit
poetry run bandit -q -r src -lll
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
poetry run python tools/check_coverage_policy.py coverage.xml
poetry run python tools/baseline_integrity.py --verify
NEOENG_SOURCE_HEAD_SHA=<commit técnico> poetry run python tools/run_legacy_tests.py --group all --output <diretório temporário>
```

## Resultados

- Testes focais: `21 passed`, `0 failed`, `0 skipped`.
- Suíte integral Windows/Python 3.11.9: `1241 passed`, `2 skipped`, `10 warnings`.
- Cobertura do novo módulo: `78/78` linhas e `12/12` branches, `100%`.
- Cobertura global: `13795/14887` linhas (`92,66%`) e `4102/4820`
  branches (`85,10%`); cobertura combinada reportada pelo projeto: `90,82%`.
- Política integrada: aprovada; nenhum módulo mensurável abaixo do piso.
- `pip-audit`: sem vulnerabilidades conhecidas; o pacote local não publicado no
  PyPI foi explicitamente reportado como não auditável, sem ser mascarado.
- Suíte legada real no Windows: `196` testes executados, `27` falhas brutas
  históricas em `12` arquivos, `0` erros e `0` skips; reconciliação aceita
  `27/27` falhas esperadas, `0` inesperadas e `0` ausentes. Isso não é
  apresentado como `196 passed`.
- Baseline: `1412 files`, verificado antes e depois dos gates.

## Falhas de processo encontradas e tratadas

1. A primeira cadeia local tentou executar `poetry` pelo Python do `.venv`, mas
   esse módulo não está instalado dentro desse ambiente. A execução foi
   interrompida sem declarar sucesso; a mesma cadeia foi repetida através do
   Poetry 2.4.1 disponível no sistema e passou integralmente.
2. A primeira tentativa isolada de cobertura usou um alvo em formato de caminho
   e produziu `module-not-imported/no-data-collected`. Esse resultado foi
   descartado como medição inválida; a repetição com `--cov=src.core.parallax_camera`
   produziu `100%` real.

Nenhuma regra, asserção, skip ou xfail foi alterado para obter aprovação.

## Artefatos

- `docs/evidence/artifacts/stage4-parallax-camera-2026-08-18/manifest.json`:
  manifesto hashado dos arquivos do escopo.
- `coverage.xml`: resultado bruto gerado pelo gate local; não é promovido como
  evidência versionada independente e será reproduzido nos artefatos do CI.
- O pacote não contém PNG nem captura Qt: esta unidade é matemática pura e não
  declara validação visual ou integração com engine.

## Limitações e riscos residuais

- Schema lateral versionado, hashes do projeto, rollback, preview no canvas,
  overlays, painel de camadas, persistência, exportação e consumidores Godot/
  Unity ainda não foram implementados nesta unidade.
- Não há benchmark Windows desta etapa; o contrato de desempenho permanece
  pendente do preview real.
- As `27` falhas legadas permanecem históricas e reconciliadas conforme o
  manifesto vigente; não foram reclassificadas por esta mudança.

## Decisão

**APROVADO NO ESCOPO DO MODELO MATEMÁTICO / NÃO INTEGRADO.** O núcleo está
completo e reproduzível no commit técnico indicado, mas a Etapa 4 do plano de
cenários não deve ser declarada encerrada nem promovida a `main` antes das
etapas seguintes do contrato: schema lateral, preview, overlays, UI,
exportação, benchmark, evidências e CI pós-merge.
