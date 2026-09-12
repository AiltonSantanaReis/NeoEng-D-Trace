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

## Fluxos nativos reais no binário novo

O executável recém-gerado foi aberto em janela nativa maximizada
`3866x2090` e operado com cliques Win32 reais. O título observado foi
`Editor de Cenário — NeoEng-D-Trace`.

Tilemap: entrada, mapa novo, pintura, salvar e reabrir:

- manifesto:
  [`manifest.json`](../../artifacts/post-e13-tilemap-runtime-native-final-20260912/manifest.json)
  — SHA-256 `32F673E54F50EF42431F3198DC64E868F26258381A4896934D7397DF06404AC5`;
- pintura: [`09-tilemap-painted.png`](../../artifacts/post-e13-tilemap-runtime-native-final-20260912/09-tilemap-painted.png)
  — SHA-256 `3157BF6F380AF0E221BB95CDDFA985E3717C2ADA92B21F948A6C9CCEF10B7554`;
- salvar: [`10-tilemap-saved.png`](../../artifacts/post-e13-tilemap-runtime-native-final-20260912/10-tilemap-saved.png)
  — SHA-256 `B4C330E8CB07CDEA9EEE8503BBB0099868271827F26E30E3F17EC175396F647E`;
- reabrir: [`11-tilemap-reopened.png`](../../artifacts/post-e13-tilemap-runtime-native-final-20260912/11-tilemap-reopened.png)
  — SHA-256 `B4C330E8CB07CDEA9EEE8503BBB0099868271827F26E30E3F17EC175396F647E`.

Tileset: atlas real, gerar, salvar, novo e reabrir:

- manifesto:
  [`manifest.json`](../../artifacts/post-e13-tilemap-runtime-tileset-native-final-20260912/manifest.json)
  — SHA-256 `BC723FBF74D300BCD10FD6CAFF7C9C25F6342734DAF64F77D411EC146C80E88B`;
- gerar: [`07-tileset-generated.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-final-20260912/07-tileset-generated.png)
  — SHA-256 `61F302029C1C1D1CF2C5A02351EEEC86EECFCA6854A5D2812B9631D85EE00BF0`;
- salvar: [`08-tileset-saved.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-final-20260912/08-tileset-saved.png)
  — SHA-256 `8B6128979FEDF3D7B739FB628610E94938AFE4C668B1DF41F719CB419DA481C2`;
- reabrir: [`10-tileset-reopened.png`](../../artifacts/post-e13-tilemap-runtime-tileset-native-final-20260912/10-tileset-reopened.png)
  — SHA-256 `4B9785DE4FC7F0E41C9092900444E4EF8C7E7AD3C2113D13FE73A2AD8CB19737`.

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
