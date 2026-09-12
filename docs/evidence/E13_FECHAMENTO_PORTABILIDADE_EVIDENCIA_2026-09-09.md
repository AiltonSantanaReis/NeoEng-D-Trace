# E13 — Fechamento técnico e portabilidade

**Estado:** `IN_PROGRESS`  
**Data de abertura:** 2026-09-09  
**Branch:** `Ailton/e08-renderer-20260908`  
**SHA de abertura:** `510cee7166eb90026c22e3b922d45d3624bb4c91`  
**Worktree oficial:** `build/e01-independent-scene-20260908`

## Autoridade e escopo

Este relatório é subordinado à governança em
`docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`, à
`docs/PLANO_MESTRE_ESTABILIZACAO.md`, ao plano de migração MSI R-016 e à fila
central `docs/evidence/PLANO_MESTRE_FILA_EXECUCAO_CENTRAL_2026-09-09.md`.

O lote fecha tecnicamente a portabilidade do produto já comprovado em E12:
pacote portátil final, instalador MSI per-user, instalação/desinstalação,
rollback/preservação de estado, auditoria de referências locais, manifestos e
limitações. Symlink e revisão humana não pertencem a este sublote e continuam
reservados para E13-D na auditoria final.

## Metas e critérios objetivos

| Meta | Estado inicial | Critério de saída |
|---|---|---|
| E13-A — pacote portátil final | `IN_PROGRESS` | build limpa r70 ou posterior, `source_commit`, manifesto, hash do binário e ZIP, smoke completo e execução fora do checkout |
| E13-B — MSI/instalador | `PLANNED` | WiX 4.0.6 pinado, MSI hashado, instalação per-user, execução CLI/GUI/exportação, desinstalação sem resíduos e estado do usuário preservado |
| E13-C — documentação/privacidade | `PASS` | 135 manifests no gate oficial, referências locais removidas dos novos artefatos, limitações e rollback documentados |
| E13-D — auditoria final | `IN_PROGRESS` | somente no pacote final: symlink, revisão humana, findings e decisão formal |

Nenhuma meta muda para `PASS` antes de possuir teste executado, artefato,
hash, resultado observado, limitação e commit correspondente.

## Análise de impacto

- **Módulos afetados:** `scripts/build_windows.ps1`,
  `scripts/build_installer.ps1`, `tools/package_portable_release.py`,
  `tools/package_windows_msi.py`, `tools/validate_portable_release.py` e
  `tools/validate_windows_installer.py`.
- **Contratos preservados:** versão `0.3.0`, nomes dos executáveis, manifesto
  portátil, `source_commit`, estado por usuário e `UPGRADE_CODE` do MSI.
- **Riscos:** build fora da origem declarada, conteúdo instalado divergente,
  resíduos de desinstalação, vazamento de caminhos pessoais e não
  determinismo do pacote.
- **Proteções:** build exige checkout limpo; o MSI valida o manifesto portátil
  antes de empacotar; WiX é fixado em `4.0.6`; smoke e instalação são
  executados por scripts fail-closed; a auditoria final preserva symlink e
  revisão humana como gates distintos.

## Evidência executada até a abertura

| Evidência | Resultado | Referência |
|---|---|---|
| Registro canônico | `PASS` | `tools/validate_continuity_registry.py`, E13 ativo |
| E12 predecessor | `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING` | build r69, smoke 11 checks, suíte `2104 passed, 2 skipped, 1 warning` |
| Binário predecessor | `PASS_LOCAL` | SHA-256 `07D3B3FBFAD22518628A8E8405FEA69E783750BBBD9593786A8E049781203152` |
| Captura predecessor | `PASS_AUTOMATED_CAPTURE_ONLY` | `artifacts/e12-binary-capture-r69-20260909/` |
| Symlink | `DEFERRED_UNTIL_FINAL_AUDIT` | não executar nesta fase |
| Revisão humana | `DEFERRED_UNTIL_FINAL_AUDIT` | não executar nesta fase |

## Comandos previstos e artefatos obrigatórios

Os comandos devem ser executados a partir do worktree oficial, com o Python
canônico do workspace (`<workspace-root>/.venv/Scripts/python.exe`). Caminhos
pessoais não devem ser gravados em manifestos, relatórios ou pacotes:

1. `tools/validate_continuity_registry.py`;
2. suíte oficial completa e gates estáticos;
3. `scripts/build_windows.ps1` para o pacote portátil r70 ou posterior;
4. `tools/validate_portable_release.py` no bundle e em uma cópia fora do
   checkout;
5. `scripts/build_installer.ps1` ou seus passos equivalentes, após validar a
   origem e o hash do pacote portátil;
6. `tools/validate_windows_installer.py` para instalação, execução,
   exportação, desinstalação e preservação do estado;
7. auditoria documental de referências locais, hashes e manifestos.

Os resultados brutos, relatórios JSON, hashes e capturas serão anexados a este
relatório somente após a execução corrente. Evidência histórica de E12 não é
reclassificada como evidência de E13.

## Decisão de abertura

`E13` está autorizado para execução técnica contínua no mesmo worktree. E13-A,
E13-B e E13-C passaram o checkpoint técnico. E13-D está em execução com a
auditoria final reservada; não há aprovação de release, push, merge ou tag.

## Evidência corrente do r71

Após o commit `b7244ca769f3f3331f1bd3d9be1c06f9026b2671`, o pacote portátil foi
reconstruído em checkout rastreado limpo:

- release relativa: `release/e13-portable-20260909-r71`;
- binário SHA-256: `5F897449D7F712C0CBA2DE4141934E065D4CA5F5F41ABD91A74CE57AD9998E8B`;
- ZIP portátil SHA-256: `C21D3A717F934DA014AFD181E3E2CCF507A975306EA8A2DFCF941D884F8306E7`;
- manifesto portátil SHA-256: `768D54234750BD2717F732B536C0E42F43230215163D5E2CD0916308FA7DD1E5`;
- relatório smoke local: `SUCCESS`, 11 checks, SHA-256
  `5D69BE738588A12AC0CE2063FCC5B0907BBA509BE86D51766418B7F8021DB9DC`;
- proveniência: `status=PASS`, `python_command=canonical-project-python` e
  `release_root=release/e13-portable-20260909-r71`, sem caminho pessoal;
- execução fora do checkout: smoke `SUCCESS` e CLI real `NeoEng-D-Trace-CLI.exe
  0.3.0`;
- captura nativa: janela principal `1933x1045`, SHA-256
  `28AA060935049CD6CED2195351ACF18E94B8A2661429873CA4BEE23683BA5D64`, e
  Cena Independente `993x716`, SHA-256
  `2464B49EBA3378ED0252A5EE941C00746E56F8A94FD11B82C7D1C7CC17BE0A6F`.

As capturas foram abertas para inspeção automatizada: toolbar PT-BR, textos
`Abrir`, `Salvar`, `Exportar`, `Visualizar`, `Cenário`, `Objetos` e o fluxo de
abertura da Cena Independente permanecem observáveis; os hashes são idênticos
ao r69.

O MSI foi gerado com WiX `4.0.6`, mantendo `UpgradeCode` estável:

- MSI SHA-256: `6F4DB9EBD3FF4DA224F90066CC3EB2B2A2B62ED3F827DCE78761F2057E000B62`;
- validação: `status=SUCCESS`, instalação exit `0`, desinstalação exit `0`;
- checks: instalação per-user, CLI, projeto/JSON/GLB, GUI, smoke instalado,
  desinstalação completa e estado do usuário preservado;
- relatório SHA-256:
  `86C643BA5430D0579433C4F7D7A2A610DE3AC66249C9155B63EE15EBD54932EF`.

## Auditoria documental e privacidade — E13-C

Uma execução diagnóstica sem `--git-blob` foi preservada como `DIAGNOSTIC_ONLY`:
ela comparou snapshots históricos de `docs/evidence/artifacts/` com o worktree
atual e reportou hash/bytes divergentes e CRLF. Esses findings não foram
apagados nem reclassificados; os snapshots não foram reescritos.

