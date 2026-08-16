# Estabilização de transações e documentação

Data: 2026-08-16
Estado: evidência local final antes do commit; o SHA do commit funcional será vinculado após o versionamento.

## Decisão

A transação conjunta do atlas não foi reimplementada: ela já existia e foi
revalidada pelos testes de falha no segundo arquivo, restauração de destinos
anteriores, remoção de destinos novos e falha na preparação de backup.

A lacuna real estava na CLI com múltiplas saídas. Foi implementado staging no
mesmo diretório, commit agrupado, restauração do conjunto anterior quando o
commit falha, remoção de novos parciais e rejeição de destinos duplicados.

A garantia é transacional durante a execução normal do processo. Não é uma
garantia contra perda de energia, corrupção externa do filesystem ou
interrupção não controlada durante uma substituição.

## Evidências funcionais

- tests/test_atomic_outputs.py: sucesso, rollback de destinos existentes,
  remoção de destinos novos, duplicidade, falha de backup e falha de rollback.
- tests/test_atomic_export_replacement.py: regressão dos exportadores atômicos
  existentes.
- tests/test_stage_7_cli_contract.py: regressão do contrato CLI e saídas reais.
- docs/CONTRATO_CLI.md: contrato vigente atualizado.
- docs/MATRIZ_FUNCIONALIDADES_ATUAL.md: matriz vigente atualizada.
- docs/evidence/ADENDO_ESTABILIZACAO_CONTRATOS_2026-08-16.md: ponte explícita
  entre documentação vigente e registros históricos congelados.

## Resultados

- Suíte completa: 1080 passed, 10 warnings.
- Cobertura oficial: linhas >= 90%, branches >= 85% e módulos mensuráveis >= 30%.
- Testes específicos de transação: 10 passed.
- Baseline: 598 arquivos verificados.
- flake8, Black, isort, mypy e compileall: aprovados.
- Bandit: aprovado.
- pip-audit: nenhuma vulnerabilidade conhecida encontrada; o pacote local não
  publicado não pôde ser consultado no índice externo.
- Higiene de referências e caminhos locais: aprovada.
- A saída completa da suíte está em
  docs/evidence/artifacts/transaction-stabilization/full-test-results.txt.

## Regra histórica

Relatórios anteriores não foram reescritos. Quando continham uma limitação
válida no momento da auditoria, continuam preservados como evidência daquele
estado. A documentação vigente foi atualizada e este relatório registra a
transição.
