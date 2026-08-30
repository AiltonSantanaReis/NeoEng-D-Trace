# NeoEng-D-Trace — Decisão P2D-03C

## Navegação do viewport, fit e estados visuais

**Status:** `ACCEPTED / CLOSED`<br>
**Data:** 30/08/2026 (UTC-03)<br>
**Checkpoint de entrada:** `78f773583b0277fa9b970d1f849538b4fa3fdcc6`<br>
**Branch:** `modernization/multiaxis-ui`<br>
**Evidência factual:** `docs/EVIDENCIA_P2D_03C_AUDITORIA_BASELINE_2026-08-30.md`<br>
**Evidência de fechamento:** `docs/EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md`

Este documento contém o contrato aceito para o sublote P2D-03C. O proprietário
registrou o aceite explícito em 30/08/2026 com `P2D-03C ACEITO — contrato de
navegação, fit e estados visuais`. O aceite autoriza a implementação limitada
às decisões abaixo; não autoriza alteração de schema, legado, C3, baseline
canônica, push, tag, merge ou release.

## 1. Dependências e precedência

1. C3, baselines G/V/B, tolerâncias, auditores, seals e histórico anterior são
   imutáveis.
2. P2D-03A e P2D-03B estão formalmente `ACCEPTED / CLOSED` e não serão
   reabertas por este sublote.
3. A decisão geral P2D-03 continua aberta até P2D-03C, P2D-04, P2D-05,
   P2D-06 e P2D-07 satisfazerem seus próprios critérios.
4. O alvo é somente `ScenarioEditorWindow` e o viewport profissional. O
   `CanvasView` é legado e não pode ser usado como atalho de implementação.

## 2. Objetivo de produto

Permitir que a usuária navegue com precisão pela composição 2D profissional,
enquadre seleção ou composição inteira e compreenda os estados interativos dos
controles, sem modificar transforms, IDs, membership, assets, schema V1 ou o
editor legado.

## 3. Escopo autorizado

O sublote poderá alterar apenas:

- navegação de zoom no viewport profissional;
- pan no viewport profissional;
- `Fit Selection` e `Fit All` no fluxo profissional;
- conversão determinística entre viewport e mundo após navegação;
- controles e mensagens estritamente necessários para as operações acima;
- revisão visual e acessibilidade operacional de hover, pressed, checked, focus e
  disabled nas superfícies profissionais envolvidas;
- testes, auditorias, capturas, build e documentação da etapa.

Não é parte deste sublote:

- tilemap, brush, bucket, eraser, autotiling, Rule Tiles, isométrico ou
  hexagonal;
- colisão de cenário, NavMesh, entidades/componentes/prefabs, iluminação ou
  VFX;
- semântica nova para `position.z`, parallax, exportação 2.5D ou 3D;
- mudança de schema, salvo decisão formal adicional se a implementação provar
  que o schema atual não é suficiente;
- qualquer alteração do editor legado, visualizador de máscara ou menus globais;
- publicação remota, push, tag, merge ou release.

## 4. Decisão de arquitetura proposta

### 4.1 Separar navegação do viewport da câmera persistida da cena

**Recomendação:** a navegação de zoom, pan e fit deve ser um estado transitório
do viewport, separado de `SceneAuthoringDocumentV2.camera`.

Motivos:

- `camera` já é um campo persistido e já participa do contrato de preview,
  parallax e do inspector `Apply Camera`;
- usar a mesma variável para scroll/zoom de trabalho faria uma operação de
  navegação alterar dados da cena, deixar o documento dirty e mudar o preview
  salvo sem uma ação explícita de autoria;
- um estado de viewport separado evita uma segunda interpretação do schema e
  preserva o comportamento atual do inspector de câmera;
- a separação mantém aberta a evolução futura para 2.5D/3D sem confundir
  câmera de edição com câmera do produto/runtime.

