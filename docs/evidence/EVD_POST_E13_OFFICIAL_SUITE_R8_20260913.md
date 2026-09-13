# Evidência pós-E13 — suíte oficial r8 sem falhas

**ID da feature:** `AUD-POST-E13-OFFICIAL-SUITE-R8-20260913`  
**Status documental:** `PASS`  
**Data:** 2026-09-13  
**Commit auditado:** `74e8ad9`  
**Checkout:** `WORKSPACE`

## Escopo e governança

Esta execução é o gate oficial de regressão após a sanitização dos artefatos
históricos r6. A [governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
foi lida antes da execução. O comando percorreu todos os testes descobertos
por `pytest.ini`, sem `-k`, `--ignore`, `--deselect`, `xfail`, redução de
cobertura ou supressão de warnings.

Os testes potencialmente danosos não foram executados nativamente. O guard
`NEOENG_ALLOW_CONTROLLED_SYMLINK_TEST=0` manteve os dois casos de symlink como
`SKIP_CONTROLLED_ONLY`; a execução definitiva desses casos está comprovada
separadamente pelo sandbox r4.

## Execução real

```text
python -m pytest --tb=short --junitxml=WORKSPACE/artifacts/audit-post-e13-official-suite-safe-host-20260913-r8/official-junit.xml
```

Resultado observado:

```text
2633 passed, 2 skipped, 0 warnings, 0 failures, 0 errors in 81.64s
```

Os skips confirmados no JUnit são:

- `tests.test_integration_sync::test_plan_rejects_symlink_escape`;
- `tests.test_integration_sync::test_plan_rejects_symlink_destination`.

Ambos registram explicitamente `symlink creation is controlled-only; run in
the approved sandbox`. Não houve skip adicional, warning ou falha ocultada.

## Evidências e hashes

Pacote: `artifacts/audit-post-e13-official-suite-safe-host-20260913-r8/`

| Artefato | SHA-256 |
|---|---|
| `official-junit.xml` sanitizado | `B4ADB31031532294659AD1BB88E68EFE9F5B56788BA81C98D72852789A4DD874` |
| `official-pytest.log` sanitizado | `4488F0EFA77707192A6CC93BC513D26F524FC650C6CF6436DA57EE44EF2C0BA4` |
| JUnit bruto preservado fora do repositório | `CECCC450397B711F2E1F9A9B618294BD990F49793A34C68D358D0202A26B454F` |
| log bruto preservado fora do repositório | `7AFBCA6F2ECD3ACE3E2FDDAFAC27FFCA4F175D6330BB13E0F7C1F561E3759EF7` |

O JUnit sanitizado foi parseado com sucesso. A higiene de referências do
repositório passou (`2 passed`), sem caminhos absolutos de usuário; a
sanitização removeu somente os prefixos locais dos artefatos, não os casos,
mensagens, contagens ou resultados.

## Critério de aceitação e limites

O gate oficial r8 está `PASS`. A prova host segura e a prova sandbox de
symlink são evidências complementares, não intercambiáveis. O teste de
symlink só deve ser repetido se houver alteração no teste de integração,
guard, runner/Dockerfile, dependências/digest/runtime, integridade dos
artefatos ou decisão formal. Shutdown nativo continua fora deste host e não
foi inferido como aprovado por esta suíte.