O gate oficial foi então executado com o contrato do CI:
`tools/evidence_integrity.py --require-tracked --git-blob`. Resultado observado:
`Evidence integrity passed: 135 manifests validated.` O modo `git-blob` leu
cada snapshot contra o `source_commit` registrado, preservando a imutabilidade
histórica sem mascarar alterações correntes.

O gerador de proveniência foi corrigido no commit `b7244ca` para eliminar
caminhos pessoais de novos artefatos. O manifesto portátil r71 e a
proveniência corrente foram inspecionados sem referências a perfis de usuário,
`/Users`, `/home` ou `AppData`. A validação de manifestos de evidência nova
permanece limitada pela regra de rastreamento/ignore do pacote portátil; o
resultado global histórico continua registrado como `FAIL` e mantém E13-C em
`PASS` para E13-C: os 135 manifests versionados passaram no modo oficial, os
novos manifestos de proveniência r71 não possuem caminhos pessoais, e os
limites/rollback estão documentados.

O roteiro de captura de recuperação E11 também produziu um finding
`DIAGNOSTIC_ONLY`: a ação automatizada não acionou “Recuperar Último Válido”,
embora o sidecar `.recovery.json` permanecesse íntegro e o fixture tenha sido
restaurado dele. Isso não é usado como prova de PASS nem é ocultado.

Após a correção de proveniência, a suíte oficial corrente foi repetida no
mesmo worktree: `2104 passed, 2 skipped, 1 warning` em `59.08s`. Compileall,
validador de continuidade e `git diff --check` também passaram.

## Auditoria final E13-D — build r72

O SHA final auditado é `f8fa83e219c42413c02f9436c9a9a7a9c26f9812`, na branch
`Ailton/e08-renderer-20260908`, com arquivos rastreados limpos. A build final
foi gerada antes desta atualização documental e registra no manifesto a
proveniência temporal do registro canônico no instante da build:

- binário: `release/e13-final-20260909-r72/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`, SHA-256 `909051E78F09BA009EEAD4082E2A5829F09DA285E62DC835CA0376024D2F9AF6`;
- ZIP portátil: `release/e13-final-20260909-r72/NeoEng-D-Trace-0.3.0-win64-portable.zip`, SHA-256 `1CA07263268B489D6E357F879A98BA9D2C1485E6C0C1E5EA03BC4268F4E0F646`;
- manifesto de proveniência: `release/e13-final-20260909-r72/continuity-provenance.json`, SHA-256 `818709AFF2543CA86DB3574E7657F3FC3CF1B81565CEF63C0CD5A9D0DCA28F24`;
- relatório local do pacote: `release/e13-final-20260909-r72/smoke/portable-smoke-report.json`, SHA-256 `058441DAECC97F6C8A51020F1526ADA13F4A82CB93675EABB2B68C2490A8A58D6`;
- smoke fora do checkout: `artifacts/e13-final-outside-smoke-r72-20260909/portable-smoke-report.json`, SHA-256 `B069CE2FD214271EDD97100B9CADC2238F0752B478030C55721ACE8FE3BB24DC`, `SUCCESS`, 11 checks, CLI `0.3.0`;
- MSI WiX `4.0.6`: `release/e13-final-20260909-r72/NeoEng-D-Trace-0.3.0-win64.msi`, SHA-256 `C4D4A646F2963F0491F9CAA9355FC8C9C67B06CE54ABFB5131517CF18F6F29F7`;
- validação MSI: `artifacts/e13-final-msi-validation-r72-20260909/installer-validation-report.json`, SHA-256 `78C7E4E5079CCA1EB8DBB34192D246BD54798437228360922C9DF08C320ADDD4`, `SUCCESS`, instalação/desinstalação exit `0`, estado de usuário preservado.

O fluxo fora do checkout foi executado novamente no binário r72 e as capturas
reais foram preservadas em `artifacts/e13-final-capture-r72-20260909/`:

- janela principal `01-main-before-independent.png`, 1933x1045, SHA-256 `28AA060935049CD6CED2195351ACF18E94B8A2661429873CA4BEE23683BA5D64`;
- Cena Independente `02-independent-scene-after-shortcut.png`, 993x716, SHA-256 `2464B49EBA3378ED0252A5EE941C00746E56F8A94FD11B82C7D1C7CC17BE0A6F`.

