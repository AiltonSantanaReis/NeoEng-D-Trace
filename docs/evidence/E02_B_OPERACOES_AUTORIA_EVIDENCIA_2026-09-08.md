# E02-B — evidência das operações de autoria

**Data de abertura:** 2026-09-08  
**Estado:** `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`
**Branch:** `Ailton/e02-primitives-20260908`  
**Escopo:** edição/seleção/transformação, remoção/duplicação, histórico e
save/reopen observável no fluxo do usuário.

## Dependência

E02-A possui checkpoint técnico registrado em
`docs/evidence/E02_A_CONTRATO_PRIMITIVAS_EVIDENCIA_2026-09-08.md`. O binário r4
e o preview renderizado foram preservados antes da abertura deste sub-lote.

## Metas executáveis

- ligar seleção da lista de objetos ao estado da sessão;
- tornar transformação e remoção/duplicação observáveis no canvas e na lista;
- validar Undo/Redo no fluxo real do binário;
- completar save/reopen com comparação dos objetos e da geometria;
- adicionar negativos de objeto bloqueado, ID inexistente e arquivo alterado;
- repetir suíte focada, suíte oficial, build oficial e captura real após cada
  correção reproduzível.

## Resultado técnico

Passaram os testes focados de modelo/UI, a suíte oficial completa
(`1988 passed, 2 skipped, 1 warning`), a build portátil r7 com smoke
`SUCCESS` em 11 checks e o fluxo real do binário:

- seleção de objeto e destaque no canvas;
- transformação por Objeto X=42;
- duplicação por Ctrl+D;
- remoção por Ctrl+Shift+Delete, sem conflito com campos numéricos;
- salvar por diálogo nativo PT-BR;
- reabrir pelo diálogo nativo PT-BR;
- comparação visual reaberta com 3 objetos, retângulo, elipse e polígono.

Build: source commit `5e1f886ebb7933a5b15a8b5786975941f60c03a6`; binário
SHA-256 `8366905A82BB3756ACBFEB89F7FC217F0233437C7939EBAD44A9104FB50F4E3C`;
ZIP portátil SHA-256 `42936A0CB10248CB06478651805A1078EB9FA3063C7155A2FE062CF4053F5932`.

Captura principal:
`artifacts/e02-primitives-20260908/captures-r7-save-reopen/10-independent-scene-after-reopen.png`,
SHA-256 `F0552D3D6AED055B17027CE49F081D150E04F909AFF80415E6D75C287B59878F`.
O arquivo salvo no mesmo fluxo tem SHA-256
`105108408839C41F8BCDB0980E663AB1239DC593392FC73445387A6F9F84DA6E`.

## Limite transferido para E02-C

E02-B não declara concluída a edição livre de pontos/curvas, estados de gesto
e negativos de cancelamento durante desenho. Esses critérios foram transferidos
para E02-C, que permanece `IN_PROGRESS`. Symlink e revisão humana continuam
reservados à auditoria final do Plano Mestre.
