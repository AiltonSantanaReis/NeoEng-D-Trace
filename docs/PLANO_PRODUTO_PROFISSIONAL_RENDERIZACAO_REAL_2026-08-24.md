# Plano de Produto Profissional — NeoEng-D-Trace

**Versão:** 1.0  
**Data:** 2026-08-24  
**Status:** proposta de arquitetura e execução  
**Escopo:** evolução do produto para editor profissional de cenas 2D/2.5D, com fundação compatível com 3D e renderização real

## 1. Finalidade

Este documento define a direção técnica, visual e operacional para que o NeoEng-D-Trace deixe de ser tratado como protótipo e evolua como produto profissional.

O objetivo não é apenas melhorar a aparência da interface. O produto deverá possuir:

- modelo de cena persistente e versionado;
- viewport profissional como núcleo de autoria;
- renderização real, preferencialmente acelerada por GPU;
- iluminação, partículas, materiais, máscaras e pós-processamento efetivamente renderizados;
- reprodução previsível no editor e no runtime;
- exportação verificável;
- testes funcionais, visuais, de desempenho e de compatibilidade;
- builds identificáveis, rastreáveis e impossíveis de confundir entre fases;
- documentação que declare claramente o que está implementado, simulado, degradado ou indisponível.

Este plano complementa as etapas históricas já concluídas e não as reescreve. As etapas 0–9 continuam tendo seus próprios critérios, evidências e aprovações. As fases deste documento são um plano de evolução de produto e não devem ser confundidas com a numeração histórica das etapas.

## 2. Princípios obrigatórios

### 2.1 Produto antes de demonstração

Nenhum recurso será considerado concluído apenas porque existe um botão, uma estrutura de dados, um sidecar, uma simulação ou uma tela de demonstração. A conclusão exige comportamento real, persistência, integração, testes e evidência.

### 2.2 Sem alegações superiores à implementação

Cada capacidade será classificada como uma destas categorias:

1. **Renderizada:** o resultado visual é produzido pelo renderer e foi comprovado em artefato visual.
2. **Executável:** o comportamento é executado em runtime, mas ainda não possui composição visual completa.
3. **Simulada:** existe uma simulação controlada, sem equivalência garantida com renderização final.
4. **Persistida/exportada:** os dados são armazenados ou exportados, mas ainda não são reproduzidos visualmente.
5. **Degradada:** funciona com limitações documentadas.
6. **Planejada:** ainda não existe implementação suficiente.

O produto não poderá apresentar um recurso como renderizado quando ele for apenas estrutural ou simulado.

### 2.3 Separação de responsabilidades

O `CanvasView` não será destruído nem usado como substituto artificial do viewport profissional. Ele permanecerá como ferramenta especializada para imagem, máscara, X-Ray e inspeção 2D.

O `SceneViewport` será o viewport principal de autoria de cenas. Ambos deverão compartilhar contratos de domínio e recursos quando apropriado, mas não deverão misturar responsabilidades, ciclos de vida ou modelos visuais incompatíveis.

### 2.4 Editor e runtime devem convergir

O editor não deve exibir uma composição que o runtime não consiga reproduzir sem uma justificativa explícita. A mesma definição de cena deverá alimentar:

- autoria;
- preview;
- reprodução;
- exportação;
- validação visual.

Quando houver diferença inevitável entre editor e runtime, ela deverá ser medida, documentada e testada.

### 2.5 Baseline encadeada e preparada para o produto final

Cada baseline deverá preservar:

- identidade do commit;
- manifesto de arquivos;
- versão do schema da cena;
- versão do renderer;
- versão dos assets e fixtures;
- capacidades suportadas;
- resultados de testes;
- artefatos visuais;
- limitações conhecidas.

A baseline não poderá limitar etapas futuras. Novos recursos deverão ser adicionados por compatibilidade, migração de schema ou extensão de contrato, sem destruir a leitura das cenas e evidências anteriores.

## 3. Estado atual que orienta o plano

