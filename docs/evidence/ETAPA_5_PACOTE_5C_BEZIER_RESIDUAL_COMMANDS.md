# Etapa 5 — Pacote 5C — Histórico Bézier e contratos residuais

## Escopo

Este pacote trata exclusivamente os achados `R004-F009` e `R004-F010` sobre a
base `ee38a2f1dc85093e34140ddd087312629b4ecb43`.

## Implementação

- núcleo Bézier canônico sem dependência de Qt;
- criação de objeto Bézier por `CreateBezierObjectCommand`;
- integração runtime de `HandleMoveCommand` à ferramenta Caneta;
- prévia de movimento sem histórico e consolidação em uma única entrada;
- preservação exata do estado de colisão durante edição de handle;
- amostragem compartilhada entre ferramenta, cena e comandos;
- contratos explícitos de Execute, Undo, Redo, no-op, rejeição e falha;
- cobertura nominal ativa de `HandleMoveCommand`,
  `UpdateObjectGeometryCommand` e `ExpandContractCommand`.

## Política de colisão

A edição de handle não cria, remove ou regenera colisões. O estado existente é
preservado exatamente e alterações externas bloqueiam Undo ou Redo.

## Validação planejada

- 42 testes focais;
- 448 testes totais esperados;
- baseline esperado de 262 arquivos;
- CI Linux e Windows;
- evidência visual focal da criação e edição Bézier.

## Limitação adjacente

Os pontos de controle Bézier não são persistidos pelo formato atual de projeto.
O pacote preserva esses dados em criação, edição, Execute, Undo e Redo durante a
sessão, sem alegar persistência após salvar e reabrir o arquivo.

## Estado

O risco `R-004` permanece aberto. A Etapa 5 não é concluída e a Etapa 6 não é
iniciada por este pacote.
