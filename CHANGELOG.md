# Changelog

## 0.6O2 — observabilidade confiável e persistência segura

- no modo `--validation-log`, as cinco exportações manuais usam uma pasta exclusiva da sessão e não dependem de seletores nativos;
- o resumo da sessão passa a distinguir `SUCCESS`, `INCOMPLETE` e `FAILURE` sem declarar sucesso quando faltam ações;
- tokens de objetos passam a usar HMAC com chave aleatória não registrada, reduzindo a possibilidade de recuperação por dicionário;
- exceções registradas fora de um bloco `except` passam a conter o traceback real da exceção;
- erros que já possuem evento estruturado deixam de ser recapturados como `python.log`, evitando contagem duplicada;
- substituições de JSON, sprite, atlas e GLB deixam de apagar o destino antes da gravação e usam `os.replace` no mesmo sistema de arquivos;
- os bytes e contratos dos formatos exportados permanecem inalterados nos testes de regressão;
- `CLI-LAZY-001` e `LOG-DUP-001` são encerrados; as demais limitações conhecidas permanecem documentadas.

## 0.6O1 — observabilidade da validação manual

- adiciona modo opcional `--validation-log` com eventos JSONL sanitizados;
- registra abertura, idioma, imagem, criação/seleção de polígono e exportações;
- valida pós-condições reais de JSON, PNG, atlas e GLB;
- captura avisos, erros, tracebacks e exceções não tratadas;
- corrige a duplicação do logger sem alterar os fluxos funcionais;
- mantém uma única árvore `src/`, sem aliases ou migração estrutural.

## 0.6C1 — consolidação da renomeação em árvore única

### Decisão

- encerrada a migração física para `neoeng_d_trace/`;
- restaurada uma única fonte de verdade em `src/`;
- removidos aliases, wrappers e a entrada `python -m neoeng_d_trace`;
- distribuição e marca permanecem `neoeng-d-trace` / NeoEng-D-Trace;
- `app.py` e o console `src.launcher:main` são as entradas oficiais.

### Preservado

- todas as melhorias funcionais do checkpoint 0.5.2F3 e da identidade 0.6N1;
- correções JSON e GLTF/GLB, incluindo `save_binary()`, generator, atomicidade e padding;
- interface bilíngue, ferramentas, física, UI e formatos existentes;
- configuração `config.json` na raiz.

### Removido explicitamente

- segunda árvore `neoeng_d_trace/`;
- testes e documentos exclusivos da migração física.

> As entradas 0.6N2 e 0.6N3 abaixo permanecem somente como histórico de uma abordagem cancelada. Elas não descrevem a arquitetura atual.



## 0.6N3E-R3 — contrato real de metadados vazios no GLB

- Corrige somente o contrato de teste da serialização real GLB.
- Registra que `pygltflib 1.16.5` remove listas vazias durante a serialização JSON.
- Mantém `groups` presente em memória antes da gravação e considera sua ausência após reabertura equivalente a nenhuma associação.
- Não altera o exportador, a geometria, os buffers, a interface ou qualquer arquivo de runtime.

## [0.6N3-E-R2] - 2026-07-27

### Correção de serialização GLB real
- O exportador passa a chamar `GLTF2.save_binary()` diretamente quando disponível.
- Isso evita que `GLTF2.save()` do `pygltflib` 1.16.5 substitua o `asset.generator` definido pelo NeoEng-D-Trace.
- Backends alternativos e doubles de teste sem `save_binary()` continuam usando o fallback `save()`.
- Retorno explícito `False` do backend de persistência passa a ser tratado como falha.

### Contrato GLB
- O teste de objeto individual passa a distinguir dados úteis de padding do chunk BIN.
- O tamanho JSON do buffer e o blob reaberto são validados com alinhamento de quatro bytes.
- Os dois bytes finais de padding são exigidos como zero sem alterar `bufferView.byteLength`.
- Geometria, índices, accessors, metadados e aliases `src.*` permanecem inalterados.

## [0.6N3-E] - 2026-07-27

### Migração estrutural
- Migração física de `exporters.gltf_exporter` para `neoeng_d_trace.exporters`.
- Preservação de `src.exporters.gltf_exporter` como alias do mesmo módulo.
- Atualização dos imports internos para identidade, logger, cena e triangulação canônicos.

