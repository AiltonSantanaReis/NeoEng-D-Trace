# Plano Mestre de Estabilização — NeoEng-D-Trace

## Atualização viva — lote corretivo da Caneta — 05/09/2026

A branch Ailton/pen-handles-quantization-20260905, baseada em 5b3e6b1,
corrige a origem de tangentes implícitas e implementa alças apenas por arraste
explícito. Os controles existentes do validador e da quantização não foram
alterados. A rodada focada passou 69/69; a suíte agregada local permanece
FAIL diagnóstico (2016 passed, 2 skipped, 1 failed), com a mesma falha
modal reproduzida na base limpa. Estado IN_PROGRESS / PRECOMMIT_PENDING;
runner oficial, build, CI e publicação continuam bloqueados até aceite do
patch exato e requalificação limpa.
Registro: LOTE_CANETA_ALCAS_QUANTIZACAO_2026-09-05.md.

## Atualização viva — correção de idioma/status P2D-05 — 05/09/2026

Base `4b873c3`; o proprietário autorizou corrigir os achados de idioma da
Caneta e leitura/acesso aos detalhes do canal STATUS. Estado IN_PROGRESS,
em pré-commit; geometria e histórico protegidos. Não herda CI, symlinks ou
revisões humanas de pais. PRECOMMIT e qualificação pós-commit pendentes;
PR #170 em rascunho, Ready/merge/tag/release BLOCKED.
[Fronteira e gates](P2D05_LOTE_IDIOMA_STATUS_2026-09-04.md).

R2 local registrada: 1.968 testes aprovados, dois symlinks com WinError 1314;
cobertura/estática/integridade passaram. Runner legado FAIL por árvore suja,
build limpo e revisão humana pendentes. Próximo ponto: aceite PRECOMMIT do
pacote exato, sem declarar etapa concluída ou iniciar outro workstream.

## Atualização viva — sincronização P2D-05 — 04/09/2026

O SHA `35727d9` passou no CI Linux/Windows `33932398814`, com 1.956
testes Windows e zero skips, incluindo os dois symlinks. A PR #170 continua
em rascunho. O proprietário autorizou preservar o histórico privado e
sincronizar main `b9557e6` na candidata, sem merge da PR ou publicação de
históricos privados. A integração exige gates próprios e revisão humana
vinculada à candidata exata; o CI de entrada não aprova seu descendente.
Estado global `IN_PROGRESS`; Ready, merge, tag e release `BLOCKED`.
Fronteira e evidência: [registro vivo P2D-05](P2D05_REQUALIFICACAO_ATUAL.md).

## Snapshot anterior — P2D-05 — fonte efb0caf

Fonte local `efb0caf`, branch `Ailton/error-presentation-contract-20260904`:
tipagem e baseline corrigidos; integridade rastreada aprovada no checkout limpo.
Requalificação `PARCIAL` pelos dois skips de symlink e pelos gates humanos e
remotos pendentes; publicação `BLOCKED`. O commit documental descendente não
é apresentado como tendo executado a suíte completa do SHA-fonte.
O [registro vivo P2D-05](P2D05_REQUALIFICACAO_ATUAL.md) discrimina escopo,
integridade versionada, artefatos locais preservados e gates pendentes.
Os registros abaixo conservam os fatos de suas revisões anteriores; não
atestam o HEAD atual nem autorizam avançar para outro lote.

O plano vivo `docs/PLANO_INTERFACE_MODERNA_PROFISSIONAL_2026-08-21.md` é a fonte de verdade do escopo específico de modernização da interface. Ele permanece subordinado a este plano mestre e às demais governanças; em 21 de agosto de 2026 a Etapa 0 está aprovada somente no escopo de baseline visual, enquanto as Etapas 1–14 permanecem planejadas. O plano não autoriza, por si só, implementação, merge ou release.

Baseline deste snapshot: `baseline_manifest.json`, atualizado em 18 de agosto de 2026.

## Snapshot histórico — encerramento pós-merge LEGACY-26 — 04 de setembro de 2026

A revisão corrente é a integração da PR `#168` em `main`, pelo merge commit
`9a25f0be0ea47a092e90c0194797ddcaf33a7dcf`. O produto foi validado no SHA
`6ede2f6073f6d2aaf5a394e4043019a3ac85a5e4`; o commit-fonte da PR é
`9adb66a5ab9cfaabc1703d4b9b225b141473ec52`.

