# Etapa 6 — baseline do gizmo: encerramento pós-merge

**Estado:** BASELINE VALIDADO; IMPLEMENTAÇÃO DA ETAPA 6 NÃO INICIADA
**Data:** 2026-08-22
**Release:** não aprovada por este documento

## Proveniência

- PR: `#142`.
- Merge normal confirmado no `main`: `c42542ee428bd81c79257d10e62546694442b9a0`.
- Branch de origem do baseline: `Ailton/stage6-gizmo-baseline`.
- Branch deste registro: `Ailton/stage6-baseline-postmerge`.
- O baseline técnico foi produzido antes do merge contra o commit-base `425f21df2bbf9a67c01a577b59ae6bbba25995b7`; este documento registra a revalidação do conteúdo efetivamente integrado.

## Validação real pós-merge

Executada no Windows/Python 3.11.9/PySide6 6.10.1/Qt 6.10.1:

```text
.venv/Scripts/python.exe tools/baseline_integrity.py --verify --git-blob
Baseline verified: 2238 files

.venv/Scripts/python.exe tools/evidence_integrity.py --require-tracked --git-blob
Evidence integrity passed: 99 manifests validated.

.venv/Scripts/python.exe -m pytest -q --tb=short
1600 passed, 2 skipped in 50.48s
```

Os dois skips foram preservados como parte da suíte existente; nenhum teste foi removido, relaxado ou convertido para obter resultado favorável.

## Estado do gizmo após a revalidação

O merge contém apenas a reconciliação do plano e o baseline documental. Nenhum arquivo de implementação do gizmo foi alterado neste ciclo. A análise anterior continua válida: há um gizmo principal e um `SceneTransformGizmo` separado; as lacunas de acessibilidade, edição por vértice, snapping de transformação, profundidade Z, feedback numérico editável, limites de hit-test e capturas dedicadas de DPI/redimensionamento/multiseleção/undo-redo ainda não foram comprovadas.

As capturas históricas das etapas anteriores não são reutilizadas como prova da Etapa 6.

## Estado da árvore

Não há alterações rastreadas ou staged após a validação. Os diretórios locais históricos não rastreados foram preservados e não foram incluídos no ciclo.

## Decisão

O baseline da Etapa 6 está validado pós-merge. A implementação do **Gizmo profissional permanece planejada e não iniciada**. O próximo passo correto é criar uma branch própria de implementação, caracterizar os contratos atuais com testes adicionais e somente então alterar o código, mantendo o ciclo de evidência, CI e pós-merge.
