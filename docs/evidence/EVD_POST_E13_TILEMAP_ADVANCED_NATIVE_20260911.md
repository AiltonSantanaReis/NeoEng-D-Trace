# Evidência pós-E13 — ferramentas avançadas do Tilemap no binário nativo

**ID:** `EVD_POST_E13_TILEMAP_ADVANCED_NATIVE_20260911`

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`

**Data:** 2026-09-11

**Base auditada:** `Ailton/e08-renderer-20260908` em `0689e72c9051c3daeb42d656b87e9128f2a736ba`

**Mudança:** [`CHG_POST_E13_TILEMAP_ADVANCED_TOOLS_20260911.md`](CHG_POST_E13_TILEMAP_ADVANCED_TOOLS_20260911.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de continuidade:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Regra de interpretação

Esta evidência comprova somente as operações realmente executadas no binário
hashado. Ela não promove a captura automatizada à revisão humana, não declara o
Tilemap/Tileset completo e não apaga o fluxo anterior que revelou o problema de
undo por segmento.

## Rastreabilidade

| Requisito/feature | Entrada e operação real | Resultado observado |
|---|---|---|
| `TMAP-003` / `REQ-F04` | abrir o combo de ferramentas, selecionar Retângulo e arrastar no canvas | bloco retangular visível; status `Retângulo aplicado` |
| `TMAP-003` / `REQ-F04` | selecionar `water`, escolher Balde e clicar na região | região preenchida; status `Preenchimento aplicado` |
| `TMAP-003` / `REQ-F04` | escolher Conta-gotas e clicar em célula ocupada | tile `water` selecionado; status `Tile selecionado: water` |
| `TMAP-003` / `TMAP-005` | selecionar Borracha e arrastar sobre o bloco | 12 → 8 células, com captura do estado real |
| `TMAP-005` | clicar `Desfazer` e depois `Refazer` nos botões visíveis | 8 → 12 → 8 células; um gesto inteiro por comando |
| `REQ-F03-SCENE-PERSISTENCE` | salvar, reabrir e ler o arquivo gerado | 8 células `water`, grade `orthogonal`, JSON preservado |
| `REQ-F10-UI-ACCESSIBILITY` | observar o painel estreito do Inspector | `Adicionar camada`, `Desfazer` e `Refazer` completos e acionáveis em PT-BR |
| `REQ-F02-EVIDENCE-AUTOMATION` | registrar cliques, teclas, arrastes, janelas e SHA-256 | manifesto `actions.jsonl` e 56 PNGs hashados |

## Testes automatizados

- Foco: `35 passed` em 1,39 s.
- Log focado: `artifacts/post-e13-tilemap-advanced-responsive-native-20260911/focused-pytest.log`.
- SHA-256 do log focado: `11DEBFFB55CB5C69AE3F9483A4DDD7BEE09EC830EF38608240EDA6DE567F9BCF`.
- Suíte oficial, sem filtros: `2215 collected; 2213 passed; 2 skipped; 1 warning`.
- Comando oficial: `.venv311\Scripts\python.exe -m pytest -q`.
- Log oficial: `artifacts/post-e13-tilemap-advanced-responsive-native-20260911/official-pytest-0689e72.log`.
- SHA-256 do log oficial: `ACC5C0C713E94627FF2DFB1F1C96E5CF1CF45F8BA9FEF8DEAB909B1AB75581EE`.
- Reexecução oficial após a atualização do índice e do registro canônico:
  `2213 passed, 2 skipped, 1 warning`.
- Log final dessa reexecução:
  `artifacts/post-e13-tilemap-advanced-responsive-native-20260911/official-pytest-final-docs.log`;
  SHA-256 `DD3AF5F6DF0C4EDD4CAC9FB1E23FBB356F5C7E648D2E4757D6194CDA0132514A`.
- O warning é o conhecido `DeprecationWarning` do construtor de
  `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`.

## Build e proveniência

- Diretório de build: `build/post-e13-tilemap-advanced-source-20260911/build/post-e13-tilemap-advanced-responsive-20260911/`.
- Branch de build: `Ailton/post-e13-tilemap-advanced-build-20260911`.
- Commit de origem: `0689e72c9051c3daeb42d656b87e9128f2a736ba`.
- Executável: `build/post-e13-tilemap-advanced-source-20260911/build/post-e13-tilemap-advanced-responsive-20260911/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- SHA-256 do executável: `0F79231DE0F242F77EFE29BA1AA1F98749A2DC686B732E43A4C7BA9D68B1C423`.
- Pacote portátil: `build/post-e13-tilemap-advanced-source-20260911/build/post-e13-tilemap-advanced-responsive-20260911/NeoEng-D-Trace-0.3.0-win64-portable.zip`.
- SHA-256 do pacote: `A228EE9FEA349795922A4E224B6025F4022BA4F5CFA3819F43966A7B926D2C24`.
- Proveniência: `build/post-e13-tilemap-advanced-source-20260911/build/post-e13-tilemap-advanced-responsive-20260911/continuity-provenance.json`.
- SHA-256 da proveniência: `EEF375B2149DFC56A382442AA62472F842626FEF2179188C2BF0D631EF7E97C1`.
- Smoke: `smoke/portable-smoke-report.json`, SHA-256
  `8708AEBE108726F1F5386854B73B1F2C6025C621F2F395A7B1C43319B49E8D86`,
  `SUCCESS`, 11 checks.