O CI pós-merge `33871734689` passou em Linux e Windows, incluindo baseline,
integridade de evidências, suíte/cobertura, estática, segurança, Stage 4B.5,
runner legado formal e verificação da árvore-fonte. C01–C13 estão `PASS` no
escopo comprovado e o plano mestre está `APROVADO / CONCLUÍDO NO ESCOPO
COMPROVADO`. Os snapshots legados e as limitações de proveniência permanecem
explícitos. Tag e release continuam sem aprovação.

## Snapshot histórico — encerramento pós-merge da PR #166 — 03 de setembro de 2026

A PR `#166` foi integrada no merge commit
`8a97ae14e8f84eb86fcacfaefed61f014830fbf9`, originada no commit-fonte
`c6a2d18f9c6bcd48dba65b0df333a813ad6b86b3`. O CI pós-merge `33794660766`,
disparado por `push` em `main`, passou nos jobs Linux `100779319495` e Windows
`100779319836`.

A execução pós-merge confirmou baseline de `3213` arquivos e integridade de
`130` manifestos. Linux passou com `1919 passed` e um warning. Windows aceitou
`189/189` arquivos, `1919` testes, `0` falhas, `0` erros e `0` skips. A
cobertura foi `92,60%` de linhas e `85,03%`/`85,05%` de branches em Linux e
Windows, respectivamente. Lock, compilação, estática, segurança, Stage 4B.5
e o gate formal também passaram.

O gate formal preservou o histórico bruto `196/26/0/0`, retorno `1`, com `15`
falhas exatas, `11` assinaturas divergentes, `12` ausências e `42` substitutos.
Os snapshots legados continuam imutáveis. O JUnit Windows confirmou os dois
contratos de symlink; a prova VMware permanece scoped à reconstrução ZIP/patch.

Estado atual: Etapa 7 `APROVADA NO ESCOPO DA PR #166`; plano global
`IN_PROGRESS`; tag e release `BLOCKED`. Evidência pós-merge:
`docs/evidence/ETAPA_7_ENCERRAMENTO_POS_MERGE_PR166_2026-09-03.md`.

## Atualização viva — CI remoto verde da PR #166 — 03 de setembro de 2026

O commit-fonte publicado da candidata é
`f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9`, na branch
`fix/legacy-27-functional-regressions`. O run remoto
`33785352331` concluiu com os dois jobs obrigatórios em `SUCCESS`:
Linux `100748662139` e Windows `100748662510`.

O Windows executou o runner oficial sem seleção parcial: `189/189` arquivos,
`1919` testes, `0` falhas, `0` erros e `0` skips. O JUnit confirmou os
dois contratos de symlink. Linux passou com `1919 passed` e um warning. A
cobertura extraída dos XMLs foi `23890/25799` linhas (92,60%) nos dois
sistemas; branches `6665/7838` (85,03%) no Linux e `6666/7838` (85,05%)
no Windows. Baseline, integridade de evidências, política de cobertura e
Stage 4B.5 passaram.

O checkout do evento `pull_request` testou o merge sintético
`1eb297dec2faea82b06779778b6463b94a625897`, cujo segundo pai é
`f61ba6108f1c13ffe2c3d9b6b03aca132f3e4fe9`. O gate formal registrou a cabeça
da fonte separadamente e aceitou a reconciliação: histórico bruto
`196/26/0/0`, retorno `1`, `15` exatas, `11` divergentes, `12`
ausências e `42` substitutos. Os snapshots legados permaneceram imutáveis.

Estado remoto desta revisão: `PASS`. Estado do plano: `IN_PROGRESS`. A
integração segue `BLOCKED` até revisão humana e autorização explícita; não
foram executados merge, tag ou release. Evidência:
`docs/evidence/ETAPA_7_CI_RERUN_PR166_2026-09-03.md`.

## Atualização viva — correção do timeout Windows — 03 de setembro de 2026

O rerun remoto `33767197026` foi analisado antes de nova autorização de merge:
Linux `100687993442` passou e Windows `100687993643` falhou no shard `44/189`
porque `elapsed_ms=47,0` ficou abaixo do timeout contratual de `50 ms`. A causa
foi medida de início tardia no worker, depois da fila do `QThreadPool`.

