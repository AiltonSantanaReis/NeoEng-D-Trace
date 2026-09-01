# NeoEng-D-Trace — decisão formal P2D-05/O-2

**Etapa:** O-2 — preview e viewport da composição 2D
**Status:** `ACCEPTED / CLOSED`
**Data de abertura:** 30/08/2026 (UTC-03)
**Branch de auditoria:** `p2d-05-quality-hardening`
**HEAD auditado:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Rollback de O-2:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Aceite PRECOMMIT:** `Continue com o plano` — recebido em 31/08/2026.
**Commit técnico:** `ffb97eb788d1acecc2d874dd84f9fb6f1e51c0ef`.
**Baseline de produção anterior:** `f55b07b85ef2cf65160f2c10ffac5e63b45732ac`
**Contrato pai:** `docs/DECISAO_P2D_05_PERFORMANCE_LIMITES_FORMATOS_ERROS_2026-08-30.md`
**Contrato de otimização:** `docs/DECISAO_P2D_05_OTIMIZACAO_PERFORMANCE_2026-08-30.md`
**Pré-requisito concluído:** O-1 commit `15300a0d580a57110828d8511ae48a0f68326e3a`

Este documento abre somente a decisão e o contrato de O-2. Nenhuma alteração
de código está autorizada antes do aceite explícito deste contrato. A abertura
não fecha O-1, não fecha P2D-05, não autoriza O-3, não altera C3/G/V/B, não
autoriza build, commit, merge, push, tag, release ou alteração remota.

**Aceite do proprietário:** `P2D-05-O2 ACEITO — contrato de preview e viewport` — recebido em 31/08/2026.

## 1. Finalidade

O-2 investigará, com medição reproduzível, o custo do preview e da atualização
do viewport profissional de composição 2D. O objetivo é corrigir somente um
hot spot confirmado por profiling, mantendo a mesma apresentação, a mesma
semântica de edição e os mesmos resultados observáveis.

Uma decisão `NO_CHANGE` é resultado válido quando a investigação não encontrar
um ganho seguro e material. Não será criada uma otimização cosmética, um
culling presumido ou uma arquitetura genérica de engine sem evidência.

## 2. Auditoria somente de leitura do estado atual

### 2.1 Caminho Qt do viewport

`src/ui/scene_authoring_viewport.py` contém o `SceneAuthoringViewport`, um
`QGraphicsView` com objetos, sockets e gizmo como itens da cena. O caminho
`sync()` atualmente:

1. limpa o `QGraphicsScene`;
2. descarta os mapas de itens de objetos, sockets e gizmo;
3. percorre os objetos na ordem canônica e filtra visibilidade efetiva,
   isolamento e camadas;
4. resolve e decodifica assets, usando um cache de pixmaps limitado àquela
   chamada;
5. cria novos `QGraphicsItem` para objetos e sockets;
6. recalcula transformações, seleção, gizmo, retângulo de navegação e estado
   de diagnóstico.

`set_geometry()` e a mudança do modo de preview chamam `sync()`. O callback
`_on_session_change()` evita a reconstrução completa quando os conjuntos de
objetos/sockets visíveis, o estado dos assets e a ordem das camadas permanecem
iguais; nesse caso chama `_refresh_after_model_change()`, que atualiza
transformações, gizmo e pintura. Quando uma dessas condições estruturais muda,
volta ao `sync()` completo.

Esse comportamento é uma observação do código atual, não uma decisão de que
deve ser substituído. A necessidade e a segurança de qualquer reuso de item,
cache, índice espacial ou atualização incremental deverão ser demonstradas.

### 2.2 Preview determinístico e histórico

`src/core/scene_authoring_preview.py` possui um construtor determinístico de
frames projetados para objetos e sockets. Ele não deve ser confundido com a
reconstrução de itens Qt do viewport.

O-1 preservou deliberadamente o caminho de preview de gestos: cada evento
restaura a base do gesto e reaplica a transformação. O experimento incremental
rejeitado está preservado em `artifacts/p2d05/o1-gesture-ab-20260830.json`.
O-2 não reabre ou altera O-1 por inferência. Qualquer mudança em
`SceneAuthoringSession` exigirá uma decisão específica e uma nova fronteira.

### 2.3 Evidência de performance disponível

`artifacts/p2d05/calibration-o1-final-20260830.json` mediu o caminho
`preview_sync` com 50 amostras, 5 warm-ups e 8 workloads. Os p95 registrados
para 512 objetos foram aproximadamente 76,48 ms com asset compartilhado e
949,59 ms com assets únicos; os valores completos permanecem no JSON.

