# Etapa 6 — Gizmo profissional: validação local

**Estado:** `PASS_LOCAL / PR, CI, merge e validação pós-merge pendentes`
**Data:** 2026-08-22
**Plano vivo:** `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md`
**Release:** não aprovada por este documento

## Autoridade e baseline

Esta evidência segue as governanças globais do repositório. O baseline técnico da etapa permanece preservado em `docs/evidence/ETAPA_6_GIZMO_BASELINE_2026-08-22.md` e seu encerramento pós-merge em `docs/evidence/ETAPA_6_GIZMO_BASELINE_ENCERRAMENTO_POS_MERGE_2026-08-22.md`. Esses snapshots históricos não foram reescritos.

A implementação foi executada na branch `Ailton/stage6-gizmo-professional`, derivada do conteúdo pós-merge documental `b02227b917363cea49fc5e8d7ae933aecb3fade3`. O relatório local registra `worktree_clean=false` porque há alterações da etapa e diretórios locais históricos não rastreados preservados; isso não foi mascarado.

## Escopo implementado

- `TransformGizmo` mantém os códigos existentes de eixos e separa semanticamente `CENTER` de `SCALE_UNIFORM`, eliminando a colisão de contrato que tornava as duas alças indistinguíveis.
- A geometria visual compartilhada (`visual_radius`/`visual_bounds`) é usada pelo posicionamento e pelo feedback, com clamp dentro do viewport sem alterar coordenadas da imagem.
- O hit-test da alça XY foi contraído para a área interna efetivamente pintada, evitando que um clique no limite deslocado do gizmo capture a criação manual de polígono.
- A translação XY, escala uniforme, rotação Z, escalas por eixo, snapping baseado na âncora original e nudges de teclado transacionais foram preservados ou integrados ao fluxo existente.
- Compatibilidade fail-safe foi mantida para dublês/integrações que não expõem os novos helpers geométricos.
- `SceneTransformGizmo` mantém seu contrato de sinais, rejeita áreas vazias e expõe hover para feedback consistente.
- O toggle do gizmo recebeu nome e descrição acessíveis.
- O gizmo de vértice não foi inventado: a edição de vértices continua no `PolygonEditTool` existente; esta etapa não declara um novo contrato de gizmo de vértice.

## Causa raiz encontrada durante a validação

A primeira suíte após a implementação encontrou uma falha real em `test_canvas_context_menu_selection_and_manual_polygon`: o clamp do gizmo em viewport pequeno colocou a alça XY exatamente sobre a região de clique manual. A segunda execução revelou dublês históricos sem `visual_radius`; isso era uma incompatibilidade real de interface, não uma falha a ser escondida.

A correção foi aplicada no código: margem interna no hit-test XY e fallback geométrico para dublês legados. Os testes históricos não foram enfraquecidos nem convertidos em skips.

## Testes e gates executados

Ambiente real: Windows 10 build 26200, Python 3.11.9, PySide6 6.10.1, Qt 6.10.1, backend Qt `windows`, DPI nativo 2.0.

Comandos relevantes:

```text
.venv/Scripts/python.exe -m pytest -q tests/test_stage6_professional_gizmo.py tests/test_transform_gesture.py --tb=short
15 passed

.venv/Scripts/python.exe -m pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=term --cov-report=xml
1609 passed, 2 skipped in 63.18s

.venv/Scripts/python.exe tools/check_coverage_policy.py coverage.xml
Coverage policy passed: total lines >= 90%, total branches >= 85%, measurable modules >= 30%.
```

Cobertura exata do `coverage.xml` final: 20.157/21.676 linhas (92,99%) e 5.650/6.632 branches (85,19%). Os dois skips são os casos históricos condicionados a symlink/permissão do Windows; não foram criados ou alterados nesta etapa.

Gates estáticos executados no escopo alterado: `compileall`/`py_compile`, Black, isort, Flake8, mypy (`Success: no issues found in 131 source files`), pip-audit (`No known vulnerabilities found`, com o pacote local não publicado no PyPI explicitamente listado como não auditável) e Bandit de alta severidade. Todos passaram; o aviso do pacote local não foi ocultado.