A correção está no commit local `febc85471e5ced519f47626665f5d995e7cf60a9`:
o relógio começa na construção do worker, a asserção permanece e os snapshots
legados não foram editados. Em árvore limpa, o runner Windows passou em
`189/189` arquivos e `1919` testes, sem falhas ou erros e com `2` skips; cobertura
`92,59%` de linhas e `85,02%` de branches. Os demais gates e o empacotamento
também passaram.

Estado: `PASS_LOCAL / BLOCKED_REMOTE_RERUN`. O próximo passo permitido é o
registro final, push técnico e observação dos dois jobs remotos. Merge, tag,
release e aprovação global continuam bloqueados.

## Atualização viva — correção cross-platform do CI — 03 de setembro de 2026

A execução inicial da PR `#166` (`33758279765`) foi analisada antes de qualquer
autorização de merge. O job Linux falhou em três testes do gate formal porque
comparava o hash bruto CRLF registrado na decisão histórica com o arquivo LF do
checkout; o job Windows passou por coincidir com CRLF. A falha é de
portabilidade da validação, não do produto nem dos fixtures legados.

A correção nos commits `78e47d7` e `42dcb63` preserva o campo bruto histórico,
adiciona o digest canônico LF e compara o arquivo por normalização explícita.
A suíte completa local passou com `1917 passed, 2 skipped`; cobertura foi
`92,59%` de linhas e `85,02%` de branches; o runner Windows passou em
`189/189` arquivos, `1919` testes, sem falhas. O pacote foi construído com
`SUCCESS`, `11` smoke checks e `314` arquivos.

Estado atual: `PASS_LOCAL / BLOCKED_REMOTE_RERUN`. Baseline/evidências estão em
fechamento para o push técnico. O rerun remoto deve ser observado antes de
qualquer decisão de merge; tag, release e aprovação global continuam bloqueados.

## Atualização viva — candidata Windows/legado de 03 de setembro de 2026

A revisão candidata em `8e0ada3fcf1d08058240e5263732d14087b5335c`, na branch
`fix/legacy-27-functional-regressions`, definiu o comportamento operacional do
runner Windows/Qt por subprocessos isolados por arquivo de teste. O runner
versionado passou duas vezes com `189/189` arquivos, `1918` testes, `0` falhas,
`0` erros e `2` skips condicionais, com cobertura acumulada de `92,59%` de
linhas e `85,02%` de branches.

A reconciliação formal mantém o runner histórico em `196` testes, `26` falhas e
retorno `1`, classifica as `11` assinaturas divergentes e as `12` ausências, e
preserva os snapshots legados sem edição. Os `42` contratos substitutos
passaram. Compile, estática, segurança, Stage 4B.5 e empacotamento local
passaram; o symlink no host atual continua condicionado a `WinError 1314`,
enquanto a prova VMware permanece scoped à reconstrução ZIP/patch registrada.

O estado é `PARCIAL / BLOQUEADO`: a primeira conferência do baseline ainda exige
regeneração a partir do staged final, e o CI remoto do SHA candidato ainda não
foi executado. Merge, tag, release e qualquer declaração de aprovação continuam
proibidos até os gates correspondentes serem comprovados na mesma revisão.

## Estado operacional de referência — 18 de agosto de 2026
## Atualização viva final — candidata Windows/legado — 03 de setembro de 2026

O commit candidato `55110c03a84a560823586d34e12e514592e6948b` foi validado em
árvore limpa. O runner Windows isolado passou com `189/189` arquivos, `1918`
testes, `0` falhas, `0` erros e `2` skips condicionais; cobertura de
`92,59%` de linhas e `85,02%` de branches. A reconciliação formal preservou o
runner histórico (196 testes, 26 falhas, retorno 1), as `11` assinaturas
divergentes e as `12` ausências, com `42` substitutos aprovados e snapshots
legados imutáveis.

Compileall, estática, segurança, Stage 4B.5, baseline (3196 files),
evidence integrity (125 manifests) e empacotamento passaram (SUCCESS, `11`
smoke checks, `314` arquivos). Symlink no host atual permanece `2 skipped`
por `WinError 1314`; a prova VMware é scoped à reconstrução ZIP/patch. O CI
remoto ainda não foi executado.

