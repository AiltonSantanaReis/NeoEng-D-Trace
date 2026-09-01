# NeoEng-D-Trace — decisão formal de implementação P2D-05/O-2

**Etapa:** P2D-05/O-2 — cache seguro, atualização incremental e equivalência do frame
**Status:** `PRECOMMIT ACCEPTED — POST-COMMIT REQUALIFICATION PENDING`
**Data de abertura:** 30/08/2026 (UTC-03)
**Branch de trabalho:** `p2d-05-quality-hardening`
**HEAD de referência e rollback:** `15300a0d580a57110828d8511ae48a0f68326e3a`
**Contrato de abertura:** `docs/DECISAO_P2D_05_O2_PREVIEW_VIEWPORT_2026-08-30.md`
**Baseline O-2-0:** `docs/EVIDENCIA_P2D_05_O2_0_BASELINE_2026-08-30.md`
**Relatório O-2-0:** `artifacts/p2d05/o2-0-baseline-20260830-restarted.json`
**Integridade O-2-0:** `docs/INTEGRIDADE_P2D_05_O2_0_2026-08-30.md`
**Aceite do proprietário:** `P2D-05-O2 IMPLEMENTAÇÃO ACEITA — cache/incremental/frame` — recebido em 31/08/2026.
**Aceite PRECOMMIT:** `Continue com o plano` — recebido em 31/08/2026; autoriza staging, commit e requalificação pós-commit dentro da fronteira qualificada.
**Qualificação final:** concluída em 31/08/2026; PRECOMMIT aceito; requalificação pós-commit pendente.
**Benchmark final:** `artifacts/p2d05/o2-implementation-final-20260831.json` — PASS, 26/26 workloads, zero erros, determinismo em todos; SHA-256 `8250b3abf6f730696cbf314c3f56cb6bd16fa2a782b0cf8f3c4d82109931a731`.
**Captura visual pós-correção:** `artifacts/p2d05/o2-viewport-capture-after-acceptance-20260831-r3/manifest.json` — PASS, pixel-equivalente após sync sem mudança.
**Regressão final:** `1871 passed, 2 skipped, 1 warning`.

Este documento registra o lote controlado de implementação do O-2. O aceite
explícito foi recebido em 31/08/2026 e autorizou somente a fronteira descrita
aqui; a implementação e a qualificação foram concluídas com os gates
registrados acima. O aceite PRECOMMIT foi recebido para esta fronteira; o lote
entra agora em staging, commit e requalificação pós-commit. Merge, push, tag,
release e avanço para O-3 seguem bloqueados até essa requalificação.

## 1. Decisão de engenharia

O-2 será tratado como uma otimização de infraestrutura do viewport e do preview,
não como uma mudança de produto visual ou funcional. A implementação poderá
conter somente melhorias comprovadas para os seguintes problemas medidos:

1. resolução, validação, hash, leitura e decodificação repetidos de assets em
   reconstruções completas;
2. atualização e pintura de todos os itens quando apenas uma parte do estado
   efetivamente mudou;
3. recomputação repetida de visibilidade, grupos, parallax, bounds e projeção
   no construtor determinístico de frames.

O desenho escolhido é conservador:

- o cache de assets só será aceito se tiver chave, validade e invalidação
  demonstráveis, mantendo todos os diagnósticos atuais;
- a atualização incremental só será aceita se a classificação de mudança for
  correta e o frame resultante for equivalente ao caminho completo;
- a otimização do frame só será aceita se reduzir recomputação sem alterar
  objeto, ordem, z-order, transformação, sockets, visibilidade, isolamento ou
  parallax;
- qualquer subparte que não possa ser concluída com equivalência e cobertura
  completas será marcada `NO_CHANGE` ou `BLOCKED`; não haverá aceitação parcial
  apresentada como conclusão do lote.

## 2. Evidência que fundamenta o lote

A baseline canônica O-2-0 foi reiniciada no HEAD correto, com o produtor
canônico normalizado e validado:

