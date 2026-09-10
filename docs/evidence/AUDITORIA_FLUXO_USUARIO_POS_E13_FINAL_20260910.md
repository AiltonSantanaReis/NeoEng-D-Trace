# Auditoria final do fluxo real de usuário — pós-E13 — 2026-09-10

**ID:** `AUDIT-POS-E13-FINAL-20260910`

**Estado governado:** `IN_PROGRESS`

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base ativa:** checkout `build/e01-independent-scene-20260908`, branch
`Ailton/e08-renderer-20260908`

**E13:** concluído e congelado como histórico; não foi reaberto.

## 1. Objetivo e limite

Esta auditoria fecha a investigação técnica pós-E13 do Editor de Cenário,
parallax, catálogo de assets e ferramentas de autoria. O objetivo foi executar
o fluxo que um usuário comum faria, do projeto carregado à criação, edição,
salvamento e reabertura dos recursos, sem remover conteúdo existente ou
promover uma evidência parcial a aceite global.

As referências a E00–E13, builds antigas e tentativas que falharam continuam
preservadas para rastreabilidade. A base de implementação deste relatório é
somente o commit `cf829b7583c4a6a63fb86d8a0cafc5103808f498` e a build final10.

## 2. Governança e método de evidência

Foram lidos antes desta etapa:

- [Governança de Integridade, Execução e Antialucinação](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md);
- [Base Ativa Pós-E13](BASE_ATIVA_POS_E13_2026-09-09.md);
- [Plano Pós-E13 do Estúdio Parallax](PLANO_POS_E13_ESTUDIO_PARALLAX_2026-09-09.md);
- decisão formal de continuidade pós-E13 e proposta dos pacotes de assets.

As capturas finais foram produzidas pelo processo nativo do executável portátil
real, iniciado com fixtures isoladas, usando o harness versionado
`scripts/capture_e03_asset_library_binary.ps1`. O harness usa eventos Win32 de
mouse/teclado e `PrintWindow`; menus sem janela enumerável foram capturados pela
tela primária real (`CopyFromScreen`). Não houve mock de widget, alteração
manual de JSON para simular resultado ou composição offline.

O serviço CUA de janelas nativas não estava disponível nesta sessão — o
inventário expôs apenas navegador e a inicialização retornou
`Trusted RPC service is not configured: sky`. Portanto, o fallback Win32 foi
usado e declarado; ele não é apresentado como clique CUA.

O harness de menu contextual profissional foi versionado no commit
`072427e` (`test: capture professional viewport context menu`), sem alterar
código de produto, schema, assets ou comportamento do usuário.

## 3. Build final e proveniência

- Diretório: `build/_clean-post-e13-final10-20260910/`.
- Commit de produto/build: `cf829b7583c4a6a63fb86d8a0cafc5103808f498`.
- Executável: `portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`, tamanho
  `10739195`, SHA-256
  `754B6EAD8E56FB87CEC09E4AFFFF7ABB5EC3E309C45933042C5B461B94E9F856`.
- Pacote portátil: `NeoEng-D-Trace-0.3.0-win64-portable.zip`, SHA-256
  `C4831D3493671D512EDA2CA168A345F26A7430B159E08B04667E4B5E14D64F03`.
- Proveniência: `continuity-provenance.json`, `PASS`, SHA-256
  `41DF28C1F46B244284FBEA05313EBC31DE4FB0C12D45D0F6541C8DFDE0052DC3`.
- Smoke portátil: `smoke/portable-smoke-report.json`, `SUCCESS`, 11 checks,
  SHA-256 `7B890789F9B46B6126AA4F8A2791E0633B8F7612E2B47F7E2674C842E99E3D54`.
- O empacotamento ainda registra `Hidden import "tzdata" not found!`; o smoke
  passou e o aviso não foi ocultado.

## 4. Matriz de fluxos nativos final10

`PASS` nesta tabela significa que o fluxo específico foi executado no binário
real, produziu saída observável e, quando aplicável, foi salvo e reaberto. Não
significa encerramento formal do projeto: esse encerramento continua impedido
pelos gates descritos na seção 6.

