# Plano integral de engenharia — correção e reconciliação das 26 falhas legadas

**Projeto:** NeoEng-D-Trace
**Etapa:** Reconciliação técnica pós-auditoria — 26 falhas legadas restantes
**Identificador operacional:** `P2D-COMP-01/LEGACY-26-RECON`
**Data de abertura:** 01/09/2026 (America/Sao_Paulo)
**Status:** `EM EXECUÇÃO — FASE 7 EXECUTADA; B-04 PARCIAL; INTEGRAÇÃO BLOQUEADA`
**Última atualização:** 02/09/2026 — após validação autorizada de symlink no Windows 11/VMware
**HEAD de execução:** `eaa28b9a75194d25741323b4b72911426a740349`
**Aceite do proprietário:** recebido nesta conversa em 01/09/2026, incluindo as recomendações para os 26 casos
**Branch de trabalho:** `fix/legacy-27-functional-regressions`
**Base de reprodução:** `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`
**Snapshot histórico de origem:** `cf749564ab5d961772d66dc363d0e990cebf8da3`
**Documento de diagnóstico:** `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`

Este documento é um plano vivo de execução. Ele registra as decisões e as
evidências produzidas até a revisão candidata atual, mas não declara aprovação
global, encerramento da etapa, commit, push ou merge. A etapa somente poderá ser
encerrada quando todos os critérios deste documento forem comprovados em um
pacote integral e reproduzível.

## 0. Registro vivo de execução — atualização de 01/09/2026

Esta atualização substitui o estado de abertura que informava “implementação não
iniciada”. O plano passa a refletir o estado real e verificável da execução no
HEAD registrado acima. A atualização não altera snapshots, manifests históricos,
reconciliações históricas ou qualquer outro artefato que represente o comportamento
legado. Também não transforma resultados parciais em aprovação.

### 0.1 Regras e governança consultadas antes desta atualização

A consulta obrigatória foi realizada antes de registrar o estado e antes de tomar
a decisão de manter o bloqueio. Foram consultados, em modo de leitura, os
seguintes controles e fontes:

- `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`: definições de `APROVADO`,
  `REPROVADO`, `BLOQUEADO`, `NÃO TESTADO` e `PARCIAL`; proibição de omitir
  falhas, usar skips/xfail ou substituir objetos reais por mocks quando o
  comportamento real é parte do contrato; requisitos de evidência, integridade,
  rastreabilidade, privacidade, rollback e critérios de merge.
- Este plano, `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`: fronteira
  dos 26 casos, preservação do caso #10, sequência de fases, reconciliação
  formal, auditoria de manifests, gates finais e proibição de integração antes
  do fechamento comprovado.
- `docs/evidence/README.md`: organização e exigências do pacote de evidências,
  referências rastreadas e relação entre manifest, conteúdo e hashes.
- `tools/run_legacy_tests.py`: seleção e execução do runner histórico integral,
  sem alterar a fonte histórica nem introduzir exceção de execução.
- `quality/legacy_tests/manifest.json` e
  `quality/legacy_tests/reconciliation.json`: lidos como registros históricos
  somente; seus bytes, hashes e significado não foram modificados.
- `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`, os registros de decisão
  de `P2D-05/O-2` e os relatórios das Fases 1–5: usados para conferir a
  correspondência entre o diagnóstico, os contratos substitutos e a evidência
  atual.

A regra aplicada nesta atualização é: divergência de assinatura não explicada,
falha ausente sem reconciliação formal, manifest sem classificação final ou gate
não executado mantém a etapa bloqueada. Nesta revisão, os 27 casos e os 63
manifests têm classificação formal registrada; as limitações e o bloqueio
residual permanecem explícitos. Nenhuma divergência foi reescrita para produzir
`accepted=true`.

### 0.2 Identidade da revisão e fronteira operacional

- Branch: `fix/legacy-27-functional-regressions`.
- HEAD testado: `eaa28b9a75194d25741323b4b72911426a740349`.
- Snapshot histórico de origem: `cf749564ab5d961772d66dc363d0e990cebf8da3`.
- Base de reprodução/rollback registrada no plano:
  `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`.
- O estado de trabalho está sujo de forma conhecida: há alterações controladas
  desta execução no índice e artefatos não rastreados preexistentes. A fronteira
  staged foi revisada; nenhum arquivo de `quality/legacy_tests` está staged.
- As alterações controladas incluem implementação de timeout/cancelamento
  cooperativo, contratos substitutos reais, testes de integração Qt, relatórios
  das fases e o pacote formal da Fase 5. Os artefatos não rastreados anteriores
  permaneceram fora da fronteira de alteração; sua auditoria formal posterior
  registrou classificação, hashes e tratamento sem adicioná-los automaticamente.

### 0.3 Estado comprovado por fase

| Fase | Estado vivo | Comprovação e limite da decisão |
|---|---|---|
| Fase 0 — entrada e congelamento | `EXECUTADA — BLOQUEIO DE INTEGRAÇÃO MANTIDO` | Branch, HEAD, ambiente, hashes históricos, fronteira staged, rollback, inventário dos 63 manifests e reconciliação formal foram registrados. O gate de integração permanece bloqueado somente pelos itens residuais documentados em B-04. |
| Fase 1 — contratos substitutos e fixtures | `EXECUTADA — CONTRATOS PASSARAM` | Fixtures usam `Scene`, `CommandManager`, `CanvasView`, `QApplication`, `QImage` e `ndarray` reais quando aplicável; contratos nativos passaram sem skip/xfail. Isso comprova os substitutos, não a aceitação histórica. |
| Fase 2 — geometrias, bordas, exportação e viewport | `EXECUTADA — DECISÕES REGISTRADAS` | Casos #1, #2, #3, #4, #5, #23 e #24 foram exercitados com geometria válida/negativa, dtype, atlas, undo/redo, bordas e viewport conforme os contratos atuais. O adendo formal registra `NO_CHANGE` por caso, sem alterar o histórico. |
| Fase 3 — ferramentas síncronas e histórico | `EXECUTADA — DECISÕES REGISTRADAS` | Casos #6–#9, #11–#16, #25 e #26 foram cobertos com objetos reais, histórico, erro, seleção e undo/redo; o #10 permanece como não regressão. O #25 é `CORRIGIDO` somente no defeito cycle-safe; os demais têm decisão `NO_CHANGE`, sem converter divergência histórica em aprovação. |
| Fase 4 — Magnetic Lasso, cache e assincronia | `EXECUTADA — TESTADA E REPRODUZIDA` | Casos #17–#22 e #27 foram exercitados com imagem real, solver/cache/worker, sinais Qt, timeout, cancelamento e descarte de resposta tardia; os testes de timeout/stale-result/end-to-end passaram em duas repetições. |
| Fase 5 — reconciliação formal | `EXECUTADA — GATE FORMAL ACEITO; HISTÓRICO PRESERVADO` | O gate `formal_reconciliation.json` retornou `accepted=true` no escopo de equivalência do contrato atual; 27/27 decisões e 63/63 manifests resolvidos formalmente. O runner histórico exato permanece `accepted=false`, com 196 testes, 26 falhas, 11 assinaturas divergentes e 12 ausências, sem alteração de snapshots. |
| Fase 6 — pacote e integridade | `EXECUTADA — PACOTE FORMAL RASTREADO` | `evidence_integrity --require-tracked --git-blob` passou com 123 manifests; a resolução atual preserva bytes/hashes dos 63 fontes, registra owner/origem/escopo/referências/tratamento e declara as 706 referências históricas ausentes dos 2 releases. |
| Fase 7 — gates finais e integração | `EXECUTADA — INTEGRAÇÃO BLOQUEADA` | Reexecução final: suíte oficial `1925 passed, 2 skipped, 1 warning em 48.66s`; substitutos `42 passed em 2.71s`; runner histórico `196/26/0/0`; cobertura `92.65%` de linhas e `85.12%` de branches; estática, segurança, benchmarks O1/O2, determinismo, baseline `3179 files` e evidence integrity passaram. A validação autorizada na VM Windows 11/VMware executou os dois testes de symlink com `2 passed, 0 skipped`; permanecem a confirmação de CI/empacotamento e a repetição dos gates em pacote completo. |

