# NeoEng-D-Trace — Evidência P2D-03C — implementação pré-commit

**Sublote:** P2D-03C — navegação do viewport, fit e estados visuais<br>
**Status:** `IMPLEMENTATION / PRECOMMIT QUALIFICATION`<br>
**Data:** 30/08/2026 (UTC-03)<br>
**Contrato:** `docs/DECISAO_P2D_03C_NAVEGACAO_CAMERA_ESTADOS_2026-08-30.md`<br>
**Checkpoint de entrada:** `4be3b1139e82198147b09a8367eff5119cf3df66`<br>
**Branch:** `modernization/multiaxis-ui`<br>
**Python de qualificação:** `.venv\Scripts\python.exe` 3.11.9<br>
**Qt:** PySide6 6.10.1<br>
**Suíte:** pytest 9.1.1

Este documento registra a implementação autorizada pelo aceite explícito do
proprietário:

> `P2D-03C ACEITO — contrato de navegação, fit e estados visuais`

O registro não declara o sublote fechado. O fechamento exige commit, repetição
dos gates no commit final, captura pós-commit, comparação, seal e aceite final
da entrega. C3, G/V/B, schema V2, editor legado e P2D-03A/P2D-03B permanecem
fora da mutação deste lote.

## 1. Fronteira efetivamente alterada

O código autorizado está limitado a:

- `src/core/scene_view_navigation.py` — matemática pura de zoom, wheel
  ancorada, pan e fit;
- `src/ui/scene_authoring_viewport.py` — navegação transitória do viewport
  profissional, estados visuais dos objetos, foco e pan;
- `src/ui/scene_authoring_inspector.py` — ações `Fit Selection` e `Fit All`;
- `src/ui/scenario_editor_window.py` — conexão das ações ao viewport e ordem
  explícita de tabulação;
- `tests/test_p2d_03c_navigation_math.py`;
- `tests/test_p2d_03c_viewport.py`;
- `tests/test_p2d_03c_professional_flow.py`;
- `scripts/audit_p2d_03c_navigation.py` — produtor de captura e evidência.

As alterações documentais desta qualificação somente reconciliam o estado do
contrato e registram os resultados; não reescrevem a auditoria baseline.

## 2. Implementação contra o contrato

| ID | Requisito | Implementação/evidência | Resultado |
|---|---|---|---|
| D03C-01 | Navegação transitória, sem dirty/undo/save | Estado interno do viewport separado de `SceneAuthoringDocumentV2.camera` | PASS |
| D03C-02 | Wheel ancorada, fator 1.15 por 120, limites 0.10x..8.00x | `scene_view_navigation.py` + teste de inversão/âncora e limites | PASS |
| D03C-03 | Pan apenas por middle-button drag | Interceptação exclusiva de botão médio; seleção esquerda preservada | PASS |
| D03C-04 | Fit Selection/Fit All com margem de 10% | Bounds de objetos elegíveis/visíveis; sockets, overlay e gizmo excluídos | PASS |
| D03C-05 | Navegação disponível em preview; mutações bloqueadas | Navegação reaplicada sem alterar documento; fluxo profissional coberto | PASS |
| D03C-06 | Evidência nas resoluções e fluxo canônicos | Produtor nativo Windows e auditoria visual dedicados | PASS COM LIMITAÇÃO DOCUMENTADA |

## 3. Invariantes protegidos

- Nenhuma operação de zoom, pan ou fit altera o documento persistido.
- Nenhuma operação de zoom, pan ou fit cria histórico, dirty state ou ação de
  salvar.
- Transformações de objetos continuam sendo operações do modelo e não são
  confundidas com navegação da câmera.
- A matemática de fit considera geometria transformada, seleção, visibilidade
  e isolamento conforme o contrato.
- Cena vazia e seleção sem objetos elegíveis são no-ops seguros.
- A navegação não altera QAction, atalhos globais, schema, camera persistida,
  grupos, camadas, sockets ou o editor legado.
- O foco do viewport possui indicador visual; os controles novos têm nomes,
  tooltips e ordem explícita de tabulação.
