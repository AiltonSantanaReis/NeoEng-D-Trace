# Controle de continuidade atual — NeoEng-D-Trace

**Registro canônico da sessão:** `CONTINUITY-NEOENG-20260908`  
**Estado:** `E00 TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING / E01 IN_PROGRESS`
**Plano mestre adotado:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**E01:** `IN_PROGRESS` — checkpoint técnico de E01-A/B/C concluído; aceite final pendente

Este documento é o ponto único de continuidade operacional. O JSON ao lado é
a fonte estruturada consumida pela validação automática. Governança, decisões
formais e o plano mestre continuam sendo as autoridades superiores; este
registro não cria aceite funcional nem autorização de publicação.

## Fronteira única

O trabalho em andamento está sendo auditado contra o worktree E01 dedicado
`Ailton/e01-independent-scene-20260908`, derivado do checkpoint técnico
`4e26f49`. A existência de outras
branches, worktrees, builds ou pastas de captura não muda a base ativa. Nenhum
artefato externo pode ser promovido sem `source_commit` verificável.

Antes de qualquer nova build, registrar no mesmo pacote:

1. branch e SHA de origem;
2. status da árvore rastreada e lista de alterações;
3. ID/hash deste registro;
4. comandos e resultados dos gates;
5. hash do executável, manifesto e capturas;
6. limitações, incluindo skips e bloqueios.

## Status atual

| Gate | Estado | Interpretação |
|---|---|---|
| Suíte oficial | `PASS_LOCAL` | 1973 aprovados, 2 skips, 1 warning |
| Estática | `PASS_LOCAL` | compileall, mypy, Black, isort, Flake8 e diff check |
| Symlink no Sandbox | `PASS_SANDBOX_DIAGNOSTIC_ONLY / PENDING_EVIDENCE / DEFERRED_UNTIL_FINAL_AUDIT` | 31/31 é diagnóstico de SHA anterior; a nova tentativa sem relatório foi registrada e a requalificação foi adiada para a auditoria final |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; sem revisão humana |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | revisão deferida por autorização; obrigatória na auditoria final |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS_LOCAL` | r5, source commit `39c414b`, manifesto, hashes e smoke test com 11 verificações |
| Runtime funcional | `PASS_LOCAL` | abertura PT, restauração de geometria, salvamento e fechamento; `failure_count=0` |
| Restauração de continuidade | `PASS_LOCAL_TRACKED_CHECKOUT` | bundle e checkout `3705fa8` restaurados; suíte `1959/2/1`; binário, symlink final e revisão humana permanecem fora deste subgate |

A execução direta da build corrigida `5a6275f` gerou as capturas em
`artifacts/e00-continuity-20260908/official-build-5a6275f/captures/`.
Na captura maximizada `1933x1045`, os rótulos `Visualizar` e `Selecionar`
aparecem completos. O finding anterior permanece preservado no pacote
`1a1a0e9`; a correção automatizada não substitui a revisão humana final.

## Próximo passo permitido

Consolidar a documentação técnica de E01-A/B/C e produzir somente a análise
preparatória de E02. A revisão visual/humana e a requalificação final de symlink
foram deferidas por autorização explícita para a auditoria final; continuam
obrigatórias antes de marcar E01/E00 como `PASS` ou concluir o plano.

Não iniciar implementação funcional de E02 enquanto E01 não estiver formalmente
aceita; somente documentação `PREPARATORY_ONLY` é permitida. Não refazer
funcionalidades já corrigidas em outra base e não reutilizar capturas de SHA
diferente. A validação de symlink deve ser reportada
em duas linhas: `PASS_SANDBOX` quando os 31 casos passarem no Sandbox e
`SKIP_LOCAL` quando o checkout não tiver privilégio; uma linha nunca substitui
a outra.

## Critério de encerramento de E00

E00 somente pode mudar do checkpoint técnico para `PASS` após a mesma revisão possuir proveniência,
suíte completa, tipagem/estática, build limpa, restauração funcional, symlink
aplicável, captura do binário, revisão visual/humana final e documentação vinculada. Sem
qualquer um desses itens, o estado correto permanece `IN_PROGRESS`,
`PENDING_EVIDENCE` ou `BLOCKED`.
