# Evidência pós-E13 — suíte oficial segura sem warnings

**ID da feature:** `AUD-POST-E13-OFFICIAL-SUITE-SAFE-20260913`
**Status documental:** `PASS`
**Data:** 2026-09-13
**Checkout testado:** `783b385e17506bd898910d4a96fa44db2d7bf1c9`
**Fonte de produto:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`

## Objetivo e segurança

Esta evidência fecha a correção dos cinco `DeprecationWarning` de
`QMouseEvent`, registra a higiene de caminhos e comprova a regressão oficial
completa sem executar symlink ou shutdown nativamente. A suíte foi executada
no Windows host com a variável de autorização controlada ausente; os testes
de symlink terminaram como `SKIP_CONTROLLED_ONLY` antes de qualquer chamada de
filesystem. A prova real desses dois casos está no sandbox Docker r4.

Governança: [GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md).
Mudanças relacionadas: [CHG_POST_E13_CONTROLLED_DANGEROUS_TESTS_20260913.md](CHG_POST_E13_CONTROLLED_DANGEROUS_TESTS_20260913.md) e [CHG_POST_E13_PATH_HYGIENE_20260913.md](CHG_POST_E13_PATH_HYGIENE_20260913.md).

## Execução oficial

Comando completo, sem `-k`, `--ignore`, `--deselect`, `xfail`, supressão de
warnings ou redução de cobertura:

```text
..\..\.venv\Scripts\python.exe -m pytest -q --junitxml=artifacts/audit-post-e13-official-suite-safe-host-20260913-r4/official-junit.xml
```

Ambiente: Python 3.11.9, Windows, `QT_QPA_PLATFORM=offscreen`, guard de
symlink controlado ativo por ausência da variável
`NEOENG_ALLOW_CONTROLLED_SYMLINK_TEST`.

Resultado observado:

```text
2630 passed, 2 skipped in 84.68s (0:01:24)
```

Warnings: `0`. O JUnit confirma exatamente estes skips, ambos com motivo
`symlink creation is controlled-only; run in the approved sandbox`:

- `tests.test_integration_sync::test_plan_rejects_symlink_escape`;
- `tests.test_integration_sync::test_plan_rejects_symlink_destination`.

Os demais 2630 casos passaram, incluindo contratos de UI, persistência,
runtime, exportação, auditoria, limites operacionais e substituição atômica
GLTF.

## Artefatos e hashes

Pacote vigente: `artifacts/audit-post-e13-official-suite-safe-host-20260913-r4/`

| Artefato | SHA-256 |
|---|---|
| `official-pytest.log` | `42DDC5779276493987C3A9010765C26FCB530C8AAEB64A0EF43055AC586534C7` |
| `official-junit.xml` | `B0919A12CDA76364973599B0851178002496C428946B6AA4E5A9BA4F7972BA72` |

O pacote r3 anterior permanece preservado com os hashes
`300CF0299F863EF3518191B089C23524D5FED517DA15803F3A66299B61979C33` e
`7133498F9B043AA46DF88773AD7103ED375131A5D9D50142E5AF0CBA31FABDBB`.

O pacote r1 da regressão segura foi preservado com `FAIL` por 19
incompatibilidades do Linux container (paths Windows/Git, fixtures específicas
do host e PyInstaller ausente). O pacote r2 preserva a falha isolada e
transitória de `os.replace` no GLB; o teste isolado passou e as execuções r3 e
r4 completas passaram. Nenhuma dessas falhas foi apagada ou reclassificada.

## Critério de encerramento desta etapa

Os cinco construtores de `QMouseEvent` não geram mais depreciação; o contrato
de higiene passou; o guard impede symlink nativo; e a suíte oficial completa
passou sem warnings. O skip de segurança e a prova sandbox são estados
distintos e permanecem assim no registro de continuidade.

## Dependências e regra de reexecução

- [EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md](EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md)
- [DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md](DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md)
- [CONTROLE_CONTINUIDADE_ATUAL.md](../CONTROLE_CONTINUIDADE_ATUAL.md)

Reexecutar a suíte oficial após qualquer alteração de código, teste,
dependência ou governança que a afete. Reexecutar symlink isoladamente apenas
se o contrato de integração, guard, runner, Dockerfile, imagem/runtime
controlado ou necessidade formal mudar; nunca para alterações documentais
não relacionadas.
