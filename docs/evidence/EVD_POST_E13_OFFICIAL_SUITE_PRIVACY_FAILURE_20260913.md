# Evidência preservada — falha de higiene do JUnit oficial r5

**ID:** `EVD-POST-E13-OFFICIAL-JUNIT-PRIVACY-FAILURE-20260913`
**Status documental:** `FAIL`
**Data:** 2026-09-13
**Commit executado:** `3ee4a70a9eb354c6ee39f58778b498eb1f2d1e7c`

## Resultado preservado

A execução oficial sem filtros do pacote
`artifacts/audit-post-e13-official-suite-safe-host-20260913-r5/` terminou com:

```text
2631 passed, 2 skipped, 1 failed in 86.08s
```

O teste que falhou foi
`tests/test_repository_reference_hygiene.py::test_tracked_files_and_nested_archives_have_no_prohibited_references`.
O restante da suíte não apresentou falha funcional. O JUnit r5 bruto tem
SHA-256 `EADAA75064D43F81B694697FE2DB02001393C4DD41B00018E808F5B7E721B1F5`
e o log bruto tem SHA-256
`8D3DD55FBC5BD11428EEDF1892F5E8E0B52845057A2422148EC773CABD6E2F2A`.

## Causa técnica

Os dois motivos de skip controlado gerados pelo pytest carregam o prefixo
absoluto do checkout local no XML. Como o JUnit r4 já estava versionado, a
varredura de privacidade detectou três ocorrências de caminho local no arquivo
r4. Isso é uma falha de higiene da evidência, não uma falha dos testes de
symlink nem do produto.

## Correção aplicada

O JUnit versionado foi normalizado mecanicamente para trocar somente o prefixo
local por `WORKSPACE`, preservando testes, contagens, motivos e resultados. O
raw foi preservado fora do conjunto versionado para auditoria temporal. O r4
normalizado tem SHA-256
`BF0176EB03CD54A68F89FD1DBC9105EB477D76C2815D68F4CE1977C118276E18`.
O log r5 normalizado, com whitespace final removido, tem SHA-256
`C1B73C8A310B2A421495D8EBE72F6994F754418D188562C500C3ECB2ABD9AEE3` e o
JUnit r5 normalizado tem SHA-256
`9AADA23BFDA6BFA9E0D54EB65953435A9848011709C546170F1ABD8E24AFF29E`.

O r5 permanece preservado como execução que falhou e não será promovido a
PASS. Uma nova suíte completa, com o artefato versionado higienizado, é
obrigatória para fechar este finding.
