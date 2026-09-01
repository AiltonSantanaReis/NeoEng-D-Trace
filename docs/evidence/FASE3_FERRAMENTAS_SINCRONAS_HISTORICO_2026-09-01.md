# Fase 3 — ferramentas síncronas e histórico

**Projeto:** NeoEng-D-Trace
**Identificador:** `P2D-COMP-01/LEGACY-26-RECON`
**Fase:** `3 — ferramentas síncronas e histórico`
**Data da coleta:** 2026-09-01 (America/Sao_Paulo)
**Status da coleta:** `CANDIDATO PRÉ-COMMIT — fechamento pendente dos gates staged e pós-commit`
**HEAD de entrada:** `3c287ac73925ef0ef33404da63de7401dee43913`
**Branch:** `fix/legacy-27-functional-regressions`

Este relatório registra a execução da Fase 3 sem editar snapshots históricos,
sem alterar o runner legado, sem adicionar `skip`/`xfail`, sem mudar limiares
e sem alterar a lógica de produção. O escopo é #6–#9, #11–#16, #25 e #26; o
#10 permanece no inventário como não regressão. Isto não encerra os 26 casos,
a Fase 4 ou o `P2D-COMP-01` inteiro.

## Regras e governança consultadas

Antes da decisão foram relidos:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
5. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
6. `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`;
7. `quality/legacy_tests/manifest.json`;
8. `quality/legacy_tests/reconciliation.json`;
9. `tools/run_legacy_tests.py`;
10. os relatórios rastreados das Fases 0, 1 e 2.

Foram aplicadas as regras de imutabilidade dos snapshots, substituição por
contrato atual com objetos reais, preservação do estado em erro, um comando por
gesto, evidência reprodutível e bloqueio diante de falha desconhecida, teste
faltante, divergência sem causa, skip novo ou evidência incompleta. Commit,
push e merge são operações distintas; este documento trata somente do
fechamento local da Fase 3.

## Gate de entrada e integridade histórica

| Item | Resultado |
|---|---|
| Branch | `fix/legacy-27-functional-regressions` |
| HEAD de entrada | `3c287ac73925ef0ef33404da63de7401dee43913` |
| Código de produção alterado nesta fase | `0 arquivos` |
| Snapshot/runner/reconciliação alterados nesta fase | `0 arquivos` |
| Manifest histórico SHA-256 | `061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` |
| Reconciliação histórica SHA-256 | `296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493` |
| Fonte histórica do runner | `cf749564ab5d961772d66dc363d0e990cebf8da3` |
| Manifest não rastreado novo | nenhum |
| Entradas não rastreadas preexistentes | preservadas fora da fronteira |

Gates de integridade previamente aprovados no HEAD de entrada:

```text
.\.venv\Scripts\python.exe tools\evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 121 manifests validated.

.\.venv\Scripts\python.exe tools\baseline_integrity.py --verify --git-blob
Baseline verified: 3113 files.
```

`git diff --name-only HEAD -- quality/legacy_tests` foi vazio. Os gates de
integridade serão repetidos após staging e após commit.

## Ambiente

```text
OS: Windows-10-10.0.26200-SP0
Python: 3.11.9
pytest: 9.1.1
PySide6: 6.10.1
Qt: 6.10.1
NumPy: 2.2.6
OpenCV: 4.12.0
QT_QPA_PLATFORM: offscreen
```

## Caracterização histórica preservada

Comando exato:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe tools\run_legacy_tests.py --file test_lasso.py --file test_pen_tool.py --file test_polygonal_lasso.py --file test_rect_ellipse.py --file test_tools_integrated.py --timeout-seconds 120
```

Resultado bruto:

```text
[FAILED] test_lasso.py: tests=7 failures=1 errors=0 skipped=0
[FAILED] test_pen_tool.py: tests=19 failures=2 errors=0 skipped=0
[FAILED] test_polygonal_lasso.py: tests=10 failures=1 errors=0 skipped=0
[FAILED] test_rect_ellipse.py: tests=14 failures=2 errors=0 skipped=0
[FAILED] test_tools_integrated.py: tests=7 failures=7 errors=0 skipped=0
Reconciliation: failed matched=2/14 unexpected=11 missing=12
Totais: 57 testes, 13 falhas, 0 erros, 0 skips
accepted=false
```

A falha histórica permanece observável. Assinaturas e causas:

| Caso | Assinatura histórica | Causa |
|---:|---|---|
| #6 | `_points` reteve 3 pontos | fixture usa Scene/Canvas/manager incompatíveis |
| #7 | retorno `None` em vez de id | fixture não fornece manager real |
| #8 | `_nodes` reteve nós | mesmo protocolo inválido; limpar nós esconderia falha |
| #9 | `_vertices` reteve 3 vértices | fixture Qt/Scene obsoleta |
| #10 | conversão inteira passa | não regressão, mantida no inventário |
| #11 | `_start_point=(10,10)` | fixture usa Scene/parent incompatíveis |
| #12 | `_center=(50,50)` | fixture usa Scene/parent incompatíveis |
| #13 | lasso integrado viu `len(objects)==0` | Scene genérica não muta |
| #14 | poligonal integrada viu `len(objects)==0` | protocolo parcial |
| #15 | elipse integrada viu `len(objects)==0` | protocolo parcial |
| #16 | sequência undo/redo viu coleção vazia | histórico sobre fixture falsa |
| #25 | recursão/falha ao congelar estado | grafo cíclico de Mock |
| #26 | retângulo integrado não criou objeto | Scene falsa sem mutação |

As assinaturas #17 em diante não foram reclassificadas nesta fase.

## Substituto executável

Arquivo:

```text
tests/test_legacy_phase3_contracts.py
```

Hash pré-staging:

```text
SHA-256: d97b570e1f6f6fe536505b9d4bbb7f82b24cc229408cf2ec4ea5160134783eaf
Bytes: 13843
Linhas: 433
```

O teste usa `QApplication`, `CanvasView`, `Scene`, `CommandManager`,
`QMouseEvent` nativo, geometria determinística e persistência real. Não usa
`unittest.mock.Mock`, `MagicMock`, fake Scene ou fake manager. O único
monkeypatch observa `QMessageBox.critical` para que a rejeição não fique
modal em `offscreen`; comando, Scene, histórico e estado continuam reais.
Nenhum `CommandResult` é fabricado.

## Resultados dos substitutos

Focal:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_legacy_phase3_contracts.py
```

