# E11 — composição e runtime completo

**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Fonte do binário:** `2486cd1b7684b02f01aae483ca2440b5ab454004`  
**Build executada:** `release/e10-real-captures-20260909-r55`  
**Status:** `IN_PROGRESS`

## Contrato de aceite

E11 exige um percurso de produto no binário: iniciar sem projeto, criar cena,
usar recursos próprios, compor/editar, salvar, fechar, reabrir, recuperar
erro, exportar e consumir o resultado fora do editor. Teste de classe ou JSON
isolado não substitui a execução nativa. Os sublotes só recebem `PASS` quando
possuem fluxo observável, negativo, captura real, teste proporcional e
proveniência.

## Execução nativa já comprovada

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
| E11-A composição no binário | `PASS_LOCAL` | compor recursos de E03–E09 em uma única cena e captura |
| E11-B persistência/recovery | `PASS_LOCAL` | erro recuperável e preservação da saída válida |
| E11-C exportação/consumo final | `IN_PROGRESS` | exportar a cena composta e executar no fluxo runtime Godot/Unity |
| E11-D acessibilidade/usabilidade | `IN_PROGRESS` | roteiro integral, mensagens, foco, cancelamento e latência observável |
| E11-E fechamento técnico | `PLANNED` | suíte completa, build final, manifesto e decisão de promoção |

E11 ainda não pode ser promovida: a execução independente comprovou a
composição/persistência de E01/E02, mas o roteiro integral que combina
asset-library, tilemap, colisão, NavMesh, entidades/prefab, FX e vetor no mesmo
consumidor ainda precisa de uma captura/execução única e de seus negativos.
Nenhuma lacuna é tratada como `PASS` por inferência.
