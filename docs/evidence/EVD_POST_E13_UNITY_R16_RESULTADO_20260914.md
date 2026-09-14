# Evidência pós-E13 — resultado corrente do Unity r16 em Windows Sandbox

**ID:** `EVD-POST-E13-UNITY-R16-RESULTADO-20260914`
**Status:** `IN_PROGRESS`
**Data da execução:** 2026-09-14
**Requisito:** `REQ-POST-E13-UNITY-LICENSING-SHUTDOWN-20260913`
**Ambiente:** Windows Sandbox descartável, com rede habilitada somente dentro da VM
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**SHA-256 da governança:** `D933DB005B7110C391CF776CDA3014CE348D61A91A5E9902AEEA619185EC3EA0`

## Escopo e regra de segurança

Esta evidência reconcilia a execução real r16 já concluída depois da confirmação
manual do proprietário de que a instalação/autenticação estavam prontas. Ela
não inicia Unity, não repete o ciclo e não executa `shutdown`, encerramento
forçado ou symlink no host. O objetivo é separar, com precisão, o que foi
comprovado do que ainda está bloqueado por diagnóstico incompleto.

O checkout e a fixture de entrada foram usados de forma somente leitura; a
saída ficou isolada no pacote de evidências. O log bruto permanece apenas no
ambiente controlado local, pois contém identificadores voláteis. A projeção
sanitizada versionada preserva os sinais funcionais e redige somente dados
voláteis.

## Execução real observada

| Item | Resultado factual |
|---|---|
| Editor realmente executado | Unity `6000.5.7f1` (`6000.5.7.96354`) |
| Motivo da seleção | o mount `C:\UnityInstall` não continha `Unity.exe`; foi usado o fallback mapeado `C:\Unity\Editor\Unity.exe` |
| Unity `6000.6` | inventariado na interface do Hub, mas não atribuído a esta execução |
| Handoff/login | confirmação manual recebida; espera controlada de `2466 s`, sem timeout automático |
| Processo Unity | iniciado, sem timeout, código de saída `0` |
| Pacote | `com.neoeng.dtrace`, versão `0.3.0`, `SourcePolicy=source-only` |
| Checks do pacote | `7/7` `Success=true`: nome, versão, manifesto, assemblies, contrato de identidade e fonte somente código |
| Resultado da Sandbox | marcador produzido dentro da VM; descarte terminou no polling posterior |
| Host | nenhum Unity, shutdown ou terminação forçada executado |

O relatório do pacote comprova a execução do método corrigido e não é uma
prova de importação de um modelo 3D. O asset `Eclipse Warden` continua com
importação nativa Unity pendente até ser aberto por um importador glTF/OBJ
adotado pelo projeto; o r16 qualificou o pacote UPM, não esse importador.

## Diagnósticos preservados

| Sinal | Observação r16 | Estado controlado |
|---|---:|---|
| `Unity Personal` / `Unlimited` | presente | `PASS` como entitlement resolvido nessa execução |
| `Code 10` | 1 ocorrência | `BLOCKED` para licensing limpo |
| `Access token is unavailable` | 1 ocorrência | `BLOCKED` para licensing limpo |
| `Failed to open WMI` / `wmiOpened` | presentes | `BLOCKED` para diagnóstico de ambiente limpo |
| `SUCCEEDED(hr)` | 2 ocorrências | warning preservado; não convertido em falha do pacote |
| `Curl error 42: Callback aborted` | 1 ocorrência | `BLOCKED` para rede/telemetria limpa |
| `batchmode quit` / saída de batchmode / retorno `0` | presentes | `PASS` para o caminho de saída observado |
| `Shut down.` | ausente | `BLOCKED` para shutdown limpo comprovado |
| `abort_threads` / `MemoryLeaks` | ausentes no r16 | observação limitada; não prova ausência universal |
| processos compatíveis antes do descarte | `29` entradas | `BLOCKED` para prova de encerramento individual; os nomes não foram coletados |

O entitlement resolvido e o código de saída zero não anulam os diagnósticos
negativos. O snapshot com 29 nomes compatíveis também não prova que todos eram
instâncias do Editor; por isso o resultado não afirma vazamento nem shutdown
incorreto, apenas mantém o gate sem prova suficiente.

## Matriz de gates