- Warning de build preservado: `Hidden import "tzdata" not found`.

## Execução nativa real

O executável foi iniciado com PID `34344`. A janela principal teve HWND
`14550466`; o Editor de Cenário teve HWND `23792058` e foi maximizado para
`3866x2090` em tela de `3840x2160`. A sequência usou entrada Win32 real,
captura `PrintWindow` e observação após cada operação. O CUA não estava
disponível nesta sessão (`failed to write kernel assets`); isso foi declarado e
não substituído por mock ou simulação.

Pacote de capturas: `artifacts/post-e13-tilemap-advanced-responsive-native-20260911/`.

Manifesto: `actions.jsonl`, 26 registros, 56 PNGs.

SHA-256 do manifesto: `448E10EBC701729B8C6D24132B447A73C31AE8C1ECAB0AED8E7D17A29C3EB7C0`.

Sequência observada: abrir `Cenário` → `Novo Cenário` sem asset 2D → adicionar
clip de timeline para acessar `Ferramentas` → abrir `Tilemap / Terreno` →
`Novo` → Retângulo → arraste → seleção de tile → Balde → preenchimento →
Conta-gotas → Borracha → arraste → Desfazer → Refazer → Salvar → Reabrir.

Nenhuma janela de erro foi observada. O processo de teste foi encerrado e
confirmado como `PROCESS_STOPPED=34344`.

## Capturas reais e hashes

| Estado | Artefato | SHA-256 |
|---|---|---|
| painel responsivo com ações visíveis | `07-tilemap-panel-23792058.png` | `BF8D9939EE10E72DBD5BD32B5510CC5FA15602FBB214D9A2DE48FA793107C3CC` |
| menu nativo com cinco ferramentas | `09-tool-menu-open-12650752.png` | `1754720DAE39E61AD5588B0B2D11898D2F857E417A5C6BD5BC0A4E2D1234CB9E` |
| Retângulo aplicado | `11-rectangle-painted-23792058.png` | `AD5A435326659129BCBE35699E715B95B2980AECAB061775DD56FAC775FF0274` |
| Balde aplicado | `16-bucket-filled-23792058.png` | `E95FFE8122FCD387C8041F3C4794B9BFF7E2A4E920AEE56F249865983F1289B4` |
| Conta-gotas aplicado | `19-picker-applied-23792058.png` | `8FD1025740AFA43171C553CD59E3933C937CD1BEBCC9AE1C09AC0B0F4E9E158E` |
| Borracha: 8 células | `22-eraser-applied-23792058.png` | `FFE420A79060A91ACA2F205F4E526F4830EF585032E70DA7C425370807CB2861` |
| Desfazer: 12 células | `23-undo-eraser-23792058.png` | `BCB48D4D54FB37F04E53C08393F6F73F290089E46A7F35A2BAF5C76C890313EF` |
| Refazer: 8 células | `24-redo-eraser-23792058.png` | `8B04E3BDB46F4298D545538DCD7BEC49A2E6B9E5142AAF416E4494152735ECAC` |
| salvar | `25-tilemap-saved-23792058.png` | `03B95A11AB26CA9DA6B12CC8DFCA0817F048882A429B6042719D0B5D2831EF40` |
| reabrir | `26-tilemap-reopened-23792058.png` | `8D189B39452BBDEF8DBB1F5B14AEC0F1DB5FA319614F6771F7689C74D9513C4D` |

## Persistência observada

O arquivo escrito pelo binário foi copiado sem alteração para:
`artifacts/post-e13-tilemap-advanced-responsive-native-20260911/tilemap-persistence/scenario.tilemap.json`.

- SHA-256: `83229F5A3D9E701AEAF2C585C408E8EB0C269E4285C8265E4B1AD4D6F987D8EE`.
- Leitura objetiva: `grid=orthogonal`, `cells=8`, `tile_ids=water`.
- O caminho temporário real observado foi
  `%TEMP%\neoeng-d-trace-scenario-kt70bzba\assets\tilemaps\scenario.tilemap.json`;
  a cópia no pacote de evidência foi preservada para não depender do ciclo de
  vida do diretório temporário.

## Resultado e limites

`PASS` no subconjunto comprovado de ferramentas avançadas, transação por gesto,
layout responsivo, localização PT-BR e persistência observável. Permanecem
`PENDING_EVIDENCE`: autotiling/Rule Tiles, variação avançada, seleção/cópia/
colagem completas na UI, equivalência de runtime externo e refinamentos de
snapping. O checkpoint não substitui a revisão humana final, que continua
deferida até os itens formais restantes do pós-E13.
