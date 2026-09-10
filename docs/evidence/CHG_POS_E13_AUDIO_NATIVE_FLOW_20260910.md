# Registro de mudança pós-E13 — evidência nativa de áudio na timeline

**ID:** `CHG-P13-AUDIO-NATIVE-FLOW-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de implementação requalificada:** `cf829b7583c4a6a63fb86d8a0cafc5103808f498`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Finding reproduzido

O fluxo nativo anterior da timeline comprovava câmera, luz, chuva/partículas e
texto/cutscene, mas não havia uma captura de um usuário escolhendo um arquivo
de áudio e criando um clip na linha `Áudio`. A existência do seletor não foi
tratada como prova de funcionamento.

## Alteração controlada

- O harness gera uma fixture WAV PCM silenciosa de um segundo dentro do projeto
  temporário, sem tocar nos assets do usuário.
- O fluxo seleciona `Áudio`, abre o diálogo nativo, captura o diálogo real,
  informa o caminho do WAV por teclado, captura o clip criado e depois continua
  com o clip de texto/cutscene.
- O fluxo não altera contratos de áudio, schema, reprodução ou persistência do
  produto; ele somente amplia a prova funcional nativa.

## IDs e impacto

- Requisitos: `REQ-F09-PLAYBACK-CONTROL`, `REQ-F10-UI-ACCESSIBILITY`,
  `REQ-F02-EVIDENCE-AUTOMATION`.
- Módulos: `MOD-RUNTIME-PLAYBACK`, `MOD-TOOLS-EVIDENCE`.
- Features: `FEAT-PARTICLE-REPLAY`, `FEAT-UI-ACCESSIBILITY`,
  `FEAT-QA-EVIDENCE-PACKAGE`.
- Contratos preservados: seleção de tipos da timeline, preparação de assets,
  referência por hash e todos os clips existentes.
- Risco principal: o diálogo de arquivo não ser identificado como janela do
  processo ou o WAV não ser aceito pelo fluxo de importação.
- Mitigação: falha explícita se o diálogo não aparecer, captura do diálogo e
  do estado final, além dos testes de sequência e áudio já existentes.

## Verificação exigida

- Parser PowerShell: `PASS` antes do commit.
- Nova build limpa, com commit identificado.
- Capturas reais `PrintWindow` após entrada Win32 no executável final:
  `09-sequence-studio-audio-dialog.png` e
  `10-sequence-studio-audio-clip.png`.
- A captura deverá mostrar o clip na linha `Áudio`, a referência importada e
  a ausência de erro; playback e recuperação de arquivo ausente continuam
  vinculados às evidências específicas do painel e não serão inferidos desta
  única captura.

## Requalificação final10

- A build limpa final10 foi gerada do commit `cf829b7`, com smoke `SUCCESS`
  em 11 checks.
- O fluxo abriu o seletor nativo por clique Win32, informou uma fixture WAV
  PCM silenciosa de um segundo, criou o clip na linha `Áudio` e prosseguiu
  até o clip real de `Texto / cutscene`.
- Diálogo de áudio: `artifacts/post-e13-binary-final10-20260910/sequence/09-sequence-studio-audio-dialog.png`;
  SHA-256 `373B5428B0B1541A96EFC5B1CABF8F5A2DB61883DBA4E15B59D673411BDFFFAE`.
- Clip de áudio: `artifacts/post-e13-binary-final10-20260910/sequence/10-sequence-studio-audio-clip.png`;
  SHA-256 `7FCE9CF499AB614588D452FBFCAD8B7E4CC6006E2F31251A477E8EA582543DD7`.
- Clip final de texto/cutscene: `artifacts/post-e13-binary-final10-20260910/sequence/11-sequence-studio-text-clip-real.png`;
  SHA-256 `818AF471F12ACCB376BCD1F391065D8F4A6169279C8783ADD0BEF7015E5E8825`.
- A execução confirmou câmera, luz, chuva/partículas, áudio e texto. A
  timeline oferece rolagem vertical quando o número de trilhas cresce; isso
  é registrado como melhoria de densidade, não como perda de clip.

## Evidência anterior preservada

O pacote anterior `artifacts/post-e13-binary-final5-20260910/sequence/` não é
apagado nem reclassificado; ele permanece como diagnóstico que comprovava os
outros quatro tipos de clip, mas não o áudio.

O fluxo técnico passou. Este registro permanece `IN_PROGRESS` até o gate
oficial sem abort e a revisão/aceite humano formal.