O `OrthographicCamera` existente permanece a autoridade da projeção da cena e
do preview. A navegação do viewport será uma transformação de apresentação
aplicada depois da projeção, com inversão correspondente antes de converter um
clique em coordenada do mundo.

Consequências aprovadas somente se o proprietário aceitar esta decisão:

- navegar não altera JSON, `is_dirty`, undo/redo, seleção ou transforms;
- salvar/reabrir restaura a câmera persistida da cena, mas não precisa restaurar
  a posição transitória do viewport;
- `Apply Camera` continua sendo o único caminho explícito para editar a câmera
  persistida existente;
- os novos controles devem ser rotulados como navegação do viewport, sem
  reutilizar silenciosamente o rótulo de câmera da cena.

### 4.2 Zoom

Proposta operacional:

- roda do mouse no viewport profissional;
- zoom ancorado no ponto sob o cursor: o ponto do mundo sob o cursor permanece
  sob o cursor depois da operação;
- um delta vertical padrão de roda (`120`) aplica fator multiplicativo `1.15`;
- o fator é acumulado de modo determinístico para deltas fracionários de
  dispositivos de alta resolução;
- limite inferior de apresentação: `0.10x`;
- limite superior de apresentação: `8.00x`;
- atingir um limite é um no-op visual, sem alterar documento ou histórico;
- não são adicionados atalhos globais de `+`/`-` nesta etapa, para não competir
  com o editor principal e para manter a ação contextual ao viewport.

### 4.3 Pan

Proposta operacional:

- middle-button drag no viewport profissional;
- a posição inicial do cursor e a posição corrente definem o deslocamento da
  apresentação;
- o gesto não seleciona, não arrasta objeto, não abre menu contextual e não
  altera documento;
- soltar o botão encerra o gesto mesmo se o cursor sair do viewport;
- não será incluído `Space+drag` na primeira implementação; ele poderá ser
  proposto em decisão posterior se a revisão humana demonstrar necessidade.

### 4.4 Fit Selection

Proposta operacional:

- o comando usa os objetos atualmente selecionados que estejam efetivamente
  visíveis e elegíveis no viewport;
- o bounding box considera a geometria do objeto após transformações de escala,
  flip e rotação, no espaço do mundo;
- o enquadramento usa margem visual de `10%` em cada lado, com área útil mínima
  de `1 px`;
- seleção sem objetos enquadráveis é no-op, não gera exceção, não altera câmera
  persistida e emite mensagem não bloqueante objetiva;
- o botão existente `Fit Selection` deve ser conectado ao viewport profissional;
  não haverá caminho paralelo no legado;
- a operação não muda seleção, primary, transforms ou histórico.

### 4.5 Fit All

Proposta operacional:

- novo comando disponível somente na janela profissional;
- enquadra todos os objetos efetivamente visíveis, elegíveis e renderizados;
- sockets, grade, overlay, gizmo e elementos de diagnóstico não expandem o
  bounding box de conteúdo;
- aplica a mesma margem de `10%` e os mesmos limites de zoom;
- composição sem objetos preserva a navegação atual e emite mensagem não
  bloqueante;
- o comando não muda seleção, primary, transforms, documento, dirty state ou
  histórico.

### 4.6 Authoring, preview e parallax

- Em authoring, a apresentação usa coordenadas de mundo sem atenuação de
  parallax, seguida do estado transitório de navegação.
- Em preview, a projeção existente usa a câmera persistida e o parallax da
  camada, seguida do mesmo estado transitório de navegação.
- O estado transitório deve ser aplicado de forma uniforme ao resultado visual;
  não pode alterar a semântica de `position`, layer ou parallax.
- A conversão viewport → mundo deve inverter primeiro a navegação e depois a
  projeção de câmera/parallax aplicável ao item.
- Preview continua read-only para mutações de objetos, clipboard e histórico;
  zoom, pan e fit permanecem permitidos por serem navegação visual sem efeito no
  documento.

## 5. Estados visuais obrigatórios

A implementação deverá produzir uma matriz de captura, sem depender de leitura
subjetiva do código:

| Estado | Superfícies mínimas | Critério |
|---|---|---|
| hover | ações de fit, controles de navegação e handles relevantes | destaque perceptível sem mover layout ou conteúdo |
| pressed | fit e início/continuidade do pan | feedback durante o press/gesto; release encerra o estado |
| checked | Preview, Authoring e Overlay existentes | estado marcado inequívoco; Preview/Authoring continuam exclusivos |
| focus | viewport, Fit Selection, Fit All e ações de modo | foco de teclado visível e ordem documentada |
| disabled | controles sem projeto e inspector read-only em preview | sem execução por clique/tecla e motivo compreensível |

Regras adicionais:

- não alterar dimensões, splitter, padding, margins ou geometry-sensitive
  declarations fora do contrato da etapa;
- nenhum estado pode depender somente de cor; deve haver foco/borda/forma ou
  outro feedback perceptível;
- a barra de ferramentas, inspector e viewport devem manter tab order explícito;
- o foco inicial continua no viewport conforme P2D-03A/B;
- mensagens de no-op e indisponibilidade não devem ser modais quando não houver
  erro de integridade.

## 6. Invariantes bloqueantes

- Zoom, pan e fit nunca modificam transforms, IDs, assets, layers, groups,
  sockets, seleção, primary ou membership.
- Navegação nunca altera `SceneAuthoringDocumentV2.camera` nem o JSON salvo,
  salvo se o proprietário aprovar posteriormente outra arquitetura.
- A projeção e a inversão viewport ↔ mundo são finitas, determinísticas e
  round-trip dentro da tolerância numérica declarada.
- Zoom não ultrapassa `0.10x..8.00x`.
- Fit nunca gera zoom não finito, zero ou negativo.
- Fit vazio é no-op seguro; não há alteração parcial.
- Pan não intercepta clique de seleção, drag de objeto ou gizmo.
- Preview não permite mutações de edição, mesmo depois de pan/zoom/fit.
- Os atalhos já aceitos de P2D-03A/B continuam limitados ao viewport e não são
  sequestrados por campos editáveis do inspector.
- A mudança não altera `SceneAuthoringDocumentV1`, `CanvasView`, menus globais,
  C3 ou gates G/V/B.

## 7. Testes obrigatórios antes do aceite

### 7.1 Domínio/projeção

- projeção e inversão em zoom neutro, mínimo, máximo e valor intermediário;
- ponto sob o cursor permanece ancorado após zoom;
- pan positivo/negativo e múltiplos movimentos;
- fit de um objeto, vários objetos, rotação, escala e flip;
- fit com seleção vazia e fit all em cena vazia;
- objetos ocultos, isolados e não elegíveis fora do cálculo;
- sockets, grid, overlay e gizmo fora do cálculo de conteúdo;
- nenhum drift de transform, câmera persistida, seleção ou dirty state;
- preview com parallax e authoring com projeção neutra;
- valores extremos e deltas fracionários sem NaN, infinito ou exceção.

### 7.2 Qt e fluxo da usuária

- abrir projeto, abrir a janela profissional e receber foco inicial;
- usar wheel zoom em pontos distintos e confirmar ancoragem;
- usar middle drag e confirmar que não move objetos;
- usar Fit Selection pelo inspector e Fit All pelo novo controle;
- confirmar mensagens de no-op em seleção/cena vazia;
- confirmar hover, pressed, checked, focus e disabled com capturas reais;
- confirmar Tab/Shift+Tab e foco de retorno sem sequestrar campos do inspector;
- repetir authoring/preview, visibilidade, lock, isolamento e seleção;
- salvar/reabrir e provar que apenas os dados persistentes esperados foram
  preservados.

### 7.3 Regressão e gates

- testes focalizados P2D-03C;
- suíte completa com Python 3.11 da `.venv`;
- `git diff --check`, fronteira autorizada e checks protected/geometry-sensitive;
- G60/60, V12/12 e B21/21 no aggregate canônico;
- produtores legacy continuam visíveis e classificados, sem relaxamento;
- captura Windows nas três resoluções canônicas `1920x1080`, `1366x768` e
  `1280x720`, além do fluxo funcional profissional `1280x820` quando aplicável;
