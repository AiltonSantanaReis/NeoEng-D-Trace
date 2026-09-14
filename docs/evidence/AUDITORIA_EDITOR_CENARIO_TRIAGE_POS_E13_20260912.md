# Auditoria de engenharia — Editor de Cenário e parallax pós-E13

**ID:** `AUD-POS-E13-SCENARIO-EDITOR-TRIAGE-20260912`
**Data:** 2026-09-12
**Estado:** `AUDIT_COMPLETE / POST_E13_IN_PROGRESS / HUMAN_REVIEW_PENDING`
**Commit auditado:** `a26bf3d960e800c16115007a458f3b562e8b6e91`
**Checkout de auditoria:** `build/_merge-main-20260912`
**Base:** `origin/main` (árvore idêntica no momento da auditoria)

Este documento registra a investigação estrutural, visual e de compatibilidade
solicitada para continuar o projeto sem reabrir o E13, sem remover o Editor de
Cenário profissional e sem promover evidência parcial a aceite de produto.

## 1. Governança e fronteira protegida

Antes desta etapa foram lidos integralmente:

- `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`;
- `docs/CONTROLE_CONTINUIDADE_ATUAL.md` e o registro JSON correspondente;
- `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`;
- `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`;
- `docs/evidence/AUDITORIA_PRONTIDAO_REVISAO_HUMANA_POS_E13_20260912.md`.

Aplicações da governança nesta auditoria:

1. E13 permanece fechado/congelado; o lote ativo continua sendo pós-E13.
2. O viewport profissional, a persistência e os contratos de cena existentes
   são fronteiras protegidas.
3. Falhas históricas, capturas antigas e limitações de engine permanecem
   visíveis; não foram convertidas em `PASS` por interpretação.
4. Nenhum asset, captura, build, branch ou documento histórico foi removido.
5. A limpeza executada limitou-se a metadados órfãos de worktree do Git; os
   arquivos e diretórios que continham artefatos não foram apagados.

## 2. Resultado executivo

O produto tem uma base funcional real e mais madura do que a aparência inicial
sugere: o fluxo nativo de câmera, rotação, timeline, salvamento e reabertura
foi executado com o binário real e possui evidência hashada. O problema
principal não é a ausência de um editor profissional completo, mas a mistura
de superfícies com papéis diferentes e uma linguagem visual de viewport ainda
técnica/prototípica.

O diagnóstico correto é:

- **não remover** `ScenarioEditorWindow` nem `SceneAuthoringViewport`;
- **não tratar o fluxo independente como editor profissional equivalente**;
- **não excluir imediatamente** `CanvasView` ou `ScenarioPanel`, porque ainda
  existem dependências de compatibilidade e preview;
- consolidar uma única entrada visível chamada **Editor de Cenário**;
- deixar o modo independente explícito como **Cena 2D independente / protótipo
  de formas**, caso seja mantido;
- evoluir o gizmo, câmera, guias de parallax, catálogo e performance em lotes
  pequenos, com teste e captura nativa por lote.

Portanto, a duplicidade é principalmente de **arquitetura percebida e
nomenclatura**, não de três editores completos concorrentes.

## 3. Evidências reais usadas

As conclusões visuais abaixo não foram derivadas somente de leitura de código.
Foram usadas capturas nativas do executável Windows, produzidas por interação
Win32 real e `PrintWindow`/`CopyFromScreen`, conforme o registro de evidência.

| Evidência | Resultado observado |
|---|---|
| `build/e01-independent-scene-20260908/artifacts/post-e13-native-flow-20260911-camera-timeline/camera-rotate-handle-real-v2-24053066.png` | câmera visível, deslocável e rotacionável; handle funcional, porém visualmente simples e dominante |
| `.../timeline-scrub-clip-real-24053066.png` | timeline aceita arraste contínuo do playhead e mostra o clip |
| `.../reload-camera-inspector-persisted-real-24053066.png` | câmera reaberta com valores persistidos (`X 90`, `Y 45`, `Zoom 1`, rotação aproximada `32,5844`) |
| `build/e01-independent-scene-20260908/artifacts/post-e13-final-build-recovery-v4-20260912/artifacts/post-e13-final-native-composition-recovery-v4-20260912/composition-01-scenario-editor.png` | janela profissional real, molduras, hierarquia, viewport, inspector e guias de profundidade |
| `build/e01-independent-scene-20260908/artifacts/post-e13-binary-final10-20260910/asset-pack/06-asset-pack-dialog.png` | catálogo real com seis assets, miniaturas, preview, descrição e estado de licença/proveniência |

