# E08 — Composição 2.5D, iluminação, sombras e FX reais

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E08_CONTRATO_RENDERER_25D_FX_2026-09-08.md`.
Dependência técnica: E07 checkpoint `d35bc84`.

## Estado dos lotes

- E08-A — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: plano de composição e fronteira de backend.
- E08-B — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: câmera e paralaxe profissional.
- E08-C — `IN_PROGRESS`: C1–C4 têm checkpoint técnico comprovado; E08-C
  permanece aberto somente para auditoria final antes da promoção formal.
- E08-D — `IN_PROGRESS`: D1 partículas em checkpoint técnico; D2 shaders e
  D3 pós-processamento ainda ativos.
- E08-E — `PLANNED`: determinismo temporal e matriz de destino.

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
