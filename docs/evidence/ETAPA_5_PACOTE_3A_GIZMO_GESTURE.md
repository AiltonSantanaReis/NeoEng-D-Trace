# Evidência — Etapa 5, Pacote 3A: gesto transacional do gizmo

## Base

- Commit da `main`: `46f73d47081bcc6e997f494eb0c092c615a8f108`;
- Pacotes 2A e 2B integrados;
- workflow pós-merge do Pacote 2B: `#62` (`30776478287`);
- baseline inicial: `240` arquivos;
- risco relacionado: `R-004`.

## Objetivo

Transformar o arraste contínuo do gizmo em uma única alteração reversível,
sem registrar cada movimento intermediário no histórico.

## Escopo

- transação reutilizável de gesto poligonal;
- prévia contínua com notificações para renderização;
- consolidação em um `UpdatePolygonCommand` ao soltar o mouse;
- restauração exata de colisão customizada ao cancelar ou desfazer;
- acumulação de deltas fracionários;
- cancelamento por `Escape`, troca de ferramenta e modo de preview;
- bloqueio seguro sem `CommandManager`;
- oito testes específicos.

## Fora do escopo

- mover, adicionar ou excluir vértices na ferramenta de edição;
- criação manual de polígonos;
- migração integral das 117 mutações candidatas;
- encerramento de `R-004` ou da Etapa 5;
- início da Etapa 6.

## Gates obrigatórios

- `8` testes específicos do Pacote 3A;
- suíte completa;
- Black, isort, Flake8 fatal e mypy;
- baseline de `243` arquivos;
- CI Linux e Windows;
- revisão integral do diff;
- validação manual posterior do gizmo.

## Decisão esperada

Aprovação somente do gesto do gizmo. O Pacote 3B e `R-004` permanecem abertos.
