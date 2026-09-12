# Evidência pós-E13 — runtime externo do editor híbrido 2D/2.5D/3D

**ID:** `EVD-POST-E13-HYBRID-3D-RUNTIME-20260912`

**Estado:** `PASS` — gate técnico do vertical slice de runtime externo

**Estado do lote pós-E13:** `IN_PROGRESS / PENDING_EVIDENCE`

**Data:** 2026-09-12

**Branch:** `Ailton/e08-renderer-20260908`

**Commit de implementação auditado:** `2226598927dbc91a664714069068aceca2dd2fa9`

**Mudança:** [`CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md`](CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md)

**Governança:** [`../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisões:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md) e [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Escopo comprovado

Este artefato fecha somente a equivalência técnica do vertical slice híbrido
com runtime externo. O sidecar e o exportador continuam explicitamente
`VERTICAL_SLICE_ONLY`; esta evidência não promove o editor para 3D completo e
não reabre o E13.

IDs avaliados:

- `REQ-F03-SCENE-PERSISTENCE` — pacote hash-bound preservando a cena autorada;
- `REQ-F04-SCENE-VIEWPORT` — câmera, mesh, material, luz e captura observável;
- `REQ-F02-EVIDENCE-AUTOMATION` — auditoria reprodutível com hashes e falha;
- `REQ-F10-UI-ACCESSIBILITY` — strings de suporte preservadas; a UI nativa do
  editor permanece coberta pelo checkpoint anterior.

## Contrato implementado

O pacote híbrido agora contém, de forma aditiva:

- `hybrid3d.json`: fonte autorada original, preservada;
- `hybrid-runtime-scene.json`: representação normalizada para consumo nativo;
- `hybrid-runtime.json`: manifesto versionado com bindings e SHA-256 da fonte,
  cena normalizada, manifesto de animação e primeiro frame;
- adapters de produto em `integrations/godot/.../hybrid3d_runtime.gd` e
  `integrations/unity/.../NeoEngRuntimeHybrid3D.cs`.

Os adapters validam o pacote antes de criar objetos. No caminho positivo eles
criam objetos nativos: `MeshInstance3D`, `Camera3D`, `DirectionalLight3D`/
`OmniLight3D` e `AnimationPlayer` no Godot; `MeshFilter`, `MeshRenderer`,
`Camera`, `Light` e `Animation` no Unity. A animação avança para `Y=0,125` e o
primeiro frame real é decodificado.

## Testes executados

| Camada | Comando/artefato | Resultado |
|---|---|---|
| Contrato/exportação | `tests/test_composition_export.py` | `6 passed` |
| Scaffolding Godot/Unity | `tests/test_godot_plugin_scaffold.py tests/test_unity_package_scaffold.py` | `7 passed` |
| Auditoria externa | `scripts/audit_post_e13_hybrid_runtime_engines.py --engine both` | `SUCCESS` |
| Godot positivo | Godot `4.7-stable`, OpenGL Compatibility, janela Windows real | `SUCCESS` |
| Unity positivo | Unity `6000.5.7f1`, projeto temporário real | `SUCCESS` |
| Godot negativo | cena normalizada adulterada sem atualizar hash | `REJECTED` |
| Unity negativo | cena normalizada adulterada sem atualizar hash | `REJECTED` |

O pacote de entrada usado pelo auditor está em
[`artifacts/post-e13-hybrid-runtime-fixture-20260912/package`](../../artifacts/post-e13-hybrid-runtime-fixture-20260912/package).
O manifesto autoritativo da requalificação v3 está em
[`hybrid-runtime-engine-audit.json`](../../artifacts/post-e13-hybrid-runtime-engines-requalified-v3-20260912/hybrid-runtime-engine-audit.json)
com SHA-256
`C163E8B103B67700B4F801078079E960B51AEDB9DBD9DDEC3C915984AB1E5F37`.
Ele foi executado com o ambiente oficial e os caminhos explícitos de Godot
4.7 e Unity 6000.5.7f1; o comando foi:

```text
.venv311\Scripts\python.exe scripts\audit_post_e13_hybrid_runtime_engines.py --engine both --godot C:\ProgramData\chocolatey\bin\godot.exe --unity "C:\Program Files\Unity\Hub\Editor\6000.5.7f1\Editor\Unity.exe" --package artifacts\post-e13-hybrid-runtime-fixture-20260912\package --output artifacts\post-e13-hybrid-runtime-engines-requalified-v3-20260912
```

## Evidência visual real

As imagens foram geradas pelo processo dos engines, não por mock ou chamada
interna do editor:

- Godot: [`godot-hybrid-runtime-capture.png`](../../artifacts/post-e13-hybrid-runtime-engines-requalified-v3-20260912/godot-hybrid-runtime-capture.png), 640×360, SHA-256 `0CB98627C0F4EA192FD0A6FDD65728A5FC8D9752D774D371981628C60701DCA8`;
- Unity: [`unity-hybrid-runtime-capture.png`](../../artifacts/post-e13-hybrid-runtime-engines-requalified-v3-20260912/unity-hybrid-runtime-capture.png), 640×360, SHA-256 `BE4F668ECFCC516EC834569B34EAD1ED4E89D7591E055F03F42B65C36D1AC0D0`.

A captura Godot foi revisada visualmente e contém fundo e triângulo renderizado;
o auditor mediu `3.600` amostras não pretas. A captura Unity contém o mesmo
triângulo em ambiente renderizado. O guard impede `PASS` quando a captura é
vazia ou totalmente preta.

## Findings preservados durante a qualificação

O primeiro ensaio não foi apagado:

- [`post-e13-hybrid-runtime-engines-20260912`](../../artifacts/post-e13-hybrid-runtime-engines-20260912)
  registrou falha real do Godot por orientação da câmera antes da árvore e por
  textura indisponível no renderer dummy; Unity já passou o positivo e o
  negativo nesse ensaio;
- [`post-e13-hybrid-runtime-engines-20260912-v2`](../../artifacts/post-e13-hybrid-runtime-engines-20260912-v2)
  comprovou o caminho nativo com janela, mas a captura Godot ainda era preta;
- [`post-e13-hybrid-runtime-engines-20260912-v3`](../../artifacts/post-e13-hybrid-runtime-engines-20260912-v3)
  comprovou a correção visual Godot antes da execução consolidada final.

Esses resultados permanecem como histórico; somente a execução final é usada
para o `PASS` do gate.

## Limitações declaradas

O runtime comprovado é deliberadamente um vertical slice: meshes inline com
triângulos, câmera perspectiva, materiais básicos, luz direcional/pontual e
animação por posição. Permanecem fora deste gate: colisão 3D, partículas
completas, tilemap 3D, timeline/cutscene híbrida, importação de modelos 3D
externos, equivalência completa de iluminação e o editor 3D profissional
completo. A captura Godot usa o renderer OpenGL Compatibility nativo deste
ambiente; não houve fallback para imagem sintética.

O build final pós-E13, a integração automática do payload no exportador geral
de composição e a revisão humana continuam gates separados. A revisão humana
permanece `PENDING_EVIDENCE` conforme a decisão formal.
