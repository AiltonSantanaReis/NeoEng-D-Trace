# Evidência — correção cross-platform do gate formal legado

**Data:** 03/09/2026 (America/Sao_Paulo)
**Branch:** `fix/legacy-27-functional-regressions`
**Commits avaliados:** `78e47d75a17775f8f38ceddb2551ed570cc0cf2f`,
`42dcb63d032d9e973664850222241ae9e9666bb5`
**PR:** `#166` — sem merge
**Estado:** `PASS_LOCAL / BLOCKED_REMOTE_RERUN`

## 1. Objetivo e escopo

Registrar a análise da primeira execução remota da PR e a correção mínima
necessária para que o gate formal do runner legado produza o mesmo resultado em
Linux e Windows, sem alterar os snapshots históricos, os thresholds ou o
contrato formal dos 27 casos.

## 2. Falha remota preservada

No run `33758279765`, o job Linux `100657937566` falhou em três testes de
`tests/test_formal_legacy_gate.py`; o job Windows `100657937266` passou. O Linux
registrou `1915 passed`, `3 failed` e `1 warning`. A mensagem comum foi
`Formal decisions source reconciliation hash does not match`.

A causa raiz foi a comparação direta dos bytes de
`quality/legacy_tests/reconciliation.json` com o campo histórico bruto. O
checkout Linux contém LF (`34a186435d35936fc340ed2935bb6cb69756e13323f5c89fb82f9a632c733587`),
enquanto a decisão histórica preserva o digest CRLF bruto
(`296ca97f07341eedd99ef8aae57d7053fe6110bdddbc01a55b872d3bf20fb493`). No
Windows, `core.autocrlf` fez os bytes coincidirem. Portanto, a divergência era
do mecanismo de verificação, não de produto ou fixture.

O snapshot anterior permanece disponível no run remoto e neste registro; a
falha não foi apagada nem reclassificada.

## 3. Decisão de engenharia e implementação

Foi preservado o campo `historical_reconciliation_sha256` bruto. O registro
formal recebeu `historical_reconciliation_sha256_lf`, calculado sobre conteúdo
canônico LF. `tools/run_formal_legacy_gate.py` passou a usar
`_canonical_sha256(reconciliation_path)`, e o teste
`test_canonical_hash_is_independent_of_text_line_endings` protege a regra para
arquivos equivalentes em LF e CRLF.

Nenhum snapshot legado foi reescrito. A mudança semântica está em
`78e47d75a17775f8f38ceddb2551ed570cc0cf2f`; a formatação Black está em
`42dcb63d032d9e973664850222241ae9e9666bb5`.

## 4. Gates locais no SHA corrigido

- suíte completa: `1917 passed, 2 skipped`, `1 warning`; cobertura de linhas
  `23887/25798 = 92,59%` e branches `6664/7838 = 85,02%`;
- gate formal: `ACCEPTED`, histórico `196/26/0/0`, retorno `1`, `15` casos
  exatos, `11` divergências, `12` ausências e `42` substitutos aprovados;
- runner Windows: `189/189` arquivos, `1919` testes, `0` falhas, `0` erros,
  `2` skips;
- lock, compileall, Flake8, Black, isort, mypy, pip-audit e Bandit: `PASS`;
- Stage 4B.5: `PASS`, determinístico, entrada inalterada;
- empacotamento: `SUCCESS`, `11` smoke checks e `314` arquivos;
- integridade de evidências: `PASS`, `128` manifestos validados;
- baseline Git-blob: `PASS`, `3206` arquivos verificados.

## 5. Entradas e artefatos hashados

O resumo reprodutível está em
`artifacts/etapa7-cross-platform-formal-hash-2026-09-03/final-execution-summary.json`.
A análise remota está em
`artifacts/etapa7-cross-platform-formal-hash-2026-09-03/remote-ci-initial-failure.json`.
Os hashes dos artefatos externos, do runner, do relatório formal, do Stage 4B.5
e do pacote portátil estão no resumo.

O pacote portátil desta execução possui `124181836` bytes e SHA-256
`8deb27102ffec728e153c0595f2d66bc654e1b608a95ddac5c9a4ed6fd176c8a`; o
manifest de release possui `55754` bytes e SHA-256
`f073d1bcbb87a88145797a45e2fe6e14fd47cb93213cfbd3da1e71032e6d653d`.

## 6. Limitações e decisão

A prova de symlink no Windows 11/VMware é uma evidência scoped ao ZIP/patch
reconstruído (`2 passed`, sem skips naquela reconstrução), não uma prova do SHA
`42dcb63`. No host local, o teste de criação permanece condicionado por
`WinError 1314`; isso não foi ocultado.

Decisão: `PASS_LOCAL / BLOCKED_REMOTE_RERUN`. O push técnico é permitido somente
após a conclusão da integridade final deste pacote, agora comprovada. Merge, tag, release e
aprovação global permanecem bloqueados até os dois jobs remotos do SHA corrigido
passarem e a revisão humana autorizar o próximo passo.

Rollback: reverter `42dcb63` e `78e47d7`, preservando o snapshot anterior e este
registro de falha como histórico.