- Estados hover, pressed, checked, focus e disabled permanecem distinguíveis
  sem depender exclusivamente de cor ou produzir salto de layout.

## 4. Testes automatizados

### 4.1 Focal

`tests/test_p2d_03c_viewport.py`: **6 passed**.<br>
O teste de pan usa eventos `QTest` reais, sem warnings de API depreciada.

`tests/test_p2d_03c_navigation_math.py` e
`tests/test_p2d_03c_professional_flow.py` fazem parte do conjunto focal de
matemática e fluxo profissional e permanecem incluídos na suíte completa.

### 4.2 Suíte completa

```text
1821 passed, 2 skipped, 0 failed
```

Ambiente: Python 3.11.9 da `.venv`, PySide6 6.10.1, pytest 9.1.1.

## 5. Gates e conformance

Os produtores oficiais foram executados contra o source baseline
`4be3b1139e82198147b09a8367eff5119cf3df66`.

| Gate | Resultado | Interpretação |
|---|---:|---|
| G Stage9 responsive/DPI | produtor `FAIL` misto | `capture_dimensions` e `critical_widgets` canônicos passam; o FAIL é o átomo legacy `visual_geometry`/`minimum_size_hint`, já conhecido e não introduzido como requisito deste lote |
| V Stage1 contract | `PASS` | 12 verificações visuais canônicas preservadas |
| B Stage9 functional | produtor `FAIL` misto | `functional_actions` passa; o FAIL é o átomo legacy `visual_geometry`/`minimum_size_hint`, não uma falha de navegação P2D-03C |
| Aggregate gate | `PASS`, `blocking=false` | G60/60, V12/12, B21/21; total 93/93 |

Os resultados mixed legacy continuam visíveis e não foram mascarados. O
aggregate canônico é o gate bloqueante para G/V/B, conforme C3.

## 6. Captura nativa e auditoria visual

Root da evidência pré-commit:

`<external-evidence-root>\neoeng-p2d-03c-precommit-20260830-run01`

Captura r4:

`<external-evidence-root>\neoeng-p2d-03c-precommit-20260830-run01\10-p2d03c-capture-r4`

Auditoria visual r4:

`<external-evidence-root>\neoeng-p2d-03c-precommit-20260830-run01\10-p2d03c-capture-r4-visual-audit\visual-audit-report.json`

Resultado objetivo:

```text
capture producer: PASS
visual audit: PASS
finding_count: 0
captured states: focus, fit-selection-hover, fit-all, pan-pressed,
                 preview-disabled, canonical-1366x768, canonical-1920x1080
```

As imagens foram produzidas com QSS e captura Qt nativa, incluindo geometria
dos widgets profissionais, foco, hover, pressed, checked e disabled. A
auditoria verificou schema, decode Pillow/OpenCV, dimensões, transparência,
hash, clipping, geometria Qt, overlap, contexto de palette e saída anotada.

### 6.1 Limitação de host

No host Windows usado para a captura, a janela lógica solicitada de
`1920x1080` foi limitada pelo espaço disponível para `1920x1060`; a captura
física correspondente foi `3840x2120` em DPR 2. A evidência registra o tamanho
real e não o apresenta como cumprimento exato de `1920x1080`. A resolução
`1366x768` foi capturada em `2732x1536` em DPR 2; o fluxo profissional
`1280x820` foi capturado em `2560x1640`.

## 7. Estado de pré-commit

No momento deste registro:

- a suíte automatizada passa;
- o aggregate canônico passa sem blocking;
- a captura e a auditoria visual passam sem findings;
- a revisão estrutural final confirmou os 13 arquivos staged exatamente
  previstos para o lote;
- ainda não existe commit do P2D-03C;
- ainda não existe seal do P2D-03C;
- P2D-03C ainda não pode ser chamada `ACCEPTED / CLOSED`.

Próxima sequência obrigatória: revisão final da fronteira, `git diff --check`,
stage explícito dos arquivos desta evidência, commit, repetição pós-commit de
testes/gates/captura, comparação, build/release local se aplicável e seal.
