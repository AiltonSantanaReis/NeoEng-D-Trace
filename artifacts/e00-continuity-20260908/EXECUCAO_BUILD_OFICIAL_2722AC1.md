# E00 — execução da build oficial `2722ac1`

**Classificação:** `PASS_LOCAL / PASS_AUTOMATED_CAPTURE_ONLY / E00_IN_PROGRESS`

- branch: `Ailton/e00-continuity-build-20260908`;
- source commit: `2722ac1cf39b222931ed440a0eb935ee5d1dcc50`;
- plano mestre: `52e9896d2ecf1bc928fb27aca5b8091890c580d7`;
- executável: `release/e00-20260908/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- SHA-256 do executável: `2C5B91A9C5145C69FCAB986FF8D73BD67C0E411995A09BF655565ACF690E32FF`;
- pacote portátil SHA-256: `385731D0F0593BE3F6A1C8D6646DC7A2F1AB2E22F9B827752613F77ED00320BF`;
- CLI: `NeoEng-D-Trace-CLI.exe --version` → `NeoEng-D-Trace-CLI.exe 0.3.0`;
- smoke portátil: `SUCCESS`, 11 verificações;
- fluxo funcional do executável: `SUCCESS`, com abertura em PT, restauração de geometria, salvamento de estado e fechamento; `failure_count=0`;
- log funcional: `official-build-2722ac1/functional-flow-validation.jsonl`;
- manifesto: `release/e00-20260908/continuity-provenance.json`;
- captura normal: `official-build-2722ac1/captures/00-official-normal.png`, `1213x860`, SHA-256 `20B4502F21852A331B743D681340CD1D45CC7FCEB612BA8EA713894060F06FCB`;
- captura maximizada: `official-build-2722ac1/captures/01-official-maximized.png`, `1933x1045`, SHA-256 `FBA8E1EAABBA7B3F16230245B28F3EF735304F88DE612479CBB36DA5CCB53EDD`.

## Achado visual

Na captura maximizada, os rótulos da toolbar `Visualizar`, `Selecionar` e
`Desfazer` aparecem truncados. O achado está limitado a este executável,
estado e resolução. A aba Objetos e a correção de rolagem não foram alteradas
nem reclassificadas nesta execução.

## Limitações

A captura é automatizada por handle Win32. A revisão humana/nativa permanece
`BLOCKED` porque o host de Computer Use não expôs uma janela de aplicação.
Symlink continua reportado separadamente: 31/31 no Sandbox e 2 skips locais.
