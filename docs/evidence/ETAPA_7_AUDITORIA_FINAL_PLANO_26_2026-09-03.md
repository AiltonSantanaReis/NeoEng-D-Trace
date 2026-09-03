# Auditoria final de encerramento do plano das 26 falhas legadas — 03/09/2026

**Status da auditoria:** `PASS`

**Decisão do plano:** `APROVADO / CONCLUÍDO NO ESCOPO COMPROVADO`

**Código candidato auditado:**
`bcaf5b079881800899d121b071108fe404fa48da`

**Branch documental:** `Ailton/legacy26-closure-audit`

## Objetivo e escopo

Esta é a candidata de reavaliação final dos 13 critérios da seção 9 do plano
`docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`, após o registro humano
de C12. O escopo inclui as 11 assinaturas divergentes, as 12 ausências
históricas, os contratos substitutos, o runner Windows, a prova de symlink no
VMware, a candidata de empacotamento e os gates de qualidade. Nenhum snapshot
legado foi alterado.

## Proveniência e revisão humana

- código auditado: `bcaf5b079881800899d121b071108fe404fa48da`;
- CI pós-merge: run `33800311976`, Linux `100797952263`, Windows
  `100797952611`;
- CI corrente: Linux `1919 passed`; Windows `189/189`, `1919` testes, zero
  falhas, erros ou skips;
- gate formal limpo: histórico `196/26/0/0`, retorno `1`, 11 divergências,
  12 ausências e 42 substitutos;
- VMware: Windows 11 com Developer Mode, dois testes de symlink aprovados sem
  skip, com escopo `PASS_SCOPED` para a reconstrução identificada;
- empacotamento: smoke `SUCCESS` em 11 checks na candidata ancestral
  `d6e02cd9ee3445a02ef21faefb4c05d17e0d0fad`; não é apresentado como novo
  build no SHA `bcaf5b0`;
- revisão humana C12: `docs/evidence/ETAPA_7_REVISAO_HUMANA_C12_2026-09-03.md`.

## Critérios reavaliados

| ID | Critério | Status nesta candidata | Evidência/limite |
|---|---|---|---|
| C01 | 26 casos com diagnóstico, decisão e substituto | `PASS` | Gate formal, catálogo corrente e 42 testes substitutos. |
| C02 | Caso #10 passando e sem regressão | `PASS` | Contrato `NO_CHANGE`, suíte substituta e gate formal com retorno `0`. |
| C03 | Snapshots históricos não alterados | `PASS` | Hashes preservados e baseline Git-blob. |
| C04 | Nenhum bypass por skip, xfail, filtro ou threshold | `PASS` | Glob oficial, `selection_filters=[]`, `189/189`, zero skips no CI; histórico intacto. |
| C05 | Fixtures reais, determinísticas e adequadas | `PASS` | Contratos substitutos reais e Stage 4B.5 determinístico; fixtures históricas não promovidas. |
| C06 | Suítes aplicáveis passam integralmente | `PASS` | CI Linux/Windows com `1919` testes aprovados e zero falhas, erros ou skips. |
| C07 | Falhas negativas preservam estado e histórico | `PASS` | Contratos negativos e Stage 4B.5 comprovaram preservação. |
| C08 | Reconciliação formal aceita e testada | `PASS` | Contrato atual aceito; reconciliação histórica permanece fail-closed. |
| C09 | Manifests não rastreados resolvidos/classificados | `PASS` | `63/63` classificados e integridade corrente aprovada. |
| C10 | Suíte, cobertura, estática, segurança, performance e baseline | `PASS` | Gates locais/remotos aprovados; timings são primeiro baseline reproduzível. |
| C11 | Evidências completas e íntegras | `PASS` | Comandos, entradas, hashes, resultados, limites e integridade registrados. |
| C12 | Revisão humana final dos seis pontos | `PASS` | Declaração humana explícita para o SHA auditado. |
| C13 | Autorização operacional somente após todos os critérios | `PASS` | C12 confirmado e todos os gates finais revalidados nesta candidata; autorização registrada pelo proprietário. |

## Gates obrigatórios desta candidata

A candidata passou baseline Git-blob (`3224` arquivos), integridade de
evidências (`133` manifestos), contratos documentais/auditoria (`70 passed`),
`git diff --cached --check`, suíte completa (`1934 passed, 2 skipped`),
cobertura total (`90,90%`), gate formal em worktree limpo (`ACCEPTED`),
Stage 4B.5 (`PASS`) e CI pós-merge `33800311976` em Linux e Windows. Os dois
skips locais da suíte completa são explícitos e decorrem do privilégio de
symlink (`WinError 1314`); VMware e o CI Windows comprovaram os contratos no
ambiente autorizado. O lock foi confirmado no CI remoto; localmente foram
executados os equivalentes no `.venv`, pois Poetry não está instalado nesta
árvore. Nenhum snapshot legado foi alterado e os artefatos untracked
preexistentes permaneceram fora da fronteira.

## Decisão final

C01–C13 estão `PASS` no SHA auditado. O plano está
`APROVADO / CONCLUÍDO NO ESCOPO COMPROVADO`, sem reescrever snapshots ou
promover a prova VMware e o build ancestral a evidência de outro SHA. Tag e
release permanecem sem aprovação.

## Rollback

O rollback documental é `git revert` do commit que contiver esta candidata,
seguido de baseline, integridade, testes e CI. Não usar `git reset --hard`,
`git checkout --` ou limpeza ampla.

**Decisão:** `PASS` — C01–C13 comprovados no escopo documentado; plano aprovado e concluído nesse escopo.
