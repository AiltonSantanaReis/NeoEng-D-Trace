# Evidência nativa pós-E13 — editor híbrido 2D/2.5D/3D

**ID:** `EVD-POST-E13-HYBRID-3D-NATIVE-20260911`
**Estado:** `PASS` — checkpoint técnico do vertical slice de autoria do editor
**Estado do runtime externo:** `PENDING_EVIDENCE`
**Estado da revisão humana final:** `PENDING_EVIDENCE` — deferida por decisão formal

**Data:** 2026-09-11
**Branch:** `Ailton/e08-renderer-20260908`
**Commit de produto auditado:** `b2d2df4feb1b8107644977c83bacd3e0948e3c5c`
**Mudança:** [`CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md`](CHG_POST_E13_HYBRID_3D_AUTHORING_20260911.md)
**Governança:** [`../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
**Decisões:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md) e [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Escopo e IDs

Este artefato comprova somente a autoria nativa do editor híbrido. Os IDs
avaliados foram `REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`,
`REQ-F10-UI-ACCESSIBILITY` e `REQ-F02-EVIDENCE-AUTOMATION`, sob
`CHG-P13-HYBRID-3D-AUTHORING-20260911`.

A implementação é aditiva: o `.ndtscene.json` 2D não é sobrescrito e a cena
híbrida é salva em `*.hybrid3d.json`, com `schema_version=1`,
`format_id=neoeng-d-trace-hybrid-editor` e `support_status=EDITOR_VERTICAL_SLICE`.
O fluxo inicia sem exigir imagem ou objeto previamente carregado no viewport 2D.

## Testes e build

| Camada | Comando/artefato | Resultado observado |
|---|---|---|
| Focado | `.venv\Scripts\python.exe -m pytest -q tests/test_post_e13_hybrid_3d_authoring.py` | `5 passed` |
| Oficial sem filtros | `.venv\Scripts\python.exe -m pytest -q` | `2201 passed, 2 skipped, 1 warning` |
| Log oficial | `build/post-e13-hybrid-3d-20260911/official-suite-final.log` | SHA-256 `5C7A5C79BCA3BC73C958A54E51A1380274BD1CA921C113D4E49A7BCD99ABDB9E` |
| Log focado | `build/post-e13-hybrid-3d-20260911/hybrid-focused.log` | SHA-256 `2233A2D81F4F32FA73917C7ED9CD854922F5AF993D4B3909CE1191953C3F23E8` |
| Executável | `build/post-e13-hybrid-3d-20260911/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | SHA-256 `C3A884F7B81F3B07490762A0A86DD0F1C489F1CD3DC2F6EF93B2333E9AC6B2C9` |
| Pacote portátil | `build/post-e13-hybrid-3d-20260911/NeoEng-D-Trace-0.3.0-win64-portable.zip` | SHA-256 `E403C7CE0820B38E46FD2CA6BCBDBF02643B9CF436974DAA7B43F91D0CB57415` |
| Smoke portátil | `build/post-e13-hybrid-3d-20260911/smoke/portable-smoke-report.json` | `SUCCESS`, 11 checks; SHA-256 `AA4917E33EDE0F503E2B329E77016533F3F70475B8CFAF8540015BB3E984940B` |
| Proveniência | `build/post-e13-hybrid-3d-20260911/continuity-provenance.json` | `PASS`; SHA-256 `2BF7E4C4427686254A8C6E8D9A465DDDF801B2C3AC7D9387BA90C42C37D516D3` |

O build preserva o warning de empacotamento `Hidden import "tzdata" not
found`; o smoke continuou `SUCCESS`. A suíte preserva o warning de depreciação
de `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py`.
Nenhum warning foi convertido em PASS ou ocultado.

## Fluxo nativo real

O binário foi iniciado com o projeto de fixture, abriu a janela nativa
`Editor de Cenário — NeoEng-D-Trace` em janela maximizada de `3866x2090`, e
recebeu cliques, arrastes, botão do meio, edição de campos e reabertura. A
captura foi feita pelo helper Win32 aprovado (`mouse_event`, `keybd_event`,
`PrintWindow` e `CopyFromScreen`); a indisponibilidade do CUA foi mantida
explícita, sem substituir a operação por mock ou chamada interna da UI.

| Passo | Operação real | Evidência |
|---|---|---|
| 1 | Abrir projeto e observar o editor 2D existente | `01-editor-2d-initial.png` — SHA-256 `C95B8A618F3F8A140DBAF8155EB332CC0AC4FA86D6C5D3571C0CF2EDE547A1BF` |
| 2 | Clicar em `Ver` e observar o menu com `Viewport 3D/Híbrido` | `02-view-menu.png` — SHA-256 `262E4CA162D0364C01521FDD198306B7FCEFF4D12CFEBB0462A4395F019A8F81` |
| 3 | Clicar no item visível `Viewport 3D/Híbrido` | `03-hybrid-entry.png` — SHA-256 `56F86C01170C5A8377580D9565E8E20CD149D277CA5A08E8C53AA7E144270E71` |
| 4 | Clicar `Adicionar plano` em cena sem asset 2D extra | `04-hybrid-plane.png` — SHA-256 `263C42FCF2C48231BB4D0AB2218C9F6FA6A5DCD0DF6FE7EA3F284E36ED3460B1` |
| 5 | Clicar `Adicionar luz` e observar o marcador | `05-hybrid-light.png` — SHA-256 `3131F4A62DAAD416C145C23844EBC3F87B170701C3213DAC7EB59C0C188BE3F1` |
| 6 | Clicar `Adicionar câmera` | `06-hybrid-camera.png` — SHA-256 `70A7B4609DF347CB25DD6A2939028962D349A1E7A976D039CE5A648A40674244` |
| 7 | Clicar na câmera na hierarquia 3D | `07-camera-selected.png` — SHA-256 `ABD4F6135BBB78CC5A9E2FA9DBD6E177014BE85E2700072EC7E6B8A9C6DEDBDD` |
| 8 | Editar alvo X/Y com separador decimal PT-BR (`2,5` e `1,25`) | `08-camera-target.png` — SHA-256 `B9D231BE4DA0B5D012AE56B344BA41A77E664A49CEC0C2B1331A725CC9928AA5` |
| 9 | Arrastar o cubo com botão esquerdo | `09-mesh-drag.png` — SHA-256 `6DE2BC5E133E7B8B5DE3A20EBC29E78ED47D35314EB2E5465F5BFB668C0A0E32` |
| 10 | Orbitar o viewport com botão do meio | `10-viewport-orbit.png` — SHA-256 `61A6425F020660639AEB8F994940DC9E76D11754360488D1200A843CFDC86924` |
| 11 | Abrir a lista de projeção e clicar `Ortográfica` | `11-projection-menu.png` — SHA-256 `1C5D735AF561024CDD57E2203B2410D6E51413DDECB89E1245F8F796B0BA35B1` |
| 12 | Confirmar modo `2.5D` e projeção `Ortográfica` | `11-mode-25d-orthographic.png` — SHA-256 `9DE782CFFF12987813EB120C8D6CE361024CD1C9A2FEEC4F8FB9C88E61B29EE2` |
| 13 | Clicar `Salvar 3D` e observar mensagem de sucesso | `12-hybrid-saved.png` — SHA-256 `DED551836FE3913C00A8C0248AF7F364DCDD1D73446A84CC605CE3E902A01B45` |
| 14 | Fechar, relançar o mesmo binário e reabrir o modo híbrido | `13-hybrid-reopened.png` — SHA-256 `3F89E0D6529D1891D4C21BBBD25FEB6EF82DA7239607D9F0BD71337BE080B029` |

O manifesto do fluxo `actions.json` está em
`artifacts/post-e13-native-flow-20260911-hybrid-v9/actions.json`, SHA-256
`468B17E2CE66C13230157355FDF025CDB122BF4759E1A2B4FB20A9251332ED7C`.
O harness usado no roteiro final é
`scripts/capture_post_e13_hybrid_native.ps1`, SHA-256
`DB7C4C0A64E8BDD97AC7D855ED1FFAC4DAAF7CEB04180CD7CD84BC2CC5C00EDE`.

## Resultado observável e persistência

O fluxo terminou com `PASS_NATIVE_FLOW`. O sidecar salvo é
`artifacts/post-e13-native-flow-20260911-hybrid-v9/hybrid-fixture/e08_lighting_smoke.hybrid3d.json`,
SHA-256 `E0205325768F9D59CF12F30D77AEC4EA3D75BD910E87E33B3526D5033640BF7B`.
A validação tipada confirmou:

- `format_id` e `schema_version` corretos;
- seis objetos persistidos, incluindo `mesh-plane-1`, `light-point-1` e
  `camera-1`;
- projeção `orthographic`;
- alvo da câmera global e da câmera adicionada em `[2.5, 1.25, 0.0]`;
- posição X do cubo em `2.381`, alterada pelo arraste real;
- sidecar reaberto no segundo processo com os mesmos dados observáveis.

As telas finais exibem a localização PT-BR de modo, projeção, hierarquia,
inspector, alvo da câmera, botões de criação e mensagem `Cena híbrida salva`.

## Findings e aborts preservados

Os diretórios diagnósticos v1–v8 permanecem no pacote de artefatos; não foram
apagados nem reclassificados. Eles registram, entre outros, coordenadas da
imagem redimensionada usadas por engano, navegação por teclado que fechava o
`QMenu` sem disparar a ação, separador decimal inadequado para PT-BR e um
`SendKeys("{SPACE}")` inválido no próprio harness. O v8 comprovou o fluxo e o
v9 é o registro final após a correção textual do roteiro.

Também houve uma primeira asserção de diagnóstico que comparou números como
texto sob cultura PT-BR e produziu falso negativo; a validação foi corrigida
para números tipados e passou sem alterar o sidecar. Esse finding permanece
descrito para evitar repetir o erro de interpretação.

## Limitações e próximo gate

Este checkpoint não declara um runtime 3D externo. O sidecar é consumido e
visualizado pelo editor vertical slice, mas ainda não há prova de consumo por
Godot/Unity, renderer 3D físico, colisão 3D, partículas completas, tilemap 3D,
timeline/cutscene híbrida ou equivalência de iluminação em runtime. Esses
itens não foram simulados para obter PASS.

O lote pós-E13 continua `IN_PROGRESS`. A revisão humana final permanece
`PENDING_EVIDENCE` até que, além deste checkpoint, sejam fechados runtime
aplicável de partículas e as ferramentas restantes de tilemap/tileset, conforme
a decisão formal. Nenhuma publicação, merge, tag ou release foi executada.