| ID / requisitos | Fluxo real executado | Evidência final10 | Resultado observado |
|---|---|---|---|
| `P13-NATIVE-01` / `REQ-F02`, `REQ-F10`, `PACK-03` | Biblioteca → Pacotes NeoEng → miniaturas e nomes comuns | [Pacote Floresta](../../artifacts/post-e13-binary-final10-20260910/asset-pack/06-asset-pack-dialog.png) — SHA `4C6AF75116A4E4478C90BB2C882C6BD10F19A69A7918DC4D385ACBA0E9E9B0FA` | `PASS`: seis assets, `Problemas: 0`, preview nativo e licença pendente explicitamente exibida. |
| `P13-NATIVE-02` / `REQ-F04`, `REQ-F10` | Selecionar asset vetorial, detectar, editar e criar objeto | [Vetor criado](../../artifacts/post-e13-binary-final10-20260910/vector/13-vector-contour-created.png) — SHA `2DC75915D02BC390546AF806A9E227E91F308DF6F34D3C18F4F3764FB26CC28E` | `PASS`: a linha correta foi selecionada e o objeto apareceu no viewport. |
| `P13-NATIVE-03` / `REQ-F03`, `REQ-F10` | Novo tilemap → pintar → salvar → reabrir | [Tilemap reaberto](../../artifacts/post-e13-binary-final10-20260910/tilemap/11-tilemap-reopened.png) — SHA `8CCFB88526042B14E29F29715BAB78B3BE6272E6EE16BBCE34909D70662AB68E` | `PASS`: `2 células · 1 chunks` persistidos; status PT-BR `Edição do tilemap aplicada`. |
| `P13-NATIVE-04` / `REQ-F03`, `REQ-F04` | Abrir tileset, gerar atlas, salvar, criar novo e reabrir | [Tileset reaberto](../../artifacts/post-e13-binary-final10-20260910/tileset/10-tileset-reopened.png) — SHA `7EB90D94495C9E9EA161ECFD870E1C863BDDC961F15C039D5C401CA485CA1FD8` | `PASS`: atlas e recurso dedicado foram mantidos após reabertura. |
| `P13-NATIVE-05` / `REQ-F03`, `REQ-F04` | Criar colisor box/circle, salvar e reabrir | [Colisores reabertos](../../artifacts/post-e13-binary-final10-20260910/collider/09-collider-reopened.png) — SHA `91D5E1B22BB7122234C24FE28F76B112094B74328828AFD3629F34E47B731E11` | `PASS`: os dois tipos foram criados e persistiram. |
| `P13-NATIVE-06` / `REQ-F03`, `REQ-F04` | Criar região/obstáculo, fazer bake, salvar e reabrir NavMesh | [NavMesh reaberta](../../artifacts/post-e13-binary-final10-20260910/navmesh/09-navmesh-reopened.png) — SHA `F58A0D2F981781E27633723C715220A3F42F4A9FE6284296DB93BC766439D9B4` | `PASS`: bake disponível após reabertura. |
| `P13-NATIVE-07` / `REQ-F04`, `REQ-F10` | Entidade → prefab → instância → override → atualizar → desvincular | [Prefab desvinculado](../../artifacts/post-e13-binary-final10-20260910/entities/15-prefab-detached-state.png) — SHA `72AB506729F3F3A648D30F782AC59F6106A534B661D81CF354FD66C8011903D6` | `PASS`: estados de instância, override, atualização e detach observados. |
| `P13-NATIVE-08` / `REQ-F04`, `REQ-F10` | Menu de renderer → preview → authoring | [Authoring](../../artifacts/post-e13-binary-final10-20260910/renderer/08-renderer-authoring.png) — SHA `7310A70A0C4C9CA92DC2AB48B58F2DDF02C6451FB6BF906BCB43FF33E7F2057B` | `PASS`: preview e autoria alternaram no editor real. |
| `P13-NATIVE-09` / `REQ-F04`, `REQ-F03` | Selecionar V2 sem material → editar albedo → aplicar → salvar → recarregar | [Material recarregado](../../artifacts/post-e13-binary-final10-20260910/material-clean/14-material-reloaded.png) — SHA `EEAC6CED18C07D82ED1073A9087AF9862074500EA33BB16CD9E250F2862D2D2C` | `PASS`: controles habilitados, `#ff0000` persistido e `Cenário recarregado` localizado. |
| `P13-NATIVE-10` / `REQ-F04`, `REQ-F09` | Alterar profundidade/translação e aplicar parallax | [Parallax aplicado](../../artifacts/post-e13-binary-final10-20260910/parallax/07-parallax-applied.png) — SHA `3CF614B50573E3DFB60648AFDD54C31853309E6653ACFAE9285D053523512920` | `PASS`: valores `0,7500` foram aplicados; estado não salvo ficou explícito. |
| `P13-NATIVE-11` / `REQ-F09`, `REQ-F10` | Câmera, luz, chuva/partículas, áudio real e texto/cutscene na timeline | [Clip de áudio](../../artifacts/post-e13-binary-final10-20260910/sequence/10-sequence-studio-audio-clip.png) — SHA `7FCE9CF499AB614588D452FBFCAD8B7E4CC6006E2F31251A477E8EA582543DD7`; [texto final](../../artifacts/post-e13-binary-final10-20260910/sequence/11-sequence-studio-text-clip-real.png) — SHA `818AF471F12ACCB376BCD1F391065D8F4A6169279C8783ADD0BEF7015E5E8825` | `PASS`: o seletor WAV nativo abriu, o clip `Áudio` foi criado e o texto/cutscene ficou editável. A timeline usa rolagem vertical quando as trilhas excedem a área visível. |
| `P13-NATIVE-12` / `REQ-F10`, `REQ-F02` | Clique direito na lista principal e no viewport profissional | [Menu principal](../../artifacts/post-e13-binary-final10-20260910/context/06-context-menu-layer.png) — SHA `C609C6AACA9F5A95D94619471F565A3E62E7F235863BA67757FDF1DF41C1C4DF`; [viewport profissional](../../artifacts/post-e13-binary-final10-20260910/context-professional-object/07-professional-context-menu.png) — SHA `C486E629B5DB30320B51D0E14D44ADDC2018B1FEEA8CDE079719D8EE978F35EDD` | `PASS`: menus reais em PT-BR; o viewport exibiu `Objeto`, `Mostrar propriedades`, `Enquadrar seleção` e `Enquadrar tudo`, sem ação destrutiva. |
| `P13-NATIVE-13` / `REQ-F10`, `REQ-F02` | Visualizar → máscara/raio-X com imagem carregada | [Visualizador de máscara](../../artifacts/post-e13-binary-final10-20260910/mask/04-mask-viewer.png) — SHA `948F66644F6780EEC870CF4AF3DA967411B5112B428C8ACBE09F267C33FCA120` | `PASS`: a janela semântica correta foi capturada; tentativas anteriores incorretas continuam preservadas. |
| `P13-NATIVE-14` / `REQ-F04`, `REQ-F03` | Arraste direto Biblioteca → viewport → salvar → reabrir | Registro [CHG-POS-E13-003](CHG_POS_E13_DIRECT_ASSET_DRAG_20260910.md) | `PASS` no commit `0a2f18e`, ancestral da build final10; a captura específica foi produzida em binário anterior e não é apresentada como captura final10. |