As capturas foram abertas para inspeção automatizada. Foram observados os
textos PT-BR `Abrir`, `Salvar`, `Exportar`, `Visualizar`, `Cenário` e
`Objetos`, a toolbar da cena independente, o canvas vazio `1920 x 1080` e a
contagem `0 objetos`; não foi observado achado automatizado de tradução,
toolbar ou painel Objetos. Esta inspeção não é revisão humana do proprietário.

### Gate final de symlink

No checkout final, o comando focado executou 2 casos e preservou ambos como
`SKIP_LOCAL`: `WinError 1314 — O cliente não tem o privilégio necessário`.
O conjunto de integração completo executou `29 passed, 2 skipped`.

Depois, o gate foi reexecutado no Windows Sandbox sobre um arquivo Git
imutável exatamente no SHA `f8fa83e`, com Python canônico/venv somente para
leitura e uma pasta de evidências externa. O JUnit bruto foi produzido dentro
da VM e registra `tests=2`, `skipped=0`, `failures=0` e os dois casos de
symlink. O wrapper foi encerrado antes de escrever seu log/relatório; por isso
o `report.json` abaixo é uma reconciliação host explicitamente derivada apenas
dos atributos e casos do JUnit, não uma afirmação de que o wrapper o gravou:

- `artifacts/e13-final-symlink-sandbox-exact-f8fa83e-20260909/report.json`,
  SHA-256 `11551736A8B7BB380E504B6D224AAD17E8A4D9FEE10C971D5B75525C005DB79A`;
- `artifacts/e13-final-symlink-sandbox-exact-f8fa83e-20260909/symlink-junit.xml`,
  SHA-256 `885FF1A505F0251C6F87E7B2A5E17D7757C832C18A117A020569A7269C0E3A9B`;
- resultado observado no Sandbox: `2 passed, 0 skipped, 0 failures`, exit `0`,
  `status=PASS_SANDBOX`.

O resultado histórico `31/31` e o primeiro relatório de reexecução em worktree
posterior continuam preservados como históricos; não são usados como a
proveniência principal. A evidência acima é a requalificação do SHA final
imutável `f8fa83e`.

### Gates repetidos e findings

- `tools/evidence_integrity.py --require-tracked --git-blob`: `Evidence integrity passed: 135 manifests validated.`
- `tools/validate_continuity_registry.py`: `CONTINUITY_REGISTRY=PASS`.
- suíte oficial: `2104 passed, 2 skipped, 1 warning` em `61.03s`;
- finding conhecido de automação de recovery E11 permanece `DIAGNOSTIC_ONLY` e não foi promovido a PASS;
- nenhum novo finding de produto foi reproduzido no pacote r72;
- não houve push, merge, tag ou release.

## Decisão pendente de encerramento

E13-A, E13-B e E13-C permanecem tecnicamente comprovados. O gate Sandbox de
E13-D está `PASS_SANDBOX`; a única pendência restante é a revisão humana do
proprietário sobre as capturas r72 e a decisão formal de encerramento. O teste
local pulado permanece separado e não reduz o resultado do Sandbox.

## Pacote completo de revisão do proprietário — r73

Para permitir a revisão manual e novos testes do proprietário, foi gerada uma
build completa a partir do SHA-fonte `f37b6d32ec086b4e7e07a8d17ca7457638b371d5`,
sem alterar o binário depois da captura. O pacote é candidato de revisão, não
uma autorização de release.

### Artefatos entregues

