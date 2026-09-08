# Controle de continuidade atual — NeoEng-D-Trace

**Registro canônico da sessão:** `CONTINUITY-NEOENG-20260908`  
**Estado:** `E00 IN_PROGRESS / PREPARATORY_ONLY`  
**Plano mestre adotado:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**E01:** `NOT_STARTED`

Este documento é o ponto único de continuidade operacional. O JSON ao lado é
a fonte estruturada consumida pela validação automática. Governança, decisões
formais e o plano mestre continuam sendo as autoridades superiores; este
registro não cria aceite funcional nem autorização de publicação.

## Fronteira única

O trabalho em andamento está sendo auditado contra o worktree oficial limpo
`Ailton/e00-continuity-final-20260908` em `5a6275f`. A existência de outras
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
| Suíte oficial | `PASS_LOCAL` | 1959 aprovados, 2 skips, 1 warning |
| Estática | `PASS_LOCAL` | compileall, mypy, Black, isort, Flake8 e diff check |
| Symlink no Sandbox | `PASS_SANDBOX_DIAGNOSTIC_ONLY` | 31 casos, 0 skips; não substitui o gate oficial |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; sem revisão humana |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | revisão deferida por autorização; obrigatória na auditoria final |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS_LOCAL` | commit `5a6275f`, manifesto, hashes e smoke test com 11 verificações |
| Runtime funcional | `PASS_LOCAL` | abertura PT, restauração de geometria, salvamento e fechamento; `failure_count=0` |

A execução direta da build corrigida `5a6275f` gerou as capturas em
`artifacts/e00-continuity-20260908/official-build-5a6275f/captures/`.
Na captura maximizada `1933x1045`, os rótulos `Visualizar` e `Selecionar`
aparecem completos. O finding anterior permanece preservado no pacote
`1a1a0e9`; a correção automatizada não substitui a revisão humana final.

## Próximo passo permitido

Continuar os gates automatizados e as correções controladas de preservação da E00. A revisão
visual/humana foi deferida por autorização explícita para a auditoria final;
ela continua obrigatória antes de marcar E00 como `PASS` ou concluir o plano.

Não iniciar E01, não refazer funcionalidades já corrigidas em outra base e não
reutilizar capturas de SHA diferente. A validação de symlink deve ser reportada
em duas linhas: `PASS_SANDBOX` quando os 31 casos passarem no Sandbox e
`SKIP_LOCAL` quando o checkout não tiver privilégio; uma linha nunca substitui
a outra.

## Critério de encerramento de E00

E00 somente pode mudar para `PASS` após a mesma revisão possuir proveniência,
suíte completa, tipagem/estática, build limpa, restauração funcional, symlink
aplicável, captura do binário, revisão visual/humana final e documentação vinculada. Sem
qualquer um desses itens, o estado correto permanece `IN_PROGRESS`,
`PENDING_EVIDENCE` ou `BLOCKED`.
