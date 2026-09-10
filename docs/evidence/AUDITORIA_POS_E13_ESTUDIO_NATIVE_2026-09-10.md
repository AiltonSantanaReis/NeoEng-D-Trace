# Auditoria pós-E13 — estúdio nativo de cenário/parallax

**Status global:** `PASS` para o lote pós-E13 do estúdio
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
| STUDIO-04 | `PASS` | suíte integral, R7, build limpa, smoke oficial e smoke direto do binário |

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

- Provenance: `release/post-e13-native-20260910-final/continuity-provenance.json` (`status=PASS`).
- Smoke oficial: `release/post-e13-native-20260910-final/smoke/portable-smoke-report.json` (`status=SUCCESS`, 11 checks).
- GUI smoke direto: `artifacts/post-e13-native-flow-20260910-r7/binary-smoke-final.jsonl` (`GUI_EXIT=0`, `failure_count=0`).
- SHA-256 do GUI: `641018A96AB60A6BFA467DE9D86217D50361A65F9AE7183B99426A8B2CB7B86D`.
- SHA-256 do ZIP: `894D00CCE84DBF3ED865AD6A23FC581361907F1212F7B40F886C1B0621A8B834`.
- Provenance vinculado ao commit de evidência `74373d6e37beeccfdf75492bf7df5b5c0895b72b`; o código funcional auditado está no commit `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`.

O smoke direto do binário final registrou `application.opened`,
`application.state.saved` e `application.closed` com `failure_count=0`. O fluxo
detalhado de autoria foi capturado no processo fonte nativo; o smoke do
binário comprova abertura, persistência de estado e encerramento, sem declarar
que o editor completo do binário foi operado quando essa evidência específica
não foi produzida.

## Falhas preservadas e limitações abertas

- `artifacts/post-e13-native-flow-20260910-r4/` preserva uma execução que ficou
  pendente após a captura 07; não foi promovida nem apagada.
- STUDIO-03 não possui pendência aberta após R7.
- O build registra warning de dependência opcional: `tzdata` não encontrado
  no grafo PyInstaller; o smoke e o binário passaram.
- O smoke direto registra warning operacional explícito: CuPy ausente, com
  fallback para CPU; não houve falha de sessão.
- A suíte mantém uma advertência de depreciação do construtor Qt
  `QMouseEvent`; ela não foi ocultada.
