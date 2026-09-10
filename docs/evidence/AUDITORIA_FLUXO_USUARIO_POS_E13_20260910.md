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
| AUDIT-UI-01 | Abrir projeto/editor e entrar no fluxo de autoria | `sequence-studio-v3/06-sequence-studio-camera.png` | PASS | Janela nativa e timeline visíveis. |
| AUDIT-UI-02 | Biblioteca de assets e ferramenta vetorial | `vector-v4/13-vector-contour-created.png` | PASS | Asset selecionado, contorno detectado/corrigido e objeto criado. |
| AUDIT-UI-03 | Criar tilemap, pintar, salvar e reabrir | `tilemap-v3/11-tilemap-reopened.png` | PASS | 2 células persistiram após reabertura; mensagens em PT-BR. |
| AUDIT-UI-04 | Criar/editar tileset dedicado | — | PENDING_EVIDENCE | Há contratos/exportadores de tileset e o tilemap usa tipos internos, mas não foi encontrada uma tela nativa dedicada de autoria de tileset nesta build. Não classificar como PASS. |
| AUDIT-UI-05 | Criar colisores box/circle, salvar e reabrir | `collider-v2/09-collider-reopened.png` | PASS | 2 colisores persistiram após reabertura. |
| AUDIT-UI-06 | Criar região/obstáculo, fazer bake, salvar e reabrir | `navmesh-v3/09-navmesh-reopened.png` | PASS | Região e obstáculo persistem. Limitação observada: o bake é transitório e precisa ser executado novamente depois de reabrir. |
| AUDIT-UI-07 | Criar entidade, prefab, instância, override, atualizar e desvincular | `entities-v8/15-prefab-detached-state.png` | PASS | Estados de override, versão do prefab e detach foram observados. |
| AUDIT-UI-08 | Alternar renderer preview/authoring | `renderer-v2/08-renderer-authoring.png` | PASS | HUD nativo alternou `PREVIEW` e `AUTHORING`; preview ficou somente leitura. |
| AUDIT-UI-09 | Selecionar objeto e editar material/albedo | `material-v6-v2object/12-material-applied.png` | PASS | Edição real com fixture de objeto V2 e mensagem de alteração não salva. Fixture V1 não editável foi preservada como diagnóstico, não como sucesso. |
| AUDIT-UI-10 | Editar parallax de camada | `parallax-v5-v2object/07-parallax-applied.png` | PASS | Translação alterada para `0,7500` e aplicação confirmada. Limitação: o clique de profundidade não alterou o valor e não foi promovido a sucesso. |
| AUDIT-UI-11 | Timeline com câmera, luz, partículas/chuva e texto/cutscene | `sequence-studio-v3/09-sequence-studio-text-clip-real.png` | PASS | Quatro tracks visíveis; clips de Luz, Chuva e Texto/cutscene adicionados por fluxo real. |
| AUDIT-UI-12 | Menu de contexto do mouse | `context-menu-v5/06-context-menu-layer.png` | PENDING_EVIDENCE | Clique direito e fallback `Shift+F10` foram tentados. O popup não foi exposto como janela top-level para a captura; a imagem é preservada, mas não comprova o menu. |
| AUDIT-UI-13 | Localização PT-BR de painéis, controles e tooltips | Capturas `tilemap-v3`, `collider-v2`, `navmesh-v3`, `parallax-v5-v2object` | PASS | Textos visíveis dos painéis e mensagens verificadas em português. O menu de contexto permanece pendente. |
| AUDIT-UI-14 | Build nova, execução do binário e smoke runtime | `release/user-flow-audit-final-20260910/smoke/portable-smoke-report.json` | PASS | 11 checks com status `SUCCESS`; ZIP final e hash confirmados. |

## Evidências principais

