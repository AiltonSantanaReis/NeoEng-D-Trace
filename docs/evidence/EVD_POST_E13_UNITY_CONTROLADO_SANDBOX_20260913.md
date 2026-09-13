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
| Execução real Unity | comprovada no r10: `process_started=true`; candidato atualizado transportado, zero entitlements aplicáveis |

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
| r9 | `BLOCKED` | candidato autorizado foi copiado com hash correspondente; Unity encontrou zero entitlements aplicáveis e saiu com código 198 |
| r10 | `BLOCKED` | candidato local atualizado foi copiado com hash correspondente; Unity novamente encontrou zero entitlements aplicáveis e saiu com código 198 |

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

## Execução real r9 com licença autorizada

No r9, a pasta de licença do host foi mapeada em modo read-only para a sandbox.
O runner validou o SHA-256 esperado, copiou o arquivo para o caminho local do
usuário descartável e confirmou o mesmo hash no destino. O Unity iniciou em
`batchmode/nographics`, conectou-se ao LicensingClient e chegou ao handshake,
mas o LicensingClient reportou `0` grupos de entitlement e `0` free
entitlements correspondentes.

Resultado objetivo do r9:

- `process_started=true`, `timed_out=false` e `process_exit_code=198`;
- origem e destino da licença: `89525CC063037191D198C1D3FF19FF566AB32BD6E3D3D917274EFCC8665B8926`;
- `package-report.json` ausente; método `RunHeadless` não alcançado;
- `Code 10`, token indisponível, `Code 404` e “No valid Unity Editor license found”: observados;
- sinais de `-quit` limpo, retorno zero, `abort_threads` e `MemoryLeaks`: não observados;
- dois processos Unity/licensing ainda estavam presentes no instante anterior ao shutdown da sandbox;
- marcador de shutdown presente e todos os processos `WindowsSandbox*` terminaram naturalmente;
- nenhum processo foi encerrado nem o host foi desligado.

O r9 elimina a dúvida sobre o transporte do arquivo: a licença chegou ao local
esperado dentro do ambiente controlado. Ele não elimina a falha de entitlement;
o candidato autorizado não é uma licença válida/aplicável para essa execução.

## Execução real r10 com candidato atualizado

Após o r9, o arquivo no mesmo caminho autorizado apresentou nova data de
modificação e novo SHA-256, mantendo `6731` bytes. O r10 foi preparado como um
harness separado, com runner e WSB próprios, para não reusar silenciosamente o
artefato r9. A origem foi mapeada read-only, copiada dentro da sandbox descartável
e o hash do destino conferiu com a origem.

Resultado objetivo do r10:

- `process_started=true`, `timed_out=false` e `process_exit_code=198`;
- origem e destino da licença:
  `C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498`;
- `package-report.json` ausente; método `RunHeadless` não alcançado;
- `Code 10`, token indisponível, `Code 404`, zero grupos/free entitlements e
  “No valid Unity Editor license found”: observados;
- warnings `SUCCEEDED(hr)` e `wmiOpened` permaneceram no log sanitizado;
- sinais de `-quit` limpo, retorno zero, `abort_threads` e `MemoryLeaks`: não
  observados;
- dois processos Unity/licensing ainda estavam presentes no instante anterior
  ao shutdown da sandbox;
- marcador de shutdown presente e todos os processos `WindowsSandbox*`
  terminaram naturalmente;
- nenhum processo foi encerrado nem o host foi desligado.

O r10 demonstra que a mudança do arquivo local não resolveu o entitlement: dois
candidatos distintos foram transportados com hash confirmado e ambos foram
recusados pelo LicensingClient antes da execução do pacote.

## Evidências e hashes

