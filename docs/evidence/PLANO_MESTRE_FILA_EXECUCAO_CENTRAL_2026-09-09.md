# Plano Mestre — fila central de execução

**Registro:** `CONTINUITY-NEOENG-20260908`  
**Worktree único:** `build/e01-independent-scene-20260908`  
**Branch:** `Ailton/e08-renderer-20260908`  
**Estado:** execução técnica contínua autorizada; auditoria final ainda pendente

Este arquivo é a fila operacional única. O registro JSON canônico aponta para
ele. Nenhuma etapa é promovida apenas por uma captura, por um teste parcial ou
por uma afirmação textual. Cada item só muda para `CONCLUÍDO_TECNICAMENTE`
quando possui implementação, teste proporcional, evidência, proveniência e
commit; o encerramento formal continua condicionado aos gates finais.

## Regra de continuidade

Continuar automaticamente na ordem abaixo. Não parar por uma pendência que
possa ser tratada no próximo lote. Parar somente quando toda a fila estiver
concluída ou quando uma decisão material do proprietário for indispensável.

Symlinks e revisão humana não são executados entre os lotes: permanecem
reservados exclusivamente para `AUDITORIA_FINAL`. Um `SKIP` local nunca vira
`PASS`.

## Quadro central

| Ordem | Meta | Estado | Evidência/saída obrigatória |
|---:|---|---|---|
| 00 | Governança, continuidade e preservação | `CHECKPOINT_TECNICO_PASS` | registro canônico, decisões, base restaurável e proveniência |
| 01 | Contratos, backend e cena independente | `CHECKPOINT_TECNICO_PASS` | contrato, testes, binário, captura e rollback |
| 02 | Primitivas, edição, histórico e persistência | `CHECKPOINT_TECNICO_PASS` | fluxo nativo, negativos, save/reopen e evidência |
| 03 | Biblioteca própria e lifecycle de assets | `CHECKPOINT_TECNICO_PASS` | pacote offline, proveniência, lifecycle e captura |
| 04 | Tilemaps, grids e regras | `CHECKPOINT_TECNICO_PASS` | três grids, ferramentas, regras e persistência |
| 05 | Colisão própria | `CHECKPOINT_TECNICO_PASS` | formas, triggers, validação e consumidor |
| 06 | NavMesh e navegação | `CHECKPOINT_TECNICO_PASS` | bake, caminho, negativos e persistência |
| 07 | Entidades, hierarquia e prefabs | `CHECKPOINT_TECNICO_PASS` | componentes, ciclo de prefab e captura |
| 08 | Renderer, materiais, paralaxe e FX | `CHECKPOINT_TECNICO_PASS` | pixels, determinismo, fallback e destinos |
| 09 | Autoria e exportação vetorial | `CHECKPOINT_TECNICO_PASS` | edição, colisão, persistência e exportação |
| 10 | Integração real com Godot e Unity | `CHECKPOINT_TECNICO_PASS` | importação, execução, comparação, negativos e capturas |
| 11 | Composição e runtime completo | `EM_EXECUÇÃO` | cena composta, recovery, exportação, consumo e UX no binário |
| 12 | Recursos avançados e híbrido 3D | `PLANEJADA` | contrato aprovado, implementação, testes e destinos |
| 13 | Fechamento técnico e portabilidade | `PLANEJADA` | portátil/MSI, smoke, documentação e pacote final |
| F | Auditoria final do Plano Mestre | `BLOQUEADA_POR_FLUXO` | symlinks, revisão humana, findings e decisão formal |

Os estados `CHECKPOINT_TECNICO_PASS` não significam aceite final. Todos os
itens continuam sujeitos à auditoria final, conforme a decisão de continuidade.

## Metas ativas de E11

| ID | Meta | Estado | Critério objetivo |
|---|---|---|---|
| E11-A | Compor capacidades em uma cena do produto | `PARCIAL_PASS` | recursos de E03–E09 usados na mesma cena e captura real |
| E11-B | Persistência e recovery | `PARCIAL_PASS` | salvar, fechar, reabrir, erro recuperável e saída válida preservada |
| E11-C | Exportar e consumir fora do editor | `EM EXECUÇÃO` | exportação da cena composta, Godot e Unity executando o resultado |
| E11-D | Usabilidade e acessibilidade operacional | `EM EXECUÇÃO` | foco, teclado/mouse, tradução, mensagens, cancelamento e tempos |
| E11-E | Fechar tecnicamente E11 | `PENDENTE` | suíte, estática, build, manifesto, regressão e promoção documentada |

### Próxima sequência obrigatória

1. Construir uma fixture composta rastreável com as capacidades realmente
   suportadas pelo schema atual; não inventar suporte a campos inexistentes.
2. Executar essa fixture no binário portátil r55 ou em nova build somente se
   uma correção de código exigir a reconstrução.
3. Capturar o fluxo completo no processo real, incluindo erro recuperável,
   cancelamento e preservação do último estado válido.
4. Exportar o mesmo resultado e repetir o consumo nos projetos reais Godot e
   Unity, com hashes, logs e capturas nativas.
5. Corrigir findings reproduzíveis, repetir os gates afetados e fazer commit
   da etapa comprovada.
6. Reexecutar a suíte proporcional e a suíte oficial; atualizar o registro e
   só então abrir E12.

## Gates finais reservados

| Gate | Estado | Regra |
|---|---|---|
| Symlinks | `ADIADO_ATÉ_AUDITORIA_FINAL` | executar apenas no SHA/build final; preservar `SKIP_LOCAL` separado |
| Revisão humana | `ADIADA_ATÉ_AUDITORIA_FINAL` | revisar capturas e roteiro reais no SHA/build final |
| Publicação | `NÃO_AUTORIZADA` | push, merge, tag e release exigem autorização separada |

## Definição de término

A fila só poderá ser marcada como encerrada quando E11, E12 e E13 tiverem
critérios comprovados, todas as regressões estiverem resolvidas ou formalmente
aceitas, o pacote portátil/MSI estiver qualificado, a auditoria final executar
symlinks e revisão humana, e o registro canônico apontar para o SHA/build final.

**Última atualização:** 2026-09-09  
**Próximo status esperado:** resultado da fixture composta e do consumo real de E11-C.
