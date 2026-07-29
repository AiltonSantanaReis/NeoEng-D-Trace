# Auditoria técnica do projeto — 27 de julho de 2026

## 1. Escopo e fonte de verdade

Esta auditoria usa exclusivamente o conteúdo do ZIP recebido, incluindo o estado atual dos arquivos e do repositório Git interno.

Não foram tratados como verdade:

- afirmações antigas do changelog sem nova validação;
- arquivos compilados `.pyc`;
- resultados de testes armazenados em cache;
- cópias dentro de `backup/`;
- documentação que descreve recursos não comprovados pelo código atual.

## 2. Limites da auditoria

Foi possível:

- inspecionar a árvore completa;
- analisar código e histórico Git;
- compilar sintaticamente os arquivos Python;
- executar testes não gráficos compatíveis com o ambiente de auditoria;
- verificar importações de módulos sem Qt;
- comparar documentação com implementação.

Não foi possível no ambiente de auditoria:

- abrir a interface PySide6;
- validar interação real com mouse, teclado, janelas e diálogos;
- gerar um executável Windows;
- executar toda a suíte gráfica, pois PySide6 não estava instalado no ambiente Linux usado para a auditoria;
- confirmar visualmente todos os modos X-Ray e ferramentas.

A aplicação foi aberta no Windows pelo usuário com Python 3.11.9. Essa validação confirma a inicialização, mas não substitui testes funcionais de cada recurso.

## 3. Resumo executivo

### Classificação atual

**Protótipo de engenharia funcional, ainda não pronto para distribuição, venda ou repositório público.**

O projeto possui uma quantidade relevante de funcionalidades e uma separação inicial por módulos, mas a confiabilidade é comprometida por problemas de reprodutibilidade, higiene do repositório, documentação divergente, testes incompletos e acoplamento excessivo entre interface, ferramentas e modelo.

### Pontos positivos confirmados

- estrutura `src/` dividida por responsabilidade;
- uso de PySide6, NumPy, OpenCV, Pillow e Pydantic;
- command pattern para parte das operações;
- persistência de cena em JSON;
- algoritmos próprios de geometria, colisão e broadphase;
- exportadores separados por módulo;
- ferramentas especializadas separadas em arquivos;
- modo headless existente em `app.py`;
- escrita atômica presente na configuração e em partes dos exportadores;
- 17 testes não gráficos selecionados aprovados;
- compilação sintática de `app.py`, `src/` e testes concluída sem erro.

### Veredito

A base pode ser preservada. Não há justificativa técnica para reescrever tudo do zero agora. A estratégia correta é estabilizar, definir o produto e refatorar por fronteiras, mantendo testes de regressão.

## 4. Evidências quantitativas

Métricas calculadas excluindo `.git`, `.venv`, caches e cópias de `backup/`:

- 72 arquivos Python analisados;
- aproximadamente 14.530 linhas Python;
- arquivos mais extensos:
  - `src/ui/mask_viewer.py`: 896 linhas;
  - `src/ui/canvas_view.py`: 841 linhas;
  - `src/models/scene.py`: 646 linhas;
  - `src/ui/main_window.py`: 553 linhas;
  - `src/ui/side_panel.py`: 535 linhas;
  - `src/tools/auto_detect.py`: 513 linhas;
  - `src/core/commands.py`: 459 linhas;
- 95 blocos que capturam `Exception` de forma ampla;
- 29 ocorrências de `pass`, incluindo métodos abstratos legítimos, fallbacks e funcionalidades incompletas;
- 60 referências textuais ao nome antigo em 18 arquivos relevantes;
- tamanho extraído aproximado do projeto: 1,2 GB;
- 10.201 arquivos no pacote extraído;
- 145 arquivos `.pyc` rastreados no histórico Git;
- 416 entradas no estado de trabalho Git:
  - 124 modificadas;
  - 105 apagadas;
  - 187 não rastreadas;
- nenhum `remote` Git configurado.

## 5. Testes realmente executados

### Compilação sintática

Comando equivalente:

```text
python -m compileall -q -f app.py src tests test_gui_interaction.py test_physics_core.py
```

Resultado: aprovado.

### Testes não gráficos

Executados:

- `tests/test_auto_detect.py`;
- `tests/test_broadphase_sap.py`;
- `tests/test_scene_repair.py`;
- `test_physics_core.py`.

Resultado: **17 aprovados**.

### Suíte completa antes da correção do `pytest.ini`

Resultado: abortou durante a coleta ao entrar em `backup/backup/test_physics_core.py` e executar `sys.exit(1)`.

Causa confirmada: o arquivo `pytest.ini` usava a seção `[tool:pytest]`, inválida para um arquivo chamado `pytest.ini`; com isso, `testpaths` e `norecursedirs` não eram aplicados.

### Suíte `tests/` no ambiente de auditoria

Resultado: quatro erros de coleta por ausência de PySide6 no ambiente de auditoria. Não se trata de prova de defeito do código do Windows, mas impede declarar a suíte completa como aprovada.

## 6. Bloqueadores críticos — prioridade P0

### P0-01 — Estado Git não reproduzível