```text
HEAD/source_commit: 15300a0d580a57110828d8511ae48a0f68326e3a
Branch: p2d-05-quality-hardening
Workloads: 26/26
Erros de operação: 0
Frames determinísticos repetidos: 26/26
Amostras de timing: 50 por operação/workload
Warm-ups: 5
Observações de memória: 20 por workload
Relatório SHA-256: e88ab2b5db2b120424b800f03534354eba8d1a24639bf244778d14122e8e0d23
Produtor SHA-256: 9f6ff0eb1e2bea3b9d8ef9aba708da91f5ab2ab808df324fe229f34e8dedc091
```

Os perfis CPU sanitizados confirmaram:

- `full_sync` em `unique:512` é dominado por `resolve_scene_asset`,
  `Path.resolve`, `sha256_file`, leitura de arquivo e decodificação; o custo
  de pintura Qt isolada não é o principal fator nesse cenário;
- o refresh incremental em `shared:512` ainda atualiza transforms e repinta
  todos os objetos;
- o frame determinístico repete visibilidade efetiva, ancestralidade de grupo,
  parallax, bounds e projeções por objeto;
- zoom, pan e fit não demonstraram hot spot suficiente para implementação neste
  lote;
- `group_membership` permanece fora da implementação porque envolve o caminho
  transacional/histórico geral e não autoriza alteração de `SceneAuthoringSession`.

Os detalhes, p50/p95/p99, pior caso, memória e perfis locais estão nos documentos
e no relatório indicados no cabeçalho. Nenhum valor medido nesta decisão é um
orçamento normativo de performance; qualquer orçamento futuro exigirá decisão
própria e aceite explícito.

## 3. Fronteira exata de implementação

### 3.1 Arquivos de produto permitidos

Somente os arquivos a seguir poderão receber alterações de produto neste lote:

- `src/ui/scene_authoring_viewport.py`, para cache/reuso seguro de asset,
  classificação de alterações e atualização incremental do viewport;
- `src/core/scene_authoring_preview.py`, somente para redução de recomputação
  do frame determinístico confirmada pelo profiling;
- `src/ui/scenario_editor_window.py`, somente se uma integração indispensável
  do viewport for provada, sem modificar menu, QAction, atalhos, layout ou
  geometria.

Se a solução exigir qualquer outro arquivo de produto, a execução será parada e
será aberta uma nova decisão formal antes da alteração.

### 3.2 Arquivos de teste, ferramenta e evidência permitidos

Podem ser criados ou ajustados, dentro do mesmo lote:

- `tests/test_p2d_05_o2_preview.py` e testes focais diretamente relacionados;
- `scripts/benchmark_p2d_05_o2_preview.py` e ferramentas de medição necessárias,
  sem caminhos pessoais ou credenciais em saída versionável;
- documentos sob `docs/` e relatórios sanitizados sob `artifacts/p2d05/`.

Perfis brutos que contenham caminhos locais permanecem locais e não podem ser
staged, commitados ou incluídos em seal.

### 3.3 Fora da fronteira

Não está autorizado neste lote:

- alterar `SceneAuthoringSession`, histórico O-1, snapshots, gestos ou
  undo/redo;
- alterar schema, persistência, recovery, formatos, hashes canônicos,
  coordenadas ou exportadores;
- alterar `scene_asset_library.py` ou o contrato público de diagnóstico sem uma
  decisão adicional específica;
- alterar QSS, layout, dimensões, widget tree, QAction, atalhos, aparência ou
  comportamento de usuário;
- alterar engines, adapters, Godot, Unity, tiles, colisão, NavMesh,
  entidades/prefabs, iluminação, partículas, VFX, pós-processamento ou shaders;
- implementar culling, spatial index, virtualização, GPU, worker thread,
  paralelismo, instancing ou batching apenas por expectativa;
- otimizar zoom, pan, fit, resize ou group membership sem profiling específico
  e inclusão formal na fronteira;
- limpar untracked, alterar `.gitignore`, reescrever baselines ou publicar
  remotamente.

## 4. Contrato A — cache e invalidação de assets

### 4.1 Objetivo