Hashes registrados para as três capturas de câmera/timeline e para o catálogo:

- `camera-rotate-handle-real-v2-24053066.png` —
  `E379EFD65A6A64BC25B31274B88BD8BCCA8214B2EDA3072B056D4AF699E66222`;
- `timeline-scrub-clip-real-24053066.png` —
  `AFF2AA8A1936CC2CAE4AA8A5FA4227CA98F751730E65E6ED4DBD7BDE39D60D5E`;
- `reload-camera-inspector-persisted-real-24053066.png` —
  `018BDBBD1DA6F613C117A10040A687205E415AEDA75275B3AA7EEFABADAEA329`;
- `06-asset-pack-dialog.png` —
  `4C6AF75116A4E4478C90BB2C882C6BD10F19A69A7918DC4D385ACBA0E9E9B0FA`.

Os hashes acima foram recalculados no filesystem auditado; a evidência
autoritativa do lote permanece no manifesto
`EVD_POS_E13_PROFESSIONAL_AUTHORING_NATIVE_20260911.md` e nos manifestos
hashados correspondentes. O catálogo mantém o hash histórico explicitamente
registrado na auditoria de fluxo pós-E13.

**Limitação do método:** a automação CUA não ficou disponível nesta sessão por
falha de infraestrutura ao inicializar os assets do kernel. Não foram
simulados cliques nem foi declarado novo PASS de CUA. As conclusões de runtime
usam somente as capturas nativas reais já produzidas pelo fallback documentado.

## 4. Topologia real dos “três editores”

### 4.1 Cena 2D independente

`src/ui/independent_scene_actions.py` instala a ação **Novo Cenário
Independente...** (`Ctrl+Alt+N`) e abre `IndependentSceneWindow`.

`src/ui/independent_scene_window.py` documenta uma superfície sem dependência
de projeto. Ela trabalha com resolução, câmera simples, retângulos, elipses,
polígonos e edição de pontos, usando o formato de cena independente. É útil
para prototipar formas ou iniciar uma cena 2D mínima, mas não é o estúdio
profissional de parallax: não é a mesma sessão V2, não é a mesma hierarquia de
molduras e não representa o caminho completo de assets, tilemap, efeitos,
entidades e exportação do Editor de Cenário.

**Classificação:** capacidade válida, porém mal posicionada se aparecer para o
usuário como sinônimo de cenário profissional.

**Recomendação:** manter por compatibilidade e utilidade, mas renomear e
reposicionar para `Cena 2D independente / protótipo de formas`, com descrição
explícita e ação para converter/exportar o resultado para o Editor de Cenário.
Não apagar nesta etapa.

### 4.2 Janela contêiner do Editor de Cenário

`src/ui/scenario_editor_window.py` implementa `ScenarioEditorWindow`. O botão
superior **Cenário** e a ação **Open Scenario Editor** chegam nesta janela.
Ela monta docks de composição, hierarquia, biblioteca, timeline, inspector,
tileset/tilemap, colisão, navegação, entidades e ferramentas auxiliares.

Na inicialização ela ainda cria `self.canvas` e o alias
`self.legacy_canvas`, inserindo o `CanvasView` em `professional_pages` como
superfície de compatibilidade/preview. Isto explica parte da percepção de que
há outro editor: a janela contém uma página legada e uma página profissional,
mas não são duas implementações equivalentes que devam ser expostas como
opções paralelas.

**Classificação:** contêiner canônico. Deve permanecer intacto nesta etapa.

### 4.3 “Novo Cenário” dentro da janela profissional

O `open_action` da mesma janela tem o texto **Novo Cenário** e chama
`_new_professional`. Esse método cria uma cena vazia temporária, gera o
documento profissional V2 e seleciona o `SceneAuthoringViewport`. Portanto o
terceiro caminho percebido é um **modo de inicialização do mesmo editor
canônico**, não um terceiro editor.

