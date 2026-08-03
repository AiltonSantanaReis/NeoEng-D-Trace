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


## Correção pós-merge — caminho duplicado de clique

A auditoria realizada após o merge da PR `#20` identificou que
`PolygonEditTool.on_mouse_press` continha o novo fluxo transacional seguido
por uma cópia residual do fluxo legado de seleção.

Embora os testes e a validação visual do Pacote 3B tenham sido aprovados,
a duplicação executava uma segunda passagem de seleção em cliques normais e
não deve permanecer no estado integrado.

Esta correção:

- remove exclusivamente o segundo bloco legado de clique;
- preserva o fluxo transacional já validado;
- adiciona um teste que exige uma única inicialização da transação;
- adiciona um teste que impede o retorno do `drag_start_pos` legado ao clicar
  no corpo do polígono;
- mantém a baseline em `245` arquivos;
- não encerra `R-004`, a Etapa 5 ou inicia a Etapa 6.
