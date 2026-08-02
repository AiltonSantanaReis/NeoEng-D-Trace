# Evidência — Etapa 5, Pacote 2A: relações de objetos

## Base

- Commit: `2a9c80bf0134ef5eb0ebed830bb225bf5b8db174`;
- Branch: `feat/etapa-5-pacote-2a-object-relations`;
- Baseline inicial: `236` arquivos;
- Risco: `R-004`.

## Escopo

- renomeação consistente entre objeto, colisão, grupos e seleção;
- exclusão e restauração integral das relações do objeto;
- colisão customizada preservada no Undo;
- alteração de polígono protegida contra estado obsoleto;
- Undo de polígono restaura geometria e colisão atomicamente;
- listeners recebem uma única notificação com o estado final;
- limpeza reversível com seleção;
- testes de execute, undo, redo e rejeições.

## Fora do escopo

- migração dos fallbacks da UI, reservada ao Pacote 2B;
- movimento pelo gizmo e vértices, reservados ao Pacote 3;
- camadas, grupos, Bézier e importação completos;
- migração integral das 117 mutações candidatas;
- metas finais de cobertura;
- encerramento de `R-004` ou da Etapa 5.

## Decisão esperada

Aprovação somente no escopo do Pacote 2A. `R-004` permanece aberto.