Os estados acima distinguem execução de teste, integridade do pacote e aceite
formal. Nenhuma linha que diga `EXECUTADA` equivale a `APROVADO / CONCLUÍDO`.

### 0.4 Resultados brutos desta revisão

#### Runner histórico integral

Comando executado:

```text
.\.venv\Scripts\python.exe tools\run_legacy_tests.py --group all --timeout-seconds 120 --output <RUN_TMP>
```

Resultado bruto confirmado:

- seleção: 24 arquivos;
- total: 196 testes;
- falhas: 26;
- erros: 0;
- skips: 0;
- processo terminou com exit code 1 por causa das falhas;
- resumo bruto SHA-256: `75b9724a8c1782a8f0b8dd53c88f8bb4f2b51a2aa83156eb8e99aa1545744c5`;
- reconciliação produzida pelo runner: `failed`, `accepted=false`,
  `expected=27`, `matched=15`, `unexpected=11`, `missing=12`.

As 12 ausências não significam 12 novos testes aprovados. Elas representam
falhas esperadas que não apareceram com a assinatura histórica: 11 casos
reapareceram com assinatura diferente e o caso #10 não produziu falha. O caso
#25 pertence ao primeiro grupo e falhou no runner atual com a assinatura
`assert None is not None`, causada pelo caminho histórico com `Mock` incompatível.
A correção cycle-safe foi verificada separadamente e não foi tratada como passe
histórico.

#### Suítes substitutas nativas

Comando executado:

```text
.\.venv\Scripts\python.exe -m pytest -q tests\test_legacy_phase1_contracts.py tests\test_legacy_phase2_contracts.py tests\test_legacy_phase3_contracts.py tests\test_legacy_phase4_contracts.py --junitxml=<RUN_TMP>\native-substitutes.xml
```

Resultado válido confirmado após a execução inicial inválida ser descartada
como erro de invocação e não como resultado de teste:

- execução empacotada anterior: `42 passed in 2.86s`;
- rerun final desta revisão: `42 passed in 2.71s`;
- JUnit empacotado: `tests=42`, `failures=0`, `errors=0`, `skipped=0`;
- não foram adicionados skips, xfails, filtros de falha ou alteração de
  threshold para obter esse resultado;
- o pacote rastreado contém o log e o JUnit sanitizados em
  `docs/evidence/artifacts/legacy-26-phase5-20260901/`.

O registro preliminar da reconciliação, incluindo todos os IDs 1–27, permanece
preservado em `docs/evidence/artifacts/legacy-26-phase5-20260901/case_reconciliation.json`.
As decisões formais atuais estão no adendo
`docs/evidence/FASE5_RECONCILIACAO_FORMAL_2026-09-01.md` e no artefato
`docs/evidence/artifacts/legacy-26-formal-review-20260901/case_decisions.json`.
As funções de teste referenciadas existem e foram verificadas; o gate formal
atual está `accepted=true` no escopo de equivalência do contrato atual. A decisão
global de integração continua bloqueada porque a reconciliação histórica exata
preserva `accepted=false` por imutabilidade dos snapshots, e os bloqueadores
residuais de symlink/CI/empacotamento ainda não foram encerrados.

### 0.5 Proteção dos históricos

Os registros históricos permanecem byte a byte protegidos:

- `quality/legacy_tests/manifest.json` — SHA-256
  `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a`;
- `quality/legacy_tests/reconciliation.json` — SHA-256
  `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493`;
- a comparação de imutabilidade contra o anchor
  `3c287ac73925ef0ef33404da63de7401dee43913` terminou com exit code 0;
- `git diff --cached --name-only -- quality\legacy_tests` não retornou arquivo;
- não houve edição, normalização, regeneração, remoção ou substituição de
  snapshot para reduzir o número de falhas.

### 0.6 Integridade do pacote e auditoria do manifest não rastreado

Os seguintes controles foram executados e registrados:

- pacote preliminar da Fase 5: 52 arquivos; pacote do adendo formal: 4 arquivos,
  incluindo manifest, relatório, decisões e auditoria;
- `tools/evidence_integrity.py --require-tracked --git-blob`:
  `Evidence integrity passed: 123 manifests validated`;
- `tools/baseline_integrity.py --verify --git-blob`:
  `Baseline verified: 3179 files`;
- `git diff --check --cached`: exit code 0;
- verificação independente: 27 IDs únicos, decisões `1 CORRIGIDO / 26 NO_CHANGE`,
  resultados históricos `196/26/0/0`, substitutos `42/0/0/0`, referências de
  funções existentes, hashes dos 63 manifests estáveis e pacote sem os padrões
  de privacidade proibidos.
- reexecução final da suíte oficial: `1925 passed, 2 skipped, 1 warning em
  48.66s`; a auditoria específica confirmou que os dois skips são apenas os
  testes de symlink com `WinError 1314` e não foram adicionados nesta revisão;
- cobertura final: `92.65%` de linhas e `85.12%` de branches; a política de
  cobertura passou;
- benchmarks P2D-05 O1 e O2 retornaram `status: PASS`; as duas repetições dos
  testes de timeout, resposta tardia e end-to-end retornaram `3 passed` cada.

A auditoria individual está registrada em
`docs/evidence/artifacts/legacy-26-formal-review-20260901/untracked_manifest_audit.json`
e cobriu 63/63 arquivos `manifest.json` preexistentes e não rastreados, das
famílias F02, limpeza legada, P2D-05 e snapshots de stages. Todos os 63 são
JSON válidos; 9 têm CRLF, 54 têm LF e há 7 grupos de SHA-256 duplicados.
A consulta da data corrente não encontrou manifest com `20260901`. Os bytes e
hashes foram revalidados após o registro; nenhum arquivo foi apagado, movido,
sobrescrito ou adicionado ao índice. O resolution manifest resolve formalmente
owner operacional sob a autorização vigente, origem limitada ao que é provado,
escopo, referências e tratamento preservador para os 63 itens. A autoria
histórica e o evento de criação continuam não provados onde a evidência não os
suporta; as 706 referências históricas ausentes permanecem declaradas. O
conjunto não é mais um bloqueador de classificação, mas suas limitações não
podem ser convertidas em integridade histórica retroativa.