Esse relatório foi produzido no worktree O-1 quando o HEAD Git ainda era
`fc59ff571e4e4d99ddd40a8ec318d50b8edd77f3` e o conteúdo medido foi posteriormente consolidado no commit
`15300a0d580a57110828d8511ae48a0f68326e3a`. Portanto, ele é evidência histórica do estado que foi
commitado, mas não será tratado como uma medição O-2 vinculada ao novo HEAD.
O primeiro passo de execução de O-2 deverá produzir uma nova baseline O-2-0
com `source_commit=15300a0d580a57110828d8511ae48a0f68326e3a`.

Não existe, nesta abertura, evidência suficiente para afirmar que culling,
spatial index, virtualização, GPU, instancing ou paralelismo sejam necessários.

## 3. Objetivo técnico autorizado

Investigar e, somente se confirmado, reduzir custo de:

- reconstrução completa do viewport em mudanças estruturais;
- atualização de transforms, seleção e gizmo em mudanças incrementais;
- resolução/decodificação repetida de assets durante sincronizações;
- cálculo de bounds, retângulo de cena, projeção de parallax e navegação;
- troca entre authoring e preview, resize, fit, zoom e pan;
- atualizações de visibilidade, isolamento, camadas, grupos e sockets.

O objetivo é custo de atualização e responsividade do viewport. Não é alterar o
design visual, criar novos recursos de edição ou mudar o contrato de engine.

## 4. Fronteira permitida

### 4.1 Implementação potencial

Somente após o aceite, profiling e classificação do hot spot, poderão ser
alterados, se necessários:

- `src/ui/scene_authoring_viewport.py`, para o caminho de sincronização e
  atualização do viewport;
- `src/core/scene_authoring_preview.py`, somente se o profiling demonstrar
  custo nesse construtor e os frames permanecerem equivalentes;
- `src/ui/scenario_editor_window.py`, somente para a integração indispensável
  do viewport e sem alteração de QAction, atalhos, layout ou geometria.

Testes, benchmarks e evidências poderão ser adicionados em:

- `tests/test_p2d_05_o2_preview.py`;
- `scripts/benchmark_p2d_05_o2_preview.py`;
- novos documentos sob `docs/` e artefatos sanitizados sob `artifacts/p2d05/`.

### 4.2 Fora da fronteira

Este contrato não autoriza:

- alteração de `SceneAuthoringSession`, do histórico O-1 ou do caminho de
  preview de gestos;
- schema, persistência, recovery, exportação, formatos, hashes ou coordenadas;
- engines Godot/Unity, adapters, tiles, colisão, NavMesh, entidades/prefabs,
  iluminação, partículas, VFX, pós-processamento ou shaders;
- mudança de QSS, layout, dimensões, widget tree, QAction, atalhos ou aparência
  intencional;
- culling, spatial index, virtualização, GPU, worker thread ou paralelismo sem
  profiling específico e decisão técnica documentada dentro de O-2;
- limpeza de untracked, alteração de `.gitignore` ou publicação remota.

Qualquer arquivo, símbolo, formato, comportamento ou eixo fora desta lista
interrompe O-2 e exige nova decisão formal.

## 5. Invariantes obrigatórios

Toda implementação O-2 deverá preservar:

1. `G=0`: nenhuma alteração geométrica, de dimensões, escala de UI ou
   coordenadas autoradas;
2. `V=0` como intenção de produto: nenhuma mudança de design ou aparência; uma
   diferença raster deverá ser explicada e aprovada antes de ser aceita;
3. `B=0`: seleção, transformação, grupos, camadas, isolamento, undo/redo,
   atalhos e transições permanecem iguais;
4. schema V1/V2, bytes canônicos, SHA-256, formatos e exportações permanecem
   iguais;
5. o preview continua somente apresentação e não altera o documento autorado;
6. objetos, ordem, z-order, transforms, flips, seleção, primary, visibilidade,
   isolamento, parallax, zoom, sockets e diagnósticos permanecem equivalentes;
7. authoring e preview continuam distinguíveis, e preview continua read-only;
8. toda mutação de `QGraphicsScene`, `QGraphicsItem`, `QPixmap` e controles Qt
   permanece na thread Qt apropriada;
9. assets ausentes, inválidos ou alterados continuam gerando diagnóstico
   seguro, sem fallback silencioso ou caminho pessoal;
10. nenhum cache poderá retornar resultado de documento, asset, geometria ou
    revisão obsoleta;
11. memória nativa e Python devem ser observadas, sem crescimento não
    explicado;
12. rollback não remove evidências, untracked, histórico ou baselines.

## 6. Metodologia de O-2-0

Antes de qualquer código, a baseline deverá ser recalibrada no commit
`15300a0d580a57110828d8511ae48a0f68326e3a`, usando o Python 3.11 da `.venv` e o mesmo ambiente Qt do O-1:

- workloads de 64, 128, 256 e 512 objetos;
- assets compartilhados e únicos;
- camadas, grupos, memberships, sockets e proporções de visibilidade
  representativas;