Estado: `PASS_LOCAL / BLOCKED_REMOTE`. O próximo passo permitido é o push
técnico da candidata conforme a seção 10.1; merge, tag, release e aprovação
global permanecem proibidos.


## Atualização viva — validação do SHA efetivo — 03 de setembro de 2026

A execução final foi repetida no worktree limpo do SHA
`33abb5955f41f89f18f2a5fbe42d2ffc36274099`. O runner Windows isolado
passou com `189/189` arquivos, `1918` testes, `0` falhas, `0`
erros e `2` skips condicionais; cobertura de `92,59%` de linhas e
`85,02%` de branches. O gate formal preservou o histórico
`196/26/0/0`, retorno `1`, as `11` divergências, as `12`
ausências e os snapshots legados, com `42` substitutos aprovados.

Estática, segurança, Stage 4B.5, baseline (`3202 files`), evidence integrity
(`127 manifests`) e empacotamento (`SUCCESS`, `11` smoke checks,
`314` arquivos) passaram. O symlink local permanece limitado por
`WinError 1314`; a prova VMware segue scoped. Estado:
`PASS_LOCAL / BLOCKED_REMOTE`. O próximo passo permitido é o push técnico;
merge, tag, release e aprovação global continuam proibidos. Evidência:
`docs/evidence/ETAPA_7_WINDOWS_RUNNER_SHA_EFETIVO_2026-09-03.md`.

Este bloco é um snapshot vivo condicionado à verificação do repositório e do GitHub.

## Reconciliação corrente do estado e do novo plano

- baseline funcional verificado no merge `a129cd251345456c39254b39682d1ef083fd28d0`,
  PR `#99`; CI pós-merge `32184900502` passou em Linux e Windows nos jobs
  `95866168681` e `95866168551`.

- A PR `#97` integrou a paleta visual, busca, teclado, localização e acessibilidade,
  com captura real e hashes registrados na evidência da Etapa 3.

- A PR `#99` integrou câmera/parallax (4A), schema lateral (4B.1), preview/overlays (4B.2), autoria lateral (4B.3), exportação/consumidores (4B.4) e fechamento de qualidade (4B.5), comprovados em evidências locais hashadas. O merge resultou no commit `a129cd251345456c39254b39682d1ef083fd28d0`; o CI pós-merge `32184900502` foi aprovado em Linux e Windows. Isso não aprova automaticamente uma nova release.

- A release `v0.2.0` permanece um snapshot publicado anterior; este `main`
  contém commits posteriores e não deve ser apresentado como idêntico à release.

Etapa 14 — encerrada no escopo técnico pós-merge:

- commit-fonte do build MSI `828cf626b7ce382c360723b1be10c4ce718c4187`; merge atual `f15193a55d1a5de0c7031f5bab656107302eee1b`;
- `982` testes por sistema no CI pós-merge; cobertura `11.621/12.523` linhas (`92,80%`), `3.382/3.978` branches (`85,02%`) e `90,92%` combinada;
- MSI WiX reproduzido byte a byte em duas execuções; instalação, binários instalados, exportações, GUI, upgrade, reparo e desinstalação aprovados;
- Godot `4.7` e Unity `6000.5.7f1` com glTFast `6.19.0` consumiram fixtures produzidos pela implementação integrada;
- integridade recursiva, ausência de referências proibidas e Microsoft Defender aprovados;
- executáveis e MSI permanecem sem assinatura; a release oficial `v0.2.0` foi publicada pelo proprietário com esse risco aceito; assinatura, licenciamento e formalizações de R-015 não são gates obrigatórios; R-016 está revisado e aprovado;
- PR `#58`, merge `f15193a55d1a5de0c7031f5bab656107302eee1b` e CI pós-merge `31905237922` auditado;
- `982` testes por sistema; cobertura idêntica ponto a ponto em 80 módulos; legado `27/27` reconciliado e zero violações nos pacotes auditados;
- `STAGE14_TECHNICAL_CANDIDATE=PASS`; `STAGE14_COMPLETED=YES`; `FIRST_OFFICIAL_RELEASE_PUBLISHED=v0.2.0`; artefatos sem assinatura declarados.

### Decisão vigente sobre riscos de release

