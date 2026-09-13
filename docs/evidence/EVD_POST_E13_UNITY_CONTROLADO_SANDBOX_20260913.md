# Evidência pós-E13 — tentativa Unity em Windows Sandbox controlado

**ID da feature:** `AUD-POST-E13-UNITY-CONTROLLED-SANDBOX-20260913`
**Status:** `BLOCKED`
**Data:** 2026-09-13
**Requisito:** `REQ-POST-E13-UNITY-LICENSING-SHUTDOWN-20260913`
**Decisão habilitadora:** `DECISAO-POST-E13-LIMITE-PERFORMANCE-SOAK-CONTROLADO-20260913`
**Commit auditado:** `adc4db85ffc1c6dc1c5cfb0331c97043423600d0`

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
- Configuração-base r8–r10: rede e VGPU desabilitados, clipboard/impressora/
  áudio/vídeo desabilitados, memória limitada a 8192 MB. As requalificações r11
  e r12 usaram rede habilitada somente dentro da Sandbox descartável; VGPU e
  demais redirecionamentos permaneceram desabilitados.
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
| Execução real Unity | comprovada no r12: `process_started=true`; candidato atualizado transportado com rede habilitada, zero entitlements aplicáveis |

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
| r11 | `BLOCKED` | WSB com rede habilitada executou Unity, mas o runner herdado registrou `networking=disabled`; zero entitlements e código 198; falha de metadado preservada |
| r12 | `BLOCKED` | WSB e runner registraram rede habilitada; candidato foi copiado com hash correspondente; Unity novamente encontrou zero entitlements e saiu com código 198 |

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

## Execução real r11 com rede habilitada — metadado inconsistente

O r11 foi uma requalificação controlada para verificar se a validação offline
era a causa do bloqueio. O manifesto WSB tinha `<Networking>Enable</Networking>`
e SHA-256 `6E61952B3ED34F8AE2ABC812DC5BCF02C391246B39FE4F1B8C7A0372F1999060`;
o runner herdado ainda serializou `networking=disabled` no resultado. Essa
divergência é uma falha de instrumentação (`harness_metadata_status=FAIL`), não
foi corrigida retroativamente e não é usada como prova final de rede.

O Unity, contudo, foi executado dentro da Sandbox: `process_started=true`,
`timed_out=false`, retorno `198`, LicensingClient alcançado, `Code 10`, token
indisponível, `Code 404`, zero grupos/free entitlements e ausência de
`com.unity.editor.headless`. O `package-report.json` não foi produzido; os
warnings `SUCCEEDED(hr)` e `wmiOpened` permaneceram no log sanitizado; sinais de
`-quit` limpo, retorno zero, `abort_threads` e `MemoryLeaks` não foram observados.
O marcador de shutdown existiu, os processos terminaram após polling e nenhum
processo/ shutdown foi executado no host.

Hashes do r11: resultado
`AE1D1B036AF836A1EE069A24D2A8E6D06A5D21AEDF11A1B9BF114A3B2665F07D`; log bruto
local `FEAD966D64FFE466E8D7E062F32CD904F0B010946D3CA5F02A5065A7C1094153`;
projeção sanitizada
`97441BA7E373BDB435D6817A5B4C3A086D68C963078D0703D3133A9B6D21EAF1`; runner
`4D8243FEFE284C310FD91C5C1506135CA644E525933CABAC88B8D4AF5FFEA261`; licença
`C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498` na origem
e destino dentro da Sandbox. O log bruto não é versionado.

## Execução real r12 com rede habilitada e runner corrigido

Para eliminar a ambiguidade do r11, o runner r12 alterou somente o metadado do
resultado para `networking=enabled`; o manifesto WSB permaneceu com rede
habilitada e foi separado em `output-r12`. A validação estática passou com XML
válido, seis mapeamentos, somente `C:\output` gravável, runner PowerShell sem
erros de parse, nenhum processo Unity/Sandbox no host e licença com hash
esperado.

O resultado r12 confirmou `networking=enabled`, `process_started=true`,
`timed_out=false` e `process_exit_code=198`. A licença de `6731` bytes foi
copiada dentro da Sandbox com SHA-256
`C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498` na origem
e no destino. O Unity alcançou o LicensingClient, mas registrou `Code 10`,
token indisponível, `Code 404`, zero entitlement groups/free entitlements e
`com.unity.editor.headless` ausente. `package-report.json` não existe e
`RunHeadless` não foi alcançado; o retorno `198` ocorreu antes do pacote.

