# P2D-05 — tipagem, integridade rastreada e requalificação isolada

**Data:** 2026-09-04. **Decisão global:** `PARCIAL / BLOCKED` para publicação.
**Base:** `7283e40dea58f039e9d16b1584739ca339058e5f`.
**SHA-fonte testado:** `efb0caf6fcf34b2ccdcf2d70314a6b2ea69991d3`.
**Branch:** `Ailton/error-presentation-contract-20260904`.
**Contrato:** `C-GLOBAL-ERROR-PRESENTATION-P2D05-2026-09-04`.

Este snapshot registra execução local, não CI, aprovação visual ou fechamento
global P2D-05. O commit documental que incorpora este relatório é descendente
do SHA-fonte acima; não é apresentado como tendo executado sua suíte completa.
O estado vivo está em `docs/P2D05_REQUALIFICACAO_ATUAL.md`.

## 1. Objetivo, autorização e fronteira

O proprietário solicitou corrigir tipagem global e integridade das evidências,
além de requalificar o novo SHA em checkout limpo. A correção de produção
acrescenta somente `model is None or` a dois guardas de
`src/tools/polygon_edit_tool.py`. Seis regressões foram adicionadas em
`tests/test_error_presentation_contract.py`, cobrindo ausência do atributo
modelo, modelo nulo e histórico ausente, tanto para gesto quanto para exclusão.

Não houve alteração de geometria, persistência, comandos, texto de mensagem,
thresholds, validadores, CI, snapshots ou engines. O manifesto vivo foi
reconciliado sem remover entradas. README, plano mestre, matriz de riscos e
índice de evidências receberam um estado P2D-05 separado das revisões antigas.

## 2. Causa reproduzida e resolução

O SHA-base reproduziu três erros `union-attr` em `mypy src`: linhas 160, 745
e 755. O guarda do histórico não estreitava o tipo opcional do modelo. Os
guardas explícitos resolvem os três erros sem `cast`, `ignore` ou relaxamento
de tipagem. A pré-condição e a mensagem já existentes são preservadas.

O baseline da base falhou por sete entradas ausentes e 17 digests divergentes
dos lotes P2D-05 já commitados. Sua reconciliação não removeu nenhum arquivo.
Na execução diagnóstica inicial, o índice Git permaneceu na base, embora o
patch de dois arquivos tenha sido aplicado ao worktree durante a leitura;
o recibo registra esse estado final. A prova posterior usa o SHA corrigido
com árvore limpa antes e depois dos gates.

O gate de evidência passou nos **134 manifestos rastreados**, tanto na base
limpa quanto no SHA corrigido. A pasta principal continua contendo três
pacotes não rastreados da Caneta, com falhas de tracked boundary e, no primeiro,
ausência de hash/tamanho de `report.json`. Permanecem nos locais originais:

- `docs/evidence/artifacts/pen-tool-revalidation-20260903/`;
- `docs/evidence/artifacts/pen-tool-revalidation-20260904-5aec/`;
- `docs/evidence/artifacts/pen-tool-revalidation-20260904-r2/`.

O inventário hashado desses arquivos está no pacote. Eles não foram apagados,
movidos, ignorados ou incorporados silenciosamente. Aprovar a integridade da
fronteira rastreada não significa aprovar o gate da pasta principal.

## 3. Ambiente e reprodução

Checkout Git detached, ambiente virtual próprio criado com Poetry **2.4.1**,
`poetry check --lock --strict` e `poetry sync --no-interaction --no-ansi`.
Python **3.11.9**, PySide6 **6.10.1**, pytest **9.1.1**, PyInstaller **6.22.0**.
Plataforma reportada: `Windows-10-10.0.26200-SP0`; Qt `offscreen`, DPI lógico 96.
O módulo importado foi confirmado como pertencente ao checkout de qualificação.

SHA-256 canônico LF do lock:
`05e0262e40a3f956bdcfb20b47794f8e8a04ec68d5afeec1931f2285d0340e65`.
As dependências completas estão em `runs/postcommit-environment.log` no ZIP.

Para repetir, criar um checkout limpo do SHA-fonte e sincronizar o lock com
Poetry 2.4.1/Python 3.11. Executar os comandos dos recibos `runs/*.json`, usando
`<project>` para o checkout e `<output>` para uma nova pasta externa de logs.
Manter `QT_QPA_PLATFORM=offscreen`, prefixar `.venv/Scripts` no PATH e definir
`NEOENG_SOURCE_HEAD_SHA` com o SHA testado para o runner formal.
O smoke usa `LOCALAPPDATA=<project>/build/smoke-profile` para isolar configuração.
Os coletores locais utilizados estão em `reproduction/` dentro do ZIP.

## 4. Resultados observados no SHA-fonte

