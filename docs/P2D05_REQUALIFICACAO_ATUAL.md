# P2D-05 — acompanhamento vivo da requalificação

## Revisão corrente — qualificação pós-commit da Caneta — 05/09/2026

O lote `PEN-HANDLES-20260905` está no commit
`1068166f3c046e008928d98e68fdb187838c87bc`, em árvore limpa. O runner
Windows oficial passou `196/196` arquivos e `2019` testes, com `0` falhas,
`0` erros e `2` skips previstos; cobertura, estática, segurança, Stage 4B.5,
baseline/evidências, gate legado e build portátil com smoke `SUCCESS` também
passaram. A falha inicial de qsb foi reproduzida no SHA-base `5b3e6b1` e não
é regressão deste lote.

Estado `IN_PROGRESS / BLOCKED`: o CI remoto e a auditoria nativa de cliques do
SO no executável ainda não foram executados. Push, merge, tag e release não
estão autorizados. [Evidência](evidence/PEN_HANDLES_QUANTIZACAO_POSTCOMMIT_2026-09-05.md).

## Revisão corrente — lote corretivo da Caneta — 05/09/2026

O lote PEN-HANDLES-20260905 é uma alteração geométrica separada do lote
anterior de idioma/status. Na base 5b3e6b1, a criação por clique introduzia
controles implícitos que podiam produzir auto-retorno após a quantização. A
candidata elimina essa mutação implícita e cria alças somente por arraste
explícito, preservando o validador de polígonos inválidos.

Estado IN_PROGRESS / PRECOMMIT_PENDING, sem SHA de commit candidato. A
rodada focada passou 69/69, com persistência/exportação e cancelamento
incluídos. A suíte agregada local deu 2016 passed, 2 skipped, 1 failed;
essa falha modal foi reproduzida na base limpa e permanece classificada como
diagnóstico herdado. Runner oficial, cobertura, build, CI remoto e revisão
humana ainda não qualificam este lote.
Fronteira e resultados:
LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md.

## Revisão corrente — lote autorizado em 04/09, atualizado em 05/09/2026

A coleta no merge documental `4b873c3` encontrou idioma incorreto na Caneta
recém-selecionada e truncamento do canal STATUS. O proprietário autorizou um
lote limitado a apresentação/idioma, sem mudança de matemática ou histórico.
Estado IN_PROGRESS, em pré-commit; os resultados são do patch sobre a base,
não qualificação limpa de 4b873c3. PRECOMMIT, revisão humana, build/CI do
futuro SHA e symlinks correspondentes seguem pendentes; publicação final
BLOCKED. [Registro de mudança e gates](P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md).

Rodada local R2: 1.968 testes aprovados, dois skips WinError 1314; cobertura
92,74% de linhas / 85,17% de branches e gates de estática/integridade passaram.
Runner legado retornou FAIL por árvore não limpa; build não executado.
Código/testes congelados para revisão pré-commit; dez capturas Qt reais
disponíveis, sem aceite visual humano. Não representa encerramento do lote.

## Snapshot anterior — sincronização autorizada em 04/09/2026

Estado: `IN_PROGRESS`; PR #170 em rascunho. O proprietário aprovou a
recomendação de preservar o histórico privado, manter `f9f39ed` separado,
sincronizar `origin/main` na candidata e requalificar antes da revisão humana.
A autorização não permite merge da PR, tag, release ou aceite humano automático.

Entrada: `35727d99c7002ad26c3277dff8542f82dad4c3f8`; main incorporada:
`b9557e6e85c7b28adf90ea616c171e222c96e84c`. O merge de sincronização
preserva ambos os pais, sem rebase/force-push. A alteração recebida de main é
documental; código, testes, dependências, workflows e snapshots binários não
serão modificados por este lote. O manifesto vivo deve conter a união da
fronteira aprovada, sem remoções para obter PASS.

O CI `33932398814` passou em Linux e Windows no SHA de entrada: Windows
1.956 testes, zero falhas, erros ou skips; os dois testes de symlink foram
conferidos nominalmente no JUnit. Isso resolve a pendência no SHA `35727d9`,
não aprova o novo commit de integração. Revisão humana da UI continua
`PENDING_EVIDENCE`; Ready/merge/release permanecem `BLOCKED`.

Evidência e roteiro: [sincronização da candidata](evidence/P2D05_SINCRONIZACAO_MAIN_2026-09-04.md).
Os registros anteriores abaixo conservam seus resultados e limitações de
época; não descrevem o resultado de gates posteriores.

## Snapshot anterior — fonte efb0caf

**Data:** 2026-09-04. **Estado:** `PARCIAL / BLOCKED` para publicação.
**Base:** `7283e40dea58f039e9d16b1584739ca339058e5f`.
**SHA-fonte requalificado localmente:** `efb0caf6fcf34b2ccdcf2d70314a6b2ea69991d3`.
**Branch:** `Ailton/error-presentation-contract-20260904`.

