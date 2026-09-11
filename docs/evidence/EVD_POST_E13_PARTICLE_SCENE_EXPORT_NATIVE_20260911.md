# Evidência pós-E13 — exportação profissional de partículas autoradas

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`
**Data:** 2026-09-11
**Branch:** `Ailton/e08-renderer-20260908`
**Commit auditado:** `73b7fccd61f2673b6c5479581cb1645912755e22`
**Mudança:** `docs/evidence/CHG_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md`
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Continuidade:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`
**Revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Escopo comprovado

Esta evidência fecha a ponte `SceneAuthoringDocumentV2 → exportação Godot/Unity
→ componente nativo`, sem remover o formato legado. Um sistema autorado só é
exportado para um engine quando existe exatamente um socket VFX com
`effect_id == particle_system.id`; payloads sem esse vínculo falham de forma
explícita. A origem V2 é versionada no componente nativo, e a origem runtime V1
continua aceita.

| Requisito/feature | Entrada controlada e operação real | Saída observada | Estado |
|---|---|---|---|
| `REQ-F09-RUNTIME-EQUIVALENCE` / `FEAT-PARTICLE-EMIT` / `FX-002` | fixture V2 com um socket VFX `fountain`, um emissor, burst 4, taxa 10/s e três ticks de 0,1 s | Godot e Unity materializaram um componente nativo; cada um contou 7 partículas e 1 emissor | `PASS` |
| `FEAT-PARTICLE-REPLAY` / `FX-005` | avanço determinístico no importador nativo | estado/contagem e hash de estado registrados nos logs | `PASS` |
| contrato de exportação | exportação real para `scene-authoring.godot.json` e `scene-authoring.unity.json` | `runtime_particles` em `capabilities.supported`, `particle_systems` preservado | `PASS` |
| falha controlada | remover todos os sockets VFX da mesma fixture | Python, Godot e Unity rejeitaram com “exactly one VFX socket” | `PASS` |
| formato legado | documento sem `particle_systems` | chaves legadas permanecem sem o campo novo | `PASS` |
| `REQ-F08-PARTICLE-RENDER` | execução nativa Godot Windows/OpenGL fora de `--headless` | PNG real com partículas visíveis, 480×270, 1907 bytes | `PASS` |

## Auditoria nativa v15

Artefato: `artifacts/post-e13-particle-scene-export-native-20260911-v15/`
Report: `post-e13-particle-scene-export-report.json` — SHA-256
`A10FF4AC36C38582378A127B5DB73890A03A554D0C794C7632E19A83F37BE0FB`
Índice: `artifact-index.json` — SHA-256
`69F2E49F4E6275F2AF90B17FD28A2EBC876269A9C92F6A4414C7E75EDC747995`
Resultado: `PASS`, `17/17` checks.

### Godot 4.7

- headless: retorno `0`, importação profissional, 1 emissor, 7 partículas;
  `headless_capture_mode=true` registra a limitação do backend dummy;
- janela nativa: `display_server=Windows`, `returncode=0`, marcador de captura
  `SUCCESS`, 7 partículas;
- log nativo: `godot-native-window.log`, SHA-256
  `C8493B333464C168B127DC82A2C102067BF5CFE357170330A5535A018000F106`;
- captura: `scene-particles-window.png`, 1907 bytes, SHA-256
  `56C8AAE8F52CE147FC7E19C92F9E1740608E6A74D8DDD8B69E781786D948C6EF`.

![Captura real do renderer Godot em janela Windows](../../artifacts/post-e13-particle-scene-export-native-20260911-v15/scene-particles-window.png)

### Unity 6000.5.7f1

- retorno `0`, compilação com `UnityEngine.JSONSerializeModule` e
  `UnityEngine.ParticleSystemModule`, 1 componente e 7 partículas;
- log positivo: `unity-positive.log`, SHA-256
  `C9E91FCA81AAA501AEEAFCFB7C9B1650E219AC10D2E6A1B6A2EE7F00DF8D1F9B`;
- o warning/licensing `Access token is unavailable` e o `Curl error 42` foram
  preservados; não alteraram o marcador funcional e não foram ocultados;
- Unity foi executado em `batchmode/nographics`; a prova visual rasterizada é
  a captura Godot, enquanto Unity comprova a materialização/contagem.

## Suíte, build e binário

- Suíte oficial sem filtros: `2208 passed, 2 skipped, 1 warning` em 2210
  testes; o warning de `QMouseEvent` foi preservado. O rerun final após o
  fechamento documental está em
  `artifacts/post-e13-particle-scene-export-native-20260911-v15/official-pytest-final.log`,
  SHA-256 `82AB34996599AFA92CB95277E8BB18BE3BE3CB5941548DBD2DCCBCF041B97E13`.
  A execução anterior do mesmo código, preservada como histórico, permanece
  em `artifacts/post-e13-particle-scene-export-native-20260911-v14/official-pytest-v2.log`,
  SHA-256 `C89C46562EA80C4D8A0EC935819D31D8E7B242FB48EEB0239638ACB03A5410AA`.
- Requalificação dos contratos documentais e do exportador: `49 passed` em
  1,75 s; log `artifacts/post-e13-native-binary-20260911-particles-requal-v2/official-requalification-contracts.log`,
  SHA-256 `BA12E4D682567E9C13E25CF82A0F421DD04864A5603BE60C0473DF71D439C19C`.
