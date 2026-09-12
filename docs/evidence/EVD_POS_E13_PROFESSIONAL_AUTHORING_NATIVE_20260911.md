# EVD-POS-E13-PROFESSIONAL-AUTHORING-NATIVE-20260911

**Status:** `PENDING_EVIDENCE`
**Data:** 11/09/2026 (UTC-03)
**Escopo:** comprovação nativa da subetapa de câmera, parallax e timeline autorizada no lote pós-E13 de autoria profissional.

## Autoridade e base

- [Governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [Requisitos do editor de cenários](../REQUISITOS_EDITOR_CENARIOS_COMPLETO_2026-08-30.md)
- [Mudança autorizada do lote](CHG_POS_E13_PROFESSIONAL_AUTHORING_UX_20260911.md)
- [Decisão de revisão humana final](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)
- Commit auditado: `19a16c373094d5b43a6b86cacaa5441f54dde1ae`
- Branch: `Ailton/e08-renderer-20260908`

## Entrada controlada e build

- Executável nativo: `build/post-e13-professional-clean-20260911-ux-camera/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`
- SHA-256 do executável: `65A970AE0E695DF47A7D35ED466585552C6214B73B4EA6F3B779085597E8F378`
- Pacote portátil: `build/post-e13-professional-clean-20260911-ux-camera/NeoEng-D-Trace-0.3.0-win64-portable.zip`
- SHA-256 do pacote: `6F6316D5AA85A43E89FDEB8EAAF1D14677A664623D5E29CF61D3829A0FF2CA37`
- Smoke da build: `PASS` — 11 verificações em `smoke/portable-smoke-report.json`.
- A execução utilizou o binário compilado, não o interpretador Python nem uma simulação de viewport.

## Operações reais observadas

O processo nativo `964` foi iniciado com projeto válido e recebeu eventos Win32 de mouse e teclado. Cada operação foi capturada com `PrintWindow` e registrada em [`actions.jsonl`](../../artifacts/post-e13-native-flow-20260911-camera-timeline/actions.jsonl), incluindo hash SHA-256 por captura.

| Operação | Resultado observável | Estado |
|---|---|---|
| mover a moldura da câmera | moldura e referência espacial mudaram no viewport; status `Câmera reposicionada — alterações não salvas` | `PASS` |
| girar pela alça superior | moldura mudou de orientação; a operação foi consolidada em uma alteração de câmera | `PASS` |
| adicionar clip de câmera | clip apareceu na faixa e o inspetor exibiu início, duração, posição, zoom e rotação | `PASS` |
| arrastar continuamente a timeline sem clip | playhead foi de `000.00` para `015.32 / 30.00 s` | `PASS` |
| arrastar continuamente sobre clip | playhead foi de `015.32` para `018.89 / 30.00 s` e permaneceu sobre o clip | `PASS` |
| salvar, recarregar e abrir o inspetor da câmera | estado reapareceu com moldura, clip e campos PT-BR | `PASS` |

Capturas principais para revisão visual:

- [giro real pela alça](../../artifacts/post-e13-native-flow-20260911-camera-timeline/camera-rotate-handle-real-v2-24053066.png) — SHA-256 `E379EFD65A6A64BC25B31274B88BD8BCCA8214B2EDA3072B056D4AF699E66222`.
- [timeline contínua sobre clip](../../artifacts/post-e13-native-flow-20260911-camera-timeline/timeline-scrub-clip-real-24053066.png) — SHA-256 `AFF2AA8A1936CC2CAE4AA8A5FA4227CA98F751730E65E6ED4DBD7BDE39D60D5E`.
- [inspetor após recarregar](../../artifacts/post-e13-native-flow-20260911-camera-timeline/reload-camera-inspector-persisted-real-24053066.png) — SHA-256 `018BDBBD1DA6F613C117A10040A687205E415AEDA75275B3AA7EEFABADAEA329`.

## Persistência

O salvamento nativo gerou [`persisted-camera-timeline.ndtscene.json`](../../artifacts/post-e13-native-flow-20260911-camera-timeline/persisted-camera-timeline.ndtscene.json), SHA-256 `3BCF915CA6442B57557A32F06DB85D882ACD32E0503B63D386557A6404EB2D17`. A leitura do documento salvo confirmou:

- câmera: `x=90`, `y=45`, `zoom=1`, `rotation=32.584424909267206`;
- sequência: um clip `camera`, início `15.321428571428571`, duração `5.0`, posição inicial `90,45`, posição final `290,45`, rotação inicial/final `32.584424909267206`;
- após `Recarregar`, a captura real exibiu a moldura rotacionada, o clip e o inspetor com `Câmera X 90,0000`, `Câmera Y 45,0000`, `Zoom da Câmera 1,0000` e `Rotação da Câmera 32,5844`.

## Regressão e testes

- Testes focados do lote: `51 passed in 13.77s`.
- Suíte oficial sem filtros: `2179 passed, 2 skipped, 1 warning in 69.96s`.
- Requalificação oficial pós-commit `849ecf2`: `2179 passed, 2 skipped, 1 warning in 88.28s`.
- O warning é a depreciação já existente do construtor `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`; não foi ocultado nem reclassificado.
- O processo nativo foi encerrado por `Alt+F4` no editor e na janela principal; não permaneceu processo `NeoEng-D-Trace` com PID `964`.

## Fallback e falhas preservadas

- A automação CUA/`@oai/sky` não inicializou neste host por erro de infraestrutura (`failed to write kernel assets: path not found`). O fallback aprovado foi o harness Win32 `scripts/audit_native_usability.ps1`, presente no checkout e preservado como arquivo não rastreado preexistente, com SHA-256 `A288D676E446E201E814AC396FEF71793FC2B61C5575B03CCBC8F0E25332E008`, entrada de mouse/janela real e captura `PrintWindow`.
- A tentativa anterior com a fixture de texto inválida permanece preservada em `artifacts/post-e13-native-flow-20260911-professional/` e não foi usada como evidência de sucesso; ela produziu o erro real `invalid project JSON`.

## Pendências que permanecem abertas

- A revisão humana final das capturas ainda não foi executada por decisão explícita do proprietário; ela será realizada depois dos itens abertos listados na decisão vinculada. Este documento não promove o lote inteiro a `PASS`.
- Iluminação direcional com efeito de runtime, orientação editável dos efeitos, partículas completas, tilemap, colisão, NavMesh, exportação/round-trip e editor 3D continuam `OPEN`/`PENDING_EVIDENCE` conforme o lote autorizado.
- Esta evidência comprova a subetapa de autoria de câmera, guias de parallax e scrub contínuo; não comprova maturidade completa 2D/2.5D/3D nem encerra E13.

## Decisão da subetapa

Os critérios técnicos e nativos de câmera, guias de profundidade e timeline foram observados com `PASS` no executável da build identificada. O estado formal do lote permanece `IN_PROGRESS` e este relatório `PENDING_EVIDENCE` até a revisão humana final e os lotes funcionais ainda abertos.