O projeto já possui uma base funcional relevante:

- shell de interface alinhado parcialmente à referência;
- `CanvasView` com zoom, pan, ajuste à janela, grade, snap, seleção, gizmo e modos visuais;
- visualizador de máscaras e fluxo X-Ray;
- viewport de autoria de cenas separado;
- inspector de transformação;
- câmeras, parallax e sockets;
- persistência e exportação de cenários;
- contratos de runtime, iluminação e partículas;
- suíte automatizada ampla e governança de evidências.

Entretanto, ainda existem lacunas que impedem a declaração de produto profissional completo:

- o `CanvasView` ainda ocupa o papel de viewport principal em partes do fluxo;
- o viewport de autoria ainda não é o compositor visual final;
- iluminação e partículas não estão comprovadas como renderização integrada em tempo real;
- o painel direito está funcional, mas não possui a densidade e o acabamento da referência;
- editor e runtime ainda precisam compartilhar um pipeline de renderização real;
- o suporte 3D ainda não deve ser declarado antes de uma decisão de backend e uma prova técnica.

## 4. Arquitetura-alvo

### 4.1 Camadas do produto

```text
Interface do editor
 ├── SceneViewport
 ├── barra de ferramentas
 ├── barra de ferramentas lateral
 ├── inspector
 ├── layer stack
 ├── asset browser
 └── playback/diagnostics HUD

Aplicação de autoria
 ├── comandos e undo/redo
 ├── seleção e ferramentas
 ├── câmera editorial
 ├── validação de cena
 └── persistência/migração

Domínio de cena
 ├── entidades e componentes
 ├── transformações
 ├── camadas e grupos
 ├── câmeras
 ├── materiais
 ├── luzes
 ├── partículas
 ├── colisões
 ├── sockets
 └── animação/timeline

Renderização
 ├── backend GPU
 ├── render graph
 ├── recursos/texturas
 ├── materiais/shaders
 ├── iluminação
 ├── partículas
 ├── máscaras/blending
 └── pós-processamento

Runtime/exportação
 ├── fixed timestep
 ├── carregamento de cena
 ├── reprodução
 ├── captura/replay
 ├── adapters
 └── pacotes exportados
```

### 4.2 Modelo de cena

O modelo deverá deixar de depender da interface. A cena deverá representar, no mínimo:

- identificador estável de entidade;
- tipo de entidade;
- transform local e global;
- ordem de camada e profundidade;
- visibilidade e bloqueio;
- asset ou textura associada;
- material;
- máscara;
- parâmetros de parallax;
- sockets;
- colisão;
- componentes de câmera, luz, partículas ou efeitos;
- propriedades editoriais que não afetam o runtime;
- versão de schema e metadados de migração.

O modelo deverá ser serializável de maneira determinística: a mesma cena, com os mesmos recursos, deve produzir o mesmo conteúdo lógico e o mesmo hash normalizado.

### 4.3 Renderer

O renderer deverá ser isolado do código de widgets e não depender de `paintEvent` como mecanismo principal de composição da cena.

Ele deverá possuir:

- contexto de renderização explicitamente gerenciado;
- inicialização e fallback documentados;
- fila de recursos;
- render graph ou equivalente de passes ordenados;
- composição de sprites e texturas;
- profundidade e ordenação;
- blending e máscaras;
- câmera ortográfica;
- câmera perspectiva quando o backend 3D for aprovado;
- iluminação e materiais;
- partículas atualizadas por timestep controlado;
- pós-processamento opcional;
- captura de frame para auditoria;
- diagnóstico de GPU, backend, tempo de frame e memória.

O backend exato não será escolhido por preferência subjetiva. A decisão deverá ser tomada após um benchmark comparativo entre as opções compatíveis com o ambiente do projeto, sua distribuição para Windows/Linux e sua integração com PySide6.

### 4.4 2.5D como primeiro alvo visual