### 0.7 Registro formal dos bloqueadores atuais

| ID | Bloqueador | Evidência objetiva | Consequência obrigatória |
|---|---|---|---|
| B-01 | Reconciliação histórica exata preservada, equivalência formal aceita | `formal_reconciliation.json` registra `accepted=true` no escopo atual; `historical_runner.accepted=false` permanece por imutabilidade dos snapshots. | Resolvido para o contrato atual; não converter o runner histórico em pass nem alterar a origem. |
| B-02 | Divergências históricas reconciliadas formalmente | As 11 assinaturas divergentes e as 12 ausências permanecem enumeradas, incluindo #10 e #25; a decisão individual e a causa/substituto estão registradas sem remapeamento silencioso. | Resolvido como reconciliação formal atual; a divergência histórica continua visível. |
| B-03 | Manifests preexistentes classificados formalmente | `manifest_resolution.json` resolve 63/63 com proprietário operacional autorizado, origem limitada ao que é provado, escopo fora do pacote atual, referências e tratamento preservador; 2 releases declaram 353 referências ausentes cada. | Resolvido formalmente sem alterar, mover, excluir ou rastrear automaticamente os fontes. |
| B-04 | Confirmação final de CI/empacotamento; capacidade residual de symlink resolvida na prova autorizada | A validação autorizada na VM Windows 11/VMware registrou `DEVELOPER_MODE_FLAG=1`, executou `poetry run pytest \"tests\test_integration_sync.py\" -k symlink -q -rs` e obteve `2 passed, 0 skipped`; a evidência está em `docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`. | Manter integração bloqueada; repetir os gates completos em pacote integral e reproduzível e confirmar CI/empacotamento. |
| B-05 | Divergência documental corrigida | O plano vivo e o adendo formal agora refletem a resolução 63/63, o gate `accepted=true` atual e os bloqueios residuais reais. | Resolvido; históricos e snapshots permanecem intactos. |

### 0.8 Decisão vigente e operações proibidas

A decisão vigente é `BLOQUEADA / DECISÕES INDIVIDUAIS REGISTRADAS / ACEITE
FORMAL ATUAL ACEITO / INTEGRAÇÃO PENDENTE`. Há evidência rastreada de execução,
decisões por caso e integridade de pacote. O gate formal atual é `accepted=true`
no escopo declarado; isso não converte o runner histórico em pass nem equivale a
aceite histórico global. A capacidade de symlink foi comprovada na VM autorizada,
mas CI e empacotamento ainda não foram confirmados. O projeto ainda não pode
declarar `APROVADO`, `CONCLUÍDO`, pronto para integração ou equivalência histórica
final.

Enquanto B-04 existir, ficam proibidas:

- alterar `quality/legacy_tests/manifest.json`,
  `quality/legacy_tests/reconciliation.json` ou snapshots para fazer o runner
  passar;
- adicionar skip, xfail, filtro, tolerância ou threshold cosmético;
- substituir objetos reais por `Mock`, placeholder ou fixture parcial nos
  contratos que exigem Scene/manager/Qt/imagem reais;
- chamar o caso #10 de resolvido apagando-o do inventário, ou chamar o #25 de
  passado por não reproduzir a mesma exceção;
- alterar, limpar, excluir, mover ou rastrear automaticamente os 63 manifests;
- executar merge, tag ou release;
- executar commit ou push, exceto o checkpoint técnico de candidata
  formalizado na seção 10.1. Esse checkpoint não representa aprovação,
  integração, encerramento ou autorização de release.

### 0.9 Atualização de 02/09/2026 — prova autorizada de symlink no VMware

O bloqueio de capacidade de symlink foi testado no ambiente solicitado: Windows
11 em VMware com Developer Mode observado como `1`. A candidata foi reconstruída
fora do repositório Git a partir de `neoeng-base-eaa.zip` e
`neoeng-candidate.patch`; essa limitação de proveniência foi registrada, sem
criar um repositório Git artificial.

- ZIP-base: `64.977.183` bytes; SHA-256
  `5668b579260ff0e098e407f9c5a588d2113cfd5cd37f6cf7a763d7a331545e8e`.
- Patch candidato: `621.637` bytes; SHA-256
  `ed477bb5c6d204005fa684b866886456bce9d5010d25cc47fb49eebde4f5950d`.
- Ambiente: Python `3.11.0`, Poetry `2.4.1`, pytest `9.1.1`.
- Comando focal: `poetry run pytest \"tests\test_integration_sync.py\" -k symlink -q -rs`.
- Resultado: `31` coletados, `2` selecionados, `29` deselecionados,
  `2 passed`, `0 skipped`, código de saída `0`.
- Evidência: `docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md` e
  `docs/evidence/artifacts/symlink-vmware-2026-09-02/`.

Esta prova resolve somente a capacidade real de symlink e os dois contratos
focais. O ZIP continua inadequado para o gate completo por não conter `.git` e
por não conter o manifesto F02 exigido; CI e empacotamento continuam pendentes.

A documentação continuará aceitando somente resultados que possam ser repetidos
a partir do comando, entrada, hash, ambiente e artefatos registrados.

## 1. Regra de governança antes de qualquer decisão

Antes de decidir sobre código, fixture, teste, harness, reconciliação,
evidência, commit ou merge, a equipe deverá consultar, na versão efetivamente
presente no branch, pelo menos:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `tools/run_legacy_tests.py`;
5. `quality/legacy_tests/manifest.json`;
6. `quality/legacy_tests/reconciliation.json`;
7. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
8. as decisões e evidências vigentes de `P2D-05/O-2` quando uma alteração
   puder afetar cache, incremental, frame, viewport, histórico ou desempenho.

Cada decisão deverá registrar no relatório:

- regra consultada e versão/commit observado;
- fato verificável que motivou a decisão;
- alternativas consideradas;
- impacto sobre funcionalidade, dados, compatibilidade, desempenho e segurança;
- teste ou evidência que comprovará a decisão;
- condição de rollback;
- responsável pela revisão, quando houver revisão formal.

### 1.1 Regras absolutas desta etapa

- `quality/legacy_tests/manifest.json` e os arquivos históricos referenciados
  são snapshots imutáveis. Não serão editados, regenerados ou removidos para
  reduzir falhas.
- `quality/legacy_tests/reconciliation.json` não será alterado para obter
  `PASS`. Qualquer mudança será uma decisão formal de harness, acompanhada de
  testes substitutos reais e revisão explícita.
- Nenhum `skip`, `xfail`, filtro, threshold, tolerância, timeout ou critério de
  aceite será alterado para transformar uma falha em aprovação.
- Nenhuma funcionalidade, caminho de rollback, validação, mensagem de erro,
  histórico, exportação ou formato será removido ou ignorado para fazer um
  teste passar.
