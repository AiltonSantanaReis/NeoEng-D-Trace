# E04 — Tilemaps, grids e regras de terreno

Status: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

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
em três repetições sobre 4096 células. A qualificação registrada na decisão
E04 observou 26.1121 ms para chunk 64, com 1 chunk populado; uma execução
posterior variou por ruído local e mediu 32 como menor tempo. O modelo mantém
64 como padrão técnico explícito, enquanto o benchmark permanece diagnóstico e
reexecutável, sem transformar uma amostra instável em regra presumida.

## Gates deste lote

- Testes focados E04: `34 passed` incluindo modelo, grids, ferramentas, Rule
  Tiles, persistência e UI Qt.
- Suíte oficial: `2021 passed, 2 skipped, 1 warning`.
- Estática focada: `mypy src` sem erros em 161 arquivos, Black nos arquivos E04,
  isort dos testes E04, compileall e `git diff --check` aprovados.
- Auditor Stage 1 após integração do canvas: `8 passed`; as cores do canvas
  foram classificadas corretamente como semântica de conteúdo, sem rebaixar
  uma falha de chrome.
- Build oficial r14: fonte `cc1ebaa3001f9cf533df8093aac1efec5c81dc10`, binário
  SHA256 `809D7ECD3E0CF0D721898FD99748A276B6328ADFBCB6EE4F905C393B23EB1FD3`,
  archive SHA256 `89ee347d430b699d6f877bd9cc21d4e12dc5aebb43cc205c2f24ae1bf463323b`,
  smoke portátil `SUCCESS` com 11 checks.
- Captura real do binário: manifesto em
  `docs/evidence/E04_R14_CAPTURAS_MANIFESTO.json`; o fluxo abriu o projeto,
  criou o tilemap, pintou 2 células, salvou e reabriu preservando as células.
  As capturas foram inspecionadas quanto a clipping, tradução e usabilidade.

Symlink e revisão humana permanecem adiados para a auditoria final do plano;
captura automatizada não foi promovida a revisão humana.
