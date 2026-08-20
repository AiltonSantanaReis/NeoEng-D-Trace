# Evidência — Etapa 1: encerramento pós-merge

## Identificação

- Etapa: runtime base determinístico.
- PR: `#113`.
- Commit candidato validado: `795a59d8da8b84546186011081c127b9d7b2cd5c`.
- Merge: `84dfee76c45b0611f73332a679de0985f1dfd990`.
- Branch pós-merge validada: `main`.
- Branch temporária da auditoria reproduzível: `Ailton/close-runtime-base-phase1-postmerge`.
- CI: workflow `Private validation`, run `32362255134` (`350`).
- Referência do CI: [execução 350](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/32362255134).
- Data/hora da auditoria pós-merge: `2026-08-20T11:25:56+00:00`.

## Objetivo e escopo

Confirmar, após o merge, que o runtime base determinístico e a reconciliação do
gate global permanecem íntegros no `main`. Esta etapa cobre o host versionado,
fixed-step, ciclo de vida, cancelamento, capacidades/fallback e ativação
transacional. Não cobre runtime completo de engine nem efeitos gráficos.

## Gates remotos

O CI `32362255134` foi concluído com sucesso nos dois jobs obrigatórios:

- Linux: sucesso em baseline, evidências, lint, formatação, isort, tipos,
  dependências, riscos, cobertura, política integrada, auditoria de qualidade e
  árvore-fonte.
- Windows: sucesso nos mesmos gates, incluindo cobertura Windows, suíte legada,
  verificação da árvore e armazenamento da evidência.

O CI passou sem alteração de regras, sem bypass, sem `skip` novo e sem force.

## Validação pós-merge reproduzível

Auditoria executada no commit de merge `84dfee7` com worktree limpo:

- Focados: `70 passed`.
- Suíte completa: `1421 passed, 2 skipped`.
- Baseline: `1662 files` verificados.
- Integridade de evidências: `63 manifests validated`.
- Gate staged final após a inclusão deste pacote: baseline com `1673 files` e
  `64 manifests validated`.
- Black, Flake8, mypy, `py_compile` e `git diff --check`: aprovados.

## Artefatos

O pacote integral está em
`docs/evidence/artifacts/runtime-base-phase1-postmerge-2026-08-20/`.

- `runtime-base-report.json`: 2676 bytes; SHA-256
  `756d4e15ca52f62375fc6498db191752e0450ea8d5dd2b4e0d52e9b2df430e65`.
- `artifact-index.json`: 1261 bytes; SHA-256
  `c12fc800fb4fe37f6df43950610a95a5c65bd531bc6b617ece2d7749a8e680fe`.
- O índice registra bytes e SHA-256 de cada log gerado pela auditoria.

## Reconciliação documental

Os documentos `ETAPA_1_RUNTIME_BASE_2026-08-20.md` e
`RECONCILIACAO_GATE_GLOBAL_2026-08-20.md` permanecem preservados como registros
pré-merge e não foram reescritos. Este documento é a fonte viva do encerramento
pós-merge e substitui o estado `BLOQUEADO` daqueles snapshots para o estado
atual do projeto.

## Limitações e riscos residuais

Continuam fora do escopo desta etapa: iluminação, partículas, shaders,
pós-processamento, triggers, streaming, GPU/VRAM/driver/FPS específicos e
runtime completo de engine. Esses itens permanecem planejados para etapas
posteriores e não são declarados resolvidos por este fechamento.

## Decisão

**APROVADO — Etapa 1 concluída formalmente no escopo aprovado, após CI e merge.**

Esta decisão não aprova release comercial nem altera os gates das etapas futuras.