- Mock somente poderá representar uma fronteira estreita e explicitamente
  isolada. Mock genérico não será aceito como substituto de `Scene`,
  `CommandManager`, `CanvasView`, `QImage`, exportador ou pipeline assíncrono
  quando esse comportamento real for o objeto do teste.
- Exceções deverão permanecer observáveis no teste e no log. O estado anterior
  deverá ser preservado quando a operação não puder ser confirmada.
- Não será aceita implementação parcial, suíte parcial ou pacote de evidências
  parcial como resultado final. Lotes internos poderão existir apenas como
  mecanismo de segurança de desenvolvimento; nenhum lote poderá ser declarado
  concluído isoladamente nem poderá ser merged antes do fechamento integral.
- Qualquer resultado não executado será classificado como `NÃO TESTADO`;
  impedimento identificado como `BLOQUEADO`; cobertura incompleta como
  `PARCIAL`. Nenhuma dessas classificações equivale a `APROVADO`.
- Diante de perda de dados, regressão, divergência não explicada,
  não determinismo, falha de build, queda de cobertura, risco de segurança ou
  alteração fora do escopo, o fluxo será interrompido e a etapa será registrada
  como bloqueada até haver causa e decisão formal.

## 2. Estado de entrada e fronteira

### 2.1 Fatos já comprovados

Os itens abaixo preservam os fatos observados na abertura desta etapa. Eles são
evidência histórica de entrada, não uma substituição do estado vigente registrado na seção 0.

- A reprodução histórica inicial registrou `196 testes, 27 falhas, 0 erros e
  0 skips`.
- A execução histórica integral no HEAD atual registrou `196 testes, 26 falhas,
  0 erros e 0 skips`, com exit code 1 por causa das falhas.
- O caso histórico `polygonal_lasso.test_commit_selection_converts_to_integers`
  não produziu falha nesta execução e permanece protegido como não regressão;
  ele não foi apagado do inventário nem usado para alterar o snapshot.
- A reconciliação bruta do runner histórico nesta entrada está `failed`: `15/27`
  assinaturas coincidentes, `11` assinaturas inesperadas/alteradas e `12` falhas esperadas ausentes.
- Os 11 casos com assinatura alterada não foram considerados passados; o caso
  #25 falhou no runner atual com `assert None is not None` devido à fixture `Mock`
  incompatível, enquanto a correção cycle-safe passou no teste nativo real. O caso
  #10 não produziu falha, mas continua exigindo registro explícito.
- A suíte substituta nativa da entrada executou 42 testes e registrou `42 passed`, sem
  falhas, erros ou skips. Esse resultado comprovava os contratos atuais naquela
  fronteira e não convertia automaticamente a reconciliação histórica em `accepted=true`.
- `tools/evidence_integrity.py --require-tracked --git-blob`,
  `tools/baseline_integrity.py --verify --git-blob` e `git diff --check --cached`
  passaram na fronteira de entrada; os gates finais de cobertura, estática, segurança,
  performance, determinismo e integração ainda não haviam sido aceitos em conjunto naquela etapa.
- A auditoria da árvore identificou 63 arquivos `manifest.json` preexistentes
  e não rastreados. Não há manifest com data corrente `20260901` nesse conjunto.
  Na entrada, eles não foram removidos ou incluídos automaticamente; propriedade, origem,
  escopo, integridade, referências e tratamento ainda aguardavam a resolução
  formal que foi registrada posteriormente no pacote da Fase 5.
- O relatório preliminar e o artefato de entrada permanecem preservados como
  registro da rodada:
  `docs/evidence/FASE5_RECONCILIACAO_26_CASOS_2026-09-01.md` e
  `docs/evidence/artifacts/legacy-26-phase5-20260901/case_reconciliation.json`.
- A decisão formal atual está no adendo
  `docs/evidence/FASE5_RECONCILIACAO_FORMAL_2026-09-01.md`, com pacote
  `docs/evidence/artifacts/legacy-26-formal-review-20260901/`.

### 2.2 Escopo incluído

Estão incluídos exatamente os 26 casos históricos ainda falhos: `#1–#9`,
`#11–#27`. O caso `#10` permanece no inventário como não regressão protegida;
a ausência de falha nesta execução não encerra sua reconciliação formal.

Estão incluídos:

- criação de fixtures reais e determinísticas;
- testes substitutos equivalentes ou superiores;
- correções de produto somente quando houver defeito de produto demonstrado;
- correções do harness quando a divergência for de fixture, contrato ou
  integração histórica;
- testes de erro, preservação de estado, undo/redo e rollback;
- equivalência geométrica, visual, de exportação, cache e comportamento;
- execução Windows/Qt, quando aplicável;
- reconciliação formal, integridade de evidências e gates finais.

### 2.3 Fora do escopo sem decisão nova

- alterar o contrato aprovado de `P2D-05/O-2` por conveniência;
- adicionar culling, spatial index, paralelismo ou nova otimização sem evidência
  e aprovação próprias;
- aceitar geometrias inválidas, imagens falsas ou objetos parciais para reduzir
  falhas;
- remover APIs, funcionalidades, formatos ou caminhos antigos;
- corrigir unrelated changes do workspace;
- modificar artefatos históricos só porque estão fora do estado atual;
- executar merge, tag, release ou avanço de etapa antes dos gates;
- executar commit ou push somente conforme a exceção controlada da seção
  10.1, sem declarar conclusão ou integração.

## 3. Matriz integral dos 26 casos

Cada linha abaixo terá uma ficha de execução no relatório final. A coluna
“aceite específico” é obrigatória: passar somente no teste unitário isolado não
encerra uma linha que exige integração, dados, Qt ou exportação.