O primeiro alvo profissional será 2.5D, pois entrega valor real sem obrigar o projeto a assumir imediatamente toda a complexidade de um editor 3D.

O 2.5D deverá suportar:

- planos e sprites texturizados;
- coordenada de profundidade;
- câmera ortográfica;
- parallax por profundidade;
- escala e perspectiva controlada;
- iluminação sobre elementos;
- partículas no espaço da cena;
- composição por camadas;
- máscaras e colisão;
- preview e runtime com o mesmo pipeline.

A compatibilidade com 3D deverá ser preservada no modelo e no renderer, mas a declaração de suporte 3D dependerá de uma fase própria com câmera, malhas, materiais, iluminação e testes de desempenho reais.

## 5. Fases de execução

### Fase A — Governança e contrato de produto

**Objetivo:** congelar a definição do produto profissional antes de substituir componentes críticos.

Entregas:

- visão oficial do produto;
- matriz de capacidades;
- glossário técnico;
- classificação de cada recurso atual;
- matriz de responsabilidades entre `CanvasView`, `SceneViewport`, renderer e runtime;
- mapa de dependências;
- política de compatibilidade de cenas;
- política de baseline e builds;
- registro de riscos;
- critérios de aprovação humana.

Critérios de saída:

- nenhuma funcionalidade possui descrição ambígua;
- cada recurso possui responsável técnico;
- recursos históricos e futuros estão separados;
- não existe promessa de renderização sem implementação correspondente;
- a baseline encadeada é gerada e validada.

### Fase B — Decisão de backend de renderização

**Objetivo:** escolher a fundação técnica que permita renderização real e evolução para 2.5D/3D.

O benchmark deverá comparar, no mínimo:

- inicialização no Windows e Linux;
- integração com a janela PySide6;
- textura e composição de sprites;
- câmera e profundidade;
- iluminação simples;
- partículas;
- captura de frame;
- resize e troca de contexto;
- fallback quando GPU não estiver disponível;
- empacotamento;
- estabilidade por pelo menos 30 minutos;
- desempenho em hardware de referência.

A decisão deverá ser registrada em ADR, incluindo alternativas rejeitadas, motivos, riscos e plano de migração.

Critério de saída: existe uma cena mínima renderizada pela GPU, com frame capturado, métricas e execução nos sistemas suportados.

### Fase C — Núcleo de cena independente da UI

**Objetivo:** tornar a cena o contrato central do produto.

Entregas:

- entidades/componentes;
- transformações locais e globais;
- hierarquia e camadas;
- câmeras;
- materiais e recursos;
- componentes de iluminação e partículas;
- schema versionado;
- migrações;
- validação estrutural;
- serialização determinística;
- undo/redo baseado em comandos.

Critérios de saída:

- uma cena pode ser criada, salva, carregada e validada sem abrir a UI;
- o mesmo arquivo pode ser usado pelo editor e pelo runtime;
- cenas antigas continuam carregando ou falham com diagnóstico explícito;
- nenhum widget contém a regra de negócio principal.

### Fase D — SceneViewport profissional

**Objetivo:** substituir o papel de viewport principal do `CanvasView` por um viewport de autoria real.

Entregas:

- viewport baseado no renderer escolhido;
- renderização de cena real;
- pan, zoom e fit;
- seleção de entidades;
- gizmos de translação, rotação e escala;
- câmera editorial;
- grade, snap e réguas;
- overlays de colisão, sockets e bounds;
- minimapa;
- coordenadas e diagnóstico de frame;
- drag-and-drop de assets;
- sincronização bidirecional com inspector e layer stack.

O `CanvasView` continuará disponível para visualização de imagem e máscara, mas não deverá ser utilizado para representar a cena final.

Critérios de saída:

- uma cena com pelo menos dez entidades é editável sem perder seleção ou estado;
- o viewport preserva transformação, zoom e câmera ao alterar propriedades;
- o frame renderizado pode ser capturado para evidência;
- o editor não desenha a cena final por uma simulação visual enganosa.

