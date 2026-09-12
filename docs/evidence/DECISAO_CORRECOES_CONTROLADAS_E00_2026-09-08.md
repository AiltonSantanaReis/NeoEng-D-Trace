# Decisão de controle — correções comprovadas durante E00

**Data:** 2026-09-08  
**Escopo:** E00 / preservação visual e responsiva  
**Estado:** `AUTHORIZED / CONTROLLED_CORRECTION`

## Autorização

O proprietário autorizou aplicar correções sempre que um problema for detectado.
Esta decisão formaliza a autorização como uma exceção controlada à preparação
de E00, limitada a findings reproduzíveis da base preservada. Ela não abre E01,
não autoriza uma reescrita funcional, não altera requisitos e não permite
push, merge, tag ou release.

## Limites

- cada correção precisa apontar para um finding, teste, commit e nova build;
- a correção deve preservar contratos, atalhos, tradução e dados existentes;
- o pacote anterior permanece preservado e não é reclassificado;
- a revisão humana continua deferida até a auditoria final, mas obrigatória
  antes do fechamento de E00;
- a autorização vale para correções de preservação detectadas em E00, não para
  iniciar capacidades planejadas de E01–E13.

## Finding tratado

A captura maximizada do binário `1a1a0e9` mostrou truncamento de rótulos da
toolbar desktop. A causa reproduzida foi a aplicação de largura mínima de
60/62 px, menor que o `sizeHint` dos rótulos localizados. O modo compacto
continua icon-only; no modo desktop os botões passam a respeitar seu tamanho
renderizado e o teste responsivo verifica essa invariável.
