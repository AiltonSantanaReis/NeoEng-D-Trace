# Etapa 9 - Responsividade e DPI

Status: **AUTOMATED PASS / HUMAN REVIEW PASS / ETAPA NAO ENCERRADA**

Este registro documenta a execucao local da Etapa 9 do plano
"docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md". O plano e as
politicas de governanca continuam sendo a fonte normativa; este arquivo e uma
evidencia da execucao, nao uma alteracao de criterio.

## Escopo validado

| Resolucao logica | Modo |
|---:|:---|
| 1280x720 | compacto |
| 1366x768 | compacto |
| 1920x1080 | desktop |

Escalas Qt executadas em processos independentes: 100%, 125%, 150% e 200%.
Para cada escala foram exercitadas as tres resolucoes e os estados de captura
do editor principal, incluindo projeto/paineis, gizmo e validacao, alem do
editor de cenario usado pelo auditor funcional.

## Comandos reais

$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_stage9_responsive_dpi_matrix.py tests\test_ui_responsive_layout.py tests\test_stage9_functional_ui_audit.py --tb=short
.\.venv\Scripts\python.exe scripts\audit_stage9_responsive_dpi.py --output <diretorio-local-de-saida>
.\.venv\Scripts\python.exe -m pytest -q --disable-warnings --cov=src --cov-branch --cov-report=xml:coverage-stage9-20260823.xml --tb=short
.\.venv\Scripts\python.exe tools\check_coverage_policy.py coverage-stage9-20260823.xml

## Resultados

- Testes focados: **12 passed**.
- Suíte completa: **1647 passed, 2 skipped**, em 62.21 s na execucao com cobertura.
- Cobertura total: **92.97% linhas / 85.00% branches**.
- "tools/check_coverage_policy.py": **PASS**.
- Worker DPI 100%: **PASS**.
- Worker DPI 125%: **PASS**.
- Worker DPI 150%: **PASS**.
- Worker DPI 200%: **PASS**.
- Cada worker: dimensoes, widgets criticos, abas, acoes funcionais, geometria visual e auditoria de PNG: **PASS**.
- Auditoria visual automatizada: "finding_count=0" em cada worker.
- Transparencia, hashes, clipping, overlap, paleta e areas anotadas foram processados pelo auditor de artefatos.
- O PNG fisico foi comparado com "dimensao logica x devicePixelRatio"; a geometria Qt logica foi validada separadamente.

## Alteracoes justificadas por achados

1. O auditor funcional passou a validar a dimensao fisica do PNG usando o
   "devicePixelRatio" real do "QPixmap", sem confundir captura fisica com
   geometria logica.
2. O agregador Stage 9 valida simultaneamente "actual_window_size" logico e
   "actual_capture_size" fisico.
3. O agregador valida a aba ativa e a existencia/geometria das quatro paginas
   ("Objects", "Layers", "Groups", "Collision"); paginas inativas nao sao
   classificadas como ausentes.
4. A geometria de overlap ignora apenas toolbars legadas que estao realmente
   invisiveis; nenhum widget foi removido do auditor.
5. Em modo compacto, a toolbar de referencia usa "IconOnly", largura de busca
   limitada e texto reduzido de "Focus", evitando compressao observada.
6. O HUD deixa de usar largura fixa menor que seus controles.
7. A rail de ferramentas e o botao de menu receberam dimensoes minimas
   compativeis com o QSS medido.

## Evidencia e hashes

Pacote versionavel:

"docs/evidence/artifacts/stage9-responsive-dpi-local-20260823/"

Arquivos principais:

- "stage9-responsive-dpi-report.json"
- "stage9-responsive-dpi-report.md"
- "artifact-index.json"
- "dpi_100/", "dpi_125/", "dpi_150/", "dpi_200/"
- "coverage-stage9-20260823.xml"

SHA-256 calculados apos a execucao:

- "stage9-responsive-dpi-report.json":
  "54EB2532719648DF4C39895D5F3FF94E58386CB780A98D94DF7BC03CECC59980"
- "artifact-index.json":
  "63BBA5A77189FE9F5703ADDEB9AF7290F8A7B9137AF50FE93BE5DC61A9A7DC08"
- "coverage-stage9-20260823.xml":
  "FC36A25D2FEC9D3D1C2BE0D06FBDED459860A11AA6313EDCCAF240D8A319FBCE"

O relatorio preserva a proveniencia: commit-base
"c425fa53ab607d7ac1d73171b55786ffd3b65186", branch "main" e
"worktree_clean=false" no momento da execucao. Esse estado nao foi mascarado.

## Advertencias preservadas

Os workers registraram duas mensagens por execucao do caminho GPU do OpenCV:
o processamento GPU falhou e houve fallback para CPU por erro de argumento em
"cv2.merge". A advertencia foi mantida nos "worker.stderr.log". Ela nao foi
transformada em PASS silencioso nem tratada como falha de layout; requer
avaliacao separada se o objetivo for corrigir o caminho GPU.

## Revisao visual humana

Em 2026-08-23, o proprietario aprovou a revisao visual das capturas PNG
originais da matriz. A aprovacao nao foi inferida pelo auditor automatico e
nao usa a prancha JPEG compacta como evidencia de nitidez. A prancha foi
somente um auxiliar de navegacao; os arquivos originais permanecem no pacote
hashado em dpi_100/, dpi_125/, dpi_150/ e dpi_200/.

Escopo aprovado: legibilidade, clipping, sobreposicao entre canvas e paineis,
acessibilidade visual das abas, proporcao do gizmo, toolbars, menus e
consistencia da paleta nas tres resolucoes e quatro escalas DPI.

Registro: HUMAN_REVIEW_PASS confirmado pelo proprietario nesta execucao.

## Limites e pendencias

- A revisao visual humana foi registrada como **PASS** pelo proprietario. O
  PASS automatizado, isoladamente, nao provaria legibilidade, equilibrio
  visual ou aparencia profissional.
- O worktree estava sujo por alteracoes da Etapa 9 e artefatos locais
  preexistentes; isso nao foi usado para aprovar a etapa.
- CI, commit, push, PR, merge e validacao pos-merge ainda nao foram executados
  para este checkpoint.
- A Etapa 9 somente podera ser encerrada apos revisao humana registrada,
  documentacao reconciliada, validacao em arvore adequada, CI aprovado e ciclo
  Git autorizado conforme as politicas vigentes.