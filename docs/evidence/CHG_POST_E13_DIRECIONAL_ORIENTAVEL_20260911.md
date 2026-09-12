# Mudança controlada — iluminação direcional e efeitos orientáveis

**Estado:** TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED
**Lote:** POST-E13-SCENE-EDITOR-ASSET-PACKS  
**Data:** 2026-09-11  
**Autoridade:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`  
**Decisão de continuidade:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Objetivo

Fechar o primeiro item aberto autorizado após E13: permitir que luzes direcionais
e efeitos visuais orientáveis sejam criados, reposicionados, rotacionados,
visualizados no viewport, persistidos e reabertos sem alterar o significado das
cenas existentes.

## Análise de impacto

- **Módulos afetados:** schema de autoria V2, modelo/sessão undoable, inspector,
  item gráfico de socket, viewport e rasterizador de iluminação.
- **IDs/requisitos:** requisitos `FX-001`, `FX-005` e `FX-006`; continuidade do
  lote pós-E13 e critérios de cena/parallax. A revisão humana final permanece
  deferida e não é substituída por esta etapa.
- **Contratos preservados:** JSON legado sem `rotation` continua válido; sockets
  de luz omitindo `kind` continuam sendo luzes `point`; APIs existentes de
  `update_socket_position` e `ScenePointLight` permanecem disponíveis.
- **Contratos ampliados:** sockets passam a aceitar transformação orientável;
  luzes passam a declarar `kind=point|directional`; a iluminação direcional
  participa do mesmo resultado de pixels do preview raster.
- **Riscos:** alteração de serialização de defaults, regressão no gesto antigo
  de arrastar, divergência entre rotação visual e contribuição luminosa, e
  perda de dados em cenas legadas.
- **Proteções:** testes de compatibilidade sem campos novos, testes de modelo e
  undo, testes de pixels para direção/inversão, teste de gesto do gizmo, teste de
  inspector/PT-BR e suíte oficial sem filtros.
- **Migração:** nenhuma migração destrutiva; Pydantic aplica defaults somente ao
  carregar documentos antigos e o novo snapshot preserva os campos em salvamento.
- **Limites desta etapa:** partículas completas, tilemap/tileset e editor 3D
  continuam abertos e não serão declarados concluídos aqui.

## Critérios de aceite da etapa

1. documento antigo abre com `kind=point` e rotação zero;
2. luz direcional altera pixels conforme sua orientação, intensidade e cor;
3. viewport exibe a direção e permite girar por handle, além do arraste antigo;
4. VFX/postprocess acompanha a rotação orientada no viewport;
5. inspector oferece rotação do socket e tipo de luz com localização PT-BR;
6. salvar/reabrir preserva posição, rotação, tipo e preview observável;
7. testes focados passam como diagnóstico e a suíte oficial completa requalifica
   sem filtro antes de qualquer build;
8. build nativa limpa, execução real, captura e hashes foram produzidos após o
   commit da implementação; a evidência completa está em
   `docs/evidence/EVD_POST_E13_DIRECIONAL_ORIENTAVEL_NATIVE_20260911.md`.

## Resultado

Os oito critérios foram comprovados por testes, build limpa e fluxo nativo real.
O incremento está tecnicamente fechado, mas o lote pós-E13 permanece aberto para
partículas completas, tilemap/tileset e editor 3D. A revisão humana final segue
`HUMAN_REVIEW_DEFERRED` conforme a decisão formal.
