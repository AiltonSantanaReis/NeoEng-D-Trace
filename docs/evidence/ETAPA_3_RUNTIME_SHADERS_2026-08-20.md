# Evidência — Etapa 3 — Runtime de shaders

## Identificação

- Estado: validação local pré-checkpoint; não é encerramento da etapa.
- Baseline de implementação: `ff66fa7`.
- Branch de trabalho: `Ailton/runtime-phase3-shaders`.
- Data: 20 de agosto de 2026.
- Auditor planejado: `scripts/audit_runtime_shaders_phase3.py`.

## Objetivo e escopo

Implementar o contrato versionado de shaders/materials do runtime, com vínculo
explícito ao sidecar de iluminação, validação canônica, compilação real pelo
Qt Shader Tools (`qsb`), rejeição fail-closed de parâmetros inválidos e
publicação atômica dos binários. A etapa não implementa partículas,
pós-processamento, triggers, streaming ou adaptadores completos de engine.

## Validação local já executada

Comandos canônicos executados no ambiente Windows/Python 3.11 do projeto:

- `pytest --cov=src --cov-branch --cov-fail-under=90 --cov-report=term-missing --cov-report=xml` — **1456 passed, 2 skipped**; linhas `91,02%`.
- `python tools/check_coverage_policy.py coverage.xml` — **PASS**; linhas >= 90%, branches >= 85% e módulos mensuráveis >= 30%.
- `black --check`, `isort --check-only`, `flake8`, `mypy src` e `compileall` — **PASS**.
- testes focados de shaders, documentação e evidências — **60 passed**.
- compilação real de vertex/fragment pelo `qsb.exe` do PySide6 — **PASS**.
- shader inválido — rejeitado pelo backend e binários anteriores preservados — **PASS**.

## Resultado honesto do auditor nesta árvore

A execução temporária do auditor comprovou os comportamentos reais abaixo:

- sidecar canônico e round-trip — PASS;
- backend `qt-qsb` real resolvido — PASS;
- dois estágios compilados — PASS;
- rejeição de shader inválido sem substituição — PASS;
- privacidade do relatório — PASS;
- `source_tree_clean` — **FAIL esperado**, pois a implementação e esta
  evidência ainda estão modificadas e não foram commitadas.

Esse resultado não foi promovido a PASS nem usado como evidência final.

## Artefatos e hashes

O pacote hashado final será gerado somente após o checkpoint da implementação
em árvore limpa. Até esse momento não há hash de artefato final versionado e
não se declara auditoria concluída.

## Limitações e riscos residuais

- O backend real comprovado nesta etapa é Qt Shader Tools (`qsb`); outros
  backends são rejeitados explicitamente, sem fallback silencioso.
- A validação GPU/hardware e a reprodução em Godot/Unity pertencem às fases
  posteriores previstas no ADR.
- CI remoto, PR, merge e validação pós-merge ainda não foram executados.

## Decisão

**NÃO APROVADO — implementação local validada; checkpoint, auditoria em árvore
limpa, evidência hashada, CI, PR, merge e pós-merge ainda pendentes.**
