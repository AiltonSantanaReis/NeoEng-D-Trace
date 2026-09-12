# Registro de mudança pós-E13 — autoria de Tilemap e Tileset

**ID:** `CHG-P13-TILEMAP-TILESET-AUTHORING-20260911`

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`

**Data:** 2026-09-11

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Commit de implementação:** `0ac4ac7` (`feat: improve tilemap and tileset authoring`)

**Commit de requalificação:** `c1ea7bc` (`fix: classify tileset content colors in stage1 audit`)

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Objetivo

Fechar o incremento pós-E13 de autoria visual de tileset e tilemap sem remover
os fluxos existentes: atlas real com recorte visual, miniaturas, paleta de
tiles, pintura por arraste, camadas, três geometrias de grade, localização
PT-BR e persistência observável no Editor de Cenário.

Este registro não reabre o E13 e não declara concluído o requisito final de
tilemap profissional. O subconjunto comprovado, as ferramentas ainda ausentes
e a equivalência de runtime permanecem separados na evidência vinculada.

## Finding e análise de impacto

O baseline nativo preservado em
`artifacts/post-e13-native-flow-20260911-tilemap-baseline/` mostrava células
do tilemap como retângulos verdes sem textura de atlas e o painel de Tileset
sem preview de atlas/miniaturas. A primeira abertura também expunha rótulos
de formulário em inglês. O finding foi reproduzido no binário anterior e não
foi apagado.

Módulos afetados:

- `src/core/tilemap_model.py`: API de camadas adicionáveis e visibilidade;
- `src/ui/tileset_authoring_panel.py`: preview real do atlas, grade de slices,
  seleção, miniaturas, carregamento de texturas e rótulos PT-BR/EN;
- `src/ui/tilemap_authoring_panel.py`: paleta com ícones, carregamento do
  tileset salvo, renderização das texturas, camadas, estados e geometrias;
- `tests/test_post_e13_tilemap_tileset_authoring.py`: regressões visuais,
  persistência e renderização de textura;
- `scripts/audit_stage1_contract.py`: classificação explícita das cores de
  conteúdo do atlas, sem relaxar o auditor de chrome.

Requisitos e IDs afetados:

- `TMAP-001`, `TMAP-002`, subconjunto de `TMAP-003` e `TMAP-005`;
- `REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`,
  `REQ-F10-UI-ACCESSIBILITY` e `REQ-F02-EVIDENCE-AUTOMATION`;
- `P13-NATIVE-03` e `P13-NATIVE-04` como continuidade da auditoria pós-E13.

Contratos preservados:

- documentos de tilemap e tileset continuam versionados e legíveis;
- o combo textual de seleção foi preservado para compatibilidade, enquanto a
  paleta visual foi agregada em paralelo;
- o fallback de placeholder continua disponível quando uma textura não está
  disponível;
- cenas e assets existentes não foram removidos e não houve alteração de
  contratos de E13.

Riscos controlados:

- atlas grande pode gerar muitas texturas derivadas e aumentar I/O;
- tiles transparentes podem parecer apenas texto até que um tile com conteúdo
  seja selecionado;
- o caminho de origem do atlas ainda não é persistido no JSON do tileset, por
  isso um novo processo pode exigir reseleção para reconstruir o preview do
  atlas, embora as texturas por tile permaneçam listáveis;
- o botão `Adicionar camada` fica parcialmente truncado na largura capturada
  do painel, apesar de ter sido acionável no fluxo real.

## Alteração controlada

1. O Tileset passou a exibir o atlas real, linhas de recorte, seleção de tile,
   miniaturas e dimensões do tile selecionado.
2. O Tilemap passou a carregar o tileset salvo, exibir miniaturas reais,
   renderizar texturas nas células e oferecer camada ativa, criação de camada
   e visibilidade sem remover o combo legado.
3. A renderização de grade distingue ortogonal, isométrica e hexagonal no
   viewport do painel.
4. Os textos de criação, salvamento, reabertura, edição e falha do fluxo foram
   mantidos em PT-BR/EN.
5. A auditoria de Stage 1 foi corrigida para reconhecer as cores do atlas como
   conteúdo, preservando a detecção de cores de chrome não classificadas.

## Critério de checkpoint

O checkpoint técnico pode ser `PASS` apenas para a superfície implementada e
comprovada: importar atlas, gerar tiles, selecionar miniatura, criar mapa,
pintar por arraste, adicionar camada, alternar as três grades, salvar,
reabrir e localizar a interface. `TMAP-003` além de pincel/paleta,
`TMAP-004` e a paridade de runtime ficam `PENDING_EVIDENCE`.

A revisão humana final continua `HUMAN_REVIEW_DEFERRED` porque ainda depende
dos blocos de partículas/runtime, tilemap/tileset completo e editor 3D/híbrido
definidos na decisão formal.

