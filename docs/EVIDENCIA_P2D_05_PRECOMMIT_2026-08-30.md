# Evidência P2D-05 — revisão PRECOMMIT O-1

**Fase:** O-4 — revisão de fronteira e artefatos antes da consolidação
**Status:** `PRECOMMIT REVIEW PASS — AUTORIZAÇÃO PARA STAGE/COMMIT PENDENTE`
**Data:** 30/08/2026 (UTC-03)
**Branch:** `p2d-05-quality-hardening`
**HEAD:** `fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3`
**Rollback técnico:** `f55b07b85ef2cf65160f2c10ffac5e63b45732ac`

Este registro documenta a revisão local PRECOMMIT. Nenhum `git add`, commit,
push, tag, merge ou release foi executado. A aprovação técnica desta revisão
não substitui o aceite explícito para staging e commit.

## 1. Fronteira verificada

Não há arquivos staged. A árvore tracked possui exatamente 14 arquivos
modificados, todos dentro do conjunto P2D-05 hardening + O-1 previamente
registrado:

- `docs/DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md`;
- `docs/PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md`;
- `src/core/logger.py`;
- `src/core/scene_authoring_session.py` — O-1;
- `src/exporters/scene_authoring_export.py`;
- `src/persistence/scene_authoring_io.py`;
- `src/ui/scenario_authoring_actions.py`;
- `src/ui/scenario_editor_window.py`;
- `src/ui/scenario_panel.py`;
- `src/ui/scene_asset_panel.py`;
- `src/ui/scene_authoring_group_stack.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/ui/scene_authoring_layer_stack.py`;
- `src/ui/scene_authoring_viewport.py`.

Resultado da comparação com a fronteira esperada: `14/14`, zero arquivo
inesperado e zero arquivo faltante. `git diff --check` passou; os avisos de
conversão CRLF/LF em três arquivos são os line endings já conhecidos e não
representam erro de conteúdo.

Os arquivos novos relacionados ao lote continuam untracked e não foram
selecionados automaticamente. Entre eles estão o classificador
`src/persistence/p2d05_errors.py`, os testes e scripts de O-1, as decisões e
evidências P2D-05 e os JSONs sob `artifacts/p2d05/`. A seleção exata desses
arquivos será feita somente em uma operação de staging autorizada. O script
bruto da experiência rejeitada `scripts/benchmark_p2d_05_o1_gesture.py` foi
preservado para auditoria e permanece explicitamente fora do conjunto de
reprodutibilidade aprovado. Nenhum untracked foi removido ou limpo.

## 2. Gates executados

| Gate | Resultado |
|---|---:|
| testes focais O-1, P2D-05 e gestos | `27 passed` |
| suíte completa | `1863 passed, 2 skipped, 1 warning` |
| `py_compile` | `PASS` |
| `black --check` nos fontes/scripts O-1 | `PASS` |
| `isort --check-only` | `PASS` |
| `flake8` | `PASS` |
| `mypy src/core/scene_authoring_session.py` | `PASS` |
| `bandit src/core/scene_authoring_session.py` | `PASS` |
| auditor P2D-05 | `PASS`, `mapping_errors=0` |
| privacidade dos fontes/evidências auditados | `0 hits` |
| staged inesperado | `0` |

A única advertência da suíte é a depreciação conhecida do construtor de
`QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py`. Não houve
falha ou erro de teste.

## 3. Integridade dos artefatos O-0/O-1

- `calibration-o0-20260830.json`: `PASS`, 8 workloads, zero erros;
- `calibration-o1-final-20260830.json`: `PASS`, 8 workloads, zero erros;
- cena: determinismo `8/8` e memória completa `8/8`;
- generic, Godot e Unity: determinismo `8/8` em cada destino;
- comparação O-0/O-1 de hashes de cena e exportações: zero deltas;
- `o1-gesture-finish-ab-20260830.json`: `PASS`, 8 workloads, zero erros;
- reprodução pós-formatação
  `o1-gesture-finish-ab-precommit-20260830.json`: `PASS`, 8 workloads, zero
  erros, no HEAD atual;
- `audit-precommit-final-20260830.json`: `PASS`, 25 limites, 2 formatos, 11
  classificadores de erro e zero mapeamentos inválidos;
- fingerprints de produto, teste e benchmark: conferidos contra os arquivos
  atuais; todos coincidem.

A experiência incremental de preview que foi rejeitada permanece preservada em
`o1-gesture-ab-20260830.json`; ela mostrou regressão de 13,36% a 32,18% e não
foi incorporada. O-1 não declara preview otimizado e não altera o caminho de
preview.

## 4. Limites de interpretação

O-1 altera somente a representação do histórico de transforms e a finalização
de gestos em `src/core/scene_authoring_session.py`. Não houve alteração de
schema, formato, coordenadas, exportadores, preview, UI, geometria ou
semântica de produto. Por isso não foi gerada uma nova captura visual
específica de O-1; as capturas e auditorias Windows do hardening P2D-05
permanecem como evidência anterior e não são apresentadas como nova evidência
visual do O-1.

O resultado `PASS` desta revisão significa que a fronteira e os artefatos estão
aptos para a decisão de staging. Não significa que O-1 ou P2D-05 estejam
formalmente fechados, nem autoriza commit ou publicação.

## 5. Próxima decisão obrigatória

Solicitar explicitamente autorização para selecionar os arquivos do lote e
executar o commit. Antes do commit, repetir a prova de staged e a verificação
do conjunto selecionado; depois do commit, executar a requalificação
pós-commit prevista pelo contrato. O-2 e O-3 permanecem pendentes.
