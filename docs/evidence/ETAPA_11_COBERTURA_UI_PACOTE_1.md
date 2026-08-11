# Etapa 11 — cobertura integral da interface — Pacote 1

**Data:** 11 de agosto de 2026
**Base integrada:** `5e88c8d548e2b60612601f83e1bf24aeb91081bb`
**Estado:** APROVADO LOCALMENTE / NÃO INTEGRADO
**Release:** NÃO APROVADA

## Objetivo e escopo

O pacote prioriza todos os módulos que, na base integrada, tinham cobertura de
ramos inferior a 30%:

- `src/tools/ellipse_selection.py`;
- `src/ui/canvas_view.py`;
- `src/ui/export_dialog.py`;
- `src/ui/export_preview.py`;
- `src/ui/tool_palette.py`.

Foram adicionados 11 testes comportamentais em
`tests/test_stage_11_priority_branch_coverage.py`. Os testes usam objetos Qt
reais em modo offscreen, `Scene`, `CommandManager`, histórico Undo/Redo e
arquivos Pillow reais em diretórios temporários. Não se limitam a mocks de
retorno ou à existência de símbolos.

## Falha estrutural encontrada e corrigida

`ToolPalette.select_previous_tool()` continha uma condição
`prev_idx < 0` inalcançável: o operador módulo de Python, com divisor positivo,
já produz índice no intervalo válido. O bloco morto foi removido. A navegação
cíclica anterior/seguinte permaneceu coberta por teste comportamental.

Essa alteração reduz duas linhas e dois ramos do denominador. Ela não foi
contabilizada como execução de comportamento inexistente.

## Resultados locais reproduzíveis

Ambiente executado: Windows 11, Python 3.11.9, pytest 9.1.1 e pytest-cov 7.1.0.

Comando focal:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_stage_11_priority_branch_coverage.py -q --cov=src.tools.ellipse_selection --cov=src.ui.canvas_view --cov=src.ui.export_dialog --cov=src.ui.export_preview --cov=src.ui.tool_palette --cov-branch --cov-report=term-missing
```

Resultado: `11 passed`.

Comando canônico integral:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
```

Resultado: `742 passed`, zero falhas, zero erros, zero ignorados.

Métricas extraídas diretamente de `coverage.xml`:

| Métrica | Base integrada | Pacote 1 local | Variação |
|---|---:|---:|---:|
| Linhas | 8.582/11.634 — 73,77% | 8.831/11.632 — 75,92% | +249 cobertas; -2 no denominador |
| Ramos | 2.146/3.706 — 57,91% | 2.247/3.704 — 60,66% | +101 cobertos; -2 no denominador |
| Combinada | 69,93% | 72,24% | +2,31 pontos percentuais |

Cobertura por módulo priorizado:

| Módulo | Linhas antes | Linhas depois | Ramos antes | Ramos depois |
|---|---:|---:|---:|---:|
| `ellipse_selection.py` | 35/96 — 36,46% | 86/96 — 89,58% | 3/22 — 13,64% | 20/22 — 90,91% |
| `canvas_view.py` | 276/680 — 40,59% | 372/680 — 54,71% | 39/222 — 17,57% | 75/222 — 33,78% |
| `export_dialog.py` | 189/424 — 44,58% | 212/424 — 50,00% | 30/104 — 28,85% | 42/104 — 40,38% |
| `export_preview.py` | 107/161 — 66,46% | 159/161 — 98,76% | 11/40 — 27,50% | 33/40 — 82,50% |
| `tool_palette.py` | 132/181 — 72,93% | 158/179 — 88,27% | 5/20 — 25,00% | 18/18 — 100,00% |

A inspeção programática do XML retornou `0` módulos abaixo de 30% em linhas e
`0` módulos com ramos mensuráveis abaixo de 30%.

## Transparência sobre iterações de teste

Duas primeiras execuções focais falharam durante o desenvolvimento dos testes:

1. o teste presumiu incorretamente que a exclusividade Qt desmarcaria o botão
   ativo e também registrou uma expectativa errada para o wrap da paleta;
2. o teste substituiu `ImageFont` de forma ampla demais e bloqueou inclusive o
   fallback que pretendia validar.

