# E04 — Tilemaps, grids e regras de terreno

Status: `IN_PROGRESS`.

Dependência confirmada: E03 técnico selado no commit `464f7c9`. O contrato
vigente está em `docs/DECISAO_E04_CONTRATO_TILEMAP_GRID_2026-09-08.md`, derivado
da seção 11 do Plano Mestre e da matriz de dependências E00.

## Metas rastreáveis

- E04-A: separar TileSet, células, camadas, IDs, atlas, pivô, variantes,
  animações, propriedades, chunks e limites;
- E04-B: implementar paleta, seleção, pincel interpolado, balde limitado,
  borracha, retângulo, copiar/colar e variação determinística como transações;
- E04-C: implementar e testar ortogonal, isométrico e hexagonal com conversões
  reversíveis, picking, vizinhança, bordas e coordenadas negativas;
- E04-D: implementar Rule Tiles determinísticos, prioridades, fallback e
  invalidação incremental entre vizinhos/chunks;
- E04-E: salvar/reabrir, validar limites, medir chunk size e produzir destino
  representativo sem afirmar capacidade não implementada de engine.

O benchmark de E04-A (`scripts/benchmark_e04_chunks.py`) comparou 16, 32 e 64
em três repetições sobre 4096 células. O menor tempo mediano observado foi
26.1121 ms para chunk 64, com 1 chunk populado; esse é o padrão inicial do
modelo e a decisão permanece mensurável, não presumida.

## Gates deste lote

Ainda não há build E04 nem captura final. O próximo artefato obrigatório é o
contrato/modelo testado do E04-A, seguido de benchmark de chunks. Symlink e
revisão humana permanecem adiados para a auditoria final do plano.
