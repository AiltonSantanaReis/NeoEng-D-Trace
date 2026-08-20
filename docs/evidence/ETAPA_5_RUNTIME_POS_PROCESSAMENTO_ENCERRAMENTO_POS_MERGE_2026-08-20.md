# Encerramento pós-merge — Etapa 5 do ADR de runtime

**Estado:** APROVADA NO ESCOPO DEFINIDO; INTEGRADA EM `main`
**Data:** 20 de agosto de 2026
**ADR:** `docs/ADR_RUNTIME_CENARIOS_EFEITOS_2026-08-20.md`
**PR:** `#121`
**Merge:** `159b1241b01264aec7c80424fc5da8985fbede4b`
**CI:** run `32415391528`

## Escopo efetivamente integrado

A Etapa 5 integra o contrato `runtime.post_processing` com preview CPU
determinístico, cadeia ordenada de `exposure`, `grayscale`, `tint`,
`vignette` e `box_blur`, limites explícitos, preservação de alfa, fallback
explícito, persistência atômica e auditoria fail-closed.

O contrato não declara suporte nativo de Godot/Unity, GPU, VRAM, driver, FPS,
triggers, streaming ou runtime completo de engine. Esses recursos permanecem
fora do escopo concluído desta etapa.

## Evidências remotas

- Job Linux `96575255353`: PASS em `1m56s`;
- Job Windows `96575255123`: PASS em `4m57s`;
- baseline Git-blob: `1764 files`, PASS;
- checks de evidência, dependências, lint, formato, imports, tipagem, segurança,
  cobertura e auditoria do CI: PASS;
- nenhum bypass, force push, alteração de regra ou supressão de falha foi usado.

## Validação local pós-merge

Comandos executados no `main` sincronizado com o merge:

```text
python -m pytest -q
1492 passed, 2 skipped

python tools/baseline_integrity.py --verify --git-blob
Baseline verified: 1764 files

python scripts/audit_runtime_post_processing_phase5.py --output <diretório temporário>
10/10 checks PASS; source_tree_clean=true
```

Os dois skips são os testes históricos de symlink que dependem de privilégio do
Windows; não foram introduzidos nem relaxados pela Etapa 5.

## Artefatos pós-merge

Pacote: `docs/evidence/artifacts/runtime-post-processing-phase5-postmerge-2026-08-20/`.

- `stage5-runtime-post-processing-report.json` — `1860` bytes — SHA-256 `aebfccbf0a351490be4cccca12bee9ce5e0528ae6c4b62aa478a173f59fcb281`;
- `post-processing-sidecar.json` — `1031` bytes — SHA-256 `52e93174d4d8450239b470f5142685376786785a811a47121634eea7227f97a6`;
- `post-processing.json` — `1031` bytes — SHA-256 `52e93174d4d8450239b470f5142685376786785a811a47121634eea7227f97a6`;
- `artifact-index.json` — `541` bytes — SHA-256 `7619a2d6cbc669630969f9bfdb5ba936c2a72b45aa706eaffda54d1caff828b3`.

## Decisão

A Etapa 5 está formalmente encerrada e integrada em `main` somente no escopo
acima. A publicação de release continua sendo uma decisão independente e não é
aprovada automaticamente por este encerramento.