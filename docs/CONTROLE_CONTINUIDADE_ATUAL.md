# Controle de continuidade atual — NeoEng-D-Trace

> **Base ativa única (pós-E13):** este checkout e o branch
> `Ailton/e08-renderer-20260908`. Todas as referências a E00–E13, branches,
> worktrees e builds anteriores neste documento são somente histórico e não
> podem ser usados como base de implementação, teste ou promoção.

**Registro canônico da sessão:** `CONTINUITY-NEOENG-20260908`  
**Estado:** `POST_E13_IN_PROGRESS / E13 fechado e congelado como histórico`
**Plano mestre adotado:** `52e9896d2ecf1bc928fb27aca5b8091890c580d7`  
**E01:** checkpoint técnico concluído; aceite final pendente
**E02:** checkpoint técnico aprovado; aceite final pendente
**E10:** `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` — A/B/C/D/E comprovados em Godot 4.7 e Unity 6000.5.7f1
**E11:** `TECHNICAL_CHECKPOINT_PASS` — composição, recovery, exportação, consumo e UX comprovados no r67
**E12:** `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` — A/B/C/D/E comprovados tecnicamente no r69; auditoria final permanece pendente
**Pós-E13:** correções finas do Editor de Cenário, parallax, catálogo de assets,
localização e validação nativa continuam somente sobre o HEAD deste checkout.
O registro formal da fronteira é
`docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`.

Este documento é o ponto único de continuidade operacional. O JSON ao lado é
a fonte estruturada consumida pela validação automática. Governança, decisões
formais e o plano mestre continuam sendo as autoridades superiores; este
registro não cria aceite funcional nem autorização de publicação.

## Fronteira única

O trabalho em andamento está sendo auditado contra o worktree oficial
`Ailton/e08-renderer-20260908`. A fonte de produto da build pós-E13 de autoria
profissional é o commit `c1ea7bc`; o
harness Win32 complementar de captura está preservado no checkout como arquivo
não rastreado preexistente, SHA-256
`A288D676E446E201E814AC396FEF71793FC2B61C5575B03CCBC8F0E25332E008`. A existência de outras branches,
worktrees, builds ou pastas de captura não muda a base ativa. Nenhum artefato
externo pode ser promovido sem `source_commit` verificável.

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
| Suíte oficial | `PASS` | 2196 passaram, 2 skips e 1 warning na requalificação sem filtros do commit `c1ea7bc`; partículas, tilemap/tileset e a correção do auditor de atlas passaram; o abort histórico do magnetic lasso e a falha inicial do auditor permanecem preservados |
| Estática | `PASS_LOCAL_FOCUSED` | compileall e parser PowerShell passaram; matriz funcional/documental focal passou |
| Symlink no Sandbox | `PASS_SANDBOX` | reexecução final no SHA `f8fa83e`: 2/2 casos passaram, 0 skips, JUnit e `report.json` preservados |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; manifests final10 hashados |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | build pós-E13 abriu/fechou; luz direcional, VFX orientável, partículas, tileset/tilemap com duas camadas e três grades foram exercitados com capturas reais; por decisão do proprietário, a revisão humana fica deferida até runtime aplicável de partículas, ferramentas completas de tilemap/tileset e 3D/híbrido passarem |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS` | build `post-e13-tilemap-tileset-20260911-fix`, proveniência `PASS`, executável `D033E4C6DEE0DBE1973038F8496B95230E7A4963E95404E4D9BF01AA482DA498`, ZIP `AC1CA958EA21C7746ECFFB10A103AEB7CE12DAE1945DBEDFFE7AF13A84FD4E7C` e smoke `SUCCESS` em 11 checks |
| Runtime funcional | `PASS` | build pós-E13 corrigida abriu/fechou e executou smoke; autoria nativa de tileset/tilemap foi exercitada com persistência e a equivalência de engine externa continua explicitamente pendente |
| Restauração de continuidade | `PASS_LOCAL_TRACKED_CHECKOUT` | bundle e checkout `3705fa8` restaurados; suíte `1959/2/1`; binário, symlink final e revisão humana permanecem fora deste subgate |

A execução direta da build final10 gerou capturas reais em
`artifacts/post-e13-binary-final10-20260910/`, incluindo catálogo, vetor,
tilemap, tileset, colisores, NavMesh, entidades/prefabs, renderer, material,
parallax, timeline, menus e máscara. A build pós-E13 gerou a evidência
específica em `artifacts/post-e13-native-flow-20260911-camera-timeline/`, e o
incremento de iluminação/VFX gerou `artifacts/post-e13-native-flow-20260911-directional/`,
vinculado a `docs/evidence/EVD_POST_E13_DIRECIONAL_ORIENTAVEL_NATIVE_20260911.md`.
O incremento de partículas corrigido gerou
`artifacts/post-e13-native-flow-20260911-particles-fix/`, vinculado a
`docs/evidence/EVD_POST_E13_PARTICULAS_AUTORIA_RUNTIME_NATIVE_20260911.md`.
A build `post-e13-tilemap-tileset-20260911-fix` gerou o fluxo nativo
`artifacts/post-e13-native-flow-20260911-tilemap-tileset-fix/`, vinculado a
`docs/evidence/EVD_POST_E13_TILEMAP_TILESET_NATIVE_20260911.md`, com atlas,
6084 tiles, 12 células persistidas em duas camadas e grades ortogonal,
isométrica e hexagonal.
A captura automatizada não substitui a revisão humana final.

## Próximo passo permitido

Concluir e comprovar os itens funcionais ainda abertos — runtime aplicável de
partículas, ferramentas avançadas de tilemap/tileset e editor 3D/híbrido — antes de executar a
[auditoria final pós-E13](evidence/AUDITORIA_FLUXO_USUARIO_POS_E13_FINAL_20260910.md)
e a revisão humana final, conforme a
[decisão de deferimento](evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md).
O trabalho técnico do lote, a build e as capturas nativas foram executados;
revisão visual/humana, licença/proveniência de distribuição e os requisitos
funcionais ainda abertos continuam explicitamente separados. O preview de
partículas tem checkpoint técnico, mas a equivalência de runtime/exportação
externa continua `PENDING_EVIDENCE`. O abort legado
permanece como falha histórica preservada, não como resultado atual da suíte.

Não reabrir bases anteriores, não refazer funcionalidades já corrigidas em outra base e
não reutilizar capturas de SHA diferente. A validação de symlink deve ser reportada
em duas linhas: `PASS_SANDBOX` quando os 31 casos passarem no Sandbox e
`SKIP_LOCAL` quando o checkout não tiver privilégio; uma linha nunca substitui
a outra.

## Critério de encerramento de E00

E00 somente pode mudar do checkpoint técnico para `PASS` após a mesma revisão possuir proveniência,
suíte completa, tipagem/estática, build limpa, restauração funcional, symlink
aplicável, captura do binário, revisão visual/humana final e documentação vinculada. Sem
qualquer um desses itens, o estado correto permanece `IN_PROGRESS`,
`PENDING_EVIDENCE` ou `BLOCKED`.
