# Evidência P2D-05/O-2 — auditoria de preview e viewport

**Fase:** abertura formal de O-2
**Status:** `AUDIT COMPLETE — ACCEPTED / CLOSED`
**Data:** 30/08/2026 (UTC-03)
**HEAD auditado:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Branch:** `p2d-05-quality-hardening`
**Rollback:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Commit técnico:** `ffb97eb788d1acecc2d874dd84f9fb6f1e51c0ef`.

## 1. Limite da auditoria

Esta auditoria foi somente de leitura. Antes da abertura documental, a prova
do repositório registrou HEAD e branch esperados, zero arquivos tracked
modificados e zero arquivos staged. A abertura de O-2 altera apenas a
documentação do plano e cria a decisão/evidência deste estágio; nenhum código,
schema, formato, coordenada, exportador ou comportamento foi alterado.

O contrato formal é
`docs/DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`. A implementação
do lote foi qualificado com testes, benchmark e captura vinculados conforme
a decisão `docs/DECISAO_P2D_05_O2_IMPLEMENTACAO_2026-08-30.md`.

## 2. Constatações no código atual

### 2.1 Sincronização completa

Em `src/ui/scene_authoring_viewport.py`, `SceneAuthoringViewport.sync()`:

- chama `QGraphicsScene.clear()`;
- limpa os mapas de objetos, sockets e gizmo;
- percorre os objetos na ordem canônica;
- filtra visibilidade efetiva, layers, groups e isolamento;
- resolve e decodifica assets, com cache de pixmap limitado à chamada;
- cria novamente os itens gráficos;
- recalcula transforms, seleção, gizmo e navegação.

`set_geometry()` e a troca do modo preview chamam `sync()` diretamente.

### 2.2 Caminho incremental existente

`_on_session_change()` compara IDs visíveis, sockets, estado dos assets e ordem
das layers. Quando esses elementos não mudam, chama
`_refresh_after_model_change()`, que atualiza transforms, gizmo e o viewport.
Quando um elemento estrutural muda, usa `sync()` completo.

Essa distinção já existente será preservada e medida. A auditoria não conclui
que a reconstrução completa é necessariamente um defeito: a necessidade de
reuso de item, cache persistente ou índice espacial deverá ser demonstrada pelo
profiling do O-2-0.

### 2.3 Separação do histórico O-1

O-1 alterou a representação do histórico de transforms e a finalização de
gestos. O preview de gesto continua restaurando a base antes de reaplicar a
transformação. A experiência incremental rejeitada está documentada em
`artifacts/p2d05/o1-gesture-ab-20260830.json` e não será reaberta por
inferência em O-2.

O-2 não pode modificar `src/core/scene_authoring_session.py`. Caso o profiling
mostre que o caminho de preview de gesto também exige alteração, o trabalho
deverá ser interrompido e uma decisão específica deverá ser aberta.

## 3. Evidência quantitativa existente

O relatório histórico
`artifacts/p2d05/calibration-o1-final-20260830.json` contém 8 workloads, 50
amostras, 5 warm-ups e medição de memória separada. No workload de 512 objetos,
`preview_sync` registrou p95 aproximado de 76,48 ms com asset compartilhado e
949,59 ms com assets únicos.

Esses valores foram coletados no worktree O-1 antes do commit e o conteúdo
medido foi consolidado em `15300a0d580a57110828d8511ae48a0f68326e3a`. Eles
servem como referência histórica. A baseline normativa de O-2 deverá ser
reexecutada com `source_commit` igual ao HEAD atual antes de escolher qualquer
otimização.

Não há evidência atual que autorize presumir culling, spatial index,
virtualização, GPU, instancing, paralelismo ou worker thread.

## 4. Escopo de investigação aprovado para avaliação

O contrato O-2 propõe medir, sem ainda implementar:

- sync inicial e sync estrutural;
- refresh incremental de transforms, seleção e gizmo;
- troca authoring/preview;
- visibilidade, isolamento, layers, groups e sockets;
- parallax, zoom, pan, fit e resize;
- resolução/decodificação de assets;
- fluxo real de seleção, arraste, gizmo, preview, undo/redo e cancelamento.

As cargas devem cobrir 64, 128, 256 e 512 objetos, assets compartilhados e
únicos, e as resoluções 1280x720, 1366x768 e 1920x1080. O contrato exige
timing, memória, determinismo, equivalência do frame, thread affinity,
privacidade, captura e revisão humana quando aplicável.

## 5. Resultado e próxima decisão

O estado atual foi auditado sem suposições de causa ou solução. O-2-0 foi
concluído na baseline vinculada ao HEAD correto e o contrato de abertura foi
aceito pelo proprietário com `P2D-05-O2 ACEITO — contrato de preview e
viewport` em 31/08/2026.

A implementação foi qualificada com os gates registrados na decisão de lote.
O aceite PRECOMMIT, o commit técnico `ffb97eb788d1acecc2d874dd84f9fb6f1e51c0ef`
e a requalificação pós-commit foram concluídos em 31/08/2026. O estado final é
`ACCEPTED / CLOSED` dentro da fronteira O-2.