Os warnings `SUCCEEDED(hr)` e `wmiOpened` foram preservados. Os sinais de
`-quit` limpo, retorno zero, `abort_threads` e `MemoryLeaks` não apareceram.
O marcador de shutdown foi produzido e a Sandbox terminou naturalmente; nenhum
processo foi encerrado nem o host foi desligado.

Hashes do r12: resultado
`E95995806B98A263F44C43FE487FF3615447B88B24DD27CEA95933A6079BC960`; log bruto
local `96E220638A19A677ADF9D6F81381E2EFE4A887D7B08A60A75E1E13B33DD01E8A`;
projeção sanitizada
`7D0FDC95E631C30EFD00535D33E9BD6DCEE9166FFAF813B3600826F90E873598`; runner
`1ACA40E88B8DDEC7D3C16CF4C1EED8C95C2ED869A5BC2E31DA86A1EC4BEC781D`; WSB
`22400D86B5C909D7267FC2B19A99BAEE1B20FD9BD92B78600A2F625D7913C96B`.

## Evidências e hashes

O resultado completo das tentativas r1–r12, incluindo os hashes da configuração
e do runner, está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/sandbox-attempt.json`
(SHA-256 `B372556C39A32CCAF295C64DBB3FC45910EE02E8A844FFFABC0AF0C42EEDC3C4`).

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
(SHA-256 `1D454F48223C295381D81BB1575022DFB7A4D1B70A9D9BBE4B58230D01FE1B4F`).
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
(SHA-256 `DAB84CC6C3D1045AE8027F3CA4E75579053C701DBC0FD47B8BDC415FBE095661`).
O log bruto r10 permanece preservado localmente com SHA-256
`08F959B0772783090937C7F215216589DE4CAC02A04E4E325880FD6CD8333A2B`; a
projeção sanitizada está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r10/unity-sanitized.log`
(SHA-256 `8E164DD151DCCD2E640530842D91468913DD749F9088B9B822FC4FE93C1B0CE2`).
O runner r10 tem SHA-256
`4D8243FEFE284C310FD91C5C1506135CA644E525933CABAC88B8D4AF5FFEA261` e a
configuração WSB r10 tem SHA-256
`F1FE66DAE51CD0AD1792DAF181E2B6F6FC757F814DD1BE365F1675970DCDC0B6`.

O resultado r11 está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r11/sandbox-result.json`
(SHA-256 `AE1D1B036AF836A1EE069A24D2A8E6D06A5D21AEDF11A1B9BF114A3B2665F07D`).
O log bruto r11 permanece localmente com SHA-256
`FEAD966D64FFE466E8D7E062F32CD904F0B010946D3CA5F02A5065A7C1094153`; a
projeção sanitizada está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r11/unity-sanitized.log`
(SHA-256 `97441BA7E373BDB435D6817A5B4C3A086D68C963078D0703D3133A9B6D21EAF1`).
O runner r11 tem SHA-256
`4D8243FEFE284C310FD91C5C1506135CA644E525933CABAC88B8D4AF5FFEA261` e a
configuração WSB r11 tem SHA-256
`6E61952B3ED34F8AE2ABC812DC5BCF02C391246B39FE4F1B8C7A0372F1999060`.

O resultado r12 está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r12/sandbox-result.json`
(SHA-256 `E95995806B98A263F44C43FE487FF3615447B88B24DD27CEA95933A6079BC960`).
O log bruto r12 permanece localmente com SHA-256
`96E220638A19A677ADF9D6F81381E2EFE4A887D7B08A60A75E1E13B33DD01E8A`; a
projeção sanitizada está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r12/unity-sanitized.log`
(SHA-256 `7D0FDC95E631C30EFD00535D33E9BD6DCEE9166FFAF813B3600826F90E873598`).
O runner r12 tem SHA-256
`1ACA40E88B8DDEC7D3C16CF4C1EED8C95C2ED869A5BC2E31DA86A1EC4BEC781D` e a
configuração WSB r12 tem SHA-256
`22400D86B5C909D7267FC2B19A99BAEE1B20FD9BD92B78600A2F625D7913C96B`.

## Alternativas seguras verificadas