Resultados:

```text
11 passed in 2.01s
11 passed in 1.42s
11 passed in 1.34s
```

Regressão combinada:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q tests\test_legacy_phase3_contracts.py tests\test_stage_5_package_5a_creation_commands.py tests\test_stage_5_package_5a_creation_ui.py tests\test_stage_5_package_5b_ui_paths.py tests\test_stage_5_package_5c_bezier_history.py tests\test_stage_0_5_2e_ui.py tests\test_tools_real.py tests\test_view_modes_and_tools.py tests\test_legacy_phase1_contracts.py tests\test_legacy_phase2_contracts.py
```

Resultado: `183 passed in 3.05s`.

## Decisão formal por caso

| Casos | Evidência executada | Decisão |
|---|---|---|
| #6 | lasso nativo válido: id real, um comando, undo/redo; self-intersection rejeitada sem mutação, pontos preservados | `APROVADO — produção NO_CHANGE` |
| #7–#8 | três âncoras e duplo clique nativos: status `APPLIED`, Bézier, um comando, undo/redo; incompleto preserva nó e não cria histórico | `APROVADO — produção NO_CHANGE` |
| #9–#10 | fechamento poligonal real, inteiros, undo/redo; degenerado fail-closed; #10 passa como não regressão | `APROVADO — produção NO_CHANGE` |
| #11 | retângulo real de quatro pontos, dimensões positivas, estado limpo, undo/redo; zero área não muta | `APROVADO — produção NO_CHANGE` |
| #12 | elipse real de 64 pontos, dimensões positivas, undo/redo; degenerada fail-closed | `APROVADO — produção NO_CHANGE` |
| #13–#16 | lasso, poligonal, retângulo e elipse na mesma Scene/manager reais; quatro comandos, undo/redo em ordem, persistência de conteúdo e erro sem mutação | `APROVADO — produção NO_CHANGE` |
| #25 | SceneObject real com ciclo; Add/undo/redo passam sem recursão e preservam ciclo | `APROVADO — produção NO_CHANGE` |
| #26 | retângulo real, save/load em Scene nova, geometria igual, seleção transitória nula no load, undo/redo | `APROVADO — produção NO_CHANGE` |

No round-trip, objetos, polígonos, camadas e colisões coincidem. A seleção é
estado transitório e corretamente não é serializada. Não houve alteração de
lógica original.

## Cobertura, determinismo e limitações

Comando:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m pytest -q --cov=src.tools.base_tool --cov=src.tools.lasso_tool --cov=src.tools.pen_tool --cov=src.tools.polygonal_lasso --cov=src.tools.rect_selection --cov=src.tools.ellipse_selection --cov=src.ui.canvas_view --cov=src.core.commands --cov=src.models.scene --cov-report=term-missing tests\test_legacy_phase3_contracts.py
```

Resultado: `3790 statements instrumentados, 2462 não cobertos, 35% agregado,
11 passed em 3.41s`. É métrica focal, sem limiar alterado, e não substitui a
cobertura global da Fase 7.

A opção `--count=2` foi rejeitada por não existir plugin de repetição; não foi
usada como resultado. Duas execuções independentes passaram. Durante o
desenvolvimento, uma caixa crítica modal no modo offscreen bloqueou um teste;
o processo foi interrompido e o teste foi corrigido com observação estreita da
fronteira Qt. O gate final não teve crash, abort, worker pendente ou hang de
produção. Não há dump/stack nativo a afirmar; nenhum foi inventado.

Performance, memória e Magnetic Lasso assíncrono não são escopo desta fase e
permanecem `NÃO TESTADOS nesta fase`; não autorizam encerramento das Fases
4–7 ou do conjunto completo.

## Fronteira, manifest e rollback

Fronteira pretendida, e única a ser staged:

```text
tests/test_legacy_phase3_contracts.py
docs/evidence/FASE3_FERRAMENTAS_SINCRONAS_HISTORICO_2026-09-01.md
baseline_manifest.json
```

Nenhum artefato não rastreado preexistente será incluído. O manifest histórico
continua com o hash de entrada. A higiene do manifest não rastreado foi tratada
na Fase 0 e não será reclassificada ou apagada aqui.

Base de rollback: `3c287ac73925ef0ef33404da63de7401dee43913`. Como esta fase
adiciona somente teste e documentação, não há alteração de produção para
desfazer. Se um gate pós-commit falhar, o status será `BLOQUEADO` e não haverá
push/merge.

O status ainda é pré-commit. O fechamento exige staging exclusivo, baseline e
evidence integrity, diff check, suíte focal/combinada/global, commit local,
repetição pós-commit dos gates, hashes confirmados e atualização deste relatório
para apontar o commit de código sob teste. Snapshots não serão reescritos para
fazer o runner passar.
