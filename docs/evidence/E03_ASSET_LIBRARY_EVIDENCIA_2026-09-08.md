# E03 — Biblioteca e lifecycle de assets

Status do lote: `TECHNICAL_CHECKPOINT_PASS_FINAL_AUDIT_PENDING`.

Este lote foi executado no worktree declarado pela governança, na branch
`Ailton/e03-assets-20260908`. O checkpoint técnico não encerra a auditoria do
Plano Mestre: symlink e revisão humana continuam exclusivamente na auditoria
final.

## Escopo entregue

- biblioteca própria com importação controlada e resolução por conteúdo;
- pesquisa por ID/caminho, filtro Raster/Vetorial e miniatura para assets prontos;
- drag-and-drop interno com MIME explícito, reutilizando o registro existente e
  sem duplicar conteúdo;
- estados `READY`, `MISSING`, `MODIFIED`, `INVALID` e `UNAVAILABLE` com
  diagnóstico visível;
- relink, replace, atualização e fluxo transacional cobertos por testes;
- limites de caminho, hash, colisão de nome, conteúdo duplicado e falhas de
  disponibilidade preservados pelo backend existente;
- interface do editor profissional validada em português no binário oficial.

## Evidência automatizada e funcional

- Testes focados: `14 passed` em `tests/test_p2d_01_assets.py` e
  `tests/test_p2d_01b_asset_lifecycle.py`.
- Auditoria offscreen atual: `PASS`, `finding_count: 0`, em
  `artifacts/e03-assets-20260908/offscreen-audit-r13`.
- Suíte oficial após o commit de fechamento técnico: `1995 passed, 2 skipped,
  1 warning` em `58.24s`.
- Gates estáticos: mypy sem problemas em 154 arquivos; Black (377 arquivos),
  isort, Flake8, compileall, parser PowerShell e `git diff --check` aprovados.

## Build e proveniência

- Commit-fonte: `6899d20a20cc6efe343e575744754c3d8b2f632b`.
- Plano Mestre: `52e9896d2ecf1bc928fb27aca5b8091890c580d7`.
- Build oficial: `release/e03-assets-20260908-r13`.
- Binário: `release/e03-assets-20260908-r13/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`.
- SHA-256 do binário: `882EC881E55CF3212DC360AF7F78D2FE58F21660BB3DFCF76EDA9A93D87EACD2`.
- Smoke portátil: `SUCCESS`, 11 verificações.
- Arquivo portátil SHA-256:
  `032CAFB6E743A9B2392FE40610552399090A95F648586E677882ECB7C7A9CB5B`.
- Manifesto de proveniência: `release/e03-assets-20260908-r13/continuity-provenance.json`.

## Captura real do binário

O roteiro `scripts/capture_e03_asset_library_binary.ps1` abriu o executável
r13, abriu o projeto de fixture e acionou o editor pelo fluxo visível da
aplicação. O manifesto está em
`artifacts/e03-assets-20260908/binary-capture-r13/manifest.json`.

Capturas produzidas pelo binário:

- `01-main.png` — SHA-256
  `60A586B1B395DC6204D2E9C89B83FC918634880E790440FEFE2472076A9C8803`;
- `02-project-open-dialog.png` — SHA-256
  `41AEB289238CEFC04D7860E9040F3E746EE03971E9F7D76EA0A9AB8DEE3EC513`;
- `03-main-after-project-load.png` — SHA-256
  `D98F55C9B024200288C08D8E2EF44693A38D2420853A331E616CB9D34CFE6F90`;
- `05-asset-library-ready.png` — SHA-256
  `233559402A0F0AC13CFD6A1C1D5E27D61F0F6A068717BDB72DCDCB8E1D703A2C`.

Observação visual objetiva da captura real: o título `Editor de Cenário —
NeoEng-D-Trace`, os controles `Pesquisar assets por ID ou caminho`, `Todas as
categorias`, `Importar`, `Relink`, `Substituir` e `Atualizar` aparecem sem
clipping; o asset aparece como `READY`, com miniatura, caminho, dimensão e
contagem de uso; `No asset issues detected.` e a hierarquia permanecem legíveis.
A busca/filtro e o MIME de drag-and-drop têm cobertura comportamental focada;
não se promove essa captura automatizada a revisão humana.

## Decisões e limites

O fixture de captura é temporário e está em artefatos ignorados; nenhum asset
externo foi adicionado ao pacote portátil. A proveniência segue o registro
content-addressed do projeto (ID, caminho, hash e origem); não houve alteração
de licença ou redistribuição. Symlink permanece `DEFERRED_UNTIL_FINAL_AUDIT` e
revisão humana permanece `PENDING_EVIDENCE` por autorização do proprietário.
