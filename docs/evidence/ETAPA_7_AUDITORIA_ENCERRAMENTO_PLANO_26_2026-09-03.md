# Auditoria formal de encerramento do plano das 26 falhas legadas — 03/09/2026

**Status da auditoria:** `PENDING_EVIDENCE`

**Decisão do plano:** `IN_PROGRESS`

**Revisão candidata auditada:** `bcaf5b079881800899d121b071108fe404fa48da`

**Escopo:** reconciliação viva do plano `LEGACY-26-RECON`, incluindo as 11
assinaturas divergentes, as 12 ausências históricas, a prova de symlink no
VMware e o CI pós-merge da revisão corrente. Esta auditoria não altera código
de produto nem reescreve snapshots.

## Regras aplicadas

Antes deste registro foram relidos a governança de integridade e
antialucinação, a política de qualidade e evidências, a política de não
regressão, a ADR do runner Windows, este plano, o índice de evidências e os
validadores oficiais. Foram aplicadas especialmente as seguintes regras:

- estados controlados: `PASS`, `PENDING_EVIDENCE` e `BLOCKED`;
- nenhuma falha histórica pode ser removida, mascarada ou convertida em pass;
- snapshots históricos, baseline e lockfile devem permanecer preservados;
- documentos vivos precisam apontar para a revisão e a evidência corrente;
- uma etapa não pode ser declarada concluída enquanto houver prova pendente;
- rollback deve ser reversível por revert ou patch inverso documentado.

## Proveniência e evidência corrente

- PR documental: `#167`, merge commit
  `bcaf5b079881800899d121b071108fe404fa48da`;
- commit integrado anterior que contém a correção técnica:
  `8a97ae14e8f84eb86fcacfaefed61f014830fbf9`;
- CI pós-merge corrente: run `33800311976`, evento `push` em `main`;
- job Linux: `100797952263`, `SUCCESS`;
- job Windows: `100797952611`, `SUCCESS`;
- artefato Linux: ID `9910870622`, digest
  `sha256:b84cda3d9bf55ec42276d63a057587cc860474e12e7f7ca871099af950515c68`;
- artefato Windows: ID `9911162210`, digest
  `sha256:37cb1f01c71bb8f4d7fe952b2443c5837af9bfb145f151a30210fe61e8a5d4b3`;
- resumo Windows: `152965` bytes, SHA-256
  `b7d9e7c7e31e96572a7837c41152b53bfc61c188d6853769b14da58ed9a0c987`;
- gate formal: `10743` bytes, SHA-256
  `80b759495e6dd14b83a74d973619a6949e2642178ead918177e8a3a36f3e9225`;
- JUnit de sincronização Windows: `4218` bytes, SHA-256
  `e98437ead23dcee34ef7a406b127c845c7ae4d4b796723db85c5796e536e29b3`;
- cobertura Linux: `1157539` bytes, SHA-256
  `bc59df003e39704df32e858f51cddcbdf8729fe0fbfa5eea21d5c89bce8f667b`;
- cobertura Windows: `1184094` bytes, SHA-256
  `840cba1e0e4d93b4b99dc33d0c3a06d1fb4834a2669d9d95fe4b049f8e331708`;
- ambiente Linux: `1435` bytes, SHA-256
  `2e8d3739f31bb776f2488574c8812a0a7e4c82e599fcd9c9f903155f942cee23`;
- ambiente Windows: `1566` bytes, SHA-256
  `49cc98c6fb7ecd4b8edeb1ec8f9c2ce58e0e6d3840ec53a9616be2685504d156`.
- build portátil: candidata limpa ancestral `d6e02cd9ee3445a02ef21faefb4c05d17e0d0fad`,
  smoke `SUCCESS`/`11 checks`, ZIP de `124181819` bytes, SHA-256
  `1559638225fe9e664ba5ebbc5d023b2ec4565b9d8dfb268fae5207c05401e33e`;
  o run `33800311976` não executou novamente o script de empacotamento.

O pacote de referências corrente está em
`docs/evidence/artifacts/legacy-26-closure-audit-2026-09-03/`. Os artefatos
remotos permanecem referenciados por ID e digest; não são apresentados como
arquivos locais quando não estão versionados.

## Critérios formais da seção 9

`PENDING_EVIDENCE` é o estado controlado usado aqui para o `PENDING` solicitado
na revisão operacional. O status é por critério e sempre se refere ao mesmo
SHA auditado.