O ZIP contém um repositório com centenas de mudanças fora de commit. Não existe uma referência limpa que represente exatamente o aplicativo que abriu no Windows.

Risco:

- perda de arquivos durante limpeza;
- comparação de versões incorreta;
- impossibilidade de reverter uma mudança com segurança;
- publicação acidental de caches, caminhos pessoais e cópias antigas.

Ação obrigatória:

1. preservar o ZIP original sem alteração;
2. criar uma cópia de trabalho;
3. remover artefatos da área de versionamento sem apagar a cópia original;
4. executar testes;
5. criar um commit de baseline com inventário e hash do ZIP.

### P0-02 — Repositório contaminado

Há `.pyc`, `.coverage`, logs, caches, arquivos de teste antigos, `.venv`, backups recursivos e relatórios gerados.

O arquivo `project_context.txt` possui cerca de 70 MB e aparece três vezes devido à cópia recursiva em `backup/backup`.

Causa confirmada no gerador:

- ignorava `backups`, mas a pasta real é `backup`;
- ignorava `venv`, mas a pasta real é `.venv`;
- não impunha limite de tamanho por arquivo.

Ação aplicada nesta etapa: atualização de `pack_for_ai.py` e criação de `.gitignore`.

### P0-03 — Dependências não reproduzíveis

O `pyproject.toml` usa `*` para praticamente todas as dependências e não há lockfile válido entregue.

Risco:

- uma instalação futura pode receber versões incompatíveis;
- testes passam em uma máquina e falham em outra;
- builds não são reproduzíveis.

Ação futura:

- fixar faixa compatível;
- gerar lockfile;
- testar instalação limpa no Windows;
- registrar versões exatas do build de distribuição.

### P0-04 — Documentação contraditória

O README rastreado foi apagado no estado atual. O `pyproject.toml` apontava para `README_pt.md`, que não existe.

O README antigo afirmava, sem corresponder ao estado atual:

- todos os testes passando;
- licença MIT, embora não exista arquivo de licença;
- arquitetura MVC consolidada;
- MaxRects, enquanto o código atual utiliza outra estratégia de packing;
- Python 3.8+, enquanto o `pyproject.toml` exige Python 3.11;
- caminhos e nomes de funções que não coincidem com a implementação atual.

Ação aplicada nesta etapa: README substituído por um documento de estado verificável e referência corrigida no `pyproject.toml`.

### P0-05 — API de colisão quebrada

`src/collision/__init__.py` tentava importar `project_polygon` e `overlap_intervals` de `src/collision/sat2d.py`, mas esse arquivo não exportava esses nomes.

Resultado comprovado:

```text
ImportError: cannot import name 'project_polygon' from 'src.collision.sat2d'
```

Ação aplicada nesta etapa: exportar as funções canônicas de `src.physics.sat2d` e manter `polygon_collision_sat` como wrapper de compatibilidade.

### P0-06 — Formato de projeto sem contrato de compatibilidade

`Scene.save_project()` grava JSON sem:

- versão de esquema;
- identificador do aplicativo;
- migrações;
- checksum;
- persistência do caminho da imagem;
- persistência de curvas Bézier;
- persistência das geometrias de colisão independentes; são salvos apenas IDs e as formas são reconstruídas a partir do polígono principal.

Risco:

- perda silenciosa de dados;
- impossibilidade de evoluir o formato;
- incompatibilidade entre versões futuras.

Ação obrigatória antes de release: criar esquema versionado, validação e testes de round-trip/migração.

### P0-07 — Funcionalidades declaradas mas incompletas

Exemplos confirmados:

- `MainWindow._on_collision_export()` está vazio;
- o painel de colisão exibe JSON em um diálogo, mas o sinal conectado à janela não salva arquivo;
- `PhysicsManager` possui `gravity`, callbacks e `backend`, porém a gravidade não é aplicada, os callbacks registrados não são disparados e o backend é apenas uma referência vazia;
- `PolygonEditTool.on_mouse_release()` contém um ramo explicitamente não implementado;
- `sample_beziers_to_polygon()` está descrito no próprio código como solução provisória e usa apenas o primeiro ponto de cada segmento;
- o exportador GLTF contém um laço antigo incompleto com `pass` antes de uma segunda implementação;
- o perfil Godot em `json_exporter.py` não aplica transformação específica;
- existem duas classes diferentes chamadas `LassoTool` em `lasso.py` e `lasso_tool.py`, mas somente uma está registrada na paleta atual.

Esses itens não devem ser descritos como finalizados.

## 7. Problemas de arquitetura — prioridade P1

### P1-01 — Interface com responsabilidades excessivas

`MainWindow`, `CanvasView`, `MaskViewer`, `SidePanel` e `Scene` acumulam responsabilidades de:

- apresentação;
- coordenação;
- leitura/escrita;
- validação;
- ferramentas;
- processamento de imagem;
- física;
- exportação.

Consequência: alterações pequenas exigem conhecer muitos componentes e aumentam o risco de regressão.

### P1-02 — Acoplamento direto ao Qt