Foram feitas apenas sondagens read-only de alternativas. O Docker Desktop ativo
é `29.5.3` com daemon `linux` sobre WSL2; não há daemon Windows ativo. Também
não foram encontrados VMs Windows no Hyper-V, VirtualBox ou VMware. Nenhuma
alternativa foi iniciada, e não há base técnica para executar o `Unity.exe`
Windows dentro do Docker Linux.

## Candidatos locais de licença — somente metadados

Uma inspeção estrutural read-only encontrou no host um possível arquivo de
entitlement em
`<redacted-host-license-fixture>/UnityEntitlementLicense.xml`.
Nenhum valor de elemento, token ou identificador foi exposto. Após autorização
explícita, o arquivo foi somente mapeado read-only e copiado para o ambiente
descartável no r9, r10, r11 e r12; não foi alterado pelo harness no host. Entre
r9 e r10, o mesmo caminho apresentou novo SHA-256 e foi tratado como candidato
distinto; r11 e r12 reutilizaram o candidato corrente para qualificar o efeito
da rede e do harness, sem copiar credenciais ou tokens.

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

### Requalificação r11/r12 com o mesmo candidato corrente

| Tentativa | Configuração de rede | Integridade do metadado | Resultado |
|---|---|---|---|
| r11 | WSB `Enable` | `FAIL`: o runner registrou `disabled` | Unity alcançou LicensingClient, encontrou zero entitlements e saiu `198` |
| r12 | WSB `Enable` | `PASS`: WSB e resultado registraram `enabled` | Unity alcançou LicensingClient, encontrou zero entitlements e saiu `198` |

O hash do candidato foi `C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498`
nas duas cópias internas. O resultado r11 não é usado para afirmar que a rede
estava desabilitada; ele comprova uma execução real com falha de instrumentação.
O r12 é a prova coerente para a requalificação com rede e mantém o gate de
licensing `BLOCKED`.

Os ensaios r9–r12 já foram usados sob autorização explícita e não devem ser
repetidos sem mudança relevante. A próxima tentativa exige uma licença/ativação
válida diferente, uma fixture própria ou alteração material do harness/engine/
configuração; isso não autoriza qualquer execução nativa no host.

## Classificação

| Gate | Estado | Evidência |
|---|---|---|
| carregamento/execução real do Unity | `PASS` | r12 iniciou o Unity x64 em Sandbox com rede habilitada, copiou o candidato atualizado e alcançou o LicensingClient |
| licensing limpo | `BLOCKED` | r12 observou zero entitlements aplicáveis, token ausente, `Code 404` e código 198; r11 mantém falha de metadado do harness |
| método/relatório do pacote | `BLOCKED` | execução interrompida pelo licensing antes do método |
| shutdown limpo do Unity/`-quit` | `BLOCKED` | Unity saiu por entitlement inválido/ausente antes dos sinais de encerramento limpo |
| shutdown da sandbox descartável | `PASS` | marcador interno presente e processos terminaram após polling |
| segurança do host | `PASS` | não houve Unity, shutdown ou terminação forçada no host |

O `BLOCKED` atual é ambiental/de credencial e não representa falha funcional do
pacote: mesmo com o candidato transportado corretamente em quatro execuções e
com a rede habilitada de forma coerente no r12, o Unity não reconheceu
entitlement aplicável e o pacote não chegou a ser avaliado.
O `FAIL` de licensing observado é mantido explicitamente. Os diagnósticos
históricos continuam separados e não foram reutilizados como prova de ambiente
limpo.

## Risco e próxima condição de reexecução

Não alterar o pacote para contornar a licença. A próxima reexecução só é válida
quando uma licença/ativação Unity válida diferente estiver disponível dentro do
ambiente descartável, ou quando houver mudança material no harness, configuração
de rede ou versão do Unity. Nesse caso, usar a mesma fixture, registrar novo
output e repetir o ciclo completo. Não repetir r9/r10/r12 sem mudança relevante,
nem symlink ou shutdown do host; o r11 não precisa ser repetido porque seu
metadado inválido já foi corrigido e preservado.

Até essa condição, o gate Unity permanece `BLOCKED` e a meta pós-E13 continua
`IN_PROGRESS`; o carregamento e o shutdown da sandbox estão comprovados, mas
licensing limpo, método do pacote e shutdown limpo do Unity não estão.