A release pode ser entregue sem assinatura de código, com hashes, evidências e
limitações declarados. A assinatura e a formalização jurídica podem ser
adicionadas no futuro, mas não são gates obrigatórios. A execução dinâmica de
Godot/Unity no CI também não é requisito; as execuções reais locais
reproduzíveis são aceitas. `R-014`, `R-015` e a ausência de CI dinâmico não
bloqueiam release. Os detalhes estão em
`docs/CHECKLIST_RELEASE_PUBLICA.md`,
`docs/POLITICA_PUBLICACAO_E_DADOS.md`,
`docs/IDENTIDADE_VISUAL_E_ATRIBUICOES.md` e
`docs/PLANO_MIGRACAO_BUILDER_MSI_R016.md`, além da decisão vigente em
`docs/evidence/RECONCILIACAO_GATES_RELEASE_2026-08-17.md`.

Etapa 11 integrada e concluída no escopo aprovado:

- PR funcional `#45` integrada em `2a38b89e542390b3b4396a88d9a416f3695caadc`; PR de fechamento `#46` integrada em `a22a90088220e586c3382c3ed5dc1075a3ff7e6b`;
- 145 testes comportamentais novos; suíte oficial `877 passed` no Windows/Python 3.11.9;
- cobertura exata `10.787/11.628` linhas (`92,77%`), `3.147/3.700` branches (`85,05%`) e `90,91%` combinada;
- zero módulos abaixo de 30% em linhas ou branches mensuráveis;
- CIs funcional `31491221322` e final de fechamento `31495971632` aceitos após auditoria integral de Linux/Windows, proveniência, legado, hashes e conteúdo recursivo;
- `R-003` encerrado no escopo aprovado após integração e CI pós-merge auditado;
- Etapas 11 a 14 concluídas nos escopos aprovados; `R-014` e `R-015` são riscos declarados não bloqueantes; `R-016` está revisado e aprovado; release oficial `v0.2.0` publicada sem alegação de conformidade jurídica.

Etapa 12 — integrada e concluída no escopo aprovado:

- `928` testes oficiais aprovados no Windows/Python 3.11.9;
- cobertura exata `11.174/12.040` linhas (`92,81%`), `3.309/3.892` branches (`85,02%`) e `90,91%` combinada;
- limites centrais e cenários malformados implementados para configuração, imagem, projeto, geometria, detecção, broadphase, atlas, GLTF e logs;
- pip-audit sem vulnerabilidades conhecidas, Bandit de alta severidade limpo, mypy sem erros em `73` arquivos e legado `27/27` conciliado;
- commit técnico `da7611b543bb0ceb4eb8e67a7900aadcb8f04a5f` validado em worktree limpa; PR `#49` integrada em `872bf079d228d13d0203d22b844052b1f920e99b` e CI funcional `31686321925` auditado; fechamento pela PR `#50` em `fc81c2ea10e751c15a39627d462ddfff390eeb04`; CI final `31688307089` auditado em Linux/Windows;
- pacote documental de fechamento: `929` testes locais e baseline de `326` arquivos, sem alteração na cobertura do código-fonte;
- `R-012`: ENCERRADO NO ESCOPO APROVADO; Etapa 12: CONCLUÍDA; a Etapa 13 posterior também foi integrada e concluída; release: NÃO APROVADA.

Etapa 13 — integrada e concluída no escopo aprovado:

- base `fc81c2ea10e751c15a39627d462ddfff390eeb04`; PR `#51`, HEAD final `0b5d3c4e3831ad5efe52ae03a41107c6dafbf535` e merge `e7eb4a4c81fa2b46e8b9d5db40562e4ce7021108`;
- fechamento documental e correção retrospectiva integrados pela PR `#52` no merge `b4d9390dbd1274c283a3e3985d6d79be47de45d6`; CI pós-merge final `31705652046` auditado;
- sessão de documento, caminhos de estado, conversão de imagem, traduções e coordenação do autosave extraídos; `main_window.py` reduzido de `1.306` para `1.175` linhas;
- autosave local versionado, atômico, limitado e recuperável explicitamente, com quarentena, fingerprint da origem e preservação da decisão adiada;
- `955` testes no fechamento final, `11.581/12.478` linhas, `3.370/3.964` branches, `90,93%` combinada, zero módulos abaixo de 30% e baseline de `338` arquivos;
- mypy em `80` arquivos, Black, isort, Bandit e pip-audit aprovados no escopo vigente; legado `27/27` conciliado;
- provas externas aprovadas com `QTimer` real e processos distintos; CI verde `31693639653` rejeitado; CI pré-merge final `31696674184` e pós-merge `31698961646` aceitos após auditoria integral dos artefatos;
- `R-011`: ENCERRADO NO ESCOPO APROVADO; Etapa 13: CONCLUÍDA; naquele snapshot, Etapa 14: NÃO INICIADA; release: NÃO APROVADA.