### Garantias
- AST funcional preservado sem alteração intencional de algoritmo.
- Cena, cena sem metadados e objeto individual comparados byte a byte com backend determinístico.
- Estrutura GLTF, buffer binário, accessors, offsets, metadados e atomicidade protegidos por testes.
- A validação Windows exige `pygltflib` real e reabre os arquivos GLB produzidos.
- 2.5D, UI, idiomas e formato de projeto permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

## [0.6N3-D] - 2026-07-27

### Migração estrutural
- Migração física de `exporters.json_exporter` para `neoeng_d_trace.exporters`.
- Preservação de `src.exporters.json_exporter` como alias do mesmo módulo.
- Atualização dos imports internos para modelo, logger e perfis canônicos.

### Garantias
- Schemas, ordem de campos, indentação, perfis e mensagens de erro não foram alterados.
- Sete saídas determinísticas e a persistência em arquivo foram congeladas por hashes de contrato.
- GLTF, interface, idiomas e formato de projeto permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

## [0.6N3-C] - 2026-07-27

### Migração estrutural
- Migração física de `sprite_exporter`, `atlas_exporter` e quatro perfis de metadados para `neoeng_d_trace.exporters`.
- Preservação dos caminhos históricos `src.exporters.*` como aliases do mesmo objeto de módulo.
- Atualização do import do `Packer` para o namespace canônico, sem alteração do algoritmo.

