# Evidência pós-E13 — fluxo nativo de Tilemap e Tileset

**ID:** `EVD-P13-TILEMAP-TILESET-NATIVE-20260911`

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`

**Data:** 2026-09-11

**Base auditada:** `Ailton/e08-renderer-20260908` em `c1ea7bc`

**Mudança:** [`CHG_POST_E13_TILEMAP_TILESET_AUTHORING_20260911.md`](CHG_POST_E13_TILEMAP_TILESET_AUTHORING_20260911.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de continuidade:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Escopo e regra de interpretação

Esta evidência comprova uma execução nativa real no binário corrigido, com
cliques, seleção, arraste, salvamento, reabertura e capturas da janela do
Editor de Cenário. Ela não substitui a revisão humana e não declara completo o
editor de tilemap previsto para o produto final. Nenhum finding anterior foi
apagado, e a captura não é usada para provar funcionalidades que não foram
executadas.

## Rastreamento

| Requisito/feature | Operação real | Resultado controlado |
|---|---|---|
| `TMAP-001` / `REQ-F03` / `REQ-F04` | criar `Ground`, adicionar `Camada 1`, pintar 6 células em cada camada, salvar, reabrir e selecionar a segunda camada | `PASS` no subconjunto de camadas autorado; JSON final confirma `ground=6`, `layer_1=6`, 12 células |
| `TMAP-002` / `REQ-F04` | alternar `Orthogonal`, `Isométrico` e `Hexagonal` com o combo real e observar a geometria da grade | `PASS` para os três modos visuais; ajuste de resolução/snapping avançado permanece pendente |
| subconjunto de `TMAP-003` / `REQ-F04` | selecionar tile por combo, selecionar miniatura da paleta e pintar por arraste real | `PASS` para paleta, seleção e pincel; balde, borracha, retângulo, variação e seleção avançada não foram promovidos |
| `TMAP-004` | autotiling e Rule Tiles | `PENDING_EVIDENCE`; não foram inventados nem mascarados |
| subconjunto de `TMAP-005` / `REQ-F03` | salvar/reabrir tilemap e tileset e comparar estado observável | `PASS` para persistência exercitada; undo/redo, exportação reproduzível e teste de falha dedicado continuam pendentes |
| `REQ-F10-UI-ACCESSIBILITY` | abrir painéis, observar rótulos PT-BR, status e controles | `PASS` no fluxo capturado; truncamento visual do botão de camada é limitação de refinamento |
| `REQ-F02-EVIDENCE-AUTOMATION` | registrar ações, janelas, capturas e SHA-256 | `PASS`; pacote de ações e imagens preservados |

## Requalificação automatizada

- Testes focados:
  `.venv/Scripts/python.exe -m pytest -q tests/test_e04_tilemap_ui.py tests/test_e04_tilemap_contract.py tests/test_tileset_authoring_panel.py tests/test_tileset_animation_exporters.py tests/test_post_e13_tilemap_tileset_authoring.py`
  — `49 passed`.
- A correção do auditor visual foi requalificada nos testes direcionados —
  `8 passed`.
- Suíte oficial sem filtros:
  `.venv/Scripts/python.exe -m pytest -q` — `2196 passed, 2 skipped, 1 warning`
  de `2198` testes coletados.
- Log final após a documentação: `artifacts/post-e13-tilemap-tileset-20260911-official-suite-postdocs.log`;
  SHA-256 `F3F104933F9DCB427B4916093773B33E5D3CEF9DF352B14DDC0850F92D4C3767`.
  O log anterior `artifacts/post-e13-tilemap-tileset-20260911-official-suite-fix.log`
  permanece preservado com SHA `A7AF13B6FB3A8D34F9BCDD322FA617B5F14345D1AFA37345CFEEBED7708F8AD7`.
- O warning é o baseline conhecido do construtor depreciado de `QMouseEvent`
  em `tests/test_merge_coverage_authoring_contracts.py:1341`.
- A primeira suíte deste lote não foi apagada: `artifacts/post-e13-tilemap-tileset-20260911-official-suite.log`
  preserva `2194 passed, 2 failed, 2 skipped, 1 warning`. As duas falhas eram
  a classificação de cores de conteúdo do atlas no auditor Stage 1; `c1ea7bc`
  adicionou somente o arquivo de conteúdo à lista controlada e a suíte final
  passou sem filtros.

## Build e proveniência

- Manifesto: `build/post-e13-tilemap-tileset-20260911-fix/continuity-provenance.json`;
  SHA-256 `C5861CBAD507B2839B3F283F14FA8DD4D816EBA22FA3E089E9020B763BB50D29`.
- Método: PyInstaller direto com `packaging/NeoEng-D-Trace.spec`,
  `SOURCE_DATE_EPOCH` do commit e `PYTHONHASHSEED=0`.
- Executável: `build/post-e13-tilemap-tileset-20260911-fix/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
  SHA-256 `D033E4C6DEE0DBE1973038F8496B95230E7A4963E95404E4D9BF01AA482DA498`;
  8.838.017 bytes.
