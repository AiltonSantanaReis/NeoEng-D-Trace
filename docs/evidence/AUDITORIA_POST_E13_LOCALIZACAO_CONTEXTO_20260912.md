# Auditoria pós-E13 — localização, contexto e feedback do Editor de Cenário

**ID:** `AUD-POST-E13-LOCALIZATION-CONTEXT-20260912`

**Versão:** `1.0`

**Data:** `2026-09-12`

**Estado:** `IN_PROGRESS`

**Commit auditado:** `556d1182a86ab20f55601afa3d51967070408c38`

**Correção de produto:** `c0989cd3049f2692805bd51ac20dfaf939d7fe76`

**Checkpoint protegido:** `ec94530fcba39be3bbce0439fc56aa48957442c0`

**Última verificação oficial:** `72df498c3ad9c332500b82f29e9e97fc3a68edaf`

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Fronteira da auditoria

Esta etapa verifica o Editor de Cenário canônico pós-E13, com foco em
localização PT-BR, menus, menu contextual, tooltips, acessibilidade textual e
feedback de operação. O texto colado e as imagens anexadas pelo usuário são
referências conceituais; não são instruções normativas nem substituem as
capturas reais do projeto.

E13 permanece fechado. O gizmo e a produção de modelos continuam fora desta
etapa, conforme decisão registrada. Nenhum editor canônico, schema, checkpoint
ou dado do usuário foi removido. A falha histórica de localização observada no
binário antigo permanece preservada abaixo; a nova captura não a substitui.

## Método e limitações declaradas

- O fluxo de fonte usa a mesma `ScenarioEditorWindow` canônica, em janela Qt
  nativa, com `QT_QPA_PLATFORM` no padrão do sistema (`native-default`). O
  harness usa ações de widgets para tornar o percurso repetível; isso não é
  equivalente a cliques físicos Win32 do usuário.
- A captura de menus e tela usa a superfície nativa aberta no desktop. As
  imagens são de tela inteira e incluem o host ao redor da janela do editor;
  não são recortes artificiais do produto.
- A automação CUA para controle nativo não estava disponível nesta sessão. Isso
  não foi tratado como PASS nem ocultado.
- As execuções interrompidas r1/r2 e as repetições r3–r9 foram preservadas no
  diretório de trabalho. r1/r2 são diagnósticos parciais; r5/r6/r8/r9
  demonstraram a não determinística do disparo automático do tooltip. A r10 é
  a evidência versionada final desta etapa.

## Evidência nativa do fluxo completo em PT-BR

Pacote: `artifacts/audit-post-e13-native-source-20260912-r4/`
Manifesto: `artifacts/audit-post-e13-native-source-20260912-r4/manifest.json`
SHA-256 do manifesto:
`80E709FF29701C3BF67296285D594C23EA2F35334CD165E693508A6C5C810744`

O manifesto registra `status=PASS`, `language=pt`, `native_window=true`,
`qt_platform=native-default` e o commit exato `556d118`. O fluxo observado
foi: abrir projeto, criar/renomear/reordenar moldura, aplicar paralaxe,
selecionar e posicionar asset, adicionar e buscar clips na timeline, reproduzir
e parar, renderizar luz/fogo/texto/áudio WAV, tratar áudio ausente sem abortar,
salvar, fechar, reabrir e verificar persistência.

