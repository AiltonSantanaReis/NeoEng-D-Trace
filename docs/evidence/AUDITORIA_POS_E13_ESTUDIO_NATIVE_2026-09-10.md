# Auditoria pós-E13 — estúdio nativo de cenário/parallax

**Status global:** `IN_PROGRESS`  
**Commit auditado:** `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Worktree:** `build/e01-independent-scene-20260908`

## Governança aplicada

Executada a governança de integridade antes das etapas de correção, regressão,
captura nativa, build e runtime. A suíte integral não foi filtrada, nenhum
teste foi removido e a falha anterior foi preservada até a correção comprovada.

## Evidências

| Requisito | Status | Evidência |
|---|---|---|
| STUDIO-01 | `PASS` | `tests/test_post_e13_scene_studio.py`, fluxo nativo `01`–`04` |
| STUDIO-02 | `PASS` | fluxo nativo `05`–`07`, sequência versionada e save/reopen |
| STUDIO-03 | `PASS` | R7: luz/fogo, texto de cutscene, WAV real, player, erro de asset ausente, recuperação e persistência |
| STUDIO-04 | `IN_PROGRESS` | suíte integral e fluxo nativo R7 passaram; build final do novo commit ainda pendente |

### Testes

- Suíte oficial: `2151 passed, 2 skipped, 1 warning`.
- Diagnóstico focado pós-E13/UI: `25 passed`.
- `git diff --check`: `PASS` antes do commit.
- Continuidade: `CONTINUITY_REGISTRY=PASS`.

### Fluxo nativo fonte

Manifesto: `artifacts/post-e13-native-flow-20260910-r7/manifest.json`  
Capturas: `artifacts/post-e13-native-flow-20260910-r7/captures/`  
Modo: janela Qt nativa Windows (`native_window=true`, `qt_platform=native-default`).

Fluxo executado: abrir projeto/editor, criar e reordenar moldura, aplicar
paralaxe, inserir asset, criar clips, seek, play, pause, stop, renderizar luz,
fogo/partículas, texto de cutscene e WAV real, provocar asset ausente, observar
falha acionável sem crash, recuperar a sequência válida, salvar, fechar,
reabrir e comparar documento persistido. O manifesto registra
`audio_failures=["audio_native_missing"]` na captura 08 e o status de
revinculação exibido pela janela nativa.

### Build e runtime portátil

- Build final: pendente para o commit `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`; a build anterior não é
  promovida como evidência deste commit.
- Build anterior preservada: `release/post-e13-native-20260910/`.

O smoke do binário anterior registrou `application.opened`,
`application.state.saved` e `application.closed` com `failure_count=0`; ele é
mantido como evidência histórica e não substitui a nova build.

## Falhas preservadas e limitações abertas

- `artifacts/post-e13-native-flow-20260910-r4/` preserva uma execução que ficou
  pendente após a captura 07; não foi promovida nem apagada.
- STUDIO-03 não possui pendência aberta após R7.
- STUDIO-04 permanece `IN_PROGRESS` até provenance, smoke e hashes da nova
  build `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`.
