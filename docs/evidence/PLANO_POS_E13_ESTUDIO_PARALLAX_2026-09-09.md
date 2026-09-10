# Pós-E13 — Estúdio de cenários parallax

Estado: PASS para o lote pós-E13 do estúdio. STUDIO-01, STUDIO-02, STUDIO-03
e STUDIO-04 possuem evidência técnica `PASS`.
Entrada: commit `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`, na única worktree
ativa registrada em BASE_ATIVA_POS_E13_2026-09-09.md. A build e o pacote final
estão registrados na auditoria nativa correspondente.

## Decisão autorizada pelo usuário

A solicitação de 09/09/2026 amplia os ajustes pós-E13 para um estúdio integrado,
usando as três imagens anexadas como referência de organização, não como prova
de implementação nem conteúdo redistribuível. Preservar autoria, histórico,
persistência e exportadores existentes. Não reabrir E00–E13.

## Fila única e critérios

| ID | Entrega | Estado | Aceite exigido |
|---|---|---|---|
| STUDIO-01 | Molduras, destino explícito de arraste, biblioteca e inspetor por categoria | PASS | Testes de drop/mover/lock/undo/redo e fluxo nativo capturado |
| STUDIO-02 | Sequência versionada, timeline editável, câmera e animação | PASS | Seek/play/pause/stop, não mutação de autoria, save/reopen e captura nativa |
| STUDIO-03 | Luz, partículas, áudio e texto/cutscenes sincronizados | PASS | R7: efeitos, WAV real, cutscene textual, erro de asset e recuperação, save/reopen |
| STUDIO-04 | Regressão integral, build e fluxo nativo capturado | PASS | Suíte integral, R7, build portátil, smoke oficial/direto e hashes |

## Fronteiras de engenharia

O documento de autoria V2 ganha uma extensão opcional `sequence`, com contrato
próprio versionado, ausente na serialização quando não utilizada. Campos legados
não são reinterpretados. A sequência é parte do snapshot transacional de autoria;
o relógio e a cena avaliada são transitórios. Exportações que não executam a
sequência devem recusar sua perda silenciosa, nunca anunciar suporte fictício.
Os destinos de engine precisam de prova própria antes de aceitar execução de
timeline; aparência 3D nas referências não comprova editor 3D nativo.

Leituras: governança de integridade, base pós-E13, fila mestre central,
índice documental canônico, PRODUCT-SCENE-FULL-01, ADR de runtime/efeitos.
Revisão humana e symlinks permanecem na auditoria final por decisão do usuário.
