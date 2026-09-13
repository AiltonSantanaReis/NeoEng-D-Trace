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
Nesta meta, a revisão humana foi aprovada pelo proprietário; os gates técnicos
restantes continuam independentes e não são encerrados por essa aprovação.
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

A regressão oficial segura mais recente foi capturada sem filtros em
`artifacts/audit-post-e13-official-suite-safe-host-20260913-r12/official-pytest.log`,
com SHA-256 `171F156EDDA800951356FB4244459CAE08CE20D18B5E1E3CA870399CE4B1A0A3`:
`2634 passed, 2 skipped, 0 warnings` em 84,83 s. O JUnit tem SHA-256
`D75ECAB717E4752250FE85E0EEE9EB3F2336EEB239A23C161D80E304AACA2113`.
O pacote r3 anterior, inclusive o log com cinco warnings preservado antes
da correção, permanece disponível para comparação histórica.

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
de produto qualificada e o `product_source_commit` estão no commit `7f5c047`,
o harness de captura nativa está no commit `b20f2f1` e o HEAD documental
completo deve ser obtido por `git rev-parse HEAD`; o campo `head` do JSON não
é uma auto-referência do commit documental. A
requalificação corrente de runtime está em
`evidence/EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md`.

| Gate | Estado | Interpretação |
|---|---|---|
| Suíte oficial | `PASS` | r12: 2634 passaram, 2 skips controlados e 0 warnings na requalificação sem filtros; os dois skips são symlink protegido no host e foram comprovados no sandbox; failures históricos permanecem preservados |
| Estática | `PASS_LOCAL_FOCUSED` | compileall e parser PowerShell passaram; matriz funcional/documental focal passou |
| Symlink no Sandbox | `PASS_SANDBOX` | requalificação definitiva controlada r4 vinculada ao commit consolidado: 31/31 passaram, 0 skips, 0 falhas/erros; JUnit, relatório e hashes em `artifacts/audit-post-e13-symlink-sandbox-20260913-r4/` |
| Symlink no checkout local | `SKIP_CONTROLLED_ONLY` | 2 skips preservados, a barreira impede criação nativa antes de `symlink_to`; não convertidos em PASS |
| Captura automatizada | `PASS_AUTOMATED_CAPTURE_ONLY` | janela real capturada por handle; manifests final10 hashados |
| Auditoria nativa/humana | `PASS` para a revisão humana; lote técnico `IN_PROGRESS` | checkpoints nativos do editor, Tilemap/Tileset, partículas e híbrido 3D passaram; a revisão humana foi aprovada em `docs/evidence/DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md`; responsividade residual continua `FAIL` aceita formalmente, memória longa está `PASS` no soak controlado, GPU/janela QGraphicsView está `NOT_APPLICABLE` por ausência de contador; Unity r12 iniciou em Sandbox com rede habilitada, transportou o candidato atualizado e alcançou o LicensingClient, mas encontrou zero entitlements aplicáveis; a inconsistência de metadado do r11 foi preservada; licensing limpo e shutdown limpo permanecem `BLOCKED` |
| Correção controlada E00 | `PASS_LOCAL` | toolbar desktop dimensionada pelo `sizeHint`; regressão responsiva coberta |
| Build oficial | `PASS` | build portátil r5 da fonte `98ee5b4` tem executável `1D3AC2A89C35F807AEC9E707310F410FC71785ABF463E9A65DF6ACFBA3FAF403`, ZIP `63A71E5501F5165A4E7A90AD2161605C4DB4631B2DF510F1F36BC3BC203BD713` e smoke `SUCCESS` em 11 checks; `tzdata` carregado sem hidden import ausente e warnings opcionais preservados |
| Runtime funcional | `PASS` | build v4 abriu/fechou o editor, exportou composição, salvou/reabriu, mostrou erro real, recuperou a cópia válida, salvou e exportou novamente; os dois pacotes foram revalidados com Tilemap/runtime hash-bound |
| Runtime nativo de partículas | `PASS` | sidecar V1 e origem autorada V2 consumidos; Godot gerou captura rasterizada, Unity passou em `batchmode/nographics`, guards negativos passaram e a revisão humana foi aprovada |
| Exportação profissional de partículas | `PASS` | auditoria v15 com 17/17 checks, socket VFX fail-closed, persistência/hash e captura Godot Windows/OpenGL; o fluxo limpo de Cenário vazio passou com criação, salvamento e recarga nativos |
| Diagnósticos Unity controlados | `PASS` do classificador; `BLOCKED` para ambiente limpo | logs históricos positivos/negativos foram classificados em Docker; o r12 iniciou Unity real em Windows Sandbox com rede habilitada, copiou o candidato atualizado com SHA confirmado, observou LicensingClient, `Code 10`, token ausente, `404` com zero entitlements e código 198; o r11 ficou preservado como falha de metadado do harness; a sandbox encerrou, mas licensing limpo, método do pacote e shutdown limpo do Unity continuam não comprovados |
| CuPy | `PASS` da avaliação; `NOT_APPLICABLE` como dependência oficial | caminho opcional X-Ray comprovado no ambiente local, ganho somente no workload grande medido; não há evidência de que o gargalo do editor seja CuPy e a build portátil continua CPU/fallback |
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
snapping continuam explicitamente `PENDING_EVIDENCE`. A revisão humana foi
aprovada separadamente pelo proprietário.
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