Snapshot integrado anterior — encerramento formal da Etapa 10:

- branch funcional `etapa-10-exportadores-engines`, HEAD final `2d2afff2c57cd779750bcb9c02b24c421d73dc0c`, PR `#42` integrada em `9b22bdc54b13992658172d4748bfab44f3127c8e`;
- primeiro CI remoto `31450335289`: gates Linux/Windows aprovados, mas resultado rejeitado porque o artefato omitiu a evidência atual e o resumo legado não identificou separadamente o HEAD testado;
- segundo CI remoto `31451363518`: gates aprovados e upload corrigido, mas resultado rejeitado porque o resumo portátil identificava somente o merge sintético testado, não o HEAD fonte da PR;
- terceiro CI remoto `31452032479`: gates, upload e schema v4 aprovados, mas resultado rejeitado porque o scanner recursivo encontrou referências proibidas em ZIPs históricos aninhados;
- quatro ZIPs sanitizados mediante autorização explícita, checksums internos e hashes externos recalculados;
- quarto CI remoto `31457937902`: Linux e Windows aprovados com `729` testes, merge sintético `0394d55501e32e2fa38acbcc4d1e3c5e126954ce`, HEAD fonte comprovado, `44` arquivos de evidência idênticos ao repositório e varredura recursiva sem violações; resultado pré-merge aceito;
- CI pós-merge `31463873481`: jobs verdes e artefatos íntegros, mas resultado rejeitado porque Linux registrou `8.581` linhas e `2.145` branches cobertos, contra `8.582` e `2.146` no Windows;
- teste determinístico força o par inverso da broadphase; CI pré-merge corretivo `31464786333` aceito, PR `#43` integrada em `f8caec3e7156d308f03046f81d2c89996f959466` e pós-merge `31469610508` aceito após auditoria integral;
- perfis Godot/Unity corrigidos e unificados entre cena e objeto;
- rollback multi-arquivo do atlas comprovado por falha injetada;
- Godot `4.7` e Unity `6000.5.7f1` aprovados em caminhos Unicode, inclusive GLB;
- `17` testes da etapa, `730` oficiais e `196` históricos com reconciliação `27/27`;
- cobertura `73,77%` de linhas, `57,91%` de branches e `69,93%` combinada; mypy sem erros em `70` arquivos;
- Etapa 10: CONCLUÍDA; Etapa 11: NÃO INICIADA; release: NÃO APROVADA.

### Snapshot histórico — encerramento formal da Etapa 9

- commit técnico local `28273dfb7cb0e0aeab1f8f9f3a99c07df3b08a76`;
- 39 testes da etapa, 702 oficiais e 196 históricos; reconciliação 27/27;
- cobertura global 73.65% de linhas, 57.65% de branches e 69.79% combinada;
- API pública única de colisão estática; namespace histórico sem implementações concorrentes;
- PR `#40`, merge `76dd6b7ca3e7da08fab653d66ae29a33a839baf3`; CI final da PR `31445205968` e pós-merge `31445518755`: Linux e Windows em `success`, zero anotações;
- `R-008`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 9: CONCLUÍDA; Etapa 10: NÃO INICIADA; release: NÃO APROVADA.

### Snapshot histórico imediatamente anterior — encerramento da Etapa 8

