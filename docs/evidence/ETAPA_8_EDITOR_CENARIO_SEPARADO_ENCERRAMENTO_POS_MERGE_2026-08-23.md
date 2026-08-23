# Etapa 8 — encerramento pós-merge

- PR: #158
- Merge commit: f4a2ae739ac4ed23f78bb82892a0eeaff4c1c15c
- Branch validada após merge: main
- Data: 2026-08-23
- Evidência anterior: docs/evidence/ETAPA_8_EDITOR_CENARIO_SEPARADO_2026-08-23.md

## Decisão

ETAPA 8 — APROVADA FORMALMENTE NO ESCOPO DO PLANO DE INTERFACE.

Esta aprovação encerra a implementação do editor de cenário separado, seus testes e a validação pós-merge. Ela não aprova uma release e não altera os escopos de runtime, Godot/Unity ou etapas posteriores.

## Gates remotos da PR

A execução CI 32658404094 foi concluída com ambos os jobs aprovados no mesmo HEAD:

- Linux job 97240708121: SUCCESS, 2m41s.
- Windows job 97240708024: SUCCESS, 5m59s.
- Baseline reconciliado antes da execução: 2639 arquivos.
- Sem force push, bypass ou alteração de regras/thresholds.

## Validação pós-merge no main

Com o main local sincronizado em f4a2ae7:

- Suíte completa: 1644 passed, 2 skipped, 69.06s.
- Cobertura total: 91.11%.
- Política de cobertura: PASS.
- Baseline: Baseline verified: 2639 files.
- Integridade de evidências: Evidence integrity passed: 112 manifests validated.
- Auditor visual: finding_count=0, status=PASS.
- Testes focados da Etapa 8: 17 passed em 1.95s.
- Diff check: PASS.

A captura pós-merge foi gerada com:

    scripts/audit_stage8_scenario_editor.py --output stage8-postmerge-local-20260823

O manifesto pós-merge registra:

- source.commit: f4a2ae739ac4ed23f78bb82892a0eeaff4c1c15c
- manifest_sha256: adf16d886d10dd15ef98bf294a8ecac03f5c2049bc1becc3587c2307f9a955ab
- finding_count: 0
- status: PASS
- worktree_clean: false

## Integridade e limitações

O estado worktree_clean=false permanece explícito porque existem diretórios locais históricos não rastreados. Eles não foram incluídos em nenhum commit, não foram removidos e não afetam o checkout limpo usado pelo CI.

Os 112 manifests versionados foram validados contra blobs Git. O índice pós-merge lista os hashes e tamanhos exatos das capturas, imagens anotadas, manifest, relatório visual e JUnit.

A revisão visual humana registrada na evidência anterior continua válida para os estados funcionais capturados; a execução pós-merge confirmou novamente a auditoria automática sem achados.

## Resultado

Todos os critérios da Etapa 8 foram confirmados por implementação, testes locais, evidências hashadas, revisão visual, CI Linux/Windows, merge e validação pós-merge.

Próximo trabalho deve começar somente na próxima etapa do plano, após reconciliação documental normal.