### Fase E — Sistema visual profissional

**Objetivo:** aproximar a interface da referência em qualidade, consistência e produtividade.

Entregas:

- tokens de cor, tipografia, espaçamento, bordas e estados;
- barra superior agrupada por responsabilidade;
- barra lateral com estados ativos e tooltips;
- painel direito com abas Objects/Layers/Groups/Collision;
- layer rows com visibilidade, bloqueio, cor, nome, opacidade e ordem;
- inspector com seções recolhíveis;
- componentes de campo vetorial;
- indicadores de valor modificado, inválido e vinculado;
- menus contextuais;
- foco de teclado;
- feedback de operação;
- estado dirty e salvamento seguro;
- redução de comandos duplicados.

Critérios de saída:

- toda ação possui um local canônico;
- a seleção do viewport, da camada e do inspector é sempre consistente;
- a interface mantém legibilidade em diferentes tamanhos de janela;
- não há controles decorativos sem comportamento real;
- a revisão visual humana aprova o shell completo.

### Fase F — Câmera, profundidade e parallax 2.5D

**Objetivo:** entregar uma composição 2.5D real.

Entregas:

- câmera ortográfica;
- profundidade por entidade;
- parallax por camada e por objeto;
- enquadramento e limites de câmera;
- preview de movimento;
- interpolação configurável;
- suporte a múltiplas câmeras, se necessário;
- exportação das mesmas propriedades para runtime.

Critérios de saída:

- uma cena de referência demonstra deslocamento de câmera e paralaxe perceptível;
- o resultado do editor e do runtime é visualmente equivalente dentro da tolerância definida;
- mudanças de profundidade não quebram seleção, colisão ou ordenação.

### Fase G — Materiais e iluminação real

**Objetivo:** deixar de tratar luz como metadado e produzir iluminação visual real.

Escopo inicial:

- luz ambiente;
- luz direcional;
- luz pontual;
- luz focal, se suportada pelo backend;
- cor, intensidade e alcance;
- mistura com sprites e planos;
- materiais básicos;
- transparência e blending;
- máscaras de iluminação;
- opção de iluminação por camada.

Escopo posterior:

- sombras;
- normal maps;
- materiais avançados;
- HDR;
- bloom e outros pós-processamentos.

Critérios de saída:

- a luz altera efetivamente os pixels renderizados;
- existe captura antes/depois com diferença visual mensurável;
- o resultado funciona no editor e no runtime;
- fallback de GPU é documentado e não é apresentado como equivalência silenciosa.

### Fase H — Partículas e VFX reais

**Objetivo:** entregar partículas visualmente renderizadas e controláveis.

Entregas:

- emissor;
- taxa de emissão;
- ciclo de vida;
- velocidade e aceleração;
- gravidade;
- cor e escala ao longo da vida;
- textura de partícula;
- blend;
- seed determinística;
- pausa, avanço por frame e replay;
- limites de segurança;
- integração com câmera e profundidade;
- exportação.

Critérios de saída:

- partículas aparecem no frame renderizado;
- o mesmo seed produz o mesmo replay lógico;
- o sistema não congela a UI com limites normais;
- existe teste de estresse e captura visual;
- partículas não são confundidas com simples marcadores de socket.

### Fase I — Render graph, pós-processamento e composição

**Objetivo:** criar qualidade visual controlada sem acoplar efeitos ao widget.

Entregas possíveis:

- passes de composição;
- máscaras;
- blend modes;
- correção de cor;
- vignette;
- bloom;
- blur;
- efeitos por camada;
- ordem explícita dos passes;
- diagnóstico de custo por pass.

Critérios de saída:

- cada efeito possui contrato, backend e fallback documentados;
- o editor mostra o mesmo efeito que o runtime quando ambos o suportam;
- efeitos indisponíveis são identificados, nunca silenciosamente ignorados.

### Fase J — Playback e runtime integrado

**Objetivo:** transformar a prévia em reprodução real e auditável.

