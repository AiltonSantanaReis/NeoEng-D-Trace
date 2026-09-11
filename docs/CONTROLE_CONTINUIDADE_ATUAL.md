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
`Ailton/e08-renderer-20260908`. A fonte de produto da build pós-E13 mais
recente é o commit `73b7fccd`; os commits anteriores continuam apenas como
proveniência dos checkpoints específicos; o
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
| Suíte oficial | `PASS` | 2208 passaram, 2 skips e 1 warning na requalificação sem filtros do commit `73b7fcc`; a ponte de partículas autoradas, o editor híbrido e os contratos de tilemap/tileset passaram; o abort histórico do magnetic lasso, as falhas iniciais do auditor e os aborts diagnósticos do harness permanecem preservados |
| Estática | `PASS_LOCAL_FOCUSED` | compileall e parser PowerShell passaram; matriz funcional/documental focal passou |
| Symlink no Sandbox | `PASS_SANDBOX` | reexecução final no SHA `f8fa83e`: 2/2 casos passaram, 0 skips, JUnit e `report.json` preservados |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; manifests final10 hashados |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | build pós-E13 abriu/fechou e o fluxo Win32 real foi capturado; runtime nativo de partículas, exportação profissional V2 e o fluxo limpo de criar/salvar/recarregar cenário vazio passaram checkpoints; a sequência histórica com popup de Colisão permanece preservada; ferramentas completas de tilemap/tileset, runtime 3D externo e a revisão humana final continuam pendentes por decisão formal |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS` | build `post-e13-particle-scene-export-native-20260911`, proveniência `PASS`, executável `E6716E67305268F432FDB7536A96A22608C6408AD73099225ED2540C8FD5D80B`, ZIP `B72BB9C7034CB41D814BE90C56CF0A3522D8337FF596989A7CA03C912A50E5B5` e smoke `SUCCESS` em 11 checks |
| Runtime funcional | `PASS` | build pós-E13 de partículas abriu/fechou e executou smoke; exportação V2, materialização nativa e contagem foram comprovadas em Godot/Unity; runtime 3D externo, tilemap/tileset completo e finding de início do zero continuam pendentes |
| Runtime nativo de partículas | `PASS` | sidecar V1 e origem autorada V2 consumidos; Godot gerou captura rasterizada, Unity passou em `batchmode/nographics`, guards negativos passaram e a revisão humana permanece deferida |
| Exportação profissional de partículas | `PASS` | auditoria v15 com 17/17 checks, socket VFX fail-closed, persistência/hash e captura Godot Windows/OpenGL; o fluxo limpo de Cenário vazio passou com criação, salvamento e recarga nativos |
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
A build `post-e13-hybrid-3d-20260911` gerou o fluxo nativo
`artifacts/post-e13-native-flow-20260911-hybrid-v9/`, vinculado a
`docs/evidence/EVD_POST_E13_HYBRID_3D_NATIVE_20260911.md`, com cena iniciada
sem asset 2D obrigatório, plano, luz, câmeras, hierarquia, alvo PT-BR,
arraste, órbita, 2.5D, projeção ortográfica, salvar/reabrir e sidecar
`EDITOR_VERTICAL_SLICE` persistido.
A build `post-e13-particle-scene-export-native-20260911` gerou a ponte nativa
de partículas autoradas em
`artifacts/post-e13-particle-scene-export-native-20260911-v15/`, vinculada a
`docs/evidence/EVD_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md`, com
17/17 checks, captura Godot real, logs Godot/Unity, guards negativos, binário
portátil e fluxo Win32 real. O finding do workspace vazio foi preservado.
A requalificação nativa em
`artifacts/post-e13-native-binary-20260911-particles-requal-v2/` confirmou o
fluxo direto `Cenário → Novo Cenário → Salvar Projeto → Recarregar` sem
projeto/imagem inicial. A sequência anterior que clicou primeiro em Colisão
permanece preservada como finding de entrada sobre popup em primeiro plano.
A captura automatizada não substitui a revisão humana final.

## Próximo passo permitido

Concluir e comprovar os itens funcionais ainda abertos — ferramentas avançadas
de tilemap/tileset e o runtime 3D externo do editor híbrido. A ponte de
partículas e o início do cenário do zero já possuem checkpoints técnicos, mas
isso não substitui a revisão humana. Só depois executar a
[auditoria final pós-E13](evidence/AUDITORIA_FLUXO_USUARIO_POS_E13_FINAL_20260910.md)
e a revisão humana final, conforme a
[decisão de deferimento](evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md).
O trabalho técnico do lote, a build e as capturas nativas foram executados;
revisão visual/humana, licença/proveniência de distribuição e os requisitos
funcionais ainda abertos continuam explicitamente separados. A equivalência
V2→exportação Godot/Unity de partículas tem checkpoint técnico; o abort legado
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
