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

- Governança relida antes do preflight e antes da execução:
  `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`.
- SHA-256 da governança: `D933DB005B7110C391CF776CDA3014CE348D61A91A5E9902AEEA619185EC3EA0`.
- Fixture mínima criada fora do produto: projeto Unity 6000.5.7f1, pacote
  `com.neoeng.dtrace` com 44 arquivos, entrada somente leitura e saída isolada.
- Configuração: rede desabilitada, VGPU desabilitado, editor mapeado somente
  leitura, `NEOENG_STAGE5_REPORT` em saída isolada e timeout interno de 240 s.
- O pedido de shutdown previsto no runner seria emitido somente dentro da
  sandbox. Ele não foi alcançado porque o runner nem chegou a iniciar.

## Inventário observado

O binário Unity foi somente inventariado; não há prova de que tenha sido
executado nesta tentativa:

| Item | Resultado |
|---|---|
| Unity | `6000.5.7f1` |
| SHA-256 Unity.exe | `BD70ECAA1F700D934628F943B36035D0E88F0C9E05A5F30549D1E92F90F6299C` |
| Windows Sandbox | recurso instalado (`InstallState=1`) |
| Versão WindowsSandbox.exe | `10.0.26100.8875` |
| SHA-256 WindowsSandbox.exe | `7BB5667331572C8A725A3A799AE7DED2912648B4F6EB7380FB51864C804C3E36` |
| Manifesto do pacote na fixture | `D267EBDDBDE32F78C146C194FCC083F2A36457EAEB73A6D3593F2CE28CC21F25` |

## Execução observada

O launcher do Windows Sandbox retornou código `0`, mas a aceitação do arquivo
`.wsb` não é evidência de runtime. A inspeção posterior encontrou uma VM
`vmmemWindowsSandbox` preexistente e uma sessão antiga mantendo o recurso
ocupado. A nova sessão foi criada pelo launcher, porém não montou a fixture:

- arquivos na saída: `0`;
- `unity.log`: ausente;
- `package-report.json`: ausente;
- marcador `UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS`: não observado;
- marcador de falha: não observado;
- execução Unity nesta tentativa: não comprovada;
- encerramento gracioso da sessão antiga solicitado, mas não concluído;
- terminação forçada de processo no host: não realizada;
- shutdown do host: não solicitado.

O resultado completo, incluindo os hashes da configuração e do runner, está em
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/sandbox-attempt.json`
(SHA-256 `230C2093A760F167B6C50B0C0A3643731A61C4A3D5C6655EEF8D166B2CD0B271`).

## Alternativas seguras verificadas

Depois do bloqueio, foram feitas apenas sondagens read-only. O Docker Desktop
ativo é `29.5.3` com daemon `linux` sobre WSL2; não há daemon Windows ativo.
Também não foram encontrados Windows VMs no Hyper-V, VirtualBox ou VMware.
Nenhuma alternativa foi iniciada, e não há base técnica para executar o
`Unity.exe` Windows dentro do Docker Linux.

## Classificação

| Gate | Estado | Evidência |
|---|---|---|
| execução real do Unity | `BLOCKED` | fixture não montada e nenhum log/relatório produzido |
| licensing | `BLOCKED` | não houve processo Unity no ambiente controlado desta tentativa |
| shutdown/`-quit` | `BLOCKED` | não houve execução que pudesse produzir sinais de encerramento |
| segurança do host | `PASS` | não houve Unity, shutdown ou terminação forçada no host |

O `BLOCKED` é ambiental e não representa falha funcional do pacote. Também não
é autorização para reutilizar logs históricos como prova: os diagnósticos
anteriores continuam separados e sem classificação de licensing/shutdown limpo.

## Risco e próxima condição de reexecução

Não alterar o pacote nem a fixture para contornar o bloqueio. A reexecução só é
válida depois que a sessão antiga do Windows Sandbox for liberada por uma ação
explicitamente controlada e verificável; então o mesmo runner e a mesma entrada
devem ser executados, produzindo novo artefato. Não repetir o teste de symlink.

Até essa condição, o gate Unity permanece `BLOCKED` e a meta pós-E13 continua
`IN_PROGRESS`; não há base para declarar licensing ou shutdown como `PASS`.
