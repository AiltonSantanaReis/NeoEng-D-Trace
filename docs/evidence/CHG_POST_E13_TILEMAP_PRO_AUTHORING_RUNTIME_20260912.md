# Registro de mudança pós-E13 — autoria profissional e runtime do Tilemap

**ID:** `CHG_POST_E13_TILEMAP_PRO_AUTHORING_RUNTIME_20260912`

**Estado:** `IN_PROGRESS / PENDING_EVIDENCE`

**Data:** 2026-09-12

**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`

**Base de código do checkpoint atual:** `c39a8670cee23e4bdd423429e2eb65d6b1d7c534`

**Base normativa:** [`DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`](DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

**Decisão de revisão humana:** [`DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`](DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md)

## Finding reproduzido

O núcleo já possui `copy_cells`, `paste_cells`, variação determinística e
`TileRuleSet`, mas o painel do Editor de Cenário só oferece pintura, borracha,
retângulo, balde e conta-gotas. As regras não são persistidas no tilemap e o
manifesto não preserva uma referência segura ao atlas de origem. O pacote de
composição copia o documento do tilemap, porém os adaptadores externos atuais
não materializam suas células no runtime.

Isso deixa uma diferença verificável entre capacidade de domínio e fluxo real
do usuário; não será tratado como concluído apenas porque as classes existem.

## Escopo controlado

1. Expor seleção, cópia/colagem, variação determinística e aplicação de Rule
   Tiles na UI, com operações transacionais, mensagens PT-BR/EN e falhas
   fail-closed.
2. Persistir extensões opcionais compatíveis no documento v1: referência
   relativa segura do atlas, regras e metadados de autoria. Leitores antigos
   continuarão aceitando arquivos sem esses campos.
3. Emitir um payload de runtime de Tilemap com hashes, células, camadas,
   atlas e regras, rejeitando caminhos absolutos, células inválidas e drift de
   assets.
4. Materializar o payload em Godot e Unity em fluxos headless reais, com
   relatório, contagem de células, camadas, atlas e caso negativo de hash.

## Contratos preservados

- E13 permanece fechado e não será reaberto.
- O formato existente `neoeng-d-trace-tilemap` continua legível; campos
  opcionais ausentes conservam o comportamento anterior.
- `TileEditTransaction` continua sendo a unidade de Undo/Redo.
- Nenhum asset, cena ou pacote legado será removido.
- Exportações atuais de cena, composição, partículas, iluminação e híbrido não
  serão substituídas silenciosamente.
- Runtime externo só poderá ser marcado `PASS` após execução no engine real;
  teste de contrato Python não substituirá essa prova.

## Módulos e riscos

- `src/core/tilemap_model.py`, `tilemap_tools.py` e `tilemap_rules.py`:
  seleção, variação, regras e invariantes.
- `src/persistence/tilemap_io.py` e `src/ui/tilemap_authoring_panel.py`:
  compatibilidade, histórico, localização e fluxo visual.
- `src/exporters/` e `integrations/`:
  payload externo, materialização, hashes e falhas de drift.
- Riscos: duplicar células durante uma seleção, aplicar regra ambígua,
  perder dados ao reabrir arquivo antigo, aceitar caminho fora do projeto ou
  declarar runtime por metadata sem renderização/contagem observável.

## Critério de saída desta mudança

O estado só poderá avançar para checkpoint técnico quando houver teste
unitário/contrato, UI com gesto real, persistência, teste negativo, build limpa,
fluxo nativo com capturas reais e runtime externo executado. Até lá, este
registro permanece `IN_PROGRESS / PENDING_EVIDENCE`; a revisão humana final
continua formalmente deferida.

## Checkpoint de implementação, build e fluxo nativo

O núcleo e a UI do authoring profissional foram implementados no commit
`2c87d21` e a correção responsiva de dock estreito foi concluída no commit
`b9341c9`, sem remover o fluxo anterior. Seleção por gesto, cópia/colagem
transacional, variação determinística, Rule Tiles persistíveis, validação
fail-closed, referência/hash do atlas e o layout responsivo foram cobertos por
62 testes focados, todos aprovados. A suíte oficial sem filtros passou com
`2216 passed, 2 skipped, 1 warning`.

A build limpa e dois fluxos nativos reais foram concluídos e documentados em
[`EVD_POST_E13_TILEMAP_PRO_RESPONSIVE_NATIVE_20260911.md`](EVD_POST_E13_TILEMAP_PRO_RESPONSIVE_NATIVE_20260911.md):
Tilemap com seleção/cópia/colagem/variação/Rule Tiles/salvar/reabrir e Tileset
com atlas real/gerar/salvar/novo/reabrir. Esse checkpoint histórico permanece
preservado como `PENDING_EVIDENCE` porque ainda não incluía runtime externo.

## Checkpoint de runtime externo — PASS técnico

O commit `c39a867` implementou o payload versionado
`neoeng-d-trace-tilemap-runtime`, com bindings seguros/hashados do tilemap e do
atlas, células, camadas, variantes, regras e contagens. Os adaptadores
Godot/Unity materializam as células com `Sprite2D`/`SpriteRenderer` reais e
rejeitam drift físico do atlas antes da criação da cena.

A evidência [`EVD_POST_E13_TILEMAP_RUNTIME_ENGINES_20260912.md`](EVD_POST_E13_TILEMAP_RUNTIME_ENGINES_20260912.md)
registra **69 testes focados**, suíte oficial final **2223 passed, 2 skipped,
1 warning**, build limpa `c39a867`, smoke portátil `SUCCESS` com 11 checks,
fluxo Win32 do binário novo e auditoria real nos dois engines. O caso positivo
materializou 27/27 células em cada engine; o caso negativo rejeitou o atlas
alterado por hash/tamanho. O gate específico de runtime está `PASS`.

O estado deste registro, porém, permanece `IN_PROGRESS / PENDING_EVIDENCE`:
integração automática do payload ao exportador geral de composição, runtime
externo do editor híbrido 3D e revisão humana final continuam linhas abertas
do lote pós-E13. Nenhuma dessas pendências foi ocultada ou reclassificada.
