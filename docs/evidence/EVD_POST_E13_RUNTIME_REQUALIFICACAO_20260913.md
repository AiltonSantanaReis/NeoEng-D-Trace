# Requalificação pós-E13 — runtime externo e integridade dos gates

**ID:** `EVD-POST-E13-RUNTIME-REQUALIFICACAO-20260913`

**Estado do registro:** `IN_PROGRESS`

**Data:** 2026-09-13

**Branch:** `Ailton/audit-post-e13-scenario-editor-20260912`

**Commit auditado do harness:** `d7ddbefba24706f071c6d89cf539558adfe214c4`

**Estado do lote pós-E13:** `IN_PROGRESS`

**Revisão humana final:** `PENDING_EVIDENCE`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Índice prevalente:** [`INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`](../INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md)

**Decisões aplicáveis:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md) e [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

**Registros de mudança:** [`CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md`](CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md) e [`CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md`](CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md)

## Objetivo e limite do registro

Este adendo registra a requalificação atual dos gates externos de Tilemap e do
vertical slice híbrido 2D/2.5D/3D em Godot e Unity. Ele não substitui nem
reescreve as evidências históricas de 20260912; os diretórios anteriores e a
primeira saída com status interno incorreto permanecem preservados.

Os requisitos e IDs rastreados são `REQ-F02-EVIDENCE-AUTOMATION`,
`REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`,
`REQ-F09-RUNTIME-EQUIVALENCE` e `REQ-F10-UI-ACCESSIBILITY`, nos workstreams
`CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912` e
`CHG-P13-HYBRID-3D-AUTHORING-20260911`. O resultado é um gate técnico de
runtime, não uma declaração de editor 3D completo nem o encerramento da
revisão humana pós-E13.

## Integridade do código e da execução

O commit `d7ddbef` contém somente:

- a correção do auditor `scripts/audit_post_e13_tilemap_runtime_engines.py`,
  que publica o status avaliado de cada engine;
- o teste `tests/test_post_e13_tilemap_runtime_engines.py`, com as quatro
  transições de status (`NOT_RUN`, `PASS`, `PENDING_EVIDENCE` e `FAIL`).

Nenhum arquivo do editor canônico, modelo de dados, exportador, adapter de
runtime ou layout foi alterado por essa correção. O build do produto usado no
checkpoint anterior continua identificado em
[`AUDITORIA_POST_E13_PERFORMANCE_BASELINE_20260913.md`](AUDITORIA_POST_E13_PERFORMANCE_BASELINE_20260913.md):
executável SHA-256
`245A66B8E2C29A2180B9514F8579DB3679899A6C1EE4F06F13B863ACF9055238` e pacote
portátil SHA-256
`F46A7481D94194A0BA143FEB9A6A960059D772270094C752FA8440DA3EBF86A0`. Como a
mudança `d7ddbef` é exclusiva do harness, não houve alteração silenciosa do
binário do produto.

### Regressão

| Camada | Comando/resultado | Estado formal |
|---|---|---|
| Focada do harness e Tilemap | `tests/test_post_e13_tilemap_runtime_engines.py tests/test_post_e13_tilemap_tileset_authoring.py tests/test_e04_tilemap_contract.py tests/test_e04_tilemap_ui.py` — `39 passed` | `PASS` |
| Suíte oficial sem filtros | `.venv\\Scripts\\python.exe -m pytest -q` — `2625 passed, 2 skipped, 5 warnings` em `266.23s` | `PASS` |
| Skips oficiais | Dois skips preexistentes da suíte; nenhum foi criado, ampliado ou usado para obter o resultado desta etapa | `PENDING_EVIDENCE` |
| Warnings | Cinco deprecações de `QMouseEvent`; preservadas no resultado | `PENDING_EVIDENCE` |

O primeiro acionamento pelo `pytest` global falhou por ausência do módulo
`pytest`; o Python 3.11 fora do virtualenv também falhou na coleta por ausência
de `pydantic`. Essas falhas de ambiente foram preservadas no registro de
execução. A suíte oficial só foi considerada depois de localizar o virtualenv
do projeto, sem `--ignore`, `-k`, `skip`, `xfail`, `--no-verify` ou filtro
equivalente.

## Requalificação real do Tilemap em Godot e Unity

### Entrada, engines e execução

O auditor executado após o commit foi:

```text
.venv\\Scripts\\python.exe scripts\\audit_post_e13_tilemap_runtime_engines.py --output artifacts\\post-e13-tilemap-runtime-engines-postperf-20260913-r3 --engine both
```

O pacote foi criado com atlas, payload versionado, duas camadas e regra de
Tilemap. O Godot real foi `4.7.stable.official.5b4e0cb0f`, em
`C:\\ProgramData\\chocolatey\\bin\\godot.exe`. O Unity real foi
`6000.5.7f1`, em `C:\\Program Files\\Unity\\Hub\\Editor\\6000.5.7f1\\Editor\\Unity.exe`.
Os adapters de produto continuam vinculados aos commits
`c39a8670cee23e4bdd423429e2eb65d6b1d7c534` (Godot/Unity Tilemap), e os hashes
atuais são `0B663B94CED7C119FCBD7493D286D135845EADFD18AFD8F6683F51983EC8EBCE`
(Godot) e `899F082C14FA0871FFD6163EF2AF753864DAA757330ABA0FD4475C636B1B421C`
(Unity).

| Gate | Resultado observado | Estado formal |
|---|---|---|
| Godot positivo | `SUCCESS`; 2 camadas, 4 tiles, 27 células, 27 sprites renderizados e 1 regra; retorno 0 | `PASS` |
| Unity positivo | `SUCCESS`; 2 camadas, 4 tiles, 27 células, 27 sprites renderizados e 1 regra; retorno 0 | `PASS` |
| Godot negativo | `REJECTED` por `atlas file hash or size mismatch`; retorno 0 | `PASS` |
| Unity negativo | `REJECTED` por `atlas file size mismatch`; retorno 0 | `PASS` |
| Gate agregado | `tilemap-runtime-engine-audit.json.status=SUCCESS`, com `godot.status=PASS` e `unity.status=PASS` | `PASS` |

O caso positivo foi executado pelo engine e produziu capturas nativas. A
inspeção visual confirmou o padrão de tiles coloridos nos dois arquivos; a
captura não foi criada por mock, chamada interna da UI ou imagem sintética.

### Artefatos hashados do r3

| Artefato | SHA-256 |
|---|---|
| [`tilemap-runtime-engine-audit.json`](../../artifacts/post-e13-tilemap-runtime-engines-postperf-20260913-r3/tilemap-runtime-engine-audit.json) | `B712EC8833F97295A924B25AAB32251DEE58825694EC6B7864305684EFD1EA43` |
| [`godot-tilemap-runtime-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-postperf-20260913-r3/godot-tilemap-runtime-report.json) | `8B704ED32D259F16E72B6E356EA41733B57F5C0A9EA848DC85BA74CF8990109C` |
| [`unity-tilemap-runtime-report.json`](../../artifacts/post-e13-tilemap-runtime-engines-postperf-20260913-r3/unity-tilemap-runtime-report.json) | `0AC1F823B58A99C8CFB764460F95E6826C85F11E18D5228419F05D4D2BF42313` |
| `runtime-package/assets/tiles/terrain.png` | `32B2134AA61A3676AB7B08D6F7EBAE6F5FABFE66B0E2D15F4E4CF0F8B58CB091` |
| [`godot-tilemap-runtime-capture.png`](../../artifacts/post-e13-tilemap-runtime-engines-postperf-20260913-r3/godot-tilemap-runtime-capture.png) | `EDBA9B0D42E36FB8256C7D8BD6BF73FE0DDA90A1B2425D1BA7198A7637FCD15E` |
| [`unity-tilemap-runtime-capture.png`](../../artifacts/post-e13-tilemap-runtime-engines-postperf-20260913-r3/unity-tilemap-runtime-capture.png) | `5DC92E3BC5EC1DBC469EB0EE508EABF8D22B5D69551AC3C4E4301084E9E68648` |
| `unity-positive.log` | `89FD709B6F5A380A4FA7939360A6BD9CDA652376C762A690B689E90599D2C1D0` |
| `unity-negative.log` | `6C063B35ED5675ED6712998DF11E122D0C8203A802A96AE90F2BEAC6FF887767` |

## Requalificação real do vertical slice híbrido

O fixture foi construído de forma aditiva a partir da composição preservada
no arquivo de legado, sem modificar a fonte histórica. O manifesto do fixture
[`fixture-manifest.json`](../../artifacts/post-e13-hybrid-runtime-fixture-postperf-20260913/fixture-manifest.json)
tem SHA-256
`18A190979E65539C788459A0E8BE2760AE4AAF5A4DDEB9B3B143228606C808C6`.

| Gate | Resultado observado | Estado formal |
|---|---|---|
| Godot positivo | `SUCCESS`; `MeshInstance3D`, `Camera3D`, luz direcional/pontual e `AnimationPlayer`; 1 mesh, 1 material, 1 luz, 1 clip, 2 frames, playback em `Y=0.125`, 3.600 pixels não pretos | `PASS` |
| Unity positivo | `SUCCESS`; `MeshFilter`, `MeshRenderer`, `Camera`, `Light` e `Animation`; 1 mesh, 1 material, 1 luz, 1 clip, 2 frames e playback em `Y=0.125` | `PASS` |
| Godot negativo | `REJECTED` antes da materialização por hash/tamanho de `scene.normalized` | `PASS` |
| Unity negativo | `REJECTED` antes da materialização por hash/tamanho de `scene.normalized` | `PASS` |
| Gate agregado | [`hybrid-runtime-engine-audit.json`](../../artifacts/post-e13-hybrid-runtime-engines-postperf-20260913/hybrid-runtime-engine-audit.json), SHA-256 `4BD4572C4477B9309C310307DDDD2355E7B4512CBC54C5BE83DC991F8F19C382` | `PASS` |

As capturas são do processo nativo dos engines: [Godot](../../artifacts/post-e13-hybrid-runtime-engines-postperf-20260913/godot-hybrid-runtime-capture.png), SHA-256 `0CB98627C0F4EA192FD0A6FDD65728A5FC8D9752D774D371981628C60701DCA8`, e [Unity](../../artifacts/post-e13-hybrid-runtime-engines-postperf-20260913/unity-hybrid-runtime-capture.png), SHA-256 `BE4F668ECFCC516EC834569B34EAD1ED4E89D7591E055F03F42B65C36D1AC0D0`. O gate usa a imagem produzida pelo runtime, não uma captura do editor nem um mock.

## Finding corrigido no auditor

Na primeira execução Tilemap pós-performance, o campo global estava correto,
mas os campos internos `godot.status` e `unity.status` permaneceram em
`NOT_RUN` porque eram inicializados como placeholders e não eram atualizados
após o cálculo dos gates. Isso era uma falha de observabilidade do harness,
não uma falha funcional do runtime. O artefato r1 foi preservado.

O commit `d7ddbef` adicionou `_engine_status`, que conserva `NOT_RUN` somente
quando o engine não foi selecionado, publica `PASS` quando o gate avaliado
passa e preserva `PENDING_EVIDENCE`/`FAIL` quando aplicável. O teste focado
verifica todas as quatro transições. A execução r3, depois do commit, confirma
os status internos corretos e elimina a ambiguidade sem alterar o produto.

## Diagnósticos do Unity e classificação sem ocultação

Nos logs positivos e negativos do Tilemap, o Unity registra mensagens de
licensing/telemetria e encerramento, incluindo falha de validação do cliente,
`Access token is unavailable`, `Curl error 42: Callback aborted`, timeout para
`public-cdn.cloud.unity3d.com` e `abort_threads: Failed aborting id`. Elas
ocorrem no mesmo processo que retorna 0 e, no positivo, depois da emissão de
`TILEMAP_RUNTIME_UNITY=SUCCESS` e da contagem de 27 células.

A classificação correta é:

- funcionamento do payload positivo e da rejeição negativa: `PASS`, porque o
  relatório, a contagem observável, a captura e o código de retorno passaram;
- log de engine/ambiente limpo, sem licensing/rede/shutdown diagnostics:
  `PENDING_EVIDENCE`;
- inexistência universal de abort em todas as máquinas: `PENDING_EVIDENCE`.

Não há, neste pacote, evidência de abort do produto ou de perda do resultado
funcional. Também não há evidência suficiente para declarar esses diagnósticos
inofensivos fora deste ambiente; eles permanecem publicados e exigem uma
investigação própria de runtime/licensing antes de qualquer promessa de log
limpo.

## Limitações e gates ainda abertos

O que está comprovado é um vertical slice técnico. Permanecem
`PENDING_EVIDENCE` ou `IN_PROGRESS`, conforme o caso:

- editor 3D profissional completo, com gizmo aprovado, navegação, câmeras,
  luzes, efeitos e viewport de produção;
- colisão 3D, partículas completas, tilemap 3D, timeline/cutscene híbrida,
  importação de modelos externos e equivalência completa de iluminação;
- prova de desempenho e memória em escala de produção nos engines externos;
- logs Unity limpos e qualificação independente dos diagnósticos de ambiente;
- revisão humana final do lote pós-E13.

O gizmo permanece deliberadamente adiado, conforme decisão do usuário. A
produção e promoção de novos modelos/asset packs também permanece adiada; esta
requalificação não remove, substitui ou promove assets.

## Critério de continuidade

Os gates positivos e negativos de runtime Tilemap e híbrido foram reexecutados
com engines reais, capturas reais, hashes, persistência de relatório e falha
controlada. O estado oficial continua `IN_PROGRESS`: a revisão humana, os
limites de produção e os diagnósticos do ambiente ainda não podem ser
convertidos em `PASS` por inferência.
