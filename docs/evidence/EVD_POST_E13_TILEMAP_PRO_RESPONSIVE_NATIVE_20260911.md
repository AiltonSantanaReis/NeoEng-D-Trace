# Evidência pós-E13 — autoria profissional responsiva de Tilemap e Tileset

**ID:** `EVD-P13-TILEMAP-PRO-RESPONSIVE-NATIVE-20260911`

**Estado:** `IN_PROGRESS / PENDING_EVIDENCE`

**Data:** 2026-09-11

**Base auditada:** `Ailton/e08-renderer-20260908` em `b9341c927160a2dfc17520a10942453b9b156579`

**Mudança:** [`CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md`](CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de continuidade:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Regra de interpretação

Esta evidência registra o checkpoint de implementação, build limpa e fluxo
nativo real do authoring profissional. Ela não declara a mudança completa:
materialização externa em Godot/Unity e o teste negativo de drift de hash ainda
não foram executados. E13 permanece congelado; nenhum asset, documento legado,
teste ou falha histórica foi removido.

## Rastreamento controlado

| Requisito/feature | Operação real | Resultado observado |
|---|---|---|
| `TMAP-003` / `REQ-F04` | selecionar por arraste, copiar 12 células, escolher alvo, colar e aplicar variação com dois tiles por Ctrl+clique | `PASS` no subconjunto implementado; mensagens `Área copiada: 12 células`, `Área colada: 12 células` e `Variação aplicada` apareceram no binário |
| `TMAP-004` / `REQ-F04` | escolher vizinho de Rule Tile, adicionar regra `rule_1 → grass` e aplicar autotiling | `PASS` na autoria visual e persistência da regra; runtime externo continua `PENDING_EVIDENCE` |
| `TMAP-005` / `REQ-F03` | salvar e reabrir o tilemap após as operações avançadas | `PASS` no estado observado; sidecar preservou 24 células, 1 camada e 1 regra |
| `REQ-F03` / `REQ-F04` | criar Tileset do zero com atlas real, gerar, salvar, criar novo e reabrir | `PASS` no fluxo nativo; manifesto preservou 300 tiles de 16×16 e hash do atlas |
| `REQ-F10-UI-ACCESSIBILITY` | usar o painel responsivo em dock estreito e observar labels/status PT-BR | `PASS` no layout capturado; controles e Rule Tiles ficaram visíveis sem clipping |
| `REQ-F02-EVIDENCE-AUTOMATION` | registrar ações, janelas, capturas e SHA-256 | `PASS` para o pacote nativo; método Win32 e fallback estão declarados |

## Testes automatizados

- Suíte focada de Tilemap, Tileset, composição e exportadores: **62 passed in
  2.62s**, sem filtro usado para ocultar falhas. Log:
  `artifacts/post-e13-tilemap-professional-authoring-20260912/focused-pytest-responsive-layout.log`;
  SHA-256 `06ADB2BB350747B58D2243D464627C7988AE321AA8B18689E26C1BF373266277`.
- Suíte oficial sem filtros: **2216 passed, 2 skipped, 1 warning** em 77.35s.
  Log: `artifacts/post-e13-tilemap-professional-authoring-20260912/official-pytest-responsive-layout.log`;
  SHA-256 `EB6A9BD01B3DFC1652B667345CD01529C696E9890970DE014CDB4B628FF9B609`.
- O único warning permaneceu explícito: `DeprecationWarning` em
  `tests/test_merge_coverage_authoring_contracts.py:1341`, relacionado à
  construção depreciada de `QMouseEvent`.
- A tentativa de suíte focada anterior e todos os logs de regressão anteriores
  continuam preservados; nenhum resultado foi sobrescrito para obter `PASS`.

## Build limpa e proveniência

- Executável nativo:
  `build/p12-tilemap-responsive-20260912/release/post-e13-tilemap-responsive-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
  SHA-256 `E85367987E0019C9B1F2BF77D8FC61B549DC2F52CFC7D075B576471731D36310`;
  8.157.363 bytes.
- Pacote portátil:
  `build/p12-tilemap-responsive-20260912/release/post-e13-tilemap-responsive-20260912/NeoEng-D-Trace-0.3.0-win64-portable.zip`;
  SHA-256 `84C90A14678D1508D892FC250BF74CA54BA63458744DB0D2F4519A82AC0EE20C`.
- Proveniência: `build/p12-tilemap-responsive-20260912/release/post-e13-tilemap-responsive-20260912/continuity-provenance.json`;
  SHA-256 `FB7E9E222AE5491D8098FF98BDA8803C9235785C7D8FC604E9F04A249E19DA20`.
- Smoke portátil: `build/p12-tilemap-responsive-20260912/release/post-e13-tilemap-responsive-20260912/smoke/portable-smoke-report.json`;
  SHA-256 `DE46E45FA1D5C8B2FE952E4B190A996EC9EB15FA1F86BBA280274E6023F5AECA`;
  `SUCCESS`, 11 verificações.
- A primeira tentativa em caminho profundo gerou o diagnóstico preservado
  `build-b9341c9-responsive.log`, SHA-256
  `CD7FDCE2FD4F88EFAF3859B076B1DECADEEF8EB09B34E025C153737EC3DA782D`.
  O erro foi carregamento de DLL por comprimento de caminho; a repetição em
  worktree curto passou. Isso não foi reclassificado como falha do código.
- O warning de empacotamento `Hidden import "tzdata" not found!` permaneceu
  registrado no log de build e não foi ocultado.

## Fluxo nativo real de Tilemap

O executável foi aberto em janela nativa maximizada de `3866x2090`. A execução
foi feita com cliques, arrastes, Ctrl+clique, seleção de menu, salvamento e
reabertura. O registro possui 41 ações e 85 PNGs, incluindo a janela do
Editor de Cenário e janelas transitórias.

- Registro: `artifacts/post-e13-tilemap-professional-responsive-native-20260912/actions.jsonl`;
  SHA-256 `7427F125E34FB70FEC692B35E3F5FCBB338A759DD3877A2985F5B13F878546A7`.
- Manifesto de capturas: `artifacts/post-e13-tilemap-professional-responsive-native-20260912/capture-manifest-sha256.txt`;
  SHA-256 `7520A7A255EEA13395F1D13DC9C5223DE32596669DF1AF61BDF50927E40402C8`.
- Captura do layout responsivo:
  [`09-tilemap-panel-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/09-tilemap-panel-responsive-23332244.png)
  — SHA-256 `7517879D601390F528BCE294E23C59305CA1E081DC0CD92F5C212A963703874E`.