| Caso | Diagnóstico de entrada | Trabalho obrigatório | Aceite específico e evidência |
|---:|---|---|---|
| 1 | Fixture de `convex_decompose_l_shape` possui auto sobreposição; a geometria não é um L simples válido. | Criar fixture L simples, não auto-intersectante, com orientação controlada; manter teste negativo para a fixture inválida. | Rejeição determinística da entrada inválida sem mutação; decomposição válida preserva área e produz peças convexas. Registrar coordenadas, hash da entrada, área antes/depois e traceback. |
| 2 | `ear_clipping_concave_l_shape` usa a mesma geometria inválida; aceitar triângulos incorretos seria regressão. | Usar polígono côncavo válido em ambas as orientações e preservar o validador estrito. | Triangulação termina, cobre exatamente a área, não cria triângulos fora do polígono e é independente da orientação. Manter a rejeição explícita do fixture histórico. |
| 3 | O teste histórico exige `float64`, enquanto o contrato atual operacional é `float32` sem clipping. | Atualizar somente o teste substituto para o contrato aprovado; não alterar dtype nem inserir conversão cosmética no produto. | `ndarray` com dtype, shape e finitude corretos; valores preservados dentro da tolerância do contrato e nenhum clipping silencioso. Medir custo de conversão e registrar ausência de regressão. |
| 4 | O teste histórico espera dois atlas porque rotação ainda não existia; o exportador atual acomoda os sprites em um atlas. | Usar sprites reais com e sem rotação e validar packing físico, rotação, UV e metadados. | Um atlas quando permitido pelo packing, dimensões físicas corretas, metadado de rotação coerente e round-trip de importação/exportação. Comparar bytes/estrutura conforme o contrato, não a contagem histórica obsoleta. |
| 5 | `handle_move_undo_redo` cria polígono colinear de três pontos; `Scene` deve rejeitá-lo. | Criar caso positivo com geometria Bézier não colinear e caso negativo colinear; exercitar criação, movimento, undo e redo no manager real. | Entrada inválida falha antes da mutação/histórico; entrada válida produz exatamente uma operação desfazível e refazível, preservando parâmetros e seleção. |
| 6 | Lasso usa Canvas/Scene `Mock` e manager sem `CommandResult`; o commit não pode ser confirmado. | Fixture com `QApplication`, `CanvasView`, `Scene` e `CommandManager` reais; caminho válido e caminho de falha controlada. | Release confirma seleção somente após resultado real; erro preserva seleção/nós e registra diagnóstico. Capturar estado antes/depois e histórico. |
| 7 | Pen usa modelo `Mock` sem manager válido; não há criação confirmável. | Fixture real de Scene/manager, controles válidos, conversão canônica e comando real. | Commit retorna resultado real, objeto persistido é válido, seleção e parâmetros são preservados, undo/redo são equivalentes. O teste negativo deve provar ausência de mutação parcial. |
| 8 | Duplo clique da pen depende do mesmo manager inválido; limpar nós ocultaria a falha. | Usar eventos Qt reais e curva fechável válida; testar também finalização inválida. | Duplo clique válido consolida uma entrada; inválido preserva nós e último estado válido, mostra/loga erro e não cria histórico parcial. |
| 9 | Duplo clique do laço poligonal usa Mock de Qt/Scene incompatível com o caminho atual. | Testar com CanvasView/Scene reais, quantidade mínima de vértices e eventos Qt reais. | Fechamento válido cria a seleção/objeto correto; fechamento inválido permanece fail-closed; estado e histórico são observáveis. |
| 11 | Release do retângulo usa Mock como parent e Scene; commit não é confirmação de produto. | Criar retângulo real com dimensões não nulas sobre Scene real e parent QWidget válido. | Seleção é persistida uma vez, undo/redo restauram exatamente os estados, e mensagens não produzem erro secundário de Qt. |
| 12 | Release da elipse tem a mesma incompatibilidade de fixture/Scene. | Repetir o fluxo com elipse real, dimensões válidas, sinais/eventos Qt e manager real. | Elipse válida é confirmada com área/parâmetros esperados; entrada degenerada é rejeitada sem alteração observável. |
| 13 | Integração do lasso usa Scene parcial; snapshot e comando exigem protocolo completo. | Fixture de integração compartilhada com Scene concreta, histórico real, seleção e serialização. | A operação produz exatamente uma entrada, exporta estado válido, desfaz/refaz sem divergência e mantém estado após erro. |
| 14 | Integração do laço poligonal usa o mesmo protocolo incompleto. | Executar caminho real de vértices, normalização e comando, usando a mesma fixture de integração. | Polígono válido passa por uma única preparação canônica; seleção, histórico e round-trip permanecem equivalentes. |
| 15 | Integração da elipse usa Scene falsa e não exercita o contrato real. | Integrar elipse, seleção e histórico com objetos concretos e eventos determinísticos. | Estado de cena, geometria, seleção e undo/redo são iguais após o ciclo completo; erro não deixa mutação parcial. |
| 16 | Manager real é usado sobre Scene falsa; a sequência de múltiplas operações não pode ser validada. | Construir sequência real de operações heterogêneas e snapshots de estado canônico. | A sequência completa desfaz/refaz na ordem correta, sem perder objetos, seleção, parâmetros ou listeners; comparar estados antes/depois por token determinístico. |
| 17 | `get_image_array` recebe Mock que apenas imita QImage; o adapter aceita ndarray/QImage reais. | Criar casos com ndarray válido, QImage válido, formatos/dimensões suportados e entradas inválidas. | Conversão correta, dtype/shape esperados, ownership seguro e falha clara para objeto incompatível; nenhuma aceitação de Mock genérico como imagem. |
| 18 | Sem imagem válida não existe edge map/cache determinístico. | Usar imagem sintética fixa, gerar mapa, repetir para hit e alterar imagem para invalidar. | Miss/hit/invalidação são observáveis, determinísticos e associados à chave correta; ausência de imagem termina fail-closed sem estado inválido. |
| 19 | Press do Magnetic Lasso pressupõe resolução síncrona e imagem falsa. | Exercitar worker/engine com imagem real, anchors válidos, token de geração e entrega por sinal. | Segmento só é aplicado quando a resposta correspondente chega; resposta atrasada/obsoleta é descartada sem corromper preview ou histórico. |
| 20 | Move verifica preview antes da entrega assíncrona e sem fonte de imagem válida. | Usar event loop/ponte Qt, timeout determinístico e espera por sinal explícito; proibir `sleep` arbitrário. | Preview muda apenas para o resultado correto, não bloqueia UI, não aceita resposta fora de ordem e mantém último preview válido em erro. |
| 21 | Duplo clique histórico não forma caminho fechado válido e usa manager Mock. | Construir anchors, caminho fechado e Scene reais; testar fechamento válido e inválido. | Fechamento válido consolida uma seleção; caminho inválido não executa comando, preserva nós e registra motivo. |
| 22 | Caminho com edge map usa imagem falsa; solver retorna vazio corretamente. | Gerar edge map real e executar solver determinístico com parâmetros registrados. | Caminho não vazio somente quando geometricamente suportado; cache reutilizado corretamente; ausência/invalidade do mapa permanece fail-closed. |
| 23 | Teste exige oito pontos por padrão, mas o contrato atual usa piso explícito via `min_points`. | Parametrizar teste de default e teste opt-in com `min_points=8`; não artificialmente alterar simplificação padrão. | Default respeita contrato mínimo; opt-in respeita piso solicitado; curva e área permanecem válidas e finitas. |
| 24 | Teste exige zoom fixo `1.0`, mas reset atual faz fit/center da viewport. | Testar imagens e viewports com aspect ratios distintos, DPI e dimensões pequenas/grandes. | Reset calcula escala/centro esperados, sem drift, e permanece equivalente após resize; nenhum número fixo é usado como substituto da regra. |
| 25 | Snapshot recursivo de Mock causava `RecursionError`; o snapshot cycle-safe já foi corrigido, mas a Scene falsa continua inválida. | Manter regressão direta de ciclo e executar integração com Scene/manager reais; preservar estado privado real. | Snapshot finito, determinístico e sensível a mudanças relevantes; comando real não recursa nem omite estado funcional; erro de Scene permanece visível. |
| 26 | Integração do retângulo usa Fake Scene sem mutação, seleção e retorno exigidos. | Reusar fixture concreta de Scene/CommandManager e eventos Qt reais. | Criação, seleção, undo/redo, serialização e erro controlado passam no mesmo fluxo de produção. Nenhum fallback bypassa histórico. |
| 27 | Integração Magnetic combina caminho síncrono falso, imagem ausente e Scene incompleta. | Teste end-to-end real: ndarray/QImage, edge cache, worker, sinais, Scene, CommandManager, commit e undo/redo. | O pipeline completo é determinístico dentro do timeout, respeita cancelamento/ordem, gera uma entrada de histórico e preserva estado em qualquer falha. |