Ferramentas importam eventos, painter e elementos de UI. Isso dificulta testar algoritmos sem PySide6.

Direção recomendada:

- eventos da UI convertidos para comandos de domínio simples;
- algoritmos puros fora do Qt;
- adaptadores Qt finos;
- serviços independentes para detecção, persistência, colisão e exportação.

### P1-03 — Tratamento amplo de exceções

Há 95 capturas amplas de `Exception`. Algumas são apropriadas em fronteiras de UI, mas várias ocultam a causa ou ativam fallback silencioso.

Direção recomendada:

- exceções específicas no domínio;
- log com contexto e stack trace;
- fallback somente quando definido por contrato;
- erro visível quando um resultado pode estar incorreto.

### P1-04 — APIs duplicadas e compatibilidade informal

Exemplos:

- `src.physics.sat2d` e `src.collision.sat2d`;
- duas classes `LassoTool`;
- cópias `.backup` dentro de `src`;
- fallbacks manuais que repetem a lógica de comandos;
- testes antigos apagados e novos testes não rastreados.

### P1-05 — Configuração local dentro da raiz

`config.json` contém caminho absoluto e geometria da janela da máquina do usuário.

Direção recomendada:

- defaults no pacote;
- configuração do usuário em `%LOCALAPPDATA%/<nome-do-produto>/config.json`;
- `config.example.json` no repositório;
- migração automática do arquivo antigo.

### P1-06 — CI incompatível com a própria configuração

O workflow recebido testa Python 3.9, 3.10 e 3.11, mas o `pyproject.toml` exige `^3.11`.

Ele também tenta instalar o projeto em modo editável, o que falhava porque o README declarado não existia.

## 8. Segurança e confiabilidade

### Pontos atuais favoráveis

- nenhum `eval()` ou `exec()` dinâmico real foi identificado;
- dados de projeto são JSON, não pickle;
- algumas gravações são atômicas;
- não foi identificada execução automática de código de projeto carregado.

### Riscos a tratar

- ausência de limites de tamanho, quantidade de vértices e dimensão de imagens;
- arquivos JSON carregados sem schema de projeto;
- exportações podem sobrescrever caminhos escolhidos sem política uniforme de backup;
- logs e mensagens de erro não seguem política de dados sensíveis;
- não existe política de segurança, modelo de ameaça ou processo de relato de vulnerabilidade;
- dependências não travadas impedem auditoria de cadeia de suprimentos;
- a futura arquitetura de plugins, se adotada, executará código e exigirá assinatura/permissões ou aviso explícito.

## 9. Recomendação de produto

O código atual é mais coerente como:

> **Estúdio desktop offline para transformar imagens em sprites, contornos, polígonos e colisões prontos para engines de jogos.**

Recomendação de escopo:

- manter edição de imagem e geometria 2D como núcleo;
- tratar 3D inicialmente como extrusão/mesh/exportação, não como concorrente de Blender;
- priorizar fluxo “importar → detectar → corrigir → colisão → exportar”;
- oferecer presets para Godot, Unity e formatos genéricos;
- adiar plugins e automação avançada até a API interna estar estável;
- não usar “IA” como promessa comercial enquanto não houver modelo real, métrica e fallback definidos.

A decisão final depende das respostas em `DEFINICAO_DO_PRODUTO.md`.

## 10. Modernização recomendada

### Manter

- Python 3.11 durante a estabilização;
- PySide6;
- NumPy;
- OpenCV;
- Pillow;
- Pydantic;
- Shapely como backend geométrico validado;
- mapbox-earcut com fallback testado.

### Adotar gradualmente

- `uv` e `uv.lock` para ambiente reproduzível;
- Ruff para lint e formatação;
- pytest-qt para interação PySide6;
- Hypothesis para invariantes geométricos e round-trip;
- platformdirs para configuração, cache e logs;
- coverage.py para cobertura com limites por módulo;
- PyInstaller inicialmente em modo diretório para build Windows reproduzível.

### Não adotar agora

- troca completa para Qt Quick/QML;
- reescrita em C++/Rust;
- arquitetura de microserviços;
- banco de dados;
- sistema de plugins aberto;
- serviços em nuvem obrigatórios;
- frameworks de IA pesados sem caso de uso definido.

## 11. Critérios mínimos para chamar de produto final

1. instalação limpa e reproduzível no Windows;
2. projeto abre e salva sem perda de dados;
3. migração entre versões de arquivo;
4. suíte unitária, integração e UI aprovadas;
5. ferramentas principais testadas com imagens reais e sintéticas;
6. exportações validadas nas engines declaradas;
7. limites e mensagens de erro definidos;
8. build assinado ou, no mínimo, hash e origem verificáveis;
9. licença e política de privacidade definidas;
10. manual do usuário atualizado;
11. nenhum bloqueador P0 aberto;
12. changelog gerado a partir de mudanças realmente validadas.

## 12. Próximo passo obrigatório

Responder `DEFINICAO_DO_PRODUTO.md`. O nome e a refatoração estrutural dependem dessas decisões. Até lá, o nome PolygonTool é mantido somente como identificador provisório para evitar uma migração duplicada.
