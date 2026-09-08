# Metas de execução até o encerramento do Plano Mestre

**Meta ativa:** concluir integralmente o Plano Mestre do NeoEng-D-Trace.  
**Regra de parada:** não encerrar uma rodada por uma pendência intermediária;
parar somente após a conclusão de todas as metas abaixo ou quando uma decisão
do proprietário for indispensável.

## Controle central de status

| ID | Meta | Status atual | Critério de conclusão |
|---|---|---|---|
| M00 | Governança e continuidade | CONCLUÍDA PARA O CHECKPOINT TÉCNICO | Registro único atualizado, worktree E01 identificado, proveniência conferida e nenhuma decisão material implícita |
| M01 | Checkpoint técnico de E00 | CONCLUÍDO — auditoria final pendente | Base restaurável, rastreabilidade/decisões E00 reconciliadas, suite/estática/build/runtime/capturas documentados; symlink e revisão humana ficam para auditoria final |
| M02 | Corrigir findings reproduzíveis | CONTÍNUA | Cada finding recebe causa, correção, teste focado, suíte proporcional, build oficial, captura real e commit rastreável |
| M03 | Validar experiência visual e usabilidade | EM ANDAMENTO | Fluxos reais do binário testados; layout, tradução, scroll, abas, toolbar, acessibilidade e erros sem finding aberto |
| M04 | Symlinks | ADIADA CONTROLADAMENTE | Executar somente na auditoria final do plano; 31 casos, relatório completo e skips locais mantidos separados |
| M05 | Revisão humana final | ADIADA CONTROLADAMENTE | Proprietário revisar o SHA/build final, roteiro, capturas e findings; todas as observações resolvidas ou formalmente aceitas |
| M06 | Fechar E00 | PENDENTE — auditoria final | Symlink, revisão humana, findings finais e demais critérios de fechamento; não é pré-requisito para o checkpoint técnico |
| M07 | E01 — contratos e cena vazia independente | EM ANDAMENTO | Schema/backend decididos, fluxo novo/abrir/salvar/reabrir funcionando no binário, testes e evidências concluídos |
| M08 | E02–E13 | PLANEJADAS | Executar em lotes pequenos, na ordem do Plano Mestre, sem pular dependências |
| M09 | Auditoria final do plano | PENDENTE | Suítes, estática, segurança, portabilidade, engines aplicáveis, capturas e documentação finais aprovadas |
| M10 | Encerramento/publicação | PENDENTE | Auditoria humana concluída, critérios finais satisfeitos e autorização explícita para qualquer push, merge, tag ou release |

## Regras operacionais

1. Usar somente o worktree, commit e binário declarados no registro de
   continuidade.
2. Ler governança, Plano Mestre e decisões vigentes antes de cada lote.
3. Não iniciar E02 enquanto E01 não estiver formalmente aceita; E01 só foi aberta após checkpoint técnico autorizado de E00.
4. Aplicar correções autorizadas somente quando reproduzíveis e dentro do
   escopo da etapa; reconstruir build e evidências após correção.
5. Nunca converter `SKIP`, ausência de relatório ou captura automatizada em
   `PASS`.
6. Preservar evidências históricas e artefatos não relacionados; não limpar
   worktrees nem reescrever snapshots.
7. Atualizar este checklist, o registro JSON e a evidência do lote a cada
   transição de status.

## Estado no momento da criação

- E00: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.
- Correção da toolbar: validada no binário oficial `5a6275f8`.
- Symlinks: `PENDING_EVIDENCE / DEFERRED_UNTIL_FINAL_AUDIT`.
- Revisão humana: `PENDING_EVIDENCE`, deferida até a auditoria final por
  autorização do proprietário.
- E01: `IN_PROGRESS`; E02–E13 ainda não iniciadas.
