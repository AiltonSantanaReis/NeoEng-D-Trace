# E00 — adiamento controlado da verificação de symlinks

**Data:** 2026-09-08  
**Decisão:** `DEFERRED_UNTIL_FINAL_AUDIT`  
**Etapa:** E00  
**Escopo:** apenas a requalificação final de symlinks

O proprietário determinou que a verificação de symlinks seja deixada para o
final do plano, evitando novas repetições durante a continuidade corrente. A
decisão não transforma os dois skips locais nem a ausência de relatório do
Sandbox em PASS, e não invalida o diagnóstico histórico de `35727d9`.

Até a auditoria final, o gate permanece `PENDING_EVIDENCE` e não deve ser
reexecutado. Os demais gates e atividades autorizadas continuam seguindo o
Plano Mestre; E01 só poderá ser aberta quando todos os requisitos de E00 forem
formalmente satisfeitos.