- Pacote portátil: `build/post-e13-tilemap-tileset-20260911-fix/NeoEng-D-Trace-0.3.0-win64-portable.zip`;
  SHA-256 `AC1CA958EA21C7746ECFFB10A103AEB7CE12DAE1945DBEDFFE7AF13A84FD4E7C`.
- Smoke: `build/post-e13-tilemap-tileset-20260911-fix/smoke/portable-smoke-report.json`;
  SHA-256 `5FBA7321D2D21A9DB43FC8D0A3713D5EA50D33A653D3D04DD7CB6F6305BDA9EF`;
  `SUCCESS`, 11 checks.
- A build wrapper oficial não foi executado porque o checkout compartilhado
  possui artefatos não rastreados prévios; nenhum arquivo foi removido ou
  mascarado. O warning `Hidden import "tzdata" not found` foi preservado e o
  smoke passou.

## Execução nativa real

O fluxo usou o executável acima, janela nativa maximizada de `3866x2090`,
handles Win32 reais e o fallback declarado
`mouse_event`/`keybd_event`/`PrintWindow`, pois o CUA não estava disponível
nesta sessão. Nenhuma janela de erro foi observada. O processo auditado foi
encerrado ao final e confirmado como `PROCESS_STOPPED`.

Pacote: `artifacts/post-e13-native-flow-20260911-tilemap-tileset-fix/`.

Registro de ações: `actions.jsonl` — SHA-256
`86163061BB693601200C7AE0872F0FF08C844CA8EEC260C2186E62C1A669A3BC`.

Sequência reproduzida:

1. abrir projeto real e o Editor de Cenário;
2. abrir `Ferramentas → Tileset / Atlas`;
3. procurar atlas real `cogumelos-a41ce9477ac7886c.png`;
4. gerar 6.084 tiles, selecionar `tile_0000` e salvar `tileset.json`;
5. abrir `Tilemap / Terreno`, criar mapa e selecionar `tile_4882`, que possui
   textura opaca visível;
6. arrastar o pincel no canvas e observar `orthogonal · 6 células`;
7. salvar, adicionar `Camada 1`, salvar novamente e reabrir;
8. selecionar `Camada 1`, pintar mais 6 células e salvar/reabrir;
9. alternar isométrico e hexagonal, capturar as geometrias e restaurar
   ortogonal antes do salvamento final.

## Capturas reais e hashes

