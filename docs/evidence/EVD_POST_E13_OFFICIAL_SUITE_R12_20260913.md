# Evidência — suíte oficial host pós-instrumentação r12

**ID:** `EVD-POST-E13-OFFICIAL-SUITE-R12-20260913`
**Status:** `PASS`
**Data:** 2026-09-13
**Commit auditado:** `e727e9d470b3256b05800cda59d9aa2401a1959f`
**Ambiente:** Python canônico do projeto em Windows, `QT_QPA_PLATFORM=offscreen`

## Execução

A governança ativa foi relida integralmente antes da execução. O comando
percorreu todos os testes descobertos por `pytest.ini`, sem filtros, exclusões,
`xfail`, redução de cobertura ou supressão de warnings. O log bruto foi escrito
em diretório temporário externo ao checkout; somente os artefatos sanitizados
r12 foram publicados.

Resultado observado no ambiente correto do projeto:

```text
2634 passed, 2 skipped, 0 failed, 0 errors, 0 warnings
84,83 s
```

Os únicos skips foram:

- `tests/test_integration_sync.py::test_plan_rejects_symlink_escape`;
- `tests/test_integration_sync.py::test_plan_rejects_symlink_destination`.

Ambos permanecem `controlled-only`; nenhum symlink foi criado no host. Nenhum
Unity, `-quit`, shutdown do sistema ou encerramento de processo foi executado.

## Artefatos sanitizados

Pacote: `artifacts/audit-post-e13-official-suite-safe-host-20260913-r12/`

| Artefato | SHA-256 |
|---|---|
| `official-pytest.log` | `171F156EDDA800951356FB4244459CAE08CE20D18B5E1E3CA870399CE4B1A0A3` |
| `official-junit.xml` | `D75ECAB717E4752250FE85E0EEE9EB3F2336EEB239A23C161D80E304AACA2113` |

O JUnit r12 foi reescrito por parser XML após sanitização de atributos e é
parseável: `tests=2636`, `failures=0`, `errors=0`, `skipped=2`,
`time=84.502`. Não há caminhos locais, hostname do host ou identificadores de
processo expostos nos artefatos publicados.

## Falhas de infraestrutura preservadas

O r10 Linux não é evidência oficial: terminou `2616 passed, 2 skipped, 18
failed` porque a imagem não contém `git`/PyInstaller e não reproduz algumas
semânticas Windows. Seus artefatos permanecem em
`artifacts/audit-post-e13-official-suite-safe-host-20260913-r10/` com hashes
brutos `C618D7131ED296DA7FFC24EC809135F1C0E3A3BBDE666625089F772C51B7A6E2` (log)
e `6C4EDDBC52F1968A8F068E5656C8E02EC4EAE39CD8153A4E20926FD358C69E9D` (JUnit).

O r11 também foi preservado como tentativa de sanitização rejeitada: o log era
válido, mas a substituição textual de `<local-path>` dentro de atributo XML
produziu JUnit inválido. O hash dessa tentativa foi
`176279AFF1C092E4E5D2AF4A3C7EC62652D4CF944157B33B39F6B728BD7F84A3`; ele não foi
publicado como evidência. O r12 corrige somente esse empacotamento, sem mudar
qualquer teste ou resultado.

## Regra de reexecução

Reexecutar a suíte completa quando código/testes/contratos mudarem. Não repetir
symlink fora do sandbox definitivo; manter esses dois skips separados de
`PASS`.
