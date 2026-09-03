# Fase 2 — geometrias, bordas, exportação e viewport

**Projeto:** NeoEng-D-Trace
**Identificador:** `P2D-COMP-01/LEGACY-26-RECON`
**Fase:** `2 — geometrias, bordas, exportação e viewport`
**Data:** 2026-09-01 (America/Sao_Paulo)
**Status:** `APROVADO — ESCOPO DA FASE 2`
**HEAD de entrada:** `326ba4104e5140de6d4f2cecf32b71c5db108b96`

Este relatório registra a execução integral da Fase 2. A fase substitui as
fixtures inadequadas dos casos #1, #2, #3, #4, #5, #23 e #24 por contratos
executáveis com entradas reais e determinísticas. Não altera snapshots
históricos, não altera a reconciliação e não declara a correção dos demais
casos legados, da suíte global ou do `P2D-COMP-01` inteiro.

## Regras e governança consultadas antes da decisão

Antes da investigação, dos testes e da decisão de saída foram consultados
novamente:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `tools/run_legacy_tests.py`;
5. `quality/legacy_tests/manifest.json`;
6. `quality/legacy_tests/reconciliation.json`;
7. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
8. `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
9. `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`;
10. `docs/evidence/FASE1_CONTRATOS_FIXTURES_LEGACY_26_2026-09-01.md`.

As regras reafirmadas e aplicadas foram:

- snapshots históricos e `reconciliation.json` são imutáveis;
- falhas históricas devem continuar observáveis e não podem ser convertidas
  em sucesso por edição de snapshot, filtro, `skip`, `xfail`, limiar,
  tolerância ou alteração do runner;
- a substituição deve usar o contrato atual e a fronteira real do objeto,
  incluindo `Scene`, `CommandManager`, Pillow, NumPy, Qt e o viewport real
  quando esses são o objeto do caso;
- um teste substituto aprovado deve ser reproduzível, determinístico, sem
  mock genérico que esconda protocolo incompleto e sem estado parcial aceito;
- a saída da fase exige evidência dos comandos, contagens, ambiente, hashes e
  decisão formal por caso;
- commit, push e merge são operações distintas. Nesta fase somente o commit
  local da evidência está no escopo; push e merge permanecem pendentes de
  autorização específica.

## Gate de entrada da Fase 2

Estado confirmado antes das alterações:

| Item | Resultado observado |
|---|---|
| Branch | `fix/legacy-27-functional-regressions` |
| HEAD | `326ba4104e5140de6d4f2cecf32b71c5db108b96` |
| Alterações rastreadas prévias | `0` |
| Entradas não rastreadas prévias | `3330` — preservadas fora da fronteira desta fase |
| Manifest histórico | SHA-256 `061E5981084E962F71F6357E765A0FE66DEFDA5AF521C9B7E22AE1E2BBF9833A` |
| Reconciliação histórica | SHA-256 `296CA97F07341EEDD99EF8AAE57D7053FE6110BDDDBC01A55B872D3BF20FB493` |
| Python | `3.11.9` |
| PySide6 | `6.10.1` |
| OpenCV | `4.12.0` |
| NumPy | `2.2.6` |
| pytest | `9.1.1` |

Gates de entrada executados:

```text
tools/run_legacy_tests.py --list --group all
Resultado: 24 arquivos, 196 testes listados.

tools/evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 121 manifests validated.

tools/baseline_integrity.py --verify --git-blob
Baseline verified: 3111 files.
```

Nenhum snapshot histórico ou arquivo da reconciliação foi editado.

## Caracterização histórica preservada

Foi executado o runner oficial somente sobre os arquivos que contêm os sete
casos no escopo da Fase 2:

```text
\.venv\Scripts\python.exe tools\run_legacy_tests.py \
  --file test_convex_decomp.py \
  --file test_edge_utils.py \
  --file test_exporters.py \
  --file test_handle_command.py \
  --file test_mask_utils_curvature.py \
  --file test_mask_viewer.py \
  --timeout-seconds 120
