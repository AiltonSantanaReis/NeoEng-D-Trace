# Evidência — Etapa 5, Pacote 4C: camadas e grupos sem fallbacks diretos

## Base

- `main`: `f8a7e3dce61acd6e9312d70575cdf9eb89297a9a`;
- Pacote 4B/4B.1 integrado pelo workflow pós-merge `#74`;
- baseline inicial: `250` arquivos;
- risco relacionado: `R-004`.

## Achados confirmados

O painel de camadas continha fallbacks diretos para criação, exclusão,
reordenação, visibilidade e bloqueio quando `CommandManager` não estava
disponível.

O painel de grupos continha fallbacks diretos para criação, exclusão,
associação, remoção de associação e reordenação. Visibilidade e bloqueio de
grupos eram alterados diretamente no objeto e seguidos por `_notify()`.

Comandos existentes também não preservavam sempre identidade, índice ou
notificação exata durante Undo/Redo.

## Escopo

- painéis de camadas e grupos passam a bloquear toda edição sem histórico;
- nenhuma ação de edição possui fallback direto;
- resultados `REJECTED` e `FAILED` são mostrados ao usuário;
- criação de camada e grupo preserva o mesmo ID em Redo;
- exclusão restaura índice, propriedades, membros e atribuições exatos;
- movimento restaura a ordem exata;
- toggles de camada e grupo usam comandos e notificam a cena;
- associação e desassociação de objetos são reversíveis e detectam no-op;
- trinta testes específicos.

## Fora do escopo

- alteração do modelo visual dos painéis;
- múltipla seleção de camadas ou grupos;
- renomeação de camadas ou grupos;
- encerramento de `R-004` ou da Etapa 5;
- início da Etapa 6.

## Gates

- `30` testes específicos;
- suíte completa de `328` testes;
- Black, isort, Flake8 fatal e mypy;
- baseline de `252` arquivos;
- CI Linux e Windows;
- revisão integral do diff;
- validação visual focal dos dois painéis.

## Decisão esperada

O Pacote 4C cobre somente fallbacks e comandos de edição de camadas e grupos.
`R-004` e a Etapa 5 permanecem abertos.
