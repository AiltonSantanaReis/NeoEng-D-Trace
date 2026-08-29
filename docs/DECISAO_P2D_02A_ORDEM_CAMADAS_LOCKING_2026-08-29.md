# NeoEng-D-Trace — Decisão P2D-02A: ordem visual, camadas e bloqueio seguro

**Status:** ATIVO — subestágio autorizado para implementação local
**Data:** 29/08/2026 (UTC-03)
**Linha:** P2D-COMP-01 — editor profissional de composição 2D baseado em objetos
**Etapa-mãe:** P2D-02 — ordem visual, camadas, grupos e isolamento
**Baseline de entrada:** `eb941e60a06a065c54433f852970a50b7ebeb56a`
**Branch:** `modernization/multiaxis-ui`
**Contrato normativo:** `docs/NEOENG_EDITOR_COMPOSICAO_2D_NORMATIVO_2026-08-27.md`
**Plano de evolução:** `docs/PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md`

## 1. Motivo da abertura

O fluxo foi exercitado como uma usuária do editor profissional, com janela Qt
real em modo de teste e dois objetos sobrepostos em camadas distintas. A
auditoria reproduziu os seguintes fatos:

| Fluxo | Resultado observado | Classificação |
|---|---|---|
| Abrir projeto salvo e acessar o editor profissional | janela, viewport, biblioteca e layer stack disponíveis | PASS de disponibilidade |
| Selecionar uma camada | objetos da camada são selecionados | PASS funcional existente |
| Reordenar a camada | a lista persistida muda, mas os itens gráficos mantêm `zValue=10.0` | FINDING P2D-015 |
| Ocultar uma camada | os objetos da camada desaparecem do viewport | PASS funcional existente |
| Bloquear uma camada e tentar arrastar seu objeto | o caminho de interação propaga `PermissionError` técnico | FINDING P2D-028 |
| Procurar grupos no editor profissional | não há superfície de grupos nem wrappers de sessão | FORA DE P2D-02A; reservado a P2D-02B |

Registro compactado da prova:

```text
professional_editor_available=True
asset_library_available=True
layer_stack_available=2
group_surface_count=0
initial_z_values={background_object: 10.0, foreground_object: 10.0}
after_layer_reorder_z_values={background_object: 10.0, foreground_object: 10.0}
after_visibility_off_viewport_items=[background_object]
locked_drag_probe=PermissionError: layer '<id>' is locked
session_group_api=False
window_group_stack=False
```

Nenhuma alteração de produto foi feita para produzir essa prova. Ela é a
caracterização de entrada de P2D-02A.

## 2. Decisão de engenharia

P2D-02A implementará somente a parte de P2D-02 que pode ser fechada com
semântica determinística e sem criar uma hierarquia incompleta:

1. a ordem das camadas será a ordem canônica de desenho `back → front`;
2. a camada no índice `0` é desenhada primeiro e fica atrás das camadas de
   índice maior;
3. objetos que pertencem à mesma camada preservam a ordem de `document.objects`;
4. o `zValue` do `QGraphicsItem` será uma prioridade visual derivada do índice
   da camada, nunca do valor persistido de `transform.position.z`;
5. `transform.position.z` continuará sendo preservado literalmente no schema,
   no modelo, no save/load e nos adapters existentes; não será reinterpretado
   como z-order nesta subetapa;
6. qualquer reorder de camada deverá produzir efeito visual imediato, atualizar
   a projeção determinística e permanecer no histórico undo/redo;
7. visibilidade continuará sendo uma propriedade persistida da camada e deverá
   remover imediatamente os objetos da camada do viewport e do preview;
8. lock continuará sendo uma proteção de edição, não de seleção: a usuária pode
   selecionar e inspecionar um objeto bloqueado, mas uma tentativa de transformar
   deverá ser rejeitada sem exceção não tratada, sem alteração do documento e
   sem criar transação parcial;
9. a UI deverá informar a semântica `Back → Front` e o motivo de uma edição
   bloqueada com mensagem compreensível;
10. não haverá alteração no editor principal, no modelo legado `Scene`, nos
    menus globais, nos atalhos globais ou nas linhas independentes futuras.

Essa decisão preserva o comportamento de ordenação já representado por
`Scene.render_list()` e pela construção de camadas do factory, sem afirmar que
o campo `z` já seja uma implementação 2.5D.

## 3. Escopo obrigatório de P2D-02A

### Incluído

- função única e testável para derivar prioridade visual a partir da ordem das
  camadas;
