# Plano completo de desenvolvimento por etapas

> **CLASSIFICAÇÃO DOCUMENTAL — ROADMAP HISTÓRICO SUPERADO:** este plano antecede o `docs/PLANO_MESTRE_ESTABILIZACAO.md` e contém recomendações que não são o toolchain vigente, como `uv` e Ruff. Não o use para iniciar etapas ou alterar dependências sem decisão formal. A atividade chamada aqui de Etapa 12 corresponde à Etapa 14 do plano mestre e possui candidato técnico local pré-merge; isso não aprova release.

## Princípios obrigatórios

1. preservar o ZIP original como evidência;
2. trabalhar em cópia e branch específica;
3. patches pequenos, reversíveis e com escopo único;
4. nenhum “pronto” sem teste registrado;
5. não alterar formato de projeto sem versão e migração;
6. separar correção, refatoração e nova funcionalidade;
7. não refatorar todo o sistema de uma vez;
8. cada etapa possui critérios de entrada e saída;
9. qualquer regressão bloqueia a etapa seguinte;
10. entregas contêm somente arquivos novos/alterados e um patch.

## Etapa 0 — Auditoria e contenção

Objetivo: impedir perda de estado e documentar a verdade atual.

Entregas:

- auditoria técnica;
- matriz de funcionalidades;
- questionário de produto;
- plano de renomeação;
- estratégia de GitHub;
- `.gitignore`;
- `config.example.json`;
- correção do `pytest.ini`;
- correção da API `src.collision`;
- correção do gerador de snapshot.

Critério de saída:

- arquivos Python compilam;
- testes não gráficos selecionados passam;
- nenhum backup é coletado pelo pytest;
- `import src.collision` funciona;
- patch da etapa contém apenas os arquivos desta etapa.

## Etapa 1 — Congelamento do baseline e limpeza Git

Objetivo: transformar o estado atual em uma base versionada recuperável.

Ações:

1. calcular SHA-256 do ZIP original;
2. criar repositório privado novo;
3. importar o conteúdo funcional sem `.venv`, caches, logs e backups;
4. manter um manifesto dos arquivos removidos do versionamento;
5. criar tag `baseline-import`;
6. executar instalação limpa em nova pasta;
7. registrar resultados em `docs/VALIDACAO_BASELINE.md`.

Critério de saída:

- `git status` limpo;
- clone novo executa no Windows;
- ambiente criado do zero;
- testes baseline registrados;
- hash do artefato original documentado.

## Etapa 2 — Definição do produto e nome

Objetivo: impedir que arquitetura e UX sejam guiadas por funcionalidades desconexas.

Ações:

- responder `DEFINICAO_DO_PRODUTO.md`;
- definir persona principal;
- definir fluxo principal;
- fixar escopo da versão 1.0;
- escolher nome;
- verificar nome no GitHub, mecanismos de busca, domínios e bases de marcas;
- definir licença e modelo comercial;
- aprovar vocabulário de UI.

Critério de saída:

- uma declaração de produto de uma frase;
- lista fechada de funcionalidades 1.0;
- lista explícita do que fica fora;
- nome aprovado e verificado;
- decisão de licença registrada.

## Etapa 3 — Ambiente reproduzível e qualidade automática

Objetivo: garantir que todos desenvolvam e testem o mesmo sistema.

Ações recomendadas:

- migrar metadados para padrão PEP 621;
- adotar `uv.lock`;
- manter Python 3.11 na linha estável;
- definir faixas de dependência;
- configurar Ruff;
- configurar mypy gradualmente;
- adicionar pytest, pytest-qt, pytest-cov e Hypothesis;
- atualizar CI para Windows e Linux headless;
- validar dependências e licenças.

Critério de saída:

- `uv sync --locked` funciona em instalação limpa;
- lint e formatação passam;
- suíte pura passa;
- suíte Qt passa em modo offscreen e Windows;
- relatório de cobertura gerado;
- nenhuma dependência `*`.

## Etapa 4 — Contrato de domínio e formato de projeto

Objetivo: tornar dados confiáveis antes de ampliar a interface.

Nova separação sugerida:

```text
src/<pacote_novo>/
├── domain/
│   ├── scene.py
│   ├── geometry.py
│   ├── layers.py
│   ├── groups.py
│   └── collisions.py
├── application/
│   ├── commands.py
│   ├── project_service.py
│   └── export_service.py
├── infrastructure/
│   ├── persistence/
│   ├── imaging/
│   ├── exporters/
│   └── logging/
└── presentation/
    └── qt/
```

Ações:

- dataclasses/modelos imutáveis onde fizer sentido;
- IDs tipados;
- invariantes geométricos centralizados;
- schema de projeto versionado;
- migração `v1 → v2`;
- gravação atômica;
- autosave e recuperação;
- testes round-trip;
- validação de limites.

Critério de saída:

- salvar e abrir preserva todos os dados;
- arquivo inválido produz erro claro sem alterar a cena atual;
- versões antigas suportadas conforme decisão;
- testes de corrupção, interrupção e migração aprovados.

## Etapa 5 — Sistema de comandos e estado

Objetivo: toda alteração relevante ser reversível e testável.

Ações:

- eliminar fallbacks manuais duplicados;
- definir interface única de comando;
- transações para operações em lote;
- rollback em falha;
- limite de memória do histórico;
- dirty state do documento;
- undo/redo de colisões, grupos, camadas, curvas e importação.

Critério de saída:

- cada ação de edição tem teste execute/undo/redo;
- transação falha sem deixar estado parcial;
- UI não altera modelo diretamente fora dos serviços permitidos.

## Etapa 6 — Ferramentas 2D

Objetivo: consolidar uma API única de ferramenta.

Ações:

- remover duplicidade `lasso.py`/`lasso_tool.py` após teste de equivalência;
- separar lógica geométrica dos eventos Qt;
- unificar ciclo press/move/release/cancel;
- definir snapping e tolerâncias;
- finalizar PolygonEditTool;
- finalizar Bézier;
- adicionar testes com sequências de eventos;
- padronizar overlays.

Critério de saída:

- cada ferramenta possui contrato, testes e documentação;
- troca/cancelamento de ferramenta não deixa estado parcial;
- nenhuma ferramenta depende de fallback silencioso.

## Etapa 7 — Processamento de imagem e detecção

Objetivo: resultados previsíveis com presets mensuráveis.

Ações:

- separar pipeline de preprocessamento, segmentação, contorno e simplificação;
- definir três presets somente se aprovados no produto;
- criar corpus de imagens de teste com autorização de uso;
- medir IoU, erro de contorno, vértices e tempo;
- limites de resolução e memória;
- cancelamento e progresso reais;
- CPU como referência; aceleração opcional somente com ganho comprovado.

Critério de saída:

- benchmark reproduzível;
- resultado determinístico com mesma configuração;
- erros e casos sem detecção informados corretamente;
- UI permanece responsiva.

## Etapa 8 — Colisão e física

Objetivo: decidir e implementar somente o escopo aprovado.

Caminho A — editor de colisões:

- manter SAT, broadphase e exportação;
- não prometer simulação física completa.

Caminho B — simulador:

- escolher backend maduro;
- integrar dinâmica, gravidade, massa, sensores e timestep;
- manter modelo próprio apenas como adaptador.

Ações comuns:

- corrigir callback;
- implementar exportação real do painel;
- distinguir colisão côncava/convexa;
- validar winding, degeneração e holes;
- teste de estabilidade numérica.

Critério de saída:

- escopo de física explicitamente documentado;
- resultados comparados com casos de referência;
- exportações abertas nas engines prioritárias.

## Etapa 9 — Exportadores

Objetivo: transformar exportação em contratos independentes e verificáveis.

Ações:

- interface comum de exporter;
- validação antes de escrever;
- staging + commit atômico de múltiplos arquivos;
- perfis com schema próprio;
- remover código morto do GLTF;
- validar GLB com ferramenta externa e engines declaradas;
- golden files pequenos;
- testes de nomes, paths, overwrite e Unicode.

Critério de saída:

- cada formato possui testes de estrutura;
- arquivos são importados com sucesso na engine alvo;
- falha não deixa pacote parcial.

## Etapa 10 — Refatoração da interface

Objetivo: reduzir classes gigantes e tornar o produto simples de usar.

Ações:

- MainWindow somente como composição;
- controllers/presenters por painel;
- ações centralizadas;
- estado de seleção central;
- painéis dockáveis ou layout aprovado;
- sistema real de tradução Qt;
- preferências fora da raiz do projeto;
- modo simples/avançado se aprovado;
- acessibilidade, atalhos e foco.

Critério de saída:

- smoke tests de UI;
- fluxos principais concluídos sem abrir painéis técnicos desnecessários;
- telas consistentes em 100%, 125% e 150% de escala do Windows.

## Etapa 11 — Desempenho, robustez e segurança

Objetivo: controlar limites e falhas reais.

Ações:

- orçamento de memória;
- profiling de imagens grandes;
- fuzz/property tests geométricos;
- limites de arquivo/vértices/objetos;
- recuperação após arquivo corrompido;
- logs rotativos sem dados pessoais desnecessários;
- SBOM do build;
- varredura de dependências;
- modelo de ameaça;
- `SECURITY.md`.

Critério de saída:

- metas de desempenho aprovadas;
- zero crash em corpus de robustez;
- vulnerabilidades críticas conhecidas iguais a zero;
- política de dados documentada.

## Etapa 12 — Build e distribuição Windows

Objetivo: entregar aplicativo instalável e reproduzível.

Ações:

- PyInstaller em modo pasta primeiro;
- arquivo `.spec` versionado;
- build em máquina limpa/CI Windows;
- ícone, versão e metadados;
- instalador somente depois do build portátil estável;
- hash SHA-256;
- smoke test em usuário Windows limpo;
- assinatura de código quando comercialmente viável;
- atualização manual segura antes de auto-update.

Critério de saída:

- pacote abre sem Python instalado;
- importa, edita, salva, reabre e exporta projeto de teste;
- desinstalação não apaga projetos do usuário;
- build reproduzível e versionado.

Estado vigente: os critérios técnicos foram comprovados localmente no candidato `0.2.0`, exceto o requisito de usuário Windows limpo, que foi aproximado por instalação isolada no usuário atual. Assinatura, revisão jurídica, identidade visual e integração/CI permanecem abertas.

## Etapa 13 — Recursos avançados

Somente após a versão estável:

- plugins;
- 3D avançado;
- IA local;
- automação em lote;
- scripting;
- integração direta com engines;
- atualizador automático.

Cada recurso exige ADR, threat model e critério de desativação.

## Formato obrigatório de cada futura entrega

```text
Etapa/Patch:
Objetivo:
Arquivos alterados:
Motivo de cada alteração:
Testes executados:
Resultados:
Testes não executados e motivo:
Riscos restantes:
Instruções de aplicação/reversão:
```
