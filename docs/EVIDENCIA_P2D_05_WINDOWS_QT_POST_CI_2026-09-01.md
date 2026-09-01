# Evidência — P2D-05 — fechamento da CI e decisão pré-merge

## Identificação

- Commit validado: `b5b4c3f7a5ff98ba31a01cba8e01976702e00237`.
- Branch: `p2d-05-ui-crash-root-cause`.
- PR: [#165](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/pull/165).
- Execução remota: [33488026805](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33488026805).
- Job Windows: [99792610581](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33488026805/job/99792610581).
- Job Linux: [99792610857](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33488026805/job/99792610857).
- Artefato Windows: [validation-windows-python-3.11 — 9792817394](https://github.com/AiltonSantanaReis/NeoEng-D-Trace/actions/runs/33488026805/artifacts/9792817394).
- Evidência determinística: [EVIDENCIA_P2D_05_WINDOWS_QT_DETERMINISTIC_REPRO_2026-09-01.md](EVIDENCIA_P2D_05_WINDOWS_QT_DETERMINISTIC_REPRO_2026-09-01.md).

## Resultado objetivo da CI

O job Windows terminou com `success` e registrou:

- `1863 collected`;
- `1863 passed`;
- `1 warning`;
- cobertura total de linhas de `90,88%`;
- política integrada de cobertura aprovada;
- reconciliação legada `matched=27/27`, `unexpected=0`, `missing=0`;
- lint, formatação, ordenação de imports, mypy, auditoria de dependências, varredura de riscos e auditoria de qualidade aprovados;
- verificação de que a árvore Windows permaneceu inalterada aprovada.

O job Linux também terminou com `success` e todos os seus gates foram aprovados.

## Dump e stack nativos

O passo de configuração do Windows Error Reporting foi executado como diagnóstico. O passo de coleta foi condicional e terminou como `skipped` porque a suíte não falhou. A inspeção direta do artefato Windows `9792817394` não encontrou arquivos `.dmp` ou `.mdmp`.

Portanto, esta evidência não afirma a existência de dump, stack nativa ou módulo nativo culpado. A confirmação disponível é a prova determinística equivalente no limite Qt-Python, já registrada no documento relacionado.

## Decisão pré-merge

A prova solicitada foi obtida sem alterar asserts, gates, tolerâncias ou regras de execução. Os onze casos anteriormente mascarados foram reativados e a CI atual não contém skips nesses casos.

**CI_PASS — APTO PARA DECISÃO DE MERGE.**

Esta classificação não é o encerramento pós-merge. O merge somente poderá ser executado sobre este SHA, com os checks verdes, e deverá ser seguido da validação pós-merge exigida pela governança.

## Limitações e riscos residuais

- O crash nativo histórico `Windows fatal exception: access violation` não foi reproduzido nesta campanha final; não há dump ou stack nativa para atribuir um módulo específico.
- A prova determinística demonstra a violação de ownership que era observável antes da correção e a proteção de ciclo de vida após a correção; ela não substitui uma stack nativa inexistente nem permite afirmar causalidade além desse limite.
- As 27 falhas históricas da suíte legada continuam explícitas e reconciliadas; elas não foram convertidas em sucesso silencioso.
