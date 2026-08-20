# Encerramento pós-merge — Etapa 6 do ADR de runtime

**Estado:** APROVADA NO ESCOPO DEFINIDO; INTEGRADA EM `main`
**Data:** 20 de agosto de 2026
**ADR:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`
**PR:** `#123`
**Merge:** `46604d336af7867e0dd59f9af6e07e5b39a5827f`

## Escopo efetivamente integrado

A Etapa 6 integra o contrato lateral `runtime.triggers` com zonas AABB,
condições, prioridades, eventos `enter`/`stay`/`exit`, fixed update
determinístico, pausa, cancelamento atômico, replay vinculado ao contrato,
limites explícitos, persistência atômica e capacidade anunciada pelo host.

O escopo permanece restrito ao dispatcher determinístico de CPU. Não foram
declarados suporte nativo de Godot ou Unity, streaming, rede, multiplayer,
física, engine gráfica ou runtime completo de engine.

## Evidências remotas

- PR `#123` foi aprovada e mesclada por merge normal, sem force, no commit
  `46604d336af7867e0dd59f9af6e07e5b39a5827f`;
- CI da PR `#123`: run `32422619533`;
- job Linux `96597685770`: PASS;
- job Windows `96597685395`: PASS;
- baseline Git-blob, integridade de evidências, compilação, lint, tipagem,
  segurança, cobertura e auditoria de triggers: PASS;
- nenhuma regra, asserção, threshold ou scanner foi alterado para obter PASS;
- nenhum bypass, force push ou force merge foi usado.

Não foi localizado workflow adicional associado ao SHA do merge; portanto,
nenhum CI pós-merge remoto é declarado. A validação pós-merge local abaixo foi
executada no `main` sincronizado exatamente nesse SHA.

## Validação local pós-merge

Execução real no Windows, com Python 3.11.9 do ambiente Poetry, após
`git pull --ff-only origin main`:

```text
python tools/baseline_integrity.py --verify --git-blob
Baseline verified: 1778 files

python tools/evidence_integrity.py --require-tracked --git-blob
75 manifests verificados

python -m pytest -qq
1520 passed, 2 skipped

python -m pytest -qq --cov=src --cov-branch --cov-fail-under=90 --cov-report=xml
1520 passed, 2 skipped; total coverage 91.09%; branch-rate 85.21%

python tools/check_coverage_policy.py coverage.xml
PASS — linhas >= 90%; branches >= 85%; módulos mensuráveis >= 30%

python scripts/audit_runtime_triggers_phase6.py --output <diretório temporário>
PASS — 13/13 checks; source_tree_clean=true
```

O HEAD local e `origin/main` foram confirmados no merge
`46604d336af7867e0dd59f9af6e07e5b39a5827f`; a árvore estava limpa ao final.
Os dois skips são os testes históricos autorizados de symlink no Windows; não
foram introduzidos nem relaxados pela Etapa 6.

## Artefatos pós-merge

Pacote: `docs/evidence/artifacts/runtime-triggers-phase6-postmerge-2026-08-20/`.

- `stage6-runtime-triggers-report.json` — `2147` bytes — SHA-256 `27d1809afe80e8048b233c96aa1d21511a911400cd43f04aa42fd72bc422db38`;
- `trigger-replay.json` — `948` bytes — SHA-256 `fc79e329eb2ac448755af95e7843dfb7bb45f2d24d0decedc1ea1a8a3eb8e28a`;
- `trigger-sidecar.json` — `2005` bytes — SHA-256 `22e2699d6ebc04d069fbe7a3b0d7c7d1c1100663bfe6e6d3bc7e4e857c24035c`;
- `triggers.json` — `2005` bytes — SHA-256 `22e2699d6ebc04d069fbe7a3b0d7c7d1c1100663bfe6e6d3bc7e4e857c24035c`;
- `artifact-index.json` — `651` bytes — SHA-256 `92a3aad274e89c17495e8a1ffde7b4c6148765fbfea4633c34923ee913ecf04b`.

O relatório registra o commit-fonte real do merge
`46604d336af7867e0dd59f9af6e07e5b39a5827f`, sem dados de identidade ou
caminhos absolutos nos artefatos.

## Decisão

A Etapa 6 está formalmente encerrada e integrada em `main` somente no escopo
acima. A ausência de adaptadores nativos de Godot/Unity e de um runtime gráfico
não é uma falha desta etapa: são capacidades futuras e continuam explicitamente
fora do contrato aprovado. A publicação de release permanece uma decisão
independente e não é aprovada automaticamente por este encerramento.
