# E10 — exportação real e round-trip Godot/Unity

**Data de abertura:** 2026-09-08  
**Worktree oficial:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Plano Mestre:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Status:** `IN_PROGRESS` — E10-A/B/C/D technical checkpoints passed; E10-E é o próximo gate

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
- Unity Editor foi localizado e qualificado no host em `6000.5.7f1`; a
  integração somente foi promovida após execução real do projeto limpo e
  captura nativa.
- O repositório já contém adapters, validadores e plugins Godot/Unity; eles
  serão usados como implementação candidata e não como evidência de consumo
  até a execução correspondente.

## Fila E10

| Sublote | Status | Saída obrigatória |
|---|---|---|
| E10-A contrato/capacidades | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | matriz por destino e versão, propriedades preservadas, conversões e limites |
| E10-B exportação efetiva | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | pacote temporário validado, hash, atomicidade e negativos |
| E10-C importação/execução Godot | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | projeto limpo, importador real, runtime, logs e capturas |
| E10-D importação/execução Unity | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | runtime Unity real, collider vetorial, captura e negativo de hash |
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
  E09 e registro de continuidade. A suíte oficial executada na fronteira atual
  permanece `2098 passed, 2 skipped, 1 warning` (`python -m pytest -q`, 73,46 s).
  Os dois `SKIP` continuam sendo os testes de symlink, deliberadamente adiados
  para a auditoria final; o aviso é uma depreciação do construtor Qt e não
  alterou o resultado.

## E10-D — Unity

- Runtime real localizado via registro do Unity Hub:
  `C:\Program Files\Unity\Hub\Editor\6000.5.7f1\Editor\Unity.exe`.
  O harness básico confirmou criação de projeto limpo, importação GLB e
  `ENGINE_VALIDATION=SUCCESS`; relatório:
  `artifacts/e10-unity-d-20260908/report.json`.
- A primeira execução profissional revelou um defeito real de compatibilidade:
  `JsonUtility` materializa uma classe opcional vazia e o importador interpretava
  isso como `vector_geometry` inválido. A correção foi registrada no commit
  `9708861`: o importador distingue payload ausente de payload parcial, sem
  relaxar a validação quando a geometria está presente.
- Fixture profissional assimétrica agora inclui `vector_geometry` ligado ao
  SHA da imagem e um polígono de quatro pontos. O validator Unity verifica
  transformações, pivô, flip, renderização e `PolygonCollider2D` com quatro
  pontos.
- Execução real aprovada no Unity `6000.5.7f1`:
  `artifacts/e10-unity-d-20260908/professional-work-report.json` —
  `P2D04_UNITY_VALIDATION=SUCCESS`, `P2D04_UNITY_RENDER_PIXELS=266` e
  `negative_hash.rejected=true`. A captura real é
  `professional-work/unity-project/unity-professional-capture.png`, SHA-256
  `4F96FEB7A3CA0681538A02108BE0D4A1007C21429DBDF2D3783132BBCE8D829C`.
- O negativo executado no mesmo projeto adulterou `Assets/assets/hero.png` e
  foi recusado com `asset hash does not match`; o asset foi restaurado e o SHA
  válido final é `252E9339BE02074658C2AE8DA520281C8B1A1799F56C48825F9CECCE78A09C8B`.
- O harness profissional foi corrigido para inserir explicitamente o root do
  worktree no `sys.path`; o Godot foi reexecutado com a mesma fixture e passou
  em `4.7-stable (official)`, com `P2D04_GODOT_RENDER_PIXELS=14400`.

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

E10-D possui checkpoint técnico `PASS` nos dois destinos executados. E10-E
permanece aberto para consolidar comparação, round-trip permitido pelo
contrato, manifesto e fechamento do lote.

## E10-D — diagnóstico de disponibilidade resolvido

- Comando formal:
  `python tools/validate_engine_exports.py --engine unity --report artifacts/e10-unity-d-20260908/report.json`.
- Resultado do harness básico: `SUCCESS`, Unity `6000.5.7f1`.
- Resultado profissional: `SUCCESS`, com collider vetorial, captura e negativo
  de hash no relatório `professional-work-report.json`.
- A limitação anterior de disponibilidade foi encerrada com evidência real;
  nenhuma ausência de runtime permanece aberta em E10-D.
