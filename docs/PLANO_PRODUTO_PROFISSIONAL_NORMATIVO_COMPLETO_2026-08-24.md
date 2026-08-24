# Plano Normativo Completo do Produto Profissional NeoEng-D-Trace

**Versão:** 1.0  
**Data:** 2026-08-24  
**Natureza:** especificação obrigatória de produto, arquitetura, execução, testes e encerramento  
**Release-alvo:** Release Profissional 2.5D, com expansão formal posterior para 3D

## 1. Finalidade e força normativa

Este documento é o contrato de execução do produto. Não é uma lista de ideias, uma sugestão aberta, um resumo ou uma autorização para decidir o escopo durante a implementação.

As etapas históricas 0–9 permanecem válidas, com seus próprios requisitos, evidências e aprovações. As fases deste documento são uma evolução de produto e não substituem a numeração histórica.

Os termos têm significado obrigatório:

- **DEVE:** requisito obrigatório.
- **NÃO DEVE:** comportamento proibido.
- **CONCLUÍDO:** todos os requisitos e evidências da fase foram atendidos.
- **COMPROVADO:** implementado, testado, reproduzido e documentado.
- **PENDENTE:** qualquer item sem evidência suficiente, ainda que parcialmente implementado.
- **FALLBACK:** caminho alternativo de execução, sempre registrado e nunca apresentado como equivalente sem comprovação.

Nenhum requisito poderá ser reduzido, reinterpretado, substituído por simulação ou transferido para uma fase posterior sem registro formal de mudança contendo motivo, impacto em arquitetura e escopo, requisitos afetados, testes afetados, artefatos afetados e aprovação do responsável pelo produto.

## 2. Resultado final obrigatório

O produto deverá ser um software profissional de autoria e composição de cenas 2D/2.5D com renderização real. Não será aceito um conjunto de telas que apenas simule um editor, nem uma interface sofisticada sem comportamento integrado.

O **Release Profissional 2.5D** somente poderá ser encerrado quando todos os requisitos abaixo estiverem comprovados:

1. O viewport principal utilizará o `SceneViewport` integrado ao renderer de cena.
2. O `CanvasView` permanecerá separado para imagem, máscara, X-Ray e inspeção 2D.
3. Cenas poderão ser criadas, editadas, salvas, fechadas, reabertas e migradas.
4. Entidades terão transformação, profundidade, camada, visibilidade, bloqueio e seleção.
5. A câmera ortográfica funcionará no editor e no runtime.
6. O parallax alterará visualmente a composição conforme câmera e profundidade.
7. A iluminação alterará efetivamente os pixels renderizados.
8. Partículas serão emitidas, atualizadas e renderizadas visualmente.
9. Texturas, materiais, blending e máscaras serão processados pelo renderer.
10. Haverá reprodução com play, pause, stop, step e timestep controlado.
11. Editor e runtime usarão o mesmo modelo de cena e terão equivalência visual medida.
12. A cena poderá ser exportada e executada em ambiente limpo.
13. Haverá diagnóstico de backend, GPU, fallback, tempo de frame e memória.
14. O inspector, o layer stack, as ferramentas e os estados visuais terão nível profissional.
15. Testes funcionais, visuais, de integração, desempenho, compatibilidade e empacotamento passarão.
16. A revisão humana formal aprovará os fluxos completos.

Se um único item estiver pendente, o release não estará concluído e o status oficial permanecerá **EM DESENVOLVIMENTO**.

O suporte 3D será uma expansão independente, denominada **Release Profissional 3D**. Compatibilidade arquitetural não é suporte 3D e não poderá ser declarada como tal.

## 3. Responsabilidades dos viewports

### 3.1 `CanvasView`

O `CanvasView` DEVE permanecer disponível para:

- visualização de imagens;
- visualização e processamento de máscaras;
- X-Ray;
- inspeção 2D;
- ferramentas auxiliares que não representam a composição final de uma cena.

