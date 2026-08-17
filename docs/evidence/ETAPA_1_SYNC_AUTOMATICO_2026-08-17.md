# Etapa 1 — sincronização automática nativa

Status: **APROVADA**.

## Escopo comprovado

- Godot usa `EditorFileSystem.filesystem_changed`, debounce de 350 ms, supressão de eventos gerados pelo próprio importador, configuração `neoeng_d_trace/automatic_sync_enabled` e bloqueio de divergência manual.
- Unity usa `AssetPostprocessor.OnPostprocessAllAssets`, `EditorApplication.delayCall`, resolução de manifestos por imagem e página de atlas, tratamento de overrides e uma única retentativa controlada para hash transitório.
- Exclusão ou alteração de uma entrada não apaga saídas automaticamente.
- Erro de hash permanente permanece rejeitado; a retentativa não transforma drift em sucesso.

## Execuções reais

| Engine | Versão real | Cenários | Resultado |
|---|---|---|---|
| Godot | 4.7.stable | evento de filesystem atualizou saída; divergência manual ficou bloqueada | PASS |
| Unity | 6000.5.7f1 | `AssetPostprocessor` atualizou saída; divergência persistente de `PolygonCollider2D` ficou bloqueada | PASS |
| Unity | 6000.5.7f1 | manifesto schema v2 com página de atlas separada; atualização e conflito | PASS |

Os logs contêm os marcadores `GODOT_AUTO_SYNC_STAGE1=UPDATED`, `GODOT_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED`, `UNITY_AUTO_SYNC_STAGE1=UPDATED`, `UNITY_AUTO_SYNC_STAGE1=CONFLICT_BLOCKED` e `UNITY_NATIVE_AUTO_SYNC=FAILED` para a divergência manual.

## Evidências reproduzíveis

- Godot: `docs/evidence/artifacts/native-auto-sync-stage1-2026-08-17/`.
- Unity básico e rerun após a correção de caminhos: `docs/evidence/artifacts/native-auto-sync-stage1-2026-08-17/` e `docs/evidence/artifacts/native-auto-sync-stage1-rerun-2026-08-17/`.
- Unity com atlas schema v2 e retry: `docs/evidence/artifacts/native-auto-sync-stage1-atlas-rerun-04-2026-08-17/`.
- Cada diretório possui relatório e índice SHA-256. As tentativas FAIL de timing, parse, mutação de fixture e ordem de callbacks foram preservadas com prefixos `attempt-`.
- O rerun final do Unity foi executado com o sanitizador corrigido em `docs/evidence/artifacts/native-auto-sync-stage1-final-rerun-2026-08-17/` e passou novamente os marcadores de atualização e conflito.
- O índice consolidado `docs/evidence/artifacts/native-auto-sync-stage1-final-index-2026-08-17.json` cobre 36 arquivos em 7 diretórios de todas as execuções e foi verificado independentemente após a geração.

## Validação de regressão

Comandos executados:

```text
.\.venv\Scripts\python.exe -m pytest -q tests/test_stage1_automatic_sync_contracts.py tests/test_godot_plugin_scaffold.py tests/test_unity_package_scaffold.py --tb=short
.\.venv\Scripts\python.exe scripts/audit_native_auto_sync_stage1.py --executable godot.exe
.\.venv\Scripts\python.exe scripts/audit_unity_auto_sync_stage1.py --unity Unity.exe
```

As execuções de engine foram realizadas em projetos temporários, com caminhos sanitizados nos artefatos. Nenhuma evidência de falha foi removida ou convertida em PASS.
A auditoria de privacidade foi executada depois da sanitização estruturada dos logs e JSON; os 18 JSON permaneceram válidos e o teste fail-closed de dados de host passou.

## Limitações declaradas

- A sincronização automática não remove recursos órfãos quando um manifesto é excluído; a remoção continua explícita e segura.
- O callback Unity importa cada manifesto afetado individualmente. A transação global de múltiplos manifestos permanece na Etapa 4 do plano e não é considerada concluída nesta etapa.