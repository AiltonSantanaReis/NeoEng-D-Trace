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
| 11 | Composição e runtime completo | `CHECKPOINT_TECNICO_PASS` | composição, recovery, exportação, consumo, UX e suíte r67 |
| 12 | Recursos avançados e híbrido 3D | `CHECKPOINT_TECNICO_PASS` | contrato, pacote, destinos reais, captura r69, smoke e suíte |
| 13 | Fechamento técnico e portabilidade | `EM_EXECUÇÃO` | portátil/MSI, smoke, documentação e pacote final |
| F | Auditoria final do Plano Mestre | `BLOQUEADA_POR_FLUXO` | symlinks, revisão humana, findings e decisão formal |

Os estados `CHECKPOINT_TECNICO_PASS` não significam aceite final. Todos os
itens continuam sujeitos à auditoria final, conforme a decisão de continuidade.

## Metas ativas de E11

| ID | Meta | Estado | Critério objetivo |
|---|---|---|---|
| E11-A | Compor capacidades em uma cena do produto | `CONCLUÍDO_TECNICAMENTE` | fixture composta no r67, recursos E03–E10, exportação e captura nativa |
| E11-B | Persistência e recovery | `CONCLUÍDO_TECNICAMENTE` | save, close/reopen, corrupção controlada, recovery, JSON válido e reexport |
| E11-C | Exportar e consumir fora do editor | `CONCLUÍDO_TECNICAMENTE` | pacote autocontido, Godot 4.7 e Unity 6000.5.7f1 com asset real |
| E11-D | Usabilidade e acessibilidade operacional | `CONCLUÍDO_TECNICAMENTE` | toolbar responsiva, português, atalhos exclusivos, foco e capturas r67 |
| E11-E | Fechar tecnicamente E11 | `CONCLUÍDO_TECNICAMENTE` | suíte 2101/2/1, estática, build r67, manifesto e promoção documentada |

### Próxima sequência obrigatória

1. Reexecutar a suíte proporcional e a suíte oficial no SHA/build r67, além
   dos gates estáticos e do diff check.
2. Consolidar manifesto, hashes, limitações e promoção técnica de E11-E.
3. Corrigir qualquer finding reproduzível e repetir os gates afetados com
   commit rastreável.
4. Atualizar o registro e só então abrir E12, relendo governança e plano.

## Metas ativas de E12

| ID | Meta | Estado | Evidência objetiva |
|---|---|---|---|
| E12-A | Contrato/schema e limites | `CONCLUÍDO_TECNICAMENTE` | exporter versionado, pacote hash-bound e negativos focados |
| E12-B | Animação e playback | `CONCLUÍDO_TECNICAMENTE` | 2 frames coerentes, clip `0.0 → 1.0`, CLI e teste de persistência do manifesto |
| E12-C | Vertical slice híbrida 3D | `CONCLUÍDO_TECNICAMENTE` | Godot 4.7 e Unity 6000.5.7f1 reais, relatório `e12-engine-audit-20260909-r4` |
| E12-D | UX, mensagens e documentação | `CONCLUÍDO_TECNICAMENTE` | limitação `VERTICAL_SLICE_ONLY` documentada e captura r69 |
| E12-E | Fechamento técnico | `CONCLUÍDO_TECNICAMENTE` | suíte 2104/2/1, build r69, smoke, manifesto e promoção |

## Metas ativas de E13

| ID | Meta | Estado | Critério objetivo |
|---|---|---|---|
| E13-A | Qualificar pacote portátil final | `CONCLUÍDO_TECNICAMENTE` | build r72, hashes, smoke e execução fora do checkout |
| E13-B | Qualificar MSI/instalador | `CONCLUÍDO_TECNICAMENTE` | WiX 4.0.6, instalação/desinstalação, smoke instalado e rollback de estado no r72 |
| E13-C | Auditoria técnica de documentação e privacidade | `CONCLUÍDO_TECNICAMENTE` | 135 manifests no gate oficial, referências locais removidas, limites e rollback documentados |
| E13-D | Auditoria final reservada | `EM_EXECUÇÃO` | r72 concluído; evidência Sandbox, revisão humana e decisão formal pendentes |

## Gates finais reservados

| Gate | Estado | Regra |
|---|---|---|
| Symlinks | `PASS_SANDBOX` | 2/2 casos no SHA/build final; `SKIP_LOCAL` preservado separadamente |
| Revisão humana | `EM_EXECUÇÃO` | revisar capturas e roteiro reais no SHA/build final; aceite do proprietário ainda necessário |
| Publicação | `NÃO_AUTORIZADA` | push, merge, tag e release exigem autorização separada |

## Definição de término

A fila só poderá ser marcada como encerrada quando E11, E12 e E13 tiverem
critérios comprovados, todas as regressões estiverem resolvidas ou formalmente
aceitas, o pacote portátil/MSI estiver qualificado, a auditoria final executar
symlinks e revisão humana, e o registro canônico apontar para o SHA/build final.

**Última atualização:** 2026-09-09  
**Próximo status esperado:** concluir E13-D com build final r72, symlink,
revisão humana, findings e decisão formal; somente então encerrar o Plano Mestre.