O resultado completo das tentativas r1–r10, incluindo os hashes da configuração
e do runner, está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/sandbox-attempt.json`
(SHA-256 `960D1E096B22456AB07A745DD084EAA33532EA460CF68BD3596F6E762C579EF5`).

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

O resultado r9 está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r9/sandbox-result.json`
(SHA-256 `C770D760743CC36F08DB863C8DCBD3AB6A5C62D3562092E6188F7A74FA5D227E`).
O log bruto r9 permanece preservado localmente com SHA-256
`DEC8C7C2529BD4B2BDFDA139E92C92F0498D8B530912517532561681B9F1FD5A`; a projeção
sanitizada está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r9/unity-sanitized.log`
(SHA-256 `E7AFC86CE5D4427668496E1E3D379CB4C7052C2ABA39C34F8D57ACE21E2D04C0`).
O runner r9 tem SHA-256
`A35F1E416A947396294AB94FA578876AC83E9D9C4B726DFDEDCDA4C5819DBF25` e a
configuração WSB r9 tem SHA-256
`2B79174A90FD0986A973C955F8534E8DC9030DC7B9882859E089629641C5BCC0`.

O resultado r10 está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r10/sandbox-result.json`
(SHA-256 `8FC3E5A983C25CC548BFE18ED18892121D3318310AA7A2573ADA4A58BEC2FF1F`).
O log bruto r10 permanece preservado localmente com SHA-256
`08F959B0772783090937C7F215216589DE4CAC02A04E4E325880FD6CD8333A2B`; a
projeção sanitizada está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r10/unity-sanitized.log`
(SHA-256 `8E164DD151DCCD2E640530842D91468913DD749F9088B9B822FC4FE93C1B0CE2`).
O runner r10 tem SHA-256
`4D8243FEFE284C310FD91C5C1506135CA644E525933CABAC88B8D4AF5FFEA261` e a
configuração WSB r10 tem SHA-256
`F1FE66DAE51CD0AD1792DAF181E2B6F6FC757F814DD1BE365F1675970DCDC0B6`.

## Alternativas seguras verificadas

Foram feitas apenas sondagens read-only de alternativas. O Docker Desktop ativo
é `29.5.3` com daemon `linux` sobre WSL2; não há daemon Windows ativo. Também
não foram encontrados VMs Windows no Hyper-V, VirtualBox ou VMware. Nenhuma
alternativa foi iniciada, e não há base técnica para executar o `Unity.exe`
Windows dentro do Docker Linux.

## Candidatos locais de licença — somente metadados

Uma inspeção estrutural read-only encontrou no host um possível arquivo de
entitlement em
`C:/Users/atnco/AppData/Local/Unity/licenses/UnityEntitlementLicense.xml`.
Nenhum valor de elemento, token ou identificador foi exposto. Após autorização
explícita, o arquivo foi somente mapeado read-only e copiado para o ambiente
descartável no r9 e no r10; não foi alterado pelo harness no host. Entre as duas
execuções, o mesmo caminho apresentou novo SHA-256 e foi tratado como candidato
distinto.

### Candidato r9 — hash histórico usado no r9

| Metadado | Resultado |
|---|---|
| Estado | `USED_CONTROLLED_NO_VALID_ENTITLEMENT` |
| Tamanho | `6731` bytes |
| SHA-256 | `89525CC063037191D198C1D3FF19FF566AB32BD6E3D3D917274EFCC8665B8926` |
| Raiz XML | `root` |
| Estrutura | inclui `Entitlement`, `License`, `Signature`, `SignedInfo`, `StartDate` e `UpdateDate` |
| Valores expostos | não |
| Cópia/montagem na sandbox | mapeamento read-only e cópia interna r9; hash confirmado |
| Verificação estrutural local | assinatura XML retornou `INVALID` no verificador read-only; resultado não foi usado como prova de ativação |
| Resultado Unity r9 | zero grupos de entitlement e zero free entitlements; retorno `198` |
| Prova de licença Unity válida | não — o Unity recusou o entitlement para `6000.5.7f1` |

### Candidato r10 — hash atualizado usado no r10

| Metadado | Resultado |
|---|---|
| Estado | `USED_CONTROLLED_NO_VALID_ENTITLEMENT` |
| Tamanho | `6731` bytes |
| SHA-256 | `C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498` |
| Valores expostos | não |
| Cópia/montagem na sandbox | mapeamento read-only e cópia interna r10; hash confirmado |
| Verificação estrutural local | não repetida; o resultado Unity r10 é a evidência de execução controlada |
| Resultado Unity r10 | zero grupos de entitlement e zero free entitlements; retorno `198` |
| Prova de licença Unity válida | não — o Unity recusou o entitlement para `6000.5.7f1` |

Os candidatos r9 e r10 já foram usados sob autorização explícita e não devem ser
repetidos. A próxima tentativa exige uma licença/ativação válida diferente ou
uma fixture própria para o ambiente; isso não autoriza qualquer execução nativa
no host.

## Classificação

| Gate | Estado | Evidência |
|---|---|---|
| carregamento/execução real do Unity | `PASS` | r10 iniciou o Unity x64, copiou o candidato atualizado e alcançou o LicensingClient |
| licensing limpo | `BLOCKED` | r10 observou zero entitlements aplicáveis, token ausente, `Code 404` e código 198 |
| método/relatório do pacote | `BLOCKED` | execução interrompida pelo licensing antes do método |
| shutdown limpo do Unity/`-quit` | `BLOCKED` | Unity saiu por entitlement inválido/ausente antes dos sinais de encerramento limpo |
| shutdown da sandbox descartável | `PASS` | marcador interno presente e processos terminaram após polling |
| segurança do host | `PASS` | não houve Unity, shutdown ou terminação forçada no host |

O `BLOCKED` atual é ambiental/de credencial e não representa falha funcional do
pacote: mesmo com dois candidatos transportados corretamente, o Unity não
reconheceu entitlement aplicável e o pacote não chegou a ser avaliado.
O `FAIL` de licensing observado é mantido explicitamente. Os diagnósticos
históricos continuam separados e não foram reutilizados como prova de ambiente
limpo.

## Risco e próxima condição de reexecução

Não alterar o pacote para contornar a licença. A próxima reexecução só é válida
quando uma licença/ativação Unity válida diferente estiver disponível dentro do
ambiente descartável, ou quando o harness/versão do Unity mudar. Nesse caso,
usar a mesma fixture, registrar novo output e repetir o ciclo completo. Não
repetir os candidatos r9/r10, symlink nem shutdown do host.

Até essa condição, o gate Unity permanece `BLOCKED` e a meta pós-E13 continua
`IN_PROGRESS`; o carregamento e o shutdown da sandbox estão comprovados, mas
licensing limpo, método do pacote e shutdown limpo do Unity não estão.
