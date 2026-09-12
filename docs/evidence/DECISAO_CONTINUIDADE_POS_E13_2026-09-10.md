# Decisão de continuidade pós-E13 — fechamento sem regressão

**Estado:** `AUTHORIZED / POST_E13_IN_PROGRESS`  
**Data:** 2026-09-10  
**Base:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`

## Decisão registrada

O proprietário confirmou que o E13 está concluído. A partir deste registro,
`POST_E13` é a única etapa ativa. O E13 fica congelado como histórico de
portabilidade e fechamento técnico: seus documentos, builds, capturas, hashes,
skips e limitações continuam preservados e não serão reabertos, reinterpretados
ou usados como base alternativa de código.

A auditoria final do plano, a revisão humana e os gates de publicação continuam
separados. Eles podem permanecer pendentes sem transformar o E13 novamente em
uma etapa de implementação.

## Objetivo da meta ativa

Fechar as pendências identificadas depois do E13 no Editor de Cenário e no
catálogo de assets, com correções pequenas, rastreáveis e reversíveis, sem
remover conteúdo existente nem alterar contratos já funcionais. O fechamento
exige:

1. auditoria do estado real do worktree e das evidências;
2. testes automatizados focados e suíte oficial sem filtros;
3. build limpa a partir do commit das correções;
4. fluxo nativo real com cliques, mensagens, persistência e capturas;
5. revisão técnica de parallax, catálogo, tilemap/tileset, partículas, áudio,
   timeline, menus e localização PT-BR;
6. documentação de impacto, limitações, hashes e regressões, mantendo
   findings históricos visíveis.

## Escopo de implementação autorizado

- melhorar responsividade e previsibilidade das miniaturas do catálogo;
- completar mensagens, títulos e affordances PT-BR do fluxo de assets;
- oferecer menu de contexto seguro no viewport profissional, sem ação
  destrutiva implícita;
- corrigir somente findings reproduzíveis nos testes e na execução nativa;
- agregar pacotes e evidências, preservando `archive/legacy` e os artefatos
  existentes.

Não estão autorizados push, merge, tag, release, publicação, remoção de
assets, limpeza destrutiva de halos ou mudança silenciosa do modelo de cena.

## Critério de saída

O lote pós-E13 só pode ser marcado como concluído quando a evidência final
identificar requisito, commit, teste, artefato, resultado observado e
limitação/fallback. Uma falha ou warning não pode ser escondido para obter
`PASS`; quando não for seguro corrigir, deverá permanecer explícito com
escopo, impacto e decisão necessária.

## Decisões reservadas ao proprietário no final

Somente após a entrega das evidências ficarão para decisão humana:

- aceite visual final dos assets proprietários e autorização para distribuição;
- licença, proveniência comercial e política de atualização dos pacotes;
- autorização de publicação/release, se desejada;
- aceite explícito de limitações ambientais que não sejam regressões do
  produto, como skips locais de privilégio e warnings de empacotamento.

Até lá, a execução técnica continua autorizada no mesmo worktree.
