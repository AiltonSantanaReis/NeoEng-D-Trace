# Evidência — Etapa 3: plugin Godot source-only

## Identificação

- Commit funcional: `1f9c1ac`
- Commit de validação ZIP: `e6082e5`
- Branch: desenvolvimento local (nome omitido por higiene do repositório)
- Data: 2026-08-16
- Decisão: **APROVADO no escopo da etapa 3**

## Objetivo e escopo

Foi criado o addon `neoeng_d_trace` em `integrations/godot/addons`, distribuível
por cópia de pasta, ZIP determinístico ou checkout do repositório. O addon é
source-only: contém somente GDScript, configuração e documentação; não contém
DLL, executável, biblioteca nativa, download automático ou dependência externa.

A etapa implementa identidade, versão, contrato de manifesto, comando de
 diagnóstico somente leitura e varredura de `res://NeoEngGenerated`. Não
implementa Sprite2D, pivô, CollisionPolygon2D, sincronização, overrides,
tiles, animação ou rollback de recursos; esses itens pertencem às etapas 4 e
seguintes e continuam pendentes.

## Ambiente real

- Godot: `4.7.stable.official.5b4e0cb0f`
- Execução: editor headless para carregar o plugin e execução headless do
  validador dedicado
- Fixture: projeto Godot real com `plugin.cfg` habilitado, manifesto real do
  contrato, PNG real, addon copiado por pasta ou extraído do ZIP

## Implementação verificada

- `plugin.cfg`: identidade `NeoEng D-Trace`, versão `0.2.0`, script de plugin.
- `plugin.gd`: ciclo `_enter_tree`/`_exit_tree`, item de menu de diagnóstico,
  identidade pública e declaração explícita `source_only`/sem binários.
- `manifest_diagnostic.gd`: validação somente leitura de formato, versão,
  engine, identidade do gerador, hashes com tamanho válido, referências
  relativas seguras, política unidirecional e payload de metadados.
- `scripts/package_godot_plugin.py`: ZIP determinístico com timestamps fixos e
  somente extensões `.gd`, `.cfg` e `.md`.
- `scripts/audit_godot_plugin_stage3.py`: fixture real, sanitização de saída,
  instalação por pasta e extração de ZIP com proteção contra path traversal.

## Comandos executados

```text
poetry run pytest -q tests/test_godot_plugin_scaffold.py tests/test_integration_manifest.py
poetry run black --check --diff scripts/package_godot_plugin.py scripts/audit_godot_plugin_stage3.py tests/test_godot_plugin_scaffold.py
poetry run isort --check-only --diff scripts/package_godot_plugin.py scripts/audit_godot_plugin_stage3.py tests/test_godot_plugin_scaffold.py
poetry run flake8 scripts/package_godot_plugin.py scripts/audit_godot_plugin_stage3.py tests/test_godot_plugin_scaffold.py
poetry run pytest -q --disable-warnings --cov=src --cov-branch --cov-report=xml:coverage.xml
poetry run python tools/check_coverage_policy.py coverage.xml
poetry run python scripts/package_godot_plugin.py --output <artifact-dir>/neoeng-d-trace-godot-stage3.zip
poetry run python scripts/audit_godot_plugin_stage3.py --executable <godot-executable-resolved-locally> --work-dir <folder-fixture> --report <artifact-dir>/stage3-report.json
poetry run python scripts/audit_godot_plugin_stage3.py --executable <godot-executable-resolved-locally> --package <artifact-dir>/neoeng-d-trace-godot-stage3.zip --work-dir <zip-fixture> --report <artifact-dir>/stage3-zip-report.json
```

Os marcadores `<...>` representam caminhos locais omitidos para não expor
endereços da máquina; os comandos foram executados com os valores reais.

## Resultados

- Testes focados: `27 passed`.
- Suíte completa: `1107 passed`, `10 warnings`, `0 failed`.
- Cobertura global e política: aprovadas; linhas ≥90%, branches ≥85% e
  módulos mensuráveis dentro do contrato.
- Validação por pasta: código `0`, `NATIVE_PLUGIN_STAGE3=SUCCESS`,
  `PLUGIN_ID=neoeng_d_trace`, `PLUGIN_VERSION=0.2.0`,
  `DIAGNOSTIC_MANIFESTS=1`.
- Validação por ZIP: código `0`, os mesmos marcadores e extração segura do
  pacote para um projeto Godot real.
- Importação do projeto com o plugin habilitado: código `0` no Godot 4.7.
- O pacote ZIP foi produzido deterministicamente; o teste Python confirmou bytes
  idênticos em duas gerações e ausência de extensões binárias.
- O modo Git foi mantido compatível pelo layout source-only do repositório; clone
  remoto não foi executado nesta etapa.

## Artefatos e hashes

Índice completo: `docs/evidence/artifacts/godot-plugin-stage3-2026-08-16/stage3-index.json`.

- ZIP: `195461b99279b8d3516247a2635a9dc0c89263d394f71873beb846a483b00dc9`
- Relatório por pasta: `50fa529409edc51d05e3e4e191fb339bdd55b205286b35461a4d16924d6d1d5e`
- Relatório por ZIP: `6486994a3dcecabf5a3c575d5356e37fd408f44c752fe0edb0af5182aafca2db`
- `manifest_diagnostic.gd`: `afe17bae4547d35387b4171aa749ba509294ba10730df8f07937540e18fa0a26`
- `plugin.gd`: `040afd81a789eb5d741af8f52b039fff10023ea34ea63b0bb90e44223c5fb059`

Nenhum relatório persistido contém o caminho absoluto do computador; os
argumentos locais foram sanitizados para `<local-path>`.

## Falhas encontradas e correções

- O teste estrutural inicial tratou as aspas do `plugin.cfg` como parte do
  valor; a expectativa foi corrigida para respeitar a sintaxe do Godot.
- O primeiro relatório do harness expôs o caminho do fixture nos argumentos;
  a serialização foi corrigida e o relatório foi regenerado sem o endereço.
- O harness inicialmente validava apenas a instalação por pasta; foi ampliado
  com extração segura do ZIP e o cenário foi executado novamente no Godot real.
- Um índice intermediário apontou para um relatório inexistente; ele foi
  descartado e substituído por um índice final contendo somente arquivos
  existentes e hashes válidos.

## Limitações e riscos residuais

- A etapa 4 ainda não foi iniciada: nenhum Sprite2D, pivô ou
  CollisionPolygon2D é gerado pelo addon.
- O diagnóstico valida estrutura e política do manifesto; ainda não recalcula
  o SHA-256 canônico da imagem/metadados dentro do GDScript.
- O modo Git foi verificado por compatibilidade estrutural, não por clone remoto.
- O risco R-017 permanece aberto para importação nativa, Unity, sincronização,
  overrides, dry-run e rollback.

## Decisão

**APROVADO — etapa 3 concluída no escopo comprovado.** O addon Godot
source-only é instalável por pasta e ZIP e foi executado dentro do Godot real.
As etapas 4 a 10 não foram promovidas.