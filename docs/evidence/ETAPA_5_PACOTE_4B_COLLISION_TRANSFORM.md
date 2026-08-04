# Evidência — Etapa 5, Pacote 4B: movimento e escala transacionais

## Base

- `main`: `8b59e4fa4dfbe14ad44e85e155073a0843634fd1`;
- Pacote 4A/4A.1 integrado e validado pelo workflow pós-merge `#71`;
- baseline inicial: `247` arquivos;
- risco relacionado: `R-004`.

## Achado confirmado

`CollisionBrushTool` ainda alterava diretamente `obj.polygon` e
`collision_shapes` durante movimento e escala.

A escala também era aplicada sobre a geometria já escalada, usando um fator
cumulativo novamente sobre o resultado anterior. Isso causava composição
progressiva, arredondamento acumulado e substituição da colisão personalizada
pelo contorno do polígono.

## Escopo

- novo `UpdateObjectGeometryCommand` para polígono e colisão exatos;
- nova `ObjectGeometryGestureTransaction`;
- prévia contínua sem entrada no histórico;
- um único comando no encerramento do gesto;
- movimento calculado sempre a partir da origem;
- escala absoluta calculada sempre a partir da origem;
- transformação da colisão personalizada junto com o polígono;
- Undo e Redo exatos;
- cancelamento por Escape, troca de operação, Undo, Redo e cancelamento da
  ferramenta;
- bloqueio seguro sem `CommandManager`;
- quinze testes específicos.

## Fora do escopo

- camadas e grupos;
- geração em massa de colisões;
- criação manual de polígonos;
- encerramento de `R-004` ou da Etapa 5;
- início da Etapa 6.

## Gates

- quinze testes específicos;
- suíte completa de `296` testes;
- Black, isort, Flake8 fatal e mypy;
- baseline de `250` arquivos;
- CI Linux e Windows;
- revisão do diff;
- validação visual posterior de movimento, escala, cancelamento e Undo/Redo.

## Decisão esperada

O Pacote 4B cobre somente movimento e escala da ferramenta de colisão.
`R-004` e a Etapa 5 permanecem abertos.
