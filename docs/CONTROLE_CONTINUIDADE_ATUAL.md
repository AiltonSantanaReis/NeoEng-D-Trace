# Controle de continuidade atual — NeoEng-D-Trace

> **Base ativa única (pós-E13):** este checkout e o branch
> `Ailton/audit-post-e13-scenario-editor-20260912`. Todas as referências a E00–E13, branches,
> worktrees e builds anteriores neste documento são somente histórico e não
> podem ser usados como base de implementação, teste ou promoção.

**Registro canônico da sessão:** `CONTINUITY-NEOENG-20260908`  
**Reconciliado em 2026-09-13:** branch atual, HEAD documental, produto/harness,
suíte corrente e próxima ação estão registrados em
`docs/evidence/CHG_POST_E13_CONTINUIDADE_RECONCILIACAO_20260913.md`.
**Arquivo legado reconciliado em 2026-09-13:** execuções históricas não
referenciadas foram movidas de forma reversível para
`archive/legacy/artifacts/post-e13-historical-20260913/`, com manifesto e
hashes em `docs/evidence/CHG_POST_E13_ARQUIVO_LEGADO_ARTEFATOS_20260913.md`.
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

O trabalho em andamento é auditado exclusivamente neste checkout e no branch
`Ailton/audit-post-e13-scenario-editor-20260912`. No JSON canônico,
`checkout_under_audit.branch` e `checkout_under_audit.product_source_commit`
identificam a base atual de produto/harness; `documentation_base_head` identifica
somente a base documental usada para preparar a auditoria de prontidão. A
separação é intencional: o registro é versionado pelo próprio Git e o commit que
materializa a versão corrente deve ser verificado com `git rev-parse HEAD`, em
vez de ser duplicado dentro do próprio arquivo. O campo de base documental não
pretende ser o parent de cada commit posterior de metadados. Os commits e
branches anteriores, incluindo `Ailton/e08-renderer-20260908` e `dd344f47`,
continuam apenas como proveniência dos checkpoints específicos; o
harness Win32 complementar de captura está preservado no checkout como arquivo
não rastreado preexistente, SHA-256
`A288D676E446E201E814AC396FEF71793FC2B61C5575B03CCBC8F0E25332E008`. A existência de outras branches,
worktrees, builds ou pastas de captura não muda a base ativa. Nenhum artefato
externo pode ser promovido sem `source_commit` verificável.

Os artefatos históricos que não tinham referência na árvore rastreada foram
preservados, sem exclusão, em
`archive/legacy/artifacts/post-e13-historical-20260913/`. O manifesto final
hashado é `archive-manifest.json` (SHA-256
`2E89672381BEF30BFAFD5E773D41FF0BDBDF742F99379B23A9A800CA5529F666`), com
22 diretórios e 541 arquivos. O diretório inicialmente selecionado que era
rastreado pelo Git foi restaurado; a auditoria está em
`restoration-audit-mask-viewer-r3.json` (SHA-256
`0C9E05251F4F973B04520A1D3A497BDBCBC64EDA12B2BF2CD4FEF17C4E72BE7B`). O
pacote corrente da suíte oficial permanece em `artifacts/` e não foi arquivado.

A revalidação oficial pós-commit foi capturada sem filtros em
`artifacts/audit-post-e13-official-suite-20260913-r1/official-pytest.log`, com
SHA-256 `065E565085828EB3F1702CE210AC0BD75B7001D321173A2EBF9AFBD55556E7C0`:
`2625 passed, 2 skipped, 5 warnings` em 77,51 s. O metadata da execução tem
SHA-256 `962D963030F4DA19EBBA85632E4500946CD499A19738933B2FD761C86CA7115F`.

Antes de qualquer nova build, registrar no mesmo pacote:

1. branch e SHA de origem;
2. status da árvore rastreada e lista de alterações;
3. ID/hash deste registro;
4. comandos e resultados dos gates;
5. hash do executável, manifesto e capturas;
6. limitações, incluindo skips e bloqueios.

## Status atual

O ponteiro histórico abaixo é preservado para proveniência. Para a execução
atual, o checkout é `Ailton/audit-post-e13-scenario-editor-20260912`, a fonte
de produto qualificada está no commit `7f5c047`, a documentação corrente está
no HEAD `c433960`, o harness de captura nativa está no commit `b20f2f1` e o
HEAD documental completo deve ser obtido por `git rev-parse HEAD`. A
requalificação corrente de runtime está em
`evidence/EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md`.

