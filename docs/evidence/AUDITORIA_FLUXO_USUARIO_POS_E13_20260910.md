# Auditoria do fluxo real de usuário — pós-E13 — 2026-09-10

**Estado governado:** `IN_PROGRESS`

Esta auditoria começa depois da conclusão do E13. As etapas E00–E13 não foram reabertas nem reinterpretadas. O material histórico foi preservado em `archive/legacy/20260910`; este documento registra somente a continuidade pós-E13.

## Objetivo

Executar o fluxo de um usuário comum no editor de cenário, usando a build Windows empacotada, cliques nativos e capturas da janela real em execução. Foram exercitados os fluxos de criação/edição de tilemap, colisores, navegação, entidades/prefabs, vetor, renderer, material, parallax e timeline com luz, partículas e texto/cutscene.

O procedimento foi orientado por:

- `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`;
- `docs/evidence/BASE_ATIVA_POS_E13_2026-09-09.md`;
- `docs/evidence/PLANO_POS_E13_ESTUDIO_PARALLAX_2026-09-09.md`.

## Método de evidência

- Executável testado: `NeoEng-D-Trace.exe` da build final, com título nativo `Editor de Cenário — NeoEng-D-Trace`.
- Interação: mouse/teclado Win32 sobre a janela do binário, incluindo clique direito e menus nativos quando expostos.
- Captura: `PrintWindow` da janela real, não mock, não composição offline e não imagem de referência.
- Cada fluxo foi iniciado com o projeto de fixture correspondente e cada etapa foi capturada após a ação observável.
- Os manifests das capturas preservam hashes SHA-256 e observações da execução.

## Matriz de resultados

| ID | Fluxo verificado | Evidência real | Estado | Observação |
|---|---|---|---|---|
| AUDIT-UI-01 | Abrir projeto/editor e entrar no fluxo de autoria | `sequence-c35/06-sequence-studio-after-clip.png` | PASS | Janela nativa, projeto carregado e timeline visíveis na build c35. |
| AUDIT-UI-02 | Biblioteca de assets e ferramenta vetorial | `vector-c35/13-vector-contour-created.png` | PASS | Asset selecionado, contorno detectado/corrigido e objeto criado. |
| AUDIT-UI-03 | Criar tilemap, pintar, salvar e reabrir | `tilemap-c35-rerun/11-tilemap-reopened.png` | PASS | 2 células persistiram após reabertura; painel nativo `Tilemap / Terreno` e mensagem em PT-BR confirmados. |
| AUDIT-UI-04 | Criar/editar tileset dedicado | `tileset-c35/10-tileset-reopened.png` | PASS | Atlas real, 300 tiles gerados, `tileset.json` salvo, limpo e reaberto com os 300 tiles preservados. |
| AUDIT-UI-05 | Criar colisores box/circle, salvar e reabrir | `collider-c35/09-collider-reopened.png` | PASS | 2 colisores persistiram após reabertura. |
| AUDIT-UI-06 | Criar região/obstáculo, fazer bake, salvar e reabrir | `navmesh-c35-rerun/09-navmesh-reopened.png` | PASS | Região, obstáculo e bake persistem; a captura reaberta mostra `bake disponível` e a mensagem nativa `NavMesh reaberta; bake disponível`. |
| AUDIT-UI-07 | Criar entidade, prefab, instância, override, atualizar e desvincular | `entities-c35/15-prefab-detached-state.png` | PASS | Estados de override, versão do prefab e detach foram observados. |
| AUDIT-UI-08 | Alternar renderer preview/authoring | `renderer-c35/08-renderer-authoring.png` | PASS | HUD nativo alternou `PREVIEW` e `AUTHORING`; preview ficou somente leitura. |
| AUDIT-UI-09 | Selecionar objeto e editar material/albedo | `material-c35/12-material-applied.png` | PASS | Edição real com fixture de objeto V2 e mensagem de alteração não salva. Fixture V1 não editável foi preservada como diagnóstico, não como sucesso. |
| AUDIT-UI-10 | Editar parallax de camada | `parallax-c35/07-parallax-applied.png` | PASS | Profundidade e translação alteradas para `0,7500`; aplicação e mensagem de alteração não salva confirmadas. |
| AUDIT-UI-11 | Timeline com câmera, luz, partículas/chuva e texto/cutscene | `sequence-c35/09-sequence-studio-text-clip-real.png` | PASS | Quatro tracks visíveis; clips de Luz, Chuva e Texto/cutscene adicionados por fluxo real. |
| AUDIT-UI-12 | Menu de contexto do mouse | `context-menu-c35/06-context-menu-layer.png` | PASS | Clique direito nativo no primeiro objeto da lista principal abriu o popup real com `Propriedades`, `Modificar Forma` e `Exportar`. |
| AUDIT-UI-13 | Localização PT-BR de painéis, controles e tooltips | Capturas `tilemap-c35-rerun`, `collider-c35`, `navmesh-c35-rerun`, `parallax-c35`, `context-menu-c35` | PASS | Painéis, mensagens, popup de contexto e contratos de tooltip verificados em português. |
| AUDIT-UI-14 | Build nova, execução do binário e smoke runtime | `release/user-flow-audit-c35d458e-20260910/smoke/portable-smoke-report.json` | PASS | 11 checks com status `SUCCESS`; ZIP e executável da build baseada em `35d458e` foram hash-confirmados. |

## Evidências principais

