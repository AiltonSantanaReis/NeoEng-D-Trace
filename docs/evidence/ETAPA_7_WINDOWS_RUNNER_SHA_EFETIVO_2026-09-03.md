# Evidência — Etapa 7 — runner Windows no SHA efetivo

**Status local:** `PASS_LOCAL`
**Integração:** `BLOCKED_REMOTE`
**Data:** 2026-09-03
**Commit-fonte testado:** `33abb5955f41f89f18f2a5fbe42d2ffc36274099`
**Branch:** `fix/legacy-27-functional-regressions`

## Objetivo e decisão

Esta evidência registra a repetição dos gates na revisão efetiva que contém a
implementação do runner Windows e a documentação anterior. A execução foi feita
em worktree limpo, com dependências sincronizadas pelo lock. O commit-fonte é
anterior a este registro documental; o resumo hashado aponta todos os resultados
da execução exata.

Decisão: os gates locais foram comprovados e a candidata está apta somente ao
push técnico controlado previsto na seção 10.1 do plano. O CI remoto ainda não
foi executado; merge, tag, release e aprovação global permanecem bloqueados.

## Ambiente e comandos

- Windows `win32`, build `10.0.26200`, Python `3.11.9`;
- Poetry `2.4.1`, pytest `9.1.1`, pytest-cov `7.1.0`, PyInstaller `6.22.0`;
- `QT_QPA_PLATFORM=offscreen`, ambiente criado e sincronizado pelo Poetry;
- os comandos exatos e hashes dos artefatos estão em
  `docs/evidence/artifacts/windows-runner-effective-sha-2026-09-03/final-execution-summary.json`.

## Runner/CI e cobertura

O comportamento aprovado para Windows é o runner versionado
`tools/run_windows_coverage_shards.py`: cada arquivo top-level
`tests/test_*.py` é executado em subprocesso próprio, em ordem determinística,
sem `-k`, `--ignore` ou outra redução de escopo, com JUnit por shard, cobertura
acumulada, timeout e falha fechada. O workflow Windows chama esse runner; o
workflow Linux continua usando o pytest de processo único definido no CI.

Na execução do SHA efetivo:

| Arquivos | Testes | Falhas | Erros | Skips | Resultado |
|---:|---:|---:|---:|---:|---|
| 189/189 | 1918 | 0 | 0 | 2 | `ACCEPTED` |

A política de cobertura passou com `23887/25798` linhas (`92,59%`) e
`6664/7838` branches (`85,02%`). Os dois skips foram exclusivamente os testes
condicionais de symlink, por indisponibilidade do privilégio no host atual.

## Reconciliação e snapshots legados

O gate formal aceitou o contrato atual sem alterar o histórico:

- runner histórico bruto: `196` testes, `26` falhas, `0` erros, `0` skips,
  retorno `1`;
- `15` assinaturas históricas exatas;
- `11` assinaturas divergentes formalmente resolvidas/classificadas;
- `12` ausências históricas preservadas na reconciliação;
- `42` substitutos reais: `0` falhas, `0` erros e `0` skips;
- `quality/legacy_tests/manifest.json` e
  `quality/legacy_tests/reconciliation.json` permaneceram byte a byte
  inalterados.

Os hashes canônicos dos snapshots são, respectivamente,
`061e5981084e962f71f6357e765a0fe66defda5af521c9b7e22ae1e2bbf9833a` e
`34a186435d35936fc340ed2935bb6cb69756e13323f5c89fb82f9a632c733587`.

## Demais gates

- lock, compileall, Flake8, Black, isort, mypy, Bandit e pip-audit: `PASS`;
- pip-audit não encontrou vulnerabilidades conhecidas; o pacote local não
  publicado no PyPI foi explicitamente não auditável;
- Stage 4B.5: `PASS`, determinismo e entrada inalterada;
- baseline Git-blob: `PASS`, `3199 files`;
- evidence integrity: `PASS`, `126 manifests`;
- empacotamento: `SUCCESS`, `11` smoke checks, `314` arquivos;
- ZIP portátil: `124181835` bytes, SHA-256
  `c51855fd60841048b7464d43034229789210dc36c96e060c64ccf7fe42271099`;
- manifesto do pacote: `55754` bytes, SHA-256
  `ab3962cdbb5f9f1528c910059c25fb44420e629f1ff9d4dab66492756bf674b9`.

Após a inclusão desta evidência e dos documentos vivos no índice Git, a
verificação staged final também passou: baseline com `3202` arquivos e
evidence integrity com `127` manifestos. Esses números incluem os
próprios arquivos deste registro; os números da execução do SHA estão acima.

## Symlink e limitações

No checkout efetivo, o comando
`poetry run pytest tests\\test_integration_sync.py -k symlink -q -rs`
terminou com `2 skipped, 29 deselected`, ambos por `WinError 1314`. A evidência
VMware anterior continua registrada como `PASS_SCOPED` para a reconstrução
identificada de ZIP/patch no Windows 11 com Developer Mode: `2 passed`, `0`
skips. Ela não é promovida a prova do SHA efetivo.

O CI remoto não foi executado porque o SHA efetivo ainda não foi publicado. Os
logs brutos, JUnit, XML de cobertura, gate formal e Stage 4B.5 permanecem fora
da árvore; seus tamanhos e hashes estão no resumo hashado e a limitação é
declarada explicitamente.

## Decisão formal

`PASS_LOCAL / BLOCKED_REMOTE`: a candidata passou nos gates locais exigidos,
resolveu formalmente as `11` divergências e `12` ausências sem reescrever os
snapshots e está apta ao push técnico controlado. Merge, tag, release e qualquer
declaração global de `APROVADO`, `CONCLUÍDO`, `INTEGRADO` ou `PRONTO` continuam
proibidos até a validação remota e o fechamento dos critérios restantes.