O fato de o fluxo vazio usar um projeto temporário é positivo para o requisito
de autoria do zero, mas precisa ser explicado ao usuário e persistido por um
fluxo “Salvar projeto como” sem criar dependência artificial de imagem.

### 4.4 O que não é um editor independente

`ScenarioPanel` é um painel de propriedades/estado criado dentro da janela
profissional. `CanvasView` é um canvas legado usado no preview e na integração
com o editor principal. Nenhum dos dois deve ser excluído por limpeza nominal.

## 5. Achados de engenharia e UX

| ID | Severidade | Achado | Tipo | Estado |
|---|---|---|---|---|
| `UX-GIZMO-01` | Alta | `SceneTransformGizmo` usa geometria fixa, poucos modos e cores básicas; não há espaço local/mundo, pivot, caixa de seleção multiobjeto, rótulos de eixo ou compensação de tamanho em tela. | lacuna de produto/UX | `OPEN` |
| `UX-CAMERA-01` | Média | A `SceneCameraGuide` já permite mover e rotacionar e a persistência foi comprovada, mas a moldura/handle e o rótulo ocupam muito peso visual e não há uma lista de shots, presets, safe areas e preview “camera view” suficientemente descobríveis. | refinamento de produto | `OPEN` |
| `UX-PARALLAX-01` | Média | Os limites de parallax existem e são desenhados fora do export, mas as guias diagonais e rótulos Z00/Z01/Z02 podem dominar a composição. Falta modo de visualização graduado: bounds, safe area, debug e overview. | refinamento de produto | `OPEN` |
| `UX-ENTRY-01` | Alta | “Cenário independente”, “Cenário” e “Novo Cenário” parecem editores concorrentes. A mesma janela alterna página vazia, canvas legado, viewport profissional e viewport híbrido. | IA/nomenclatura | `OPEN` |
| `UX-ASSET-01` | Média | A biblioteca de projeto mostra ícone de 40 px e dados; o catálogo de pacotes tem grade de 144 px e preview. Existe base profissional, mas falta catálogo unificado por tipo, tags visuais, filtros de modo 2D/2.5D/3D, uso na cena e ação de arrastar direta com feedback. | usabilidade | `OPEN` |
| `PERF-ASSET-01` | Média | `SceneAssetLibrary.refresh()` inspeciona e decodifica cada asset de forma sequencial; o catálogo de pacotes usa lotes por `QTimer`, mas a biblioteca de projeto ainda pode bloquear ao crescer. | risco de desempenho | `OPEN — medir antes de corrigir` |
| `PERF-VIEW-01` | Média | O viewport usa `QGraphicsScene`/pintura nativa e atualiza guias, gizmos e transformações; não há nesta auditoria um baseline de FPS/tempo de frame por quantidade de objetos. | lacuna de observabilidade | `OPEN — não declarar falha sem métrica` |
| `LOC-PT-01` | Baixa/Média | As capturas atuais mostram PT-BR funcional em títulos, inspector e status. Ainda falta uma matriz nativa completa de menus de contexto, tooltips, erro, tilemap, partículas e exportação para garantir que não restem labels ingleses ou truncamentos. | localização | `OPEN` |
| `PARITY-01` | Alta | O preview do editor e os adaptadores de engine não podem ser tratados como equivalência automática. O runtime híbrido é explicitamente `VERTICAL_SLICE_ONLY`; alguns recursos são contratos/sidecars e precisam de validação por destino. | arquitetura/contrato | `OPEN controlado` |

Nenhum desses achados autoriza apagar o código existente. O gizmo atual é
funcional no escopo comprovado, mas visualmente imaturo; a câmera é funcional,
mas ainda não oferece uma experiência completa de direção de câmera; e o
desempenho percebido precisa de medição para separar regressão real de
expectativa visual.

## 6. Limites reais das engines e implicações para o produto

### Godot

- `Parallax2D` fornece `scroll_scale`, repetição, offset e limites; a
  velocidade relativa deve ser exportada como semântica de camada e não como
  textura pré-combinada.
- `Camera2D` registra uma câmera ativa por viewport, tem zoom, limites,
  margens, smoothing e rotação; posição do nó, posição alvo e posição efetiva
  da tela podem divergir quando smoothing/limites estão ativos.