- repositório: `AiltonSantanaReis/NeoEng-D-Trace`;
- commits técnico/documental da Etapa 7: `a940ef13018aabc430126db3fd705b521fc1be06` e `51e55a37021c506471111ef1f4e7bc9abe67c65d`;
- PR `#36`, merge `99326f2d7ccf7046e401d90830feb8a5d33e9f9a`;
- CI da PR `31436763095` e pós-merge `31437000772`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9081388807`, Windows `9081419753`;
- validação local: 620 testes no commit técnico, 621 no pacote pré-merge e 622 no fechamento, cobertura combinada 68.53%, launcher 85% e mypy sem erros em 66 arquivos;
- cobertura crítica integrada pela PR `#35`; `R-003` permanece aberto para as metas finais;
- `R-006`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 7: CONCLUÍDA;
- Etapa 8 integrada pela PR `#38`, merge `fc869250e5067fb7b06b70c7d2dd3c0e1e1ee94e`;
- CI da PR `31440755594` e pós-merge `31441024001`: Linux e Windows em `success`, zero anotações;
- validação local: 125 testes focais, 661 totais no pacote pré-merge e 662 no fechamento; núcleo geométrico com 95.59% de linhas e 93.29% de branches;
- `R-007`: ENCERRADO NO ESCOPO APROVADO; Etapa 8: CONCLUÍDA;
- gate naquele snapshot: executar a auditoria de física, colisão e APIs da Etapa 9;
- naquele snapshot, Etapa 9: não iniciada; release: NÃO APROVADA.

### Snapshot histórico imediatamente anterior — encerramento da Etapa 6

- commits técnico/documental: `3c80bb7f0f72a26f5f4972c5aeb483b8d16e2e98` e `321ccf3a692c7c1916eeeb61e7a041ee8bcef035`;
- PR `#33`, merge `73a128ec44cde17867bbac6a7854ce86a43aba5a`;
- CI da PR `31431473940` e pós-merge `31431739320`: Linux e Windows em `success`, zero anotações;
- artefatos pós-merge: Linux `9079413130`, Windows `9079450269`;
- validação local de fechamento: 543 testes, cobertura combinada 62.45%, mypy sem erros em 66 arquivos;
- `R-005`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 6: CONCLUÍDA;
- naquele snapshot, Etapa 7: não iniciada; release: NÃO APROVADA.

### Snapshot histórico anterior — encerramento da Etapa 5

- âncora técnica integrada e auditada: `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- PR funcional: `#27`, fechada e mesclada;
- HEAD funcional v4.1: `9bf83af0d58b5984ccfefc59a543428379b02632`;
- HEAD documental final da PR: `8ce44c238aaea79dafa64b8e1bba3ba5a8a7157e`;
- Pacotes 1, 2A, 2B, 3A, 3B, 3B.1, 4A, 4B, 4C, 5A, 5B e 5C: integrados;
- gate funcional Windows/Python 3.11.9: 95 testes focais, 16 documentais, 517 totais e 66% de cobertura;
- validação visual: manual aprovada e automática aprovada em 17/17 estados;
- CI final pré-merge: workflow `Private validation` `#83` (`31135700216`) com Linux e Windows em `success`;
- CI pós-merge da `main`: workflow `Private validation` `#84` (`31136893143`) com Linux e Windows em `success`;
- artefatos pós-merge: Linux `8978309717` (`25ee252a77fb43796a6c5b1cbbf10c5987791187a6e860a11c17e9980d45b091`) e Windows `8978326062` (`0432e2e7ccc11d21d8769f160268f820ccf62af7edb5fd6f5a2070bcca4c912f`);
- branch funcional: preservada no remoto;
- PR de fechamento: `#28`, HEAD `ab71e148c0b7441bd36f489472856d0b4adfaa1e`, mesclada em `56533b65f81d21fd9c762aa10c0d3e6747d742ca`;
- pacote técnico final: PR `#29`, HEAD `956db473a88641bfdcfbd49ed122479f3fa2c51d`, merge `574be9bd0268e70c384903f93f16cf6e73aa57a2`;
- CI pós-merge técnico: `31425585259`, Linux e Windows em `success`, zero anotações;
- `R-004`: ENCERRADO NO ESCOPO APROVADO;
- Etapa 5: CONCLUÍDA;
- gate naquele snapshot: planejar a Etapa 6 sem iniciá-la implicitamente e manter release bloqueada;
- naquele snapshot, Etapa 6: não iniciada.

O fechamento de `R-004` e a conclusão da Etapa 5 foram executados com evidência
remota. Naquele snapshot, o início da Etapa 6 ainda era um gate independente.

## Reavaliação auditada publicada — 10 de agosto de 2026

