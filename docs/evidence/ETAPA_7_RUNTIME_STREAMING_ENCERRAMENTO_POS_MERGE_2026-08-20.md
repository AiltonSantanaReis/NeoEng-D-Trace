# Etapa 7 do ADR de runtime — encerramento pós-merge

**Estado:** APROVADA NO ESCOPO DEFINIDO
**PR:** #125
**Head validado:** `bccf4e871ad81e1226418f711617b017301cafa6`
**Merge:** `f0d350ad7b61e2e9bc7865515768f3662804c953`
**CI:** run `32430267567` — Linux `success`, Windows `success`
**ADR:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`

## Decisão

A RUNTIME-ETAPA-7 está encerrada somente no escopo do sidecar `runtime.streaming`:
carregamento assíncrono de arquivos reais sob raiz confinada, prioridades
estáveis, limite de pendências, cache LRU, descarte seguro, cancelamento
observável, retry explícito, recuperação de falhas, limites lógicos e
persistência atômica. O contrato não declara streaming GPU, residência de VRAM,
integração nativa Godot/Unity ou runtime completo de engine.

## Evidências reproduzidas no main pós-merge

| Gate | Resultado real |
|---|---|
| Suíte integral | `1535 passed, 2 skipped` |
| Cobertura | `coverage.xml`: linhas `92,92%`, branches `85,23%`; policy checker PASS; 123 fontes mensuráveis observadas |
| Baseline Git-blob | PASS — `1794 files` |
| Integridade de evidências | PASS — `78 manifests validated` |
| Auditoria Etapa 7 | PASS; commit fonte `f0d350ad7b61e2e9bc7865515768f3662804c953`; `source_tree_clean=true`; SHA-256 do relatório temporário `189667951c8126fa3c090fb649a23a9f86b9cad11f1342dba6216af3c5862baf` |
| Qualidade estática oficial | compilação, Flake8, Black (`269` arquivos), isort e mypy (`123` fontes) PASS |
| Segurança | pip-audit sem vulnerabilidades conhecidas; Bandit sem achados de alta severidade |
| Sincronização | `main` local e `origin/main` no merge SHA `f0d350ad7b61e2e9bc7865515768f3662804c953`; worktree limpo |

A auditoria confirmou todos os checks do contrato como verdadeiros. O relatório
foi gerado em diretório temporário e removido após a captura do hash; não é
apresentado como artefato versionado. Os pacotes pré-merge versionados continuam
preservados em `docs/evidence/artifacts/runtime-streaming-phase7-2026-08-20/` e
`docs/evidence/artifacts/runtime-streaming-phase7-post-isort-2026-08-20/`.

## Achado residual não bloqueante

Uma execução manual de Black incluindo o diretório histórico `scripts/` encontrou
13 scripts fora do escopo oficial de formatação do CI. O workflow oficial valida
`src`, `tests`, `tools`, `app.py` e `pack_for_ai.py`; portanto nenhum desses
scripts foi alterado durante o encerramento da Etapa 7. O achado deve ser tratado
em tarefa própria, sem ser reclassificado como falha desta etapa nem ocultado.

## Governança

Nenhum limiar, regra, scanner, asserção histórica ou contrato de auditoria foi
alterado para obter PASS. Não houve bypass, force push, force merge, alteração
fora do escopo, suporte de engine inventado ou evidência não reproduzível.

A release permanece uma decisão independente deste encerramento.