- A iluminação 2D depende de recursos próprios: `CanvasModulate`,
  `PointLight2D`/`DirectionalLight2D`, receptores e `LightOccluder2D`. Sombras
  direcionais têm limitação documentada de comprimento infinito; isso não é
  defeito do nosso gizmo.
- `GPUParticles2D` é uma simulação GPU e não colide com `PhysicsBody2D`;
  o produto deve distinguir emissão visual, colisão de partículas e colisão
  física de cena.
- `TileMap` está depreciado na documentação estável em favor de
  `TileMapLayer`; atualizações são agrupadas ao fim do frame e há limites de
  coordenadas serializadas. O exportador deve declarar versão e capacidades.

### Unity

- A iluminação 2D profissional documentada é o sistema `Light 2D` do URP,
  com tipos, blend styles, sorting layers, sombras e compatibilidade de
  shaders. Um projeto Built-in/HDRP não deve ser vendido como equivalente sem
  adaptador específico.
- Tilemap é um sistema de assets e componentes; o pacote/editor pode precisar
  ser instalado no projeto de destino e o renderer/collider são componentes
  diferentes do dado de autoria.
- Timeline e Cinemachine são pacotes/versionamentos próprios. A matriz do
  produto precisa fixar versões e declarar se um clip foi convertido em
  `Timeline`, `Animation`, metadata ou apenas sidecar.
- O adaptador atual cria camadas, metadata, sidecars e partículas nativas em
  caminhos hash-bound; isso é uma base segura de importação e validação, mas
  não significa que cada capacidade de autor do NeoEng tenha sido materializada
  como GameObject/Component equivalente.

### Consequência de arquitetura

O modelo de autoria deve ser engine-neutral e semântico: câmera, camada,
profundidade, objeto, material, luz, partícula, clip, colisão e tilemap devem
ter contrato próprio. Cada engine deve possuir uma matriz de capacidades:
`native`, `adapted`, `metadata_only`, `unsupported` e `fallback`, com teste
positivo, negativo, persistência e captura. O editor não deve prometer
paridade apenas porque conseguiu serializar JSON.

## 7. Plano profissional recomendado

### Lote A — convergência de entrada e modelo mental

1. Manter uma única ação principal **Editor de Cenário**.
2. Mover `Cena 2D independente / protótipo de formas` para submenu “Novo” e
   explicar que é um fluxo leve, sem parallax completo.
3. Renomear internamente `ScenarioPanel` para um nome de painel de metadados
   quando a migração tiver cobertura, sem alterar o schema.
4. Ocultar a página `CanvasView` da tomada de decisão do usuário; mantê-la como
   preview/compatibilidade até uma matriz de consumidores permitir migração.
5. Exibir no primeiro uso um fluxo “Cena vazia → configurar câmera → escolher
   moldura → inserir asset/forma → salvar como”, sem exigir imagem inicial.

### Lote B — viewport e gizmo profissional

1. Criar um `GizmoStyle/InteractionModel` versionado, separado da pintura do
   item, mantendo os sinais existentes.
2. Adicionar modos explícitos: mover, girar, escala uniforme, escala por eixo,
   pivot, espaço local/mundo, snap e bloqueio de eixo.
3. Aplicar tamanho em coordenadas de tela com limites mínimo/máximo para que o
   handle permaneça utilizável em zoom alto/baixo.
4. Adicionar caixa de seleção multiobjeto, pivot visual, rótulos X/Y, estado
   ativo/hover/disabled e tooltip contextual.
5. Para 2.5D/3D, não reutilizar silenciosamente o gizmo 2D: oferecer eixos
   depth/rotation coerentes, com modo híbrido claramente marcado.

### Lote C — câmera, luz, efeitos e parallax

1. Câmera: lista de shots, “enquadrar seleção”, presets de resolução/aspecto,
   safe area, limites, follow/smoothing, preview de câmera e keyframes.
2. Luz: origem, raio/ângulo, direção com alvo visual, intensidade, cor,
   máscara de camada, sombra/occluder e indicação explícita de “preview local”
   versus “runtime nativo”.
3. Efeitos/partículas: handles de emissão e direção, bounding box, seed,
   preview pausável, reset determinístico e painel de custo aproximado.
