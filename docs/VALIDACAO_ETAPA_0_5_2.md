# Validação da Etapa 0.5.2 — Preservação inicial

## Arquivos adicionados

- 24 snapshots históricos em `quality/legacy_tests/tests/`;
- `quality/legacy_tests/manifest.json`;
- `quality/legacy_tests/pytest.ini`;
- `quality/legacy_tests/.gitattributes` para preservar os bytes dos snapshots;
- `quality/legacy_tests/README.md`;
- `tools/run_legacy_tests.py`;
- `tools/run_legacy_tests.ps1`;
- `docs/ETAPA_0_5_2_RECONCILIACAO_TESTES.md`;
- `docs/ETAPA_0_5_2_MAPEAMENTO_TESTES.csv`.

## Arquivos funcionais alterados

Nenhum.

## Validações executadas

- conteúdo dos 24 testes comparado com o commit de origem;
- SHA-256 normalizado registrado;
- contagem: 24 arquivos e 196 testes;
- integridade verificada pelo executor;
- executor validado com execução isolada do grupo não gráfico;
- 92 testes aprovados, 8 falhas e 13 bloqueados por API;
- suíte oficial atual não foi alterada;
- o `pytest.ini` principal continua coletando apenas `tests/`.

## Limites

- PySide6 não está disponível no ambiente Linux de auditoria;
- os 83 testes Qt ainda precisam ser executados no Windows;
- as regressões identificadas ainda não foram corrigidas;
- nenhum commit, tag ou baseline foi criado.
