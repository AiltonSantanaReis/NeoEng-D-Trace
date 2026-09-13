# Registro de evidência pós-E13 — fluxo nativo de materiais

**ID:** `CHG-POST-E13-MATERIAL-BINARY-AUDIT-20260912`

**Estado:** `PASS_TECNICO / UX_REFINEMENT_OPEN`

**Data:** 2026-09-12

**Commit auditado:** `e2aa6367f09ba83a113c4ffa18153eefb27a891c`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Escopo

Requalificar o fluxo de material no binário pós-E13 com objeto real: seleção
no viewport, abertura do inspetor contextual, edição do albedo, aplicação,
salvamento e recarregamento. A captura anterior permanece preservada em
`artifacts/audit-post-e13-binary-material-20260912-r1/` e não é sobrescrita.

## Ajuste controlado no teste

O harness `scripts/capture_e03_asset_library_binary.ps1` tinha um clique em
uma área vazia entre os objetos (`1760,860`), portanto a captura antiga não
selecionava o objeto. O alvo foi corrigido para o centro do objeto visível
(`1300,780`) com comentário sobre a superfície nativa DPI-aware. Nenhum código
de produto, contrato de cena ou dado do usuário foi alterado.

## Evidência nativa real

Executável auditado:

- `build/post-e13-final-build-20260912/release/post-e13-final-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- versão de arquivo/produto `0.3.0`, idioma `Português (Brasil)`;
- SHA-256 `0A7E2BFF66F91B365D3D415B732A5C8C33265880E7678533F50E99F5A11F6229`.

Pacote requalificado: `artifacts/audit-post-e13-binary-material-20260912-r2/`.

| Passo | Evidência | SHA-256 | Observação |
|---|---|---|---|
| seleção real no viewport | `10-material-selection.png` | `35E54D6ED2201B723C1A772466008D64B539071525BAA8202F5FE90B0E879D76` | `pivot-object` selecionado e campos de transformação disponíveis |
| inspetor Material contextual | `11-material-authoring-selected.png` | `B5FBA528CDC7B4C6C228F45FCB5814DB352B4D4B62A5A8C8DCE658FD1C093894` | campos habilitados, albedo inicial `#ffffff` |
| edição real | `11-material-albedo-edited.png` | `4936D93F52C32D094C54942C52CC1E84D5A3747495413AEB99F84E9BF96C3BC3` | albedo alterado para `#ff0000` |
| aplicação | `12-material-applied.png` | `60B7EC57B2E9DF34183EEAA477EB5B8593E9C4341EB569E2FA33AB24146EE306` | status localizado `Material atualizado — alterações não salvas` |
| recarregamento | `14-material-reloaded.png` | `0C732A4BA54906769C7166BDDE14D4157A53B426D70151652C03912F091337EA` | albedo `#ff0000` preservado, status `Cenário recarregado` |

O arquivo persistido confirma o resultado:
`artifacts/audit-post-e13-binary-material-20260912-r2/fixture/compound-project.ndtscene.json`,
objeto `pivot-object`, `material.albedo = "#ff0000"`.

## Resultado e limites

- O fluxo técnico de edição e persistência de material passa no binário real.
- A localização observada nesta superfície está em PT-BR.
- O recarregamento limpa a seleção atual; por isso o inspector permanece sem
  objeto ativo e o botão `Aplicar Material` fica desabilitado. Isso não invalida
  a persistência, mas é uma oportunidade de UX: restaurar a seleção anterior
  quando seguro ou comunicar claramente `Material salvo` antes de limpar o
  contexto.
- O fluxo prova o contrato do editor e do arquivo `.ndtscene.json`; não prova
  equivalência de shader em Godot/Unity. Essa matriz permanece pendente.

## Classificação de governança

`PASS` técnico para seleção, edição, aplicação e persistência no editor nativo.
O finding anterior permanece histórico e o refinamento de restauração de
contexto após reload permanece `OPEN`; nenhuma regressão foi introduzida.