- Build oficial com proveniência: `build/post-e13-particle-scene-export-native-20260911/continuity-provenance.json`,
  SHA-256 `830AA59792C12E949762046CD3CCBC16CA6984158640774D55D48D44384CA159`;
  `source_commit=73b7fccd61f2673b6c5479581cb1645912755e22`.
- Executável portátil: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`,
  9.595.112 bytes, SHA-256
  `E6716E67305268F432FDB7536A96A22608C6408AD73099225ED2540C8FD5D80B`.
- ZIP: `NeoEng-D-Trace-0.3.0-win64-portable.zip`, 138.968.775 bytes,
  SHA-256 `B72BB9C7034CB41D814BE90C56CF0A3522D8337FF596989A7CA03C912A50E5B5`.
- Smoke: `smoke/portable-smoke-report.json`, `SUCCESS`, 11 checks, SHA-256
  `4C28F24B9EF11606D5DDA05AB094BA07D776B16662810369A1381EF1409C875E`.
- Warning de build `Hidden import "tzdata" not found` preservado; não impediu
  o smoke.

## Execução real do binário do projeto

O executável foi aberto por handle Win32 real e capturado em 3866×2090. Pacote:
`artifacts/post-e13-native-binary-20260911-particles/`.

- `launch-capture-6554212.png`: SHA-256
  `31AF6C1E3FEA86B64AD4E3AB5A85514CD2F2C0E51DDB2B64FD74E91FB28715DD`;
- `actions.jsonl`: SHA-256
  `68640D13BFE520AEE8D23334CE9C9A3EEB3ED966F200C592B72242ADB5B6B457`;
- cliques reais em `Colisão` e `Cenário` foram registrados em
  `scenario-click-6554212.png` e `scenario-editor-click-6554212.png`.

O pacote original preserva uma sequência diagnóstica em que `Colisão` foi
clicado primeiro e abriu uma janela/popup sobre o editor principal; o clique
seguinte em `Cenário` ocorreu com essa janela ainda em primeiro plano. A
captura e o finding permanecem preservados como resultado histórico dessa
sequência, sem serem apagados nem promovidos a PASS.

### Requalificação nativa do fluxo começar do zero

Uma execução nova do mesmo binário foi iniciada sem projeto nem imagem. O
primeiro clique foi diretamente em `Cenário` e abriu a janela nativa
`Editor de Cenário — NeoEng-D-Trace` (handle `6753566`, captura
`scenario-open-6753566.png`, SHA-256
`CB9AA17F403C18A3E0FE4AEE0522BC339714CCAA05785B99115265E8A2C999C5`).
Em seguida, o clique real em `Novo Cenário` materializou três molduras Z00/Z01/Z02,
guias de câmera/parallax e timeline vazia (captura `scenario-new-6753566.png`,
SHA-256 `86425D094761B93200D327405D82F29868173EF384971DA1CB39E1F1E63375FC`).

O ciclo de persistência também foi executado por interação nativa: `Salvar
Projeto` gravou `scenario-from-zero.ndtproj` e
`scenario-from-zero.ndtscene.json`; `Recarregar` restaurou as molduras,
câmera, guias e timeline. O manifesto de cliques `actions.jsonl` desta
requalificação está em
`artifacts/post-e13-native-binary-20260911-particles-requal-v2/`, SHA-256
`BEC5C9EED229BF250A332762DCF154729100534DFBBA34FFC6DAE4DF4F1D9C56`.

| Artefato da requalificação | SHA-256 | Observação |
|---|---|---|
| `scenario-new-6753566.png` | `86425D094761B93200D327405D82F29868173EF384971DA1CB39E1F1E63375FC` | cena vazia criada sem asset/imagem |
| `scenario-save-confirm-6753566.png` | `55CE3A610801462D36F8C05694189F929A7A3ED105489AA3B82E26CBE1B218B7` | projeto salvo pelo diálogo nativo |
| `scenario-reload-6753566.png` | `C95AE0F6F4417CA7C4473E1E812795544363E98CF1AECFDCE87F1306A292CA0F` | estado restaurado após recarregar |
| `scenario-from-zero.ndtproj` | `EDE878C1799E551FF42E46C7BCC730314E7C6BC3FC0EC5CA6E7D054F65D4A21E` | projeto criado no caminho de artefato isolado |
| `scenario-from-zero.ndtscene.json` | `B35DA0B1C3C918CA07101732B47C0F771E6687F8B01B446E07047F6B358ED166` | schema V2 com três camadas e câmera |

![Cena vazia criada no editor nativo](../../artifacts/post-e13-native-binary-20260911-particles-requal-v2/scenario-new-6753566.png)

O fluxo limpo atende o critério técnico de iniciar do zero; o finding
histórico fica classificado como erro de sequência do harness nativo, não como
limitação do produto.

## Limitações e fronteira de aceite

- O modo headless Godot não fornece pixels; a captura visual foi obtida em
  execução Windows/OpenGL real e essa diferença permanece declarada.
- A captura original do binário principal mostra o finding histórico da
  sequência com popup; a requalificação v2 comprova separadamente a abertura,
  criação, salvamento e recarga de uma cena vazia sem projeto/imagem.
- A revisão humana final permanece `PENDING_EVIDENCE`/deferida até concluírem
  iluminação direcional, efeitos orientáveis, sistema completo de partículas,
  tilemap/tileset e editor 3D/híbrido conforme a decisão formal.
- A suíte e os checks não autorizam push, merge, tag, release ou publicação.
