# Registro de mudança pós-E13 — identificação da janela nativa de máscara

**ID:** `CHG-P13-MASK-NATIVE-CAPTURE-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de implementação:** `86bdc53dca954a94f2d63436d9b287b9dbc967fc`

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

## Limitações

O serviço CUA de janelas nativas não está disponível nesta sessão. O fallback
declarado é o harness Win32 versionado (`mouse_event`/`keybd_event`/`PrintWindow`)
operando sobre o executável real; isso não é apresentado como clique CUA.

Até a nova build e revisão da captura correta, este registro permanece
`IN_PROGRESS`.
