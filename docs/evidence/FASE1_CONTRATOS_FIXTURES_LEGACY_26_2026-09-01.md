# Fase 1 — contratos substitutos e fábrica de fixtures

**Projeto:** NeoEng-D-Trace
**Identificador:** `P2D-COMP-01/LEGACY-26-RECON`
**Fase:** `1 — contratos substitutos e fábrica de fixtures`
**Data:** 2026-09-01 (America/Sao_Paulo)
**Status:** `APROVADO — ESCOPO DA FASE 1`
**HEAD de entrada:** `6bb04028b2a1f153f03f67a40e686663f75ddee7`
**Base histórica de reprodução:** `cf749564ab5d961772d66dc363d0e990cebf8da3`

Este relatório registra a execução integral da Fase 1. A saída aprovada é
restrita à fábrica de fixtures e aos contratos substitutos desta fase. Não
declara correção dos 26 casos legados, alteração de produto, aceitação da
reconciliação histórica ou autorização de push/merge.

## Regras e governança consultadas

Antes da decisão e da alteração foram consultados, no branch de trabalho:

1. `docs/POLITICA_NAO_REGRESSAO.md`;
2. `docs/POLITICA_QUALIDADE_E_EVIDENCIAS.md`;
3. `docs/evidence/README.md`;
4. `tools/run_legacy_tests.py`;
5. `quality/legacy_tests/manifest.json`;
6. `quality/legacy_tests/reconciliation.json`;
7. `docs/AUDITORIA_27_FALHAS_TECNICAS_2026-09-01.md`;
8. `docs/PLANO_CORRECAO_26_FALHAS_LEGADAS_2026-09-01.md`;
9. `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`, para confirmar que
   nenhum contrato aprovado de cache, incremental, frame ou viewport seria
   alterado.

As regras aplicadas foram: snapshots históricos imutáveis; falhas visíveis;
nenhum `skip`, `xfail`, filtro, threshold ou tolerância alterado para obter
aprovação; mock genérico não substitui Scene, CommandManager, CanvasView,
QImage ou pipeline real; e a etapa somente pode ser aprovada com comandos e
resultados reproduzíveis.

## Decisão de engenharia

### Fato verificável

Os 26 casos restantes dependem de objetos reais, invariantes de Scene,
histórico real, imagem válida e entrega Qt explícita. Os testes históricos
preservados continuam separados e não podem ser reescritos para acomodar os
contratos atuais.

### Alternativas consideradas

- manter os mocks genéricos: rejeitada, pois não representa os protocolos que
  são o objeto da validação;
- alterar o produto para aceitar objetos incompletos: rejeitada, pois
  mascararia falhas de integração e poderia bypassar histórico ou validação;
- criar uma fábrica concreta e isolada, com entradas fixas e sincronização por
  sinal/timeout: adotada, pois preserva o caminho de produção e permite
  substituir cada fixture histórica por uma entrada verificável.

### Impacto, segurança e rollback

- Produto: nenhum arquivo em `src/` foi alterado.
- Dados e formatos: nenhum projeto, snapshot, exportador ou schema foi
  alterado.
- Desempenho: nenhum caminho de produção foi alterado ou otimizado nesta fase.
- Segurança: imagens sintéticas sem dados pessoais; QImage recebe cópia
  própria; nenhum arquivo de entrada externo é executado.
- Rollback: remover/reverter somente os arquivos desta fase; snapshots,
  evidências preexistentes e untracked fora da fronteira permanecem intactos.

## Arquivos controlados

| Arquivo | Função | SHA-256 no worktree |
|---|---|---|
| `tests/legacy_phase1_fixtures.py` | fábrica concreta e sincronização Qt | `0ECFBFA1521F3DFE97CA515FCB825AA29A87502B5C25ACF2F4D14B0EE6F13255` |
| `tests/test_legacy_phase1_contracts.py` | oito contratos executáveis da Fase 1 | `8D5C8C5407A419DE8227822E0A07C30007C28EB46BD2CDFBFB2A908B170BB06A` |
| `docs/evidence/FASE1_CONTRATOS_FIXTURES_LEGACY_26_2026-09-01.md` | este registro | não auto-referenciado; incluído no baseline após o commit |

Nenhum arquivo rastreado fora desta fronteira foi modificado. Os snapshots
continuam com os hashes observados antes da fase:

- `quality/legacy_tests/manifest.json` — SHA-256
  `061E5981084E962F71F6357E765A0FE66DEFDA5AF521C9B7E22AE1E2BBF9833A`;
- `quality/legacy_tests/reconciliation.json` — SHA-256
  `296CA97F07341EEDD99EF8AAE57D7053FE6110BDDDBC01A55B872D3BF20FB493`.

## Contratos implementados

