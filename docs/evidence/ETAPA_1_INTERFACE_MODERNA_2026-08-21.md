# ETAPA 1 - INTERFACE MODERNA: TOKENS E TEMA CONTROLADO

Data da execucao local: 2026-08-21

## Estado da evidencia

**PASS_LOCAL / AGUARDANDO CI E VALIDACAO POS-MERGE**

Este documento registra a implementacao e a validacao local da Etapa 1 do plano
de Interface Moderna e Profissional. Ele nao declara a etapa formalmente
encerrada antes do ciclo de commit, push, PR, CI e validacao pos-merge.

## Escopo implementado

- Criacao de `src/ui/theme_tokens.py` como fonte semantica e imutavel dos
  tokens de fundo, superficie, borda, texto, destaque, selecao, foco, erro,
  aviso e sucesso.
- Geracao controlada do QSS em `src/ui/theme_qss.py`, sem depender de tema
  externo e sem cores laranja fixas.
- Estados hover, pressed, checked, disabled e focus visiveis e derivados dos
  tokens.
- Remocao dos estilos inline da chrome da aplicacao em `src/ui` e
  `src/tools`; os menus e botoes passam a usar o QSS central.
- Atualizacao do auditor visual para paleta contextual: modal nao e obrigado a
  renderizar cores de paineis que nao pertencem ao seu estado; tokens
  interativos precisam aparecer em pelo menos um estado nao modal.
- Teste especifico para impedir regressao da regra de paleta contextual.

Cores de cena, gizmo e overlays permanecem semanticas do conteudo e nao foram
substituidas por tokens de chrome nesta etapa.

## Evidencias reais

Artefatos finais:

- `docs/evidence/artifacts/ui-modernization-stage1-final-20260821/raw-captures/`
- `docs/evidence/artifacts/ui-modernization-stage1-final-20260821/visual-audit/`
- `docs/evidence/artifacts/ui-modernization-stage1-final-20260821/stage1-baseline-report.json`
- `docs/evidence/artifacts/ui-modernization-stage1-final-20260821/stage1-baseline-report.md`
- `docs/evidence/artifacts/ui-modernization-stage1-final-20260821/artifact-index.json`

A captura real produziu 15 PNGs nos estados sem projeto, projeto com paineis,
validacao, modal de validacao e feedback do gizmo, nas resolucoes logicas
1920x1080, 1366x768 e 1280x720. O manifesto preserva tambem o tamanho fisico
observado pelo DPI local.

Auditoria visual automatica:

- Pillow e OpenCV: PASS.
- Dimensoes, transparencia e SHA-256: PASS.
- Clipping e geometria Qt: PASS.
- Sobreposicao de regioes: PASS.
- Paleta contextual e presenca agregada do destaque: PASS.
- PNGs anotados: gerados.
- Achados: 0.

Auditoria comparativa contra a baseline da Etapa 0:

- Capturas: 15.
- Deltas geometricos inesperados: 0.
- Deltas esperados: 12 registros, todos na redistribuicao horizontal entre
  `nav_toolbar` e `xray_toolbar`.
- A redistribuicao preserva altura e limite direito; qualquer outro delta faria
  o auditor falhar.
- Indice final: 38 arquivos, 0 divergencias de bytes ou SHA-256.

## Testes executados

- `.venv/Scripts/python.exe -m pytest -q tests/test_stage1_ui_theme.py tests/test_visual_artifact_auditor.py tests/test_repository_reference_hygiene.py --tb=short`
  - 13 passed.
- `.venv/Scripts/python.exe -m pytest -q --tb=short`
  - 1583 passed, 2 skipped.
- Black e isort nos arquivos novos e alterados de teste/auditoria: PASS.
- Flake8 nos modulos existentes tocados e nos novos tokens/testes: PASS.
- Mypy em `src/ui/theme_tokens.py` e `scripts/audit_stage1_ui_theme.py`: PASS.
- `git diff --check`: PASS.

Os dois skips da suite sao historicos e permanecem explicitamente reportados pelo
projeto; nao foram criados nem convertidos em PASS artificial nesta etapa.

## Integridade de evidencias e limitacao conhecida

`tools/evidence_integrity.py --git-blob` passou com 84 manifests no estado
versionado de referencia.

A execucao normal contra a arvore de trabalho foi reprovada por divergencias
de snapshots historicos que referenciam bytes antigos. Isso e reportado, nao
mascarado e nao foi resolvido reescrevendo historico. O modo Git-blob e o gate
adequado para validar os bytes versionados; apos o staging e o merge, o gate
foi repetido no `main` apos o merge contra os blobs do estado final.

## Revisao visual

A inspeccao das capturas reais confirmou que:

- o contraste do tema escuro e consistente;
- os botoes e paineis nao apresentam as linhas esmagadas da baseline;
- o canvas nao foi sobreposto pelos paineis;
- o gizmo e seu feedback permanecem dentro da area de visualizacao;
- o modal conserva foco visivel e texto legivel.

A revisao visual do agente nao substitui uma confirmacao independente do
proprietario quando essa confirmacao for exigida. Nenhum achado subjetivo foi
transformado em PASS automatico.

## Reconciliacao do gate de baseline

A segunda execucao do CI da PR #131 (`32530692607`, jobs Linux e Windows) falhou
legitimamente no passo `Verify clean baseline manifest`. A causa foi confirmada
nos logs: o manifesto continha 1214 entradas de cinco diretorios locais
`release-stage9-*` que estavam apenas como untracked no worktree e nao existem
nos blobs enviados ao GitHub. Nenhum desses diretorios foi removido ou alterado.

A correcao foi feita na origem, em `tools/baseline_integrity.py`: o baseline
passa a enumerar exclusivamente caminhos rastreados no indice Git (`--cached`),
pois o contrato `--git-blob` deve representar o repositorio versionado. Arquivos
untracked continuam sob o contrato de `evidence_integrity` e so entram no
baseline depois de serem explicitamente staged/versionados.

Foi adicionado o teste regressivo
`test_baseline_ignores_untracked_worktree_outputs`. Apos staging dos tres
arquivos de correcao e regeneracao contra os blobs staged:

- `Baseline verified: 1911 files`;
- `Evidence integrity passed: 84 manifests validated`;
- `1583 passed, 2 skipped` na suite completa;
- Black e Flake8 dos arquivos corrigidos: PASS;
- os cinco diretorios locais permanecem preservados e fora do commit.

Nao houve bypass, relaxamento de regra ou reescrita de snapshot historico.

## Encerramento pos-merge

A PR #131 foi mergeada normalmente em `main` no commit
`71b1c44313b28d3323e17dc14fbb58179d02eb74`, apos o CI `32532498310` aprovar os
jobs Linux `96927141129` e Windows `96927140823`.

A validacao pos-merge executada no `main` local sincronizado com `origin/main`
confirmou:

- `Baseline verified: 1911 files`;
- `Evidence integrity passed: 84 manifests validated`;
- `1583 passed, 2 skipped` na suite completa;
- `git diff --exit-code` sem divergencia na arvore rastreada.

Os cinco diretorios locais `release-stage9-*` permanecem preservados como
untracked e nao fazem parte do estado versionado. A Etapa 1 da interface
moderna profissional esta formalmente encerrada. A Etapa 2 nao foi iniciada.