O `CanvasView` NÃO DEVE ser usado como renderer principal de cenas, iluminação, partículas, composição 2.5D ou 3D.

### 3.2 `SceneViewport`

O `SceneViewport` DEVE ser o viewport principal para:

- entidades de cena;
- camadas e grupos;
- câmera;
- profundidade;
- parallax;
- materiais;
- iluminação;
- partículas;
- colisões;
- sockets;
- preview e playback.

Os dois viewports poderão compartilhar modelo de domínio, assets, comandos e validações, mas NÃO DEVERÃO compartilhar responsabilidades visuais de maneira ambígua.

## 4. Proibições absolutas

Não será aceito como conclusão:

- botão sem processamento real;
- marcador de socket apresentado como luz ou partícula renderizada;
- sidecar apresentado como efeito visual concluído;
- simulação sem saída visual quando o requisito exigir renderização;
- screenshot de tela estática como prova de comportamento;
- teste que passe porque o backend real foi silenciosamente substituído por fallback;
- função presente apenas em caminho interno não acessível ao usuário;
- recurso que não possa ser salvo, reaberto e exportado;
- divergência editor/runtime sem medição e justificativa aprovada;
- limitação conhecida omitida da documentação;
- aparência visual profissional usada para mascarar implementação parcial.

## 5. Arquitetura obrigatória

O sistema deverá conter quatro camadas separadas.

### 5.1 Interface

Contém janela, toolbar, inspector, layer stack, menus, atalhos e overlays. Não poderá conter as regras centrais de renderização, persistência ou simulação.

### 5.2 Domínio de cena

Contém entidades, componentes, transformações, camadas, grupos, câmeras, materiais, luzes, partículas, colisões, sockets, schema e migrações.

Deverá funcionar sem abrir a UI e possuir serialização determinística.

### 5.3 Renderer

Contém recursos GPU, texturas, materiais, render passes, câmera, profundidade, iluminação, partículas, máscaras, blending e pós-processamento.

Não deverá depender de `paintEvent` para compor a cena final.

### 5.4 Runtime

Contém carregamento, fixed timestep, playback, eventos, replay, exportação, diagnóstico e execução fora da janela de edição.

Editor e runtime deverão consumir o mesmo modelo de cena e as mesmas regras de composição compartilhadas.

## 6. Escolha do backend de renderização

Antes da migração ampla, deverá ser produzido um benchmark executável comparando os backends candidatos compatíveis com a integração do projeto, Windows, Linux e empacotamento oficial.

O backend escolhido DEVE demonstrar, em uma vertical slice:

- textura e composição por GPU;
- câmera ortográfica;
- profundidade;
- iluminação que altere pixels;
- partículas visíveis;
- captura de frame;
- resize;
- recuperação de contexto;
- diagnóstico do backend realmente usado;
- execução nos sistemas suportados;
- empacotamento;
- fallback explícito.

O backend será rejeitado se não cumprir qualquer requisito. A decisão será registrada em ADR com alternativas, medições, riscos, decisão e plano de migração.

## 7. Modelo de cena e persistência

Cada entidade deverá possuir identificador estável, tipo, transformação local, transformação global calculável, camada, profundidade, visibilidade, bloqueio, asset, material e componentes adicionais.

O schema deverá possuir:

- versão explícita;
- validação;
- migração;
- rejeição segura de versão incompatível;
- preservação de dados desconhecidos quando possível;
- hash normalizado;
- fixtures válidas, inválidas e antigas;
- diagnóstico de erro acionável.

Uma cena só será considerada persistente quando puder ser salva, fechada, reaberta e comparada sem perda de dados relevantes.

## 8. Fases de implementação e encerramento

### Fase 1 — Contrato de produto

**Objetivo:** congelar requisitos, limites e responsabilidades antes da alteração estrutural.

**Entregas obrigatórias:** matriz de capacidades, glossário, limites entre viewports, riscos, baseline, matriz requisito–teste–evidência e critérios de release.

**Encerramento:** nenhum requisito ambíguo; nenhum recurso sem categoria; aprovação formal do contrato.