## 4. Arquitetura obrigatória das fixtures e dos contratos substitutos

### 4.1 Geometria e exportação

- As entradas serão declaradas como dados fixos, versionados e hasháveis.
- Cada fixture terá classificação `válida`, `inválida por auto-interseção`,
  `inválida por área zero`, `degenerada` ou `fora do formato`.
- A preparação canônica será a mesma usada pela criação, edição, API direta e
  exportação.
- Asserções incluirão área assinada, orientação, interseções, contagem de
  vértices, finitude, dimensões físicas, metadados e round-trip.
- Tolerâncias serão derivadas do contrato documentado, fixas e justificadas;
  não serão ajustadas caso a caso para obter aprovação.

### 4.2 Scene, comandos e histórico

- O caminho principal usará `Scene` concreta, `CommandManager` real e objetos
  com estado completo.
- Testes de adapter poderão usar doubles somente quando a fronteira estiver
  explicitamente isolada e com `spec_set`/protocolo restrito.
- Cada operação verificará estado antes, estado após, tamanho do histórico,
  undo, redo, seleção, listeners e persistência.
- Uma falha deverá deixar o último estado válido intacto e fornecer traceback,
  código/mensagem e estado observável.
- O token de snapshot deverá observar estado funcional relevante; somente
  referências efêmeras comprovadamente não semânticas poderão ser excluídas,
  com justificativa e teste.

### 4.3 Qt e viewport

- Testes que cobrem parent, eventos, sinais, widget, viewport ou diálogo usarão
  `QApplication` e `QWidget` reais no ambiente controlado.
- O fluxo assíncrono será sincronizado por sinal, geração, sequência ou condição
  explícita com timeout. `sleep` arbitrário não será evidência de entrega.
- Falhas de plataforma, plugin ou display serão classificadas como bloqueio de
  ambiente, com log completo; não serão convertidas em skip silencioso.
- Capturas visuais deverão indicar resolução, DPI, viewport, commit, hash e
  comparação usada.

### 4.4 Imagens e Magnetic Lasso

- Imagens sintéticas serão determinísticas, pequenas o suficiente para testes e
  suficientemente expressivas para produzir bordas e caminhos.
- Cada imagem terá formato, shape, dtype, hash e expectativa de conversão
  registrados.
- Cache terá testes de miss, hit, invalidação por conteúdo/parâmetro e
  isolamento entre imagens.
- Worker terá testes de sucesso, erro, cancelamento, resposta obsoleta,
  timeout e encerramento seguro.
- O solver determinístico será testado separadamente da ponte Qt, mas o teste
  end-to-end deverá confirmar a integração real.

## 5. Sequência completa de execução

Esta sequência é obrigatória. O avanço entre fases não significa aprovação
parcial; significa somente que o pacote intermediário passou o controle de
segurança necessário para continuar.

### Fase 0 — gate de entrada e congelamento da fronteira

1. Consultar novamente todas as políticas listadas na seção 1.
2. Registrar branch, HEAD, Python, PySide6/Qt, OpenCV, sistema operacional,
   variáveis de ambiente relevantes e estado completo da árvore.
3. Confirmar hashes dos snapshots legados e não tocar em seus bytes.
4. Separar arquivos controlados desta etapa de alterações/untracked preexistentes.
5. Registrar o `manifest.json` não rastreado como bloqueador de evidência até
   haver decisão de propriedade e escopo.
6. Confirmar que não há autorização implícita para excluir, mover, sobrescrever
   ou limpar artefatos do usuário.
7. Criar um plano de rollback e uma cópia/referência verificável dos artefatos
   de entrada.

**Saída obrigatória:** relatório de entrada `APROVADO` ou etapa `BLOQUEADA`.
**Resultado desta execução:** controle de entrada executado com bloqueio de
evidência mantido; isso não é aprovação de fechamento ou de integração.

### Fase 1 — contratos substitutos e fábrica de fixtures

1. Definir helpers reais para Scene/CommandManager/CanvasView/QImage/ndarray.
2. Definir eventos Qt e sincronização assíncrona determinística.
3. Criar fixtures válidas e inválidas com hashes e expectativas.
4. Criar testes de caracterização do estado atual antes de alterar produto.
5. Executar somente os testes de contrato da fábrica e verificar que eles não
   dependem de Mock genérico ou estado global implícito.

**Saída obrigatória:** todos os contratos da fábrica passam sem skips e sem
   erro; qualquer divergência é corrigida ou classificada antes da Fase 2.
**Resultado desta execução:** contratos reais incluídos na suíte substituta
   passaram; as decisões formais por caso estão registradas no pacote da Fase 5.

### Fase 2 — geometrias, bordas, exportação e viewport

1. Tratar os casos `#1`, `#2`, `#3`, `#4`, `#5`, `#23` e `#24`.
2. Não alterar produto quando o comportamento atual for o contrato correto.
3. Corrigir somente defeito demonstrado por comparação com a especificação.
4. Executar testes unitários, caracterização, exportação/round-trip e viewport.
5. Repetir os casos negativos para provar rejeição sem mutação parcial.

**Saída obrigatória:** cada caso tem diagnóstico, teste substituto executado,
resultado bruto e classificação formal `CORRIGIDO`, `NO_CHANGE` ou `BLOQUEADO`.
**Resultado desta execução:** os substitutos dos casos #1, #2, #3, #4, #5,
   #23 e #24 passaram; as decisões formais estão registradas como `NO_CHANGE`.

### Fase 3 — ferramentas síncronas e histórico

1. Tratar `#6`, `#7`, `#8`, `#9`, `#11`, `#12`, `#13`, `#14`, `#15`, `#16`,
   `#25` e `#26`.
2. Usar objetos reais para confirmação; nenhum fallback poderá fabricar
   `CommandResult` ou ignorar o histórico.
3. Verificar commit único por gesto, cancelamento, troca de ferramenta,
   undo/redo e preservação em erro.
4. Executar também o caso `#10` como não regressão, sem removê-lo do inventário.

**Saída obrigatória:** cada fluxo passa por criação, erro, undo, redo e estado
   persistido quando aplicável; nenhum teste depende de estado não declarado.
**Resultado desta execução:** os substitutos reais dos casos #6–#16, #25 e #26
   passaram; o caso #10 foi mantido como não regressão. A reconciliação formal
   registra a causa e a decisão de cada divergência do runner histórico.

### Fase 4 — Magnetic Lasso, cache e assincronia

1. Tratar `#17`, `#18`, `#19`, `#20`, `#21`, `#22` e `#27`.
2. Separar solver determinístico, conversão de imagem, cache e ponte Qt.
3. Exercitar sucesso, erro, timeout, cancelamento e resposta fora de ordem.
4. Registrar os sinais, tokens, tempos, geração e estado de cache observados.
5. Repetir o fluxo em Windows com `QApplication` real e ambiente controlado.