Entregas:

- play, pause, stop e step;
- fixed timestep;
- relógio determinístico;
- timeline mínima;
- replay por seed e snapshot;
- eventos e triggers;
- câmera em movimento;
- atualização de partículas;
- atualização de luzes e materiais;
- telemetria de frame;
- captura de sequência;
- comparação editor/runtime.

Critérios de saída:

- uma cena pode ser reproduzida por tempo controlado;
- pausar e avançar um frame produz comportamento previsível;
- falhas de asset, shader ou backend são visíveis;
- o runtime não depende de controles internos exclusivos da UI.

### Fase K — Fundamentos de 3D

Esta fase só deverá ser iniciada depois da estabilização do 2.5D.

Escopo:

- câmera perspectiva;
- coordenada 3D;
- malhas;
- materiais 3D;
- iluminação 3D;
- profundidade real;
- importação de um formato definido;
- seleção e gizmos 3D;
- testes de culling e desempenho.

O suporte 3D não será anunciado antes de uma vertical slice funcional com asset 3D, câmera, luz, material, renderização e exportação comprovados.

### Fase L — Assets, empacotamento e distribuição

**Objetivo:** transformar o produto em software distribuível e operável.

Entregas:

- asset browser;
- importação validada;
- cache de recursos;
- thumbnails;
- detecção de recurso ausente;
- empacotamento de cenas;
- build Windows e Linux;
- logs de diagnóstico;
- recuperação de projeto;
- versionamento de formato;
- documentação de instalação.

Critérios de saída:

- uma máquina limpa consegue instalar e abrir o build;
- recursos são localizados por manifesto e hash;
- projetos incompletos produzem diagnóstico acionável;
- a build de cada fase possui nome, versão, commit e finalidade explícitos.

### Fase M — Qualidade, segurança e desempenho

**Objetivo:** comprovar que o produto é confiável em condições reais.

Testes obrigatórios:

- unitários;
- integração;
- contrato de schema;
- persistência;
- migração;
- renderer;
- visual golden;
- GPU/headless;
- compatibilidade Windows/Linux;
- desempenho;
- memória;
- stress;
- longa duração;
- interrupção e recuperação;
- fuzzing de arquivos de cena;
- validação de paths e assets;
- empacotamento limpo.

Metas iniciais a validar no hardware oficial, não fatos atuais:

- 60 FPS em cena 2.5D de referência em 1080p;
- p95 de frame abaixo de 16,7 ms no perfil-alvo;
- ausência de crescimento contínuo de memória em sessão prolongada;
- carregamento de projeto dentro do limite aprovado;
- exportação reproduzível;
- degradação explícita quando a GPU não suportar um recurso.

### Fase N — Release candidate e revisão humana

O release candidate deverá conter:

- build isolada e identificada;
- manifesto de fontes e assets;
- relatório de testes;
- relatório visual;
- relatório de desempenho;
- matriz de capacidades;
- limitações conhecidas;
- instruções de instalação;
- cenários de revisão humana;
- checklist de aceite;
- hash da build;
- vínculo com o commit e a baseline anterior.

A revisão humana deverá testar fluxos completos, e não apenas telas:

1. criar projeto;
2. importar assets;
3. compor camadas;
4. editar transformações;
5. ajustar câmera e parallax;
6. adicionar luz;
7. adicionar partículas;
8. reproduzir a cena;
9. salvar e reabrir;
10. exportar;
11. abrir o resultado em ambiente limpo;
12. verificar se a imagem final corresponde ao preview.

## 6. Estratégia de migração

A migração deverá ocorrer de forma incremental:

1. congelar os contratos atuais das etapas concluídas;
2. criar o novo modelo de cena sem remover o legado;
3. criar o backend de renderer em uma vertical slice isolada;
4. conectar o `SceneViewport` ao novo modelo;
5. migrar primeiro cenas de teste;
6. migrar o construtor de cenários;
7. migrar ferramentas de câmera e parallax;
8. migrar luzes e partículas;
9. somente depois revisar o fluxo principal;
10. manter o `CanvasView` para imagem, máscara e X-Ray;
11. remover caminhos antigos apenas após cobertura equivalente e aprovação.

