# Evidência pós-E13 — symlink definitivo em ambiente controlado

**ID da feature:** `AUD-POST-E13-SYMLINK-SANDBOX-20260913`
**Status documental:** `PASS`
**Modo de execução:** `PASS_SANDBOX`
**Data:** 2026-09-13
**Escopo:** requalificação definitiva dos testes de segurança de integração que
dependem de criação de symlink.
**Fonte de produto:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`
**Checkout montado durante a execução:** `72e60784d90030219a5300a4d6677726f5d0815e`
**Requalificação vigente:** `r3`, após a barreira de segurança controlada dos
testes; o pacote `r2` permanece preservado como evidência anterior.

## Autoridade e decisão de segurança

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Decisão anterior: `docs/evidence/DECISAO_ADIAMENTO_SYMLINKS_E00_2026-09-08.md`.
- Continuidade: `docs/CONTROLE_CONTINUIDADE_ATUAL.json` e `.md`.
- Mudança de segurança: `docs/evidence/CHG_POST_E13_CONTROLLED_DANGEROUS_TESTS_20260913.md`.
- O checkout Windows não criou symlink. O projeto foi montado em
  `read_only:/workspace`; somente a pasta de evidências isolada foi montada
  com escrita em `/output`.
- A execução funcional usou `--network=none` dentro do container.
- A verificação de capacidade criou symlinks somente em `/tmp` do container;
  a checagem no host não encontrou reparse point na pasta de evidências.

## Ambiente reproduzível

| Item | Valor |
|---|---|
| Runtime | Docker Desktop / WSL2 Linux |
| Imagem de dependências | `python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534` |
| Imagem de auditoria | `neoeng-dtrace-symlink-audit:20260913-r3` |
| ID da imagem construída | `sha256:5015b1a1b3a29c75f95523a45e30ed6db5c7536ab6571c6f3a71a16edde79376` |
| Python no container | `3.11.16` |
| Pytest | `9.1.1` |
| Pillow | `12.3.0` |
| Rede durante o teste | desabilitada |

## Execução

O runner montou a fonte atual somente para leitura, copiou apenas
`tests/test_integration_sync.py` para `/tmp` do container para evitar o
`conftest.py` visual que exige PySide6, e executou o arquivo completo:

```text
python -m pytest /tmp/test_integration_sync.py -q -p no:cacheprovider \
  --rootdir=/tmp --confcutdir=/tmp \
  --basetemp=/tmp/pytest-symlink-audit \
  --junitxml=/output/symlink-junit.xml
```

O comando Docker foi executado com `--network=none`,
`/workspace:ro` e `/output:rw` apontando exclusivamente para o pacote desta
evidência. A variável `NEOENG_ALLOW_CONTROLLED_SYMLINK_TEST=1` foi definida
somente dentro do container. Nenhum comando de symlink ou teste de shutdown
foi executado diretamente no host.

## Resultado observado

O probe real de capacidade passou para um link de diretório e um link de
arquivo. O arquivo completo de integração produziu:

```text
31 passed in 0.36s
EXIT_CODE=0
```

Os dois casos críticos foram encontrados no JUnit e executados, sem skip,
failure ou error:

- `test_plan_rejects_symlink_escape` — rejeição de escrita através de link de
  diretório que escaparia do root gerado.
- `test_plan_rejects_symlink_destination` — rejeição de destino de arquivo que
  é symlink.

O relatório controlado confirma `tests=31`, `skipped=0`, `failures=0` e
`errors=0`. O resultado prova a proteção do código atual em ambiente com
suporte real a symlink; não promove o teste local do Windows a `PASS`.

## Artefatos e hashes

Pacote vigente: `artifacts/audit-post-e13-symlink-sandbox-20260913-r3/`

| Artefato | SHA-256 |
|---|---|
| `report.json` | `2702093D2FB5F1223B3F38F231B70F2BE3246658AF9117145B1567B2A0FCF92F` |
| `symlink-junit.xml` | `DF5A1ADC15D9B5A54407B2B9D648A0AD62F3C806523D346629AB607E5362E45F` |
| `pytest-output.txt` | `24CC9AE6108B89BE2869DB8C907FD84084BEDB37F1ACF3A6BB178372218438A3` |
| `runner/symlink_audit.py` | `CCDDFBB62DBAF1788D879997D2C4ECE061B14026BC94C24C02F845AAAB503A7D` |
| `runner/Dockerfile` | `B5B336CADB1E1097E771B8F25DD699C4595A1F85B6778344D991731B307A81C0` |

Hashes da fonte montada:

- `tests/test_integration_sync.py` —
  `A88FED24F5B1D0C35407DFE7843342481B13F363EAFF212B8BDC899B583E062B`;
- `src/exporters/integration_sync.py` —
  `90381E44173A7D034DFFE89DD88841554ED97D5C23D2497BBB8AF972F677276E`.

## Falha histórica preservada

A tentativa `r1` não foi apagada. Ela passou pelo probe de symlink, mas
terminou com `FAIL` e exit `1` porque o `conftest.py` importou PySide6, ausente
na imagem mínima. O JUnit não foi produzido nessa tentativa. A execução `r2`
passou antes da introdução do guard de segurança; depois dessa alteração no
teste, a execução vigente `r3` confirmou novamente os 31 casos. Os pacotes
`r1` e `r2` continuam disponíveis para auditoria histórica.

## Relação com o checkout local

Os dois skips que aparecem na suíte Windows são agora classificados como
`SKIP_CONTROLLED_ONLY`: a barreira encerra o teste antes de qualquer chamada
de `symlink_to`. O resultado é esperado sob a política de segurança adotada e
permanece separado do gate controlado `PASS_SANDBOX`; nenhum skip foi
convertido artificialmente em passagem. A limitação anterior
`SKIP_PRIVILEGE_LIMITATION` e o log oficial correspondente permanecem
preservados nos artefatos históricos.

## Regra de reexecução

Não repetir esta validação para alterações somente documentais, de UI, de
localização ou de desempenho que não toquem o contrato de integração. Reabrir
este gate somente se ocorrer pelo menos uma destas condições:

1. alteração em `tests/test_integration_sync.py` ou
   `src/exporters/integration_sync.py`;
2. alteração no runner, no Dockerfile, nas versões/pins de dependência ou no
   digest da imagem-base;
3. mudança do runtime Docker/WSL que altere a capacidade de symlink;
4. invalidação, perda ou dúvida de integridade dos artefatos hashados; ou
5. necessidade formal de nova comprovação registrada em uma decisão/ADR.

Até uma dessas condições, o resultado `PASS` deste pacote é a evidência
definitiva do gate de symlink para a fonte indicada, enquanto o skip local é
mantido como barreira de segurança do host. A repetição `r3` ocorreu porque o
teste foi alterado para impedir execução nativa; alterações que não toquem o
contrato, a barreira ou a infraestrutura controlada não exigem nova execução.