## Auditoria visual reproduzível

Auditor versionado: `scripts/audit_stage6_professional_gizmo.py`.

```text
.venv/Scripts/python.exe scripts/audit_stage6_professional_gizmo.py
capture_count=12, decision=PASS, failure_count=0, qt_platform=windows
```

Foram capturados quatro estados reais por resolução: `selected`, `hover`, `feedback` e `undo`, em 1920×1080, 1366×768 e 1280×720 lógicos. O Windows produziu capturas físicas 2×: respectivamente 3840×2120, 2732×1536 e 2560×1440. Pillow e OpenCV validaram decodificação, dimensões, transparência opaca, hashes e metadados PNG; a geometria veio de widgets Qt reais.

O auditor registrou, sem findings: gizmo dentro do canvas, feedback dentro do canvas e sem interseção com o gizmo, seis tokens da paleta presentes e 12 imagens anotadas. Artefatos:

- `docs/evidence/artifacts/ui-modernization-stage6-20260822/stage6-gizmo-report.json`
- `docs/evidence/artifacts/ui-modernization-stage6-20260822/stage6-gizmo-artifact-index.json`
- `docs/evidence/artifacts/ui-modernization-stage6-20260822/windows-captures/`
- `docs/evidence/artifacts/ui-modernization-stage6-20260822/windows-visual-audit/`

A inspeção visual humana direta não foi confirmada nesta execução porque o visualizador do ambiente encontrou ACL nos PNGs do workspace. Isso permanece declarado como limitação; o resultado `PASS` acima é somente da auditoria automatizada Pillow/OpenCV/Qt, não uma alegação de revisão humana.

## Hashes do escopo

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| `src/ui/canvas_view.py` | 62068 | `cebb7c3ce669d66d0458deee577c843185ef56418cf09f68b0c34fd5fafa5349` |
| `src/ui/gizmo_reference.py` | 10498 | `bc2d8baec86817d7966a402e92e87feb7734b178c15379d0131e972eefb03bb3` |
| `src/ui/scene_authoring_viewport.py` | 27776 | `795665d5b5944520eb07d2258ce197a8762509a18f412f5d45ae800d613f8409` |
| `tests/test_stage6_professional_gizmo.py` | 4641 | `70149299ee00ef9616aefd2a7b49d97207eb070cf5e0114ebfb891eb32830a54` |
| `scripts/audit_stage6_professional_gizmo.py` | 11619 | `b1e1e2489581f8254ee6a40e14d18c050c2f56bf65b2c6bbd8b16e2b00f63494` |
| `stage6-gizmo-report.json` | 23709 | `e5e14692a9d7805329188a19069ba36abe96d01a1080ad8f1b941c869595517e` |
| `stage6-gizmo-artifact-index.json` | 5464 | `929687fe3ea38ae58c6d2415a4d1bc0a088408b2480c32a7d4d7d59f93705d03` |

O índice contém 29 arquivos e registra bytes/SHA-256 de cada captura bruta, anotada, fixture e relatório incluído no pacote.

## Pendências e decisão

- O baseline por Git blob foi regenerado e verificado com 2270 arquivos; a integridade de evidências passou com 100 manifests. A árvore ainda contém alterações locais e diretórios históricos não rastreados, portanto isso não equivale a worktree limpa pós-commit.
- Push, PR, CI remoto e validação pós-merge ainda não foram executados nesta etapa.
- A revisão visual humana dos PNGs permanece não confirmada por ACL do visualizador.
- Não há claim de release, aprovação formal da Etapa 6 ou equivalência entre plataformas antes dos gates remotos.

**Decisão local:** implementação e validações locais concluídas no escopo acima; etapa permanece `PASS_LOCAL`, aguardando revisão do diff, manifesto por blobs Git, commit, push, PR, CI e autorização explícita para merge.