As expectativas do harness foram corrigidas. Nenhuma dessas duas falhas foi
classificada como defeito do produto. Depois das correções, o pacote focal e a
suíte integral passaram. O ramo morto de `ToolPalette` foi tratado separadamente
como problema real de código.

## Portões complementares

Também foram aprovados localmente: baseline de 304 arquivos, `poetry check
--lock --strict`, compilação integral, Flake8, Black, isort, mypy sem erros em
70 arquivos, `pip-audit` sem vulnerabilidades conhecidas e Bandit sem achados de
alta severidade. A suíte legada executou 196 testes: 27 falhas históricas foram
reconciliadas exatamente, com zero falhas inesperadas e zero ausentes.

A primeira verificação do diff staged bloqueou três espaços finais no cabeçalho
deste documento. Eles foram removidos antes do commit e o gate foi repetido.

A primeira invocação do gate legado gravou 49 arquivos temporários dentro da
árvore do projeto. A verificação final da baseline os rejeitou corretamente. O
diretório temporário foi removido após validação do caminho; a suíte legada foi
repetida em diretório temporário externo e a baseline voltou a aprovar 304
arquivos. Essa ocorrência foi operacional e não foi convertida em aprovação.

## CI pré-merge auditado

O workflow `31473415874` executou sobre o HEAD fonte
`2e7ad84afc4c66ffaa78d177d418a59ec0e5c4da`. O resumo legado identificou
separadamente o merge sintético testado
`2d7e0c41e4960d02af63813244d4b6ee7b3584d2`, cujos pais são a base
`5e88c8d548e2b60612601f83e1bf24aeb91081bb` e o HEAD fonte.

- Linux: job `93721601195`, artefato `9094281869`, SHA-256
  `937517fe4b519ca2053e750445326a678498f691d5956599addb7b9e5c8171f3`;
- Windows: job `93721601233`, artefato `9094317936`, SHA-256
  `dd76edf7791f2a1c0a8367c7189be721646f5425c29dc9d676b5512ec4bc341a`;
- `742 passed` nos dois sistemas; cobertura idêntica em arquivo, módulo, linha
  e ramo: `8.831/11.632` linhas e `2.247/3.704` ramos;
- legado Windows: 196 testes, 27/27 divergências esperadas, zero inesperadas,
  zero ausentes e árvore limpa;
- 53 arquivos externos, 47 evidências e 1.412 payloads recursivos inspecionados;
- 327 checksums internos validados e zero referências proibidas, caminhos
  pessoais ou divergências de checksum;
- duas evidências apresentaram diferença bruta apenas por LF/CRLF no checkout
  Windows; após normalização exclusiva de fim de linha, as 47 evidências
  coincidiram com os blobs do HEAD fonte. Nenhuma outra diferença foi aceita.

O CI pré-merge foi **ACEITO** após essa inspeção. Isso não comprova merge, CI
pós-merge, encerramento de `R-003`, conclusão da Etapa 11 nem release.

## Riscos e decisão

- `R-003` permanece **ABERTO**: as metas globais de 90% de linhas e 85% de
  ramos ainda não foram atingidas.
- Faltam, no mínimo, 1.638 linhas e 902 ramos cobertos para alcançar as metas
  com o denominador atual.
- `canvas_view.py` e `export_dialog.py` ultrapassaram 30% de ramos, mas ainda
  possuem cobertura insuficiente para encerramento.
- Próximos alvos por menor cobertura de ramos incluem lasso magnético,
  visualizador de máscara, pincel de colisão e edição poligonal.
- O CI pré-merge foi aceito; integração e CI pós-merge ainda não existem.
- A Etapa 11 está **EM ANDAMENTO**; este documento não aprova integração,
  encerramento da etapa nem release.

## Marcadores auditáveis

```text
BASE_COMMIT=5e88c8d548e2b60612601f83e1bf24aeb91081bb
LOCAL_TESTS_PASSED=742
LOCAL_LINES_COVERED=8831/11632
LOCAL_BRANCHES_COVERED=2247/3704
MODULES_BELOW_30_LINES=0
MODULES_BELOW_30_BRANCHES=0
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