Reduzir a repetição de resolução, hash, leitura e decodificação quando o mesmo
asset ainda é válido, sem ocultar alteração, remoção, path inválido, path fora
da raiz do projeto, hash divergente ou diagnóstico existente.

### 4.2 Requisitos obrigatórios

Uma implementação de cache somente será válida se demonstrar, por teste e
evidência:

1. a validação de contenção do caminho e a identidade/proveniência do asset
   continuam sendo verificadas;
2. o cache não transforma um asset ausente em asset disponível;
3. o cache não reapresenta um pixmap ou diagnóstico antigo depois de uma
   alteração do arquivo no mesmo caminho;
4. mudança de hash, tamanho, timestamp/identidade observável ou estado do
   arquivo invalida a entrada de forma determinística, conforme o mecanismo
   efetivamente adotado;
5. remoção, substituição, renomeação, path inválido e asset fora da raiz
   produzem os mesmos diagnósticos sem fallback silencioso;
6. assets compartilhados podem reutilizar resultado somente quando a chave
   representa a mesma revisão validada;
7. assets únicos não provocam crescimento não limitado durante a sessão;
8. encerramento e descarte do cache são seguros e não deixam referências Qt
   inválidas;
9. a ordem e o conteúdo observável dos objetos permanecem iguais;
10. o caminho de fallback de erro permanece seguro e testado.

O mecanismo não será considerado seguro se confiar somente em um caminho, no
ID do objeto ou em uma suposição de que o arquivo externo não mudou. Se a
garantia necessária não puder ser obtida dentro da fronteira permitida, o
resultado correto será `NO_CHANGE — cache não implementado`, preservando o
diagnóstico existente.

### 4.3 Evidência específica

Deverá incluir, no mínimo:

- cache miss e hit de asset compartilhado;
- assets únicos com revisão independente;
- arquivo removido após uma leitura válida;
- arquivo modificado mantendo o mesmo caminho;
- hash divergente e arquivo ilegível;
- path inválido ou fora da raiz;
- reabertura/reload e descarte do viewport;
- contagem de entradas e memória antes/depois de uma série de refreshes;
- comparação do diagnóstico e do frame com o caminho sem cache.

O relatório deve distinguir claramente `hit`, `miss`, `invalidated` e
`diagnostic`; não pode reportar somente uma redução de tempo.

## 5. Contrato B — atualização incremental do viewport

### 5.1 Objetivo

Atualizar somente o que foi efetivamente afetado por uma mudança, evitando
reconstrução ou repintura global quando isso não for necessário, sem alterar a
semântica da operação.

### 5.2 Classificações mínimas

O caminho deverá distinguir, com estado observável e testes:

- mudança estrutural: criação/remoção, asset, ordem de camada, visibilidade,
  grupo, membership, isolamento ou mudança que altere a composição dos itens;
- mudança de transformação: posição, escala, rotação, flip ou parallax de
  objeto já existente;
- mudança de seleção/gizmo: somente seleção, primary, handles e estilo
  correspondente;
- mudança de navegação: zoom, pan, fit ou resize;
- mudança de preview: entrada/saída do modo read-only e atualização de frame.

Essa classificação não poderá ser deduzida por uma comparação incompleta. Se
um caso não puder ser identificado com segurança, o comportamento permitido é
usar a reconstrução completa, com equivalência preservada.

### 5.3 Requisitos obrigatórios

1. a reconstrução completa continuará disponível como caminho de fallback;
2. nenhum item fora do conjunto afetado poderá sofrer mudança observável;
3. itens afetados manterão ID, ordem, z-order, posição, escala, rotação, flip,
   asset, sockets, seleção e estilo equivalentes;
4. qualquer mudança de visibilidade, grupo, camada, ordem ou asset deverá
   invalidar o conjunto mínimo correto e nunca reutilizar itens obsoletos;
5. o refresh incremental não poderá ignorar uma atualização de diagnóstico;
6. o caminho incremental não poderá alterar o documento autorado;
7. seleção, drag, gizmo, cancelamento e undo/redo continuarão usando o mesmo
   contrato O-1;
8. quando houver dúvida entre incremental e estrutural, o caminho seguro será o
   full sync, sem falha silenciosa;
