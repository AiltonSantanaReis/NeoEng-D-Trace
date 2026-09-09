# E10 — exportação real e round-trip Godot/Unity

**Data de abertura:** 2026-09-08  
**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Plano Mestre:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Status:** `IN_PROGRESS` — E10-A/B/C technical checkpoints passed; E10-D é o próximo gate

## Contrato de execução

E10 implementa e comprova `EXP-001/002/003/004/005`, integrando os recursos
qualificados em E01–E09. O aceite distingue explicitamente:

1. save/reopen interno do documento;
2. exportação para um pacote validado;
3. importação em projeto limpo da engine;
4. execução real e comparação visual/funcional;
5. retorno à autoria, somente se houver importador reverso e política de
   identidade/conflito implementados.

JSON/sidecar isolado não será tratado como execução real. Cada destino terá
versão detectada, capacidades suportadas, diferenças aceitáveis, negativos,
logs e capturas nativas.

## Inventário inicial verificável

- Godot foi localizado no host como `C:\ProgramData\chocolatey\bin\godot.exe`;
  a versão e a execução headless serão registradas no primeiro sublote.
- Nenhum executável Unity foi localizado pelos comandos de descoberta do host;
  a integração Unity permanece uma lacuna de disponibilidade externa até que
  um runtime qualificável seja encontrado, sem converter scaffold C# em prova
  de engine real.
- O repositório já contém adapters, validadores e plugins Godot/Unity; eles
  serão usados como implementação candidata e não como evidência de consumo
  até a execução correspondente.

## Fila E10

| Sublote | Status | Saída obrigatória |
|---|---|---|
| E10-A contrato/capacidades | `IN_PROGRESS` | matriz por destino e versão, propriedades preservadas, conversões e limites |
| E10-B exportação efetiva | `PLANNED` | pacote temporário validado, hash, atomicidade e negativos |
| E10-C importação/execução Godot | `PLANNED` | projeto limpo, importador real, runtime, logs e capturas |
| E10-D importação/execução Unity | `PLANNED` | runtime Unity real, ou lacuna de disponibilidade explicitamente mantida |
| E10-E round-trip/fechamento | `PLANNED` | comparação visual/funcional, retorno somente se implementado, suíte e manifesto |

## Regras de evidência

- Não declarar round-trip visual completo com base somente em JSON.
- Usar fixtures assimétricas para revelar inversão de eixo, escala, pivô e
  rotação.
- Preservar saída válida anterior durante exportação interrompida ou inválida.
- Manter symlink e revisão humana exclusivamente na auditoria final.

Este documento será atualizado somente com comandos, versões, hashes, logs,
capturas e limitações reproduzíveis.

## E10-A/B/C — exportação efetiva e consumo Godot

- Correção aplicada no commit `4ba005d`: o importador Godot agora aceita e
  materializa `vector_geometry` como `StaticBody2D` + `CollisionPolygon2D`; o
  importador Unity preserva a mesma geometria em `PolygonCollider2D` e valida o
  hash da fonte quando o recurso vetorial existe.
- Auditoria real Godot:
  `python -m scripts.audit_e10_godot_professional_vector --output artifacts/e10-godot-c6-20260908`
  — `PASS`.
- Engine detectada: Godot `4.7-stable (official)`.
- Export efetivo: `artifacts/e10-godot-c6-20260908/scene.godot.runtime.json`,
  SHA-256 `816f18f4b046e9becb7257dcc941c9c912024e0e259994247958e061f164df9a`.
- Execução real confirmou `E10_GODOT_VECTOR_VALIDATION=SUCCESS`, sprite
  carregado, objeto importado e colisão com 4 pontos. O log completo e os
  comandos estão em `artifacts/e10-godot-c6-20260908/report.json`.
- Negativo real: após adulterar `assets/scene/subject.png`, o importador
  recusou a cena com `professional scene asset hash does not match`; o relatório
  marca `negative_hash.rejected=true` e restaura a fonte válida.
- Regressão Python focada: `80 passed` em persistência/exportação, adapters,
  E09 e registro de continuidade. A suíte oficial anterior ao lote permanece
  `2098 passed, 2 skipped, 1 warning`; uma nova suíte completa será executada
  depois de E10-D/E10-E.

## E10-D — Unity

- Nenhum executável Unity foi localizado no host (`Get-Command Unity` e
  `Get-Command Unity.exe` sem resultado). O scaffold e o código C# não são
  promovidos a prova de engine real.
- O adapter Unity já recebeu a preservação de `vector_geometry`, mas o gate
  de importação/execução real permanece aberto até existir runtime qualificável.
  Enquanto isso, a execução continua com validações estáticas e Godot, sem
  declarar E10 concluída.

## Build e captura do produto após a correção

- Build oficial limpa r53:
  `release/e10-vector-import-20260908-r53`, source commit
  `a09a0819494e01c0bbc5531bbdedc3604f6d07a0`, executável SHA-256
  `067427523A63C75493CFE3E3A9E5A6811A7744EB0E4A98E06CB1E4BE3BAE8D69`,
  archive SHA-256
  `a0afd5c33c36a86f839ea39938e8f4f6c8dffdcdd23b47eb3771882261e0d6e4` e
  smoke `SUCCESS` com 11 verificações.
- Captura nativa do binário r53:
  `artifacts/e10-godot-c6-20260908/binary-capture-r53-regression/`.
  O fluxo E09 foi repetido após a build: `11-vector-contour-created.png`,
  SHA-256 `E8ADA633B2E1E4E5DEF443893DA8B15EF896F6DF3DE5B8A8E5089249CB2A3A02`, confirma detecção,
  correção manual, criação do objeto, gizmo e feedback no produto.

E10-D permanece aberto exclusivamente pela ausência de runtime Unity
qualificável no host; essa ausência não é mascarada como PASS.

## E10-D — diagnóstico de disponibilidade

- Comando formal:
  `python tools/validate_engine_exports.py --engine unity --report artifacts/e10-unity-d-20260908/report.json`.
- Resultado: `FAILED` esperado, `FileNotFoundError: unity executable not found`;
  o relatório não é convertido em PASS nem em falha funcional do produto.
- Busca adicional em `Program Files`, `Program Files (x86)`, `ProgramData`,
  `AppData/Local` e `AppData/Roaming` não encontrou `Unity.exe`,
  `UnityEditor.exe` ou `UnityHub.exe`. O .NET SDK instalado não substitui o
  runtime Unity e não permite declarar importação/execução real.

Este é o único ponto que exige decisão externa: fornecer o caminho de um Unity
Editor qualificável ou autorizar a instalação de uma versão compatível. Sem uma
dessas opções, E10-D/EXP-003 não pode ser concluído honestamente; o registro
central permanece `IN_PROGRESS`, sem marcar `BLOCKED` ou mascarar a lacuna.
