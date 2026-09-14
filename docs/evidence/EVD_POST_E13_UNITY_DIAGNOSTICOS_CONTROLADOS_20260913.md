# Evidência — Diagnósticos Unity controlados pós-E13

**ID:** `EVD-POST-E13-UNITY-DIAGNOSTICS-CONTROLLED-20260913`
**Status do classificador:** `PASS`
**Status do ambiente Unity limpo:** `PENDING_EVIDENCE`
**Status do shutdown/soak limpo:** `PENDING_EVIDENCE`
**Execução nativa nesta etapa:** `NOT_APPLICABLE` por decisão de segurança
**Classificação:** `CONTROLLED_LOG_CLASSIFICATION_ONLY`
**Data:** 2026-09-13
**Checkout auditado:** `72e60784d90030219a5300a4d6677726f5d0815e`
**Fonte de produto:** `7f5c0477b3f4594928751aec6b97a4b1e9c0178b`

## Dependências e limite

- Governança: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- Índice ativo: `docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`.
- Requalificação externa histórica: `docs/evidence/EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md`.
- Decisão de segurança: `docs/evidence/DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md`.
- Classificador: `tools/qualify_post_e13_unity_diagnostics.py`.
- Resultado controlado corrente: `artifacts/post-e13-unity-diagnostics-controlled-20260913-r2/report.json`; o r1 permanece preservado.

O objetivo desta etapa é fechar a lacuna de observabilidade sem executar Unity,
`-quit`, encerramento de processo, shutdown do sistema, alteração de licensing,
rede ou qualquer ação potencialmente danosa no host. O harness lê somente os logs
já preservados da requalificação anterior e também é coberto por testes com
fixtures sintéticas. Ele não é um mock publicado como prova de runtime: é um
classificador de evidência, e mantém estados não comprovados como `PENDING_EVIDENCE`.

## Execução controlada

O classificador foi executado dentro do Docker Desktop com:

- imagem `python:3.11-slim@sha256:9534e5a8e315485d4061ed659af0fd78a284c015f9b73661b41d6bab25604534`;
- rede desativada (`--network none`);
- filesystem do checkout somente leitura;
- somente o diretório de saída montado como gravável;
- sem processo Unity iniciado e sem pedido de encerramento.

Comando lógico executado:

```text
python tools/qualify_post_e13_unity_diagnostics.py \
  --positive artifacts/post-e13-unity-diagnostics-20260913-r2/unity-positive.log \
  --negative artifacts/post-e13-unity-diagnostics-20260913-r2/unity-negative.log \
  --output artifacts/post-e13-unity-diagnostics-controlled-20260913-r1/report.json
```

O teste focado `tests/test_post_e13_unity_diagnostics.py` passou com `3 passed`.
O artefato controlado passou com `status=PASS`, e registrou explicitamente
`native_unity_reexecuted=false` e
`native_shutdown_or_process_termination_requested=false`.

## Evidência nativa histórica analisada

As entradas foram lidas dos logs reais da execução anterior do Unity 6000.5.7f1;
elas permanecem preservadas e não foram reescritas:

| Entrada | SHA-256 | Resultado funcional |
|---|---|---|
| `r2/unity-positive.log` | `007008BA03F2853F04D34DB56615D32DB6938589CD0F069B8E89EA39D20732E7` | marcador `TILEMAP_RUNTIME_UNITY=SUCCESS`, `ExitCode: 0` |
| `r2/unity-negative.log` | `81609EE56ABBD740EE232557716756D7B245270595E7972FC41A67F51D541EC6` | marcador `TILEMAP_RUNTIME_UNITY_DRIFT=REJECTED`, `ExitCode: 0` |
| `r2/tilemap-runtime-engine-audit.json` | `479736FE12C9051212022E3DB9840C3B1757DAB2EE390A5033533B61536AAD8C` | positivo/negativo agregados como `PASS` |

O classificador encontrou, em cada log positivo e negativo:

| Sinal | Contagem por log | Estado correto |
|---|---:|---|
| `Code 10 while verifying Licensing Client signature` | `1` | `PENDING_EVIDENCE` para causa/ambiente limpo |
| `LicensingClient has failed validation` | `1` | `PENDING_EVIDENCE` para causa/mitigação |
| `Access token is unavailable` | `1` | `PENDING_EVIDENCE`; entitlement posterior preservado |
| entitlement `Unity Personal` resolvido | `1` | `PASS` como observação do ambiente histórico |
| `Curl error 42: Callback aborted` | `1` | `PENDING_EVIDENCE` de rede/telemetria |
| timeout/CDN relacionado | `3` | `PENDING_EVIDENCE` de rede |
| `abort_threads: Failed aborting id` | `4` | `PENDING_EVIDENCE` de shutdown limpo |
| evento `MemoryLeaks` | `1` | observação; não é veredicto de leak/soak |
| `Found no leaked weakptrs` | `1` | evidência limitada, sem promoção do evento anterior |

No log positivo também foi preservado `ExitCode: 4` de subprocesso interno do
Bee, separado do `ExitCode: 0` do fluxo Unity. O classificador não confunde esse
código com falha do processo principal.

## Resultado e decisão de segurança

O fluxo funcional Unity continua comprovado no vertical slice histórico: positivo
aceito, negativo rejeitado por drift e ambos com código do processo principal
`0`. A camada de diagnóstico agora está qualificada para identificar e contar os
sinais sem ocultá-los.

O que **não** foi comprovado e permanece aberto:

- que a instalação/licensing do Unity esteja limpa em um ambiente novo;
- que `Code 10`, token, Curl e timeout sejam inofensivos em todos os hosts;
- que todo encerramento Unity seja limpo em soak prolongado;
- que o evento `MemoryLeaks` represente ou não vazamento persistente;
- que o host suporte nova execução nativa sem risco ou sem intervenção humana.

Esses itens ficam `PENDING_EVIDENCE`, e não serão “resolvidos” por reclassificação
do log. A execução nativa não será repetida nesta máquina. Qualquer requalificação
futura deverá ocorrer em ambiente controlado dedicado, com autorização e pacote
de evidências próprio, sem transformar uma simulação em equivalência nativa.

## Regra de reexecução

Não repetir a classificação por rotina. Reexecutar somente se mudar o classificador,
os padrões de diagnóstico, o contrato de licensing/shutdown, os logs de origem ou
o formato do relatório. Alterações apenas de UI, localização, assets,
documentação ou desempenho do editor não exigem repetir esta etapa. Um eventual
teste de shutdown real continua proibido no host e deve usar sandbox/VM dedicada.

## Hashes do pacote controlado

- `r2/report.json`: `EACEB7B39137563573366AD854AB9FC3C3D481BC286C1AE1D9F77268444735C1`.
- `r1/report.json` permanece preservado com o mesmo resultado hashado.
- `qualify_post_e13_unity_diagnostics.py`:
  `4AA80C48D42719C5CD5B14D28F627F824AE5F2FB3668C1C08DA421C499C6FDFE`.
