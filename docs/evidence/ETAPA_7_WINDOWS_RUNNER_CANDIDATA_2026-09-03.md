# Evidência — Etapa 7 — runner Windows e candidata de empacotamento

**Status da candidata:** `PARCIAL`
**Integração:** `BLOCKED`
**Data:** 2026-09-03
**Commit-fonte testado:** `8e0ada3fcf1d08058240e5263732d14087b5335c`
**Branch:** `fix/legacy-27-functional-regressions`

## Objetivo e escopo

Esta execução fecha a definição operacional do runner/CI para Windows/Qt,
formaliza as 11 assinaturas divergentes e as 12 ausências do runner legado sem
alterar snapshots, e repete os gates de Fase 7 na mesma candidata técnica. O
escopo inclui cobertura, contratos substitutos, segurança, Stage 4B.5,
empacotamento e a capacidade de symlink. Não autoriza merge, tag ou release.

## Ambiente e comandos

- Windows `win32`/Windows-10 build `10.0.26200`, Python `3.11.9`;
- Poetry `2.4.1`, pytest `9.1.1`, pytest-cov `7.1.0`, PyInstaller `6.22.0`;
- `QT_QPA_PLATFORM=offscreen`;
- dependências instaladas por `poetry sync --no-interaction --no-ansi`;
- `poetry check --lock --strict`;
- `poetry run python tools/run_windows_coverage_shards.py --output <runner-temp>`;
- `poetry run python tools/check_coverage_policy.py <runner-temp>/coverage.xml`;
- `poetry run python tools/run_formal_legacy_gate.py --group all --output <legacy-temp>`;
- `poetry run python -m compileall -q -f app.py src tests pack_for_ai.py tools`;
- `poetry run flake8 src tests tools app.py pack_for_ai.py`;
- `poetry run black --check --diff src tests tools app.py pack_for_ai.py`;
- `poetry run isort --check-only --diff src tests tools app.py pack_for_ai.py`;
- `poetry run mypy src`;
- `poetry run bandit -q -r src -lll`;
- `poetry run pip-audit`;
- `poetry run python scripts/audit_stage4b5_quality.py --output <stage4b5-temp>`;
- `poetry run pytest "tests\test_integration_sync.py" -k symlink -q -rs`;
- `.\scripts\build_windows.ps1 -OutputRoot release`.

## Resultado do runner/CI

O runner anterior executava todos os testes Qt no mesmo processo e reproduzia
abort/violação de acesso durante cobertura. A decisão registrada na
[ADR do runner](../ADR_WINDOWS_COVERAGE_SHARD_RUNNER_2026-09-03.md) é isolar
cada arquivo top-level `tests/test_*.py` em subprocesso novo, sem filtros, com
`--cov-append` e threshold inalterado.

O runner versionado passou duas vezes:

| Execução | Arquivos | Testes | Falhas | Erros | Skips | Resultado |
|---|---:|---:|---:|---:|---:|---|
| r1 | 189/189 | 1918 | 0 | 0 | 2 | `ACCEPTED` |
| r2 | 189/189 | 1918 | 0 | 0 | 2 | `ACCEPTED` |

Os dois skips são os testes condicionais de symlink, que não criaram o link
quando o privilégio Windows não estava disponível. A cobertura acumulada passou
com `23.887/25.798` linhas (`92,59%`) e `6.664/7.838` branches (`85,02%`);
`check_coverage_policy.py` também passou.

## Reconciliação formal e preservação dos snapshots

O gate formal passou somente no contrato atual e preservou o resultado bruto:

- runner histórico: `196` testes, `26` falhas, `0` erros, `0` skips, retorno `1`;
- `15` assinaturas históricas exatas;
- `11` assinaturas divergentes formalmente observadas e classificadas;
- `12` falhas históricas ausentes formalmente mantidas;
- `1` observação atual ausente, correspondente ao caso poligonal mantido como
  não regressão;
- `42` contratos substitutos reais, `0` falhas, `0` erros, `0` skips.

Os snapshots permanecem byte-identificados pelo contrato: o manifesto e a
reconciliação não foram editados. Os detalhes individuais e testes substitutos
continuam em `quality/legacy_tests/current_contract.json` e no pacote formal
anterior. O relatório externo do gate e seus hashes estão em
`artifacts/windows-coverage-shards-2026-09-03/formal-legacy-summary.json`.

## Outros gates

- compileall: `PASS`;
- flake8: `PASS`;
- Black: `PASS`;
- isort: `PASS`;
- mypy: `PASS`, 145 arquivos fonte;
- Bandit: `PASS`;
- pip-audit: `PASS`, nenhuma vulnerabilidade conhecida;
- Stage 4B.5: `PASS`, determinismo e benchmarks dentro dos limites;
- empacotamento: `SUCCESS`, 11 smoke checks, 314 arquivos, ZIP de
  `124181818` bytes, SHA-256
  `4db44b144ffa0774893583454716c18344e36d740ce7d6536b6a1cf3ea1d04e6`;
- symlink neste checkout: `BLOCKED_FOR_THIS_HOST`, dois skips por `WinError
  1314`; a prova autorizada VMware anterior permanece `PASS_SCOPED` para os
  hashes ZIP/patch que ela identifica e não é apresentada como prova do SHA
  atual.

## Integridade, falhas e limitações

`evidence_integrity` passou com 124 manifests. A primeira verificação do
baseline desta candidata encontrou uma divergência no hash do ADR recém-ajustado
após sua geração; isso foi identificado antes de qualquer push e exige
regeneração do baseline a partir do staged final. Portanto, o resultado desta
execução não é um pacote final aprovado.

Os logs completos de cada shard, XML de cobertura, JUnit, relatório formal e
auditoria Stage 4B.5 permanecem fora da árvore em diretórios temporários do
host; seus tamanhos e SHA-256 observados estão no índice permanente do pacote.
O CI remoto ainda não foi executado para este SHA.

## Decisão formal

`PARCIAL / BLOCKED`: a causa operacional do abort Qt foi mitigada por runner
isolado e comprovada em duas repetições; a reconciliação formal atual foi aceita
sem falsificar o histórico; e o pacote local passou. A candidata ainda exige a
correção/verificação final do baseline, a revisão da evidência, a confirmação do
CI remoto e, se necessário, a repetição VMware com Developer Mode para eliminar
o `WinError 1314` no SHA candidato. Merge, tag, release e declaração global de
`APROVADO` permanecem proibidos.