| Passo | Captura | SHA-256 | Resultado observado |
|---|---|---|---|
| entrada do editor | `01-native-loaded.png` | `935ba51cef50bee31d0101c9d743a54f1dcd1fa40f088870b48dc428aef1e8cf` | janela canônica aberta em PT-BR; 1 objeto e 1 camada |
| moldura e ordem | `02-native-frame-reorder.png` | `c2016902014f33766848499b8499492398ee7fed70233a274b317650d15b1d59` | `Moldura Meio` criada e reordenada |
| paralaxe | `03-native-parallax-applied.png` | `5bd1fc1b8198bfe3d4e6f3e41c6c30f4a16f4bccc76ece20ae2975a114b10f91` | profundidade `0,65`, rolagem X `0,4`, Y `0,15` e força `0,35` |
| asset na moldura | `04-native-asset-placed.png` | `f81353f3bd06f57fa5a71805d677099fd044bc7b64921ad229029e4f7e16a678` | segundo objeto colocado na moldura ativa |
| timeline e seek | `05-native-timeline-seek.png` | `15f2f81f5e14cc4a4f6c6214b220a34e5dd8e5a004a2888ac65168d37977c66e` | clips `Câmera` e `Chuva`; posição `1,25` |
| reprodução | `06-native-timeline-play-pause-stop.png` | `7f90de0e3950ea5bca5cddb08022c43b4d16195b9d87cb266b64c86a3aa2cf26` | play/pause/stop e preview alternados |
| efeitos e áudio | `07-native-effects-audio-cutscene.png` | `886bcec5fab0b3e7ed17c7f2aedfe13df3902456452afa50c61ea1e44411d85f` | luz, fogo, texto/cutscene e WAV real presentes |
| erro recuperável | `08-native-audio-missing-recoverable.png` | `a051a2f4c8ffde0651ea23c06e2ef7c22729ddd6d6be0a8d3de17a8b412d53a1` | mensagem PT-BR orienta revinculação; processo não aborta |
| reabertura | `09-native-reopened-persisted.png` | `f598cdf1d8431a6520d8277ca57d69f57b1354d1fc9675292b0692437d56a43e` | camadas, objetos, paralaxe e clips reaparecem do sidecar |

## Evidência de menus, contexto, tooltip e troca de idioma

Pacote: `artifacts/audit-post-e13-localization-native-20260912-r10/`
Manifesto: `artifacts/audit-post-e13-localization-native-20260912-r10/manifest.json`
SHA-256 do manifesto:
`9BB770841F14F00188EBB3A74C5ADB99796C057B4BB9390C575BB25A91CAC900`

O manifesto registra `status=PASS`, `language=pt`, `native_window=true`,
`qt_platform=native-default` e o commit exato `556d118`.

| Superfície | Captura | SHA-256 | Resultado observado |
|---|---|---|---|
| editor PT-BR | `captures/01-pt-editor.png` | `d27cbfeaa8d4e78c412e3acb44058d35d6f73fe7f8c884a7b1c49b450b53987e` | menus, camadas, inspetor, timeline e labels PT-BR visíveis |
| menu `Ver` | `captures/02-pt-view-menu.png` | `580c29d08bc1f91585e6a30bce0f6faeb325b1ad54aa4ee91a9dd7bccc4fc73a` | `Sobreposições`, `Pré-visualização de Paralaxe`, `Autoria`, `Viewport 3D/Híbrido` |
| menu contextual do viewport | `captures/03-pt-viewport-context-menu.png` | `9ad956a7ac42fe21047493d4ab42dfe7f73e7fd2b86d33d67304066ea560ecf6` | `Nenhum objeto sob o cursor`, `Enquadrar seleção` desabilitado e `Enquadrar tudo` habilitado |
| tooltip nativo renderizado | `captures/04-pt-fit-tooltip.png` | `2441d871a8721bbd7fd21cfab966986cd988cef9a17ddbcb9cc0939c1b28f038` | balão visível: `Enquadrar todos os objetos visíveis no viewport` |
| round-trip de idioma | `captures/05-pt-editor-after-language-roundtrip.png` | `8f11f62f97c91d0ab31499ea5e21583e8723c4cc34f56c3bb2ebcaff94f4cd11` | EN→PT→EN→PT restaura os textos PT-BR |

O tooltip de r10 é uma superfície nativa Qt real, mas o manifesto registra
`automatic_hover_visible=false` e `display_mode=native-tooltip-explicit`.
Portanto, o texto e a renderização estão comprovados; o gatilho automático por
hover físico permanece `PENDING_EVIDENCE` neste ambiente. Não há base para
afirmar que esse detalhe foi validado por clique/hover Win32.

