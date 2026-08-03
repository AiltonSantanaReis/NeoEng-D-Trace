# Evidência — Etapa 5, Pacote 3B: edição transacional de vértices

## Base

- Commit da `main`: `830075b354b2fc4f96a8c1516757c1f10cac9833`;
- Pacotes 2A, 2B e 3A integrados;
- workflow pós-merge do Pacote 3A: `#64` (`30778333151`);
- baseline inicial: `243` arquivos;
- risco relacionado: `R-004`.

## Objetivo

Migrar os caminhos de mover, adicionar e excluir vértices para o histórico
transacional, sem registrar cada movimento intermediário do mouse.

## Escopo

- reutilização da transação de gesto poligonal no arraste de um vértice;
- uma única entrada de histórico por arraste concluído;
- inclusão de vértice por `UpdatePolygonCommand`;
- exclusão de vértice por `UpdatePolygonCommand`;
- restauração exata do polígono e da colisão anterior no cancelamento e Undo;
- cancelamento por `Escape`, troca de ferramenta, Undo e modo de preview;
- bloqueio seguro quando o `CommandManager` está indisponível;
- conjunto específico de `10` testes.

## Fora do escopo

- exclusão de polígonos inteiros pela ferramenta;
- criação manual de novos polígonos;
- seleção múltipla transacional;
- migração integral das demais mutações candidatas;
- encerramento de `R-004` ou da Etapa 5;
- início da Etapa 6.

## Gates obrigatórios

- `10` testes específicos do Pacote 3B;
- suíte completa;
- Black, isort, Flake8 fatal e mypy;
- baseline de `245` arquivos;
- CI Linux e Windows;
- revisão integral do diff;
- validação manual posterior da edição de vértices.

## Decisão esperada

Aprovação apenas dos três caminhos de vértices. `R-004` e a Etapa 5
permanecem abertos.
