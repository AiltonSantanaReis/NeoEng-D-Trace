# E08 — Composição 2.5D, iluminação, sombras e FX reais

Status: `IN_PROGRESS`.

Contrato ativo: `docs/DECISAO_E08_CONTRATO_RENDERER_25D_FX_2026-09-08.md`.
Dependência técnica: E07 checkpoint `d35bc84`.

## Estado dos lotes

- E08-A — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: plano de composição e fronteira de backend.
- E08-B — `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`: câmera e paralaxe profissional.
- E08-C — `IN_PROGRESS`: materiais, normal maps, luzes e sombras; C2/C3 têm
  checkpoint técnico comprovado e C4 permanece ativo.
- E08-D — `PLANNED`: partículas, shaders e pós-processamento.
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
- `E08-C.4` — `IN_PROGRESS`: completar autoria e persistência explícitas de
  material/albedo/normal map no fluxo V2; não promover E08-C enquanto esse
  contrato permanecer apenas determinístico/interno.

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
