# Decisão de continuidade técnica E01–E13 com auditoria final deferida

**Data:** 2026-09-08  
**Autoridade:** autorização explícita do proprietário registrada na conversa e
na decisão `DECISAO_CONTINUIDADE_POS_E00_GATES_DEFERIDOS_2026-09-08.md`  
**Estado:** `AUTHORIZED / TECHNICAL_CONTINUATION_UNTIL_FINAL_AUDIT`

## Decisão

Os lotes E01–E13 podem ser executados sequencialmente em checkpoints técnicos,
sem esperar a revisão humana e a requalificação final de symlinks entre lotes.
Essas pendências ficam reservadas exclusivamente para a auditoria final do
Plano Mestre, no SHA/build final.

Esta decisão não encerra E00 ou qualquer etapa, não transforma `PENDING_EVIDENCE`
em `PASS`, não autoriza publicação e não elimina nenhum requisito. Cada etapa
deverá ter implementação, testes, build, captura, documentação, rollback e
estado técnico próprio. O aceite formal de fechamento permanece condicionado à
auditoria final.

## Fronteiras obrigatórias

- uma única branch/worktree ativa por lote, com SHA e proveniência declarados;
- nenhum symlink durante os lotes intermediários;
- nenhuma revisão humana declarada por inferência de captura automatizada;
- nenhuma etapa posterior poderá justificar a conclusão da etapa anterior;
- qualquer finding reproduzível será corrigido no lote correspondente e
  requalificado no binário gerado daquele SHA;
- push, merge, tag, release e publicação continuam proibidos sem autorização
  separada.

## Critério de promoção técnica

Uma etapa pode deixar `PLANNED` e entrar em `IN_PROGRESS` somente quando a
etapa anterior possuir checkpoint técnico documentado, sua dependência estiver
preservada e o registro central apontar para a branch/worktree do novo lote.
Uma etapa só poderá ser marcada como concluída após todos os critérios finais,
incluindo auditoria humana e symlink quando aplicáveis.

## Aplicação imediata

E01-A/B/C possui checkpoint técnico documentado em suas três evidências. E02
será aberto agora em branch própria, inicialmente pelo sub-lote de contrato e
modelo de primitivas. A preparação E02 já existente será mantida como histórico;
ela não será usada como prova de implementação.
