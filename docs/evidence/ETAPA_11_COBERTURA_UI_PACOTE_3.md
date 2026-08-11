# Etapa 11 — cobertura integral da interface — Pacote 3

**Data:** 11 de agosto de 2026
**Base integrada:** `5e88c8d548e2b60612601f83e1bf24aeb91081bb`
**Base técnica do pacote:** `075b5b0231ca0aeb8a26d6253e847619d70211cf`
**Estado:** APROVADO LOCALMENTE / CI NÃO EXECUTADO / NÃO INTEGRADO
**Release:** NÃO APROVADA

## Objetivo e escopo

O terceiro pacote cobre fluxos de maior déficit residual em:

- `src/ui/canvas_view.py`;
- `src/ui/export_dialog.py`.

Foram adicionados oito testes comportamentais em
`tests/test_stage_11_canvas_export_branch_coverage.py`. Os cenários exercitam
Qt real em modo offscreen, eventos de mouse e teclado, seleção, polígono
manual, gesto do gizmo, histórico, desenho em `QImage`, modos de visualização,
worker de raio X, exportações unitária, em lote, atlas e GLTF/GLB, arquivos
reais temporários, cancelamentos, pós-condições e falhas injetadas. Mocks foram
restritos a diálogos modais, fronteiras de arquivo e exportadores isolados.

Nenhum código de produção foi alterado neste pacote.

## Resultados locais reproduzíveis

Ambiente executado: Windows 11, Python 3.11.9, pytest 9.1.1 e pytest-cov 7.1.0.

Comando focal:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest tests\test_stage_11_canvas_export_branch_coverage.py -q --cov=src.ui.canvas_view --cov=src.ui.export_dialog --cov-branch --cov-report=term-missing
```

Resultado: `8 passed`.

Comando canônico integral:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=62 --cov-report=term-missing --cov-report=xml
```

Resultado antes do contrato documental deste pacote: `762 passed`, zero
falhas, zero erros e zero ignorados.

Métricas extraídas diretamente de `coverage.xml`:

| Métrica | Pacote 2 | Pacote 3 local | Variação |
|---|---:|---:|---:|
| Linhas | 9.314/11.632 — 80,07% | 9.747/11.632 — 83,79% | +433 cobertas |
| Ramos | 2.453/3.704 — 66,23% | 2.606/3.704 — 70,36% | +153 cobertos |
| Combinada | 76,73% | 80,55% | +3,82 pontos percentuais |

Cobertura por módulo priorizado:

| Módulo | Linhas antes | Linhas depois | Ramos antes | Ramos depois |
|---|---:|---:|---:|---:|
| `canvas_view.py` | 372/680 — 54,71% | 632/680 — 92,94% | 75/222 — 33,78% | 179/222 — 80,63% |
| `export_dialog.py` | 212/424 — 50,00% | 385/424 — 90,80% | 42/104 — 40,38% | 91/104 — 87,50% |

O ganho global coincide exatamente com a soma dos dois módulos: 433 linhas e
153 ramos. A baseline do Pacote 2 foi reconstruída localmente com os 754 testes
anteriores e reproduziu `9.314/11.632`, `2.453/3.704` e `76,73%`.

## Transparência sobre iterações de teste

Os primeiros validadores encontraram somente divergências de formatação no
novo arquivo. A tentativa inicial de edição literal falhou no parser antes de
escrever qualquer byte. A forma alternativa foi validada por contagem exata;
as quebras de linha também foram inspecionadas em bytes e não apresentaram
duplicação de `CR`.

Não houve falha funcional nos oito testes: o primeiro conjunto executado após
o ajuste de estilo aprovou todos os casos. A suíte oficial também aprovou todos
os 762 testes.

## CI anterior auditado

O CI documental final do Pacote 2, workflow `31477232020`, foi auditado antes
do início deste pacote:

- Windows: job `93733642207`, artefato `9095795979`, SHA-256
  `e800a8137260499822d9f1ea137d818d03c3fe421e45dddcd3483c589f3572aa`;
- Linux: job `93733642214`, artefato `9095766083`, SHA-256
  `11105c6d5182555f4981b5ec13903b376f13ba64f21f104501115829d817847b`;
- merge sintético `83348bb2d12327ab23eebcba59a7e2cc43bcfca6`, com pais base
  `5e88c8d548e2b60612601f83e1bf24aeb91081bb` e fonte
  `075b5b0231ca0aeb8a26d6253e847619d70211cf`;
- `754 passed` nos dois sistemas e métricas exatas semanticamente idênticas;
- 54 arquivos externos, 48 evidências, 1.413 payloads e 327 checksums
  inspecionados, sem violação, checksum inválido ou divergência canônica;
- 42 diferenças textuais brutas limitaram-se a CRLF no checkout Windows;
- legado reconciliado em `27/27`, árvore limpa e 20/20 checks de auditoria.

Esse CI anterior foi **ACEITO**. O Pacote 3 ainda não possui CI próprio.

## Riscos e decisão

- `R-003` permanece **ABERTO**: as metas globais de 90% de linhas e 85% de
  ramos ainda não foram atingidas.
- Faltam, no mínimo, 722 linhas e 543 ramos cobertos para alcançar as metas
  com o denominador atual.
- `canvas_view.py` supera a meta global de linhas, mas ainda não a de ramos;
  `export_dialog.py` supera ambas as metas.
- Processamento, ferramentas grandes e painéis Qt mantêm lacunas relevantes.
- O Pacote 3 está aprovado somente localmente; CI, integração e CI pós-merge
  não existem.
- A Etapa 11 está **EM ANDAMENTO** e a release permanece **NÃO APROVADA**.

## Marcadores auditáveis

```text
BASE_COMMIT=5e88c8d548e2b60612601f83e1bf24aeb91081bb
PACKAGE_BASE_COMMIT=075b5b0231ca0aeb8a26d6253e847619d70211cf
TECHNICAL_COMMIT=PENDING
LOCAL_TESTS_PASSED=762
LOCAL_LINES_COVERED=9747/11632
LOCAL_BRANCHES_COVERED=2606/3704
MODULES_BELOW_30_LINES=0
MODULES_BELOW_30_BRANCHES=0
PRE_MERGE_CI_RUN=NOT_RUN
PRE_MERGE_CI_STATUS=NOT_RUN
R003_CLOSED=NO
STAGE11_COMPLETED=NO
RELEASE_APPROVED=NO
```