### Fixtures versionadas

O catálogo contém quatro entradas fixas, serializáveis e hasháveis:

| Fixture | Classificação | SHA-256 canônico |
|---|---|---|
| `valid_rectangle` | `valid` | `b8265ae9ee5689ecb369b10d40e3e5d3341ba26d573c70b0d360a0b4c327079c` |
| `valid_l_shape` | `valid` | `28af06744716740f6d689d68e71bb511d2230cae5004071ae35b38f8a7526361` |
| `invalid_self_overlapping` | `invalid_self_intersection` | `eef2a568bc4486a803d2922b1b80ccfea7367fe3537b27e25efebe0181f3ad0a` |
| `invalid_collinear` | `invalid_zero_area` | `0f5918683d9350629d0ca078d5feae21d78a6e77bf3a33409ffff142d223cd52` |

As fixtures inválidas são exercitadas contra `Scene.add_object` real e devem
falhar sem mutação, sem seleção e sem entrada no histórico. As válidas são
aceitas pela mesma Scene concreta.

### Fronteiras concretas

- `real_scene()` cria `Scene` e `CommandManager(max_history=50)` reais;
- `real_canvas()` cria `CanvasView` real ligado à Scene;
- `synthetic_image_array()` cria `ndarray` `uint8` contíguo, determinístico;
- `qimage_from_array()` cria `QImage.Format_Grayscale8` com cópia própria;
- `mouse_event()` e `key_event()` criam eventos nativos `QMouseEvent` e
  `QKeyEvent`;
- `wait_for_signal()` usa `QEventLoop` e timeout explícito, lançando
  `TimeoutError` quando não há entrega;
- `DeterministicSignalEmitter` é um `QObject` real com `Signal(object)`.

Nenhum mock genérico, estado global implícito, `sleep`, `skip` ou `xfail` foi
usado nos contratos novos.

## Execução e resultados brutos

Ambiente observado:

- Windows (`win32`);
- Python `3.11.9`;
- pytest `9.1.1`;
- PySide6 `6.10.1`;
- OpenCV `4.12.0`;
- NumPy `2.2.6`;
- `QT_QPA_PLATFORM=offscreen`;
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

Comandos executados:

```text
\.venv\Scripts\python.exe -m pytest tests\test_legacy_phase1_contracts.py --tb=long -q
```

Resultado final:

```text
collected 8 items
tests\test_legacy_phase1_contracts.py ........ [100%]
8 passed in 1.12s
```

```text
\.venv\Scripts\python.exe -m pytest tests\test_legacy_phase1_contracts.py --collect-only -q
```

Resultado: `8 tests collected`; todos os oito testes foram coletados
explicitamente.

```text
\.venv\Scripts\python.exe -m py_compile tests\legacy_phase1_fixtures.py tests\test_legacy_phase1_contracts.py
\.venv\Scripts\python.exe -m black --check tests\legacy_phase1_fixtures.py tests\test_legacy_phase1_contracts.py
\.venv\Scripts\python.exe -m isort --check-only tests\legacy_phase1_fixtures.py tests\test_legacy_phase1_contracts.py
\.venv\Scripts\python.exe -m flake8 tests\legacy_phase1_fixtures.py tests\test_legacy_phase1_contracts.py
```

Resultado: compilação, Black, isort e Flake8 aprovados.

Uma primeira coleta falhou por importação incorreta de `QKeyEvent` e
`QMouseEvent` a partir de `PySide6.QtCore`. A causa foi corrigida movendo os
dois imports para `PySide6.QtGui`; a coleta e a execução subsequentes passaram.
O incidente não alterou critérios, produto ou snapshots.

## Gates staged pós-implementação

Comandos e resultados antes do commit:

```text
tools/evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 121 manifests validated.

tools/baseline_integrity.py --verify --git-blob
Baseline verified: 3111 files

git diff --cached --check
Resultado: aprovado, sem whitespace inválido.
```

## Limitações e fronteira de aprovação

Esta aprovação não cobre ainda:

- correção dos 26 casos legados;
- alteração do produto para resolver qualquer divergência;
- exportação/round-trip, solver completo, worker real ou integração end-to-end;
- atualização da reconciliação histórica;
- suíte oficial completa, benchmark, cobertura global ou CI;
- push, merge, release ou aprovação global do `P2D-COMP-01`.

Esses itens permanecem nas Fases 2–7. O runner histórico continua sendo uma
fonte imutável de divergências e o caso #10 continua protegido separadamente.

## Critério de saída

**APROVADO no escopo da Fase 1:** a fábrica concreta e os oito contratos
passaram sem skips, xfails, erros ou estado global implícito. A próxima fase
somente poderá começar após nova consulta às regras e novo gate, conforme o
plano aceito.
