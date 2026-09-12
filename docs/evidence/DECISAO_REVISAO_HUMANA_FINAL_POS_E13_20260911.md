# Decisão de revisão humana final pós-E13

**Data:** 2026-09-11
**Autoridade:** decisão explícita do proprietário registrada nesta conversa
**Estado:** `AUTHORIZED / HUMAN_REVIEW_DEFERRED`

## Decisão

A revisão humana final do Editor de Cenário será realizada somente depois que
os itens funcionais ainda abertos forem implementados, testados, executados no
binário e comprovados com evidências reais. A revisão não é um bloqueio para os
checkpoints técnicos intermediários, mas continua obrigatória antes do aceite
final do lote pós-E13 ou do produto.

Os itens que devem ser concluídos antes da revisão humana são:

- iluminação direcional com efeito observável no ambiente e na direção da luz;
- efeitos orientáveis, com posicionamento e direção editáveis;
- sistema completo de partículas, incluindo fluxo de autoria e runtime;
- tilemap/tileset com criação e edição profissional do zero;
- editor 3D e o fluxo híbrido 2D/2.5D/3D correspondente.

## Aplicação imediata

- A subetapa já comprovada de câmera, guias de parallax e scrub contínuo
  permanece tecnicamente registrada com `PASS` nos critérios observados.
- O lote pós-E13 permanece `IN_PROGRESS`; nenhuma evidência intermediária é
  promovida a aceite humano ou conclusão do produto.
- A revisão humana fica `PENDING_EVIDENCE` por ausência deliberada de execução
  nesta fase, não por falha ou bloqueio técnico.
- Cada item aberto deverá possuir entrada controlada, operação real, saída
  observável, persistência quando aplicável, runtime quando aplicável,
  comportamento de erro, captura e hash antes de solicitar a revisão final.

## Critério para reabrir a revisão humana

A revisão será iniciada quando todos os itens acima tiverem:

1. implementação preservando os contratos existentes;
2. testes unitários, integração e regressão aplicáveis;
3. execução da suíte oficial sem filtros;
4. build limpa vinculada ao commit;
5. fluxo nativo real com capturas e persistência;
6. limitações, warnings e falhas históricas explicitamente documentados.

Depois disso, a revisão humana deverá validar visual, usabilidade, fluxo,
localização PT-BR, desempenho percebido e coerência do editor com os fluxos
2D, 2.5D e 3D. O resultado poderá ser `PASS`, `FAIL` ou `PENDING_EVIDENCE`,
conforme os artefatos observados.

## Limites preservados

E13 continua fechado e histórico. Esta decisão não autoriza push, merge, tag,
release ou publicação, não remove falhas históricas e não altera os requisitos
dos itens ainda abertos.
