# Evidência — Cobertura dos módulos críticos

## Identificação

- base integrada: `f700db3fbb2c92ec1d3d9dd8d1f911537269da30`;
- commit técnico: `4f53a0d7df25ba6de7b2dd5759b4abc4be5e5b5e`;
- data: 10 de agosto de 2026;
- sistema: Windows 11;
- Python: 3.11.9;
- dependências: `poetry.lock` vigente;
- estado: **APROVADO LOCALMENTE / NÃO INTEGRADO**.

## Objetivo e método

Elevar cobertura por testes comportamentais, negativos e Qt offscreen nos
módulos que estavam abaixo de 30%, sem remover testes, excluir linhas ou
reduzir o piso do CI. O launcher foi reservado para a matriz integral da
Etapa 7, onde argumentos, saídas e códigos serão avaliados em conjunto.

## Cobertura antes e depois

| Módulo | Antes | Depois |
|---|---:|---:|
| `src/tools/smoothing.py` | 8% | 96% |
| `src/tools/edge_utils.py` | 18% | 88% |
| `src/tools/selection_tool.py` | 22% | 96% |
| `src/ui/gizmo.py` | 23% | 100% |
| `src/core/view_processor.py` | 25% | 60% |
| `src/tools/polygonal_lasso.py` | 25% | 86% |
| `src/tools/lasso_tool.py` | 27% | 85% |
| `src/core/config.py` | 28% | 80% |
| `src/utils/selection_tools.py` | 28% | 98% |
| `src/tools/rect_selection.py` | 29% | 86% |
| `src/ui/collision_overlay.py` | 29% | 98% |
| `src/launcher.py` | 18% | 18% — encaminhado à Etapa 7 |

A cobertura combinada de linhas e branches subiu de `62.45%` para `67.51%`.
As metas finais de 90%/85% não foram atingidas e `R-003` permanece aberto.

## Falhas descobertas e corrigidas

1. `multi_scale_edges()` aceitava escalas vazias, não positivas ou não
   finitas e pesos com soma zero/não finita, permitindo divisão por zero e
   propagação de `NaN`; agora rejeita esses contratos com `ValueError`.
2. `ViewProcessor.to_qimage()` podia lançar exceção bruta para arrays 1D e
   não validava quantidade de canais; agora falha de forma controlada.
3. `CollisionOverlay` dividia por zero no offset do rótulo quando o zoom era
   zero, apesar de já possuir fallback para a fonte; agora usa offset seguro.

## Arquivos e hashes SHA-256

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/core/view_processor.py` | 10366 | `bd70498ac5f0b89bbc10dc2eed8ba8a9680a891dbca5a4808bb62b8249c1a96c` |
| `src/tools/edge_utils.py` | 5357 | `47a6069a383ce0a10a15c6e35a6c3f1fbd60c21737ebc528332561ac91e6d535` |
| `src/ui/collision_overlay.py` | 6331 | `ea667c3de8d52a80e9e6beca33d280300a3c69b7b1d9ad20adc40cec066ce1fe` |
| `tests/test_critical_numeric_coverage.py` | 10845 | `50baea48cccef2b6e48d06567735dcc27968089bc060445b4a75f2f2828b3099` |
| `tests/test_critical_ui_coverage.py` | 11490 | `563f0d389d8b19a45feed90e694b38c1a1f0a46a1320bc4045bcfbc028b609ff` |

## Gate local executado

```text
poetry check --lock --strict
python -m compileall -q -f app.py src tests pack_for_ai.py tools
python -m flake8 src tests tools app.py pack_for_ai.py
python -m black --check --diff src tests tools app.py pack_for_ai.py
python -m isort --check-only --diff src tests tools app.py pack_for_ai.py
python -m mypy src
python -m pip_audit
python -m bandit -q -r src -lll
python -m pytest --cov=src --cov-branch --cov-fail-under=62
python tools/run_legacy_tests.py --group all
python tools/baseline_integrity.py --verify
git diff --check
```

## Resultados

- testes novos: `46 passed`;
- suíte oficial do commit técnico: `589 passed`, `0 failed`, `0 skipped`;
- suíte com o pacote documental: `590 passed`, `0 failed`, `0 skipped`;
- cobertura combinada: `67.51%`;
- mypy: zero erros em 66 arquivos;
- Flake8, Black, isort e compilação: aprovados;
- pip-audit: nenhuma vulnerabilidade conhecida nas dependências auditáveis;
- Bandit de alta severidade: zero achados;
- suíte legada: 196 executados, 26 divergências previstas reconciliadas,
  zero inesperadas e zero ausentes;
- baseline do commit técnico: 278 arquivos;
- baseline com o pacote documental: 279 arquivos;
- referências proibidas e caminhos locais rastreados: zero achados.

## Limitações e decisão

- `src/launcher.py` continua em 18% e é o primeiro alvo obrigatório da Etapa 7;
- cobertura global ainda está abaixo das metas finais;
- esta evidência não encerra `R-003` e não aprova release;
- integração depende de push, PR, CI Linux/Windows, merge e CI pós-merge.

**APROVADO LOCALMENTE / NÃO INTEGRADO.**
