# Registro de mudança pós-E13 — estados PT-BR do editor

**ID:** `CHG-P13-PTBR-STATUS-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Finding reproduzido

No fluxo nativo PT-BR do editor, a gravação aparecia como `Cenário salvo`,
mas a etapa seguinte exibia `Scenario reloaded`. O mesmo fluxo de edição de
Material mostrava `Material updated — alterações não salvas`, misturando os
idiomas numa operação que o usuário vê como uma única jornada.

O finding foi observado no binário do lote em:

- `artifacts/post-e13-binary-final-20260910/material-final4/13-material-saved.png`
- `artifacts/post-e13-binary-final-20260910/material-final4/14-material-reloaded.png`

Essas capturas permanecem preservadas como evidência anterior à correção.

## Alteração controlada

- O status de recarga agora usa `Cenário recarregado` quando o idioma ativo é
  PT-BR, preservando `Scenario reloaded` no idioma inglês.
- Os estados de câmera, paralaxe, Material, sockets e transformação do
  Inspector passam a respeitar o idioma ativo.
- As classificações de erro do Inspector passam a encaminhar
  `language=self.current_lang`, preservando os códigos e a ação sugerida.

## Contratos preservados

- O documento V1, o schema V2, a persistência e o renderer não foram alterados.
- A alteração é somente de apresentação; os textos ingleses padrão dos testes
  e da interface EN permanecem válidos.
- Nenhuma operação, asset, camada, objeto ou ação destrutiva foi removida.

## Verificação exigida

Este registro só poderá ser promovido a `PASS` após teste PT-BR focado, suíte
oficial sem filtros, build limpa e nova captura do fluxo nativo no binário
final. O finding anterior não será sobrescrito.