- ordem efetiva no `SceneAuthoringViewport`;
- atualização do viewport quando a ordem de camadas muda;
- ordem efetiva no `build_scene_authoring_preview`;
- preservação da ordem dos objetos dentro de cada camada;
- visibilidade, rename e reorder com feedback de UI mantidos;
- bloqueio seguro de arrasto e de transformação por gizmo;
- mensagens de bloqueio sem traceback técnico para a usuária;
- testes Qt/modelo/preview e fluxo de usuária;
- captura visual dedicada do fluxo antes/depois do reorder, visibility e lock;
- requalificação da suíte completa e dos gates previstos para o estágio.

### Explicitamente fora de P2D-02A

- grupos, desagrupamento, hierarquia de objetos e membership editing;
- isolamento de camada/grupo e modo solo;
- pastas, tags e filtros de hierarquia;
- alteração de `position.z`, profundidade 2.5D ou câmera 3D;
- seleção por teclado, nudge, duplicate, copy/paste, marquee e fit, que são
  P2D-03;
- tilemap, colisão de cenário, NavMesh, entidades/prefabs, iluminação e VFX;
- alteração de formatos V1/V2, migração ou adapters de engine;
- mudança de tolerâncias, auditorias, baselines ou evidência histórica;
- alteração de qualquer superfície fora do editor profissional dedicado.

Os itens fora do escopo não serão simulados por flags sem comportamento real e
não serão marcados como concluídos por esta subetapa.

## 4. Invariantes e não regressão

Durante P2D-02A deverão permanecer invariáveis:

- IDs de objetos, assets, camadas e sockets;
- conteúdo e hash dos assets;
- `transform.position`, inclusive `z`, rotação, escala, pivot e flips;
- mappings de ações, nomes acessíveis e semântica de comandos do editor
  principal;
- schema e compatibilidade V1/V2;
- parallax, câmera, sockets e preview read-only fora da ordenação declarada;
- histórico transacional: falha de edição não pode aumentar `undo_count`,
  limpar `redo` ou deixar o gesto ativo;
- estado de arquivos não tracked e artefatos históricos locais;
- C3 e todos os seals/baselines já aceitos.

## 5. Critérios verificáveis de aceite da subetapa

P2D-02A só poderá ser marcada como aceita se todos os itens abaixo forem
comprovados no mesmo estado de código:

1. dois objetos sobrepostos em camadas distintas mudam de cobertura visual
   quando a camada é reordenada;
2. a ordem observada no viewport coincide com a ordem declarada no preview;
3. o reorder é persistido e recuperado sem drift após save/load;
4. objetos da mesma camada preservam a ordem determinística documentada;
5. visibility remove/recoloca a camada sem apagar ou alterar seus objetos;
6. rename e reorder têm feedback compreensível e uma transação undo/redo;
7. arrastar objeto de camada bloqueada não lança exceção, não altera posição,
   não gera histórico e apresenta mensagem amigável;
8. gizmo/transformação de seleção bloqueada tem o mesmo comportamento seguro;
9. o fluxo de usuária é testado por Qt em pelo menos uma resolução lógica e
   capturado em Windows para revisão visual;
10. `git diff --check`, testes focados, suíte completa, auditoria visual e
    gates aplicáveis passam sem relaxamento;
11. a revisão humana não encontra deslocamento, clipping, mudança de geometria
    ou regressão fora do viewport profissional;
12. o commit contém apenas os arquivos pertencentes a P2D-02A e é identificável
    por evidência.

## 6. Plano de execução obrigatório

1. criar o contrato técnico da prioridade visual e testes de caracterização;
2. implementar a prioridade visual no preview e no viewport;
3. implementar a reação de sincronização ao reorder;
4. tornar rejeições de lock seguras e compreensíveis;
5. executar testes focados e simulação do fluxo de usuária;
6. executar captura Windows, auditoria e comparação estrutural/visual;
7. revisar o diff final e comprovar a fronteira de arquivos;
8. somente com todos os gates PASS, realizar commit;
9. requalificar o commit, gerar build/evidências quando aplicável e registrar
   decisão ACCEPTED ou REJECTED.

## 7. Rollback

O retorno operacional desta subetapa é o commit de entrada
`eb941e60a06a065c54433f852970a50b7ebeb56a`. Antes do commit, toda alteração
deverá ser descartável por restauração controlada dos arquivos explicitamente
modificados, sem tocar untracked. Depois do commit, o retorno só poderá ocorrer
por decisão explícita e operação Git autorizada; nenhum reset destrutivo será
executado implicitamente.

## 8. Aprovação de abertura

Esta decisão registra a abertura técnica de P2D-02A, não o aceite da etapa. O
aceite dependerá exclusivamente dos critérios, testes, evidências e revisão
humana definidos acima. P2D-02B — grupos e isolamento — será aberto apenas
depois que P2D-02A estiver aceita ou formalmente rejeitada.