| Estado observado | Artefato | SHA-256 |
|---|---|---|
| painel Tileset localizado | `tileset-panel-entry-real-659370.png` | `5E909D5C5376D1F3F1E7C891B6075ACDFF8A600EC1DC783CA278BEABE7712324` |
| atlas real selecionado | `tileset-atlas-selected-real-659370.png` | `25FD5BF32CFD9C9D27CC5E5C01C22C6B3C78FE79DA6F303586B05852E4E3377E` |
| atlas fatiado com preview e 6.084 tiles | `tileset-generated-real-659370.png` | `A6E2ED96C0FF80698E7956682B270704E83E0281D5D9E8F43F0D190D7B273250` |
| tile selecionado com dimensões | `tileset-tile-selected-real-659370.png` | `A6F669F9EDB131E20455428F71297F02B573143CADAB70869E27DCE0444E7E13` |
| tileset salvo | `tileset-saved-real-659370.png` | `6B0AA6D5186EB149F599476D8D77B6DC3836D337E1DDE67EABEB72452153BFD3` |
| tilemap novo | `tilemap-new-real-659370.png` | `A4FE69334C3E780E2581F4FAFC4FA5441C36DC585653938E89E591CC953AD1D7` |
| miniaturas opacas reais na paleta | `tilemap-opaque-tile-selected-real-659370.png` | `943379AA2791D39BCF58E338CDE595994358DD808452D2ADF7D7535D5C3D83CC` |
| pintura real por arraste | `tilemap-painted-opaque-real-659370.png` | `93CBB2B280E475650AB133D8ABA16444C5E1E12262B8C409A15BDDC990E929D9` |
| camada adicionada | `tilemap-layer-added-real-659370.png` | `A3247B523974D6F7528CF7DD5C8332878C766800643A0C3D864FD7F270E052E2` |
| segunda camada reaberta e selecionada | `tilemap-layer1-reopen-confirmed-real-659370.png` | `BAF534928624AE36E56FB2AB211B73F3BE6BE20DE577671EAD223897277D4698` |
| grade isométrica | `tilemap-grid-isometric-real-659370.png` | `98E9F7474F898A81B47F8D85EF31B66D07B3CFEC35805D50D6DA6DCD154B984F` |
| grade hexagonal | `tilemap-grid-hex-real-659370.png` | `05868786D9A0E545D7302CF1312A22BCE4740EE1B541B4B585DDB941C5576120` |
| salvamento final ortogonal | `tilemap-final-saved-orthogonal-real-659370.png` | `AA5E41C576A11DDF2FF2605B32B3559A3C264692D4D613B162B4C132B1F93D01` |

O atlas e a paleta usam tiles transparentes no início da ordem numérica. Por
isso a captura inicial de `tile_0000` mostra rótulos com pouca informação
visual; a captura de `tile_4882` comprova que os ícones reais aparecem quando o
tile possui pixels. Isso é uma observação de conteúdo do fixture, não uma
conversão artificial da captura.

## Persistência observada

O arquivo gerado foi preservado em
`tests/fixtures/assets/tilemaps/scenario.tilemap.json` — SHA-256
`D970E637D08BF61B3EDC9E428B2D22EADE5375E7159B82E496BBA134670E3977`.

O tileset gerado foi preservado em
`tests/fixtures/assets/tilesets/scenario/tileset.json` — SHA-256
`C4C20D6500DC4B6F6EAD2749923C5937C0537A83BEF9B267D449CCBEC0ACD89A`.

Leitura objetiva após a reabertura:

```text
grid=orthogonal
layers=2 (ground, layer_1)
cells=12 (ground=6, layer_1=6)
tileset.tiles=6084
```

O combo voltou inicialmente para `Ground` após reabrir, que é a seleção padrão
da UI; a operação nativa seguinte abriu o combo e selecionou `Camada 1`,
confirmando que a segunda camada estava persistida. A evidência final não
trata a seleção padrão como perda de dados.

## Resultado e limitações

- `PASS` no fluxo comprovado de atlas, miniaturas, seleção, pincel, camadas,
  três grades, localização e persistência.
- `PENDING_EVIDENCE` para bucket, borracha, retângulo, seleção/variação
  avançada, autotiling/Rule Tiles, undo/redo completo, exportação reproduzível
  e equivalência de runtime em engine externa.
- `PENDING_EVIDENCE` para persistência do caminho-fonte do atlas em um novo
  processo; o pacote atual preserva as texturas derivadas e permite reabrir os
  tiles do tileset.
- O botão `Adicionar camada` precisa de refinamento de layout para não ficar
  truncado no limite direito do painel.
- A revisão humana final permanece deferida; este checkpoint não encerra o
  lote pós-E13.
