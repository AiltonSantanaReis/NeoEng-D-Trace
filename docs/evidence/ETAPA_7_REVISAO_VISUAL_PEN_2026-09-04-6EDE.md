# Revisão visual humana da Caneta — candidata `6ede2f6` — 04/09/2026

## Resultado

`PASS` no escopo exclusivo da revisão visual humana das seis capturas
reproduzíveis vinculadas ao produto no SHA
`6ede2f6073f6d2aaf5a394e4043019a3ac85a5e4`, branch
`Ailton/legacy26-closure-audit`.

Confirmação explícita do proprietário do projeto:

> Confirmo a revisão visual humana das seis capturas vinculadas ao SHA
> `6ede2f6…`; os estados estão corretos.

## Estados inspecionados

| Estado | Captura | Tamanho | SHA-256 |
| --- | --- | ---: | --- |
| Prévia de fechamento pelo primeiro vértice | `pen-close-preview.png` | 29020 | `37279f8377e6b9413b72c86352ea505683c95da8a190ccb3c2b454e54b0b62f0` |
| Fechamento persistido | `pen-closed-persisted.png` | 33373 | `edb88d53511d983f434c4c2cec83a229197160f5e90d061570c5cd3d7bcfe9cf` |
| Fechamento inválido rejeitado | `pen-invalid-close.png` | 28526 | `f99a5a1923783c6aa3c14728409053ba036ec1eab04e73ac938c88a211f87f62` |
| Após Undo | `pen-after-undo.png` | 23683 | `cb71c1071a1a9f56e9090ebc10c93a6126d3d1f8cc5156c25518680d38504ebc` |
| Após Redo | `pen-after-redo.png` | 30470 | `c8bd261434ef8781406ff742753f860dc5aa11dc0516aa2eab69ae2739a999ce` |
| Duplo clique mantendo caminho aberto | `pen-double-click-open.png` | 31965 | `4be1941dcad4fc9caabf2716b3cb5a1d3474307fb892692fe4e6629baeb32ead` |

## Proveniência e decisão

O pacote `docs/evidence/artifacts/pen-tool-revalidation-20260904-6ede/` foi
produzido em checkout limpo por `scripts/audit_pen_tool_visual.py`, usando
`QApplication`, `QTest` e eventos Qt reais. Os quatro checks automatizados
passaram: fechamento válido, rejeição inválida preservando estado, Undo/Redo
e duplo clique. O `artifact-index.json` registra `12/12` arquivos com bytes e
SHA-256; `human-review.json` contém a confirmação acima.

O SHA anterior `5aec9ae…` não é promovido: seu gate local revelou falhas de
Flake8 e, durante a correção de formatação, uma regressão de tipo de tooltip
foi detectada e corrigida antes desta nova execução. O histórico permanece
preservado.

A revisão visual é uma subetapa `PASS` da C12. Os gates locais completos,
incluindo empacotamento atual, estão consolidados em
`docs/evidence/ETAPA_7_GATES_FINAIS_2026-09-04-6EDE.md` e passaram no mesmo
SHA de produto. A C12 local está `PASS`; C13 permanece `PENDING_REMOTE_CI`
até o push, a PR sem merge e a análise dos jobs remotos. Esta evidência não
autoriza merge, tag ou release.