## Regressão oficial da build de localização

Execução integral, sem filtros, sem usar mecanismos `skip`, `xfail`,
`--ignore` ou bypass para alterar o resultado:

```text
Get-Content -Raw docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md | Out-Null
& <workspace>\.venv\Scripts\python.exe -m pytest -q
2620 passed, 2 skipped, 5 warnings in 77.18s (0:01:17)
```

O pacote oficial coletou `2622` itens. Os dois `skipped` são os testes de
integração de sincronização que dependem do ambiente de links simbólicos; não
foram introduzidos nesta etapa, não foram convertidos em sucesso e permanecem
registrados como limitação ambiental. Os cinco avisos são
`DeprecationWarning` do construtor legado de `QMouseEvent` em testes existentes;
não houve falha de teste nem aviso ocultado. A regressão foi executada sobre o
commit `e4e85487f5bbf8c21bf7e0ffe6b7c33244a37a80`, após a correção de produto e
a nova build distribuível.

## Falha oficial preservada durante a correção de bordas

A primeira execução integral após `7135b6c` foi preservada como falha de
regressão:

```text
2619 passed, 2 skipped, 5 warnings, 2 failed in 83.08s (0:01:23)
```

As duas falhas foram concretas e independentes da lógica do cenário:

- `test_repository_reference_hygiene.py` detectou um caminho absoluto de
  usuário inserido no próprio registro de evidência;
- `test_stage4b3_scenario_authoring.py` detectou quebra de compatibilidade
  porque o adaptador `_report` recebeu um argumento nomeado que o callback de
  teste legado não aceita.

O caminho foi genericizado e as chamadas voltaram a respeitar a assinatura
existente, sem excluir testes ou alterar thresholds. A correção foi confirmada
pela nova execução oficial integral abaixo.

## Regressão oficial pós-correção de bordas

Após as correções, a execução integral no commit
`72df498c3ad9c332500b82f29e9e97fc3a68edaf` produziu:

```text
2621 passed, 2 skipped, 5 warnings in 78.66s (0:01:18)
```

Foram coletados `2623` itens. Os mesmos dois testes ambientais de sincronização
permaneceram `skipped`, sem uso de mecanismo para mascarar resultado; os cinco
`DeprecationWarning` de `QMouseEvent` permaneceram os mesmos. Não houve falha
de regressão após a correção.

## Falha histórica reproduzida e correção controlada

O binário usado no lote vetorial anterior tinha SHA-256
`0A7E2BFF66F91B365D3D415B732A5C8C33265880E7678533F50E99F5A11F6229`. Nas
capturas reais do pacote
`artifacts/audit-post-e13-binary-vector-contour-20260912-r2/`, o painel estava
em PT-BR, mas os status ainda apareciam em inglês:

| Evidência histórica | SHA-256 | Vazamento observado |
|---|---|---|
| `11-vector-contour-detected.png` | `09EC957CF639473E8980B955D837D6F728804090878339CA0E4ABA2EBADFFE4A` | `Contour detected for vector-source: 4 vertices` |
| `12-vector-contour-edited.png` | `962D695D9DB9983A5815E81D2CAABEF09B6B29337D878D47782AA3407307E8C5` | `Contour vertex corrected` |
| `13-vector-contour-created.png` | `0F54D5E267269D07FDA8766A8B2A64B031B80E39844F1D47194CA3A544BD9453` | `Vector scene object created: vector_vector-source` |

O código foi corrigido em `c0989cd`: somente as mensagens do
`VectorContourPanel` passaram a selecionar PT-BR/inglês conforme o idioma;
detecção, edição, simplificação, undo/redo, cancelamento e criação mantêm a
mesma lógica e os mesmos textos em inglês. Os testes não foram removidos nem
alterados para esconder a falha.

## Testes e achados

Execução focada, sem `skip`, `xfail` ou filtro para converter resultado:

