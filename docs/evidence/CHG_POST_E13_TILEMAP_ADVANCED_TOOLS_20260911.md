# Registro de mudança pós-E13 — ferramentas avançadas e layout responsivo do Tilemap

**ID:** `CHG_POST_E13_TILEMAP_ADVANCED_TOOLS_20260911`

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`

**Data:** 2026-09-11

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Commit da exposição inicial:** `a95b308cc090952524c0aab709e3e7babd43ebcd`

**Commit da correção de histórico:** `c7ca1938701f99a72335aabc05a9171703b28b27`

**Commit auditado:** `0689e72c9051c3daeb42d656b87e9128f2a736ba`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Fronteira

Esta mudança permanece exclusivamente no lote pós-E13. E13 continua fechado e
histórico; nenhum contrato, asset ou evidência anterior foi removido ou
reinterpretado.

## Finding reproduzido

O primeiro fluxo nativo de ferramentas avançadas executou um arraste real da
Borracha. O mapa saiu de 12 para 8 células, mas o primeiro `Desfazer` restaurou
somente parte do traço, pois cada segmento emitido durante o movimento do mouse
era colocado separadamente no histórico. O finding foi preservado em
`artifacts/post-e13-tilemap-advanced-native-20260911/` e corrigido sem alterar
a aplicação incremental do desenho.

A mesma captura mostrou que, na largura real do Inspector profissional,
`Refazer` ficava fora da linha de ações e `Adicionar camada` era truncado. Isso
era uma falha de usabilidade reproduzível, não apenas uma preferência visual.

## Análise de impacto

Módulos afetados:

- `src/core/tilemap_tools.py`: agrupamento de deltas já aplicados;
- `src/ui/tilemap_authoring_panel.py`: ciclo de gesto, cinco ferramentas,
  layout responsivo e localização PT-BR;
- `tests/test_e04_tilemap_ui.py`: gesto real, undo/redo atômico e geometria
  do painel estreito.

Requisitos/features afetados:

- `TMAP-003` — edição de células e ferramentas de autoria;
- `TMAP-005` — histórico e persistência do mapa;
- `REQ-F03-SCENE-PERSISTENCE`;
- `REQ-F04-SCENE-VIEWPORT`;
- `REQ-F10-UI-ACCESSIBILITY`;
- `REQ-F02-EVIDENCE-AUTOMATION`.

Contratos preservados:

- `TileEditTransaction` continua sendo a unidade de undo/redo;
- pintura e borracha continuam aplicando segmentos em tempo real;
- Retângulo, Balde e Conta-gotas continuam transacionais e fail-closed;
- combo textual, paleta, camadas, grades e arquivos versionados existentes
  continuam compatíveis;
- nenhum asset, cena, conteúdo legado ou contrato de E13 foi removido.

## Alteração controlada

1. O canvas passou a sinalizar início e fim de cada gesto contínuo.
2. Segmentos já aplicados de pincel/borracha são agrupados em uma transação
   atômica ao soltar o mouse; um `Desfazer` ou `Refazer` opera no gesto inteiro.
3. Retângulo, Balde e Conta-gotas ficam expostos no combo localizado em
   português e inglês, com mensagens observáveis de aplicação e falha.
4. As ações do Tilemap passaram para uma grade de duas linhas, mantendo
   `Desfazer`, `Refazer`, `Salvar`, `Reabrir` e `Atualizar tileset` dentro da
   largura do Inspector.
5. `Adicionar camada` passou para uma linha própria, sem truncamento no painel
   estreito.

## Critério do checkpoint

O `PASS` deste registro é limitado à superfície implementada e comprovada:
Retângulo, Balde, Conta-gotas, pincel/borracha com histórico por gesto,
localização, layout responsivo, salvar e reabrir. Não é declaração de que o
editor final de Tilemap/Tileset já possui todos os recursos previstos no
produto.

## Verificações vinculadas

- Foco: `35 passed` em `tests/test_e04_tilemap_ui.py`,
  `tests/test_e04_tilemap_contract.py` e
  `tests/test_post_e13_tilemap_tileset_authoring.py`.
- Suíte oficial sem filtros: `2215 collected; 2213 passed; 2 skipped; 1
  warning`, preservada no log do fluxo nativo.
- Build limpa do commit auditado: smoke portátil `SUCCESS`, 11 checks.
- Fluxo nativo: cliques, seleção, arrastes, undo, redo, salvar, reabrir e
  capturas reais no executável novo.

## Limitações preservadas

Continuam `PENDING_EVIDENCE` e não foram mascarados: autotiling/Rule Tiles,
variação avançada, seleção/cópia/colagem como ferramentas completas de UI,
equivalência de runtime externo do Tilemap/Tileset, refinamentos avançados de
snapping e o caminho-fonte do atlas em um novo processo. A revisão humana final
continua deferida pela decisão formal.

O fallback de captura usado foi Win32 (`mouse_event`, `SendKeys` e
`PrintWindow`), porque o CUA falhou nesta sessão com `failed to write kernel
assets`. O fallback, a limitação e todos os resultados observados estão
registrados na evidência nativa vinculada.
