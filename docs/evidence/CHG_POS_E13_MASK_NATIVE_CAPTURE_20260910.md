# Registro de mudança pós-E13 — identificação da janela nativa de máscara

**ID:** `CHG-P13-MASK-NATIVE-CAPTURE-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de implementação requalificada:** `cf829b7583c4a6a63fb86d8a0cafc5103808f498`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Finding reproduzido

Na primeira execução final6 do fluxo de máscara, o harness selecionou a
primeira janela secundária do processo e capturou o Editor de Cenário
Profissional, que já estava aberto. A imagem `04-mask-viewer.png` dessa
tentativa é preservada como diagnóstico e não comprova o Visualizador de
Máscara.

## Alteração controlada

- O harness agora identifica a janela por título semântico (`Mask`, `Máscara`,
  `Raio-X` ou equivalente) e falha explicitamente se ela não aparecer.
- A investigação do primeiro `BLOCKED` confirmou que o índice do menu compacto
  estava uma posição adiante; a entrada real da máscara é a sétima opção
  (`DOWN 6` a partir do primeiro item). O índice foi corrigido sem aceitar a
  janela de configurações como evidência.
- Nenhum produto, asset ou contrato de dados foi alterado.
- A próxima execução usará uma fixture de projeto com imagem carregada para
  que o visualizador seja comprovado com conteúdo real.

## IDs e impacto

- Requisitos: `REQ-F02-EVIDENCE-AUTOMATION`, `REQ-F10-UI-ACCESSIBILITY`.
- Módulos: `MOD-TOOLS-EVIDENCE`, `MOD-EDITOR-SCENE-VIEWPORT`.
- Feature: `FEAT-QA-EVIDENCE-PACKAGE`.
- Contratos preservados: abertura do visualizador pelo menu Visualizar,
  separação entre janela principal e Editor de Cenário e conteúdo da cena.
- Risco: título traduzido não ser localizado ou a janela secundária não ser
  exposta; mitigação é falha fechada com títulos observados no erro.

## Verificação exigida

- Parser PowerShell antes do commit: `PASS`.
- Build limpa vinculada ao novo commit.
- Captura `PrintWindow` do diálogo cujo título corresponda ao Visualizador de
  Máscara, com imagem carregada; a captura anterior permanece preservada.

## Requalificação final10

- A build limpa final10 foi gerada do commit `cf829b7`, com smoke `SUCCESS`
  em 11 checks.
- O fluxo nativo abriu o menu `Visualizar` por clique Win32, acionou a opção
  de máscara e capturou a janela com título
  `Visualizador de Máscara - Raio-X de Detecção Automática` e imagem carregada.
- Evidência: `artifacts/post-e13-binary-final10-20260910/mask/04-mask-viewer.png`;
  SHA-256 `948F66644F6780EEC870CF4AF3DA967411B5112B428C8ACBE09F267C33FCA120`.
- O popup de menu foi preservado em
  `artifacts/post-e13-binary-final10-20260910/mask/03-view-menu-popup-screen.png`;
  SHA-256 `9152D3FE0F56895E5074B2E8F946D4FBCC4CC91CDE772314437F7341343EFBC2`.
- A tentativa final6 que capturou a janela errada e a final7 que falhou
  fechadamente continuam preservadas; nenhuma foi sobrescrita ou promovida.

## Limitações

O serviço CUA de janelas nativas não está disponível nesta sessão. O fallback
declarado é o harness Win32 versionado (`mouse_event`/`keybd_event`/`PrintWindow`)
operando sobre o executável real; isso não é apresentado como clique CUA.

O fluxo técnico da captura passou. Este registro permanece `IN_PROGRESS` até
o gate oficial sem abort e a revisão/aceite humano formal; a indisponibilidade
do CUA continua explicitamente coberta pelo fallback Win32 declarado.