```

Resultado bruto preservado pelo runner:

```text
[FAILED] test_convex_decomp.py: tests=19 failures=2 errors=0 skipped=0
[FAILED] test_edge_utils.py: tests=8 failures=1 errors=0 skipped=0
[FAILED] test_exporters.py: tests=12 failures=1 errors=0 skipped=0
[FAILED] test_handle_command.py: tests=1 failures=1 errors=0 skipped=0
[FAILED] test_mask_utils_curvature.py: tests=7 failures=1 errors=0 skipped=0
[FAILED] test_mask_viewer.py: tests=9 failures=1 errors=0 skipped=0
Reconciliation: reconciled matched=7/7 unexpected=0 missing=0
```

Assinaturas observadas na caracterização:

| Caso | Assinatura histórica observada |
|---|---|
| #1 | `ValueError: Triangulation did not preserve polygon geometry` |
| #2 | `ValueError: Triangulation did not preserve polygon geometry` |
| #3 | `AssertionError` por expectativa histórica de `float64` em Sobel |
| #4 | `AssertionError: 1 != 2` por expectativa histórica de dois atlases |
| #5 | `ValueError: Invalid polygon` durante o undo/redo de handle |
| #23 | `assert 4 >= 8` no contorno circular |
| #24 | `AssertionError: 1.5 != 1.0` no reset de viewport |

Essa reconciliação é somente identificação da divergência histórica: o
resultado `7/7` não é usado como aprovação dos contratos atuais e não autoriza
alterar as entradas históricas.

## Implementação da substituição

Foi adicionado somente:

```text
tests/test_legacy_phase2_contracts.py
```

Não houve alteração em `src/`, no runner histórico, nos snapshots, na
reconciliação, no schema do atlas ou no contrato P2D-05/O-2.

O arquivo contém 12 testes reais e determinísticos:

1. decomposição de L válido com preservação de área, convexidade e limite de
   oito vértices;
2. triangulação do mesmo L nas duas orientações, com quantidade esperada de
   triângulos, áreas positivas e área total preservada;
3. rejeição explícita da fixture histórica auto-intersectante;
4. Sobel com `ndarray` real, `float32`, shape preservado, finitude e magnitude
   acima de 255 sem clipping;
5. atlas Pillow real com rotação forçada, uma página, dimensões físicas,
   `packed_rect`, `extrusion` e `rotated`;
6. Bézier real em `Scene` e `CommandManager`, com commit, mutação,
   undo/redo e igualdade dos estados completos;
7. Bézier colinear inválida rejeitada sem objeto, seleção ou entrada no
   histórico;
8. simplificação circular com contrato default e `min_points=8` explícito;
9. reset de viewport real em três combinações de aspect ratio.

Os dois testes parametrizados do L geram quatro verificações de orientação e
os três aspect ratios geram três verificações de viewport, totalizando 12
itens coletados.

## Decisões técnicas por caso

### Casos #1 e #2 — geometria L e triangulação

A fixture válida usada é `valid_l_shape` da fábrica da Fase 1:

```text
(0, 0), (40, 0), (40, 30), (15, 30), (15, 15), (0, 15)
```

Ela é simples, não auto-intersectante e tem área determinística. A decomposição
é aceita somente quando cada peça é convexa, tem no máximo oito vértices e a
soma das áreas coincide com a área de origem. A triangulação é verificada nas
duas orientações e exige `n - 2` triângulos positivos.

A fixture `invalid_self_overlapping` continua sendo rejeitada com
`Triangulation did not preserve polygon geometry`. Portanto, a correção não
foi relaxar a validação; foi substituir a entrada histórica inadequada por um
L válido e manter a rejeição da geometria inválida como contrato separado.

**Decisão:** `NO_CHANGE` em produção; contratos substitutos aprovados.

### Caso #3 — bordas/Sobel

O contrato atual é `CV_32F`/`float32`, shape igual ao input, valores finitos e
sem clipping de magnitude. A imagem sintética contém bordas de 255 e 180, e o
resultado deve exceder 255 em magnitude para provar que não houve truncamento.

**Decisão:** `NO_CHANGE` em produção; expectativa histórica `float64` não foi
reintroduzida.

### Caso #4 — atlas, rotação e UV

O atlas é gerado com uma imagem Pillow real de `3x5` e limite `5x4`, forçando
rotação para que a imagem caiba. O teste confirma uma única página, atlas
`5x3`, `rotated=True`, `rect` e `packed_rect` físicos `5x3` e ausência de
extrusão.

O contrato vigente não possui uma chave serializada chamada `uv`; ele possui
`packed_rect`, dimensão da página, rotação e extrusão. Por isso não foi
inventado um novo campo nem alterado o schema. A prova equivalente de UV é
calculada deterministicamente como:

```text
u0 = packed_rect.x / atlas.width
v0 = packed_rect.y / atlas.height
u1 = (packed_rect.x + packed_rect.w) / atlas.width
v1 = (packed_rect.y + packed_rect.h) / atlas.height
```

Para a fixture, o resultado é `(0.0, 0.0, 1.0, 1.0)`. Se uma integração
futura exigir UV serializada, isso deverá ser uma decisão de contrato própria;
não foi mascarado nesta fase pela alteração unilateral do schema atual.

**Decisão:** `NO_CHANGE` em produção; contrato de rotação, retângulo físico e
UV derivável aprovado.

### Caso #5 — Bézier, handle e histórico

O teste usa `Scene()` e `CommandManager(max_history=50)` concretos. Uma curva
cúbica não colinear é criada por `CreateBezierObjectCommand`; a criação é
confirmada, o histórico é limpo para isolar a edição, e
`HandleMoveCommand` é aplicado. O estado completo do objeto é capturado antes
e depois, e ambos são restaurados por undo/redo sem substituir a lógica de
amostragem.

Um segundo teste usa controles colineares e confirma rejeição sem mutação,
seleção ou histórico. Assim, o teste não transforma uma geometria inválida em
caso de undo/redo apenas para obter sucesso.

**Decisão:** `NO_CHANGE` em produção; fluxo real de histórico aprovado.

### Caso #23 — simplificação de curvatura

O círculo possui 32 pontos determinísticos. O comportamento default continua
aceitando a redução histórica com pelo menos três pontos. O piso de oito
pontos é exigido somente quando `min_points=8` é explicitamente informado.

**Decisão:** `NO_CHANGE` em produção; garantia de oito pontos é opt-in e
testada sem alterar o default.

### Caso #24 — reset de viewport

O teste instancia `MaskViewer` real em `QApplication` offscreen, define imagem
real em três proporções e chama `reset_view()`. O contrato confirmado é
preencher completamente a viewport com `max(zoom_x, zoom_y)` e centralizar o
excesso negativo em cada eixo. Não foi fixado zoom `1.0`.

**Decisão:** `NO_CHANGE` em produção; fit/center dependente de viewport e
imagem aprovado.

## Execução dos testes substitutos e regressão

Execução dedicada:

```text
\.venv\Scripts\python.exe -m pytest tests\test_legacy_phase2_contracts.py -q
12 passed in 1.13s
```

Regressão funcional de escopo:

```text
\.venv\Scripts\python.exe -m pytest -q \
  tests/test_legacy_phase2_contracts.py \
  tests/test_stage_0_5_2e_core.py \
  tests/test_stage_8_bezier_geometry.py \
  tests/test_stage_5_package_5c_bezier_history.py \
  tests/test_viewport_state_contract.py \
  tests/test_audit_closure_contracts.py \
  tests/test_export.py \
  tests/test_integration_manifest.py
