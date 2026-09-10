# Registro de mudança pós-E13 — edição de material com defaults

**ID:** `CHG-P13-MATERIAL-DEFAULT-EDIT-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de implementação requalificada:** `cf829b7583c4a6a63fb86d8a0cafc5103808f498`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Finding reproduzido

No fluxo nativo do binário pós-E13, um objeto V2 recém-posicionado no editor
ficou selecionável e renderizado, mas a aba `Material` apresentou os controles
desabilitados porque `SceneObjectAuthoringRecord.material` é opcional e ainda
estava `None`. Isso impedia o primeiro ajuste de material pelo caminho normal
do usuário, embora o contrato V2 já ofereça defaults válidos.

Evidência de diagnóstico preservada em:

- `artifacts/post-e13-binary-final-20260910/material-final2/`
- `artifacts/post-e13-binary-final-20260910/material-final2/11-material-albedo-edited.png`
- `artifacts/post-e13-binary-final-20260910/material-final2/12-material-applied.png`

As capturas mostram a entrada real no Material e a tentativa de edição, com
`Albedo #ffffff` permanecendo inalterado e sem `Material updated`. O pacote é
mantido como finding anterior à correção; não foi sobrescrito.

## Alteração controlada

### Antes

`SceneAuthoringInspector._refresh_material_fields()` habilitava a aba somente
quando o documento era V2 e o objeto selecionado já possuía um
`SceneMaterialAuthoringRecord`.

### Depois

Para documento V2 com objeto selecionado, os controles passam a ficar
habilitados. Quando o objeto ainda não possui material, a UI exibe um
`SceneMaterialAuthoringRecord()` tipado com defaults; o registro só é gravado
no documento quando o usuário aciona `Aplicar Material`/`Apply Material`.

### Contratos preservados

- Documento V1 continua com as páginas avançadas desabilitadas.
- Ausência de seleção continua desabilitando os controles.
- O schema não foi ampliado nem tornou `material` obrigatório.
- Nenhum objeto, asset, material existente ou ação destrutiva foi removido.
- `update_material()` continua sendo a única operação transacional e
  permanece compatível com undo/redo.

## Impacto e risco

**Módulo afetado:** `src/ui/scene_authoring_inspector.py`.

**Feature:** edição visual de material no Inspector V2 (`E08-C.4` / P13-B).

**Risco principal:** materializar defaults sem intenção durante refresh.

**Mitigação:** defaults são somente apresentados; a persistência ocorre apenas
no botão Apply, e o teste verifica que a operação cria um registro e entra no
histórico.

## Verificação exigida

Este registro só poderá ser promovido a `PASS` após:

1. teste focado de inicialização e aplicação do material;
2. suíte oficial sem filtros;
3. build limpa com commit identificado;
4. repetição do fluxo no binário, com captura real antes/depois e persistência;
5. atualização do relatório final com hashes e limitações.

Até esses gates, este registro permanece `IN_PROGRESS`; a falha original não é
reclassificada nem ocultada.

## Requalificação nativa final10

- A build limpa final10 foi produzida do commit `cf829b7`, com smoke
  `SUCCESS` em 11 checks.
- A captura `artifacts/post-e13-binary-final10-20260910/material-clean/11-material-authoring-selected.png`
  mostra os controles habilitados para o objeto V2 sem material prévio.
- A entrada real `#ff0000` foi aplicada e persistida; captura do estado
  aplicado: `12-material-applied.png`, SHA-256
  `4C28B5A6D077B65B958BE6776E3365A981833E61CB88B146865FE957DD562C6E`.
- Após salvar e recarregar, a captura
  `14-material-reloaded.png` mostra `Albedo #ff0000` e o status localizado
  `Cenário recarregado`; SHA-256
  `EEAC6CED18C07D82ED1073A9087AF9862074500EA33BB16CD9E250F2862D2D2C`.
- O finding do binário anterior permanece preservado e não foi tratado como
  se tivesse passado.

O fluxo técnico passou; o registro permanece `IN_PROGRESS` até a suíte oficial
sem abort e a revisão/aceite humano formal.