| Artefato | Resultado | SHA-256 |
|---|---|---|
| Binário GUI | `release/e13-complete-review-20260909-r73/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` — 10.624.222 bytes | `4541C48C218878702F0F9CFBC7D71FB44629166DAFF5A2F09DA4CF3B7D537B0C` |
| Binário CLI | `release/e13-complete-review-20260909-r73/portable/NeoEng-D-Trace/NeoEng-D-Trace-CLI.exe` — 10.512.606 bytes | `F6EBA7626E6E8502C242E2368544CB96C1B793B4A585D88F01F7BD4509AD81DF` |
| ZIP portátil | `release/e13-complete-review-20260909-r73/NeoEng-D-Trace-0.3.0-win64-portable.zip` — 124.931.223 bytes | `914428A1E79937D491B5744D4CEB6C3E6EFE72A980EBBC437307EF500B0F667E` |
| MSI WiX | `release/e13-complete-review-20260909-r73/NeoEng-D-Trace-0.3.0-win64.msi` — 105.504.768 bytes | `DB063C66C4FDC885104A3C4795B4928AF70F437563D3F336A2C04562FAA63D1A` |
| Manifesto portátil | `release/e13-complete-review-20260909-r73/portable/NeoEng-D-Trace/release-manifest.json` | `F01BB79F7CAF2725AC4A2FED36A0886459D5A75148AED2367D60622FCEFD88B2` |
| Proveniência | `release/e13-complete-review-20260909-r73/continuity-provenance.json` | `C7498B136E94D7A056A082801560C538CD7AFC621FCE83068A83C80033016077` |

### Testes e capturas do pacote r73

- Smoke portátil fora do checkout: `SUCCESS`, 11 checks, CLI `0.3.0`; relatório
  `artifacts/e13-complete-review-outside-r73-20260909/portable-smoke-report.json`,
  SHA-256 `0C3B876717B0153494DB515C48C72CCBF9A3054B7BF932B9C45A4FED7D5A6DFB`.
- Validação MSI: `SUCCESS`, instalação exit `0`, desinstalação exit `0`,
  CLI/projeto/JSON/GLB/GUI executados e estado do usuário preservado; relatório
  `artifacts/e13-complete-review-msi-validation-r73-20260909/installer-validation-report.json`,
  SHA-256 `A4D8BE0B68D2CE2EADA648FDC9BAC49616F18A7299809D298829FE724126B66C`.
- Captura real do binário GUI: `artifacts/e13-complete-review-capture-r73-20260909/01-main-before-independent.png`,
  SHA-256 `DD7F36BBEA1CBD095B4F7AA04E0D188834264A90C12E79B7D173A08684F82723`.
- Captura real da Cena Independente: `artifacts/e13-complete-review-capture-r73-20260909/02-independent-scene-after-shortcut.png`,
  SHA-256 `2464B49EBA3378ED0252A5EE941C00746E56F8A94FD11B82C7D1C7CC17BE0A6F`.

A inspeção automatizada das capturas confirmou textos PT-BR, toolbar, painel
`Objetos`, título da Cena Independente, canvas `1920 × 1080` e `0 objetos`.
Isso é evidência técnica de execução e não substitui a revisão visual humana.
O empacotamento registrou o aviso não bloqueante do PyInstaller sobre o import
oculto `tzdata`; todos os checks do build e das validações terminaram com
sucesso.

O pacote r73 está pronto para os testes do proprietário. A decisão formal de
encerramento do E13-D permanece `PENDING_HUMAN_REVIEW` até que esses artefatos
sejam revisados.

## Correções confirmadas e pacote final r78 — 2026-09-09

Após a reprodução dos problemas na build portátil, foram aplicadas e
versionadas as correções abaixo:

- `8173659`: fechamento do laço magnético preciso com clique no primeiro ponto
  e duplo clique durante segmento assíncrono; restauração dos estados ativos
  do Visualizador de Máscaras; Editor de Cenário iniciável sem projeto salvo;
  correções de layout dos painéis e do inspector;
- `d8b9191` e `e3cb11a`: largura responsiva dos controles, remoção das setas
  dos botões do editor via QSS centralizado, sem estilos inline proibidos pela
  governança Stage 1;
- `5193e31` e `7fce6d2`: rótulos dos modos e presets do Visualizador de
  Máscaras compactados de forma responsiva, mantendo o texto completo em
  tooltip, acessibilidade e combo de seleção.

O commit final auditado é `7fce6d2eef8389fdbb27230de0a1ebb9b7ce6098`, na
branch `Ailton/e08-renderer-20260908`. A build portátil r78 foi gerada a partir
desse SHA, sem alterar o executável depois das capturas:

| Artefato | SHA-256 |
|---|---|
| GUI `release/e13-complete-review-20260909-r78/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` | `4177AB5535E49DFF4A901095A4AF7F945C4CDEEA2EC391A70D894F887276129F` |
| CLI `release/e13-complete-review-20260909-r78/portable/NeoEng-D-Trace/NeoEng-D-Trace-CLI.exe` | `A58D4FCC4BA2432887791734C89223AB778DDC2DEB8D9230E9C93F850A4D7D65` |
| ZIP portátil `release/e13-complete-review-20260909-r78/NeoEng-D-Trace-0.3.0-win64-portable.zip` | `DDDF2A8765CCDC7DBD856EE1FA4156301A6E15506245FE15A63E5FB020A82C8C` |
| MSI WiX 4.0.6 `release/e13-complete-review-20260909-r78/NeoEng-D-Trace-0.3.0-win64.msi` | `8D5803A8D7DEC57E7D3797E5B351A1A279F0AB2186CA3ED96397536BAA1AD472` |
| Proveniência `release/e13-complete-review-20260909-r78/continuity-provenance.json` | `873A7DE31AAC7D21AEEC9EB992C55E137E127A6ED0D8F5C6412AAD06900F7FA1` |
| Manifesto portátil | `8096B5710547D341F93C932C90DBE6201EB38334F1270FE79B6EAD2F167E7BE6` |

Os checks internos da build portátil passaram: `SUCCESS`, 11 checks, CLI
`0.3.0`. A validação do MSI também passou: instalação per-user exit `0`,
desinstalação exit `0`, smoke instalado `SUCCESS` e estado do usuário
preservado. Relatório MSI:
`artifacts/e13-complete-review-msi-validation-r78-20260909/installer-validation-report.json`,
SHA-256 `F862098D9EE2B9983B33C71C85BFD3A133753E57272764A15FF7EA78A3297B93`.

### Capturas reais do executável portátil r78

As capturas foram feitas pelo handle da janela do executável portátil com
`PrintWindow`, usando um projeto real com imagem (`compound-project.ndtproj`):

- conjunto: `artifacts/e13-portable-final-capture-r78-20260909/`;
- manifesto das capturas: SHA-256
  `616A64B4567ADE18DCD66F93CA3EF5479517946D118CE3E3707E576BB9F2537D`;
- Visualizador de Máscaras carregado:
  `04-mask-viewer.png`, SHA-256
  `26C427C756D1FE2E3DF835B0A921F1478B4F300A3CFF57F3978DC4F848A63791`;
- Editor de Cenário real:
  `05-asset-library-ready.png`, SHA-256
  `04E2BF15F1EC01137CF5B91AACCCB8FFA7F63B46A1673676CFFCC733A47C6214`.

A inspeção das imagens r78 confirmou visualmente que os quatro presets e os
quatro modos do Visualizador estão visíveis, o estado ativo é distinguível,
os textos não são truncados, a barra de rolagem permanece presente e o
Editor de Cenário usa os botões planos do projeto sem setas. A captura também
mostra a imagem carregada e seus elementos no canvas; não é uma tela vazia de
fixture.

A auditoria visual automatizada final da fonte passou no commit r78:
`artifacts/e13-ui-defect-audit-r78-final-20260909/manifest.json`, SHA-256
`45947E5C585DB961F97EE90A78EB64CF243799179AA87FF9F1BB2899AF72D16D`, com
`no_unexpected_clipping=true`, modos X-Ray presentes e separação de canvas,
layers e cenário confirmada. O aviso do OpenCV sobre fallback GPU/CPU é
ambiental e não bloqueou a auditoria.

### Gates repetidos após as correções

- suíte oficial: `2108 passed, 2 skipped, 1 warning` em `59.44s`;
- testes focados de Máscaras, Cenário e regressões: `27 passed`;
- auditoria visual final: `exit 0`;
- smoke portátil r78: `SUCCESS`, 11 checks;
- MSI r78: `SUCCESS`, instalação/desinstalação completas;
- symlinks: permanecem reservados para o final do plano, conforme decisão
  registrada; não foram reexecutados nesta etapa.

O pacote r78 é o artefato portátil mais recente para revisão e testes do
proprietário. A revisão humana continua pendente apenas para o fechamento
formal do plano, não como bloqueio da execução técnica desta etapa.