- [Tilemap reaberto](../../artifacts/user-flow-binary-20260910/tilemap-c35-rerun/11-tilemap-reopened.png) — SHA-256 `34420CD7E816D649EECD06A7FBD601352AC7C2DBE7BD2C24D37983E817E1DA3C`.
- [Colisores reabertos](../../artifacts/user-flow-binary-20260910/collider-c35/09-collider-reopened.png) — SHA-256 `8E79E4C4D02DA4345D501491BD450027290D525985FAA8D2F6B33DD4297CFAA9`.
- [NavMesh reaberta — bake persistido](../../artifacts/user-flow-binary-20260910/navmesh-c35-rerun/09-navmesh-reopened.png) — SHA-256 `E0B242E6A2A614BC70BCB834CF3D7B063C670A5BA89B48B75945203EE55350B8`.
- [Prefab desvinculado](../../artifacts/user-flow-binary-20260910/entities-c35/15-prefab-detached-state.png) — SHA-256 `825630BF90C0D34AE71F73F2A50A466B9C93231065D5872D48592BD74FEF34D0`.
- [Objeto vetorial criado](../../artifacts/user-flow-binary-20260910/vector-c35/13-vector-contour-created.png) — SHA-256 `C6D906074C8038C39F7E1DCEC4A73464BCF44B42740D8E1827A7CDA6AB1B7FF6`.
- [Renderer em preview](../../artifacts/user-flow-binary-20260910/renderer-c35/07-renderer-preview.png) — SHA-256 `0D6E25E9C9B77FF1DF42E1A0454269518584B60545968615CF915215AD309834`.
- [Material aplicado](../../artifacts/user-flow-binary-20260910/material-c35/12-material-applied.png) — SHA-256 `24570BD4958E1ABDEF2456BA93E043B60BED4602DDD02C81614EB39F96634BA8`.
- [Parallax com profundidade e translação atualizadas](../../artifacts/user-flow-binary-20260910/parallax-c35/07-parallax-applied.png) — SHA-256 `18BFB664C8308E609AEE59DD0292A72570DB8F35642B91B73FCD83032CAB6882`.
- [Tileset dedicado reaberto](../../artifacts/user-flow-binary-20260910/tileset-c35/10-tileset-reopened.png) — SHA-256 `C0DD13830B8074368B9C77A96AE0140F10AD6A1DAEA49502884AB16655826901`.
- [Timeline com Texto/cutscene](../../artifacts/user-flow-binary-20260910/sequence-c35/09-sequence-studio-text-clip-real.png) — SHA-256 `9C2004734FB53EF2E4FCD2A2F333BA2CE09A035B643B08A0D72E04B3E821A183`.
- [Menu de contexto nativo em PT-BR](../../artifacts/user-flow-binary-20260910/context-menu-c35/06-context-menu-layer.png) — SHA-256 `C609C6AACA9F5A95D94619471F565A3E62E7F235863BA67757FDF1DF41C1C4DF`.
- [Tentativa histórica preservada do menu](../../artifacts/user-flow-binary-20260910/context-menu-v5/06-context-menu-layer.png) — SHA-256 `234D5DE7904A553AAE47C9DB9C9DD3550E39C9BF97BDFB769F4F341873B8C60C`; mantida como diagnóstico anterior.

## Testes automatizados

Com o interpretador correto da workspace:

```text
2155 passed, 2 skipped, 1 warning in 62.81s
```

Suíte focal pós-E13:

```text
49 passed in 2.52s
```

A única advertência registrada é a construção depreciada de `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`; não houve falha de teste.

## Build final

- Arquivo: [NeoEng-D-Trace-0.3.0-win64-portable.zip](../../release/user-flow-audit-c35d458e-20260910/NeoEng-D-Trace-0.3.0-win64-portable.zip)
- SHA-256: `9EF4CE28E6D46D97FD83A22D83D47EC4FD40998EAE5107C7179DF6ECFE7214B1`
- Executável: `NeoEng-D-Trace.exe`, SHA-256 `DE02A93AA983809A27E29AD4F25E76DB36BC49F5414745093F8C71DCE8D6B402`.
- Smoke: [portable-smoke-report.json](../../release/user-flow-audit-c35d458e-20260910/smoke/portable-smoke-report.json), `status: SUCCESS`, versão `0.3.0`.
- O empacotamento emitiu o warning de hidden import `tzdata` não encontrado; o processo não falhou e o smoke passou, mas a observação deve permanecer para futura limpeza do empacotamento.
- Commit de aplicação auditado: `35d458e` (`fix: persist valid navmesh bake`). A captura válida foi repetida com o binário desse commit; o harness também registra a correção da coordenada nativa após a inclusão da aba Tileset.

## Diagnóstico preservado e limitação remanescente

- A primeira tentativa com o binário c35 foi preservada em `artifacts/user-flow-binary-20260910/navmesh-c35/`; ela selecionou `Colisores / Física` porque a nova aba Tileset deslocou a coordenada do harness. Não foi promovida a evidência de sucesso.
- A captura corrigida em `navmesh-c35-rerun/` foi executada novamente por cliques nativos e é a evidência oficial de `AUDIT-UI-06`.
- A primeira rodada agregada `tilemap-c35/` também foi preservada como diagnóstico: o fluxo selecionou Tileset após o deslocamento da aba; `tilemap-c35-rerun/` é a evidência oficial de `AUDIT-UI-03` após a correção do harness.
- O empacotamento ainda emite o warning de hidden import `tzdata` não encontrado. O smoke passou, mas a limpeza desse warning permanece como melhoria de release; ele não foi ocultado.

Esta auditoria não declara o projeto inteiro concluído; registra o lote pós-E13 auditado com as limitações acima.
