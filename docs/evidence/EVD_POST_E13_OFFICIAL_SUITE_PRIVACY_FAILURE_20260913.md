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

## Reexecução r6 preservada

Após a correção de logging do fallback CuPy, a suíte oficial r6 sem filtros
terminou com:

```text
2630 passed, 2 skipped, 2 failed in 80.91s
```

Falharam `test_atlas_replaces_existing_outputs_without_predelete`, por
`PermissionError: WinError 5` em `os.replace`, e novamente o contrato de
higiene por causa do log r4 versionado antes da sanitização final. O raw r6
tem JUnit SHA-256
`B34DFDEB3772AB085BBFCF697DD07351687F036637B4630627ECB22E6F346B04` e log
SHA-256 `3BB5365C36A9D1B0C37D095C8B4773A94611CC39EB766A1CF46A8DFC0FB5CA69`.
As representações sanitizadas preservadas inicialmente tinham JUnit SHA-256
`D4A9964E369317D7EFB858782E4AC61D470213BC9893E8E79B1A41A8DA77BAE3` e log
SHA-256 `32A8FF6C5E52BCED1453914A5C50F629A619533B602D30A2072938538624EFAC`.
Após a auditoria de privacidade que também detectou caminhos temporários
escapados, os mesmos artefatos foram sanitizados novamente, sem alterar o
resultado da suíte: JUnit SHA-256
`0075424AFF3E630EEDC66B7223259F2ABE005B89A6042A1D828CE2B45FAB9135` e log
SHA-256 `6189A2F281483716E04BBC1A37CBEC68BC7C3EAC64F71D29FBDFC1421736DF05`.
As cópias brutas da segunda sanitização foram preservadas fora do repositório
em diretório temporário controlado; os hashes brutos foram mantidos acima.

O log r4 corrigido tem SHA-256
`0EEE691A67DEABE331B591DFC3D4455DB66A278A97266DC25811CCD9EC365F6C`.
O finding `WinError 5` continua aberto até uma qualificação focada e uma
nova suíte completa demonstrarem substituição atômica estável; nenhuma
permissão, threshold ou teste foi relaxado.

## Reexecução r7 preservada

Após o retry controlado do atlas e antes da higienização do metadata r4, a
suíte oficial r7 terminou com:

```text
2632 passed, 2 skipped, 1 failed in 81.58s
```

O único teste que falhou foi novamente
`test_tracked_files_and_nested_archives_have_no_prohibited_references`, agora
por um caminho absoluto no `run-metadata.txt` r4. O JUnit raw r7 tem SHA-256
`97C9307494397FA0F9FCAC8C452AAABD8E381B38BAE06F425BB003F7588EF9A2` e o log
raw tem SHA-256
`6C336E861D9B73C3AA826B14EC5D5900B19E84AFDC55C38A7471517898130EE8`.
As versões sanitizadas preservadas têm JUnit SHA-256
`5678673487968A46664FABD855B2E896A58336E42E17D2893E0632D079B90AC2` e
log SHA-256 `2E10FEA2259BAB35211184370ACD6204A4B295D21510EA5E66ED4C26938B340B`.
O metadata r4 raw tinha SHA-256
`28CC7D7213C37E0AEB011F000C7A9B46F9CCC35A6114CC6E4515650A8259C855` e a
versão sanitizada tem SHA-256
`CB6DD4926B5687A1336471448DB63F8BC12C342A8ACB67ABC83CFC4B848473CB`.

Os artefatos r7 continuam como `FAIL` preservado; o próximo run deve avaliar
somente a árvore já higienizada e o retry atômico commitado.