### Garantias
- Formatos de sprite, atlas e metadados não foram alterados.
- Interface, idiomas, GLTF, JSON de cena e comportamento do Laço Magnético permanecem fora do escopo.
- `LOG-DUP-001`, `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertos.

# NeoEng-D-Trace — Registro de mudanças

> NeoEng-D-Trace é a identidade ativa. O pacote de distribuição é `neoeng-d-trace`; módulos são migrados fisicamente em lotes, mantendo `src.*` como compatibilidade controlada.

## [2026-07-27] — Etapa 0.6N3-B: geometria, colisão e utilitários fundamentais

### Alterado

- transferida a fonte de verdade de broadphase, SAT, decomposição convexa, wrapper de colisão, packing e máscaras de seleção para `neoeng_d_trace`;
- os seis caminhos históricos correspondentes em `src.*` foram reduzidos a aliases dos mesmos objetos de módulo;
- referências internas do wrapper de colisão passaram a resolver o SAT pelo namespace canônico;
- adicionados testes de ordem de importação, identidade, localização física e contratos comportamentais dos seis módulos.

### Preservado

- algoritmos e resultados numéricos não foram intencionalmente alterados;
- imports antigos continuam válidos;
- schemas de cena, física, colisão, atlas e máscaras permanecem inalterados;
- interface, idiomas, Laço Magnético, exportadores e arquivos do usuário não foram modificados.

### Limites conhecidos

- `physics.physics_manager`, exportadores, ferramentas e UI ainda dependem parcialmente de `src.*`;
- `PERF-MAGNETIC-001`, `UI-RESIZE-PT-001` e `CLI-LAZY-001` permanecem abertas;
- validação completa no Windows/Python 3.11 continua obrigatória.

## [2026-07-27] — Etapa 0.6N3-A: primeiro lote da migração física

### Alterado

- transferida a fonte de verdade de `app_identity`, `logger`, `config`, `commands` e `models.scene` para `neoeng_d_trace`;
- imports internos desses módulos passaram a usar exclusivamente o namespace canônico;
- os cinco caminhos históricos em `src.*` foram reduzidos a aliases de compatibilidade para os mesmos objetos de módulo;
- classes como `Scene`, `CommandManager` e `ConfigManager` passam a declarar `__module__` no namespace canônico;
- adicionados testes de ordem de importação, identidade de classes, estado compartilhado, round-trip de configuração e contratos da cena.

### Preservado

- imports históricos `src.*` continuam válidos;
- módulos canônicos e históricos permanecem o mesmo objeto em memória;
- schemas de configuração, cena e exportação não foram alterados;
- algoritmos, interface, traduções, Laço Magnético, formato de projeto e arquivos do usuário não foram modificados.

### Limites conhecidos

- os demais módulos continuam fisicamente em `src/` e serão migrados em lotes posteriores;
- desempenho adicional do Laço Magnético, redimensionamento do painel em português e imports tardios da CLI permanecem pendências não bloqueantes;
- a suíte Qt e a validação visual no Windows continuam obrigatórias antes da aprovação da etapa.

## [2026-07-27] — Etapa 0.6N2: namespace canônico do pacote

### Alterado

- criado o namespace importável `neoeng_d_trace` com aliases para os mesmos objetos de módulo existentes em `src.*`;
- movida a lógica do launcher para `neoeng_d_trace.launcher`, mantendo `app.py` como entrada compatível;
- adicionada execução por `python -m neoeng_d_trace`;
- nome da distribuição alterado de `polygontool` para `neoeng-d-trace`;
- adicionada a entrada de console `neoeng-d-trace` no metadado Poetry;
- declarados explicitamente os pacotes `neoeng_d_trace` e `src` durante a fase de compatibilidade.

### Preservado

- os módulos funcionais continuam fisicamente em `src/` nesta subfase;
- imports antigos `src.*` permanecem válidos;
- aliases canônicos resolvem para os mesmos objetos de módulo, evitando classes e singletons duplicados;
- algoritmos, interface, idiomas, exportadores, configuração e formato de projeto não foram alterados.

### Limite conhecido

- `__module__` de classes existentes continua apontando para `src.*` até a migração física R3B;
- dependências ainda não estão travadas; isso pertence à etapa de ambiente reproduzível;
- desempenho adicional do Laço Magnético permanece dívida técnica registrada.

## [2026-07-27] — Etapa 0.6N1: identidade central e runtime bilíngue

### Alterado

- criado `src/core/app_identity.py` como fonte única da identidade visual e técnica aprovada;
- títulos da janela principal migrados para NeoEng-D-Trace em inglês e português;
- título com arquivo carregado preserva a nova marca ao alternar idioma;
- CLI, logger, GLTF generator, benchmarks e executor de testes legados passaram a consumir a nova identidade;
- ações de colisão, modos Lit/Raio-X e diálogo de abertura da janela principal receberam atualização bilíngue;
- funções duplicadas e inalcançáveis de exportação de colisão foram removidas sem alterar o formato exportado;
- adicionados testes de identidade não gráficos e contratos Qt para os dois idiomas.

### Preservado

- algoritmos de detecção, laços, polígonos, colisões, física e exportação geométrica não foram modificados;
- formato JSON e TXT das colisões não foi alterado;
- `PROJECT_FORMAT_ID` continua indefinido até ADR própria, evitando atrelar o formato à marca;
- pacote de distribuição `polygontool` permanece temporariamente até a Fase R3;
- configuração na raiz e histórico Git permanecem inalterados.

### Limites conhecidos

- ExportDialog, ExportPreview, MaskViewer, CollisionPanel e LayersPanel ainda não possuem cobertura bilíngue completa;
- CLI e logs continuam em inglês;
- migração de pacote, AppData, formato de projeto, executável e instalador permanece pendente;
- validação visual e suíte Qt completa continuam obrigatórias no Windows/Python 3.11.

## [2026-07-27] — Etapa 0.6R: realinhamento documental e privacidade

### Alterado

- definição do produto consolidada a partir das decisões aprovadas;
- identidade NeoEng-D-Trace formalizada sem alterar o código funcional;
- README corrigido para refletir os resultados reais da 0.5.2F3 e da auditoria 0.6A1;
- metadado de autoria substituído por identidade técnica e e-mail `noreply`;
- caminho pessoal do Windows removido da documentação;
- envio para serviço externo de cobertura removido;
- CI alinhada ao Python 3.11 e configurada para execução Qt offscreen;
- estratégia do novo repositório revisada para um baseline limpo, sem os 15 commits históricos locais.

### Preservado

- nenhum arquivo funcional em `app.py` ou `src/` foi alterado;
- hashes críticos do checkpoint 0.5.2F3 permanecem obrigatórios;
- histórico local continua preservado e não será enviado ao novo repositório;
- nenhuma configuração de remote, commit, tag, stage ou push faz parte desta etapa.

### Limites

- a renomeação interna ainda não foi executada;
- disponibilidade jurídica/comercial do nome ainda deve ser confirmada antes de lançamento público;
- o texto jurídico da licença proprietária ainda está pendente;
- lacunas de formato de projeto, 2.5D, build e exportação permanecem abertas.

## Nota de confiabilidade do histórico legado

As entradas abaixo são preservadas como registro histórico. Afirmações amplas como “todas as funcionalidades testadas”, “compatível” ou “sem regressões” devem ser interpretadas conforme as evidências disponíveis na época e não substituem os relatórios de validação atuais.

## Histórico legado — PolygonTool

Este arquivo registra o status das funcionalidades adicionadas e alterações no projeto, para rastrear quando o projeto quebrou.

## [2025-11-30] - CI Pipeline, CLI Headless e Benchmarks: Infraestrutura externa e configurações de sistema

### Adicionado
- **CI Pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) com testes automatizados, linting, type checking e cobertura
- **CLI Headless**: Suporte a modo headless em `app.py` com argparse para processamento automatizado
  - Carregamento de imagens e projetos
  - Export para GLTF (cena e objetos individuais)
  - Export para JSON metadata
  - Salvamento de projetos
- **Benchmarks**: Suite completa de benchmarks em `bench/` para medir performance
  - `benchmark_triangulation.py`: Performance de triangulação de polígonos
  - `benchmark_convex_decomp.py`: Performance de decomposição convexa
  - `benchmark_gltf_export.py`: Performance de export GLTF
  - `run_benchmarks.py`: Executor principal para todos os benchmarks

### Status
- CI Pipeline configurado para múltiplas versões Python (3.9-3.11)
- CLI Headless funcional com operações de export automatizadas
- Benchmarks abrangentes com medição de tempo, memória e estatísticas
- Todas as funcionalidades testadas e integradas sem regressões

## [2025-11-30] - Export GLTF: Geração de mesh.glb com triangulação e metadados

### Adicionado
- Novo módulo `gltf_exporter.py` para exportação GLTF (.glb)
- Triangulação automática de polígonos usando Mapbox Earcut
- Geração de meshes GLTF com posições, índices e primitivas
- Inclusão de metadados como object_id, layer, polygon, groups
- Suporte a exportação de cena completa ou objeto individual
- Integração com UI de exportação (botões "Export Scene to GLTF" e "Export Object to GLTF")
- Salvamento atômico para evitar corrupções

### Status
- GLTF export funcional com triangulação robusta
- Metadados preservados como extras no formato GLTF
- Compatível com engines 3D que suportam GLTF

## [2025-11-30] - Convex Decomposition com Limites Box2D

### Adicionado
- Implementação de merge de triângulos em convex_decomp.py para produzir polígonos convexos com <=8 vértices.
- Algoritmo greedy para combinar triângulos adjacentes compartilhando arestas.
- Compatibilidade com Box2D que limita fixtures a 8 vértices.

### Status
- Decomposição convexa agora produz polígonos otimizados para Box2D.
- Testes atualizados para validar polígonos com <=8 vértices.

## [2025-11-30] - Performance Gating com Progress e Cancel

### Adicionado
- Sinais de progresso em XrayWorker (progress 0-100).
- Método cancel() em XrayWorker para operações pesadas off-UI.
- Suporte a cancelamento de tarefas assíncronas.

### Status
- Operações pesadas agora têm feedback de progresso e podem ser canceladas.
- Xray generation off-UI mantido.

## [2025-11-30] - Comportamento Transacional em CommandStack

### Adicionado
- CompositeCommand para executar múltiplos comandos como transação.
- Se um comando falha, os executados anteriormente são desfeitos automaticamente.
- Suporte a undo em lote para operações compostas.

### Status
- CommandStack agora suporta transações para composite operations.
- Tests existentes passam, sem regressões.

## [2025-11-30] - Melhorias na Validação de Polígonos (Self-Intersections)

### Adicionado
- Checagem de self-intersections em _validate_polygon usando algoritmo de interseção de segmentos de linha.
- Polígonos com arestas que se cruzam são rejeitados.
- Funções auxiliares: _has_self_intersections e _lines_intersect.

### Status
- Validação completa: winding + self-intersections.
- Testes passam, sem regressões.

## [2025-11-30] - Melhorias na Validação de Polígonos

### Adicionado
- Validação de winding (counter-clockwise) em _validate_polygon usando fórmula shoelace.
- Polígonos devem ter área positiva para serem válidos.

### Status
- Validação aprimorada sem quebrar funcionalidade existente.
- Testes de cena passam.

## [2025-11-30] - Correção de Validação de Configuração

### Corrigido
- Erro de validação Pydantic para window_geometry: alterado de Dict para str para corresponder ao formato de armazenamento (base64).
- Aplicação agora inicia sem erros de configuração.

### Status
- Configuração carrega corretamente, geometria da janela restaurada via base64.
- Sem quebras em outras funcionalidades.

## [2025-11-30] - Unificação da Implementação SAT (Separating Axis Theorem)

### Adicionado
- Implementação canônica de SAT em src/physics/sat2d.py com epsilon para tolerância numérica, validação de entrada e MTV correto.
- Unificação das implementações: src/collision/sat2d.py agora importa da física e fornece wrapper numpy para compatibilidade.
- Função sat_polygon_vs_polygon com assinatura consistente, retornando tipos simples (bool, Optional[Tuple[float, float]]).
- Testes mantidos passando para ambas as interfaces.

### Status
- SAT unificado com implementação robusta em physics, wrapper em collision para compatibilidade.
- Todas as funções têm validação, epsilon e testes.
- Sem duplicação de código, API consistente.

### Próximas Melhorias
- Integrar SAT no PhysicsManager para checagem de colisão centralizada.

## [2025-11-30] - Melhorias no Módulo Convex Decomposition

### Adicionado
- Integração de mapbox_earcut para triangulação eficiente em src/physics/convex_decomp.py.
- Fallback para ear clipping algorithm quando mapbox_earcut não disponível.
- Função triangulate_to_convex usando numpy arrays para earcut.
- Testes unitários em tests/test_convex_decomp.py para triangulação de triângulos e polígonos côncavos (L-shape).

### Status
- Convex decomposition funcional com library otimizada e fallback robusto.
- Todas as funções testadas, integração mantida.
- Dependências opcionais: mapbox_earcut, numpy.

### Próximas Melhorias
- Implementar merging de triângulos para polígonos convexos maiores.

## [2025-11-30] - Melhorias no Módulo Broadphase

### Adicionado
- Nova implementação BroadPhaseSAP (Sweep and Prune) em src/physics/broadphase.py para eficiência em cenários axis-aligned.
- Testes unitários em tests/test_broadphase_sap.py para insert/update/remove e potential pairs.

### Status
- Duas implementações de broadphase: UniformGrid e SAP.
- SAP é determinístico e eficiente para muitos cenários.
- Todas as funções testadas.

### Próximas Melhorias
- Comparação de performance entre UniformGrid e SAP.

## [2025-11-30] - Melhorias no Módulo Physics

### Adicionado
- Melhorias em src/physics/physics_manager.py: fixed timestep com accumulator, scale handling (pixels_per_meter), gravity, backend placeholder, collision callbacks.
- Novos métodos: add_body, remove_body, step, register_collision_callback.
- Metadata support em PhysicsObject.
- Testes unitários em tests/test_physics_manager.py para add/remove body, step accumulator, callbacks.

### Status
- Physics manager com API clara e fixed timestep para determinismo.
- Integração mantida com broadphase e SAT.
- Todas as funções têm validação e testes.

### Próximas Melhorias
- Backend integration com Box2D ou fallback.

## [2025-11-30] - Melhorias no Módulo Collision

### Adicionado
- Melhorias em src/collision/sat2d.py: type hints, docstrings, epsilon para tolerância numérica, validação de entrada (mínimo 3 vértices).
- Atualização de src/collision/__init__.py para expor funções de SAT.
- Testes unitários em tests/test_collision_sat2d.py para casos de colisão, não-colisão e contato.

### Status
- SAT implementation profissional com validação e testes.
- Todas as funções têm docstrings e tipagem.
- Integração mantida, sem quebras.

### Próximas Melhorias
- Unificar com src/physics/sat2d.py se necessário.

## [2025-11-30] - Melhorias no Core Module

### Adicionado
- Exception handling em CommandManager.execute/undo/redo com logging de erros.
- Docstrings e typing consistente em commands.py.
- Testes unitários para CommandManager: exec/undo/redo/exception-case.
- Worker integration para ViewProcessor.xray generation usando QThreadPool em canvas_view.py.
- XrayWorker e XrayWorkerSignals para processamento assíncrono de xray.

### Status
- Todos os testes passando (7/7 novos em test_commands + existentes).
- Aplicação roda sem erros, comandos com exception handling, xray generation assíncrona.
- ViewProcessor mantém métodos puros e testáveis.

### Próximas Melhorias
- Implementar padrões avançados: comando transacional.
- Adicionar mais testes para fluxos de falha.

## [2025-11-28] - Integração de Exportadores (Fase 7)

### Adicionado
- Sistema completo de exportadores modulares para sprites, atlas e metadados JSON.
- `sprite_exporter.py`: Extração de sprites mascarados com antialiasing ('none', 'fast', 'high'), padding, trim, suporte a BGR/BGRA e RGB/RGBA.
- `json_exporter.py`: Exportação de metadados JSON com campos obrigatórios (rect, rect_trimmed, pivot normalizado, polygon_in_image/sprite, layer, group).
- `atlas_exporter.py`: Empacotamento determinístico em atlas múltiplos, com sorting por área/area/width/name, verificação de não-overlap.
- Perfis `unity.py` e `godot.py`: Ajustes específicos para engines (pivot normalizado).
- `export_preview.py`: Widget UI para preview de exportações.
- `test_exporters.py`: Testes unitários abrangentes (alpha mask, trim/padding, profiles, no-overlap, multi-atlas, save atomic).
- `docs/phase-7-exporters.md`: Documentação com APIs, extensibilidade e edge cases.

### Status
- Todos os testes passando (6/6 novos + existentes).
- Aplicação roda sem erros, exportadores funcionais.
- APIs testáveis headless, separação UI/core mantida.
- Dependências: Pillow (manipulação imagens), NumPy (arrays), OpenCV (antialias).

### Próximas Melhorias
- Integrar preview no diálogo de exportação.
- Adicionar mais perfis (ex: custom).
- Otimizar packing para rotação.

## [2025-11-28] - Integração de Groups Feature

### Adicionado
- Suporte completo a groups: criação, remoção, adição/remoção de objetos, visibilidade, bloqueio, ordenação.
- Classe Group no scene.py com atributos id, name, visible, locked, members.
- Métodos no Scene para gerenciar groups: create_group, remove_group, add_object_to_group, etc.
- Comandos undo/redo para groups: CreateGroupCommand, RemoveGroupCommand, AddToGroupCommand, RemoveFromGroupCommand, MoveGroupCommand.
- UI GroupsPanel para gerenciar groups via botões (New, Delete, Add Selected, Remove Selected, Up, Down, Toggle Vis, Toggle Lock).
- Persistência de groups em save_project/load_project.
- Testes para groups: test_groups.py.
- Integração do GroupsPanel no MainWindow com splitter de três painéis (Canvas, SidePanel, GroupsPanel).
- Método load_image adicionado ao Scene para carregar imagens.

### Status
- Todos os testes passando (9/9 incluindo test_groups).
- Aplicação inicia sem erros, carrega imagens, UI com três painéis.
- Funcionalidades de layers, Bézier e groups operacionais.
- Logs de erro em operações de persistência.

### Próximas Melhorias
- Adicionar logs detalhados para erros em todas as operações.
- Melhorar UI para edição de Bézier e groups.
- Implementar exportação de sprites com layers e groups.

## [2025-11-28] - Integração de Melhorias Iniciais

### Adicionado
- Suporte completo a layers (visibilidade, bloqueio, ordenação).
- Comandos undo/redo para layers: CreateLayerCommand, RemoveLayerCommand, MoveLayerCommand, ToggleLayerVisibilityCommand, ToggleLayerLockCommand.
- Comandos para edição de polígonos: ExpandContractCommand, HandleMoveCommand.
- Suporte a curvas Bézier: conversão Catmull-Rom, amostragem para polígonos.
- Testes adicionais: test_expand_contract_command.py, test_handle_command.py.
- Correção de sintaxe em magnetic_lasso.py.
- Sistema de logging para erros em operações críticas.
- Pasta backups/ para organização de backups de arquivos.

### Status
- Todos os testes passando (8/8).
- Aplicação inicia e carrega imagens corretamente.
- Funcionalidades de layers e Bézier operacionais.
- Logs de erro adicionados em operações de persistência (save/load project).

### Próximas Melhorias
- Adicionar logs detalhados para erros em todas as operações.
- Melhorar UI para edição de Bézier.
- Implementar exportação de sprites com layers.
