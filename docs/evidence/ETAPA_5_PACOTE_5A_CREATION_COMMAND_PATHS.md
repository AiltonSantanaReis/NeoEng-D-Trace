# Evidência — Etapa 5, Pacote 5A: comandos de criação e ferramentas ativas

## Base

- `main`: `0fc089bfc58ff9589f50bb394acd579bc2f71dd3`;
- Pacote 4C integrado pelo workflow pós-merge `#76`;
- auditoria residual do `R-004`: `10` achados confirmados;
- escopo autorizado: `R004-F001` até `R004-F005`;
- baseline inicial: `252` arquivos;
- risco relacionado: `R-004`.

## Achados confirmados tratados neste pacote

### `R004-F001`

`AddPolygonCommand` gerava um novo ID no Redo e não restaurava a seleção
anterior no Undo.

### `R004-F002`

`CreateObjectCommand` não restaurava a seleção anterior e atualizava
silenciosamente um objeto conflitante durante Execute ou Redo.

### `R004-F003`

`LassoTool` possuía criação direta por `Scene.add_polygon()` quando o
`CommandManager` estava indisponível.

### `R004-F004`

Polygonal Lasso, Magnetic Lasso, Pen, Rectangle e Ellipse possuíam fallbacks
diretos sem histórico.

### `R004-F005`

`CanvasView` possuía dois caminhos nativos de criação direta quando nenhuma
ferramenta estava ativa.

## Escopo implementado

- `AddPolygonCommand` e `CreateObjectCommand` compartilham um contrato de
  criação com:
  - identidade estável em Execute, Undo e Redo;
  - restauração exata da seleção anterior;
  - snapshot do objeto criado;
  - rejeição de conflito de ID;
  - rejeição de estado obsoleto de objeto, seleção, coleção, camada e relações;
  - ausência de sobrescrita silenciosa;
  - uma notificação por operação aplicada;
- `BaseTool` oferece um único caminho de criação por `CommandManager`;
- `LassoTool`, `PolygonalLassoTool`, `MagneticLassoTool`, `PenTool`,
  `RectSelectionTool` e `EllipseSelectionTool` não possuem fallback direto;
- ferramentas mostram `REJECTED`, `FAILED`, indisponibilidade e ausência de
  mudança sem declarar sucesso;
- gestos preservam seu estado quando a criação não é aplicada;
- `CanvasView` usa `AddPolygonCommand` nos dois caminhos nativos de criação;
- testes históricos de Magnetic Lasso e Polygonal Lasso foram atualizados para
  o novo contrato obrigatório de histórico.

## Testes específicos

- identidade estável;
- seleção anterior `None` e seleção de objeto existente;
- conflito inicial e conflito no Redo;
- objeto modificado antes do Undo;
- seleção modificada antes de Undo ou Redo;
- relações adicionadas antes do Undo;
- coleção alterada antes do Redo;
- camada removida antes do Redo;
- polígono inválido sem estado parcial ou entrada de histórico;
- criação sequencial e restauração da seleção em ordem de pilha;
- notificação única por Execute, Undo e Redo;
- ausência estrutural de `add_polygon()` direto nas seis ferramentas;
- uso do helper transacional compartilhado;
- bloqueio das seis ferramentas sem `CommandManager`;
- criação nativa do Canvas com histórico;
- bloqueio e mensagem do Canvas sem histórico;
- mensagem de falha para criação nativa inválida.

Quantidade esperada:

```text
44 testes específicos
372 testes totais
baseline 255 arquivos
```

## Fora do escopo

- `R004-F006`: lote do `MaskViewer`;
- `R004-F007`: auto-detect;
- `R004-F008`: auto-geração de colisões;
- `R004-F009`: caminho runtime de Bézier;
- `R004-F010`: contratos residuais sem cobertura nominal;
- integração do `LayersPanel` à `MainWindow`;
- fechamento de `R-004`;
- conclusão da Etapa 5;
- início da Etapa 6.

## Gates obrigatórios

- `44` testes específicos;
- suíte completa de `372` testes;
- Black, isort, Flake8 fatal e mypy;
- baseline de `255` arquivos;
- CI Linux e Windows ligados ao HEAD exato;
- revisão integral do diff;
- validação visual focal dos seis caminhos de ferramenta e dos dois caminhos
  nativos do Canvas;
- PR draft;
- autorização explícita antes do merge;
- CI pós-merge da `main`;
- evidência pós-merge.

## Estado controlado

```text
PACKAGE5A_IMPLEMENTED=YES
PACKAGE5A_INTEGRATED=NO
R004_CLOSED=NO
STAGE5_COMPLETED=NO
STAGE6_STARTED=NO
```

## Decisão esperada

O Pacote 5A cobre somente os achados `R004-F001` até `R004-F005`. Os achados
`R004-F006` até `R004-F010` permanecem abertos para os Pacotes 5B e 5C.
