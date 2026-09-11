# Mudança controlada — autoria e preview nativo de partículas

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`
**Data:** 2026-09-11
**Autoridade:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Decisão de continuidade:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`
**Decisão de revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Objetivo

Adicionar autoria profissional de sistemas de partículas ao Editor de Cenário,
com criação de VFX a partir de uma cena existente ou vazia, controles em
português, preview determinístico, atualização de posição, salvar/recarregar e
prova nativa real. A mudança também corrige o estado de habilitação dos
controles quando o usuário converte um socket já selecionado para `VFX`.

Este registro não reabre o E13 e não declara concluída a equivalência de
partículas em engines externas. O escopo comprovado e suas limitações estão
separados na evidência nativa vinculada.

## Análise de impacto

- **Módulos afetados:** schema de autoria V2, modelo/sessão undoable, inspector
  de cena, item gráfico do viewport, simulação determinística e exportação de
  adapters.
- **IDs/requisitos:** `REQ-F08-PARTICLE-RENDER`, `REQ-F08-PARTICLE-REPLAY`,
  `REQ-F09-PLAYBACK-CONTROL`, `REQ-F09-RUNTIME-EQUIVALENCE`, `FX-002`,
  `FX-005`, `FX-006`, `FEAT-PARTICLE-EMIT`, `FEAT-PARTICLE-REPLAY` e
  `CMP-PARTICLE-EMITTER`.
- **Contratos preservados:** documentos antigos sem `particle_systems` continuam
  válidos; a lista é omitida quando vazia; sockets de tipo diferente de `VFX`
  mantêm o comportamento anterior; exportadores não genéricos não inventam
  suporte e falham de forma explícita quando a cena contém partículas autoradas.
- **Contratos ampliados:** `SceneAuthoringDocumentV2` pode declarar sistemas e
  emissores de partículas versionáveis; sockets `VFX` referenciam o sistema;
  o viewport oferece preview reproduzível e controles de ciclo de vida.
- **Riscos:** divergência entre os valores do inspector e o snapshot salvo,
  controles desabilitados após mudança de tipo, simulação não observável,
  perda de dados em cenas legadas e falsa alegação de paridade com engines.
- **Proteções:** validadores de schema, testes de compatibilidade, atualização
  atômica de socket/sistema, teste específico da transição `Luz -> VFX`,
  simulação com `fixed_dt`/`max_substeps`, fluxo nativo com captura antes e
  depois, persistência e exportação fail-closed.
- **Migração:** nenhuma migração destrutiva; defaults são aplicados apenas ao
  carregar o formato compatível e os campos novos são preservados no salvamento.

## Critérios de aceite técnico

1. uma cena legada abre sem `particle_systems` e continua salvável;
2. o usuário consegue trocar um socket existente para `VFX` e os controles
   ficam imediatamente habilitados;
3. é possível criar um socket VFX e configurar emissor, taxa, vida, burst,
   velocidade, espalhamento, aceleração, loop e duração;
4. o preview real produz partículas observáveis e muda após o avanço do tempo;
5. reiniciar a prévia e atualizar posição não corrompem o snapshot;
6. salvar e recarregar preserva socket, sistema, emissor e valores em PT-BR;
7. suíte oficial sem filtros, build portátil e smoke são requalificados após
   o commit da correção;
8. falhas de exportação que ainda não suportam partículas permanecem explícitas
   e não são mascaradas como sucesso.

## Resultado do checkpoint

Os critérios 1–8 passaram no escopo de autoria e preview nativo documentado em
`docs/evidence/EVD_POST_E13_PARTICULAS_AUTORIA_RUNTIME_NATIVE_20260911.md`.
O checkpoint técnico permanece separado do aceite final: `REQ-F09-RUNTIME-
EQUIVALENCE` e a entrega equivalente em engines não são promovidos além do que
foi comprovado. A revisão humana continua `HUMAN_REVIEW_DEFERRED` até os
blocos de iluminação/efeitos, partículas completas, tilemap/tileset e editor
3D/híbrido atenderem à decisão formal.
