# E01-C — aceite técnico do fluxo independente

**Estado:** `TECHNICAL_CHECKPOINT_PASS` — aceite final e revisão humana permanecem pendentes conforme governança.  
**Branch:** `Ailton/e01-independent-scene-20260908`  
**Build observada:** r5, executável SHA-256 `8B17406ECB394B4C3D25D7E37721F8244141B2B985F4B137FD2DB907CCF92188`.

## Matriz do fluxo

| Passo do plano | Evidência | Estado |
|---|---|---|
| Abrir sem projeto | Captura real do executável r5 e `test_independent_scene_action_opens_the_real_child_window` | `PASS_LOCAL` |
| Criar cena em memória | `test_independent_scene_window_new_save_save_as_reopen` | `PASS_LOCAL` |
| Definir resolução/câmera | teste de UI e contrato com resolução/câmera explícitas | `PASS_LOCAL` |
| Salvar e Salvar como | `test_session_new_update_save_save_as_and_reopen` e fluxo de janela | `PASS_LOCAL` |
| Fechar/reabrir/comparar | round-trip canônico e UI de reabertura | `PASS_LOCAL` |
| Cancelar primeiro Save As | `test_independent_scene_save_as_cancel_preserves_unsaved_document` | `PASS_LOCAL` |
| Arquivo truncado/versão/referência inválida | testes de I/O estrito e validação de schema | `PASS_LOCAL` |
| Alteração externa | `test_external_change_is_rejected_without_overwriting_previous_file` | `PASS_LOCAL` |
| Projeto legado preservado | suíte completa + captura real da janela principal sem projeto | `PASS_LOCAL` |

## Verificação consolidada

- Suíte oficial: `1973 passed, 2 skipped, 1 warning`.
- Smoke portátil r5: `SUCCESS`, 11 checks.
- A captura real da janela independente mostra toolbar PT-BR, canvas vazio
  `1920 × 1080`, `top_left, pixel` e controles de resolução/câmera.
- Os dois skips permanecem `SKIP_PRIVILEGE_LIMITATION` e continuam reservados
  à auditoria final de symlinks.

## Limitação explicitamente registrada

O helper Win32 conseguiu abrir e capturar a janela independente, mas uma
tentativa adicional de enviar `Ctrl+Shift+S` depois de localizar a janela
secundária foi recebida pela janela principal e abriu o diálogo legado
`Salvar Projeto`. Essa imagem não é usada como prova do Save As independente.
O Save/Save As/reopen do novo documento está comprovado pelos testes de UI,
sessão e I/O; a captura nativa do diálogo independente permanece evidência
complementar pendente, sem bloquear o checkpoint técnico.
