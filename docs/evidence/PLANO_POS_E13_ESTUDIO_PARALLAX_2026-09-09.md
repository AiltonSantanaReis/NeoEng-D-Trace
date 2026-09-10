# Pós-E13 — Estúdio de cenários parallax

Estado: EM IMPLEMENTAÇÃO. STUDIO-01, STUDIO-02 e STUDIO-03 possuem evidência
técnica `PASS`; STUDIO-04 permanece `IN_PROGRESS` até a nova build do commit
final desta correção.
Entrada: commit `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9`, na única worktree ativa registrada em
BASE_ATIVA_POS_E13_2026-09-09.md. A build anterior permanece apenas como
evidência histórica; o pacote final desta correção ainda será reconstruído.

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
| STUDIO-04 | Regressão integral, build e fluxo nativo capturado | IN_PROGRESS | Suíte e R7 passaram; build portátil final do commit `fd77ab9d658a043ea8f47b41d51e98d9e0e19cc9` ainda pendente |

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
