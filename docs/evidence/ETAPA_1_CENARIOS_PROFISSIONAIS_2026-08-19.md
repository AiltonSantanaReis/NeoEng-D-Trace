# Evidência — Etapa 1 da extensão profissional de cenários

## Identificação

- Escopo: baseline real, reconciliação documental, inventário de contratos e
  caracterização da extensão profissional.
- Commit-base: `487ae11adfa7b9052debd5eda41e47460399406e`.
- Branch de execução: `codex/scenario-authoring-professional`.
- Estado: **PENDENTE DE GATES LOCAIS**.
- Plano: `docs/PLANO_CENARIOS_PROFISSIONAL_2026-08-19.md`.

## Fatos confirmados no código

O projeto integrado contém o MVP lateral de cenário: `ScenarioDocumentV1`,
`ScenarioAuthoringState`, câmera ortográfica/parallax, painel de camadas,
preview/overlays, persistência hash-bound e exportação runtime JSON. O cenário
atual armazena camadas e referências `object_ids`; não há ainda contrato de
objetos de cenário independentes com transformações, biblioteca de assets,
seleção múltipla, sockets de iluminação/VFX/triggers ou importação completa de
assets para uma viewport de autoria.

O editor de cenário já é uma janela separada do editor principal, mas sua UI
atual é um painel de autoria de camadas. Essa separação será preservada e
ampliada, não misturada novamente ao editor 2D.

Contratos preservados nesta etapa: schema de projeto v1, `SceneObject.position.z`,
colisores, gizmo 2D, menus, atalhos, histórico do editor principal, exportadores
existentes e os consumidores Godot/Unity já validados no escopo anterior.

## Entradas e hashes

Os hashes abaixo serão obtidos dos blobs Git do commit desta etapa, não de
caminhos absolutos do computador local:

| Entrada | SHA-256 |
|---|---|
| `src/persistence/scenario_schema.py` | 4999b311be46471bc75e9bc9e58d9f0c941714cc850eb19b46b31a2323c35e44 |
| `src/core/scenario_authoring.py` | f9191c8010e059b4319478674190a41fc9a42c3d4fa66baf64207c551374c548 |
| `src/ui/scenario_editor_window.py` | de6e556f641272e8b6ef8908409b867c1ea0495a4bc33aa6fb47f60cce9b3674 |
| `src/ui/scenario_panel.py` | 3589d5f4d83d9e42ca51e7a79d75976ac4a4eb1eb23c7ab624371b7edf50650a |
| `docs/PLANO_CENARIOS_PARALLAX_E_PALETA_2026-08-18.md` | 59de520a30f0f4fad9474ed56466aabf02881512da5e1d99e7975916cb479ed7 |

Os valores foram calculados com git show HEAD:<arquivo> e SHA-256; não foram
calculados a partir de caminhos absolutos do computador.

## Comandos executados

Ambiente: Windows local, Python 3.11.9, Poetry lock do projeto, PySide6 com
Qt offscreen para os testes de interface.

```text
poetry check --lock --strict
poetry run pytest -q tests/test_scenario_schema_io.py tests/test_stage4_parallax_camera.py tests/test_stage4b3_scenario_authoring.py tests/test_stage4b4_scenario_export.py tests/test_ui_defect_regressions.py --tb=short
poetry run pytest -q --tb=short
poetry run flake8 src tests tools app.py pack_for_ai.py
poetry run black --check --diff src tests tools app.py pack_for_ai.py
poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py
poetry run python tools/baseline_integrity.py --verify --git-blob
poetry run python tools/evidence_integrity.py --require-tracked --git-blob
git diff --check
git status --short --branch
```

## Resultados

- poetry check --lock --strict: **PASS** (All set!).
- Caracterização de schema, câmera, autoria, exportação e UI: **91 passed**.
- Suíte integral: **1331 passed, 2 skipped, 0 failed**, em 25,11 s.
- Flake8: **PASS**.
- Black: **PASS**, 238 files would be left unchanged.
- Isort: **PASS**.
- Integridade de evidências existente: **PASS**, 56 manifests validated.
- Baseline: a primeira execução falhou legitimamente com dois Unexpected,
  pois os novos documentos ainda não estavam rastreados. O caso será corrigido
  antes do fechamento com commit e regeneração do baseline contra os blobs
  efetivamente versionados.
- Skips: somente os skips condicionais já existentes poderão ser reportados;
  não serão criados skips para esta etapa.
- Cobertura: será registrada pela execução real; nenhum limiar será alterado.

## Lacunas deliberadamente não declaradas como resolvidas

Esta etapa não implementa drag-and-drop, objetos independentes, transformações
de cenário, seleção múltipla, sockets, preview de iluminação/VFX, adaptadores
de importação ou runtime de engine. Esses itens permanecem pendentes para as
etapas seguintes e não podem ser apresentados como prontos.

## Rollback

Como esta etapa altera apenas documentação de plano/evidência, o rollback é a
reversão do commit desta etapa. Nenhum arquivo de projeto do usuário é escrito
ou migrado.

## Decisão

**PENDENTE DE FECHAMENTO DO BASELINE.** Os testes de caracterização e a
integridade dos manifestos passaram. A etapa só será fechada após os dois novos
documentos estarem rastreados, o baseline ser regenerado contra os blobs do
commit e a validação final confirmar árvore limpa.
