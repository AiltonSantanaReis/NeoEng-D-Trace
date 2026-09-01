# Adendo de evidência — P2D-05 — diagnóstico do crash nativo Qt no Windows

## Identificação

- Commit avaliado: `5b3d9e9ba3a52620b8bbdd76791c53e153d508e0`
- Branch: `p2d-05-ui-crash-root-cause`
- Base: `0ab59eb40f8c31e482d9cad51543e7fd5e2090d5`
- PR: [#165](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/pull/165)
- Data da validação: 2026-09-01
- Execução remota: [33478940582](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33478940582)
- Job Linux: [99764037318](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33478940582/job/99764037318)
- Job Windows: [99764037498](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33478940582/job/99764037498)
- Artefato Windows: [validation-windows-python-3.11](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33478940582/artifacts/9789359101)

## Objetivo e escopo

Investigar o crash nativo `Windows fatal exception: access violation` observado no job Windows após a remoção dos 11 skips que mascaravam testes de viewport/gizmo. Este adendo registra somente a instrumentação diagnóstica e o resultado da execução; não altera limiares, asserções, seleção de testes, regras de CI ou o comportamento do produto.

## Instrumentação aplicada

O workflow passou a configurar, de forma explícita e fail-closed, os LocalDumps do Windows para `python.exe`:

- pasta temporária do runner: `D:\a\_temp\native-crash-dumps`;
- `DumpType=2` (dump completo);
- `DumpCount=5`;
- coleta condicional somente quando o passo do pytest falha;
- o diretório foi incluído no artefato Windows existente, sem criar uma rota paralela de evidência.

A configuração é diagnóstica. Ela não captura uma causa quando o crash não ocorre e não transforma uma execução passageira em correção.

## Comandos e ambiente

O comando principal do job Windows permaneceu exatamente o gate existente:

```text
poetry run pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml
```

Ambiente observado no job Windows: `windows-latest`, Python `3.11.9`, `QT_QPA_PLATFORM=offscreen`, dependências sincronizadas pelo lock. O mesmo workflow executou também lint, formatação, import ordering, mypy, pip-audit, Bandit, auditoria de qualidade, integridade de baseline/evidência e verificação de árvore-fonte.

## Resultado objetivo

- Linux: job concluído com `success`.
- Windows: job concluído com `success` em 7m15s.
- Suíte principal Windows: `1858 passed, 1 warning` em 91,14s.
- Não houve skip na suíte principal Windows; os 11 casos reativados permaneceram executáveis.
- Cobertura integrada: política aprovada (`linhas >= 90%`, `branches >= 85%`, módulos mensuráveis `>= 30%`).
- A coleta condicional de crash foi `skipped` porque o passo de testes não falhou; isso é consequência da condição declarada, não uma exclusão de teste.
- O artefato oficial foi baixado e inspecionado; não continha arquivos `.dmp` ou `.mdmp`.
- Não houve nova ocorrência de `access violation` nesta execução.

O passo separado de reconciliação da suíte legada continuou reportando falhas históricas explicitamente. Entre elas: `test_convex_decomp.py`, `test_edge_utils.py`, `test_exporters.py`, `test_handle_command.py`, `test_lasso.py`, `test_magnetic_lasso.py`, `test_mask_utils_curvature.py`, `test_mask_viewer.py`, `test_pen_tool.py`, `test_polygonal_lasso.py`, `test_rect_ellipse.py` e `test_tools_integrated.py`. O workflow já trata essa reconciliação como inventário histórico; portanto, não se declara que todas as validações legadas estão verdes.

## Relação com o defeito histórico

O defeito original permanece uma observação válida:

- execução histórica: `33469733446`;
- SHA histórico: `7c866fa60e5e818656c92f55c58b751f0b5408f9`;
- job Windows: `99751339437`;
- último frame Python registrado: `tests/test_stage6_gizmo_gap_closure.py`, linha 43, no teste `test_vertex_gizmo_exposes_only_xy_handles_and_anchors_selected_vertex`;
- erro registrado: `Windows fatal exception: access violation`.

Esse frame é o último ponto Python observado, não a identificação da causa-raiz nativa. A execução atual não produziu dump, stack nativa, módulo culpado ou informação de ownership Qt suficiente para concluir a origem.

## Falhas, causa-raiz e limitações

- Falha reproduzida nesta execução: não reproduzida.
- Causa-raiz: não determinada.
- Correção causal do produto: não implementada.
- Evidência atual: três tentativas remotas da suíte principal após a reativação dos testes, incluindo esta execução, passaram; isso demonstra não recorrência nessas amostras, não demonstra ausência do defeito.
- Limitação principal: o crash nativo é intermitente e o runner não forneceu dump nesta execução.
- Risco residual: a falha histórica de processo continua sem explicação técnica verificável.

## Decisão formal

**BLOQUEADO.**

O PR permanece aberto e não pode ser mergeado como correção. A instrumentação diagnóstica foi validada, mas não houve causa-raiz nem patch causal. O próximo avanço aceitável é obter uma reprodução com dump/stack nativa ou uma demonstração determinística equivalente, então implementar uma correção estreita com teste de regressão e repetir todos os gates sem skips, sem xfail e sem alteração de regras.
