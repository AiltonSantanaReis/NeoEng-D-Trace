# Evidência — requalificação da suíte oficial após reconciliação pós-E13

**ID:** `EVD-POST-E13-SUITE-RECONCILIACAO-20260914`
**Status:** `PASS`
**Data:** 2026-09-14
**Escopo:** contratos, persistência, UI/UX, viewport, exportadores, Unity
source-only, segurança e evidências do checkout ativo.

## Resultado final

A governança ativa foi relida antes da execução. A suíte foi executada sem
filtros, exclusões, `xfail` ou supressão de warnings, usando Python 3.11.9,
pytest 9.1.1 e o projeto instalado em modo editável. O ambiente de validação
foi atualizado somente com a dependência runtime já declarada pelo projeto,
`tzdata==2026.4`.

```text
2641 passed, 2 skipped, 0 failed, 0 errors, 0 warnings
81.78 s
```

Os dois casos `skipped` são deliberados e continuam separados de `PASS`:

- `tests/test_integration_sync.py::test_plan_rejects_symlink_escape`;
- `tests/test_integration_sync.py::test_plan_rejects_symlink_destination`.

Eles são protegidos no host por governança de segurança. A mesma família foi
qualificada definitivamente no Windows Sandbox descartável, com 31/31 casos
passando e nenhum symlink criado no computador principal. O teste de shutdown
também permanece exclusivamente controlado; não houve shutdown nativo.

## Tentativas e falhas preservadas

1. A primeira execução integral encontrou `ZoneInfo("UTC")` sem dados IANA:
   o ambiente auxiliar não possuía `tzdata`, embora `pyproject.toml` já o
   declarasse. A dependência declarada foi instalada nesse ambiente de
   validação; o código do produto não foi alterado.
2. A execução seguinte eliminou a falha de timezone, mas observou uma falha
   intermitente em
   `test_viewport_reuses_asset_validation_until_file_fingerprint_changes`:
   `resolver_calls` ficou `[]` onde o teste esperava `["asset"]`. O teste
   isolado passou cinco vezes e a reexecução integral seguinte passou; não foi
   alterado o teste para mascarar a ocorrência. Se o comportamento reaparecer,
   investigar novamente a granularidade de fingerprint/eventos de arquivo no
   Windows antes de promover uma correção.

Essa sequência é um diagnóstico, não uma autorização para reclassificar falha
como sucesso. O JUnit bruto da tentativa intermediária está preservado no
workspace local em
`artifacts/audit-post-e13-doc-reconciliation-20260914/official-junit.xml`
(SHA-256
`51EB887BAF1214D5DD363076BC606836CC9B5E532FDC620ECB5A0D9E2DE6FA1D`). A
reexecução aprovada está em
`artifacts/audit-post-e13-doc-reconciliation-20260914/official-junit-rerun.xml`
(SHA-256
`644F4AD9F62ED09AE619944387617E5785EE912FC0596FD38C197A61B75A625E`). Esses
JUnit são evidências brutas de execução local, não artefatos de release; não
foram publicados sem sanitização de caminhos.

## Limites da conclusão

Esta evidência fecha a requalificação da suíte do checkout, mas não fecha o
programa pós-E13 inteiro. O licensing/shutdown limpo do Unity continua
`BLOCKED` pelos sinais reais preservados no r16 do Windows Sandbox, e a
importação nativa do asset 3D no Unity continua `PENDING_EVIDENCE`. A avaliação
de CuPy permanece `PASS` no escopo controlado e `NOT_APPLICABLE` como
dependência oficial.

## Regra de reexecução

Reexecutar após mudança de código, testes, dependências, configuração do
empacotamento ou contratos. Reabrir a investigação do fingerprint se a falha
intermitente reaparecer; não repetir os testes de symlink ou shutdown no host.
