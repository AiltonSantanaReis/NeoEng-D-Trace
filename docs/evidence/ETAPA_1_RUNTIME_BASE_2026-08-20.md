# Evidência — Etapa 1: runtime base determinístico

## Identificação

- Commit testado: `57b753be57c57e0bbecf798adf11043023568a95`.
- Branch: `feature/runtime-base-phase1`.
- Data/hora do relatório: `2026-08-20T10:20:39+00:00`.
- Responsável: execução automatizada do repositório.

## Ambiente

- Sistema operacional: Windows.
- Python: 3.11.9.
- Dependências: ambiente virtual e lockfiles já versionados no projeto.

## Objetivo e escopo

Validar a implementação integral do host de runtime base: contrato versionado,
carregamento do manifesto estrutural existente, hash canônico, ciclo de vida,
relógio fixed-step determinístico, cancelamento, capacidades/fallback explícito e
ativação transacional com preservação do estado anterior em caso de erro.

Esta etapa não implementa efeitos gráficos nem runtime completo de engine.

## Comandos executados

- Auditor focado e integral:
  `scripts/audit_runtime_base_phase1.py --output <diretório temporário>`.
- Dentro do auditor: pytest focado, pytest completo, Black, Flake8, mypy,
  `py_compile`, `tools/evidence_integrity.py --require-tracked --git-blob` e
  `git diff --check`.

## Resultados

- Focados: `70 passed`.
- Suíte completa: `1421 passed, 2 skipped`.
- Integridade global na auditoria: `62 manifests validated`.
- Gate staged final após inclusão desta evidência: `63 manifests validated`.
- Black, Flake8, mypy, compilação e diff: aprovados.
- Falhas: nenhuma.
- Skips: dois skips históricos mantidos sem alteração.

## Artefatos

- Diretório: `docs/evidence/artifacts/runtime-base-phase1-2026-08-20/`.
- `runtime-base-report.json`: 2661 bytes; SHA-256
  `c7d2f5992fa4465582ea560dd4c8c6c83c711b6c43a75c3c6baba97101e1548b`.
- `artifact-index.json`: 1261 bytes; SHA-256
  `c9763e0561059fb31c0a21d9eff7eea098ed5fbdf594d2541d25e5904f384618`.
- O índice registra tamanho e SHA-256 de todos os logs.

## Falhas e causa raiz

Nenhuma falha permaneceu na execução final. A reconciliação do gate está descrita
em `RECONCILIACAO_GATE_GLOBAL_2026-08-20.md`; snapshots históricos não foram
reescritos.

## Limitações e riscos residuais

Não foram executados nesta etapa iluminação, partículas, shaders,
pós-processamento, triggers, streaming, GPU/VRAM/driver/FPS específicos ou um
runtime completo de engine. Esses itens permanecem fora do escopo desta etapa e
não podem ser declarados resolvidos por estes testes.

## Decisão

**BLOQUEADO** — a validação local é integralmente aprovada, mas a promoção da
etapa depende de CI remoto reproduzível e revisão posterior. Não houve push nem
merge nesta reconciliação.