Tipagem global, baseline e integridade rastreada passaram no SHA-fonte limpo.
A suíte oficial registrou 1.954 testes aprovados e dois skips por privilégio
de symlink; cobertura 92,70% de linhas e 85,17% de branches. Estática, segurança,
Stage 4B.5, gate formal, build e smoke também passaram nos respectivos escopos.
Relatório e pacote: [requalificação datada](evidence/P2D05_REQUALIFICACAO_TIPAGEM_INTEGRIDADE_2026-09-04.md).
O commit documental descendente não herda automaticamente esses gates.

## Autoridade, autorização e fronteira

O proprietário solicitou resolver tipagem global, integridade das evidências
e requalificar o novo SHA em checkout limpo. Este registro é subordinado à
Política de Qualidade e Evidências, à Governança de Integridade e ao contrato
`C-GLOBAL-ERROR-PRESENTATION-P2D05-2026-09-04`. Não altera os critérios deles.

Escopo: dois guardas de modelo em `src/tools/polygon_edit_tool.py`, seis
regressões em `tests/test_error_presentation_contract.py`, reconciliação do
manifesto vivo `baseline_manifest.json`, documentos vivos e novas evidências.
G/V/B esperado: sem mudança de geometria, aparência ou comportamento; tornar
explícita a rejeição já existente para modelo/histórico indisponível.
Schemas, limites, CI, validadores, snapshots, engines e arquivos não rastreados
preexistentes permanecem inalterados. Rollback deste lote: reversão específica
da correção sobre a base acima, nunca reset ou exclusão de evidências.

## Diagnóstico e correção

Na base limpa, `mypy src` reproduziu três erros `union-attr`, nas linhas
160, 745 e 755 de `polygon_edit_tool.py`. Verificar apenas `manager is None`
não estreitava o tipo de `model`. Os dois guardas passam a verificar também
`model is None`; sem casts, supressões ou relaxamento de configuração.

No ambiente isolado Python 3.11.9, criado com Poetry 2.4.1 e sincronizado pelo
lock existente, a correção pré-commit passou em `mypy src` (147 arquivos) e
nos 29 testes focados dos módulos de apresentação, edição de vértices e layers.
Esses testes são `DIAGNOSTIC_ONLY`, não substituem a suíte oficial nem revisão
visual humana. O checkout pré-commit continha o patch; não era um SHA limpo.

## Integridade e preservação

O gate `tools/evidence_integrity.py --require-tracked --git-blob` passou nos
134 manifestos do checkout limpo da base. A falha na pasta de trabalho vem
dos pacotes **não rastreados** abaixo; não comprova defeito nos blobs versionados:

- `docs/evidence/artifacts/pen-tool-revalidation-20260903/`;
- `docs/evidence/artifacts/pen-tool-revalidation-20260904-5aec/`;
- `docs/evidence/artifacts/pen-tool-revalidation-20260904-r2/`.

O primeiro índice também omite hash/tamanho de `report.json`. Os três pacotes
continuam preservados no local original, sem reescrita, remoção, exclusão por
regra de ignore ou incorporação automática. Não são prova da candidata atual.
Resolver a fronteira versionada não torna o gate da pasta principal aprovado.

O manifesto vivo foi reconciliado com todos os arquivos rastreados aprovados
dos lotes P2D-05, sem nenhuma remoção. Nenhum arquivo pode ser retirado para obter PASS;
schemas, canonicalização e validadores permanecem intactos. Snapshots de
baseline e auditorias históricas não serão recalculados.

## Qualificação e limitações

Executados no SHA-fonte: baseline/evidências, runner Windows com cobertura,
estática, segurança, Stage 4B.5, runner legado, build, smoke e integridade do ZIP.
Logs novos foram preservados com comandos, ambiente, SHA, estado da árvore,
bytes e hashes, separando entrada, pré-commit e pós-commit.
Pendente: os dois symlinks no SHA exato em ambiente habilitado, revisão humana,
CI remoto e requalificação completa do commit documental descendente. O novo
pacote documental requer seus próprios gates de integridade antes de publicação.

O ambiente anterior tinha resolução incorreta de qsb e teste não rastreado;
suas contagens não serão atribuídas ao novo checkout. As falhas anteriores de
cobertura monolítica Qt não são apagadas nem têm causa raiz declarada por
inferência. A qualificação Windows segue o runner por arquivo já definido no CI.

Uma invocação diagnóstica apontou para um nome de teste inexistente e coletou
zero testes (retorno 4); a invocação corrigida usou o arquivo real de edição de
vértices. Na instalação limpa, Poetry avisou sobre bytecode em wheels de NumPy
e PySide6 e arquivos sobrepostos do PySide6; não houve falha da sincronização.

CI Linux/Windows remoto e revisão humana da UI permanecem pendentes.
Resultados antigos de C12/PR #168 são históricos, não aprovam o HEAD P2D-05.
Nenhum push, merge, tag, release ou novo lote está autorizado por este registro.