A recomendação anterior foi bloqueada durante auditoria rigorosa e somente
restabelecida depois das correções descritas em
`docs/evidence/AUDITORIA_RIGOROSA_2026-08-10.md`.

Estado remoto atual:

- segurança de dependências e Bandit de alta severidade: aprovados;
- suíte oficial: `532 passed`;
- suíte legada: 196 executados, 26 divergências previstas reconciliadas, zero
  inesperadas;
- mypy estrito: zero erros em 65 arquivos;
- cobertura combinada linhas/branches: `62.18%`, com piso CI de
  62%; metas finais de 90%/85% ainda abertas;
- publicação: commit `236eefd41ee51c7085e21d52fc80074eede0a793`, HEAD final `ab71e148c0b7441bd36f489472856d0b4adfaa1e`, PR `#28` mesclada;
- CI final da PR: `31422901244`, Linux e Windows em `success`;
- CI pós-merge corretivo: `31423386971`, Linux e Windows em `success`;
- CI pós-merge técnico final: `31425585259`, Linux e Windows em `success`;
- decisão: **ETAPA 5 FORMALMENTE ENCERRADA**;
- release: **NÃO APROVADA**.

## Regras inegociáveis

1. `main` representa somente estados aprovados.
2. Nenhuma afirmação de sucesso sem evidência reproduzível.
3. Estados permitidos: APROVADO, REPROVADO, BLOQUEADO, NÃO TESTADO e PARCIAL.
4. NÃO TESTADO, BLOQUEADO e PARCIAL nunca equivalem a APROVADO.
5. É proibido remover, enfraquecer, ignorar ou maquiar teste para obter resultado verde.
6. Toda falha corrigida exige teste de regressão.
7. Nenhuma etapa avança com perda de dados, regressão, build quebrado, comportamento não determinístico ou evidência insuficiente.
8. Funcionalidade nova fica congelada até a conclusão dos bloqueadores de estabilização.

## Definição de concluído

Uma tarefa somente termina quando possuir requisito objetivo, reprodução anterior, causa raiz, implementação completa, testes unitários e de integração, testes de UI quando aplicáveis, cenários negativos, cobertura sem redução, compilação, lint, tipagem, documentação, evidências e revisão do diff.

## Evidências obrigatórias

Cada etapa deve registrar:

- commit testado;
- sistema operacional e Python;
- dependências instaladas;
- comandos completos;
- quantidade de testes aprovados, reprovados, ignorados e bloqueados;
- cobertura por módulo;
- hashes de entradas e saídas relevantes;
- limitações e riscos residuais;
- conclusão formal.

Os relatórios permanentes ficam em `docs/evidence/`. Resultados brutos devem ser publicados como artefatos do CI.

## Estratégia de testes

- unitários para domínio e serviços;
- propriedades para invariantes geométricos e round-trip;
- integração com arquivos temporários reais;
- UI com `pytest-qt`;
- ponta a ponta para importar, editar, salvar, reabrir e exportar;
- compatibilidade em Windows 11 e Linux;
- segurança para entradas malformadas, limites e permissões;
- desempenho com baseline reproduzível.

## Metas de cobertura

- nenhum módulo operacional em 0%;
- 100% dos fluxos críticos mapeados;
- persistência, Undo/Redo e exportadores: 95% de linhas e 90% de branches;
- núcleo geométrico: 90% de linhas e 85% de branches;
- cobertura global: 90% de linhas e 85% de branches;
- exclusões somente com justificativa explícita.

## Ordem obrigatória

0. Governança e proteção da baseline.
1. Ambiente reproduzível e CI Windows/Linux.
2. Inventário funcional e testes de caracterização.
3. Persistência e contrato versionado de projeto.
4. Ciclo Abrir/Salvar na interface.
5. Undo/Redo completo.
6. Exportação de colisões.
7. CLI e modo headless.
8. Bézier e geometria.
9. Física, colisão e APIs duplicadas.
10. Exportadores e validação nas engines declaradas.
11. Cobertura integral da interface.
12. Segurança e limites operacionais.
13. Refatoração protegida por testes.
14. Build Windows, auditoria final e candidato a release.

Nenhuma etapa pode ser pulada. Retorno a uma etapa anterior deve ser registrado como lacuna ou regressão descoberta.