9. as operações Qt continuarão na thread correta;
10. a otimização deverá ser mensurada contra o mesmo workload do O-2-0.

Não será aceito um contador de itens “atualizados” como única prova. A prova
deverá demonstrar o estado final e a equivalência do resultado.

## 6. Contrato C — equivalência do frame e do viewport

### 6.1 Equivalência determinística

Para a mesma entrada, o frame otimizado deverá ser byte a byte equivalente ao
frame determinístico anterior quando o formato permitir comparação binária.
Quando a representação contiver objetos não binários, deverá ser comparada por
assinatura canônica, incluindo no mínimo:

- IDs e ordem canônica dos objetos;
- camada, ordem visual e z-order;
- posição, escala, rotação, flip e parallax;
- asset resolvido, estado de validade e diagnóstico;
- visibilidade efetiva, grupo, isolamento e memberships observáveis;
- sockets e pontos projetados;
- seleção, primary, gizmo e estado read-only do preview;
- câmera, viewport, bounds e dimensões relevantes;
- ausência/presença de itens Qt esperados.

Qualquer diferença deve ser registrada, explicada e classificada antes de
qualquer aceite. Diferença desconhecida é falha, não tolerância.

### 6.2 Equivalência visual

O-2 tem `V=0` como intenção. Se a alteração de reutilização mudar pixels,
antialiasing, clipping, ordem de pintura, opacidade ou aparência, o lote não
será aceito automaticamente. Será necessário identificar a causa e abrir uma
decisão visual específica ou reverter a alteração.

Quando o caminho visual for exercitado, a evidência deve conter captura Qt
nativa Windows, auditoria visual e comparação contra a referência aprovada.
Estado vivo, cursor, DPI ou outra variação devem ser localizados e
documentados; não podem ser mascarados.

### 6.3 Equivalência de comportamento

O fluxo real deve continuar permitindo, no mínimo:

- abrir a composição e visualizar objetos;
- selecionar um objeto e uma seleção múltipla;
- mover por mouse/gizmo;
- alternar preview read-only;
- usar visibilidade, grupos, camadas e isolamento;
- usar sockets/parallax quando presentes;
- desfazer, refazer e cancelar conforme O-1;
- aplicar zoom, pan, fit e resize sem mudança semântica.

Preview não poderá alterar o documento, os bytes persistidos ou as exportações.

## 7. Invariantes de governança

Durante e depois do lote:

- `G=0`: sem mudança de geometria, dimensões ou coordenadas autoradas;
- `V=0` como intenção: sem redesign ou mudança visual não autorizada;
- `B=0`: sem alteração de comportamento, atalhos, ações ou semântica;
- schema, persistência, recovery, bytes canônicos, hashes e exportadores
  permanecem iguais;
- C3 e todas as baselines aprovadas permanecem imutáveis;
- O-1 e `SceneAuthoringSession` permanecem intocados;
- nenhum caminho pessoal, segredo, credencial ou dado sensível entra em
  código, relatório versionável, staged content, commit ou seal;
- o worktree será verificado por fronteira tracked, sem interpretar untracked
  legítimo como falha;
- nenhum push, tag, merge ou release ocorrerá como parte desta decisão sem
  autorização explícita separada.

## 8. Testes obrigatórios antes do PRECOMMIT

O lote não poderá avançar ao PRECOMMIT se qualquer grupo aplicável estiver
ausente:

### 8.1 Testes de correção

- testes focais do cache, invalidação e diagnósticos;
- testes focais das classificações estrutural/incremental/navegação/preview;
- equivalência full-sync versus incremental para transformação, seleção,
  gizmo, visibilidade, grupo, isolamento, layer, sockets, parallax e assets;
- frame determinístico repetível e equivalente;
- preview read-only e ausência de mutação do documento;
- fluxo de usuário com abertura, seleção, drag, preview, cancelamento,
  undo/redo, grupos, camadas e isolamento;
- casos de asset ausente, inválido, alterado, removido e fora da raiz;
- encerramento seguro, thread affinity e fallback completo.

### 8.2 Testes de não regressão

