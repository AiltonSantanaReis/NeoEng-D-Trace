# Reconciliação do gate global de evidências — 2026-08-20

## Identificação

- Commit da correção do gate: `28f7f14` (`fix: reconcile git blob evidence validation`).
- Commit do auditor da Fase 1: `57b753b` (`test: include global evidence gate in runtime audit`).
- Branch auditado: `feature/runtime-base-phase1`.
- Estado desta reconciliação: local aprovado; CI remoto e merge ainda pendentes.

## Objetivo

Reconciliar a validação global de evidências com os bytes efetivamente versionados,
preservando snapshots históricos e mantendo o contrato fail-closed. A reconciliação
não altera regras de qualidade, não reduz asserções, não cria skips e não reescreve
manifests históricos para o estado atual.

## Causa raiz confirmada

Foram observadas diferenças quando manifests históricos eram comparados diretamente
com `HEAD`. Esses manifests declaram `source_commit` histórico e, portanto, devem
ser validados contra aquele commit. A causa real era que o caminho de reescrita do
validador não propagava esse `source_commit`; adicionalmente, a implementação
serializada iniciava processos Git repetidos para cada referência.

## Correção aplicada

- `tools/evidence_integrity.py` agora respeita `source_commit` também na reescrita.
- A leitura em modo `--git-blob` usa um leitor batch de blobs e estado Git agrupado,
  mantendo a comparação com o índice/commit declarado sem alterar o contrato CLI.
- O auditor da Fase 1 executa explicitamente:
  `tools/evidence_integrity.py --require-tracked --git-blob`.
- A validação continua exigindo arquivos rastreados, bytes exatos, tamanho e
  SHA-256; não há bypass, `--skip`, relaxamento ou alteração de regra.

## Verificações reais

- Gate global na auditoria: `Evidence integrity passed: 62 manifests validated.`
- Gate staged final após inclusão do pacote: `Evidence integrity passed: 63 manifests validated.`
- Testes do gate e higiene: `12 passed`.
- Auditoria focada da Fase 1: `70 passed`.
- Suíte completa: `1421 passed, 2 skipped`.
- O resultado da auditoria inclui `evidence_integrity`, `git_diff_check`, Black,
  Flake8, mypy e `py_compile`, todos aprovados.
- Os dois skips são os skips históricos já existentes da suíte; não foram criados
  nem modificados nesta reconciliação.

## Evidência preservada

O pacote reproduzível da auditoria está em
`docs/evidence/artifacts/runtime-base-phase1-2026-08-20/`.

- `runtime-base-report.json`: 2661 bytes,
  SHA-256 `c7d2f5992fa4465582ea560dd4c8c6c83c711b6c43a75c3c6baba97101e1548b`.
- `artifact-index.json`: 1261 bytes,
  SHA-256 `c9763e0561059fb31c0a21d9eff7eea098ed5fbdf594d2541d25e5904f384618`.
- O índice contém tamanho e SHA-256 de cada log; nenhum caminho absoluto do
  ambiente foi incluído.

## Limites e decisão

Esta reconciliação prova o gate global local e a Fase 1 do runtime base. Ela não
prova CI remoto, merge, efeitos gráficos, partículas, shaders, iluminação,
pós-processamento, triggers, streaming ou runtime completo de engine.

**Decisão atual: BLOQUEADO para promoção/merge até o CI remoto reproduzir os gates.**
