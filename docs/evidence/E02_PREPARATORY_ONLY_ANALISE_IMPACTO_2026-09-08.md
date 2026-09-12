# E02 — análise preparatória de impacto (`PREPARATORY_ONLY`)

**Data:** 2026-09-08  
**Base documental:** Plano Mestre `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**Worktree:** `Ailton/e01-independent-scene-20260908`  
**Estado:** preparatório somente; não é início nem aceite de E02.

## Objetivo

Preparar a decomposição de E02 sem alterar a implementação do produto nem
contornar a dependência de aceite formal de E01. O documento centraliza os
critérios que deverão ser aprovados antes de qualquer código funcional de
primitivas.

## Escopo que será afetado

| Requisito | Tema | Dependência preservada |
|---|---|---|
| SCN-002 | primitiva autoral sem asset artificial, edição e persistência | E01 formalmente aceita |
| SCN-003 | transformação, pivô, organização, seleção e histórico | E01 formalmente aceita |
| SCN-004 | composição efetiva e fluxo completo no binário | E01 formalmente aceita |
| VEC-005 | autoria livre além do contorno assistido | contrato de dados de E01 |
| UX | criação, edição, cancelamento, feedback e acessibilidade | fluxos legados preservados |

## Entregáveis obrigatórios de E02

1. Especificação de retângulo, elipse e polígono/caminho, distinguindo curva
   aberta, curva fechada, preenchimento e forma apta à colisão.
2. Máquina de estados da ferramenta: ociosa, criando, editando, prévia
   inválida e finalizada.
3. Semântica de clique vazio, finalização, duplo clique, Escape e reativação,
   sem reinício automático não aprovado.
4. Identidade, pivô, transformações, seleção múltipla, duplicação, remoção,
   camada, visibilidade, bloqueio, Undo/Redo e persistência.
5. Fluxo de aceite no binário: três tipos de forma, edição, transformação,
   duplicação/remoção, Undo/Redo, salvar e reabrir.
6. Negativos: polígono cruzado, pontos repetidos, fechamento degenerado,
   valores não finitos, escala inválida, objeto bloqueado, cancelamento e
   alteração externa durante gesto.
7. Evidência com eventos, capturas reais, comparação de reabertura e rollback.

## Impacto técnico preliminar

- reutilizar `IndependentSceneSession` e o contrato de persistência de E01;
- não acoplar autoria ao widget de imagem legado;
- manter o fluxo antigo, seus arquivos e suas ferramentas sem migração
  destrutiva;
- registrar cada mudança em lote próprio, com build e captura vinculadas ao
  SHA correspondente;
- não iniciar implementação funcional enquanto `stage_status.E01` continuar
  `IN_PROGRESS` e a revisão final estiver pendente.

## Critério de saída desta preparação

Este documento só habilita a elaboração técnica do próximo lote. A promoção
para E02 exige aceite formal de E01, atualização do registro central, contrato
de mudança e nova análise de impacto antes do primeiro arquivo de código.

**Resultado:** `PREPARATORY_ONLY` — nenhum requisito de produto de E02 foi
declarado implementado ou aceito.
