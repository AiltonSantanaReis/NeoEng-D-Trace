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

O trabalho em andamento está sendo auditado contra o checkout
`Ailton/error-presentation-contract-20260904` em `35727d9`. A existência de
outras branches, worktrees, builds ou pastas de captura não muda a base ativa.
Nenhum artefato externo pode ser promovido sem `source_commit` verificável.

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
| Suíte oficial | `PASS_LOCAL` | 1975 aprovados, 2 skips, 1 warning |
| Estática | `PASS_LOCAL` | compileall, mypy, Black, isort, Flake8 e diff check |
| Symlink no Sandbox | `PASS_SANDBOX_DIAGNOSTIC_ONLY` | 31 casos, 0 skips; não substitui o gate oficial |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; sem revisão humana |
| Auditoria nativa/humana | `BLOCKED` | host de Computer Use sem janela de aplicação |
| Build mais recente | `PENDING_PROVENANCE` | hash localizado, mas sem `source_commit` verificável |

A execução direta da build mais recente observada (`D9422D02…`) gerou a captura
`artifacts/e00-continuity-20260908/captures/01-latest-binary-maximized.png`.
Ela registra truncamento de rótulos da toolbar em `1933x1045`. Esse achado é
diagnóstico da combinação binário/estado/resolução capturada; não pode ser
transferido para outra build nem usado para reabrir correções já qualificadas
em outro SHA sem uma nova execução no mesmo pacote.

## Próximo passo permitido

Produzir uma build oficial a partir de uma única árvore limpa e explicitamente
identificada, com o manifesto de proveniência obrigatório. Depois executar o
binário dessa build, capturar os fluxos do usuário e atualizar este registro
no mesmo pacote. Até isso acontecer, a build `fixed2` é apenas um artefato
observado, não a build canônica do projeto.

Não iniciar E01, não refazer funcionalidades já corrigidas em outra base e não
reutilizar capturas de SHA diferente. A validação de symlink deve ser reportada
em duas linhas: `PASS_SANDBOX` quando os 31 casos passarem no Sandbox e
`SKIP_LOCAL` quando o checkout não tiver privilégio; uma linha nunca substitui
a outra.

## Critério de encerramento de E00

E00 somente pode mudar para `PASS` após a mesma revisão possuir proveniência,
suíte completa, tipagem/estática, build limpa, restauração funcional, symlink
aplicável, captura do binário, revisão visual e documentação vinculada. Sem
qualquer um desses itens, o estado correto permanece `IN_PROGRESS`,
`PENDING_EVIDENCE` ou `BLOCKED`.
