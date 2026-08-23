# Etapa 2 — Biblioteca de ícones e matriz DPI — 2026-08-23

**Estado:** `PASS_LOCAL / AGUARDANDO PR, CI E PÓS-MERGE`

## Objetivo e escopo

Fechar a lacuna registrada na reconciliação de 2026-08-22: comprovar o
catálogo vetorial da Etapa 2 nas escalas Qt de 100%, 125%, 150% e 200%, com
capturas reais, dimensões lógicas e físicas, hashes, clipping, auditoria visual
e testes positivos/negativos. O catálogo, as ações, os fallbacks, os tamanhos
16/20/24/32 px e os thresholds existentes não foram alterados.

## Proveniência

- Branch: `Ailton/stage2-icon-dpi-matrix`.
- Commit técnico auditado: `033278c52c12279c59b39fb9766fa5a02dcab5ed`.
- Ambiente: Windows 10 build `10.0.26200`, Python `3.11.9`, PySide6/Qt do
  ambiente `.venv`.
- Backend: `QT_QPA_PLATFORM=offscreen`.
- Artefatos: `docs/evidence/artifacts/ui-modernization-stage2-dpi-20260823-r3/`.
- O relatório registra `worktree_clean=false` porque existem diretórios locais
  históricos não rastreados; não há alteração rastreada fora do escopo.

## Comandos executados

```text
.\.venv\Scripts\python.exe -m pytest -q tests\test_stage2_icon_dpi_matrix.py tests\test_stage2_ui_icons.py --tb=short
.\.venv\Scripts\python.exe -m black --check scripts\audit_stage2_icon_dpi_matrix.py tests\test_stage2_icon_dpi_matrix.py
.\.venv\Scripts\python.exe -m isort --check-only scripts\audit_stage2_icon_dpi_matrix.py tests\test_stage2_icon_dpi_matrix.py
.\.venv\Scripts\python.exe -m flake8 scripts\audit_stage2_icon_dpi_matrix.py tests\test_stage2_icon_dpi_matrix.py
.\.venv\Scripts\python.exe -m py_compile scripts\audit_stage2_icon_dpi_matrix.py tests\test_stage2_icon_dpi_matrix.py
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe scripts\audit_stage2_icon_dpi_matrix.py --output docs\evidence\artifacts\ui-modernization-stage2-dpi-20260823-r3
.\.venv\Scripts\python.exe -m pytest -q
```

A suíte inicial de coleta revelou uma falha de privacidade no procedimento:
um log escrito dentro da árvore capturou o traceback da própria falha e expôs
um padrão de caminho. O teste não foi alterado. Os logs falhos foram preservados
com o padrão sanitizado e a suíte final foi executada com saída fora do
repositório, sendo copiada somente após o término bem-sucedido.

## Resultados objetivos

| Escala | Fator Qt/DPR observado | Galeria lógica | Galeria física | Células | Clipping | Auditor visual |
|---:|---:|---:|---:|---:|---:|---|
| 100% | 1.0 | 572×1772 | 572×1772 | 144 | 0 | PASS |
| 125% | 1.25 | 572×1772 | 715×2215 | 144 | 0 | PASS |
| 150% | 1.5 | 572×1772 | 858×2658 | 144 | 0 | PASS |
| 200% | 2.0 | 572×1772 | 1144×3544 | 144 | 0 | PASS |

Cada célula representa uma chave do catálogo nas quatro variantes 16/20/24/32
px. As capturas da MainWindow também foram geradas em cada escala e submetidas
ao auditor Pillow/OpenCV/Qt. O pacote matriz retornou `status=PASS` e zero
achados em todas as escalas.

- Testes focados: `8 passed`.
- Privacidade após a sanitização procedural: `3 passed`.
- Suíte integral final: `1617 passed, 2 skipped`.
- Black, isort, Flake8, py_compile e `git diff --check`: PASS.
- Os dois skips permanecem históricos, condicionados à permissão de symlink no
  Windows; não foram criados ou modificados nesta etapa.

## Artefatos e hashes

O índice SHA-256 completo está em:
`docs/evidence/artifacts/ui-modernization-stage2-dpi-20260823-r3/artifact-index.json`.
Ele inclui os quatro manifests de captura, quatro relatórios visuais, quatro
galerias PNG, relatórios de runtime, logs dos workers, logs de falhas
sanitizados e o log final da suíte.

O relatório principal é:
`docs/evidence/artifacts/ui-modernization-stage2-dpi-20260823-r3/stage2-dpi-matrix-report.json`.

## Revisão visual e limitações

As galerias foram revisadas visualmente em cópias reduzidas temporárias. As
quatro colunas de tamanho permanecem nítidas e consistentes; nenhum ícone
tocou a borda da célula. As etiquetas textuais da galeria aparecem como blocos
no backend offscreen por limitação de fonte desse backend. Isso foi declarado,
não foi convertido em PASS de tipografia e não altera a comprovação dos
ícones vetoriais. A confirmação visual no backend nativo Windows permanece
parte dos gates de CI/revisão final.

A matriz comprova a escala Qt controlada por `QT_SCALE_FACTOR` em processos
reais. Ela não altera o DPI global do Windows, não troca monitores e não prova
comportamentos específicos de driver ou de configuração física do desktop.

## Decisão

`PASS_LOCAL`: a lacuna de matriz Qt 100/125/150/200%, hashes, clipping e
auditoria visual foi implementada e reproduzida. A Etapa 2 ainda não é
formalmente aprovada: faltam staging exato, baseline/evidência por blobs Git,
PR, CI no SHA candidato e validação pós-merge no `main`.