## 5. Testes automatizados e mensagens observadas

Resultados executados no checkout atual:

- matriz funcional focada pós-E13: `152 passed em 8,74s`;
- matriz focada mais ampla anterior ao harness final: `231 passed`;
- testes documentais, integridade, privacidade e higiene: `55 passed em
  9,93s`;
- `compileall` de `src` e `tests`: `PASS`;
- parser PowerShell do harness: `PASS`;
- smoke da build final10: `SUCCESS`, 11 checks.

Mensagens de produto observadas nas capturas: `Asset colocado`, `Edição do
tilemap aplicada`, `Cenário recarregado`, `Paralaxe atualizada — alterações não
salvas` e `Autoria de cenário — alterações não salvas`. A Biblioteca mostrou
`Problemas: 0`. A única advertência do novo fluxo de menu foi de instrumentação:
o `QMenu` não expôs um handle enumerável, então a tela primária foi preservada;
o popup é visível na captura e não foi confundido com a janela do editor.

## 6. Gate oficial e limitações que não foram escondidas

A execução obrigatória sem filtros foi:

```text
canonical-project-python -m pytest -q
```

Ela coletou `2176` itens e sofreu `ABORTED_FATAL` no teste legado
`tests/test_legacy_phase4_contracts.py::test_phase4_real_segment_timeout_cancels_and_discards_late_result`.
O stack observado passa por `magnetic_lasso_engine.py::_astar_directional`,
`live_wire_path` e `magnetic_lasso.py::run`. Esse abort não foi removido,
filtrado, marcado `xfail/skip`, nem atribuído indevidamente ao lote pós-E13.
O registro curto está em
`artifacts/post-e13-binary-final10-20260910/official-suite-final10-observation.txt`,
SHA-256 `41B240988E744EA010F3BC353E1A51E102E5E79ACD86CCB9DB12554A6323EC96`.