- suíte completa no Python 3.11 da `.venv`;
- testes focais e de integração relevantes;
- `py_compile`, diff-check e verificações estáticas aplicáveis;
- auditoria de privacidade do conteúdo staged;
- verificação de que apenas arquivos dentro da fronteira foram tocados;
- requalificação do comportamento e dos bytes de exportação;
- comparação pós-implementação usando o mesmo protocolo O-2-0.

### 8.3 Medição de performance

O benchmark pós-implementação deve repetir os 26 workloads da baseline:

- 64, 128, 256 e 512 objetos;
- assets compartilhados e únicos;
- 1280x720, 1366x768 e 1920x1080;
- 50 amostras, 5 warm-ups e 20 observações de memória separadas;
- p50, p95, p99, pior caso, erros, determinismo, Working Set, Private Bytes e
  memória Python;
- source commit explicitamente registrado.

O resultado deve apresentar antes/depois por operação e por workload. Melhora
em um caso não compensa regressão não explicada em outro caso crítico.

## 9. Evidências e critérios de PRECOMMIT

Antes de pedir aceite de PRECOMMIT, deverão existir:

1. diff completo e revisão da fronteira;
2. testes focais e suíte completa;
3. benchmark pós-implementação comparável ao O-2-0;
4. relatório de equivalência do frame e dos itens Qt;
5. relatório de cache hit/miss/invalidação, se cache for implementado;
6. relatório de classificação incremental e fallback;
7. relatório de memória e thread affinity;
8. captura/auditoria/comparação Windows quando aplicável;
9. inspeção de privacidade e staged boundary;
10. rollback reproduzível para `15300a0d580a57110828d8511ae48a0f68326e3a`;
11. decisão explícita para cada alvo: `ACCEPT`, `NO_CHANGE` ou `BLOCKED`.

Critérios mínimos:

```text
SEMANTIC/CONTRACT CHECKS = 0 falhas
FRAME EQUIVALENCE = PASS
VIEWPORT/BEHAVIOR EQUIVALENCE = PASS
ASSET DIAGNOSTICS = PASS
CACHE INVALIDATION = PASS ou NO_CHANGE formal
INCREMENTAL CLASSIFICATION = PASS ou NO_CHANGE formal
FULL SUITE = PASS, sem falha desconhecida
BENCHMARK = completo, determinístico e comparável
PRIVACY/STAGED BOUNDARY = PASS
DIFF-CHECK = PASS
ROLLBACK = reproduzível
```

Não haverá `PRECOMMIT ACCEPT` enquanto existir diferença não classificada,
teste faltante, diagnóstico silenciosamente alterado, cache sem invalidação,
regressão de comportamento ou arquivo fora da fronteira.

## 10. Sequência obrigatória após o aceite

1. registrar o aceite deste contrato;
2. criar fixtures/assinaturas de equivalência antes da alteração de produto;
3. implementar somente o primeiro subalvo confirmado, mantendo fallback;
4. executar testes focais e profiling do subalvo;
5. continuar para o subalvo seguinte somente se o anterior estiver completo e
   comprovado dentro do mesmo lote;
6. executar benchmark, memória, equivalência e fluxo real;
7. revisar a fronteira final e solicitar `PRECOMMIT ACCEPT`;
8. somente após o aceite PRECOMMIT realizar staging explícito e commit;
9. requalificar pós-commit no commit final;
10. encerrar O-2 com evidência ou registrar `NO_CHANGE/BLOCKED` fundamentado.

O-3 e todas as linhas independentes permanecem bloqueados até o fechamento
formal de O-2. A implementação não poderá ser declarada concluída apenas por
redução de tempo ou por teste sintético isolado.

## 11. Aceite solicitado

Aceite explícito registrado pelo proprietário em 31/08/2026:


`P2D-05-O2 IMPLEMENTAÇÃO ACEITA — cache/incremental/frame`

Esse aceite autoriza a implementação e qualificação do lote descrito neste
documento. Não autoriza automaticamente PRECOMMIT, commit, build, merge, push,
tag, release, alteração remota ou qualquer escopo fora da fronteira.