### Fase 2 — Backend e vertical slice

**Objetivo:** comprovar renderização real antes da migração da interface.

**Obrigatório:** textura, câmera, profundidade, uma luz que altere pixels, um emissor de partículas e captura de frame.

**Encerramento:** execução Windows/Linux, logs, captura, métricas de frame, memória, fallback e ADR aprovados.

### Fase 3 — Domínio de cena

**Objetivo:** retirar regras de cena dos widgets.

**Encerramento:** criar, salvar, carregar, validar, migrar e comparar cenas sem depender da UI.

### Fase 4 — `SceneViewport` principal

**Objetivo:** tornar o viewport profissional o centro da autoria.

**Obrigatório:** render real, zoom, pan, fit, seleção, gizmo, grade, snap, réguas, minimapa, overlays, câmera e sincronização com inspector.

**Encerramento:** cena com pelo menos dez entidades editável, salvável e reproduzível sem perda de estado.

### Fase 5 — Interface profissional

**Objetivo:** atingir o padrão de organização, densidade e acabamento da referência.

**Obrigatório:** abas Objects/Layers/Groups/Collision; linhas de camada com visibilidade, bloqueio, cor, nome, opacidade e ordem; inspector recolhível; campos vetoriais; estados de erro, foco e dirty; atalhos; ausência de comandos duplicados sem função contextual definida.

**Encerramento:** revisão visual humana aprovada em todas as resoluções do contrato e checklist de usabilidade concluído.

### Fase 6 — 2.5D

**Objetivo:** entregar composição profissional com profundidade.

**Obrigatório:** câmera ortográfica, profundidade, parallax, limites de câmera, preview e runtime equivalentes.

**Encerramento:** cena de referência com deslocamento de câmera, diferença visual mensurável entre profundidades e comparação editor/runtime aprovada.

### Fase 7 — Iluminação real

**Objetivo:** produzir iluminação visual real, não apenas dados de iluminação.

**Obrigatório:** luz ambiente, direcional e pontual; cor; intensidade; alcance; integração com texturas e materiais.

**Encerramento:** capturas antes/depois demonstram alteração de pixels; editor e runtime passam; fallback é identificado.

### Fase 8 — Partículas reais

**Objetivo:** produzir VFX visualmente renderizado.

**Obrigatório:** emissão, ciclo de vida, velocidade, gravidade, cor, escala, textura, blend, seed, pausa, step, replay e limites.

**Encerramento:** partículas aparecem em captura; seed produz replay reproduzível; teste de estresse passa.

### Fase 9 — Playback e runtime

**Objetivo:** transformar preview em reprodução real.

**Obrigatório:** play, pause, stop, step, fixed timestep, replay, eventos, telemetria e exportação.

**Encerramento:** execução fora da UI, reprodutibilidade, diagnóstico de erro e comparação visual aprovados.

### Fase 10 — Composição avançada

**Objetivo:** integrar máscaras, blending e pós-processamento.

**Encerramento:** cada pass possui ordem, custo, teste visual, fallback e documentação.

### Fase 11 — Distribuição

**Objetivo:** entregar software instalável e reproduzível.

**Encerramento:** instalação limpa em Windows/Linux, manifesto, hashes, recursos localizados, logs e recuperação de projeto aprovados.

### Fase 12 — Qualidade de release

**Objetivo:** comprovar estabilidade profissional.

**Encerramento:** testes unitários, integração, visual golden, desempenho, memória, stress, longa duração, compatibilidade, segurança de arquivos e empacotamento aprovados.

### Fase 13 — Revisão humana e Release Profissional 2.5D

**Objetivo:** validar o produto completo por fluxos reais.

**Encerramento:** checklist humano, build candidata, relatório de limitações, aprovação formal e baseline final encadeada.

## 9. Requisitos de renderização real

Um efeito será considerado renderizado somente quando cumprir simultaneamente todos os itens:

1. implementação no renderer;
2. alteração efetiva dos pixels;
3. presença em captura de frame;
4. acesso pelo fluxo de usuário previsto;
5. persistência;
6. teste automatizado ou contrato verificável;
7. equivalente no runtime quando exigido;
8. backend e fallback registrados.

Se um item faltar, o efeito será classificado como **PENDENTE** ou **PARCIAL**, nunca como concluído.

## 10. Testes e pacote de evidências

Cada fase deverá produzir um pacote contendo:

- commit exato;
- build exata;
- manifesto de arquivos;
- versões de dependências;
- logs completos;
- resultados JUnit;
- testes funcionais;
- capturas visuais;
- hashes das capturas;
- FPS, frame time e memória;
- matriz requisito–teste–artefato;
- limitações encontradas;
- relatório de fallback;
- aprovação humana quando aplicável.

Os testes obrigatórios são unitários, integração, schema, persistência, migração, renderer, visual golden, Windows/Linux, GPU/fallback, desempenho, memória, stress, longa duração, arquivos inválidos, assets ausentes e empacotamento limpo.

## 11. Metas de desempenho

As metas abaixo deverão ser medidas no hardware oficial definido antes da Fase 2:

- 60 FPS em 1080p na cena 2.5D de referência;
- p95 de frame menor ou igual a 16,7 ms;
- ausência de crescimento contínuo de memória em sessão prolongada;
- carregamento dentro do limite aprovado para a cena de referência;
- reprodução sem drift acima da tolerância definida;
- fallback visível e documentado quando a GPU não suportar uma capacidade.

O relatório deverá conter média, p95, p99, pior frame e memória inicial/final. Média isolada não será aceita como prova de desempenho.

## 12. Builds e baselines

Cada build deverá informar produto, fase, finalidade, commit, sistema operacional, backend, schema, data e status de aprovação.

Build de auditoria histórica, desenvolvimento, vertical slice, revisão humana e release candidate não poderão compartilhar nome ou diretório.

Cada baseline deverá conter manifesto, hashes, testes, limitações e vínculo com a baseline anterior. Um artefato de uma fase não poderá ser usado como prova de outra sem identificação explícita.

## 13. Critérios de bloqueio

O encerramento será bloqueado quando existir:

- requisito sem teste ou evidência;
- recurso visual substituído por marcador ou simulação;
- fallback não registrado;
- divergência editor/runtime não medida;
- perda de dados ao salvar/reabrir;
- regressão histórica;
- build sem identidade;
- teste em commit diferente do auditado;
- artefato sem hash ou origem;
- revisão humana incompleta;
- limitação conhecida omitida.

O bloqueio permanecerá até que exista correção e nova comprovação.

## 14. Release Profissional 3D

O Release Profissional 3D somente poderá ser declarado depois de cumprir todos os requisitos abaixo:

- câmera perspectiva;
- coordenadas 3D;
- malhas renderizadas;
- materiais 3D;
- profundidade real;
- iluminação 3D;
- seleção e gizmos 3D;
- importação e persistência de asset 3D;
- playback e exportação;
- testes visuais e de desempenho;
- revisão humana em cena 3D de referência.

Até então, a documentação deverá declarar somente compatibilidade arquitetural planejada ou suporte parcial, conforme a evidência disponível.

## 15. Encerramento formal sem precedentes

O release somente será declarado concluído nesta sequência obrigatória:

1. requisitos implementados;
2. testes executados no commit correto;
3. artefatos gerados e hashados;
4. limitações registradas;
5. regressão das etapas históricas aprovada;
6. build limpa instalada e executada;
7. revisão humana concluída;
8. aprovação formal registrada;
9. commit final criado;
10. baseline final encadeada;
11. documentação de capacidades atualizada;
12. nenhuma pendência crítica ou alta aberta.

Sem os doze itens, o status oficial permanecerá **EM DESENVOLVIMENTO**. Não haverá encerramento provisório, encerramento implícito, encerramento por aparência, encerramento por intenção ou encerramento por ausência de falha aparente.