| Gate | Resultado | Evidência no pacote |
|---|---|---|
| Lock estrito | PASS | `runs/postcommit-static.*` (rótulo do recibo de lock) |
| Compilação, flake8, Black, isort | PASS | recibos `postcommit-compile`, `flake8`, `black`, `isort` |
| Tipagem global | PASS; 147 arquivos | `runs/postcommit-mypy.*` |
| Bandit, severidade alta | PASS | `runs/postcommit-bandit.*` |
| pip-audit | PASS no escopo auditável | `runs/postcommit-audit.*` |
| Baseline Git blob corrigido | PASS; 3.251 arquivos | `runs/postcommit-baseline.*` |
| Integridade Git blob rastreada | PASS; 134 manifestos | `runs/postcommit-evidence.*` |
| Runner Windows oficial completo | 194/194 arquivos; 1.956 testes; 1.954 passaram, 2 skips, 0 falhas/erros | `runs/windows-coverage/summary.json`, JUnit e logs por arquivo |
| Política de cobertura | PASS | `runs/postcommit-coverage-policy.*`, `runs/windows-coverage/coverage.xml` |
| Stage 4B.5 | PASS | `runs/postcommit-stage4b5.*`, `runs/stage4b5/` |
| Gate formal legado | ACCEPTED; 42 substitutos passaram | `runs/legacy/formal-gate.json` e saídas históricas |
| Build portátil e smoke | PASS no escopo de inicialização | `runs/postcommit-build.*`, `runs/portable-smoke.jsonl` |
| ZIP e digests internos | PASS; 314 arquivos | `runs/postcommit-portable-integrity.*`, `portable/release-manifest.json` |

Cobertura corrente: **24.155/26.058 linhas (92,70%)** e
**6.727/7.898 branches (85,17%)**. Nenhum threshold foi alterado.
O conjunto limpo não inclui `tests/test_p2d_05_quality_contract.py`, arquivo
preexistente não rastreado com 17 casos. A contagem anterior não foi reutilizada:
1.967 anteriores, menos esses 17, mais seis regressões novas = 1.956 atuais.
Nenhum teste versionado foi retirado ou filtrado da execução oficial.

O runner legado manteve o resultado bruto **196 testes / 26 falhas / retorno 1**,
15 assinaturas históricas exatas, 11 divergentes e 12 ausências históricas.
O contrato atual resolveu os 27 casos com 42 testes substitutos; os snapshots
não foram modificados para tornar o resultado histórico verde.

## 5. Build e limites da prova

O ZIP local `NeoEng-D-Trace-efb0caf.zip` tem **124.229.848 bytes** e SHA-256
`ddd03a0c8a5e3e268cd14dfe576c28eb2dedcf374bc39a110043e2a2da33460d`.
Seu CRC e os 314 digests foram conferidos após reabertura. O binário não foi
publicado nem incorporado ao repositório; o manifesto está no pacote de prova.

O smoke comprovou `application.opened`, `application.state.saved` e
`application.closed`, encerramento zero e nenhuma ausência de evento esperado.
Não é teste completo de ferramentas, inspeção humana, instalação MSI ou prova
de engines. O SHA foi vinculado pelo checkout limpo, comando e manifesto da
build; isso não declara nova identidade de commit embutida no executável.

## 6. Falhas, avisos e pendências preservados

- Os dois contratos de symlink tiveram `WinError 1314`. Responsável pela
  liberação do ambiente: proprietário/revisor. Condição de remoção: executar
  ambos no mesmo SHA em Windows com privilégio adequado ou no CI obrigatório,
  sem skip. O VMware histórico não aprova este novo SHA automaticamente.
- pip-audit ignorou entradas de cache inválidas e não auditou o próprio
  `neoeng-d-trace 0.3.0`, ausente no PyPI; não encontrou vulnerabilidade conhecida
  nas dependências auditadas. Os avisos não foram removidos do log.
- Poetry avisou sobre bytecode em wheels e sobreposições PySide6 na instalação
  inicial. A saída dessa instalação está na conversa, não neste pacote; o
  lock e o ambiente resultante estão registrados. Não se alega instalação sem
  cache ou ausência de avisos.
- Black retornou zero e salvou log; o coletor falhou ao imprimir símbolos no
  terminal CP1252. As chamadas seguintes usaram `-X utf8`. Não houve mudança
  no gate nem descarte do resultado. Um diagnóstico anterior apontou para
  nome de teste inexistente e retornou 4; a execução corrigida está registrada.
- O smoke declarou fallback CPU por ausência de CuPy. Os avisos completos do
  PyInstaller foram preservados em `portable/pyinstaller-warnings.txt`; o smoke
  não prova que todos os caminhos opcionais da build foram exercitados.
- As falhas monolíticas Qt anteriores permanecem históricas, com causa raiz
  não comprovada. Foi usado o runner Windows por arquivo já exigido pelo CI.
- CI remoto Linux/Windows, nova revisão humana da UI e qualificação completa
  do commit documental descendente permanecem pendentes.

## 7. Pacote, integridade e decisão

Pacote: `docs/evidence/artifacts/p2d05-requalification-efb0caf-20260904/`.
`artifact-index.json` registra bytes/SHA-256 do ZIP e de cada membro. Inclui
logs, JUnit, cobertura, recibos com códigos de retorno/estado Git, patch e
snapshots integrais dos nove arquivos do escopo, antes/depois quando existentes.

Os arquivos de execução originais permanecem locais. As cópias publicáveis
normalizam UTF-8/LF e redigem prefixos pessoais; `normalization-provenance.json`
registra hashes originais e das cópias. Os recibos do novo pacote apontam para
os logs efetivamente empacotados. Índices transitórios de saída permanecem
locais; o novo índice cobre seus artefatos. Snapshots-fonte são blobs Git sem
reescrita. Isso é sanitização declarada da execução corrente, não recriação
de evidência histórica ausente.

Tipagem e baseline corrigidos; integridade rastreada comprovada no SHA-fonte.
Requalificação local **PARCIAL** pelos dois skips e pelas limitações acima.
Publicação/encerramento **BLOCKED**. Nenhum push, merge, tag, release ou novo
lote foi executado. Próximo gate: revisão da evidência e resolução das
pendências do SHA exato; não avançar por analogia com C12 ou CI anteriores.
