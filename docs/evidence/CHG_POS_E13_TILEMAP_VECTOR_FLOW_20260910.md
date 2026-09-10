# Registro de mudança pós-E13 — Tilemap PT-BR e seleção vetorial nativa

**ID:** `CHG-P13-TILEMAP-VECTOR-FLOW-20260910`

**Estado:** `IN_PROGRESS`

**Data:** 2026-09-10

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de execução requalificada:** `cf829b7583c4a6a63fb86d8a0cafc5103808f498`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Finding reproduzido

Na captura nativa do fluxo de Tilemap, a edição aparecia como
`Tilemap edit applied`, apesar de o editor estar em PT-BR. A operação era
funcional, mas a mensagem quebrava a continuidade de idioma da jornada.

Na primeira tentativa nativa do fluxo de contorno vetorial, o asset
`vector-source` era exibido na Biblioteca, porém o clique do harness ocorria
acima da linha real do asset. As capturas `09` a `13` permaneceram em
`Selecione um asset raster para começar`; essa tentativa é mantida como
diagnóstico e não é promovida a `PASS`.

## Alteração controlada

- O painel Tilemap agora localiza mensagens de criação, edição, abertura,
  salvamento e falha para PT-BR e inglês, mantendo o nome técnico do arquivo
  persistido (`scenario.tilemap.json`).
- O teste de UI verifica a sequência observável das mensagens nos dois idiomas.
- O harness nativo passa a clicar no centro observado da linha do asset
  vetorial (`client y≈505` na captura nativa `3866x2090`), sem alterar o
  editor, o modelo de contorno ou os assets.

## IDs e impacto

- Requisitos: `REQ-F03-SCENE-PERSISTENCE`, `REQ-F04-SCENE-VIEWPORT`,
  `REQ-F10-UI-ACCESSIBILITY`, `REQ-F02-EVIDENCE-AUTOMATION`.
- Módulos: `MOD-EDITOR-SCENE-VIEWPORT`, `MOD-EDITOR-INSPECTOR`,
  `MOD-TOOLS-EVIDENCE`.
- Features relacionadas: `FEAT-UI-ACCESSIBILITY`,
  `FEAT-QA-EVIDENCE-PACKAGE`.
- Contratos preservados: schema do Tilemap, persistência atômica, seleção e
  contorno vetorial, E13 concluído e todos os objetos/assets existentes.
- Risco principal: uma mensagem localizada divergir do idioma selecionado ou
  o clique nativo voltar a selecionar uma região vazia da Biblioteca.
- Mitigação: teste PT-BR/EN, matriz focada pós-E13, nova build limpa e captura
  do fluxo completo no binário final.

## Verificação executada até esta versão

- `tests/test_e04_tilemap_ui.py` e `tests/test_e04_tilemap_contract.py`:
  `27 passed`.
- Matriz focada pós-E13: `231 passed`.
- Black, isort, Flake8 e compileall nos arquivos alterados: `PASS`.
- Commit de implementação e build final: `cf829b7`, build limpa final10,
  smoke `SUCCESS` em 11 checks.
- A reexecução específica atual registrou `152 passed em 8,74s`; a matriz
  focada mais ampla pós-E13 anterior registrou `231 passed`.

## Requalificação nativa final10

- Tilemap: `artifacts/post-e13-binary-final10-20260910/tilemap/11-tilemap-reopened.png`;
  SHA-256 `8CCFB88526042B14E29F29715BAB78B3BE6272E6EE16BBCE34909D70662AB68E`.
  O painel mostrou `2 células · 1 chunks` depois de novo, pintura, salvar e
  reabrir, com `Edição do tilemap aplicada` em PT-BR.
- Vetor: `artifacts/post-e13-binary-final10-20260910/vector/13-vector-contour-created.png`;
  SHA-256 `2DC75915D02BC390546AF806A9E227E91F308DF6F34D3C18F4F3764FB26CC28E`.
  A sequência nativa selecionou o asset, detectou, editou e criou o objeto.
- A captura intermediária do vetor que clicava acima da linha continua
  preservada como diagnóstico; não foi promovida a sucesso.

## Evidência e limitações obrigatórias

- Evidência anterior do vetor permanece preservada em
  `artifacts/post-e13-binary-final3-20260910/vector/`.
- A evidência final10 foi gerada em
  `artifacts/post-e13-binary-final10-20260910/vector/` e mostra asset
  selecionado, detecção, edição e objeto criado; a persistência do documento
  vetorial continua coberta pelos testes de contrato e pelo fluxo anterior
  preservado.
- O serviço CUA de janelas nativas não está disponível nesta sessão; a
  captura usa o harness Win32 versionado (`SendInput`/`PrintWindow`) sobre o
  executável real. Isso é fallback declarado, não clique CUA disfarçado.
- A suíte oficial sem filtros continua sendo um gate separado; a falha de
  abort no teste legado do magnetic lasso permanece preservada e não é
  reclassificada por esta mudança.

## Critério de promoção

O critério técnico da seleção vetorial e da localização do Tilemap passou na
build final10. O registro permanece `IN_PROGRESS` até o gate oficial sem
abort, revisão humana e atualização/aceite formal do relatório final.