4. Parallax: moldura por camada, bounds editáveis, safe area, mini-map/overview,
   opacidade e presets de profundidade; guias desligadas no preview/export.

### Lote D — biblioteca visual e assets proprietários

1. Unificar biblioteca de projeto e Pacotes NeoEng em uma navegação por
   miniaturas, tags, categoria e estado de integridade.
2. Permitir drag-and-drop direto para moldura e viewport, com ghost visual,
   destino destacado, undo e mensagem clara.
3. Mostrar dependências, quantidade em uso, hash, proveniência/licença e
   compatibilidade 2D/2.5D/3D sem esconder diagnóstico.
4. Virtualizar/cachear thumbnails e medir tempo de refresh, evitando decode
   repetido no thread da UI.
5. Não distribuir pacote proprietário sem licença/proveniência aprovadas; o
   manifesto atual é a base, não a autorização comercial final.

### Lote E — performance, localização e paridade

1. Instrumentar tempo de frame, tempo de refresh da biblioteca, decodificação,
   número de itens, memória e latência de drag/drop.
2. Definir orçamento inicial de interação, por exemplo resposta de seleção e
   drag abaixo de 100 ms em uma cena de referência; calibrar depois com dados.
3. Executar matriz PT-BR para menu, contexto, tooltip, erro, status, tilemap,
   partículas, câmera, luz e exportação em DPI/resoluções diferentes.
4. Fixar matriz de engine/versão e distinguir preview aproximado de runtime
   comprovado.

### Gate de cada lote

Contrato de entrada/saída, testes unitários e negativos, regressão, execução
nativa por cliques reais, captura antes/depois, persistência, erro/recuperação,
build vinculada ao commit, hashes, `git diff --check`, suíte sem filtros e
revisão visual. Sem o conjunto, o lote permanece `PENDING_EVIDENCE`.

## 8. Limpeza realizada e itens preservados

### Limpeza segura concluída

Foi executado `git worktree prune --verbose` depois de verificar que os seis
registros apontavam para `.git` inexistentes:

- `source`;
- `stage0-9-human-review-44ce207-final-source`;
- `toolbar-fix-review-d6de70a`;
- `toolbar-reference-parity-548aa97`;
- `toolbar-reference-parity-final-45c283e`;
- `toolbar-reference-parity-final-8e3ffec`.

A operação removeu apenas metadados administrativos órfãos do Git. Não removeu
os diretórios de artefatos nem arquivos de captura.

Também foram removidos, após verificação de que não eram rastreados pelo Git e
eram somente derivados locais, os três caches do checkout raiz:
`__pycache__/`, `.mypy_cache/` e `.pytest_cache/`. Nenhum arquivo-fonte,
artefato de evidência ou build foi incluído nessa remoção.

### Itens deliberadamente não removidos

- `artifacts/`, builds, capturas, hashes e manifests, pois são evidência ou
  podem estar referenciados por documentos;
- branches e worktrees ainda registrados, mesmo quando antigos, porque podem
  conter código, builds ou estado de investigação;
- arquivos históricos de falha/abort, conforme a governança;
- `archive/`, diretórios `tmp-*`, `.build-worktree-*`, releases e demais caches
  fora dos três diretórios explicitamente verificados até uma triagem por
  referências e proprietário.

O checkout raiz continua sujo por estado preexistente do usuário; ele não foi
resetado, limpo ou reescrito. A auditoria foi feita no worktree limpo para não
confundir mudanças antigas com o estado integrado.

## 9. Decisões que ficam para o final

1. Confirmar se `Cena 2D independente / protótipo de formas` deve permanecer
   como recurso público com essa identidade ou virar apenas uma ferramenta
   avançada/legada.
2. Aprovar a nova linguagem visual do gizmo: orientação 2D profissional e
   extensão híbrida 2.5D/3D separada.
3. Definir a matriz mínima de engines/versões que o produto anunciará como
   suportada.
4. Autorizar distribuição/licença final dos pacotes proprietários.

Até essas decisões, a recomendação técnica é preservar as duas superfícies,
convergir a entrada e iniciar pelo Lote A, seguido do Lote B, sem apagar nem
reimplementar o editor profissional inteiro.
