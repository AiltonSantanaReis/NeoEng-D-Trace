# Etapa 11 — comandos e painéis — Pacote 5

**Data:** 11 de agosto de 2026
**Base integrada:** `5e88c8d548e2b60612601f83e1bf24aeb91081bb`
**Base técnica do pacote:** `eed019ff8046d667988352df0aef93e129275919`
**Estado:** APROVADO LOCAL E NO CI PRÉ-MERGE / NÃO INTEGRADO
**Release:** NÃO APROVADA

## Objetivo e escopo

O quinto pacote cobre contratos transacionais de comandos e caminhos
observáveis dos painéis de camadas, grupos e objetos:

- rollback após exceção, resultado contraditório ou subcomando sem mudança;
- compensação de comando composto e restauração atômica de estado;
- rejeição de Undo/Redo com estado obsoleto ou relacionamento quebrado;
- entradas inválidas de camadas, grupos, polígonos e colisões;
- ações reais dos painéis Qt, mensagens de rejeição/falha e limites de lista;
- exportação real de máscara PNG em diretório temporário;
- prévia de forma, exportação de sprite e mudança bilíngue de controles.

Foram adicionados 21 testes em
`tests/test_stage_11_command_contract_branch_coverage.py` e 10 testes em
`tests/test_stage_11_ui_panel_branch_coverage.py`. Os testes usam `Scene`,
`CommandManager`, widgets Qt e NumPy reais. Doubles ficam restritos a diálogos,
falhas deliberadamente injetadas e fronteiras de gravação isoladas.

Não houve alteração em código de produção neste pacote.

## Resultados locais reproduzíveis

Ambiente executado: Windows 11, Python 3.11.9, pytest 9.1.1 e pytest-cov
7.1.0.

Comando focal:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_stage_11_command_contract_branch_coverage.py tests\test_stage_11_ui_panel_branch_coverage.py
```

Resultado final: `31 passed`.

Comando canônico integral:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term --cov-report=xml -q
```

Resultado antes do contrato documental deste pacote: `810 passed`, zero
falhas, zero erros e zero ignorados.

Métricas extraídas da base do `coverage.py` e confirmadas em `coverage.xml`:

| Métrica | Pacote 4 | Pacote 5 local | Variação |
|---|---:|---:|---:|
| Linhas | 10.007/11.628 — 86,06% | 10.257/11.628 — 88,21% | +250 cobertas |
| Ramos | 2.715/3.700 — 73,38% | 2.862/3.700 — 77,35% | +147 cobertos |
| Combinada | 83,00% | 85,59% | +2,59 pontos percentuais |

Cobertura por módulo diretamente priorizado:

| Módulo | Linhas antes | Linhas depois | Ramos antes | Ramos depois |
|---|---:|---:|---:|---:|
| `commands.py` | 905/1.051 — 86,11% | 993/1.051 — 94,48% | 283/404 — 70,05% | 358/404 — 88,61% |
| `groups_panel.py` | 148/199 — 74,37% | 199/199 — 100,00% | 28/48 — 58,33% | 47/48 — 97,92% |
| `layers_panel.py` | 95/125 — 76,00% | 124/125 — 99,20% | 26/40 — 65,00% | 38/40 — 95,00% |
| `side_panel.py` | 223/311 — 71,70% | 305/311 — 98,07% | 52/68 — 76,47% | 65/68 — 95,59% |

Os quatro módulos somam todas as 250 linhas novas e 119 dos 147 ramos novos.
Os 28 ramos restantes pertencem a dependências reais exercitadas pelas ações
dos painéis, sem novas linhas cobertas nesses módulos.

## Transparência sobre iterações de teste

A primeira execução da matriz de comandos teve cinco falhas. Os testes
mantinham referências a objetos anteriores ao rollback, mas o contrato restaura
as coleções por cópia profunda. As referências foram reobtidas da cena; uma
segunda execução encontrou uma referência residual e ela foi corrigida pelo
mesmo motivo. A matriz final aprovou 21 testes.

A primeira execução dos testes de painéis teve duas falhas do harness: a
contagem correta era sete mensagens críticas, não oito, e um método ainda
estava substituído por um stub quando se esperava exercitar a implementação
real. As expectativas e a restauração do método foram corrigidas. O conjunto
final aprovou 10 testes.

Os primeiros gates estáticos encontraram Black/isort pendentes, linhas longas
e dois imports não usados nos arquivos novos. As ferramentas oficiais foram
aplicadas e todos os gates passaram na repetição.

Uma coleta intermediária aprovou os 800 testes existentes, mas o encadeamento
terminou com erro ao pedir um relatório irrestrito que tentou reler um arquivo
temporário já removido por um teste. A execução canônica com `--cov=src`
eliminou essa interferência e aprovou os 810 testes atuais. Não houve falha de
produto nessa ocorrência, mas o desvio do comando foi preservado aqui.

Durante a inspeção do CI, a primeira versão do auditor recursivo classificou
conteúdo de ZIPs históricos como documentos atuais. Uma segunda versão ainda
comparou 27 documentos históricos aninhados com versões atuais. O escopo foi
corrigido para distinguir o arquivo histórico de seu conteúdo interno; a
passagem final comparou os 50 documentos vigentes e encontrou zero divergências
canônicas. Os resultados incorretos das duas passagens não foram usados para
aprovar o CI.

## CI documental final do Pacote 4 auditado

O workflow `31482204331` executou sobre o HEAD
`eed019ff8046d667988352df0aef93e129275919`.

