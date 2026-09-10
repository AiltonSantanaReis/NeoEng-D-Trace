# PACK-01 / PACK-03 — Piloto Floresta e catálogo

**Estado:** `PENDING_EVIDENCE`
**Data:** 2026-09-10
**Base:** pós-E13, branch `Ailton/e08-renderer-20260908`
**Escopo:** primeiro incremento adicional; não reabre nem altera E13.

## Rastreamento

- Requisito: catálogo local de conteúdo próprio e importação controlada.
- Features: `PACK-01` (proveniência do piloto), `PACK-03` (catálogo), `PACK-04` (importação).
- Implementação: `src/core/asset_packs.py`, `src/ui/asset_pack_dialog.py`, integração em `src/ui/scene_asset_panel.py`.
- Conteúdo: `assets/scene/packs/floresta/manifest.json` e seis PNGs RGBA.
- Testes focados: `tests/test_asset_packs.py` — 10 aprovados.
- Suíte oficial: 2.165 aprovados, 2 ignorados, 1 warning de depreciação; log em `artifacts/pack-pilot-pytest-20260910-rerun.log`.

## Critérios observados

- `PASS` no contrato de manifesto, caminhos contidos, dimensões declaradas e hashes SHA-256.
- `PASS` na busca sem acento, carregamento de miniaturas, seleção e prévia Qt.
- `PASS` na importação repetida sem duplicação, cópia para o projeto, posicionamento, undo/redo e reabertura portátil.
- `PASS` na rejeição de asset adulterado sem mutação do projeto.
- `PASS` na disponibilidade do catálogo sem projeto salvo e bloqueio da importação nesse estado.
- `PENDING_EVIDENCE` para cliques reais no binário, persistência após execução do binário, captura em DPI real, desempenho de catálogo grande e revisão artística.

## Limitações preservadas

Os seis objetos são um piloto visual assistido por IA para avaliação interna. O
acabamento de bordas/halos ainda precisa de revisão humana, especialmente no
tronco. A árvore gerada com fundo quadriculado foi rejeitada e não entrou no
catálogo. Ainda não foram incluídos os planos de parallax, terreno/tileset, cena
exemplo, instalador de pacotes ou as coleções Ruínas e Cidade futurista.

## Próxima prova obrigatória

Após o commit deste incremento, construir uma nova distribuição limpa, executar o
binário e capturar cada ação real: abrir Biblioteca, abrir Pacotes NeoEng, buscar,
selecionar, adicionar, voltar, arrastar para uma moldura, desfazer/refazer, salvar,
fechar e reabrir. A captura deve ser observada passo a passo; existência de código
ou de uma tela não será usada como substituto dessa prova.
