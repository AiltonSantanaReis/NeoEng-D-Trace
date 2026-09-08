# E01-A — cena independente: evidência do lote

**Estado do lote:** `TECHNICAL_CHECKPOINT_PASS` — contrato, fluxo automatizado e captura real do r5 executados; aceite final segue subordinado à auditoria do plano.

**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`  
**Plano:** `e00-plan-adoption-20260907/docs/PLANO_EVOLUCAO_INCREMENTAL_PRESERVACAO_2026-09-07.md`  
**Requisitos do plano:** `SCN-001`, bases de `SCN-003/004`, `ENT-004`, `UX-001/002/003`  
**Branch:** `Ailton/e01-independent-scene-20260908`

## Resultado comprovado

- Contrato independente em `.ndtscene`, sem `ProjectReferenceRecord` fictício e sem SHA de projeto.
- Fluxo Qt real de novo, abrir, salvar e salvar como coberto por testes; a janela mantém estado sujo, resolução, câmera e coordenadas explícitas.
- QAction do menu e atalho `Ctrl+Alt+N` compartilham o mesmo caminho executável.
- Correção registrada em `a2070f65d2c5d3881fb9d781ec2bb4784d13dc53`; proteção de conflito em `361a635107b87e8f6cabbe820b42d6ee2eab29cd`.

## Verificações

| Verificação | Comando/artefato | Resultado |
|---|---|---|
| Fluxo independente | `tests/test_independent_scene_contract.py` + `tests/test_independent_scene_ui.py` | `10 passed` |
| Regressão de toolbar/layout | `tests/test_stage4_ui_top_toolbar.py` + `tests/test_ui_responsive_layout.py` | `12 passed` |
| Suíte oficial | `.venv\\Scripts\\python.exe -m pytest -q` | `1969 passed, 2 skipped, 1 warning` |
| Estático | `compileall`, `black --check`, `isort --check-only`, `flake8`, `git diff --check` | `PASS_LOCAL` |
| Build portátil | `scripts/build_windows.ps1 -OutputRoot release\\e01-independent-scene-20260908-r5` | `PASS`, smoke com 11 checks |
| Executável | `release/e01-independent-scene-20260908-r5/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | SHA-256 `8B17406ECB394B4C3D25D7E37721F8244141B2B985F4B137FD2DB907CCF92188` |

## Captura real do binário

Capturador reproduzível: `scripts/capture_independent_scene_binary.ps1`.

Manifesto: `artifacts/e01-independent-scene-20260908/captures-r5/capture-manifest.json`.

- Janela principal: [01-main-before-independent.png](../../artifacts/e01-independent-scene-20260908/captures-r5/01-main-before-independent.png), `2426x1719`, SHA-256 `52059515B539B9E1F3B6A280C7F4149A8152C2ED7D0379DB8DF293ACA5D744F8`.
- Janela independente: [02-independent-scene-after-shortcut.png](../../artifacts/e01-independent-scene-20260908/captures-r5/02-independent-scene-after-shortcut.png), `1986x1431`, SHA-256 `2975F04978004ED66172A131F56E215C5CA97F299B6E0C19AE0824DB584652B8`.
- A captura da segunda janela foi obtida após iniciar o `.exe` acima, ativar a janela principal e enviar `Ctrl+Alt+N` por Win32; o título observado foi `Cenário Independente — Untitled Scene`.
- Observação visual: a janela exibe toolbar PT-BR, canvas vazio `1920 × 1080`, `top_left, pixel` e campos de resolução/câmera. A captura veio exclusivamente do executável do projeto.

## Limitações ainda abertas

- Os dois skips da suíte continuam `SKIP_PRIVILEGE_LIMITATION` e permanecem deliberadamente adiados para a auditoria final de symlinks; não são convertidos em `PASS`.
- A revisão humana/native final continua `PENDING_EVIDENCE` conforme autorização do proprietário; a captura automatizada comprova apenas o estado observado nas imagens.
- Este documento não encerra E01: a comparação isolada de backend E01-B e os demais critérios de E01-C ainda precisam ser executados segundo o plano.
