# Evidência — Etapa 4: transação global e rollback de múltiplos manifestos

## Identificação

- Commit técnico validado: `807af85`
- Branch de validação: branch de trabalho local do candidato
- Base: `main` em `0d763358`
- Data: 2026-08-17
- Escopo: uma transação única para todos os manifestos de uma operação de sincronização.

## Objetivo e contrato

O planejamento valida todos os manifestos e todos os destinos antes de qualquer escrita. A aplicação ordena os manifestos de forma determinística, reúne as saídas alteradas e usa uma única transação de substituição. Se qualquer manifesto falhar, as saídas novas são removidas e as saídas existentes são restauradas. O contrato não promete recuperação contra perda de energia, corrupção do sistema de arquivos ou encerramento forçado do processo.

Godot passou a executar `import_project` com snapshot do diretório gerado inteiro e restauração global. Unity passou a expor `ImportManifests` e o pós-processador usa esse ponto de entrada para o lote completo. Os adaptadores continuam source-only; nenhum binário, download ou plugin de marketplace foi introduzido.

## Comandos executados

- `python -m pytest -q --cov=src --cov-branch --cov-fail-under=90 --cov-report=xml`
- `python tools/check_coverage_policy.py coverage.xml`
- `python -m mypy src`
- `python -m black --check ...`
- `python -m isort --check-only ...`
- `python -m flake8 ...`
- `python tools/evidence_integrity.py`
- Harness real, com executáveis locais fornecidos pelo operador: `python scripts/audit_native_stage4_global_transaction.py --godot <godot-executable> --unity <unity-executable> --output docs/evidence/artifacts/native-stage4-global-transaction-rerun10-2026-08-17`

## Resultados

- Suíte completa: `1202 passed, 2 skipped, 10 warnings`.
- Cobertura: linhas `90,71%`; branches acima de `85%`; política de cobertura PASS.
- Mypy: `Success: no issues found in 93 source files`.
- Integridade oficial: `48 manifests validated`.
- Godot real `4.7.stable`: retorno `0`; rollback global, importação e repetição determinística PASS.
- Unity real `6000.5.7f1`: retorno `0`; rollback global, importação e repetição determinística PASS.
- Os dois skips são os testes de symlink condicionados à disponibilidade de symlink no Windows; não foram convertidos em aprovação falsa.

## Evidências e hashes

- Evidência aprovada: `docs/evidence/artifacts/native-stage4-global-transaction-rerun10-2026-08-17/`.
- `stage4-global-engine.log`: `66481` bytes; SHA-256 `3c32d0801bfe3966589895e26a7e9e48c8653383fe30f9abc92210676452b6d1`.
- `stage4-global-report.json`: `1299` bytes; SHA-256 `5ab1d51147c017b0c7fabc5b891f74876854d886be3fb803d6ad0519afe56a9d`.
- O índice registra esses bytes e hashes e foi conferido independentemente.
- Falhas intermediárias preservadas e sanitizadas: `rerun7` (critério do fixture contando estado pré-existente), `rerun8` (erro de compilação C# no fixture) e `rerun9` (sidecars `.meta` contados como saída). Nenhuma foi promovida a PASS.

## Privacidade e limitações

Os logs finais não contêm caminhos locais, identificadores de licença, IDs de sessão, IDs de máquina ou IDs de processo não redigidos. A CI atual valida os contratos Python e os artefatos, mas não inicializa dinamicamente Godot/Unity; a validação das engines é local, real, reproduzível e hashada. A garantia é transacional dentro do processo e do sistema de arquivos normal; não cobre falha de energia, corrupção do volume ou interrupção forçada durante a restauração.

## Decisão

APROVADO no escopo da Etapa 4 e pronto para revisão/merge. Esta decisão não aprova a release pública.