| Gate | Estado | Limite da conclusão |
|---|---|---|
| Execução real do Unity em ambiente controlado | `PASS` | Unity x64 iniciou e concluiu o método do pacote dentro da Sandbox |
| Contrato/relatório do pacote UPM | `PASS` | relatório r16 com sete checks aprovados e código `0` |
| Entitlement observado | `PASS` | `Unity Personal`/`Unlimited` foi resolvido nessa sessão |
| Licensing limpo | `BLOCKED` | `Code 10`, token indisponível e warnings de ambiente permanecem |
| Saída batchmode observada | `PASS` | `quit`, saída de batchmode e retorno `0` foram observados |
| Shutdown limpo do Unity | `BLOCKED` | marcador `Shut down.` ausente e snapshot de processos não individualizado |
| Descarte/shutdown da Sandbox | `PASS` | marcador interno e término da VM ocorreram somente no ambiente descartável |
| Segurança do host | `PASS` | não houve execução perigosa nativa neste computador |
| Importação do asset 3D no Unity | `PENDING_EVIDENCE` | r16 não abriu GLB/OBJ; a entrega e o guia permanecem preparados para esse ciclo específico |

O status geral permanece `IN_PROGRESS`: os gates de execução, pacote, entitlement
observado, saída batchmode, Sandbox e segurança passaram, mas licensing limpo,
shutdown limpo e importação do asset Unity ainda não foram comprovados.

## Artefatos hashados

Pacote corrente:
`artifacts/audit-post-e13-unity-controlled-windows-sandbox-20260913-r1/output-r16-real-20260914-0122/`

| Artefato | SHA-256 da cópia de execução |
|---|---|
| `sandbox-result.json` | `ECD0247241D50CCB0964E4429ECAD6768EAA88EA83A9AEFA9EE563B87357BA00` |
| `package-report.json` | `9D4DE5C4459A88BAD7CDD65A9307862B13F44205CC29FAB14CE372D058FBF508` |
| `editor-inventory.json` | `77C27583B95982739C8B5E6AF1D4C70A4B9EA840180B244B19DD62E0FF6BADC9` |
| `editor-selection.json` | `7EEB1C83D082BA934825D2426F9EAC888A4F762EAFD4590D4C4ED9379E260C81` |
| `unity-sanitized.log` | `1AE9D29017AC7BF3AAB978B22F48460D7623A000115D1298275306C84A8FC4E2` |
| `sandbox-shutdown-requested.txt` | `0B278D52B26FFDD0E9C2470BD90F958D93B6C40F6468AF9920FF24B3B23A1D5D` |
| `../output-r16/run-test.trigger` (gatilho preservado) | `6BE88D3F8EF163DA43243E4EE8E40BB22ED650B8B2F759B00E618AD2F6AA8CC6` |

Os hashes da configuração e dos runners permanecem registrados no relatório
cumulativo `EVD_POST_E13_UNITY_CONTROLADO_SANDBOX_20260913.md`. O bruto r16 não
é promovido ao repositório; sua existência e seu hash local continuam
registrados nessa evidência cumulativa.

## Relação com o asset destinado ao Unity

O asset entregue em
`artifacts/post-e13-3d-asset-unity-20260914-r3/` possui GLB glTF 2.0,
OBJ/MTL auxiliar, materiais PBR, UV0, skin e animação, com validação estrutural
e preview Godot reais já aprovados no relatório próprio. Entretanto, Unity não
oferece aqui uma prova nativa de abertura do GLB/OBJ. O guia recomenda iniciar
com rig Generic e confirma que essa recomendação não substitui um import real.
Não será afirmado Humanoid, URP/HDRP, escala, orientação ou deformação sem essa
execução específica.

## Regra de reexecução

Não repetir o r16 apenas por alteração documental, visual do editor, localização
ou asset que não altere o pacote/fixture Unity. Abrir um novo ciclo descartável
somente se ocorrer uma mudança material na versão do Unity, no importador/asset
fixture, na licença/harness/rede ou se houver decisão formal para comprovar o
shutdown limpo e a importação Unity do asset. O próximo ciclo, se necessário,
deverá registrar a versão efetivamente selecionada, login manual, logs
sanitizados, snapshot individual de processos e resultado do importador sem
reutilizar o timeout r15.
