# Evidência E09 — autoria vetorial, colisão e integração

**Data:** 2026-09-08  
**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Plano Mestre:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Estado:** `E09-A TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING; E09-B ACTIVE`

## E09-A — importação e detecção controlada

- Implementação e contrato: commit `73e86a6`; correção de governança dos
  artefatos gerados: `d2acca7`.
- `src/core/vectorization.py` usa a camada de entrada de imagem já limitada,
  hash SHA-256 do arquivo, decodificação RGBA, limiar alpha/luminância,
  `RETR_TREE`, aproximação determinística e validação de polígono simples.
- A saída preserva `source_path`, `source_sha256`, formato, dimensões,
  parâmetros, algoritmo, área e vértices canônicos; a ordem dos vértices é
  estável e a orientação é normalizada.
- Imagens ilegíveis, vazias, fora dos limites, com múltiplas ilhas ou com furos
  são rejeitadas com códigos acionáveis. Nenhuma topologia incompatível é
  descartada silenciosamente.

## Verificações executadas

- Focado E09-A + regressão GrabCut: `26 passed`.
- Auditoria oficial:
  `python -m scripts.audit_e09_vectorization_phase1 --output artifacts/e09-vectorization-20260908/audit-e09-a-73e86a6`
  — `PASS`, repetição determinística, hash esperado, mudança de hash após
  mutação e negativos `invalid_image`, `unsupported_islands` e
  `unsupported_holes`.
- Suíte oficial: `2086 passed, 2 skipped, 1 warning`.
- Qualidade estática no escopo: Black, Flake8, compileall e `git diff --check`
  passaram. O warning conhecido é a depreciação de `QMouseEvent` em
  `tests/test_merge_coverage_authoring_contracts.py`.

## Build e evidência visual real

- Build r49: `release/e09-vectorization-20260908-r49`.
- Source commit da build: `d2acca784a78d3d730b412300d88fe2c12811105`.
- Executável portátil:
  `release/e09-vectorization-20260908-r49/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- Executável SHA-256:
  `6DD781889B4FD8AEAD089E2955A23E45D86DF31948DDA744ECB8079897F2AC9A`.
- Smoke portátil: `SUCCESS`, 11 checks.
- Captura real do executável, com fixture V2 carregada diretamente:
  `artifacts/e09-vectorization-20260908/binary-capture-r49-regression/`.
- Preview:
  `06-renderer-preview.png`, SHA-256
  `54BD892508DF62B2C1AD45D8F856E21E88226E7D144A613452261BDB5E22DB6D`.
- Autoria:
  `07-renderer-authoring.png`, SHA-256
  `F7D6BF3E53947B5E1F1F5FD176AC5079A4BD30B85E72692E71748ED0D62BBE30`.
- Fluxo de projeto e biblioteca de assets:
  `03-main-after-project-load.png` e `05-asset-library-ready.png`.
- As capturas comprovam abertura do binário, carregamento do projeto, troca
  Preview/Autoria e preservação visual do renderer; não são apresentadas como
  prova de uma UI E09-B que ainda não foi implementada.

## Limites e próxima meta

E09-A entrega a fronteira técnica de importação e detecção. A UI de correção
manual, simplificação, validação interativa, geração de colisão, criação de
objeto de cena e save/reopen permanecem no E09-B/C e não são anunciadas como
concluídas. A próxima meta é E09-B: tornar o contorno revisável com histórico,
validação explícita e diagnóstico de cancelamento/limites.

Symlink e revisão humana continuam reservados à auditoria final autorizada.