**Saída obrigatória:** solver, cache, worker e integração passam separadamente e
   no end-to-end; qualquer ausência de entrega ou timeout é falha/bloqueio
   explícito, nunca skip.
**Resultado desta execução:** os substitutos reais dos casos #17–#22 e #27
   passaram com sinais Qt, timeout/cancelamento e descarte de resposta tardia em
   duas repetições independentes; o gate formal atual foi aceito.

### Fase 5 — reconciliação formal

1. Executar novamente o runner histórico integral sem alterar snapshots.
2. Executar todos os testes substitutos referenciados, não apenas os focais.
3. Para cada caso, comparar assinatura histórica, causa raiz, substituto e
   comportamento atual.
4. Registrar explicitamente os casos sem bug de produto como `NO_CHANGE` com
   justificativa verificável.
5. Registrar a decisão formal do caso `#10` como `NO_CHANGE` por não regressão
   observada no runner atual, preservando sua expectativa histórica e deixando
   explícito que ausência de reprodução não altera o snapshot.
6. Somente após todos os substitutos passarem, propor alteração formal no
   mecanismo/manifesto de reconciliação, se o schema atual não representar
   corretamente casos resolvidos ou assinaturas substituídas.
7. Testar a própria reconciliação, inclusive ids, referências, mensagens,
   duplicatas, ausências e mudança de assinatura.

**Saída obrigatória:** reconciliação `accepted=true` ou bloqueio formal com
   divergência listada. Nesta execução, o gate formal atual retornou
   `accepted=true`; o resultado histórico bruto continua separado e
   `accepted=false` por preservação dos snapshots.

### Fase 6 — pacote de evidências e auditoria de integridade

O pacote deverá conter, no mínimo:

- relatório vivo desta etapa atualizado com resultados reais;
- branch, commit/HEAD e base de rollback;
- ambiente completo e comandos exatos;
- lista de arquivos, tamanhos, hashes e fronteira staged;
- snapshots históricos e prova de que não foram alterados;
- logs/JUnit/tracebacks completos do runner histórico integral e logs/JUnit
  dos testes substitutos, com os 27 IDs reconciliados individualmente;
- dump/stack nativo quando houver crash, hang, abort ou falha de processo;
- para falha determinística sem crash, entrada hashable, traceback, estado
  antes/depois e teste equivalente reproduzível;
- resultados de cobertura, performance, memória e determinismo;
- capturas visuais/Qt quando aplicável;
- limitações e itens `NÃO TESTADO`/`BLOQUEADO`;
- decisão formal por caso;
- plano e prova de rollback.

O `manifest.json` não rastreado deverá ser auditado quanto a:

1. proprietário e origem;
2. pertencimento ou não à etapa;
3. conteúdo, bytes, hash e referências;
4. risco de exposição de dados locais;
5. forma correta de rastrear, excluir do escopo ou classificar como bloqueio;
6. confirmação de que nenhuma ação destrutiva foi tomada sem autorização.

O pacote somente será considerado íntegro quando `tools/evidence_integrity.py
--require-tracked --git-blob` passar sobre o escopo real, incluindo seus
manifests e referências.

### Fase 7 — gates finais e decisão de integração

Executar na mesma revisão candidata:

1. suíte oficial completa;
2. suíte substituta completa dos 26 casos;
3. runner histórico integral, sem skip/xfail adicionado;
4. reconciliação formal aceita;
5. cobertura de linhas, branches e módulos conforme política;
6. compile/import;
7. flake8, Black, isort e mypy;
8. Bandit e auditoria de dependências;
9. testes Windows/Qt e exportação/round-trip;
10. benchmark comparável ao baseline, incluindo cache/incremental/frame;
11. determinismo em repetição e ausência de race/timeout;
12. diff check e revisão de exclusões acidentais;
13. baseline integrity;
14. evidence integrity;
15. revisão de privacidade e segurança do pacote.

Uma única falha desconhecida, assinatura não explicada, arquivo fora da
fronteira, teste faltante, regressão de performance, evidência incompleta ou
manifest não resolvido impede a decisão de merge.

## 6. Evidência nativa, determinística e de diagnóstico

### 6.1 Quando dump/stack nativo é obrigatório

Para crash de processo, abort nativo, hang, violação de acesso, encerramento
do Qt, worker que não termina ou comportamento dependente de plataforma, será
obrigatório coletar dump/stack nativo, identificação do processo, símbolos
disponíveis, comando, ambiente e hash do binário/código testado.

### 6.2 Quando a prova determinística é equivalente

Para rejeição geométrica, mismatch de contrato, retorno inválido, estado
parcial, assinatura de snapshot ou falha de fixture sem crash, a prova poderá
ser determinística equivalente, contendo:

- entrada serializável e hash;
- comando exato;
- traceback completo;
- estado canônico antes/depois;
- expectativa do contrato;
- teste substituto reproduzível;
- repetição que confirme a mesma assinatura;
- razão técnica para não ser necessária uma captura nativa.

Nunca será afirmado que houve dump nativo quando apenas houve traceback Python,
nem que houve equivalência quando somente um smoke test passou.

## 7. Desempenho, memória e segurança

### 7.1 Desempenho

- Comparar com a mesma metodologia do baseline e com o mesmo conteúdo de
  entrada.
- Medir p50/p95 quando o contrato exigir, além de tempo total, contagem de
  recomputações, cache hit/miss, memória e duração do worker.
- Confirmar que a correção de fixtures não esconde custo de produção.
- Repetir o benchmark para separar ruído, aquecimento e não determinismo.
- Qualquer regressão relevante em cache, incremental, frame ou UI bloqueia a
  etapa, mesmo que os testes funcionais passem.

### 7.2 Segurança e privacidade

- Não executar arquivos de entrada não confiáveis fora dos mecanismos previstos.
- Sanitizar caminhos locais, nomes de usuário, tokens e conteúdo sensível dos
  logs e dumps antes de versionar evidências.
- Não incluir dados pessoais em fixtures ou capturas.
- Validar limites de tamanho, formato, finitude, dtype e alocação das imagens.
- Confirmar que erro de imagem, exportação ou comando não grava arquivo parcial,
  não sobrescreve dado válido e não deixa cache contaminado.
- Executar Bandit, auditoria de dependências e inspeção de permissões no pacote.

## 8. Riscos, bloqueadores e rollback

### 8.1 Riscos conhecidos

- Modernizar fixtures pode revelar defeitos reais antes mascarados pelo Mock.
- A assincronia do Magnetic Lasso pode expor races que não aparecem no solver
  unitário.
- Alterar o harness de reconciliação pode criar divergência entre o histórico
  imutável e o estado vivo.
- O manifest não rastreado pode impedir o gate mesmo que o código passe.
- Testes Qt podem depender de Windows, plugin ou event loop específico.

### 8.2 Condições de parada

Parar imediatamente e registrar `BLOQUEADO` diante de:

- perda ou sobrescrita de dados;
- regressão funcional ou de compatibilidade;
- divergência entre plataformas sem causa;
- não determinismo ou race não explicado;
- crash/hang sem diagnóstico suficiente;
- alteração fora da fronteira;
- falha de integridade de snapshot, baseline ou evidência;
- ausência de fixture real, ambiente ou artefato necessário;
- necessidade de alterar regra, threshold, skip, xfail ou snapshot para passar.

### 8.3 Rollback

- A base funcional de rollback é `7f3799c1b29835f6db5ab6d35c0cab5deda5765b`,
  sem reset destrutivo da árvore do usuário.
- O lote corretivo deverá ser isolado em commit(s) pequenos o suficiente para
  revisão, mas nenhum commit será considerado integrável antes do fechamento
  integral desta etapa.
- O rollback formal será feito por revert do commit candidato ou por aplicação
  de patch reversível e verificado; não será usado `git reset --hard`,
  `git checkout --` ou limpeza ampla para ocultar estado.
- Untracked e evidências preexistentes serão preservados durante rollback.
- Após rollback, repetir baseline, integridade e smoke mínimo para provar que o
  produto retornou ao estado anterior.

## 9. Critérios formais de encerramento

A etapa só poderá receber `APROVADO / CONCLUÍDO` quando todos os itens forem
verdadeiros na mesma revisão candidata:

- os 26 casos possuem diagnóstico, decisão e teste substituto correspondente;
- o caso #10 continua passando e documentado como não regressão;
- nenhum snapshot histórico foi alterado;
- nenhuma falha foi escondida por skip, xfail, filtro ou mudança de threshold;
- todas as fixtures são reais, determinísticas e adequadas ao contrato;
- testes unitários, integração, Qt, exportação, round-trip e assíncronos
  aplicáveis passam integralmente;
- falhas negativas provam preservação de estado e ausência de histórico parcial;
- reconciliação formal está aceita e testada;
- manifest não rastreado está resolvido ou formalmente classificado, sem violar
  o gate de evidências;
- suíte oficial, cobertura, estática, segurança, performance e baseline passam;
- evidências contêm comandos, entradas, hashes, resultados, limitações e
  decisão, com integridade verificável;
- revisão final confirma que funcionalidades, dados, formatos, mensagens,
  compatibilidade e rollback foram preservados;
- somente depois disso haverá autorização operacional para merge. O commit e o
  push do checkpoint técnico de candidata, quando aplicáveis, seguem a exceção
  restrita da seção 10.1 e não equivalem à conclusão da etapa.

Qualquer item falso mantém a etapa `EM EXECUÇÃO` ou `BLOQUEADA`; não existe
estado intermediário apresentado como conclusão.

## 10. Decisões explicitamente registradas nesta abertura

1. O proprietário aceitou as recomendações técnicas para os 26 casos.
2. A execução seguirá fixtures reais, contratos substitutos, reconciliação
   formal, auditoria do manifest e todos os gates antes de integração.
3. Snapshots históricos continuarão representando o comportamento antigo e não
   serão alterados para obter pass.
4. O caso #10 permanece no conjunto de não regressão, embora já esteja passando.
5. O trabalho atual não está autorizado a declarar implementação, testes ou
   evidências completos por execução parcial.
6. Nenhum merge está autorizado antes dos critérios da seção 9. O commit e o
   push de uma candidata técnica só podem ocorrer pela exceção restrita da
   seção 10.1, sem declarar integração ou aprovação.
7. A consulta às regras é obrigatória antes de cada decisão de engenharia e
   deverá ser citada no registro da decisão correspondente.

### 10.1 Exceção controlada para candidata de CI/empacotamento

Para resolver a dependência operacional entre a árvore limpa exigida pelo
empacotamento e o CI que precisa validar um SHA rastreado, fica autorizada
somente a seguinte sequência, sem alterar a decisão `BLOQUEADA`:

1. auditar o estado staged e não rastreado, sem `reset`, `clean`, `stash`,
   exclusão, movimentação ou rastreamento automático de artefatos;
2. confirmar que o commit contém apenas o lote técnico/documental revisado e
   as evidências necessárias, sem arquivos não relacionados;
3. validar diff, baseline e integridade de evidências antes do commit;
4. criar um commit técnico de candidata, com rollback por revert, identificado
   como não integrável enquanto B-04 existir;
5. publicar esse commit somente na branch de trabalho/PR para disparar o CI;
6. executar o empacotamento em uma árvore limpa derivada exatamente desse SHA;
7. manter merge, tag, release e qualquer declaração `APROVADO`, `CONCLUÍDO`,
   `INTEGRADO` ou `PRONTO` proibidos até todos os critérios da seção 9 serem
   verdadeiros na mesma revisão candidata.

Esta exceção é administrativa e operacional: não flexibiliza testes, cobertura,
integridade, rastreabilidade, não regressão, proteção de dados, preservação dos
snapshots ou qualquer regra das políticas globais. A decisão foi registrada
após consulta à `POLITICA_QUALIDADE_E_EVIDENCIAS.md`, à
`POLITICA_NAO_REGRESSAO.md` e ao contrato de árvore limpa de
`scripts/build_windows.ps1`.

## 11. Próximo passo exato e condição de avanço

A reconciliação dos 27 casos e a auditoria formal dos 63 manifests foram
resolvidas e incorporadas como evidência rastreada. O gate atual
`formal_reconciliation.json` retorna `accepted=true` somente no escopo do
contrato atual; os snapshots e o runner histórico exato permanecem imutáveis e
com `accepted=false`.

1. Preservar as decisões individuais: 26 `NO_CHANGE` e #25 `CORRIGIDO`
   limitado ao defeito cycle-safe; #10 permanece `NO_CHANGE`. As 11 assinaturas
   divergentes e as 12 ausências continuam enumeradas.
2. Preservar os 63 manifests sem excluir, mover, sobrescrever ou rastrear
   automaticamente. O novo resolution manifest registra owner operacional,
   origem limitada ao que é provado, escopo, referências e tratamento; as 706
   referências ausentes dos dois releases históricos continuam declaradas.
3. A Fase 7 local foi executada na mesma candidata: suíte oficial, substitutos,
   runner integral, cobertura, compile/import, estática, segurança, benchmarks,
   timeout/determinismo, baseline e evidence integrity.
4. A capacidade residual de symlink foi comprovada por prova autorizada na VM
   Windows 11/VMware: os dois testes passaram sem skip. Permanece o bloqueio de
   integração para repetir os gates em pacote completo e confirmar CI/
   empacotamento no candidato final; a evidência rastreada está em
   `docs/evidence/ETAPA_7_SYMLINK_VMWARE_2026-09-02.md`.
5. Se qualquer gate produzir falha, divergência, não determinismo, regressão ou
   evidência incompleta, manter `BLOQUEADA` e investigar a causa. O checkpoint
   técnico poderá ser criado e publicado somente conforme a seção 10.1; só após
   todos os critérios da seção 9 serem verdadeiros na mesma revisão será
   possível propor o merge.

Esta atualização não altera `quality/legacy_tests/manifest.json`,
`quality/legacy_tests/reconciliation.json`, snapshots históricos ou os 63
manifests preexistentes. Também não declara que qualquer caso foi aprovado
apenas porque um substituto passou.
