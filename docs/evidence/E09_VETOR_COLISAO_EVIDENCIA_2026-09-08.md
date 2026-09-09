# Evidência E09 — autoria vetorial, colisão e integração

**Data:** 2026-09-08  
**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Plano Mestre:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Estado:** `E09-A/B/C TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING; E10 é o próximo lote técnico`

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

## E09-B — edição reversível do contorno

- Implementação: commit `2c4b17c`; suíte oficial após o lote: `2091 passed,
  2 skipped, 1 warning`.
- `src/core/contour_editing.py` preserva o polígono original e a proveniência,
  suporta mover/inserir/remover vértices, simplificação RDP/OpenCV limitada,
  Undo/Redo, validação transacional e cancelamento explícito.
- Uma edição inválida não altera o estado; o cancelamento restaura o original e
  impede o uso posterior da sessão cancelada.
- Auditoria oficial:
  `python -m scripts.audit_e09_contour_editing_phase2 --output artifacts/e09-vectorization-20260908/audit-e09-b-2c4b17c`
  — `PASS`, Undo/Redo exato, proveniência preservada, simplificação de 10 para
  4 vértices e cancelamento restaurando o contorno original.
- Build r50: `release/e09-contour-editing-20260908-r50`, source commit
  `efa3b97fa37906675afd3588439bfb3bfc489c0c`, executável SHA-256
  `8D03A986EDE5E26966E464661E48E444082A1EE837A5507F027E91C0CFF0EE94`.
- Smoke portátil: `SUCCESS`, 11 checks. Captura real do binário em
  `artifacts/e09-vectorization-20260908/binary-capture-r50-regression/`;
  Preview e Autoria mantiveram hashes `54BD8925...DB6D` e `F7D6BF3E...BBE30`.

E09-B comprova o núcleo reversível de edição, mas ainda não reivindica um
 painel nativo de contorno. Colisão, integração como objeto de cenário,
 persistência sem dependência de path externo, combinação, duplicação e
 export/import permanecem E09-C.

Symlink e revisão humana continuam reservados à auditoria final autorizada.

## E09-C — colisão, objeto reutilizável, persistência e exportação

- Implementação de recurso vetorial e colisão: commit `eb8152a`; ancoragem da
  suíte: `6ce6cf5`.
- `SceneVectorGeometryRecord` preserva algoritmo, hash SHA-256 da fonte,
  dimensões, parâmetros de detecção, polígono original, polígono editado e
  polígono de colisão. O objeto é criado transacionalmente no documento e pode
  ser duplicado sem perder proveniência.
- Save/reopen verifica os hashes dos assets relativos e rejeita a fonte
  adulterada. O export genérico V2 foi validado para manter a geometria de
  colisão; consumo de engine continua no E10.
- Auditoria oficial:
  `python -m scripts.audit_e09_vector_scene_phase3 --output artifacts/e09-vectorization-20260908/audit-e09-c-fee6cf5`
  — `PASS`; colisão com 4 vértices, duplicação determinística, save/reopen,
  export genérico e rejeição de tamper.
- Testes focados E09-C + UI: `7 passed`. Suíte oficial após o lote:
  `2098 passed, 2 skipped, 1 warning`.

## E09-C — fluxo nativo no binário portátil r52

- Integração da UI nativa: commit `f1fbebb`; correção do harness de captura:
  `a05b5fa`.
- Build oficial:
  `release/e09-vector-ui-20260908-r52`, source commit
  `f1fbebbbd2de79e359c7b5126d9e98c37507a35f`, executável SHA-256
  `E99C54B7C3754FEDC3A1E8324C3FFC01C523E9B5ED3CB18B2CEB71BC2BFBD135`,
  smoke `SUCCESS` com 11 verificações.
- Manifesto completo: `docs/evidence/E09_C_R52_VECTOR_UI_CAPTURAS_MANIFESTO.json`.
- Captura real válida:
  `artifacts/e09-vectorization-20260908/binary-capture-r52-vector10/`.
  O roteiro abriu o binário, carregou uma cena V2 com asset real, rolou a
  biblioteca, selecionou `vector-source`, detectou 4 vértices, aplicou uma
  correção manual (`X=-5`, `Y=-5`) e criou o objeto de cena. As imagens
  `09-vector-contour-detected.png`, `10-vector-contour-edited.png` e
  `11-vector-contour-created.png` foram inspecionadas por captura nativa.
- O harness inicialmente expôs dois defeitos reproduzíveis: BOM UTF-8 em
  PowerShell e fixture V1 que exigia migração explícita. Ambos foram corrigidos
  em `a05b5fa`; a captura r52-vector10 foi repetida após as correções.

E09-C está tecnicamente concluído com auditoria final pendente. E10 é o próximo
lote e deve validar importação/execução real por destino aplicável; symlink e
revisão humana permanecem reservados à auditoria final autorizada.
