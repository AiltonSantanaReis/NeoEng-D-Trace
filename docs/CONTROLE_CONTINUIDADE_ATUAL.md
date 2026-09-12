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
`Ailton/e08-renderer-20260908`. No JSON canônico, `checkout_under_audit.head`
identifica a fonte imutável de produto/build do checkpoint integrado (`dd344f47`)
e `documentation_base_head` identifica a base documental usada para preparar a
auditoria de prontidão (`9d0dd6e`). Essa separação é intencional: o registro é
versionado pelo próprio Git e o commit que materializa a versão corrente deve
ser verificado com `git rev-parse HEAD`, em vez de ser duplicado dentro do
próprio arquivo. O campo de base documental não pretende ser o parent de cada
commit posterior de metadados. Os commits anteriores continuam apenas como
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
| Suíte oficial | `PASS` | 2226 passaram, 2 skips e 1 warning na requalificação sem filtros do commit `dd344f47`; a correção de layout da recuperação passou no teste focado e os gates de Tilemap/runtime, adapters híbridos 3D e composição hash-bound passaram; o abort histórico do magnetic lasso, as falhas iniciais do auditor e os aborts diagnósticos dos harnesses permanecem preservados |
| Estática | `PASS_LOCAL_FOCUSED` | compileall e parser PowerShell passaram; matriz funcional/documental focal passou |
| Symlink no Sandbox | `PASS_SANDBOX` | reexecução final no SHA `f8fa83e`: 2/2 casos passaram, 0 skips, JUnit e `report.json` preservados |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; manifests final10 hashados |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | checkpoints nativos do editor, Tilemap/Tileset, partículas e híbrido 3D passaram; os runtimes externos de Tilemap e híbrido 3D passaram com casos negativos; a build v4 e o fluxo nativo da composição integrada passaram tecnicamente com erro/recuperação e persistência; revisão humana final permanece pendente por decisão formal |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS` | build v4 de `dd344f47`, proveniência `PASS`, executável `CBC16B6425158362572848D59D847988F8300455E1AE973DB961A0C2162046A8`, ZIP `D942187979E6BA494256DCA7ADBB2D4FBFCBBAE346FD9D2F55988845028B7C4D` e smoke `SUCCESS` em 11 checks; warning de `tzdata` preservado |
| Runtime funcional | `PASS` | build v4 abriu/fechou o editor, exportou composição, salvou/reabriu, mostrou erro real, recuperou a cópia válida, salvou e exportou novamente; os dois pacotes foram revalidados com Tilemap/runtime hash-bound |
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
A build `post-e13-tilemap-advanced-responsive-20260911` gerou a evidência
`artifacts/post-e13-tilemap-advanced-responsive-native-20260911/`, vinculada a
`docs/evidence/EVD_POST_E13_TILEMAP_ADVANCED_NATIVE_20260911.md`. O fluxo nativo
real expôs Retângulo, Balde, Conta-gotas e Borracha, comprovou `8 → 12 → 8`
células com um Desfazer/Refazer por gesto, manteve as ações visíveis no painel
estreito e salvou/reabriu o mapa com hash preservado. Autotiling/Rule Tiles,
variação avançada, seleção/cópia/colagem completas e runtime externo foram
comprovados nos checkpoints correspondentes; somente refinamentos avançados de
snapping e a revisão humana final continuam explicitamente `PENDING_EVIDENCE`.
A integração do exportador geral no commit `a7e22b3e` emite, quando há atlas
válido, o pacote `tilemap-runtime/` com payload, origem e atlas vinculados por
hash; o teste de contrato passou com `8 passed` e o caminho legado sem atlas
permanece explícito como `not-emitted-legacy-atlas-missing`. O runtime externo
do híbrido 3D também passou no vertical slice em Godot e Unity, com capturas
reais e rejeição de drift preservada. O build v4 e o fluxo nativo da composição
integrada estão documentados em
`docs/evidence/EVD_POST_E13_FINAL_BUILD_COMPOSITION_NATIVE_20260912.md`, com
capturas reais, persistência, recuperação, hashes, atlas e payload runtime.
O defeito de layout da recuperação foi corrigido no commit `dd344f47` sem
remover conteúdo anterior; os resultados v1–v3 permanecem preservados.

A captura automatizada não substitui a revisão humana final.

## Próximo passo permitido

Solicitar e executar a revisão humana final com base na [auditoria final pós-E13](evidence/AUDITORIA_FLUXO_USUARIO_POS_E13_FINAL_20260910.md),
na [auditoria de prontidão para revisão humana](evidence/AUDITORIA_PRONTIDAO_REVISAO_HUMANA_POS_E13_20260912.md),
na build v4 e na evidência nativa já registrada, conforme a
[decisão de deferimento](evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md).
Os gates técnicos externos de Tilemap e híbrido 3D, a ponte de partículas, o
início do cenário do zero, as ferramentas avançadas do tilemap, o build
integrado e seu fluxo nativo já possuem checkpoints técnicos; somente a
auditoria/aceite humano e decisões reservadas permanecem abertas.
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
