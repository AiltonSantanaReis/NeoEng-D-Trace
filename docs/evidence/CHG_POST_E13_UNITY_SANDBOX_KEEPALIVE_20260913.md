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

O r16 não declara que a instalação, o licensing, o método do pacote ou o
shutdown limpo do Unity passaram. Esses critérios continuam `PENDING_EVIDENCE`
até uma execução real após confirmação manual do proprietário.

## Gates desta mudança

| Gate | Estado | Evidência |
|---|---|---|
| causa do fechamento prematuro | `PASS` | resultado r15 com timeout 1.800 s e runner r15 com shutdown incondicional |
| preservação da repetição r15 | `PASS` | diretório `output-r15-repeat-20260913-2037` e hashes acima |
| contrato estático do r16 | `PASS` | `tests/test_unity_sandbox_harness.py`: 4 testes, `4 passed` |
| parse PowerShell/XML | `PASS` | r15/r16/wrapper sem erro de parse; WSB r16 XML válido com 7 mapeamentos |
| regressão oficial sem filtros | `PASS` | `artifacts/audit-post-e13-official-suite-safe-host-20260913-r13/official-pytest.log`: `2638 passed`, `2 skipped`, `0 failed`, `0 warnings`; blob do log `9420B5B092E56031DF81DC88281AF36328E4665E2D0D08E3ACAFE9B0F35C442A`, JUnit `EBAF912E1A84CA42DEABB77F61488EA6C3B3C38DF7F05D85CF039E6C8A503011` |
| instalação persistida no Sandbox | `PENDING_EVIDENCE` | requer execução manual do Hub dentro do r16 |
| Unity/licensing/package report/shutdown limpo | `PENDING_EVIDENCE` | requer `run-test.trigger` após instalação/login confirmados |

## Regra de avanço

Não criar `run-test.trigger` nem iniciar Unity até o proprietário confirmar que
o Editor terminou de instalar. A próxima execução deve ser uma VM descartável
nova com o WSB r16, handoff/login manual, captura dos marcadores e logs reais,
seguida de validação da correção `ImageConversionModule`/`AnimationModule`.

Symlink, shutdown e qualquer teste potencialmente danoso continuam proibidos no
host; o `shutdown.exe` desta mudança existe apenas dentro do Windows Sandbox.