O Unity 6000.5.7f1 foi executado duas vezes em `batchmode/nographics` antes da
política de segurança desta meta: os gates positivo/negativo passaram com
retorno `0`, enquanto `Code 10` do Licensing Client, token ausente, timeout/Curl
e `abort_threads` foram preservados e classificados como `PENDING_EVIDENCE`
para a causa/estabilidade do ambiente. O entitlement `Unity Personal` foi
resolvido nos dois logs. Essa qualificação histórica está em
`evidence/EVD_POST_E13_RUNTIME_REQUALIFICACAO_20260913.md` e não substitui o
ensaio controlado desta meta.

Nesta meta, o classificador somente leitura foi executado em Docker sem rede e
passou nos testes focados, classificando os logs preservados. O resultado está
em `evidence/EVD_POST_E13_UNITY_DIAGNOSTICOS_CONTROLADOS_20260913.md`. Isso
fecha a observabilidade do diagnóstico, mas não converte licensing limpo ou
shutdown/soak limpo em `PASS`. Após a VM preexistente ser liberada, o r9 iniciou
Unity real em Windows Sandbox e preservou o primeiro resultado. O r10 usou um
candidato atualizado, copiou-o com hash confirmado e alcançou o LicensingClient;
zero entitlements aplicáveis novamente encerrou a execução antes do pacote. O
r11 repetiu a fixture em WSB com rede habilitada, mas o runner herdado registrou
`networking=disabled` no resultado; essa inconsistência de instrumentação foi
mantida como `FAIL` do harness e não foi corrigida retroativamente. O r12
corrigiu somente esse metadado, repetiu a execução com rede habilitada registrada
de forma coerente e obteve o mesmo `Code 198`/zero entitlement. O shutdown da
sandbox foi comprovado em todas as tentativas, e a evidência hashada de r1–r12
está em `evidence/EVD_POST_E13_UNITY_CONTROLADO_SANDBOX_20260913.md`.

O r11 possui resultado `21429CA41A3BFB2293C70A63A831BFF3EC53100A04B3CC58AA6E905B7F0C3017`,
log bruto local `FEAD966D64FFE466E8D7E062F32CD904F0B010946D3CA5F02A5065A7C1094153`,
projeção sanitizada `97441BA7E373BDB435D6817A5B4C3A086D68C963078D0703D3133A9B6D21EAF1`,
runner `4D8243FEFE284C310FD91C5C1506135CA644E525933CABAC88B8D4AF5FFEA261` e WSB
`6E61952B3ED34F8AE2ABC812DC5BCF02C391246B39FE4F1B8C7A0372F1999060`. O r12
possui resultado `3F91FC2E5E82D9FCA7702289B686D28DEEE276658C1F377E9B9ED8E29743E0B8`,
log bruto local `96E220638A19A677ADF9D6F81381E2EFE4A887D7B08A60A75E1E13B33DD01E8A`,
projeção sanitizada `7D0FDC95E631C30EFD00535D33E9BD6DCEE9166FFAF813B3600826F90E873598`,
runner `1ACA40E88B8DDEC7D3C16CF4C1EED8C95C2ED869A5BC2E31DA86A1EC4BEC781D` e WSB
`22400D86B5C909D7267FC2B19A99BAEE1B20FD9BD92B78600A2F625D7913C96B`. Os logs
brutos permanecem fora do Git; as projeções sanitizadas preservam os warnings,
erros e sinais funcionais necessários para auditoria.

