# Lote corretivo da Caneta — alças explícitas e fechamento

ID: PEN-HANDLES-20260905. Estado: IN_PROGRESS.
Base: `5b3e6b15cee93ef5c9d1d550745293fb8372b5b9`.
Branch: `Ailton/pen-handles-quantization-20260905`.

## Autorização, precedência e escopo

Em 05/09/2026, o proprietário solicitou: “O próximo trabalho é corrigir a
geração das alças/quantização em lote próprio, preservando a validação de
polígonos realmente inválidos.” Essa autorização abre este lote geométrico,
separado da fronteira somente de idioma/status do lote anterior.

Aplicam-se [governança](GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md),
[qualidade/evidências](POLITICA_QUALIDADE_E_EVIDENCIAS.md),
[plano mestre](PLANO_MESTRE_ESTABILIZACAO.md) e
[contrato de erros](CONTRATO_APRESENTACAO_ERROS_P2D05_2026-09-04.md).
O protocolo de revisão PRECOMMIT do projeto permanece aplicável ao patch
exato; autorizar implementação não é aceite humano do resultado.
Este lote não encerra P2D-05 nem transfere CI/C12 dos pais.

## Diagnóstico de entrada

Na fonte-base limpa, os pontos (225,35), (285,35), (285,95) geram alças
automáticas. A amostra flutuante é simples, mas a conversão inteira produz
(281,35), (283,35), (285,35), (283,35), (281,37) na quina.
O retorno sobre uma aresta anterior leva à rejeição canônica correta da
amostra inválida. O defeito de interação é a própria ferramenta introduzir
esse retorno sem que o usuário tenha pedido alças.

Os casos de 40/60 px foram rejeitados; 80/100 px foram aceitos. A prova é
numérica DIAGNOSTIC_ONLY, não uma execução nativa do executável.
O executável identificado pelo proprietário pertence a `6ede2f6`; hash e
tamanho conferiram com o manifesto. A fonte-base posterior também reproduz
o mecanismo acima. A geometria exata da captura não foi recuperada.

## Contrato de interação e impacto

- Clique simples acrescenta ponto de canto, com controles coincidentes com
  sua âncora; acrescentar outro ponto não altera alças anteriores.
- Clique e arraste no novo ponto define alças de entrada/saída opostas,
  com atualização apenas enquanto o gesto está ativo.
- Fechamento no primeiro ponto usa os controles explícitos e o comando
  transacional já existente; uma criação aceita gera uma entrada de histórico.
- Rejeições continuam no canal STATUS P2D-05 e preservam o desenho e modelo.
- Cancelamento, soltura, troca de ferramenta e histórico não podem deixar
  uma alça sendo arrastada por um movimento posterior sem botão pressionado.

A distinção entre clicar para segmentos retos e arrastar para alças é uma
referência de interação, não alegação de equivalência integral com Illustrator:
[documentação primária Adobe](https://helpx.adobe.com/uk/illustrator/using/tool-techniques/pen-tool.html).

G/B mudam somente para novos gestos da Caneta: elimina-se a criação de
tangentes implícitas. V muda na prévia correspondente aos controles pedidos.
Curvas persistidas mantêm controles, amostragem, bytes e histórico de edição.
Não se altera quantização global para aprovar polígonos inválidos, não se
repara silenciosamente geometria e não se relaxa o validador.

## Fronteira declarada antes da implementação

Produção: `src/tools/pen_tool.py`, criação/soltura/cancelamento de alças e
roteamento do fechamento; texto de ajuda já existente da Caneta, se necessário
para tornar o gesto descobrível. Nenhum novo painel, QAction ou atalho.

Testes: novo `tests/test_pen_creation_gestures.py`; atualização justificada
do caso de 60 px em `tests/test_functional_user_flows.py` e de expectativas
atuais que dependiam das alças automáticas. Preservar os casos de rejeição
por área zero, sobreposição e auto-interseção; nunca apagar testes históricos.

Documentos: este registro, entradas novas nos documentos vivos/índice ativo,
novo relatório e artefatos de evidência, manifesto vivo pelo gerador oficial.

Protegidos: `src/core/bezier_geometry.py`, `src/core/polygon_validation.py`,
`src/models/scene.py`, comandos, persistência, exportadores, schemas, limites,
dependências, CI, thresholds, snapshots e toda a pasta `quality/legacy_tests`.
Se surgir necessidade comprovada de mudar essa fronteira, registrá-la antes
de continuar; não converter uma falha do validador em aprovação por exceção.

## Verificação planejada e rollback

1. Regressões que falham na base, por eventos Qt no CanvasView real.
2. Fechamento em tamanhos variados, ambos os sentidos e zooms; alças explícitas
   preservadas ao adicionar pontos; soltura, cancelamento e duplo clique.
3. Rejeição de degenerados, cruzamentos e sobreposições sem mutação; histórico,
   salvar/reabrir e exportação dos contornos criados.
4. Suíte Windows integral/cobertura, estática, segurança, integridade e Stage
   4B.5 aplicáveis; artefatos novos e falhas anteriores preservados.
5. Pacote pré-commit revisável com escopo, hashes, patch e arquivos novos.
6. Após aceite do patch exato: commit, qualificação limpa, build/smoke e CI
   conforme autorização; revisão nativa/humana antes da aprovação de produto.

A sessão nativa continua bloqueada pelo sandbox na entrada deste lote.
Qt offscreen é teste de integração, não prova de cliques do SO na build.
Build oficial e runner legado requerem árvore limpa; não serão contornados.
Rollback: reversão específica do futuro commit deste lote sobre `5b3e6b1`,
preservando arquivos locais, snapshots, branches e commits anteriores.

## Resultados observados — atualização 05/09/2026

O worktree candidato permanece sem commit sobre a base declarada.

- DIAGNOSTIC_ONLY vermelho da base: 33 failed, 3 passed, no novo contrato
  de eventos; os três casos de geometria realmente inválida passaram. Recibo:
  build/pen-handles-qualification-20260905/red-r1/.
- Candidato após a correção: 69 passed nos testes Qt do lote, nos fluxos
  funcionais relacionados e na cobertura de branches da Caneta. Recibo:
  build/pen-handles-qualification-20260905/green-r4/.
- Suíte completa sem filtros no worktree sujo: 2016 passed, 2 skipped,
  1 failed. A única falha é test_p2d05_status_notice.py::... [pt],
  causada por um QMessageBox modal residual; a mesma falha foi reproduzida
  no worktree limpo da base 5b3e6b1. Recibos: full-pytest-r1/ e
  full-pytest-r2/. Esse resultado é FAIL diagnóstico herdado, não pode
  ser atribuído à correção nem promovido a PASS.
- Compilação, Flake8, Black, isort e mypy passaram no worktree candidato.
- Baseline Git-blob e integridade de evidências passaram no índice staged,
  respectivamente com 3261 arquivos e 135 manifestos. Isso é uma verificação
  de pré-commit, não uma qualificação de SHA limpo.
- Runner oficial com cobertura, Stage 4B.5, segurança, gate legado, build
  portátil, CI remoto e auditoria nativa ainda não foram executados para um
  SHA limpo deste lote.

Estado controlado: IN_PROGRESS / PRECOMMIT_PENDING. Nenhum gate global deste
patch foi declarado aprovado; não há novo aceite C12, commit, push, merge,
tag ou release.