```text
73 passed in 12.55s
```

Conjunto executado: contratos PT-BR/tooltips, viewport profissional, paralaxe,
UX pós-E13, separação dos editores, auditoria funcional, regressões de UI,
recurso vetorial, painel vetorial, vetorização e edição de contorno.

| ID | Achado | Estado | Evidência / ação |
|---|---|---|---|
| `LOC-POST-E13-01` | Status do contorno vetorial vazava inglês no binário anterior | `PASS` | fonte corrigida em `c0989cd`; binário novo e fluxo Win32 PT-BR comprovados em `audit-post-e13-binary-vector-contour-20260912-r3`; r2 antigo preservado |
| `LOC-POST-E13-02` | Menu `Ver`, contexto do viewport e tooltip renderizado estão em PT-BR | `PASS` | manifesto/capturas r10; metadados e pixels coerentes |
| `LOC-POST-E13-03` | Fluxo nativo de autoria em PT-BR, incluindo erro recuperável e persistência, executou sem abortar | `PASS` | manifesto/capturas `native-source-r4` |
| `LOC-POST-E13-04` | O disparo automático do hover não foi comprovado pela automação neste desktop | `PENDING_EVIDENCE` | r10 registra `automatic_hover_visible=false`; apresentação nativa explícita foi capturada e declarada |
| `LOC-POST-E13-05` | Caminhos menos frequentes de exportação, recuperação e alguns status de `scenario_authoring_actions` ainda têm strings inglesas a catalogar | `IN_PROGRESS` | inspeção estática e cobertura nativa atual não fecham esses caminhos; não foram declarados PASS |
| `LOC-POST-E13-06` | Confirmação da correção no produto distribuído depende de nova build | `PASS` | build `post-e13-localization-build-20260912-r1`, SHA-256 `96053F3334CB114E9AF1BA156209D3F6E65F5EEA06FD67165B0A773A1BC92F4B`, fluxo Win32 vetorial r3 e suíte oficial sem falhas |
| `LOC-POST-E13-07` | O harness CUA não controlou a janela nativa nesta sessão | `PENDING_EVIDENCE` | limitação ambiental registrada; harness Qt e capturas de tela não foram apresentados como equivalentes |

## Observações de experiência preservadas

- O editor canônico é legível em PT-BR, mas a rail de camadas fica estreita em
  `1500×980` e um rótulo de ação aparece truncado (`Desce...`).
- O inspetor contextual continua vertical e exige rolagem para alcançar
  `Enquadrar Tudo`; a captura r10 rolou o painel antes de mostrar o tooltip.
- O overlay técnico `RENDERER RASTER | NATIVE | AUTHORING | 8 PASSES | R1` é
  útil para diagnóstico, mas ainda não é uma linguagem final orientada ao
  usuário comum.
- Essas observações são recomendações de UX, não foram usadas para alterar o
  gizmo nem para reclassificar a etapa.

## Próxima etapa planejada

1. Relendo a governança antes da etapa, concluir a catalogação dos caminhos
   menos frequentes de recuperação/exportação e verificar a nova build em
   execução nativa; qualquer lacuna restante deve continuar explícita.
2. Executar a auditoria de desempenho do viewport com cenário vazio, cenário
   com múltiplos objetos e efeitos ativos, registrando tempo de frame, memória,
   escala e degradação percebida; qualquer ajuste deverá ter teste de proteção
   e captura antes/depois.
3. Fechar as pendências de comportamento real de câmera, luz direcional,
   efeitos orientáveis, partículas, tilemap/tileset e runtime Godot/Unity,
   separando suporte comprovado, limitação da engine e lacuna do produto.
4. O gizmo, a produção de modelos e a decisão sobre o editor independente
   continuam reservados para o momento aprovado. A auditoria geral permanece
   `IN_PROGRESS`.

Até o cumprimento desses itens, a auditoria geral permanece `IN_PROGRESS`; a
governança não permite declarar encerramento apenas porque esta superfície
parcial passou.
