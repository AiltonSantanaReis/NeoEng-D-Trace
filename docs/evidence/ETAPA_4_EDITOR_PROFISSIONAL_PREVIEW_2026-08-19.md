# Evidência — Etapa 4: preview profissional de câmera, parallax e sockets

## Identificação

- Estado: **APROVADO LOCALMENTE / NÃO INTEGRADO**
- Commit-fonte da captura: `9895f5df494ae782697a9531a9352abfb8941a0c`
- Rótulo de branch da evidência: `stage4`
- Captura: `scripts/audit_stage4_professional_scene_capture.py`
- Artefatos: `docs/evidence/artifacts/stage4-professional-2026-08-19/`

O commit-fonte foi capturado com a árvore limpa. O relatório não é uma aprovação de
CI, PR, merge ou release; esses gates permanecem posteriores.

## Escopo comprovado

- contrato profissional explícito `neoeng-d-trace-scene-authoring` schema v2;
- preservação e migração explícita do schema v1, sem reinterpretar campos existentes;
- câmera ortográfica de autoria, profundidade/parallax por camada e zoom determinístico;
- marcadores tipados de luz, VFX e trigger, com validação estrita de referências;
- preview separado no viewport profissional, com atualização após câmera, redimensionamento
  e edição de parallax;
- inspector funcional para câmera, parallax e criação/atualização/remoção de sockets;
- Undo/Redo transacional para alterações da Etapa 4;
- preview sem simular runtime de partículas, shaders, iluminação ou eventos de engine.
  Esses consumidores continuam no escopo de etapas posteriores e não foram mascarados
  como implementados.

## Ambiente e comandos

- Sistema: Windows; Python 3.11.9; PySide6 real; Qt em modo `offscreen` para captura
  reprodutível.
- Testes focados:
  `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_stage3_professional_scene_editor.py tests/test_stage4_professional_scene_authoring.py tests/test_scenario_preview.py tests/test_stage4b2_preview_overlays.py tests/test_stage4b3_scenario_authoring.py tests/test_stage4b4_scenario_export.py tests/test_stage4b5_quality.py --tb=short`
  - resultado: **70 passed**.
- Suíte completa:
  `.\\.venv\\Scripts\\python.exe -m pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing`
  - resultado: **1367 passed, 2 skipped históricos**, cobertura global de branches
    **90,62%**, gate mínimo 90% atendido.
- Gates estáticos: Black, isort, mypy e `git diff --check` — **PASS**.
- Captura e auditoria:
  `.\\.venv\\Scripts\\python.exe scripts/audit_stage4_professional_scene_capture.py --output docs/evidence/artifacts/stage4-professional-2026-08-19`
  - resultado: **PASS; 0 achados**.

Os dois skips são casos históricos já existentes em `tests/test_integration_sync.py`;
nenhum skip, xfail, bypass ou alteração de regra foi criado para esta etapa.

## Auditoria visual automatizada

O auditor leu cada PNG com Pillow e OpenCV, conferiu dimensões e hashes, transparência,
clipping, geometria Qt, sobreposição entre regiões, paleta QSS escura e gerou imagens
anotadas. Foram produzidos 9 PNGs de captura e 9 PNGs anotados, todos RGB, sem alfa
variável e com dimensões iguais às janelas Qt.

| Estado | 1280x720 SHA-256 | 1366x768 SHA-256 | 1920x1080 SHA-256 |
|---|---|---|---|
| Sem projeto | `67885e641880b89b7034252901d8575af1c3fc042ed361b70ee377d8117a98f6` | `e24518d21d986798195981146ab535f53cf5eaa3e4bf7c4882fc5c49b4ea38fd` | `3dbe02ca50d063668cca2e4c85f291e089bbdd003e1e14dd3016efdc2821600f` |
| Projeto/painéis | `25a96d3ada999efcbe977b420c5db172b252b3c0d461c6b5f186c6e257d0dd32` | `5d216410bdd6ed348d6f6c4d5c9363838ba646f7faf89996a49895b0ddf0fe45` | `ca010ed616f3ba16ddca42944330259e1e90d30a55a5f339d9d0a1d73f49e90a` |
| Preview/gizmo | `2534ef490513c484ce31f806f8727763a63a51acf23127db8169470eaa56f856` | `a87190b54c768c1bd0de9caf922bb4cdff2f0c89ca6881e0d995ec41316d7686` | `851048b42fa249c68703c5b9cb303285983e92fee68ded0590ce455d8fdb10e4` |


- SHA-256 do manifest: `91ad47a0aeba6dc0015a6f68e183fd3ef234e90710394aa84b990b430675bf06`
- SHA-256 do relatório visual: `045296192dd3225113d86c2688a0babd0af849bc26a45e7b58be9b557fbedebd`
- Os hashes carregado/preview são diferentes em 1280x720, 1366x768 e 1920x1080;
  a captura falha se a atualização de câmera não mover o objeto projetado.

## Limitações honestas

- A auditoria é offscreen e automatizada; não substitui teste manual de GPU nativa.
- Esta etapa comprova marcadores declarativos e preview determinístico, não a execução
  de efeitos de runtime nem a persistência/importação de schema v2, que pertencem à
  etapa seguinte.
- O fallback informativo de CuPy para CPU apareceu no log e não alterou o escopo da
  captura; não houve falha ou bypass.

## Decisão

A implementação e os testes locais da Etapa 4 estão aprovados no escopo acima.
A etapa somente poderá ser promovida após versionar estes artefatos, revalidar os
blobs Git, executar CI e obter revisão remota. O merge não está autorizado por este
documento.
