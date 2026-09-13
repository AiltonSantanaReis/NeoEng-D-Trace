# Evidência pós-E13 — tentativa Unity em Windows Sandbox controlado

**ID da feature:** `AUD-POST-E13-UNITY-CONTROLLED-SANDBOX-20260913`
**Status:** `BLOCKED`
**Data:** 2026-09-13
**Requisito:** `REQ-POST-E13-UNITY-LICENSING-SHUTDOWN-20260913`
**Decisão habilitadora:** `DECISAO-POST-E13-LIMITE-PERFORMANCE-SOAK-CONTROLADO-20260913`
**Commit auditado:** `b58519693b65b17492d414d63cacb67d28446137`

## Escopo

Esta etapa deveria executar o Unity real dentro de uma instância descartável do
Windows Sandbox, validar a resolução do pacote UPM e observar o ciclo de
licensing e encerramento em modo batch. O host não poderia executar Unity,
encerrar processos ou solicitar shutdown do sistema para este ensaio.

## Governança e entrada

- Governança relida antes de cada preflight, alteração do harness, execução e
  reconciliação: `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- SHA-256 da governança:
  `D933DB005B7110C391CF776CDA3014CE348D61A91A5E9902AEEA619185EC3EA0`.
- Fixture mínima fora do produto: Unity `6000.5.7f1`, pacote
  `com.neoeng.dtrace` com 44 arquivos, entrada e editor somente leitura, saída
  isolada e timeout interno de 240 s.
- Configuração: rede e VGPU desabilitados, clipboard/impressora/áudio/vídeo
  desabilitados, memória limitada a 8192 MB.
- O overlay de runtime x64 foi usado somente para o ensaio e contém DLLs
  Microsoft verificadas; não foi adicionado ao produto ou ao pacote UPM.

## Inventário e execução observada

| Item | Resultado |
|---|---|
| Unity | `6000.5.7f1` |
| SHA-256 Unity.exe | `BD70ECAA1F700D934628F943B36035D0E88F0C9E05A5F30549D1E92F90F6299C` |
| Windows Sandbox | recurso instalado (`InstallState=1`) |
| Versão WindowsSandbox.exe | `10.0.26100.8875` |
| SHA-256 WindowsSandbox.exe | `7BB5667331572C8A725A3A799AE7DED2912648B4F6EB7380FB51864C804C3E36` |
| Manifesto do pacote na fixture | `D267EBDDBDE32F78C146C194FCC083F2A36457EAEB73A6D3593F2CE28CC21F25` |
| Execução real Unity | comprovada no r8: `process_started=true` |

## Histórico da requalificação controlada

As tentativas foram isoladas em diretórios distintos; nenhuma saída anterior
foi sobrescrita.

| Tentativa | Estado | Observação objetiva |
|---|---|---|
| r1 | `BLOCKED` | VM Sandbox preexistente impediu montagem; Unity não observado |
| r2 | `FAIL` | loader `0x8007007E` antes de log |
| r3 | `FAIL` | runtimes VC10 presentes; `OpenRL`/`Unity.dll` em erro 126 |
| r4 | `FAIL` | runtimes VC14 adicionados; erro 126 persistiu |
| r5 | `FAIL` | `tbb` carregou; `embree` ainda em erro 126 |
| r6 | `FAIL` | busca no diretório do Editor corrigiu `embree`/`OpenRL`; `Unity.dll` em erro 126 |
| r7 | `FAIL` | `MSVCP140_CODECVT_IDS.dll` identificado como dependência ausente |
| r8 | `BLOCKED` | Unity carregou e alcançou LicensingClient; licença válida ausente |

## Execução real r8

No r8, a configuração foi aceita sem sessão concorrente. O preflight confirmou
as seis DLLs do overlay presentes; o probe `LoadLibrary` confirmou toda a cadeia
local necessária (`OpenRL`, `embree`, `SketchUpAPI`, bibliotecas de compressão e
`Unity.dll`). O Unity iniciou em `batchmode/nographics` e escreveu `unity.log`.

Resultado do runner:

- `process_started=true`;
- `process_exit_code=198`;
- `package-report.json`: ausente;
- método `NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless`: não alcançado;
- marcador de sucesso/falha do pacote: não observado;
- licensing module e LicensingClient: observados;
- `Code 10` de validação do LicensingClient: observado;
- token de acesso indisponível e `Code 404` de entitlement: observados;
- “No valid Unity Editor license found”: observado;
- assertions `SUCCEEDED(hr)`/`wmiOpened`: preservadas como warnings do ambiente;
- `batchmode quit`, retorno zero, `abort_threads` e `MemoryLeaks`: não observados;
- marcador de pedido `shutdown.exe`: presente, executado apenas na sandbox;
- após polling, todos os processos `WindowsSandbox*` terminaram naturalmente;
- nenhum shutdown ou terminação forçada foi executado no host.

O Unity, portanto, chegou ao ciclo real de licensing, mas saiu pelo caminho de
licença ausente antes de completar o método do pacote e o encerramento limpo.

## Evidências e hashes

O resultado completo, incluindo os hashes da configuração e do runner, está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/sandbox-attempt.json`
(SHA-256 `AE773A27728C59D37C8D3A4033840BC0FD81DCEFAE4DC17BA0B7C31157B08671`).

