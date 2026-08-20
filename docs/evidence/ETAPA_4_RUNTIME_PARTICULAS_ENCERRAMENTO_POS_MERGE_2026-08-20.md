# Evidência — Encerramento pós-merge — RUNTIME-ETAPA-4 — Partículas

## Estado

**APROVADO — RUNTIME-ETAPA-4 ENCERRADA PÓS-MERGE NO ESCOPO APROVADO.**

## Identificação e proveniência

- PR: `#119`.
- Head validado no CI: `490f58cba2dde9e8dcfeccb10c4b4c3afea343a3`.
- Merge normal: `a757da027e531898d1b0e2fb1d18f4f23fd20271`.
- Branch pós-merge auditada: `main`.
- Auditor: `scripts/audit_runtime_particles_phase4.py`.
- Pacote pré-merge: `docs/evidence/artifacts/runtime-particles-phase4-2026-08-20/`.
- Pacote pós-merge: `docs/evidence/artifacts/runtime-particles-phase4-postmerge-2026-08-20/`.

## CI remoto

O run `32405503776` passou integralmente no head da PR:

- Linux job `96543519893`: PASS;
- Windows job `96543520121`: PASS;
- baseline por blobs Git: PASS;
- integridade de evidências rastreadas: PASS;
- lint, formatação, isort, mypy, pip-audit e Bandit: PASS;
- cobertura de linhas e branches e política integrada: PASS;
- auditoria Stage 4B.5 e verificação de árvore: PASS.

A execução anterior `32404980740` permanece registrada no documento pré-merge como falha legítima do baseline após alteração do README. Ela foi corrigida por `490f58c`; nenhuma regra ou limiar foi alterado.

## Validação local pós-merge

No merge `a757da027e531898d1b0e2fb1d18f4f23fd20271`:

- auditor de partículas: PASS, `source_tree_clean=true` e todos os checks verdadeiros;
- baseline `--verify --git-blob`: PASS;
- evidências `--require-tracked --git-blob`: PASS;
- `pytest --cov=src --cov-branch --cov-fail-under=90`: `1483 passed, 2 skipped`;
- cobertura total: `91,08%`;
- política de cobertura: PASS;
- `git rev-parse HEAD` e `origin/main`: mesmo SHA do merge;
- worktree: limpo;
- nenhuma regressão foi reproduzida na suíte integral ou na validação focada.

Os dois skips permanecem preexistentes e correspondem à indisponibilidade de privilégio de symlink no Windows (`WinError 1314`). Eles não foram introduzidos nem usados para produzir PASS; o job Linux executou o conjunto compatível do CI.

## Artefatos pós-merge

- `stage4-runtime-particles-report.json` — `1966` bytes — SHA-256 `6ce1f09f4d66723e65131caaf3dc2053093db14e4c9eacb288af80af80d11be1`;
- `particle-sidecar.json` — `862` bytes — SHA-256 `6b14443676c3ca8bbc612c1c470951f357bfb43b9de00601ad1226fbd4aa7408`;
- `particles.json` — `862` bytes — SHA-256 `6b14443676c3ca8bbc612c1c470951f357bfb43b9de00601ad1226fbd4aa7408`;
- `artifact-index.json` — `514` bytes — SHA-256 `409f81ef8061ce8ef344d5a9f92f3be61094709165024a1ae739577bfb15d7de`.

## Limitações preservadas

Este encerramento não aprova funcionalidades fora da Etapa 4: rasterização GPU, VRAM/FPS/driver, shaders de partículas, pós-processamento, triggers, streaming, Godot/Unity runtime completo e replay persistido em arquivo continuam fora ou não testados.

## Decisão

**APROVADO E INTEGRADO NO ESCOPO DA RUNTIME-ETAPA-4.** A implementação foi submetida, corrigiu uma falha real de baseline sem bypass, passou CI Linux/Windows, foi mergeada normalmente e validada novamente no merge. A release permanece uma decisão independente.
