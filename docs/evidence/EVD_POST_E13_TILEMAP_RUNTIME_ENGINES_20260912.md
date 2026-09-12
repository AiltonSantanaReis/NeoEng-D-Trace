# Evidência pós-E13 — materialização real de Tilemap em Godot e Unity

**ID:** `EVD-P13-TILEMAP-RUNTIME-ENGINES-20260912`

**Estado:** `PASS` — checkpoint técnico do runtime de Tilemap/Tileset

**Data:** 2026-09-12

**Base auditada:** `Ailton/e08-renderer-20260908` em `c39a8670cee23e4bdd423429e2eb65d6b1d7c534`

**Mudança:** [`CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md`](CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de continuidade:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Regra de interpretação

Este documento fecha somente o gate de payload e materialização externa do
Tilemap/Tileset. O lote pós-E13 continua `IN_PROGRESS` e a revisão humana final
continua `HUMAN_REVIEW_DEFERRED`; E13, seus artefatos e suas limitações não
foram reabertos nem removidos.

## Contrato implementado

O commit `c39a867` acrescenta um payload versionado
`neoeng-d-trace-tilemap-runtime` com:

- referência segura e hash/bytes do tilemap de origem;
- referência segura e hash/bytes do atlas efetivamente usado;
- grade, bounds, chunk size, camadas, células, variantes e regras;
- contagens verificáveis de tiles, camadas, células e Rule Tiles;
- recusa de caminhos absolutos, traversal, IDs duplicados, células inválidas,
  atlas ausente e drift de bytes.

O adaptador Godot cria `Node2D` por camada e `Sprite2D` regional por célula,
com textura real derivada do atlas. O adaptador Unity cria `GameObject` por
camada e `SpriteRenderer` por célula, com `Sprite.Create` sobre a textura real.
Ambos validam o binding antes de materializar a cena.

## Testes automatizados

- Suíte focada do lote: **69 passed** em 2.83s, incluindo 7 testes novos de
  exportação/validação do runtime, persistência do pacote, caminhos inseguros,
  atlas ausente, drift, duplicidade e recusa de sobrescrita.
- Suíte oficial sem filtros: **2223 passed, 2 skipped, 1 warning** em 69.87s.
  Log final:
  [`official-pytest-runtime-final.log`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/official-pytest-runtime-final.log)
  — SHA-256 `9B1086CFEA63F71D330F32C1AC050CA8EAFC76AC4D5B5512581E5F27B3553E50`.
- O warning permaneceu explícito: `DeprecationWarning` em
  `tests/test_merge_coverage_authoring_contracts.py:1341`, na construção
  depreciada de `QMouseEvent`.
- As execuções oficiais intermediárias foram preservadas: a primeira registrou
  a atualização necessária do scaffold Godot e a segunda registrou uma falha
  transitória de `WinError 5` no `os.replace` do teste GLTF. O teste isolado
  passou e a repetição oficial final passou; nenhum log foi sobrescrito.

## Auditoria real em engines externas

Comando executado:

```text
.venv311\Scripts\python.exe scripts\audit_post_e13_tilemap_runtime_engines.py --engine both --output artifacts\post-e13-tilemap-runtime-engines-final-20260912
```

Relatório consolidado:
[`tilemap-runtime-engine-audit.json`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/tilemap-runtime-engine-audit.json)
— SHA-256 `4AB507E226DD80E4B5C52E71BD9753E95D6B270B273D9215A23ABE1957CCBB45`.

| Engine | Caso positivo | Caso negativo | Evidência observável |
|---|---|---|---|
| Godot 4.7 (`C:\ProgramData\chocolatey\bin\godot.exe`) | `SUCCESS`, 2 camadas, 4 tiles, 27 células, 27 `Sprite2D`, 1 regra | `REJECTED`, `atlas file hash or size mismatch` | [`godot-tilemap-runtime-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/godot-tilemap-runtime-report.json), [`godot-tilemap-runtime-negative-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/godot-tilemap-runtime-negative-report.json) |
| Unity 6000.5.7f1 (`C:\Program Files\Unity\Hub\Editor\6000.5.7f1\Editor\Unity.exe`) | `SUCCESS`, 2 camadas, 4 tiles, 27 células, 27 `SpriteRenderer`, 1 regra | `REJECTED`, `atlas file size mismatch` | [`unity-tilemap-runtime-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/unity-tilemap-runtime-report.json), [`unity-tilemap-runtime-negative-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/unity-tilemap-runtime-negative-report.json) |

Capturas geradas pelo fluxo real do runtime:

- Godot: [`godot-tilemap-runtime-capture.png`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/godot-tilemap-runtime-capture.png)
  — SHA-256 `EDBA9B0D42E36FB8256C7D8BD6BF73FE0DDA90A1B2425D1BA7198A7637FCD15E`.
- Unity: [`unity-tilemap-runtime-capture.png`](../../artifacts/post-e13-tilemap-runtime-engines-final-20260912/unity-tilemap-runtime-capture.png)
  — SHA-256 `5DC92E3BC5EC1DBC469EB0EE508EABF8D22B5D69551AC3C4E4301084E9E68648`.

Os logs nativos Unity também foram preservados: positivo SHA-256
`E50E2564C00B7237AF3233FAB888B2942501F292C5A77D6BFC54E028B475F1D6` e
negativo SHA-256
`1C342F903ADAC9917BE8854203D6D3CE8C2A0B587975809DD5D6A27A428592E2`.

## Build limpa e proveniência

A build foi produzida em worktree limpo a partir de `c39a867`:

- worktree: `Ailton/p13-tilemap-runtime-build-20260912`;
- executável:
  [`NeoEng-D-Trace.exe`](../../../p13-tilemap-runtime-build-20260912/release/post-e13-tilemap-runtime-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe)
  — SHA-256 `A67347E65CA939DDC374FBC971FF7D63D8DB803AC4AD4E1A2A5213DC7CE7D409`,
  8.157.363 bytes;
- pacote portátil:
  [`NeoEng-D-Trace-0.3.0-win64-portable.zip`](../../../p13-tilemap-runtime-build-20260912/release/post-e13-tilemap-runtime-20260912/NeoEng-D-Trace-0.3.0-win64-portable.zip)
  — SHA-256 `CD8BEBD862469DCDE38A6664E7CE89F9FA21641A52955A27FA085C502313C0FC`;
- proveniência:
  [`continuity-provenance.json`](../../../p13-tilemap-runtime-build-20260912/release/post-e13-tilemap-runtime-20260912/continuity-provenance.json)
  — SHA-256 `318EF6B4A763E79A849C80C40DE6815D68380BF61AB701CD2D4AD19040D6911B`;
- smoke portátil:
  [`portable-smoke-report.json`](../../../p13-tilemap-runtime-build-20260912/release/post-e13-tilemap-runtime-20260912/smoke/portable-smoke-report.json)
  — `SUCCESS`, 11 checks, SHA-256
  `DA6771D27279892D8FCA076F6E8C61A77F8430153F8E8FFF18ECC9677A68F537`;
- log de build:
  [`post-e13-tilemap-runtime-20260912-build.log`](../../../p13-tilemap-runtime-build-20260912/release/post-e13-tilemap-runtime-20260912-build.log)
  — SHA-256 `D718C32904AC6D9763D347831379E1DF82599F07D83AE8994A35C37613695709`.

O warning de empacotamento `Hidden import "tzdata" not found!` permaneceu
visível no log; não foi ocultado nem convertido em falha do produto.

## Integração no exportador geral

O commit `a7e22b3e625cd4190258f6ed44d2ef9a68aff7c1` integrou a emissão
automática do payload ao `build_composition_package`. Com
`auto_tilemap_runtime=True` e `atlas_path` válido, o pacote geral passa a
incluir e validar o payload, a fonte e o atlas em `tilemap-runtime/`, com
bindings hashados no `composition.json`. O teste focado passou com **8 passed**
e cobre também o caminho legado sem atlas, que continua exportável com o estado
explícito `not-emitted-legacy-atlas-missing`.

## Fluxos nativos reais no binário final requalificado

O executável v4 foi aberto em janela nativa maximizada `3866x2090` e operado
com cliques Win32 reais. O título observado foi
`Editor de Cenário — NeoEng-D-Trace`. A requalificação foi necessária porque a
inspeção visual encontrou coordenadas obsoletas no harness anterior.

### Tilemap: entrada, mapa novo, canvas, pintura, salvar e reabrir

O fluxo autoritativo é o v3, executado no binário final v4:

- executável:
  [`NeoEng-D-Trace.exe`](../../build/post-e13-final-build-recovery-v4-20260912/release/post-e13-final-recovery-v4-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe)
  — SHA-256 `CBC16B6425158362572848D59D847988F8300455E1AE973DB961A0C2162046A8`;
- harness usado:
  [`capture_e03_asset_library_binary.ps1`](../../scripts/capture_e03_asset_library_binary.ps1)
  — SHA-256 `BDD56A5A8413CCB0F45CB6ACA2D63053BC8A4F21CBC06C58851C0CA81B9D4390`;
- manifesto v3:
  [`manifest.json`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/manifest.json)
  — SHA-256 `9D9A060173727C67ADCFC2DE3D8BA19EA671DBE1D9EA35A245BAD8DBAB1CB5F7`;
- mapa novo, com paleta e canvas visíveis:
  [`08-tilemap-new.png`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/08-tilemap-new.png)
  — SHA-256 `231189A01A5A750213BFDC5B1EAF852632865ADD1338F24FBCA59359EFF7E130`;
- canvas antes da edição:
  [`08-tilemap-canvas-visible.png`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/08-tilemap-canvas-visible.png)
  — SHA-256 `68E6614908BD1EE688ABA4AAC1ED0BD55811F1A8807AA8741F05DAD515A6B9F4`;
- pintura de três células adjacentes:
  [`09-tilemap-painted.png`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/09-tilemap-painted.png)
  — SHA-256 `939ED67DE479B548525BBA6B4C388AA9CC3C8C702D7693EEC519CEBA9F7BDED5`;
- salvar, com mensagem nativa `Tilemap salvo: scenario.tilemap.json`:
  [`10-tilemap-saved.png`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/10-tilemap-saved.png)
  — SHA-256 `5D1358D5E6068B66CCA1854F4DED2E6EBA487EDF892E0F7609226D600386891A`;
- reabrir, com mensagem nativa `Tilemap reaberto` e as três células
  preservadas:
  [`11-tilemap-reopened.png`](../../artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/11-tilemap-reopened.png)
  — SHA-256 `443CA4BD0B4D26C7D814A4797A18878619D2007C1CAA1C493FA696EFE25D836E`;
- sidecar persistido:
  `build/post-e13-final-build-recovery-v4-20260912/artifacts/post-e13-final-native-composition-recovery-v4-20260912/fixture/assets/tilemaps/scenario.tilemap.json`
  — SHA-256 `282F5D8B094B1A2BA98BDE991FEECB642239D9F8C05F061F01A2D5185E339FC0`,
  formato `neoeng-d-trace-tilemap`, versão 1, 1 camada e 3 células.

O harness agora falha se o sidecar esperado não existir ou se contiver zero
células; portanto a persistência não é inferida apenas pela captura visual.

### Finding histórico preservado

Os artefatos `artifacts/post-e13-tilemap-runtime-native-final-20260912/`
continuam preservados, mas foram retirados do gate autoritativo: a inspeção
humana mostrou `Sem mapa`, painel/paleta vazios e ausência de edição efetiva
nas capturas `08`–`11`. A causa foi coordenada obsoleta no harness, não uma
alteração destrutiva no produto. O finding e seus hashes não foram apagados;
somente a requalificação v3 é usada para o `PASS` técnico.

### Tileset: atlas real, gerar, salvar, novo e reabrir

O fluxo autoritativo foi requalificado no mesmo binário v4, com validação
explícita do sidecar persistido:

- manifesto v2:
  [`manifest.json`](../../artifacts/post-e13-tilemap-runtime-tileset-native-requalified-v2-20260912/manifest.json)
  — SHA-256 `32DD9EDD62A89D8C9DFE6BF5FF8AA2E0788E3779EAC1175A0CCD5CBDCC206CD8`;
- atlas gerado, mostrando `300 tiles · neoeng-d-trace-tileset v1`:
  [`07-tileset-generated.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-requalified-v2-20260912/07-tileset-generated.png)
  — SHA-256 `362DF9B35893E8F3E9FD08C19B387F90F4C9784B98422EDD26DADC9AC9EE2095`;
- salvar, com mensagem nativa `Tileset salvo: tileset.json`:
  [`08-tileset-saved.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-requalified-v2-20260912/08-tileset-saved.png)
  — SHA-256 `4AB89D4A8679D6305C5622DE22FC83C5A23F151D8B0A591FB951584CC24FE1B7`;
- reabrir, com mensagem nativa `Tileset reaberto` e os 300 tiles preservados:
  [`10-tileset-reopened.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-requalified-v2-20260912/10-tileset-reopened.png)
  — SHA-256 `59BA1576F7CC3D4D6CB20B0DD1001CFD3DD1AD9550DB47FDB1E8851462D1470C`;
- sidecar persistido:
  `artifacts/post-e13-tilemap-runtime-tileset-native-requalified-v2-20260912/tileset-fixture/assets/tilesets/scenario/tileset.json`
  — SHA-256 `E052E41671B87914D0B7C4A31783AFE59D5AE91B1B6F8CC2E5C572FEA45D5E06`,
  formato `neoeng-d-trace-tileset`, versão 1, 300 tiles, atlas
  `source_atlas.png` com SHA-256
  `4bffd31518cb8eabcfba2b2a4379ba54d6a1632ebd8836b1cbae36f9b33a9a18`.

O harness falha se o sidecar não existir ou não contiver tiles; a persistência
do Tileset é, portanto, uma condição observada e validada, não uma inferência
da imagem.

## Método e limitações

- A prova de editor usou o binário recém-gerado, `PrintWindow` e eventos
  Win32 reais. O CUA já havia sido tentado e falhou com
  `failed to write kernel assets: ... os error 3`; essa limitação permanece
  explícita e não foi apresentada como sucesso do CUA.
- Os comandos de runtime externos são headless reais. Godot usa o renderer
  dummy nesse modo; por isso a captura Godot é composta dentro do próprio
  processo a partir do atlas decodificado e das células autorais, enquanto a
  contagem de `Sprite2D` é a saída do adaptador. Unity foi executado com
  `-batchmode -nographics`; sua captura usa o atlas decodificado após a
  materialização dos `SpriteRenderer`. Os relatórios e os casos negativos são
  a prova principal do runtime.
- O payload/adapter e a integração automática no exportador geral estão
  comprovados em contrato; o fluxo nativo dessa exportação no binário da build
  final será registrado no gate pós-E13 correspondente. O runtime externo do
  editor híbrido 3D permanece uma linha separada.
- A revisão humana final continua deferida até iluminação direcional, efeitos
  orientáveis, partículas completas, Tilemap/Tileset e editor híbrido 3D
  estarem fechados conforme a decisão vigente.

## Gate

O gate específico de Tilemap/Tileset — contrato, testes, build, execução
externa positiva, falha de drift e fluxo nativo do binário — está `PASS`.
O lote pós-E13 permanece `IN_PROGRESS`; não há autorização de release,
publicação, merge ou encerramento do produto neste checkpoint.