- 50 amostras medidas, 5 warm-ups e memória em etapa separada com 20
  iterações;
- timing com `time.perf_counter_ns`, sem `tracemalloc` no timing;
- dimensões 1280x720, 1366x768 e 1920x1080; DPI adicional somente quando
  necessário para explicar o custo de apresentação;
- `QT_QPA_PLATFORM=offscreen` para medição controlada e Windows nativo para o
  fluxo visual real;
- p50, p95, p99, pior caso, erros, Working Set, Private Bytes e memória Python;
- GPU somente se um profiler confirmar custo GPU relevante.

As operações serão medidas separadamente:

1. criação/sync inicial;
2. alteração estrutural: add/remove, asset, camada, ordem, visibilidade,
   grupo, membership e isolamento;
3. alteração incremental: transform, seleção e gizmo;
4. troca authoring/preview;
5. zoom, pan, fit e resize;
6. sockets e parallax;
7. fluxo real de seleção, arraste, preview, undo/redo e cancelamento, sem
   alterar a semântica do O-1.

Nenhum limite numérico será transformado em meta normativa por inferência. O
resultado poderá ser otimização aceita, `NO_CHANGE` ou bloqueio por falta de
equivalência.

## 7. Testes e evidências obrigatórios

O-2 deverá incluir, conforme aplicável ao finding confirmado:

- testes de classificação entre atualização estrutural e incremental;
- equivalência do frame determinístico antes/depois;
- equivalência de itens, ordem, z-order, posição, escala, rotação, flip,
  seleção, sockets, visibilidade e isolamento;
- testes de assets compartilhados, únicos, ausentes e alterados;
- testes de preview read-only, toggle, zoom, pan, fit e resize;
- testes de navegação nas três resoluções-alvo;
- testes de memória, cache hit/miss, invalidação e revisão obsoleta quando
  houver cache;
- teste de thread affinity e encerramento seguro quando houver worker;
- fluxo Qt real de usuário com seleção, arraste, gizmo, grupos, camadas,
  isolamento e preview;
- captura Windows, auditoria visual, comparação e revisão humana quando o
  caminho visual for alterado;
- full suite, testes focais, qualidade estática, privacidade e diff-check;
- benchmark pós-implementação com o mesmo protocolo e source commit correto;
- rollback reproduzível para `15300a0d580a57110828d8511ae48a0f68326e3a`.

Os perfis brutos que contenham caminhos locais permanecem somente na evidência
local. Somente relatórios sanitizados, sem caminhos pessoais, segredos ou
credenciais, poderão ser versionados ou empacotados.

## 8. Sequência obrigatória

1. aceitar este contrato formalmente;
2. executar auditoria O-2-0 e baseline vinculada a `15300a0d580a57110828d8511ae48a0f68326e3a`;
3. classificar cada hot spot como corrigir, `NO_CHANGE` ou bloqueado;
4. propor e executar, se aceito, um único lote de implementação controlada;
5. executar testes, benchmark, captura e auditoria do lote;
6. revisar diff, fronteira e artefatos em PRECOMMIT;
7. solicitar aceite PRECOMMIT específico;
8. somente então realizar commit e requalificação pós-commit;
9. fechar O-2 ou registrar bloqueio fundamentado.

O-3 permanece bloqueado até o encerramento formal de O-2 e uma decisão própria.

## 9. Critérios de aceite de O-2

O-2 só poderá ser marcado `ACCEPTED / CLOSED` quando todos os itens forem
comprovados:

- baseline O-2-0 vinculada ao HEAD correto e metodologia reproduzível;
- hot spots confirmados ou decisão `NO_CHANGE` para cada alvo investigado;
- cada correção incluída tiver cobertura completa do caminho afetado;
- equivalência funcional, visual, geométrica e de bytes comprovada;
- nenhuma alteração fora da fronteira;
- memória, thread affinity, cache e invalidação explicados;
- full suite, estática, privacidade, captura e revisão humana passarem quando
  aplicáveis;
- rollback reproduzível;
- build e fluxo real do usuário concluídos quando houver alteração de viewport;
- commit, pós-commit e evidência final vinculados ao mesmo conteúdo;
- nenhum resultado for apresentado como capacidade não comprovada.

Um único item ausente mantém O-2 aberto e impede avançar para O-3.

## 10. Aceite solicitado

Aceite explícito registrado pelo proprietário em 31/08/2026:

`P2D-05-O2 ACEITO — contrato de preview e viewport`

Esse aceite autorizou a auditoria O-2-0 e a implementação controlada dentro
desta fronteira. A baseline foi concluída e registrada em
`docs/EVIDENCIA_P2D_05_O2_0_BASELINE_2026-08-30.md`. Ele não aceita build,
commit, fechamento ou publicação.