O resultado r8 está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r8/sandbox-result.json`
(SHA-256 `C22C9E1895EBBEB0CB1B879441EA7B0C10F6DFE344C5379B3917723FA7940C03`).
O marcador de shutdown da sandbox tem SHA-256
`0B278D52B26FFDD0E9C2470BD90F958D93B6C40F6468AF9920FF24B3B23A1D5D`.

O log bruto r8 permanece preservado no diretório controlado local com SHA-256
`DE61E9A5587615A077D1826F8864663AFB292D2CBC08B5B368209078EE3423E4`; a cópia
versionável sanitizada, que mantém todos os sinais funcionais e redige somente
IDs/PIDs/caminhos voláteis, está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r8/unity-sanitized.log`
(SHA-256 `FA80B56C7850C0945F405D7254576F0501927EC439AB5300863BB7028FDC1819`).

## Alternativas seguras verificadas

Foram feitas apenas sondagens read-only de alternativas. O Docker Desktop ativo
é `29.5.3` com daemon `linux` sobre WSL2; não há daemon Windows ativo. Também
não foram encontrados VMs Windows no Hyper-V, VirtualBox ou VMware. Nenhuma
alternativa foi iniciada, e não há base técnica para executar o `Unity.exe`
Windows dentro do Docker Linux.

## Classificação

| Gate | Estado | Evidência |
|---|---|---|
| carregamento/execução real do Unity | `PASS` | r8 iniciou o Unity x64 e alcançou o LicensingClient |
| licensing limpo | `BLOCKED` | falha observada: código 198, token ausente e nenhuma licença válida |
| método/relatório do pacote | `BLOCKED` | execução interrompida pelo licensing antes do método |
| shutdown limpo do Unity/`-quit` | `BLOCKED` | Unity saiu por licença ausente; sinais de encerramento limpo não ocorreram |
| shutdown da sandbox descartável | `PASS` | marcador interno presente e processos terminaram após polling |
| segurança do host | `PASS` | não houve Unity, shutdown ou terminação forçada no host |

O `BLOCKED` atual é ambiental/de credencial e não representa falha funcional do
pacote: o pacote não chegou a ser avaliado porque o Unity não possuía licença.
O `FAIL` de licensing observado é mantido explicitamente. Os diagnósticos
históricos continuam separados e não foram reutilizados como prova de ambiente
limpo.

## Risco e próxima condição de reexecução

Não alterar o pacote para contornar a licença. A próxima reexecução só é válida
quando uma licença/ativação Unity autorizada estiver disponível dentro do
ambiente descartável, ou quando o harness/versão do Unity mudar. Nesse caso,
usar a mesma fixture, registrar novo output e repetir o ciclo completo. Não
repetir symlink nem shutdown do host.

Até essa condição, o gate Unity permanece `BLOCKED` e a meta pós-E13 continua
`IN_PROGRESS`; o carregamento e o shutdown da sandbox estão comprovados, mas
licensing limpo, método do pacote e shutdown limpo do Unity não estão.
