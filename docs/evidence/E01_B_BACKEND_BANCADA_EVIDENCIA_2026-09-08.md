# E01-B — evidência da bancada de backend

**Estado:** `PASS_LOCAL` para a qualificação isolada; integração no produto não iniciada.  
**ADR:** `docs/ADR_E01_B_BACKEND_BANCADA_2026-09-08.md`  
**Script:** `scripts/e01_backend_bench.py`  
**Artefato:** `artifacts/e01-independent-scene-20260908/backend-bench-r11/backend-bench.json`

## Execução

Comando:

```powershell
.venv\Scripts\python.exe scripts/e01_backend_bench.py `
  --output artifacts/e01-independent-scene-20260908/backend-bench-r11
```

Resultado: `PASS_LOCAL`, Windows AMD64, Python 3.11.9, PySide6/Qt 6,
`QT_QPA_PLATFORM=default`.

Os dois candidatos renderizaram a mesma fixture determinística. O raster foi
validado em imagem Qt; o OpenGL foi validado em `QOpenGLWidget` real, com
`GL_DEPTH_TEST`, captura, resize de framebuffer físico e recuperação após
`makeCurrent/doneCurrent`.

## Capturas

- [raster-frame.png](../../artifacts/e01-independent-scene-20260908/backend-bench-r11/raster-frame.png) — SHA-256 `4360e6c219407ab78567f4efb4f53aa71a3ba7299ab8351505fc037f0ddedeaf`.
- [opengl-frame.png](../../artifacts/e01-independent-scene-20260908/backend-bench-r11/opengl-frame.png) — SHA-256 `4bc4c41c6db085c4defc1d4791b4e08ec21c4023a1b2c55e5a5e86fede3a7aa6`.

As capturas foram inspecionadas visualmente: ambas exibem grade ortográfica,
quadrado alfa, círculo iluminado, partículas e a moldura de camada.

## Limites de aceite

Esta evidência não encerra E01: ela conclui somente a bancada isolada E01-B.
Não houve alteração do renderer do produto, não há integração de efeitos E08 e
nenhum resultado local foi promovido a garantia universal.
