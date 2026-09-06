# P2D-05 — lote corretivo de idioma e status

ID: P2D05-LANG-STATUS-20260904. Tipo: registro de mudança e acompanhamento.
Versão 1. Data: 2026-09-04 (UTC-03). Estado: IN_PROGRESS.

Atualização em 2026-09-05: retomada sobre a mesma base e patch, sem commit.
A primeira rodada completa ficou preservada no pacote local de revisão R1;
não qualifica o ajuste posterior. A fonte/QSS reais do launcher reproduziram
três falhas de altura de 103 pixels, acima dos 96 mantidos na regressão.
O aviso agora calcula sua altura pela largura disponível, com botões em linha;
fonte/estilo do QApplication são restaurados no teardown dos testes.
Rodada R2 local encerrada; runner legado e build oficiais requerem árvore
limpa e não serão contornados antes do aceite PRECOMMIT. O lote permanece
IN_PROGRESS, sem aprovação final; resultados e pendências abaixo.
Base: `4b873c39736477652d3b71a841bba7f9bf41cfad`, checkout isolado.
Destino: `Ailton/error-presentation-contract-20260904`, PR #170 em rascunho.

## Autoridade e autorização

O proprietário respondeu "Autorizo" ao lote restrito ao idioma e à
apresentação legível das mensagens/detalhes, sem alterar a matemática da
Caneta. Esta autorização permite implementação e verificação, não aceite
humano, merge, tag ou release. O aceite PRECOMMIT do lote exato permanece
necessário conforme a seção 10 da decisão P2D-05; aceites antigos não são
transferidos a este patch.

Dependências: [contrato global](CONTRATO_APRESENTACAO_ERROS_P2D05_2026-09-04.md),
[política](POLITICA_QUALIDADE_E_EVIDENCIAS.md),
[governança](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md),
[decisão P2D-05](DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md),
[plano mestre](PLANO_MESTRE_ESTABILIZACAO.md) e
[acompanhamento](P2D05_REQUALIFICACAO_ATUAL.md).
Não redefine IDs canônicos, requisitos ou critérios de aceitação.

## Diagnóstico de entrada e fronteira

DIAG-LANG-01: selecionar a Caneta depois de ativar português cria a ferramenta
em inglês; CanvasView.set_tool não aplica o idioma corrente. DIAG-STATUS-02:
erro recuperável longo fica cortado em 1280x720, sem controle de detalhes no
ramo STATUS. Ambos reproduzidos na base limpa por eventos Qt reais.

Produção permitida: `src/ui/canvas_view.py` somente na instalação do idioma
da ferramenta; `src/ui/error_presentation.py` e novo
`src/ui/p2d05_status_notice.py` somente para apresentação persistente,
quebra de texto, detalhes/cópia seguros, foco, teclado e descarte explícito.
Testes: novo `tests/test_p2d05_status_notice.py`; testes existentes somente
se estritamente necessário ao comportamento autorizado, sem enfraquecimento.
Evidências: scripts de coleta locais e novos artefatos deste lote;
documentos vivos, índice ativo e manifesto vivo pelo gerador oficial.

Proibido: matemática Bézier, handles, amostragem, validação de polígonos,
comandos, histórico, schemas, persistência/exportadores, dependências, CI,
thresholds, golden images, snapshots, arquivos untracked preexistentes,
históricos privados e commits de outras branches.

Impacto: geometria de domínio G=0; V muda apenas durante apresentação de erro
e consulta de detalhes, com crescimento vertical controlado do rodapé; B
limitado a idioma, consulta/cópia/descarte e foco, sem mutação de documento.
Riscos: rodapé consumir viewport; aviso obsoleto; foco/atalhos; vazamento em
clipboard; ferramentas adaptadoras sem callback. Proteção por testes de
resolução, substituição/descarte, retorno ao fluxo e redaction.
Sem migração de dados. Formatos e integrações de engines não são alterados;
essa fronteira deve ser conferida no diff, sem reivindicar nova prova de runtime.

## Plano de verificação e encerramento

1. Regressões Qt que falham na base para idioma e acesso legível aos detalhes.
2. Correção mínima, testes por mouse e teclado, foco, resolução, redaction,
   preservação de nós/modelo/histórico, fechamento válido e Undo/Redo.
