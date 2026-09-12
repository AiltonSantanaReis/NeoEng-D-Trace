# Decisão E07 — Entidades, componentes, hierarquia e prefabs

**Data:** 2026-09-08  
**Estado:** `ACTIVE_TECHNICAL_CONTRACT`  
**Dependência:** checkpoint técnico E06 em `df841ef`  
**Plano normativo:** seção 14 do Plano Mestre, requisitos ENT-001/002/003/004,
SCN-003 e EXT-ENT-01.

## Escopo autorizado

E07 implementará entidades com identidade estável, transformação e componentes
tipados/versionados; instâncias com identidade própria; hierarquia espacial
distinta de membership organizacional; e o ciclo completo de prefab. A solução
reutilizará IDs e transações existentes, sem introduzir uma reescrita ECS de
alto volume ou executar scripts arbitrários embutidos ao abrir uma cena.

## Lotes e aceite

- **E07-A:** modelo de entidade, componentes, instâncias, cardinalidade,
  dependências, validação e migração não destrutiva.
- **E07-B:** parent espacial separado de grupos, prevenção de ciclos, reparent
  validado, tags, filtros, busca, isolamento, visibilidade/lock herdados,
  seleção sincronizada, drag/drop e estado de expansão.
- **E07-C:** criar prefab, instanciar duas vezes, override, comparar,
  aplicar/reverter, atualizar origem, preservar overrides, desvincular,
  salvar/reabrir e exportar.

O fluxo de aceite obrigatório é: montar conjunto → agrupar e parentear → criar
prefab → instanciar duas vezes → alterar uma instância → atualizar a origem →
verificar herdados e overrides → desvincular → salvar/reabrir/exportar.

## Negativos e rollback

Devem ser rejeitados atomicamente ciclos, IDs duplicados, componente inválido,
prefab ausente, remoção de campo com override, edição bloqueada, reparent sem
transform representável e conflito assíncrono. Versões novas de prefab serão
preservadas; migração ocorrerá em cópia; nenhuma expansão destrutiva automática
de instâncias será permitida. Undo/Redo não criará identidades novas durante
replay.

Symlink e revisão humana permanecem reservados à auditoria final do plano.