- [Tilemap reaberto](../../artifacts/user-flow-binary-20260910/tilemap-v3/11-tilemap-reopened.png) — SHA-256 `ACDD3F7E2607135CE8ED670FA1579981AF2CC1ACD57DB453EC18E5EA1B8E87B8`.
- [Colisores reabertos](../../artifacts/user-flow-binary-20260910/collider-v2/09-collider-reopened.png) — SHA-256 `9EEC0833D989ED819DDE4A6673C1181CB72095CCB5CF5D2CB3CAE39A129B4581`.
- [NavMesh reaberta](../../artifacts/user-flow-binary-20260910/navmesh-v3/09-navmesh-reopened.png) — SHA-256 `533C6F3DFF9D5B219C3430B3A5EB301DC1B28B86380E845763264AB68F024A28`.
- [Prefab desvinculado](../../artifacts/user-flow-binary-20260910/entities-v8/15-prefab-detached-state.png) — SHA-256 `43738AC99529BAF9254719F8D45104A42D4D2FF85200E8BFE0A68DCF7EEAEAFE`.
- [Objeto vetorial criado](../../artifacts/user-flow-binary-20260910/vector-v4/13-vector-contour-created.png) — SHA-256 `C6D906074C8038C39F7E1DCEC4A73464BCF44B42740D8E1827A7CDA6AB1B7FF6`.
- [Renderer em preview](../../artifacts/user-flow-binary-20260910/renderer-v2/07-renderer-preview.png) — SHA-256 `0D6E25E9C9B77FF1DF42E1A0454269518584B60545968615CF915215AD309834`.
- [Material aplicado](../../artifacts/user-flow-binary-20260910/material-v6-v2object/12-material-applied.png) — SHA-256 `33F53FC1B1DBACED8C2605B9DFF9CE99AA83C9B8198681F94FC8CD1607DBD3B3`.
- [Parallax atualizado](../../artifacts/user-flow-binary-20260910/parallax-v5-v2object/07-parallax-applied.png) — SHA-256 `869731A04C426ED998CA6813F608AC69C3F8E689730EF8EEEE8A3A8906D6322D`.
- [Timeline com Texto/cutscene](../../artifacts/user-flow-binary-20260910/sequence-studio-v3/09-sequence-studio-text-clip-real.png) — SHA-256 `9C2004734FB53EF2E4FCD2A2F333BA2CE09A035B643B08A0D72E04B3E821A183`.
- [Tentativa preservada do menu de contexto](../../artifacts/user-flow-binary-20260910/context-menu-v5/06-context-menu-layer.png) — SHA-256 `234D5DE7904A553AAE47C9DB9C9DD3550E39C9BF97BDFB769F4F341873B8C60C`; não comprova popup.

## Testes automatizados

Com o interpretador correto da workspace:

```text
2151 passed, 2 skipped, 1 warning in 69.80s
```

Suíte focal pós-E13:

```text
55 passed in 6.70s
```

A única advertência registrada é a construção depreciada de `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`; não houve falha de teste.

## Build final

- Arquivo: [NeoEng-D-Trace-0.3.0-win64-portable.zip](../../release/user-flow-audit-final-20260910/NeoEng-D-Trace-0.3.0-win64-portable.zip)
- SHA-256: `485CB2AA57A08071C9B6948FDDFFAD45FB19FE9709D26F052725813B270EEBB3`
- Smoke: [portable-smoke-report.json](../../release/user-flow-audit-final-20260910/smoke/portable-smoke-report.json), `status: SUCCESS`, versão `0.3.0`.
- O empacotamento emitiu o warning de hidden import `tzdata` não encontrado; o processo não falhou e o smoke passou, mas a observação deve permanecer para futura limpeza do empacotamento.
- Commit auditado: `fe8b7238fe806a635dba3f7f4fe39acc433193ee` (`test: capture post-e13 binary user flows`).

## Próximas ações obrigatórias

1. Expor/capturar o menu de contexto como evidência nativa real, incluindo suas descrições em PT-BR.
2. Definir se o produto terá um editor de tileset dedicado; se sim, implementar ou evidenciar o fluxo nativo de criar, editar, salvar e reabrir.
3. Corrigir ou investigar o controle de profundidade do parallax, pois a alteração testada não modificou o valor.
4. Decidir se o bake da NavMesh deve ser persistido ou se a necessidade de rebake após reabertura é comportamento documentado.
5. Reexecutar a build e a captura completa após essas correções, preservando os artefatos desta auditoria.

Esta auditoria não declara o projeto inteiro concluído. Os itens `AUDIT-UI-04` e `AUDIT-UI-12` permanecem `PENDING_EVIDENCE`, e as limitações registradas não foram ocultadas.
