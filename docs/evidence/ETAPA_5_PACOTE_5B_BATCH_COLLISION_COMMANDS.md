# Evidência — Etapa 5, Pacote 5B: lotes e colisões transacionais

## Base

- `main`: `9235ddc1ceaeddaec2074050eaebdeacaf588e53`;
- Pacote 5A integrado e validado após o merge;
- auditoria residual do `R-004`: `10` achados confirmados;
- escopo autorizado: `R004-F006`, `R004-F007` e `R004-F008`;
- baseline inicial: `255` arquivos;
- risco relacionado: `R-004`.

## Achados tratados

### `R004-F006`

A aplicação do `MaskViewer` criava cada polígono em uma entrada separada,
possuía fallback direto sem histórico e podia deixar um lote parcialmente
aplicado.

### `R004-F007`

`detect_and_create_objects()` executava comandos individualmente, podia chamar
`execute()` fora do `CommandManager` e não oferecia Undo/Redo atômico do lote.

### `R004-F008`

A auto-geração de colisões substituía `scene.collision_shapes` diretamente e
atualizava o cache de física fora de um comando reversível.

## Escopo implementado

- `MaskViewerDialog._apply_to_scene()` exige `CommandManager` e executa um
  `CompositeCommand` contendo todos os polígonos detectados;
- qualquer subcomando rejeitado ou com falha desfaz integralmente o lote;
- a janela só declara sucesso e fecha quando o lote é efetivamente aplicado;
- `detect_and_create_objects()` cria uma única entrada de histórico e retorna
  IDs somente depois da aplicação integral;
- ausência de histórico, rejeição e falha são propagadas sem falso sucesso;
- `AutoGenerateCollisionShapesCommand` substitui todas as colisões em uma
  operação reversível;
- Execute, Undo e Redo preservam o estado anterior exato e rejeitam geometria
  ou colisões obsoletas;
- coordenadas inválidas ou não finitas bloqueiam todo o lote;
- o `CollisionPanel` sincroniza o cache derivado do `PhysicsManager` com a cena
  depois de Execute, Undo e Redo;
- testes de colisão sincronizam o cache sem criar histórico artificial;
- não existe fallback direto nos três caminhos cobertos.

## Testes específicos

- lote de criação com uma única entrada de histórico;
- identidade e seleção estáveis após Undo/Redo;
- rollback integral por polígono inválido ou falha controlada;
- bloqueio sem `CommandManager`;
- preview do auto-detect sem mutação;
- lote vazio sem entrada de histórico;
- camadas por polígono;
- auto-geração de colisões com restauração exata;
- no-op quando o estado já corresponde à geometria;
- rejeição de coordenada não finita;
- rejeição de colisão ou geometria obsoleta;
- sincronização do cache de física em Execute, Undo e Redo;
- ausência estrutural de mutações e fallbacks diretos.

Quantidade esperada:

```text
34 testes específicos
406 testes totais
baseline 258 arquivos
```

## Fora do escopo

- `R004-F009`: caminho runtime de Bézier;
- `R004-F010`: contratos residuais sem cobertura nominal;
- integração do `LayersPanel` à `MainWindow`;
- fechamento do `R-004`;
- conclusão da Etapa 5;
- início da Etapa 6.

## Gates obrigatórios

- `34` testes específicos;
- suíte completa de `406` testes;
- Black, isort, Flake8 fatal, mypy e compileall;
- baseline de `258` arquivos antes e depois dos testes;
- CI Linux e Windows no HEAD exato;
- revisão integral do diff;
- validação visual focal dos lotes e da auto-geração de colisões;
- merge somente após autorização explícita;
- CI e evidência pós-merge antes de declarar integração.

## Estado ao criar o pacote

```text
PACKAGE5B_IMPLEMENTED=YES
PACKAGE5B_INTEGRATED=NO
R004_CLOSED=NO
STAGE5_COMPLETED=NO
STAGE6_STARTED=NO
```
