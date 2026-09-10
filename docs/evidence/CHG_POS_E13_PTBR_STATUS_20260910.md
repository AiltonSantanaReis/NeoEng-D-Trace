# Registro de mudança pós-E13 — estados PT-BR do editor

**ID:** `CHG-P13-PTBR-STATUS-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de implementação requalificada:** `cf829b7583c4a6a63fb86d8a0cafc5103808f498`

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

## Requalificação nativa final10

- O teste focado de localização passou e a build final10 foi gerada do
  commit `cf829b7`, com smoke `SUCCESS` em 11 checks.
- O material reaberto mostra `Cenário recarregado` em PT-BR;
  `artifacts/post-e13-binary-final10-20260910/material-clean/14-material-reloaded.png`,
  SHA-256 `EEAC6CED18C07D82ED1073A9087AF9862074500EA33BB16CD9E250F2862D2D2C`.
- O Tilemap mostra `Edição do tilemap aplicada` e os painéis nativos exibem
  rótulos em português; evidência
  `artifacts/post-e13-binary-final10-20260910/tilemap/09-tilemap-painted.png`,
  SHA-256 `F3AEA2FA363036436F8656A1D15379FDA90D6132CF6D49D7F9D5E9B75B6FE18B`.
- O menu contextual do viewport profissional foi capturado em PT-BR com
  `Objeto`, `Mostrar propriedades`, `Enquadrar seleção` e `Enquadrar tudo`;
  evidência `artifacts/post-e13-binary-final10-20260910/context-professional-object/07-professional-context-menu.png`,
  SHA-256 `C486E629B5DB30320B51D0E14D44ADDC2018B1FEEA8CDE079719D8EE978F35EDD`.

## Verificação exigida

O fluxo técnico de localização passou. Este registro permanece `IN_PROGRESS`
até a suíte oficial sem abort e a revisão/aceite humano formal; o finding
anterior não foi sobrescrito.
