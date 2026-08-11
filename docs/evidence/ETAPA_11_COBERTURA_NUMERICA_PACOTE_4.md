# Etapa 11 — cobertura numérica e ferramentas — Pacote 4

**Data:** 11 de agosto de 2026
**Base integrada:** `5e88c8d548e2b60612601f83e1bf24aeb91081bb`
**Base técnica do pacote:** `427cc803c7923970b9fd89752c0247f75b4f94c6`
**Estado:** APROVADO LOCALMENTE / CI NÃO EXECUTADO / NÃO INTEGRADO
**Release:** NÃO APROVADA

## Objetivo e escopo

O quarto pacote cobre os maiores déficits determinísticos fora das janelas Qt
completas:

- `src/tools/auto_detect.py`;
- `src/core/view_processor.py`;
- `src/tools/base_tool.py`;
- `src/tools/mask_utils.py`.

Foram adicionados 17 testes em
`tests/test_stage_11_numeric_tool_branch_coverage.py`. Eles usam imagens NumPy
e OpenCV reais, contornos e máscaras sintéticos, conversão QImage, backend GPU
simulado com operações NumPy, falhas injetadas nas fronteiras CPU/GPU,
transformações de coordenadas, resultados reais de comandos e doubles apenas
para diálogos ou operações externas isoladas.

A auditoria removeu dois ramos comprovadamente inalcançáveis de
`src/tools/auto_detect.py`:

1. o `else` posterior à validação exaustiva dos três modos aceitos;
2. o segundo filtro de área de furos, impossível após `area >= min_area`.

Não houve mudança no conjunto de entradas válidas nem no resultado produzido
por elas. O denominador global diminuiu quatro linhas e quatro ramos.

## Resultados locais reproduzíveis

Ambiente executado: Windows 11, Python 3.11.9, pytest 9.1.1 e pytest-cov 7.1.0.

Comando focal principal:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest tests\test_stage_11_numeric_tool_branch_coverage.py tests\test_auto_detect.py tests\test_stage_5_package_5b_batch_commands.py -q --maxfail=1 --cov=src.tools.auto_detect --cov=src.core.view_processor --cov=src.tools.mask_utils --cov=src.tools.base_tool --cov-branch --cov-report=term-missing
```

Resultado: `43 passed`.

Comando canônico integral:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term --cov-report=xml
```

Resultado antes do contrato documental deste pacote: `779 passed`, zero
falhas, zero erros e zero ignorados.

Métricas extraídas diretamente de `coverage.xml`:

| Métrica | Pacote 3 | Pacote 4 local | Variação |
|---|---:|---:|---:|
| Linhas | 9.747/11.632 — 83,79% | 10.007/11.628 — 86,06% | +260 cobertas; -4 no denominador |
| Ramos | 2.606/3.704 — 70,36% | 2.715/3.700 — 73,38% | +109 cobertos; -4 no denominador |
| Combinada | 80,55% | 83,00% | +2,45 pontos percentuais |

Cobertura por módulo priorizado:

| Módulo | Linhas antes | Linhas depois | Ramos antes | Ramos depois |
|---|---:|---:|---:|---:|
| `view_processor.py` | 95/162 — 58,64% | 146/162 — 90,12% | 36/56 — 64,29% | 51/56 — 91,07% |
| `auto_detect.py` | 142/268 — 52,99% | 255/264 — 96,59% | 52/114 — 45,61% | 98/110 — 89,09% |
| `base_tool.py` | 80/129 — 62,02% | 128/129 — 99,22% | 18/38 — 47,37% | 30/38 — 78,95% |
| `mask_utils.py` | 108/158 — 68,35% | 156/158 — 98,73% | 37/74 — 50,00% | 72/74 — 97,30% |

Os alvos somam as 260 linhas novas e 108 dos 109 ramos novos. O ramo adicional
vem de uma dependência compartilhada exercitada pela detecção automática.

## Transparência sobre iterações de teste

O primeiro conjunto focado falhou porque o teste esperava `False` para três
pontos em que dois eram duplicados; o terceiro ainda formava ângulo agudo e a
implementação retornou corretamente `True`. O caso foi corrigido para três
pontos idênticos, que realmente exercitam o caminho degenerado.

A segunda execução falhou porque o teste reutilizou o valor `2` passado a uma
chamada anterior de `get_canvas_zoom`; os métodos de conversão usam seu próprio
fallback padrão `1.0`. As coordenadas esperadas foram corrigidas. Essas duas
falhas eram erros do harness, não defeitos do produto.

Após a remoção dos ramos mortos, o Black encontrou uma linha em branco extra;
ela foi removida sem alteração funcional. O conjunto focal final aprovou 43
testes e a suíte oficial aprovou 779.

## CI anterior auditado

O CI documental final do Pacote 3, workflow `31479998276`, foi auditado antes
do início deste pacote:

- Linux: job `93742515599`, artefato `9096845349`, SHA-256
  `ebb2a51ad4d2f597364ecb70983259bb6459850290c7974c47840d263f3149f9`;
- Windows: job `93742515625`, artefato `9096872784`, SHA-256
  `fb5da5b78d997bebb1390582c4e0fa83736f39934f4da4954bc3b69653d3c80e`;
- merge sintético `2ffbb7c7c459c7725bd036ffd70431f436fb1053`, com pais base
  `5e88c8d548e2b60612601f83e1bf24aeb91081bb` e fonte
  `427cc803c7923970b9fd89752c0247f75b4f94c6`;
- `762 passed` nos dois sistemas, cobertura semanticamente idêntica e legado
  reconciliado em `27/27` com árvore limpa;
- 55 arquivos externos, 49 evidências, 1.414 payloads e 327 checksums
  inspecionados, sem violações ou divergências canônicas;
- 43 diferenças textuais brutas limitaram-se a CRLF no checkout Windows.

Esse CI anterior foi **ACEITO**. O Pacote 4 ainda não possui CI próprio.

## Riscos e decisão

- `R-003` permanece **ABERTO**: as metas globais de 90% de linhas e 85% de
  ramos ainda não foram atingidas.
- Faltam, no mínimo, 459 linhas e 430 ramos cobertos para alcançar as metas
  com o denominador atual.
- `pen_tool.py`, `main_window.py`, `magnetic_lasso.py`, `scene.py` e painéis Qt
  concentram os maiores déficits seguintes.
- O Pacote 4 está aprovado somente localmente; CI, integração e CI pós-merge
  não existem.
- A Etapa 11 está **EM ANDAMENTO** e a release permanece **NÃO APROVADA**.

## Marcadores auditáveis

```text
BASE_COMMIT=5e88c8d548e2b60612601f83e1bf24aeb91081bb
PACKAGE_BASE_COMMIT=427cc803c7923970b9fd89752c0247f75b4f94c6
TECHNICAL_COMMIT=PENDING
LOCAL_TESTS_PASSED=779
LOCAL_LINES_COVERED=10007/11628
LOCAL_BRANCHES_COVERED=2715/3700
MODULES_BELOW_30_LINES=0
MODULES_BELOW_30_BRANCHES=0
PRE_MERGE_CI_RUN=NOT_RUN
PRE_MERGE_CI_STATUS=NOT_RUN
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
