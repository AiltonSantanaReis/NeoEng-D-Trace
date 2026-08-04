# Evidência — Etapa 5, Pacote 4A: exclusão transacional de objetos

## Base

- `main`: `e2e95b332f2647e7e1debd0ff0ed4759676bb992`;
- Pacotes 2A, 2B, 3A, 3B e correção 3B.1 integrados;
- workflow pós-merge anterior: `#68` (`30828675955`);
- baseline inicial: `245` arquivos;
- risco relacionado: `R-004`.

## Achado confirmado

Ainda existiam exclusões diretas e irreversíveis em:

- `PolygonEditTool.delete_selected_polygon`, inclusive seleção múltipla;
- `CollisionBrushTool._remove`.

A ferramenta de colisão também mantinha fallback direto para alternar colisão
quando o `CommandManager` estava indisponível.

## Escopo

- exclusão simples por `DeleteObjectCommand`;
- exclusão múltipla por um único `CompositeCommand`;
- preservação exata da ordem dos objetos, colisões, grupos e seleção no Undo;
- remoção da ferramenta de colisão por `DeleteObjectCommand`;
- remoção do fallback direto do toggle de colisão;
- bloqueio seguro quando o histórico está indisponível;
- rejeição atômica quando qualquer ID da seleção múltipla ficou obsoleto;
- onze testes específicos.

## Fora do escopo

- movimento e escala da `CollisionBrushTool`;
- toggles e fallbacks de camadas e grupos;
- geração em massa de colisões;
- criação manual de polígonos;
- encerramento de `R-004` ou da Etapa 5;
- início da Etapa 6.

## Gates obrigatórios

- onze testes específicos;
- suíte completa;
- Black, isort, Flake8 fatal e mypy;
- baseline de `247` arquivos;
- CI Linux e Windows;
- revisão integral do diff;
- validação manual posterior de exclusão simples, múltipla e Undo/Redo.

## Decisão esperada

Aprovação somente dos caminhos de exclusão e do bloqueio do toggle sem
histórico. `R-004` e a Etapa 5 permanecem abertos.
## Correção 4A.1 — atomicidade de seleção obsoleta

A revisão do diff da PR `#22` identificou que uma seleção múltipla com IDs
válidos e obsoletos poderia excluir silenciosamente apenas o subconjunto ainda
existente. O caminho foi corrigido para rejeitar a operação inteira antes da
criação do comando, preservar a cena e manter as pilhas de Undo/Redo
inalteradas. Um teste específico congela esse contrato.

O CI `#69` aprovou a implementação inicial em Linux e Windows; um novo CI é
obrigatório para o commit desta correção.