| ID | Critério | Status | Evidência e limite |
|---|---|---|---|
| C01 | 26 casos com diagnóstico, decisão e substituto | `PASS` | `formal-gate.json` aceita o contrato atual; o catálogo corrente preserva as 11 assinaturas, 12 ausências e 42 testes substitutos. |
| C02 | Caso #10 passando e documentado como não regressão | `PASS` | O caso permanece no contrato corrente como `NO_CHANGE`; a suíte substituta e o gate formal retornaram código `0`. |
| C03 | Snapshots históricos não alterados | `PASS` | `quality/legacy_tests/manifest.json` SHA `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` e `reconciliation.json` SHA `34a186435d35936fc340ed2935bb6cb69756e13323f5c89fb82f9a632c733587`; baseline Git-blob passou. |
| C04 | Nenhum bypass por skip, xfail, filtro ou threshold | `PASS` | Runner Windows usou glob oficial, `selection_filters=[]`, `189/189`, `0` skips; histórico bruto preservou `196/26/0/0`, retorno `1`, sem reclassificação. |
| C05 | Fixtures reais, determinísticas e adequadas | `PASS` | Os contratos substitutos correntes usam objetos reais quando exigidos e passaram; Stage 4B.5 comprovou determinismo. Limite: fixtures históricas não são promovidas a prova do contrato atual. |
| C06 | Suítes unitária, integração, Qt, exportação, round-trip e assíncrona aplicáveis | `PASS` | CI corrente: Linux `1919 passed`; Windows `1919` testes, `0` falhas, `0` erros, `0` skips, `189/189` shards. |
| C07 | Falhas negativas preservam estado e não criam histórico parcial | `PASS` | Testes negativos do contrato corrente e Stage 4B.5 registraram preservação da entrada; o pacote não altera snapshots em caso de falha. |
| C08 | Reconciliação formal aceita e testada | `PASS` | `formal-gate.json`: `accepted=true` para o contrato atual, `tested_commit=bcaf5b0`; a reconciliação histórica continua `accepted=false` por desenho fail-closed. |
| C09 | Manifests não rastreados resolvidos/classificados | `PASS` | A resolução formal abrangeu `63/63` manifests, com owner, origem limitada ao provado, escopo, referências e tratamento preservador; integridade corrente validou `131` manifests. |
| C10 | Suíte, cobertura, estática, segurança, performance e baseline | `PASS` | CI corrente validou baseline `3216` arquivos, integridade de `131` manifests, estática, segurança, cobertura e Stage 4B.5; Windows aceitou `1919` testes. Limite: timings Stage 4B.5 são o primeiro baseline reproduzível dessa revisão. |
| C11 | Evidências com comandos, entradas, hashes, resultados, limites e decisão, com integridade | `PASS` | Este relatório referencia run, jobs, IDs, digests, hashes de arquivos, comandos e limitações; o CI corrente passou `evidence_integrity.py --require-tracked --git-blob`. |
| C12 | Revisão final confirma funcionalidade, dados, formatos, mensagens, compatibilidade e rollback | `PENDING_EVIDENCE` | O GitHub informa `reviews=[]` nas PRs #166 e #167. O aceite conversacional anterior autorizou a integração documental, mas não constitui, sem escopo explícito, a revisão final desta matriz integral. Falta registrar a revisão humana final deste candidato. |
| C13 | Autorização operacional somente após todos os critérios | `BLOCKED` | C12 ainda está pendente; portanto não é possível conceder nova autorização baseada nesta auditoria. Os merges anteriores permanecem como histórico de transição e não são usados para fechar este critério retroativamente. |

## Reconciliação documental

O plano vivo deve refletir que B-04 foi resolvido no escopo comprovado pelo
VMware e pelo CI pós-merge. O bloqueio atual não é mais a capacidade de symlink
nem a confirmação do runner; é a prova de revisão final C12. As formulações
anteriores que diziam “integração pendente” permanecem apenas como histórico
datado e devem apontar para esta auditoria.

Nenhum snapshot legado, manifesto preexistente, baseline ou arquivo de usuário
foi alterado. O workspace contém artefatos não rastreados preexistentes; eles
continuam fora da fronteira desta alteração e não foram limpos, movidos ou
adicionados automaticamente.

## Decisão operacional

Como C12 está `PENDING_EVIDENCE` e C13 está `BLOCKED`, a condição “todos os
critérios passam” não foi satisfeita. O status correto permanece
`IN_PROGRESS`; não é correto atualizar o plano para `APROVADO / CONCLUÍDO`, nem
gerar commit, push, merge, tag ou release nesta rodada. A próxima ação segura é
registrar uma revisão humana final, com escopo explícito sobre funcionalidade,
dados, formatos, mensagens, compatibilidade e rollback, no mesmo SHA; só então
os gates documentais poderão ser reavaliados.

A validação de empacotamento foi preservada como prova do ancestral `d6e02cd`;
ela não é apresentada como execução do build no SHA `bcaf5b0`.

## Rollback

Como esta auditoria não altera código e ainda não foi integrada, o rollback
operacional é simplesmente descartar a alteração documental local após revisão.
Se posteriormente integrada, o rollback será `git revert` do commit da
auditoria, seguido de baseline, integridade e CI novamente.

**Decisão:** `PENDING_EVIDENCE` — plano global não concluído.
