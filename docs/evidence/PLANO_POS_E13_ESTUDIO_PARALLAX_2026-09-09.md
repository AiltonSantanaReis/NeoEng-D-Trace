# Pós-E13 — Estúdio de cenários parallax

Estado: EM IMPLEMENTAÇÃO. Nenhuma capacidade deste lote foi aceita ainda.
Entrada: HEAD 1e9eebde70592ce810dafa6109448eedbbea4566, na única worktree
ativa registrada em BASE_ATIVA_POS_E13_2026-09-09.md. A build oficial anterior
permanece válida até uma substituta ser construída e qualificada.

## Decisão autorizada pelo usuário

A solicitação de 09/09/2026 amplia os ajustes pós-E13 para um estúdio integrado,
usando as três imagens anexadas como referência de organização, não como prova
de implementação nem conteúdo redistribuível. Preservar autoria, histórico,
persistência e exportadores existentes. Não reabrir E00–E13.

## Fila única e critérios

| ID | Entrega | Estado | Aceite exigido |
|---|---|---|---|
| STUDIO-01 | Molduras, destino explícito de arraste, biblioteca e inspetor por categoria | EM IMPLEMENTAÇÃO | Criar camadas, inserir/mover imagens, reorder, lock, undo/redo |
| STUDIO-02 | Sequência versionada, timeline editável, câmera e animação | PENDENTE | Seek/loop/play/pause/stop determinísticos, sem mutar autoria, salvar/reabrir |
| STUDIO-03 | Luz, partículas, áudio e texto/cutscenes sincronizados | PENDENTE | Efeito efetivo, parâmetros, duração/loop, erro acionável e persistência |
| STUDIO-04 | Regressão integral, build e fluxo nativo capturado | PENDENTE | Suíte integral, execução do binário novo, capturas inspecionadas, hashes |

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