A captura automatizada não substitui a revisão humana final; essa revisão foi
registrada como aprovada pelo proprietário em
`evidence/DECISAO_REVISAO_HUMANA_APROVADA_POS_E13_20260913.md`.

## Próximo passo permitido

O subestágio de investigação estrutural em escala e a evidência nativa 2D/3D/
híbrida do editor canônico estão tecnicamente fechados e não devem ser refeitos
sobre base anterior. A meta vigente fechou a suíte r12 sem warnings, o retry
atômico do atlas, o empacotamento `tzdata`, avaliou CuPy sem adoção oficial,
qualificou a memória em soak controlado e registrou a limitação objetiva de GPU;
permanece somente a qualificação Unity de licensing/shutdown limpos, atualmente
`BLOCKED` porque r9, r10 e a execução coerente r12 não forneceram entitlement válido na
sandbox. O carregamento Unity e o shutdown da sandbox já foram comprovados. A revisão humana já foi
aprovada; o gizmo e a produção de modelos/asset packs permanecem adiados por
decisão do proprietário.
Os requisitos funcionais, a revisão visual/humana e a licença/proveniência de
distribuição continuam explicitamente separados. A equivalência
V2→exportação Godot/Unity de partículas tem checkpoint técnico; o abort legado
permanece como falha histórica preservada, não como resultado atual da suíte.

Não reabrir bases anteriores, não refazer funcionalidades já corrigidas em outra base e
não reutilizar capturas de SHA diferente. A validação de symlink deve ser reportada
em duas linhas: `PASS_SANDBOX` quando os 31 casos passarem no Sandbox e
`SKIP_LOCAL` quando o checkout não tiver privilégio; uma linha nunca substitui
a outra. Por segurança, symlink e shutdown não devem ser executados nativamente
neste host; a execução controlada atual só deve ser repetida após mudança
relevante conforme `EVD_POST_E13_SYMLINK_SANDBOX_DEFINITIVO_20260913.md`.

## Candidato local de licença Unity

Uma inspeção estrutural read-only encontrou um possível entitlement local em
`C:/Users/atnco/AppData/Local/Unity/licenses/UnityEntitlementLicense.xml`.
O candidato histórico usado no r9 tinha 6.731 bytes e SHA-256
`89525CC063037191D198C1D3FF19FF566AB32BD6E3D3D917274EFCC8665B8926`; o
candidato corrente usado em r10, r11 e r12 tem 6.731 bytes e SHA-256
`C5CF45D8D85B08FAE7CD857499ADDA505BD06D29C456F4F9E7720DE94BCD0498`.
Nenhum valor foi exposto, os mapeamentos foram read-only e as cópias ocorreram
somente dentro da sandbox descartável. O Unity confirmou zero entitlements
aplicáveis nos ensaios correntes; o arquivo não é prova de licença válida para
`6000.5.7f1`.

## Critério de encerramento de E00

E00 somente pode mudar do checkpoint técnico para `PASS` após a mesma revisão possuir proveniência,
suíte completa, tipagem/estática, build limpa, restauração funcional, symlink
aplicável, captura do binário, revisão visual/humana final e documentação vinculada. Sem
qualquer um desses itens, o estado correto permanece `IN_PROGRESS`,
`PENDING_EVIDENCE` ou `BLOCKED`.