- auditoria visual, comparação estrutural e revisão humana;
- build portátil e smoke test se o pacote distribuível for afetado.

## 8. Evidências obrigatórias

O fechamento deverá conter:

1. commit de entrada e commit de saída;
2. lista exata de arquivos e símbolos alterados;
3. matriz requisito → código → teste → evidência;
4. logs completos, ambiente e exit codes;
5. testes positivos, negativos e no-op;
6. capturas reais Windows com resolução, DPI e estado;
7. comparação sem mascaramento e classificação de qualquer estado vivo;
8. revisão humana dos fluxos e estados;
9. suíte completa e G/V/B;
10. manifest, SHA-256, extração/re-hash e tracked tree final limpo.

## 9. Decisões que exigem aceite explícito

As escolhas abaixo são materiais e não serão assumidas silenciosamente:

| ID | Decisão proposta | Aceite necessário |
|---|---|---|
| D03C-01 | navegação transitória separada da câmera persistida; sem dirty/undo/save por zoom, pan e fit | sim |
| D03C-02 | wheel ancorada, fator `1.15` por `120`, limites `0.10x..8.00x`, sem atalhos globais `+/-` | sim |
| D03C-03 | pan exclusivamente por middle-button drag na primeira versão | sim |
| D03C-04 | fit com margem de `10%`, somente objetos visíveis/elegíveis; sockets e overlays fora do cálculo | sim |
| D03C-05 | controles de navegação permitidos em preview; mutações continuam bloqueadas | sim |
| D03C-06 | auditoria visual dos estados nas resoluções canônicas e fluxo profissional `1280x820` | sim |

O proprietário registrou o aceite explícito: **`P2D-03C ACEITO — contrato de navegação, fit e estados visuais`**, em 30/08/2026. A implementação foi autorizada exclusivamente dentro desta decisão. Após o ciclo pre-commit, commit, requalificação pós-commit, revisão humana, build e seal, o proprietário registrou **`P2D-03C ACEITO — entrega final`** em 30/08/2026.

## 10. Critérios de aceite do sublote

P2D-03C somente poderá ser marcada `ACCEPTED / CLOSED` quando:

- todas as decisões da seção 9 estiverem aceitas e registradas;
- zoom, pan, Fit Selection e Fit All funcionarem na janela profissional;
- conversão viewport ↔ mundo passar nos casos com e sem parallax;
- os invariantes tiverem testes positivos e negativos;
- estados visuais tiverem capturas e revisão humana;
- nenhum objeto, documento ou histórico sofrer alteração indevida;
- suíte, gates, captura, auditoria, build e seal passarem;
- índice, plano, decisão e evidência estiverem reconciliados;
- o proprietário registrar aceite final da entrega.

Após o commit técnico `58674dde87ba94082e84f066ebda21d144da65cd`, a
requalificação pós-commit e a build portátil foram concluídas sem finding
reproduzível. A revisão humana adicional do proprietário também não
reproduziu a lentidão relatada na transição Fit/Focus. O aceite final foi
registrado com **`P2D-03C ACEITO — entrega final`** em 30/08/2026, e a
evidência, o pacote e a verificação independente foram concluídos.
**P2D-03C ACCEPTED / CLOSED.**

## 11. Estado pós-commit e regra de encerramento

O fechamento técnico e formal está consolidado na evidência
`docs/EVIDENCIA_P2D_03C_FECHAMENTO_2026-08-30.md`. O pacote final de seal foi
gerado fora do repositório e extraído e revalidado independentemente após o
aceite final. Seu caminho local não é registrado neste documento por
privacidade; o hash do ZIP permanece no manifest do pacote. Nenhum resultado
misto legacy foi apagado ou convertido em PASS para satisfazer este fechamento.
