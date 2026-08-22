# Etapa 6 — Gizmo profissional: baseline factual

**Estado:** BASELINE APROVADA APENAS PARA ANÁLISE; IMPLEMENTAÇÃO NÃO INICIADA
**Data:** 2026-08-22
**Plano:** `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md`

## Objetivo

Registrar o comportamento efetivamente existente antes de qualquer alteração da Etapa 6. Este documento não declara a implementação do gizmo profissional concluída, não aprova release e não substitui os gates da etapa.

## Proveniência e ambiente

- Commit de origem observado: `425f21df2bbf9a67c01a577b59ae6bbba25995b7`.
- Branch de baseline: `Ailton/stage6-gizmo-baseline`.
- Ambiente: Windows, Python 3.11.9, PySide6 6.10.1, Qt 6.10.1.
- `source_tree_clean=false`: a reconciliação do plano vivo estava em andamento e seis diretórios locais históricos não rastreados foram preservados. Nenhum desses diretórios foi incluído na evidência.
- Código do gizmo: nenhum arquivo alterado nesta etapa de baseline.

## Gates executados

Comandos reais executados no ambiente acima:

```text
.venv/Scripts/python.exe tools/baseline_integrity.py --verify --git-blob
Baseline verified: 2235 files (before inclusion of this baseline package)

.venv/Scripts/python.exe tools/evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 98 manifests validated (before inclusion of this baseline package).

.venv/Scripts/python.exe -m pytest -q tests/test_reference_gizmo.py tests/test_critical_ui_coverage.py tests/test_stage3_professional_scene_editor.py tests/test_stage4_professional_scene_authoring.py tests/test_stage5_viewport_hud.py --tb=short
47 passed in 2.20s

After staging the reconciled plan and baseline package, the Git-blob revalidation reported:
Baseline verified: 2238 files
Evidence integrity passed: 99 manifests validated.
```

O relatório de máquina completo e o manifesto estão em `docs/evidence/artifacts/ui-modernization-stage6-20260822/`.

## Capacidades observadas

- `TransformGizmo` principal com translação X/Y/XY, rotação Z, escala uniforme e escala por eixo.
- Âncora para seleção individual e centro calculado para seleção múltipla.
- Prévia transacional com commit, cancelamento, Escape e integração com histórico.
- Feedback pintado com posição, rotação Z, escala e Z-Depth.
- `SceneTransformGizmo` separado no editor de autoria de cenários.

## Lacunas ou contratos ainda não comprovados

1. Existem duas implementações de gizmo com contratos visuais e de interação separados; equivalência ainda não foi comprovada.
2. Os testes atuais não comprovam o acionamento e a edição por vértice individual em todos os fluxos do gizmo principal.
3. O eixo Z é exibido como metadado; não há arrasto de profundidade comprovado no gizmo 2D.
4. O snapping existente para vértices não foi comprovado como aplicado às transformações de objeto do gizmo.
5. O feedback numérico é visual e somente leitura; edição numérica dedicada e comportamento completo em seleção múltipla ainda não foram comprovados.
6. Acessibilidade de teclado, foco e nomes acessíveis dos handles ainda não foi comprovada.
7. Ainda não existem capturas dedicadas da Etapa 6 para limites de hit-test, DPI, redimensionamento, seleção múltipla e undo/redo.

## Hashes dos contratos observados

| Arquivo | SHA-256 | Git blob SHA-1 |
|---|---|---|
| `src/ui/gizmo_reference.py` | `BE79C685FF5CC9A42D77C89FABB2EE1B6E6943E56D1B6A2FC3F5F3A74BE04EF9` | `d07a8d9f797b0704fccce52713e16a03a36c376d` |
| `src/ui/gizmo.py` | `F465CC29C2D945D94504B8DD0121F99DC45A890DA24572CBF04B60E9AF03C137` | `8993e9f6329592a236b3408fed6659c30ee9731f` |
| `src/ui/canvas_view.py` | `CD87E5C00AFB8F1CE1891F5A8326B1376E0E7239CA9D0055FF1E8BEF8393C416` | `11e2c39c2a86d6bc974c1c69a0ba7a3304a0d8fd` |
| `src/ui/scene_authoring_viewport.py` | `BB0280397AC1B062F83943096C1C52365832BFCD4B985851F8F57636F84D0D98` | `9b97341ce725b867aeec948c70ecf8d89894384c` |
| `src/core/transform_gesture.py` | `1FD8A2CA8661385361D4FDB10D3F03F56E6D6DE4DCD0BBCF269D720A8CAEC5CC` | `fc07f3542745f98f3a2d8de5a8e1ebecaaf26cc5` |

## Próximos gates obrigatórios da implementação

A Etapa 6 somente poderá avançar após caracterização adicional e implementação comprovada de hit-test, posicionamento, modos, feedback e acessibilidade, com preservação do contrato transacional existente. O gate deverá incluir testes positivos e negativos, seleção de objeto/vértice, seleção múltipla, snapping, limites, DPI, redimensionamento, undo/redo, capturas reais anotadas e análise dos artefatos. Depois disso seguem revisão de diff, baseline/evidência por blobs Git, commit, push, PR, CI, autorização de merge e validação pós-merge.

**Decisão:** baseline factual registrado; Etapa 6 permanece `PLANEJADA / IMPLEMENTAÇÃO NÃO INICIADA`.
