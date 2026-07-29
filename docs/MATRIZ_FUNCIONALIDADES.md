# Matriz de funcionalidades e estado de validação

Legenda:

- **Presente**: implementação identificada no código;
- **Parcial**: implementação incompleta, provisória ou sem fluxo completo;
- **Quebrado**: falha reproduzida;
- **Não validado**: código presente, mas sem teste suficiente nesta auditoria;
- **Validado parcialmente**: alguns testes passaram, sem validação completa de UI/integração.

| Área | Funcionalidade | Estado | Evidência / lacuna |
|---|---|---:|---|
| Aplicação | Inicialização GUI no Windows | Validado parcialmente | Aberta pelo usuário com Python 3.11.9; demais fluxos não validados |
| Aplicação | Modo headless | Presente, não validado integralmente | Argumentos em `app.py`; exportações dependem de módulos opcionais |
| Projeto | Salvar/carregar JSON | Parcial | Funciona para objetos, layers e groups; sem versão de esquema e com dados omitidos |
| Projeto | Compatibilidade entre versões | Ausente | Não há migradores |
| Projeto | Autosave/recuperação | Ausente | Não identificado |
| Cena | Objetos poligonais | Presente | Modelo e comandos existentes |
| Cena | Layers | Presente, não validado integralmente | Modelo, comandos e UI |
| Cena | Groups | Presente, não validado integralmente | Modelo, comandos e UI |
| Cena | Curvas Bézier | Parcial | Persistência ausente; amostragem provisória |
| Comandos | Undo/redo | Presente, não validado integralmente | `CommandManager` e comandos específicos |
| Comandos | Transações compostas | Presente, não validado integralmente | `CompositeCommand` |
| Seleção | Laço livre | Presente, não validado nesta auditoria | Ferramenta registrada pela paleta |
| Seleção | Laço poligonal | Presente, não validado nesta auditoria | Ferramenta registrada |
| Seleção | Laço magnético | Presente, não validado nesta auditoria | Algoritmo Sobel/Dijkstra; evento release vazio |
| Seleção | Retangular | Presente, não validado nesta auditoria | Ferramenta registrada |
| Seleção | Elíptica | Presente, não validado nesta auditoria | Ferramenta registrada |
| Edição | Caneta/Bézier | Parcial | Código presente, persistência e comportamento final incompletos |
| Edição | Edição de vértice/polígono | Parcial | Ramo de finalização de arraste não implementado |
| Edição | Expandir/contrair | Presente, não validado integralmente | Utilitário e comando existentes |
| Edição | Suavização | Validado parcialmente | Funções puras presentes; cobertura incompleta |
| Detecção | Modo basic | Validado parcialmente | Teste sintético aprovado |
| Detecção | Modo enhanced | Presente, não validado nesta auditoria | Implementação existente |
| Detecção | Modo perfect | Validado parcialmente | Fluxo testado com mocks |
| Visualização | Lit | Presente, não validado visualmente | Ação e CanvasView |
| Visualização | X-Ray 1/2/3 | Presente, não validado visualmente | Processador e worker |
| Colisão | SAT canônico | Validado parcialmente | Testes de física selecionados passaram |
| Colisão | API `src.collision` | Corrigido nesta etapa | Import quebrado reproduzido e corrigido |
| Colisão | Broadphase uniforme | Validado parcialmente | Testes selecionados passaram |
| Colisão | Sweep and Prune | Validado parcialmente | Testes específicos passaram |
| Colisão | Decomposição convexa | Presente, não validado integralmente | Algoritmo + fallback |
| Física | Teste estático de colisão | Presente, não validado em UI | PhysicsManager e painel |
| Física | Simulação dinâmica/gravitacional | Ausente como fluxo real | `gravity` não é aplicada; backend vazio |
| Física | Callback de colisão | Parcial | Registro existe; disparo não identificado |
| Exportação | Sprite PNG | Presente, não validado ponta a ponta | Exportador separado |
| Exportação | Atlas | Presente, não validado ponta a ponta | Packer e exportador |
| Exportação | JSON genérico | Presente, não validado ponta a ponta | Exportador separado |
| Exportação | Perfis Unity/Godot/Phaser | Parcial | Formatadores simples; perfil Godot sem transformação específica em um fluxo |
| Exportação | GLTF/GLB | Parcial | Implementação extensa, código morto/incompleto e ausência de validação em engine |
| Exportação | OBJ/FBX | Ausente no projeto atual | Não identificado |
| UI | Idiomas inglês/português | Parcial | Dicionário local em MainWindow; sem sistema de tradução central |
| UI | Painel de colisão | Parcial | exibição funciona por código; salvar export do sinal principal está vazio |
| UI | Interface modular | Parcial | arquivos separados, mas classes centrais grandes e acopladas |
| Qualidade | Teste unitário não gráfico | Validado parcialmente | 17 testes aprovados |
| Qualidade | Teste de UI | Não validado | PySide6 indisponível no ambiente de auditoria |
| Qualidade | CI reproduzível | Quebrado/incompatível | matriz Python contradiz `pyproject`; instalação falhava por README |
| Distribuição | Executável Windows | Ausente | não há receita de build validada |
| Segurança | Formato seguro sem pickle | Presente | JSON |
| Segurança | Limites de recursos | Ausente | sem limites centralizados de imagem/vértices/arquivo |
| Segurança | Política de vulnerabilidade | Ausente | sem `SECURITY.md` |
| Repositório | Remote Git | Ausente | nenhum remote configurado |
| Repositório | Estado limpo | Quebrado | 416 entradas no working tree |
| Licença | Licença definida | Ausente | README antigo mencionava MIT sem arquivo de licença |