```

Resultado final após formatação:

```text
collected 210 items
210 passed in 3.77s
```

Gates de qualidade do arquivo novo:

```text
\.venv\Scripts\python.exe -m black --check tests\test_legacy_phase2_contracts.py
1 file would be left unchanged.

\.venv\Scripts\python.exe -m isort --check-only tests\test_legacy_phase2_contracts.py
Resultado: aprovado.

\.venv\Scripts\python.exe -m flake8 tests\test_legacy_phase2_contracts.py
Resultado: aprovado.

\.venv\Scripts\python.exe -m py_compile tests\test_legacy_phase2_contracts.py
Resultado: aprovado.

git diff --check -- tests/test_legacy_phase2_contracts.py
Resultado: aprovado, sem whitespace inválido.
```

Uma primeira execução do Black detectou formatação pendente no teste novo.
O arquivo foi formatado automaticamente, e todos os gates — inclusive os 210
testes — foram executados novamente. Isort, Flake8, compilação e diff não
apresentaram falhas. Nenhum critério foi relaxado.

## Classificação formal da Fase 2

| Caso | Resultado | Correção de produção | Evidência |
|---|---|---|---|
| #1 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | decomposição L válida, área e convexidade |
| #2 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | triangulação em duas orientações e rejeição inválida |
| #3 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | Sobel `float32`, finito e sem clipping |
| #4 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | atlas único, rotação, rect físico e UV derivável |
| #5 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | Scene/manager reais, commit e round-trip |
| #23 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | default e `min_points=8` explícito |
| #24 | `CORRIGIDO` no contrato substituto | `NO_CHANGE` | fit/center real em três aspect ratios |

`CORRIGIDO` nesta tabela significa que o caso possui agora um contrato
substituto real aprovado. Não significa que o snapshot histórico foi alterado
nem que a divergência histórica deixou de ser observável.

## Critérios de saída e limites

Os critérios desta fase foram atendidos: consulta prévia às regras, gate de
entrada, caracterização histórica imutável, fixtures reais, contratos
substitutos, regressão funcional, gates de qualidade e decisão por caso.

Ficam explicitamente fora da saída desta fase:

- correção ou reescrita dos snapshots históricos;
- edição de `manifest.json` ou `reconciliation.json` históricos;
- correção dos casos #6–#22 e #25–#27;
- solver assíncrono, worker completo, round-trip end-to-end e demais fases do
  plano;
- push, merge, release ou aprovação global de `P2D-COMP-01`.

O commit local desta evidência só poderá ocorrer depois do gate staged,
incluindo `evidence_integrity`, `baseline_integrity` e `git diff --cached
--check`. A fase não autoriza push ou merge.

**Conclusão:** Fase 2 aprovada exclusivamente para geometrias, bordas,
exportação/atlas e viewport, com 12 contratos substitutos aprovados e 210
testes de regressão aprovados, sem alteração de produção e sem mascaramento
das sete falhas históricas.