Por isso, a auditoria técnica do lote passou nos fluxos cobertos, mas o gate
global permanece `IN_PROGRESS`; não é legítimo declarar ausência de regressão
global enquanto a suíte oficial não completa.

Limitações adicionais registradas:

- revisão artística humana dos seis PNGs ainda não foi formalmente aprovada;
  a inspeção encontrou fringe/halo visível sobretudo em `Arbusto com flores`,
  `Samambaia` e `Pinheiro`; os originais foram preservados;
- não foi feita a qualificação de DPI, memória e desempenho para catálogo grande;
- `tzdata` continua como warning de hidden import no empacotamento;
- a densidade da timeline requer rolagem após cinco trilhas; os clips não foram
  perdidos e a seleção/inspector permanecem funcionais;
- o catálogo piloto ainda não possui autorização de distribuição/licença
  publicada nem as coleções Ruínas/Cidade futurista;
- o serviço CUA não foi disponibilizado; a evidência nativa usa o fallback Win32
  declarado.

## 7. Proteção contra regressões e conteúdo preservado

- Nenhum asset, objeto, schema, camada, ferramenta ou documento histórico foi
  removido nesta auditoria.
- Falhas e capturas de diagnóstico anteriores permanecem em seus diretórios
  originais; não foram sobrescritas para produzir `PASS`.
- `archive/` e `artifacts/` continuam conteúdo não rastreado preexistente do
  usuário e não foram adicionados ao commit de código/documentação.
- O caminho de inserção por botão/menu, o arraste direto, undo/redo, persistência
  V2 e o renderer real continuam preservados em paralelo.

## 8. Decisões finais reservadas ao proprietário

Com a parte técnica fechada até onde a evidência permite, restam somente estas
decisões de aceite:

1. aceitar formalmente a revisão visual do pacote Floresta ou autorizar uma
   nova versão artística com correção de halo, sem sobrescrever os originais;
2. autorizar licença/proveniência de distribuição e decidir se Ruínas/Cidade
   futurista entram no próximo lote;
3. decidir se o abort do magnetic lasso será tratado em manutenção separada,
   mantendo E13 fechado, ou se deverá bloquear qualquer promoção global;
4. aceitar o fallback Win32 como evidência nativa desta sessão ou exigir uma
   nova rodada quando o serviço CUA estiver disponível;
5. aceitar o warning `tzdata` e a rolagem da timeline para este release, ou
   autorizar um incremento posterior de empacotamento/UX;
6. registrar a revisão humana e o aceite final da build portátil final10.

Até essas decisões e os gates formais, o estado correto deste relatório é
`IN_PROGRESS`, nunca `COMPLETED`.
