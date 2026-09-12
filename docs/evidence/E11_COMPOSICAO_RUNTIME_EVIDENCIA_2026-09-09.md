# E11 — composição e runtime completo

**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Fonte do binário:** `e404086`
**Build executada:** `release/e11-composition-20260909-r67`
**Status:** `E11-A/B/C/D CONCLUÍDOS_TECNICAMENTE; E11-E EM EXECUÇÃO`

## Contrato de aceite

E11 exige um percurso de produto no binário: iniciar sem projeto, criar cena,
usar recursos próprios, compor/editar, salvar, fechar, reabrir, recuperar
erro, exportar e consumir o resultado fora do editor. Teste de classe ou JSON
isolado não substitui a execução nativa. Os sublotes só recebem `PASS` quando
possuem fluxo observável, negativo, captura real, teste proporcional e
proveniência.

## Execução nativa já comprovada

O r67 repetiu o fluxo de composição no binário portátil com uma fixture
autocontida, incluindo asset hash-bound, tilemap, colliders, NavMesh, entidades,
prefab, FX, parallax e vetor. O processo real:

- abriu o projeto e o Editor de Cenário por entrada de captura do próprio
  binário;
- exportou `composition-e11-r9`, salvou, fechou/reabriu o editor e capturou
  cada transição;
- corrompeu somente o documento ativo após preservar um sidecar válido,
  recarregou, recuperou o último estado válido, salvou e exportou
  `composition-e11-r10`;
- restaurou o hash válido do documento (`7DE0CACFFDBBA42B11B1EB427ADB3E5E6029E8FA1FF7ACC3BA856CFE3005C4A9`)
  após a recuperação. A captura pós-recovery mudou para
  `14FD2923A3BCC2FF8EEF0549EF6F482F6A03CEBDE0674434282B82CB35A51E31`.

O manifesto dessa execução é
`artifacts/e11-native-composition-r67-r34-20260909/composition-recovery-manifest.json`.
O sidecar válido foi semeado a partir da fixture validada antes da corrupção;
isso é uma pré-condição explícita do teste de recovery, não uma afirmação de
que a captura automatizada criou o sidecar sozinha.

O binário r55 foi iniciado sem projeto e executou o fluxo de cenário
independente com capturas reais feitas pela janela do processo:

- abriu `Cenário Independente — Untitled Scene`;
- criou retângulo, elipse e polígono, totalizando 3 objetos;
- aplicou transformação, duplicação e remoção;
- entrou em edição de pontos, exibiu prévia inválida, cancelou com Escape e
  finalizou nova edição;
- salvou `e02-b-flow.ndtscene`, fechou/reabriu e preservou os 3 objetos;
- a captura após reabrir tem o mesmo SHA da captura após salvar:
  `34AC0707987AF593C78672F1E39E3175A90C225E27E904E6581C7C4A888B4F3F`.

O pacote completo e os hashes estão em
`docs/evidence/E11_COMPOSICAO_RUNTIME_MANIFESTO_2026-09-09.json` e
`artifacts/e11-product-flow-r55-20260909/`. As telas `03-independent-scene-primitives.png`
e `10-independent-scene-after-reopen.png` foram inspecionadas como capturas
reais do binário; a revisão humana formal continua reservada para o final.

## Regressão funcional

Com o Python canônico, o lote focado executou `149 passed` cobrindo comportamento
de usuário, tilemap, colisão, NavMesh, entidades, FX, paralaxe, persistência,
adapters e vetor. O teste focado do contrato independente e dos fluxos de
usuário executou `32 passed`. A suíte oficial da mesma fronteira havia
executado `2098 passed, 2 skipped, 1 warning`; os skips continuam restritos a
symlink e não foram convertidos em aprovação.

## Consumo runtime fora do editor

O pacote r64/r8 usado na auditoria de engine foi consumido com sucesso em
Godot `4.7.stable` e Unity `6000.5.7f1`, incluindo a leitura do asset real
`assets/scene/hero.png`: cada engine materializou 4 células, 2 colliders e 1
região de navegação. A evidência mais recente está em
`artifacts/e11-engine-composition-r64-r17-both-20260909/e11-engine-report.json`;
o harness exige agora a decodificação/importação do asset hash-bound.

O fechamento de adapters foi repetido em worktree limpo, com projetos reais
gerados para Godot `4.7.stable` e Unity `6000.5.7f1`. O relatório
`artifacts/e11-runtime-adapters-clean-20260909/stage8-report.json` tem SHA-256
`C0D23E82D0A5F41453657CE5312A6C012DF5B297293F272C29C0AACACBEF1965` e registra
`status=PASS`, `functional_status=PASS`, `godot=PASS`, `unity=PASS`, dois
layers e três fixed ticks. Os seis sidecars de lighting, particles,
post-processing, shaders, streaming e triggers foram validados com o mesmo
bundle; a matriz mantém `degraded` onde o destino consome metadata/sidecar,
sem promover isso silenciosamente a execução nativa.

A primeira execução no worktree com evidências presentes foi preservada como
diagnóstico `FAIL` por `worktree_clean=false`; ela não foi usada como PASS. A
repetição limpa acima é a evidência oficial do sublote.

## Fila E11 e critérios ainda abertos

| Sublote | Estado | Próxima prova obrigatória |
|---|---|---|
| E11-A composição no binário | `CONCLUÍDO_TECNICAMENTE` | fixture composta, recursos E03–E10, export e captura r67 |
| E11-B persistência/recovery | `CONCLUÍDO_TECNICAMENTE` | save/close/reopen, corrupção, recovery, JSON válido e reexport |
| E11-C exportação/consumo final | `CONCLUÍDO_TECNICAMENTE` | pacote autocontido consumido por Godot e Unity com asset real |
| E11-D acessibilidade/usabilidade | `CONCLUÍDO_TECNICAMENTE` | toolbar responsiva, tradução PT e atalhos exclusivos sem colisão |
| E11-E fechamento técnico | `EM EXECUÇÃO` | suíte oficial, estática, manifesto final e promoção documentada |

Após as correções de persistência, a suíte oficial completa executou `2101 passed,
2 skipped, 1 warning` em 60,89 s; compileall e `git diff --check` também passaram.

E11 ainda não pode ser promovida formalmente porque E11-E exige a suíte oficial,
estática, manifesto final e regressão no SHA/build vigente. Nenhuma lacuna é
tratada como `PASS` por inferência; symlinks e revisão humana continuam
exclusivos da auditoria final.