| Gate | Estado | Interpretação |
|---|---|---|
| Suíte oficial | `PASS` | 2626 passaram, 2 skips e 5 warnings na requalificação sem filtros da fonte de produto `7f5c047`; os resultados anteriores, o abort histórico do magnetic lasso, as falhas iniciais do auditor e os aborts diagnósticos dos harnesses permanecem preservados |
| Estática | `PASS_LOCAL_FOCUSED` | compileall e parser PowerShell passaram; matriz funcional/documental focal passou |
| Symlink no Sandbox | `PASS_SANDBOX` | reexecução final no SHA `f8fa83e`: 2/2 casos passaram, 0 skips, JUnit e `report.json` preservados |
| Symlink no checkout local | `SKIP_PRIVILEGE_LIMITATION` | 2 skips preservados, não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; manifests final10 hashados |
| Auditoria nativa/humana | `PENDING_EVIDENCE` | checkpoints nativos do editor, Tilemap/Tileset, partículas e híbrido 3D passaram; a requalificação r3 dos runtimes externos de Tilemap e híbrido 3D passou com casos negativos; a investigação estrutural em escala e o fluxo nativo canônico 2D/3D/híbrido passaram tecnicamente, os diagnósticos Unity foram reexecutados e classificados sem ocultação, mas a responsividade residual, diagnóstico de ambiente Unity e revisão humana permanecem pendentes |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS` | builds históricas preservadas; build pós-performance r3 da fonte `7f5c047` tem executável `F56E7E45534087F2E103FD5DD455C8E402DBA9864B40C060A985DFDE58CFCCBD`, ZIP `4CF2E538C1D7B22B48D6376B07C1CED5BC8841E801E29C4A7ABA5B6E5A860106` e smoke `SUCCESS` em 11 checks; warning de `tzdata` preservado |
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
reais e rejeição de drift preservada. A requalificação corrente está em
`artifacts/post-e13-hybrid-runtime-engines-requalified-v3-20260912/`, com
relatório SHA-256 `C163E8B103B67700B4F801078079E960B51AEDB9DBD9DDEC3C915984AB1E5F37`.
O build v4 e o fluxo nativo da composição
integrada estão documentados em
`docs/evidence/EVD_POST_E13_FINAL_BUILD_COMPOSITION_NATIVE_20260912.md`, com
capturas reais, persistência, recuperação, hashes, atlas e payload runtime.
Durante a auditoria visual, a captura nativa de Tilemap anterior foi
rebaixada a finding porque todas as imagens mostravam `Sem mapa` e não
comprovavam pintura. O harness foi corrigido sem tocar no produto e o fluxo
foi requalificado no executável v4 em
`artifacts/post-e13-tilemap-runtime-native-requalified-v3-20260912/`:
`Novo → canvas → três células → Salvar → Reabrir`, com sidecar persistido de
1 camada/3 células e SHA-256
`282F5D8B094B1A2BA98BDE991FEECB642239D9F8C05F061F01A2D5185E339FC0`.
O Tileset também foi requalificado no v2 no mesmo binário, com 300 tiles,
salvar/reabrir nativos e sidecar `neoeng-d-trace-tileset` SHA-256
`E052E41671B87914D0B7C4A31783AFE59D5AE91B1B6F8CC2E5C572FEA45D5E06`.
O defeito de layout da recuperação foi corrigido no commit `dd344f47` sem
remover conteúdo anterior; os resultados v1–v3 permanecem preservados.

A investigação estrutural em escala foi fechada tecnicamente no commit
`7f5c047`: o benchmark limpo r9 (`26/26`, zero erros e zero falhas de
determinismo) comprovou a redução de `61,72%`–`71,51%` no workload de `512`
assets únicos, mas manteve `FAIL` de responsividade pelo p95 residual de
`249,28`–`398,73 ms`. O relatório e os quatro perfis causais estão em
`evidence/AUDITORIA_POST_E13_PERFORMANCE_BASELINE_20260913.md`, e o fluxo
nativo atual do editor canônico está em
`artifacts/audit-post-e13-binary-performance-20260913-r4/actions.json`, com
`PASS_NATIVE_FLOW`, 14 capturas e sidecar reaberto após relançamento.

O Unity 6000.5.7f1 foi executado duas vezes em `batchmode/nographics`: os
gates positivo/negativo passaram com retorno `0`, enquanto `Code 10` do
Licensing Client, token ausente, timeout/Curl e `abort_threads` foram
preservados e classificados como `PENDING_EVIDENCE` para a causa/estabilidade
do ambiente. O entitlement `Unity Personal` foi resolvido nos dois logs. A
qualificação está em
`evidence/EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md`.

A captura automatizada não substitui a revisão humana final.

## Próximo passo permitido

O subestágio de investigação estrutural em escala, qualificação dos
diagnósticos Unity e evidência nativa 2D/3D/híbrida do editor canônico está
tecnicamente fechado e não deve ser refeito sobre base anterior. Permanecem
como próximos itens apenas a responsividade residual em escala, memória longa,
GPU/janela nativa, diagnóstico de ambiente Unity, limites do vertical slice e
revisão humana final. Somente depois que todos os itens exigidos
pela [decisão de revisão humana](evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)
forem implementados, testados, executados no binário e comprovados com captura,
persistência e hash será permitido solicitar a revisão humana final. O gizmo e
a produção de modelos/asset packs permanecem adiados por decisão do proprietário.
Os requisitos funcionais, a revisão visual/humana e a licença/proveniência de
distribuição continuam explicitamente separados. A equivalência
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