- Windows: job `93749506308`, artefato `9097746392`, SHA-256
  `73ec7f6d120f5047c32b7928cf6afb43247bca9523ed3393ace9f1208d5efdca`;
- Linux: job `93749506393`, artefato `9097708858`, SHA-256
  `3b7bf99d184cbae76083c89a983d5c3ca985ed275ee8e872367486cb7710851d`;
- merge sintético `0bfab191dc00dc8c60f479ed75e3ec42575767bb`, com pais base
  `5e88c8d548e2b60612601f83e1bf24aeb91081bb` e fonte
  `eed019ff8046d667988352df0aef93e129275919`;
- `779 passed` nos dois sistemas, cobertura exata `10.007/11.628` linhas e
  `2.715/3.700` ramos, baseline 310 e legado `27/27` reconciliado;
- 56 arquivos externos, 50 evidências, 1.415 payloads recursivos e 327
  checksums internos, sem violações ou divergências canônicas;
- 44 diferenças textuais brutas limitaram-se a CRLF no checkout Windows;
- zero anotações nos dois jobs.

A primeira exibição da contagem de arquivos extraídos informou zero por falta
de espaços em dois argumentos PowerShell. O download, os hashes e a extração
haviam sido concluídos; a contagem corrigida confirmou 54 arquivos Windows e
2 Linux. O resultado incorreto não foi usado para aceitar o CI.

Esse CI anterior foi **ACEITO**.

## Portões complementares locais

Foram aprovados no commit técnico:

- suíte oficial: `810 passed`, zero falhas, erros ou ignorados;
- Black, isort e Flake8 no escopo integral;
- mypy: zero erros em 70 arquivos fonte;
- `poetry check --lock --strict` e compilação integral;
- auditoria de dependências: nenhuma vulnerabilidade conhecida; o pacote local
  editável foi ignorado por não existir no índice público;
- Bandit: zero achados de alta severidade;
- suíte legada: 196 testes, 27 falhas históricas exatamente reconciliadas,
  zero inesperadas, ausentes, erros ou ignorados;
- baseline: 312 arquivos verificados;
- higiene de referências rastreadas, arquivos novos e arquivos aninhados:
  aprovada.

## CI técnico do Pacote 5 auditado

O workflow `31483687046` executou sobre o HEAD fonte
`07c5b78b4fc7e17676dcb42b4048f1a91273fd68`.

- Windows: job `93754111444`, artefato `9098343972`, SHA-256
  `b28c554b1e040ea968e958df5a87d44cd07144ca31179691402b3a72f07eddeb`;
- Linux: job `93754111445`, artefato `9098267096`, SHA-256
  `efd92d0ebffb0f8f53203fffe4db39e885da9c30dc0b8d72a3f5634a153def57`;
- merge sintético `4e7e12a0156c9d67d22482fd415ed06e075911e8`, com pais base
  `5e88c8d548e2b60612601f83e1bf24aeb91081bb` e fonte
  `07c5b78b4fc7e17676dcb42b4048f1a91273fd68`;
- `810 passed` nos dois sistemas, com cobertura semanticamente idêntica:
  `10.257/11.628` linhas e `2.862/3.700` ramos;
- hash semântico integral dos XMLs idêntico:
  `165c512eb586bf9f964cb57e393f0ec246481014f29f6b8dde135bf472a6bd1c`;
- legado Windows: schema v4, 196 testes, reconciliação `27/27`, zero
  inesperadas, ausentes, erros ou ignorados, HEAD fonte correto e árvore limpa;
- 56 arquivos externos, 50 evidências e 1.415 payloads recursivos inspecionados;
- 327 checksums internos validados; zero referências proibidas, caminhos
  pessoais, caminhos inseguros, membros duplicados ou divergências de checksum;
- 44 evidências textuais diferiram dos blobs somente por CRLF no checkout
  Windows; após normalização canônica, as 50 coincidiram com o commit;
- zero anotações nos dois jobs; PR `#45` aberta, draft e com mergeability limpa.

O CI técnico do Pacote 5 foi **ACEITO** após inspeção. Isso não comprova
integração, CI pós-merge, encerramento de `R-003`, conclusão da Etapa 11 nem
release.

## Riscos e decisão

- `R-003` permanece **ABERTO**: as metas globais de 90% de linhas e 85% de
  ramos ainda não foram atingidas.
- Faltam, no mínimo, 209 linhas e 283 ramos cobertos para alcançar as metas
  com o denominador atual.
- `magnetic_lasso.py`, `pen_tool.py`, `main_window.py`, `scene.py` e
  `polygon_edit_tool.py` concentram os maiores déficits seguintes.
- O CI pré-merge técnico do Pacote 5 foi aceito; integração e CI pós-merge
  não existem.
- A Etapa 11 está **EM ANDAMENTO** e a release permanece **NÃO APROVADA**.

## Marcadores auditáveis

```text
BASE_COMMIT=5e88c8d548e2b60612601f83e1bf24aeb91081bb
PACKAGE_BASE_COMMIT=eed019ff8046d667988352df0aef93e129275919
TECHNICAL_COMMIT=07c5b78b4fc7e17676dcb42b4048f1a91273fd68
LOCAL_TESTS_PASSED=810
LOCAL_LINES_COVERED=10257/11628
LOCAL_BRANCHES_COVERED=2862/3700
MODULES_BELOW_30_LINES=0
MODULES_BELOW_30_BRANCHES=0
PRE_MERGE_CI_RUN=31483687046
PRE_MERGE_CI_STATUS=ACCEPTED
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
