# Registro de mudança pós-E13 — viewport híbrido 2D/2.5D/3D

**ID:** `CHG-P13-HYBRID-3D-AUTHORING-20260911`

**Estado:** `CHECKPOINT TÉCNICO PASS`

**Data:** 2026-09-11

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de execução:** `Ailton/e08-renderer-20260908`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisões:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md) e [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Objetivo

Adicionar ao Editor de Cenário um viewport híbrido separado do fluxo 2D
existente, capaz de criar uma cena 3D vazia, visualizar meshes/luzes/câmera,
alternar projeção e modos 2D/2.5D/3D, editar transformações com gizmo e
persistir o sidecar sem alterar nem remover o `.ndtscene.json` legado.

O trabalho é uma extensão controlada do vertical slice E12 já existente. Não
promove o exportador `VERTICAL_SLICE_ONLY` a produto 3D completo e não fecha
os requisitos finais antes de testes nativos, persistência, build e evidência.

## Análise de impacto

- **Módulos novos:** modelo/IO do sidecar híbrido e viewport Qt de projeção
  determinística.
- **Módulo integrado:** `src/ui/scenario_editor_window.py`, apenas com uma
  ação e uma página adicionais; o viewport 2D, inspector, timeline e painéis
  existentes permanecem intactos.
- **IDs afetados:** `REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`,
  `REQ-F10-UI-ACCESSIBILITY`, `REQ-F02-EVIDENCE-AUTOMATION` e o escopo final
  de 3D/híbrido da especificação de cenários.
- **Contratos preservados:** `.ndtscene.json`, schema V2, exportador E12 e
  documentos sem sidecar híbrido continuam válidos; a criação do sidecar é
  explícita e nunca sobrescreve o documento 2D.
- **Riscos:** divergência entre projeção de autoria e runtime externo,
  seleção ambígua em perspectiva, valores não persistidos e confusão entre a
  câmera do editor e a câmera autorada da cena.
- **Proteções:** sidecar versionado, validação fail-closed, câmera de editor
  separada da câmera autorada, controles localizados, teste de pintura e
  round-trip, captura nativa e limitação explícita `PENDING_EVIDENCE` para
  runtime externo.

## Implementação e findings reproduzíveis

- O viewport híbrido foi implementado como página adicional do Editor de
  Cenário. Ele inicia sem asset 2D, cria cubo/plano/luz/câmera, alterna 2D,
  2.5D e 3D, alterna perspectiva/ortográfica, permite selecionar pela
  hierarquia ou pelo viewport, arrastar objetos, editar transformações e alvo
  da câmera, e salvar/reabrir somente o sidecar `*.hybrid3d.json`.
- O primeiro teste de pintura encontrou uma exceção Qt real no cálculo de
  `QRectF`; a correção foi aplicada antes do aceite. O mesmo fluxo encontrou
  um defeito de acumulação de delta no arraste, corrigido para usar a posição
  total desde o início do gesto.
- A qualificação integrada revelou um ciclo de importação entre exportador,
  persistência e adaptadores de runtime. As validações do manifesto passaram a
  ser importadas sob demanda nos dois pontos de uso, sem alterar a API pública;
  os contratos de runtime voltaram a importar e passar.
- O auditor visual Stage 1 também encontrou o estilo inline do viewport. O
  estilo foi removido e os tons de grade, gizmo e marcadores foram classificados
  explicitamente como semântica de conteúdo 3D no auditor, como já ocorre com
  o viewport profissional 2D, tilemap e timeline.

Esses findings permanecem rastreáveis nos testes e não foram convertidos em
`PASS` por filtro. A promoção do checkpoint técnico foi comprovada por build
limpa, execução nativa com cliques, persistência, capturas hashadas e análise
explícita da limitação de runtime externo. A implementação continua
deliberadamente limitada ao estado `EDITOR_VERTICAL_SLICE`; isso não equivale
a runtime 3D externo nem encerra a revisão humana final.

## Evidência do checkpoint

O fluxo nativo, a suíte oficial e os hashes estão registrados em
[`EVD_POST_E13_HYBRID_3D_NATIVE_20260911.md`](EVD_POST_E13_HYBRID_3D_NATIVE_20260911.md).
O escopo comprovado é autoria híbrida no editor: cena iniciada sem asset 2D,
criação de plano/luz/câmera, seleção hierárquica, edição de alvo, arraste,
órbita, modos 2.5D/3D, projeção ortográfica, salvar/reabrir e localização
PT-BR. Permanecem `PENDING_EVIDENCE` a equivalência com runtime externo e a
revisão humana final deferida pela decisão formal pós-E13.

## Critério de saída

O checkpoint só poderá ser promovido quando houver implementação, testes,
suíte oficial sem filtros, build hashada, fluxo nativo real de criação/edição,
capturas, salvar/reabrir e limitações. O aceite humano final permanece
deferido até todos os blocos definidos pelo proprietário passarem.