- Retângulo real de 12 células:
  [`18-rectangle-painted-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/18-rectangle-painted-responsive-23332244.png)
  — SHA-256 `0C3567AF3A0184B3C3A8A370B364DB794B1650FADCFC95E351640BEC81CAAA7C`.
- Seleção por gesto de 12 células:
  [`26-selection-dragged-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/26-selection-dragged-responsive-23332244.png)
  — SHA-256 `33E19D3E99D714916A00E1730DA1C912E0416870F37A35E63DC0CA971B625522`.
- Colagem observável:
  [`29-selection-pasted-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/29-selection-pasted-responsive-23332244.png)
  — SHA-256 `C3F9EEF312583E1945DA1FCFD6A2CB61A7FAE3B136BAC9A7C25F02EDE666CCB6`.
- Variação com dois tiles:
  [`33-variation-applied-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/33-variation-applied-responsive-23332244.png)
  — SHA-256 `01E4BE9AF79E8031CEA03D89F032E1C2CCC75D61690C8D0599B910ADBA094674`.
- Regra adicionada e aplicada:
  [`36-rule-added-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/36-rule-added-responsive-23332244.png)
  e [`37-rule-applied-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/37-rule-applied-responsive-23332244.png).
- Salvamento e reabertura:
  [`38-tilemap-saved-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/38-tilemap-saved-responsive-23332244.png)
  e [`39-tilemap-reopened-responsive-23332244.png`](../../artifacts/post-e13-tilemap-professional-responsive-native-20260912/39-tilemap-reopened-responsive-23332244.png).

O sidecar copiado após a reabertura é
`artifacts/post-e13-tilemap-professional-responsive-native-20260912/tilemap-persistence/scenario.tilemap.json`,
SHA-256 `B4554475631E91CEAE0D26C2BBB37803E8412CCD1EE32E60F738310DF4FE7641`.
Leitura objetiva: `grid=orthogonal`, `layers=1`, `cells=24`, `rules=1`.

## Fluxo nativo real de Tileset

Uma segunda instância limpa do mesmo executável abriu o fluxo do usuário do
zero: `Ferramentas → Tileset / Atlas` → atlas real → gerar → salvar → `Novo` →
`Reabrir`.

- Manifesto: `artifacts/post-e13-tilemap-professional-responsive-tileset-native-20260912/manifest.json`;
  SHA-256 `1771C0F16EA538DFB902253DD0400183F6EEBADAD63E1184373B2A8B2CAAF6E2`.
- Atlas gerado:
  [`07-tileset-generated.png`](../../artifacts/post-e13-tilemap-professional-responsive-tileset-native-20260912/07-tileset-generated.png)
  — SHA-256 `F592CDC6FA4DE5A99DAAFB5F8C2861BA4AB925FEF9C1801C83AFFEB695E9AB04`;
  a tela mostra `300 tiles · neoeng-d-trace-tileset v1`.
- Tileset salvo:
  [`08-tileset-saved.png`](../../artifacts/post-e13-tilemap-professional-responsive-tileset-native-20260912/08-tileset-saved.png)
  — SHA-256 `E30299A82FA8C2896DB070B450C9CE639DC0D1EC914C17BBBBBB2B0FD979B81C`.
- Reabertura:
  [`10-tileset-reopened.png`](../../artifacts/post-e13-tilemap-professional-responsive-tileset-native-20260912/10-tileset-reopened.png)
  — SHA-256 `29C8B7B2028210561BBD28F3201B4DFB5990903F7AB86EC6D1119F2AC7C5139D`.
- Manifesto persistido:
  `artifacts/post-e13-tilemap-professional-responsive-tileset-native-20260912/tileset-fixture/assets/tilesets/scenario/tileset.json`;
  SHA-256 `E052E41671B87914D0B7C4A31783AFE59D5AE91B1B6F8CC2E5C572FEA45D5E06`.
  Leitura objetiva: `tiles=300`, `tile_size=16x16`,
  `atlas_path=source_atlas.png`, `atlas_sha256=4bffd31518cb8eabcfba2b2a4379ba54d6a1632ebd8836b1cbae36f9b33a9a18`.

## Método e limitações honestas

- O CUA foi tentado antes do fallback e falhou com
  `failed to write kernel assets: O sistema não pode encontrar o caminho
  especificado. (os error 3)`. A execução comprovável usou os scripts nativos
  Win32 existentes, com `mouse_event`, `keybd_event` e `PrintWindow`; o script
  de apoio modificado foi preservado com SHA-256
  `DB081317B06640F7C43A4404CBE519E97136DE93BD5FE322FAC2CEED8AE5D331`.
- O teste negativo de variação com apenas um tile foi executado e exibiu
  `Selecione pelo menos dois tiles na paleta`; ele não foi convertido em
  sucesso.
- O menu `Mais` real exibiu somente `Atualizar V1 para V2` e `Recuperar Último
  Válido`; não há seletor de idioma nessa superfície. A localização PT-BR
  observada nos painéis e mensagens foi preservada, e a ausência do seletor
  permanece um finding.
- O painel de Tilemap não exibiu menu de contexto próprio nesta execução; isso
  não invalida o menu contextual do viewport profissional já comprovado em
  evidência anterior, mas continua separado do fluxo de Tilemap.
- O pacote ainda não comprova materialização em engine externa Godot/Unity,
  contagem de células no runtime e rejeição de drift de hash. Portanto o estado
  deste registro permanece `PENDING_EVIDENCE`.
- A revisão humana final segue `HUMAN_REVIEW_DEFERRED` até iluminação
  direcional, efeitos orientáveis, partículas completas, Tilemap/Tileset e
  editor híbrido 3D estarem fechados.

## Próximo gate autorizado

Implementar o payload de runtime do Tilemap/Tileset e executar materialização
headless real em Godot e Unity, incluindo caso positivo, drift de hash negativo,
contagem observável de células/camadas/atlas e preservação dos sidecars. Só
depois disso este registro poderá ser reavaliado; não há decisão do proprietário
necessária nesta subetapa.
