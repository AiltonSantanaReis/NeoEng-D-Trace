# E08 — Composição 2.5D, iluminação, sombras e FX reais

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E08_CONTRATO_RENDERER_25D_FX_2026-09-08.md`.
Dependência técnica: E07 checkpoint `d35bc84`.

## Estado dos lotes

- E08-A — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: plano de composição e fronteira de backend.
- E08-B — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: câmera e paralaxe profissional.
- E08-C — `IN_PROGRESS`: C1–C4 têm checkpoint técnico comprovado; E08-C
  permanece aberto somente para auditoria final antes da promoção formal.
- E08-D — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: D1 partículas,
  D2 shaders e D3 pós-processamento comprovados em checkpoint técnico.
- E08-E — `IN_PROGRESS`: determinismo temporal e matriz de capacidade por
  backend/destino.

Nenhum efeito visual será declarado suportado antes de saída observável,
comparação, teste de falha e captura real do binário. Symlink e revisão humana
ficam reservados à auditoria final.

## Análise de impacto E08-A

- módulos: `src/core`, `src/ui/canvas_view.py`, schema V2 apenas quando um
  parâmetro autoral precisar persistência, e testes de composição;
- contratos preservados: V1/V2 existentes, viewport autoral, seleção,
  `position.z`, parallax atual e fallback raster;
- risco principal: alterar o caminho de preview e regressar cenas antigas;
- proteção: plano de renderização puro, testes de ordenação/cache/resize e
  comparação do preview antigo antes de habilitar o novo caminho;
- rollback: feature flag local e fallback raster, sem modificar documentos
  legados.

## Checkpoint técnico E08-A

- Build r28: `release/e08-renderer-20260908-r28`.
- Source commit: `2bd85fc52bf76edcbe0626718eaea839997e8e44`.
- Binário: SHA-256 `7F4F8E95DB57C7E6713CDAA9AA3F7E43A1CAD73F767809EC0FCBBC2567CF0199`.
- Arquivo portátil: SHA-256 `d58e581129fe9382f31ad71c17997771001ccb73212b8a2d3e6062d77e5fed2e`.
- Smoke portátil: `SUCCESS`, 11 checks.
- Suíte oficial: `2051 passed, 2 skipped, 1 warning`.
- Capturas e hashes: `docs/evidence/E08_A_R28_CAPTURAS_MANIFESTO.json`.
- Preview real: `RENDERER RASTER | NATIVE | PREVIEW | 8 PASSES | R1`, controles
  desabilitados e status `Scenario preview — read-only`.
- Retorno real à autoria: `RENDERER RASTER | NATIVE | AUTHORING | 8 PASSES | R1`,
  controles reativados e status `Scenario authoring`.
- Inspeção visual: português preservado, HUD legível, sem clipping observável,
  viewport e inspector estáveis na superfície 3866×2090.

E08-A e E08-B estão selados apenas como checkpoints técnicos; E08-C permanece ativo. Symlink
e revisão humana continuam pendentes por autorização e serão executados somente
na auditoria final do Plano Mestre.

## E08-B — contrato de câmera/paralaxe em execução

### Escopo e critérios rastreáveis

- [x] Separar a matemática da câmera do widget Qt e preservar os campos
  legados de profundidade/força.
- [x] Persistir `scroll_x`, `scroll_y`, `offset_x`, `offset_y` e os quatro
  flags de repetição/espelhamento com defaults retrocompatíveis.
- [x] Propagar os novos campos por schema V2, bridge, preview determinístico e
  viewport profissional.
- [x] Expor a edição no inspetor com limites, labels explícitos e operação
  transacional Undo/Redo.
- [x] Cobrir movimento negativo, zoom, âncoras, round-trip, variantes de tile,
  limites inválidos e proteção contra aplicação dupla.
- [x] Executar suíte oficial, estática, build limpa e captura real do binário
  após o lote; evidência final em `docs/evidence/E08_B_R35_CAPTURAS_MANIFESTO.json`.

### Semântica aprovada

`scroll_x/y` são fatores assinados independentes em `[-4, 4]`; offsets são
finitos em unidades de mundo; repetição/espelhamento são metadados persistidos
que geram variantes determinísticas para o renderer sem reinterpretar `z`.
Defaults (`1, 1, 0, 0, false, false, false, false`) preservam a projeção
anterior. Positivos em `offset_x/y` deslocam o conteúdo para a direita/baixo.

### Estado da implementação

- Commits de implementação e validação: `2c344805cc3fdebcdb2c3ad264e20a367a021ecc`,
  `75d360e`, `c86707b`, `92c0a1f` e `5838485`.
- Teste focado: `12 passed` para o contrato E08-B, câmera legada,
  inspector/viewport, preview e exportação; a suíte oficial registrou
  `2063 passed, 2 skipped, 1 warning`.
- Build r35: source commit `5838485a44122bf5f8071a32ae5a8ceac4287edb`,
  binário SHA-256 `F8DFBDE36615946A827FB18D8101229E8159A14E81013599F71B07331628A111`,
  pacote portátil SHA-256 `a926ac951bc633571629d92b1ab84bb97f0dd9089edea35ce1591d53006350e0`,
  smoke `SUCCESS` com 11 checks.
- Captura real: Preview, Authoring e inspector foram executados pelo binário
  portátil; a captura final mostra `Câmera, Paralaxe e Sockets`, `Rolagem X/Y`,
  `Deslocamento X/Y` e `Repetir/Espelhar` em português. O manifesto com hashes
  está em `docs/evidence/E08_B_R35_CAPTURAS_MANIFESTO.json`.
- Limitação declarada: repetição/espelhamento são metadados determinísticos
  persistidos nesta fase; renderização visual de atlas/alpha/tile permanece
  deliberadamente fora do claim até o lote de renderer correspondente.
- Symlink e revisão humana: `DEFERRED_UNTIL_FINAL_AUDIT`, sem reexecução.

## E08-C — materiais, normal maps, luzes e sombras em execução

### Estado do sublote técnico

- `E08-C.1` — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: passe raster
  determinístico conectado ao `CanvasView`, com ambiente, luz pontual,
  material/albedo, emissão, normal perturbada, opacidade e oclusão explícita.
- `E08-C.2` — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: o contrato foi
  conectado ao viewport profissional V2; sockets de luz persistidos são
  resolvidos pelo passe e os controles autorais permanecem acessíveis.
- `E08-C.3` — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: build r39,
  smoke, suíte oficial e capturas V2 reais estão documentados no manifesto
  hashado `E08_C_R39_LIGHTING_V2_CAPTURAS_MANIFESTO.json`.
- `E08-C.4` — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: autoria e
  persistência explícitas de material/albedo/normal map no fluxo V2, seleção
  nativa no binário, pixels observáveis e controles habilitados comprovados em
  build r42; manifesto hashado em
  `docs/evidence/E08_C_R42_MATERIAL_AUTORIA_CAPTURAS_MANIFESTO.json`.

### Evidência do sublote E08-C.1

- Commit do núcleo: `5e6d188`; integração no passe legado: `255c4e1`.
- Testes: `tests/test_e08_lighting_pixels.py` cobre intensidade zero,
  alteração por normal map, oclusão e emissão; regressão completa registrou
  `2066 passed, 2 skipped, 1 warning`.
- Build r37: source commit `255c4e1cec7482154203ddecd96c4aeec62ab15c`,
  binário SHA-256 `17512C197D7EDD638826FB73E048DDA415072248FD14FB4BC8695ADF14AF5BDB`,
  pacote portátil SHA-256 `af562ad48bf8ca69ed4364a86f824de7c60aca1970acb9fa66be08b243807fd5`,
  smoke `SUCCESS` com 11 checks.
- Captura real: `artifacts/e08-renderer-20260908/binary-capture-r37-lighting/03-main-after-project-load.png`,
  SHA-256 `A7EF6FD7A8610CA8524CA45880F75E063DF1EB7EEC00C064E8A6C2ABA7D2F180`.
  A fixture `tests/fixtures/e08_lighting_smoke.ndtproj` contém um receptor e um
  occluder grandes; a imagem mostra os pixels do receptor alterados pelo passe
  de luz no executável portátil.
- Limitação observada: o carregamento direto dessa fixture é V1 e abre no
  canvas legado; Preview Parallax trabalha em sessão V2 e permanece vazio para
  essa entrada. Isso é uma fronteira de compatibilidade a resolver em E08-C.2,
  não uma aprovação por extrapolação.

### Evidência dos sublotes E08-C.2 e E08-C.3

- Commit auditado: `bd8101d6c39f6d140b104fe68c685a582de380a6` na branch
  `Ailton/e08-renderer-20260908`.
- A fixture V2 `tests/fixtures/e08_lighting_smoke.ndtscene.json` contém dois
  objetos e o socket persistido `key-light (light)` em `(160, 220)`, com cor,
  intensidade e raio definidos. O viewport resolve esses parâmetros para
  `ScenePointLight` antes de calcular a cor dos objetos.
- Build r39: binário SHA-256
  `10EF967993EA2C5578356C28E57A006BAF692A28EBC64C66737A80C9015DDE51`,
  pacote portátil SHA-256
  `9DCFE4FF5BAD9DE3B6DD283AF527F3ECEEADB13BB477623B7CDB1A0AFF319E7B`,
  smoke `SUCCESS` com 11 checks.
- Suíte oficial: `2067 passed, 2 skipped, 1 warning`. A primeira execução
  apresentou access violation transitório em `test_stage4_ui_top_toolbar.py`;
  o teste isolado e a repetição completa passaram, portanto o incidente fica
  preservado como ressalva de execução e não como finding funcional do E08-C.
- Capturas reais do binário: Preview
  `06-renderer-preview.png` (`02E03498...B7F81`), Autoria
  `07-renderer-authoring.png` (`75C04363...3136BA`) e inspector/paralaxe
  `08-parallax-controls-bottom.png` (`E51A9304...F69BF2`). Elas mostram os
  objetos iluminados, o HUD `RENDERER RASTER | NATIVE`, o modo Preview/Autoria,
  os controles em português e o socket persistido no inspector.
- Manifesto completo e hashes: `docs/evidence/E08_C_R39_LIGHTING_V2_CAPTURAS_MANIFESTO.json`.

### Evidência do sublote E08-C.4

- Commit de implementação auditado: `e8a602e`; harness de captura e
  requalificação nativa: `175b2ec8a40c2dfa664deec5a3b16a1a33007d24`.
- O schema V2 persiste albedo, normal map vetorial, força da normal, emissão,
  força da emissão, opacidade e flags de receber/projetar sombra. A sessão
  aplica a alteração de forma transacional e permite Undo/Redo; save/reopen
  preserva os campos.
- Testes focados: `40 passed`, incluindo pixels alterados pelo material,
  round-trip de persistência e edição transacional do inspector.
- Suíte oficial atual: `2070 passed, 2 skipped, 1 warning`; Black, mypy e
  `git diff --check` passaram no escopo E08-C.
- Build r42: source commit
  `175b2ec8a40c2dfa664deec5a3b16a1a33007d24`, binário SHA-256
  `10E2813F7FD4A3095E62007A89A3FF26A68917A76F1DD4B2E8E45DCF1A1C605C`,
  pacote portátil SHA-256
  `56C0053985EF6564172CC9AABB8C5C68AD2C764CB8E62C10F4B649B0BBF01487`,
  smoke `SUCCESS` com 11 checks.
- Captura real: o clique nativo no receptor produz seleção e gizmo em
  `10-material-selection.png`; após a navegação do inspector,
  `11-material-authoring-selected.png` exibe os valores persistidos e os
  controles habilitados. Os hashes e o comando estão em
  `docs/evidence/E08_C_R42_MATERIAL_AUTORIA_CAPTURAS_MANIFESTO.json`.
- Finding corrigido: o harness usava `(650,550)`, ponto fora do receptor na
  superfície DPI-aware 3866×2090 apesar de parecer interno na imagem reduzida;
  o clique foi centralizado em `(1250,700)` e a captura foi repetida com sucesso.
- Limitações preservadas: a captura automatizada não substitui a revisão
  humana final; o normal map é vetor autoral nesta etapa e sombras híbridas 3D
  permanecem posteriores, especialmente E12.

### Evidência do sublote E08-D.1 — partículas

- Commit de integração: `c5ca9f6fb559997ecdfa388a8244da68fb3bbc14`.
- O viewport V2 resolve sockets `type: vfx` persistidos em uma simulação
  `ParticleSimulation` com seed derivada do `effect_id`, fixed timestep,
  lifecycle inicializado e limite explícito de partículas. Os estados são
  desenhados como pixels QGraphics; o socket continua sendo o dado autoral e a
  simulação não é salva como fonte de verdade.
- Testes focados: `46 passed`, incluindo repetibilidade por seed e integração
  do socket com o viewport profissional, além do contrato runtime existente.
- Build r43: source commit `c5ca9f6fb559997ecdfa388a8244da68fb3bbc14`, binário
  SHA-256 `692178B725846275B362B965E76CF03AE8630CFDF4F23A5CA412E36907D69AC1`,
  pacote portátil SHA-256
  `C86275C2521CCB045D4E033881AFE18423A458A13A52C950EAF081DAB467ED44`, smoke
  `SUCCESS` com 11 checks.
- Suíte oficial atual: `2072 passed, 2 skipped, 1 warning`.
- Captura real: `06-renderer-preview.png` e `07-renderer-authoring.png` mostram
  partículas amarelas observáveis no socket `spark-fx`; a captura inferior
  mostra o socket VFX persistido no inspector. Manifesto e hashes:
  `docs/evidence/E08_D1_R43_PARTICULAS_CAPTURAS_MANIFESTO.json`.
- Limitação controlada: o perfil `spark-fx` é um preview determinístico
  associado ao socket; parâmetros avançados autorais, compilação de shader e
  cadeia de pós-processamento permanecem nos sublotes seguintes de E08-D.

### Evidência do sublote E08-D.2 — shaders

- Correção auditada: `6c39412219a62531eda341fc6fea0d84371a37eb`.
- Finding reproduzido: o PATH apontava para o wrapper `pyside6-qsb` do Python
  3.13, sem PySide6, e a compilação falhava antes do Qt Shader Tools. A função
  `resolve_qt_qsb` passou a priorizar o `qsb.exe` instalado no `sys.prefix` do
  interpretador ativo; o teste `test_qt_qsb_prefers_the_active_python_environment`
  protege essa decisão.
- Auditoria real limpa: `python -m scripts.audit_runtime_shaders_phase3`
  passou com `source_tree_clean`, sidecar canônico, `qsb.exe` real, vertex e
  fragment compilados, shader inválido rejeitado e binários anteriores
  preservados. Relatório:
  `artifacts/e08-renderer-20260908/runtime-shader-audit-d2-r44-clean2/stage3-runtime-shaders-report.json`.
- Testes focados: `15 passed`; suíte oficial: `2073 passed, 2 skipped,
  1 warning`.
- Build r44: source commit `6c39412219a62531eda341fc6fea0d84371a37eb`, binário
  SHA-256 `DB7BB062C46F5BB7D092F3DB1A5C486ACDF0D5411B4099ACC303A25580FF034F`,
  pacote portátil SHA-256
  `6A7BC6FD6F48D52738092FF401CB2F1F5E2B6944D90D03E077933AAE4D6E1029`, smoke
  `SUCCESS` com 11 checks.
- A captura real r44 mantém o fallback raster explícito e o socket VFX
  observável; não há claim de shader GPU aplicado sem backend acelerado. O
  manifesto hashado está em
  `docs/evidence/E08_D2_R44_SHADERS_CAPTURAS_MANIFESTO.json`.

### Evidência do sublote E08-D.3 — pós-processamento

- Implementação integrada no commit `b5baf5c7676b85a7319e1280362e4b8d005909a7`.
  Sockets VFX `post-*` resolvem uma cadeia determinística ordenada no runtime
  CPU-preview, com fallback explícito e sem substituir o documento autoral.
- Correção visual aplicada após a primeira captura: o raio inicial deixava o
  efeito praticamente transparente dentro da fixture. O raio foi reduzido e
  recebeu um stop central de baixa opacidade; a revalidação r47 mostrou a
  vinheta radial de forma perceptível, preservando a leitura do objeto e o
  marcador VFX.
- Auditoria oficial: `PASS` em round-trip canônico, vínculo por hash,
  ordenação determinística, efeitos desabilitados, alpha, limites, fallback,
  persistência atômica e privacidade. Relatório:
  `artifacts/e08-renderer-20260908/runtime-post-audit-d3-r47/stage5-runtime-post-processing-report.json`.
- Testes focados: `13 passed`; suíte oficial: `2075 passed, 2 skipped,
  1 warning`.
- Build r47: source commit `b5baf5c7676b85a7319e1280362e4b8d005909a7`, binário
  SHA-256 `414DFE697F2095BA5996EF79D41CA3F8DF83085E5A38265F0B099FCED5FBDC52`,
  pacote portátil SHA-256
  `62c91373def4e3a898bc645d85fae7c1d4b2f6ef68ac6c1414ac6a149dcaf860`, smoke
  `SUCCESS` com 11 checks.
- Captura real do binário portátil com a fixture
  `tests/fixtures/e08_post_smoke.ndtproj`: Preview
  `54BD892508DF62B2C1AD45D8F856E21E88226E7D144A613452261BDB5E22DB6D`,
  Autoria `F7D6BF3E53947B5E1F1F5FD176AC5079A4BD30B85E72692E71748ED0D62BBE30`,
  Parallax inferior `A612AA2D2AABC6CD6D256017E3A2EA422E32203D0AF97ECF529B8CF2D094BF7D`
  e PageUp `9D25D7214BC9C2499E0893FCB0B3A15D79A4CC36E7CBAAB4CF36A7FF8A707D62`.
  Manifesto completo:
  `docs/evidence/E08_D3_R47_POST_PROCESSING_CAPTURAS_MANIFESTO.json`.
- Limitações mantidas: o backend é CPU-preview determinístico, sem claim de
  rasterização GPU; adaptadores de pós para Godot/Unity, VRAM, FPS por driver
  e render específico de backend continuam fora deste sublote.
