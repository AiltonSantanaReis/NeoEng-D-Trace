# Evidência pós-E13 — suíte oficial final r9

**ID da feature:** `AUD-POST-E13-OFFICIAL-SUITE-R9-20260913`  
**Status documental:** `PASS`  
**Data:** 2026-09-13  
**Commit da árvore final:** `9586692ebfa239ae9a4a91447ed37161d289d185`

## Gate completo

A [governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
foi lida antes da execução. O comando percorreu todos os testes de `tests/`
conforme `pytest.ini`, sem filtros, exclusões, `xfail`, redução de cobertura
ou supressão de warnings:

```text
python -m pytest --tb=short --junitxml=WORKSPACE/artifacts/audit-post-e13-official-suite-safe-host-20260913-r9/official-junit.xml
```

Resultado observado: `2633 passed, 2 skipped, 0 warnings, 0 failures, 0
errors` em `81,84 s`. O JUnit confirma somente:

- `tests.test_integration_sync::test_plan_rejects_symlink_escape`;
- `tests.test_integration_sync::test_plan_rejects_symlink_destination`.

Ambos registram `symlink creation is controlled-only; run in the approved
sandbox`. O guard permaneceu desativado no host (`NEOENG_ALLOW_CONTROLLED_SYMLINK_TEST=0`);
nenhum symlink, shutdown ou encerramento potencialmente danoso foi executado
nativamente.

## Artefatos hashados

Pacote: `artifacts/audit-post-e13-official-suite-safe-host-20260913-r9/`

| Artefato | SHA-256 |
|---|---|
| `official-junit.xml` sanitizado | `ED4586936DF8A41DB2FABC93DD15AA3DAD0F095FDA17E420A82327B417CA06D3` |
| `official-pytest.log` sanitizado | `C9BEE6739BAFBD83A65D8295A98F2532ECEE9968D052DDFF09269CCCC028252D` |
| `run-metadata.txt` | `F7C1CCB78A8DB3D7EDB34B4E5275032CB220A23EF0890FC9DA0E58CB0609DA07` |
| JUnit bruto preservado fora do repositório | `D3CC372A0752F3071668148E4894482EC060448C51F3C564210285B84D5E7627` |
| log bruto preservado fora do repositório | `88159F0EAC2DFB05D7261F5BEA203237337E283CFB7A31241E31B7FBAC80FCD6` |

O JUnit foi parseado com sucesso e a higiene de referências passou após a
sanitização. As representações brutas permanecem preservadas fora do
repositório; a sanitização remove somente prefixos locais.

## Relação com os gates perigosos

Este é o gate host seguro. A prova funcional definitiva de symlink está em
`EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md` (`PASS`, r4,
31/31, 0 skips, 0 falhas/erros) e não deve ser repetida por rotina. Os
diagnósticos Unity continuam controlados, sem nova execução nativa.
