# Registro de mudança — espera segura do Unity Sandbox sem encerramento prematuro

**ID:** `CHG-POST-E13-UNITY-SANDBOX-KEEPALIVE-20260913`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-13

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Checkpoint de entrada:** `8249718` (`test: reconcile Unity package and sandbox evidence contracts`)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Motivo e causa comprovada

O usuário observou que o Windows Sandbox fechava antes de a instalação do
Unity terminar. A inspeção do resultado r15 e do runner efetivamente executado
confirmou a causa determinística:

1. `control-r15/run.ps1` definia `$activationWaitLimitSeconds = 1800`;
2. o loop terminava ao atingir 1.800 segundos sem o marcador manual;
3. o runner gravava `process_exit_code=124`, `timed_out=true` e
   `trigger_observed=false`;
4. o bloco final executava incondicionalmente
   `shutdown.exe /s /t 0 /f`.

O resultado r15 mais recente (`output-r15/sandbox-result.json`) confirma
`activation_wait_seconds=1800`, ausência de `test-started.txt` e presença de
`sandbox-shutdown-requested.txt`. Portanto, não foi um fechamento espontâneo do
Windows Sandbox e nenhum Unity foi iniciado nessa execução.

A saída observada após a segunda espera foi preservada, sem sobrescrever o
registro histórico, em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r15-repeat-20260913-2037/`.
O resultado dessa repetição tem SHA-256
`E7CD1D7AFD9036F031E17B10437CEEEA2DEAED86F413E3B17412084606C6E530`.
O arquivo `sandbox-result.raw.json` existente nessa pasta é o bruto da primeira
espera r15 (`A693E73CFAA03B1488C71B97D4086109D13EBC030D388C0293D26B7AB8918276`)
e não é tratado como bruto pareado da segunda saída.

## Análise de impacto

| Área | Impacto | Proteção |
|---|---|---|
| Produto/editor canônico | nenhum | somente `artifacts/.../control-r16`, WSB, evidência e teste de contrato |
| r14/r15 históricos | nenhum retroativo | r15 permanece intacto; a repetição foi copiada para diretório próprio |
| instalação Unity | preservação opcional dentro do ambiente controlado | volume host-backed dedicado `unity-install-r16` → `C:\UnityInstall`, gravável somente pela VM |
| licensing/autenticação | continua manual | nenhum login, token, senha ou conteúdo do navegador é automatizado/coletado |
| shutdown | mais seguro | não ocorre antes de `run-test.trigger` válido ou `abort-wait.trigger` manual válido |
| fixture/projeto/runtime | somente leitura | `C:\input`, `C:\control-r16`, `C:\runtime` e o Editor conhecido continuam read-only |

## Alteração controlada

O ciclo novo r16 foi preparado com:

- espera sem limite de tempo automático enquanto a instalação ou o login manual
  estiverem em andamento;
- `waiting-for-user-login.json` atualizado periodicamente com heartbeat,
  inventário de Editor e estado dos marcadores;
- validação fail-closed do gatilho
  `MANUAL_HUB_LOGIN_CONFIRMED_BY_USER=true`;
- abort somente mediante
  `MANUAL_WAIT_ABORT_REQUESTED_BY_USER=true`;
- encerramento condicionado exclusivamente ao gatilho válido ou ao abort manual;
- `editor-path.trigger` opcional e restrito aos mounts aprovados, permitindo
  selecionar uma instalação concluída no volume persistente;
- destino persistente explícito `C:\UnityInstall` para impedir que a instalação
  seja perdida quando a VM descartável for encerrada;
- fallback preservado para o Editor conhecido `6000.5.7f1` montado em
  `C:\Unity\Editor`.

O r16 foi executado depois da confirmação manual do proprietário. O método do
pacote passou, mas a instalação persistida 6000.6 não foi observada no mount
`C:\UnityInstall`; o fallback conhecido 6000.5.7f1 foi selecionado. Licensing e
shutdown limpos do Unity continuam `BLOCKED_PARTIAL` pelos diagnósticos
preservados no resultado real.

## Resultado da execução r16

O runner aguardou `2466` segundos sem timeout automático e só iniciou o teste
após `MANUAL_HUB_LOGIN_CONFIRMED_BY_USER=true`. O Unity real executou dentro da
Sandbox com rede habilitada, alcançou o pacote corrigido e retornou `0`. O
`package-report.json` registrou `Success=true`, pacote `com.neoeng.dtrace`,
versão `0.3.0`, política `source-only` e sete checks aprovados.

O log sanitizado preservou `Unity Personal`/`Unlimited`, `Code 10`, token
indisponível, warnings `SUCCEEDED(hr)`/`wmiOpened`, erro `Failed to open WMI` e
`Curl error 42: Callback aborted`. O Unity produziu quit de batchmode e saída de
batchmode, mas não o sinal textual exato `Shut down.`; o runner observou 29
entradas de processos compatíveis antes do encerramento da Sandbox. Por isso o
shutdown limpo do Unity não é promovido a `PASS`. A Sandbox descartável terminou
no polling posterior e o host não executou Unity, shutdown ou terminação forçada.

Evidências versionáveis do r16 estão em
`output-r16-real-20260914-0122/`; o log bruto permanece local, sem ser
versionado, e a projeção sanitizada passou na varredura de privacidade.

## Gates desta mudança

| Gate | Estado | Evidência |
|---|---|---|
| causa do fechamento prematuro | `PASS` | resultado r15 com timeout 1.800 s e runner r15 com shutdown incondicional |
| preservação da repetição r15 | `PASS` | diretório `output-r15-repeat-20260913-2037` e hashes acima |
| contrato estático e evidência real do r16 | `PASS` | `tests/test_unity_sandbox_harness.py`: 5 testes, `5 passed`; o quinto valida o resultado real sem promover shutdown parcial a PASS |
| parse PowerShell/XML | `PASS` | r15/r16/wrapper sem erro de parse; WSB r16 XML válido com 7 mapeamentos |
| regressão oficial sem filtros | `PASS` | `artifacts/audit-post-e13-official-suite-safe-host-20260913-r14/official-pytest.log`: `2639 passed`, `2 skipped`, `0 failed`, `0 warnings`; log sanitizado `920C7189382C9606AD08A1A36A4000510340A3316E8025D666712338CE1CE222`, JUnit sanitizado `E0E4C70D0A93E1AC45DA5537D423DA15290DDD2F67482E16F156DCF56AB057CB`, metadata `D06F8FC9FFE4EB105ADB233D6E242E9DF74B9770AA66822602FEED2DDFE7FD99` |
| instalação persistida no Sandbox | `PENDING_EVIDENCE` | `C:\UnityInstall` estava vazio no inventário r16; a instalação 6000.6 não foi atribuída, e o fallback 6000.5.7f1 foi usado |
| método/relatório do pacote | `PASS` | resultado r16 e `package-report.json`: `Success=true`, processo com código `0` |
| Unity/licensing limpo | `BLOCKED_PARTIAL` | r16 resolveu `Unity Personal`/`Unlimited`, mas preservou `Code 10` e token indisponível |
| shutdown limpo do Unity | `BLOCKED_PARTIAL` | quit/retorno `0` presentes, mas 29 entradas compatíveis no snapshot e nenhum `Shut down.` exato |
| shutdown da Sandbox | `PASS_SANDBOX_ONLY` | marcador interno e processos da Sandbox terminaram no polling posterior |

## Regra de avanço

O r16 já consumiu a confirmação e validou a correção
`ImageConversionModule`/`AnimationModule`. Não criar novo `run-test.trigger` sem
mudança relevante ou uma decisão explícita para qualificar 6000.6, investigar
`Code 10`/token ou comprovar shutdown limpo; qualquer novo ciclo deve ser uma VM
descartável nova, com handoff/login manual e evidência própria.

Symlink, shutdown e qualquer teste potencialmente danoso continuam proibidos no
host; o `shutdown.exe` desta mudança existe apenas dentro do Windows Sandbox.
