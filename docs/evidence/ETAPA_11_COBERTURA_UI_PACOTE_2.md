# Etapa 11 — cobertura integral da interface — Pacote 2

**Data:** 11 de agosto de 2026
**Base integrada:** `5e88c8d548e2b60612601f83e1bf24aeb91081bb`
**Base técnica do pacote:** `33a807ca41c549c283cad13250ca54b7e2bb6e0b`
**Estado:** APROVADO LOCALMENTE / NÃO INTEGRADO
**Release:** NÃO APROVADA

## Objetivo e escopo

O segundo pacote amplia testes de ramos dos quatro módulos que ocupavam as
posições seguintes no ranking de menor cobertura após o Pacote 1:

- `src/tools/magnetic_lasso.py`;
- `src/ui/mask_viewer.py`;
- `src/tools/collision_brush_tool.py`;
- `src/tools/polygon_edit_tool.py`.

Foram adicionados 11 testes comportamentais em
`tests/test_stage_11_secondary_branch_coverage.py`. Eles exercitam Qt real em
modo offscreen, imagens NumPy e QImage, sinais, eventos, desenho em memória,
detecção, seleção, edição, histórico Undo/Redo, resultados rejeitados e falhas
injetadas. Mocks foram usados somente nas fronteiras que abririam diálogos ou
executariam dependências isoladas; o estado dos modelos e widgets foi
verificado após cada operação relevante.

Nenhum código de produção foi alterado neste pacote.

## Resultados locais reproduzíveis

Ambiente executado: Windows 11, Python 3.11.9, pytest 9.1.1 e pytest-cov 7.1.0.

Comando focal:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_stage_11_secondary_branch_coverage.py -q --disable-warnings --maxfail=1 --cov=src.tools.magnetic_lasso --cov=src.ui.mask_viewer --cov=src.tools.collision_brush_tool --cov=src.tools.polygon_edit_tool --cov-branch --cov-report=term-missing
```

Resultado: `11 passed`.

Comando canônico integral:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
```

Resultado antes do contrato documental deste pacote: `753 passed`, zero
falhas, zero erros e zero ignorados. A execução final com o contrato documental
é registrada nos portões complementares.

Métricas extraídas diretamente de `coverage.xml`:

| Métrica | Pacote 1 | Pacote 2 local | Variação |
|---|---:|---:|---:|
| Linhas | 8.831/11.632 — 75,92% | 9.314/11.632 — 80,07% | +483 cobertas |
| Ramos | 2.247/3.704 — 60,66% | 2.453/3.704 — 66,23% | +206 cobertos |
| Combinada | 72,24% | 76,73% | +4,49 pontos percentuais |

Cobertura por módulo priorizado:

| Módulo | Linhas antes | Linhas depois | Ramos antes | Ramos depois |
|---|---:|---:|---:|---:|
| `magnetic_lasso.py` | 414/770 — 53,77% | 575/770 — 74,68% | 94/274 — 34,31% | 162/274 — 59,12% |
| `mask_viewer.py` | 387/616 — 62,82% | 535/616 — 86,85% | 44/122 — 36,07% | 93/122 — 76,23% |
| `collision_brush_tool.py` | 214/364 — 58,79% | 291/364 — 79,95% | 44/116 — 37,93% | 81/116 — 69,83% |
| `polygon_edit_tool.py` | 237/420 — 56,43% | 326/420 — 77,62% | 63/158 — 39,87% | 108/158 — 68,35% |

Os quatro módulos melhoraram em linhas e ramos. O ganho global excede a soma
direta dos alvos em oito linhas e sete ramos porque os cenários também
executam dependências compartilhadas.

## Transparência sobre iterações de teste

A análise inicial do XML falhou ao procurar somente separadores POSIX; no
Windows, os nomes vieram com barras invertidas. A extração foi repetida com
normalização explícita de separadores. Nenhuma métrica da tentativa inválida
foi aceita.

Três problemas do harness foram encontrados durante o desenvolvimento:

1. um mock restrito a `QMouseEvent` não expunha `key()` para eventos de teclado;
2. o valor inteiro `0` não suportava operação bit a bit com o enum forte de
   modificadores do Qt;
3. um diálogo `information` não interceptado bloqueou a execução offscreen.

Os dois primeiros produziram falhas explícitas. O terceiro foi isolado no
último teste e a execução bloqueada foi terminada; o método modal correto foi
então substituído por double controlado. Todos os 11 testes passaram juntos e
isoladamente após as correções. Esses três eventos são falhas de construção do
teste, não defeitos comprovados do produto.

O primeiro script de atualização documental concluiu cinco arquivos e parou
antes do sexto porque o wrap esperado não coincidia com o conteúdo real. O
arquivo não alterado foi relido e atualizado por correspondência exata. Em
seguida, o novo contrato documental falhou duas vezes por omissões reais da
métrica combinada na matriz de riscos e no índice de evidências. As duas
omissões foram corrigidas e os contratos passaram.

## Portões complementares

Foram aprovados localmente:

- suíte oficial final: `754 passed`, zero falhas, erros ou ignorados;
- `poetry check --lock --strict` e compilação integral;
- Flake8, Black e isort no escopo integral;
- mypy: zero erros em 70 arquivos fonte;
- `pip-audit`: nenhuma vulnerabilidade conhecida; o pacote local não publicado
  foi ignorado porque não existe no índice público;
- Bandit: zero achados de alta severidade;
- suíte legada: 196 testes, 27 falhas históricas exatamente reconciliadas,
  zero inesperadas, zero ausentes, zero erros e zero ignorados.

A baseline é regenerada e verificada depois deste fechamento documental.
Resultados remotos somente serão aceitos após inspeção dos artefatos vinculados
ao HEAD publicado.

## Riscos e decisão

- `R-003` permanece **ABERTO**: 90% de linhas e 85% de ramos ainda não foram
  atingidos.
- Faltam, no mínimo, 1.155 linhas e 696 ramos cobertos para alcançar as metas
  com o denominador atual.
- `canvas_view.py` e `export_dialog.py` continuam entre os alvos prioritários;
  módulos grandes de ferramentas e processamento também mantêm lacunas.
- O Pacote 2 ainda não está integrado e não possui CI pós-merge.
- A Etapa 11 está **EM ANDAMENTO** e a release permanece **NÃO APROVADA**.

## Marcadores auditáveis

```text
BASE_COMMIT=5e88c8d548e2b60612601f83e1bf24aeb91081bb
PACKAGE_BASE_COMMIT=33a807ca41c549c283cad13250ca54b7e2bb6e0b
LOCAL_TESTS_PASSED=754
LOCAL_LINES_COVERED=9314/11632
LOCAL_BRANCHES_COVERED=2453/3704
MODULES_BELOW_30_LINES=0
MODULES_BELOW_30_BRANCHES=0
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