Não será permitido substituir o `CanvasView` por outro widget apenas para alterar a aparência. A substituição só estará concluída quando houver renderização de cena, seleção, persistência, preview, exportação e testes equivalentes ou superiores.

## 7. Artefatos obrigatórios por fase

Cada fase deverá gerar:

- documento de escopo;
- ADR ou decisão técnica, quando houver mudança arquitetural;
- matriz requisito → implementação → teste → evidência;
- testes automatizados;
- captura visual ou vídeo quando houver alteração visual;
- relatório de desempenho quando houver renderer;
- manifesto de artefatos;
- log completo de execução;
- build identificada;
- baseline encadeada;
- relatório de riscos;
- aprovação humana.

Nenhum artefato de uma fase posterior poderá ser usado como prova de uma fase anterior sem estar explicitamente identificado como evidência adicional.

## 8. Gates de qualidade

Uma fase só poderá ser concluída quando:

- o escopo estiver fechado;
- todos os critérios de aceite estiverem atendidos;
- os testes previstos passarem;
- os testes não mascararem fallback ou indisponibilidade;
- a documentação estiver atualizada;
- a build estiver identificada;
- os artefatos forem verificáveis;
- a revisão humana for realizada quando aplicável;
- o commit estiver registrado;
- a branch estiver sincronizada conforme a governança;
- a baseline encadeada estiver íntegra.

Um teste que passa por fallback automático deverá registrar o fallback. Passar no teste não autoriza declarar que o backend principal funcionou.

## 9. Riscos principais

### Escolha inadequada de backend

Mitigação: benchmark antes da migração e ADR com critérios mensuráveis.

### Divergência entre editor e runtime

Mitigação: renderer e modelo compartilhados, golden images e comparação de frames.

### Escopo 3D prematuro

Mitigação: concluir 2.5D e sua pipeline de renderização antes de anunciar 3D.

### Interface visualmente sofisticada, mas funcionalmente incompleta

Mitigação: cada controle deve ter contrato, teste e efeito verificável.

### Regressão das etapas históricas

Mitigação: suites vinculadas à baseline, migração por compatibilidade e builds separadas.

### Desempenho insuficiente

Mitigação: orçamento de frame desde a primeira vertical slice, não apenas no fim.

### Fallback mascarado

Mitigação: capability matrix, logs obrigatórios e evidência do backend efetivamente usado.

## 10. Ordem recomendada de execução

A ordem profissional recomendada é:

1. governança e contrato do produto;
2. decisão do backend de renderização;
3. modelo de cena independente;
4. vertical slice 2.5D com renderização real;
5. SceneViewport como viewport principal;
6. inspector e layer stack profissionais;
7. câmera e parallax;
8. iluminação real;
9. partículas reais;
10. playback e runtime integrado;
11. pós-processamento;
12. empacotamento e distribuição;
13. fundamentos 3D;
14. release candidate e revisão humana.

Essa ordem evita investir primeiro em acabamento visual de controles que ainda não possuem um núcleo de renderização capaz de sustentá-los.

## 11. Declaração de produto pretendida

Ao final deste plano, o NeoEng-D-Trace deverá ser capaz de ser apresentado como um editor profissional de cenas 2D/2.5D, com renderização real, composição de camadas, câmera, parallax, iluminação, partículas, playback, persistência, exportação e evidências verificáveis.

O suporte 3D somente será declarado quando cumprir os mesmos critérios de realidade, integração e comprovação.

Até lá, qualquer documentação, tela ou build deverá informar exatamente o nível de capacidade disponível. O produto não deverá usar aparência profissional para esconder implementação parcial, nem usar contratos estruturais para afirmar que uma funcionalidade visual já está concluída.