3. Estática, suíte Windows oficial/cobertura, integridade e empacotamento
   aplicáveis; falhas anteriores preservadas, sem mudar thresholds.
4. Pacote com patch completo, arquivos novos, ambiente, logs e hashes;
   capturas Qt reais, sem aprovação visual automática.
5. Revisão do diff e solicitação de PRECOMMIT ACCEPT. Depois: commit,
   requalificação do SHA limpo e ciclo remoto autorizado; sem merge automático.

Rollback: reversão específica do lote sobre 4b873c3, nunca reset destrutivo,
remoção de evidências ou reescrita de história. O merge documental anterior
fica preservado. Status de implementação, gates e revisão ainda não concluídos.

## Resultado local R2 — 2026-09-05 — pré-commit

Árvore Git testada: `304364ef466bd1c5bf005b7c579557a940911b29`, sobre a
base `4b873c39736477652d3b71a841bba7f9bf41cfad`. Não é um commit limpo.
Após os testes, somente documentos vivos e manifesto recebem este resultado;
produção/testes permanecem com os mesmos bytes. O pacote de revisão contém
as árvores testada e final, snapshots completos, patch e índices de hashes.

Suíte Windows oficial, sem filtros: 195/195 arquivos, 1.970 casos,
1.968 aprovados, zero falhas/erros, dois skips. Retorno 0; início UTC
2026-09-05T07:42:58.816619+00:00; duração 478,516 segundos.
Log `full-windows.log`: 17.788 bytes, SHA-256
`a3e71b9981aa1f9db5e5ab80419903c2dd4c49e3c45255fab137b7d065cbab94`.
Cobertura: 24.301/26.204 linhas (92,74%) e 6.764/7.942 branches (85,17%);
política global e por módulo PASS, sem alterar limites. Os 30 testes focados
também passaram, classificados DIAGNOSTIC_ONLY, não substitutos da suíte.

PASS local: compileall, flake8, Black (368 arquivos), isort, mypy
(148 arquivos de produção), pip-audit, Bandit, Stage 4B.5, lock estrito,
Poetry sync sem dependências a instalar/atualizar, baseline (3.258 arquivos,
união sem remoções) e integridade de evidências (135 manifestos rastreados).
pip-audit não audita o próprio projeto, ausente do PyPI; não é auditoria
integral da aplicação. Stage 4B.5 não comprova FPS/runtime de engines.

Runner legado formal: FAIL, retorno 1, única mensagem de bloqueio:
`historical runner did not execute from a clean tree`. Preservados
15 exact, 11 changed, 12 missing, 27 casos resolvidos pelo contrato atual;
42 testes substitutos aprovados. Isso não aprova o gate legado no patch.
Build/smoke/ZIP executável: não executados; exigem árvore limpa, sem bypass.

Skips: `test_plan_rejects_symlink_escape` e
`test_plan_rejects_symlink_destination`, ambos por WinError 1314 local.
Responsável: manutenção do projeto/validação CI Windows. Condição de remoção
da pendência: ambos passarem sem skip no SHA candidato exato em ambiente
habilitado. O PASS de 35727d9 e o VMware histórico não são transferidos.

Dez PNGs reais em 1280x720/1920x1080: rejeição preservada, detalhes seguros,
triângulo válido, Undo e Redo, com entradas/hash/tamanho e saída Qt normal.
Inspeção do agente concluída; inspeção humana PENDING_EVIDENCE. Qt offscreen
e fontes reais carregadas explicitamente; fallback CPU/CuPy ausente declarado.
Não comprova diálogos nativos, descoberta de fontes, GPU, DPI alternativo,
fluxo geral de salvar/reabrir/exportar nem conformidade global da UI.

Artefatos privados locais no workspace principal:
`build/p2d05-qualification/lang-status-precommit-r2/`, incluindo
`REVISAO_PRECOMMIT.md`, recibos, JUnit, cobertura e capturas. R1/falhas ficam
preservados e incluídos no pacote final de revisão; não são prova da R2.
Esses artefatos ainda não estão versionados como qualificação de um SHA.

Próximo ponto: revisão do pacote e aceite explícito P2D-05 PRECOMMIT ACCEPT
do lote exato; depois commit, todos os gates em checkout limpo, build/smoke,
evidências vinculadas ao SHA, revisão humana e CI remoto autorizado.
Não há aceite humano automático, merge da PR, tag ou release autorizado.
