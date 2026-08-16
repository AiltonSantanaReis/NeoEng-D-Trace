# Adendo de estabilização de contratos

Data: 2026-08-16

Este adendo atualiza a leitura do estado pós-merge sem reescrever evidências
históricas. Relatórios anteriores continuam válidos como registros do estado
que auditaram e não devem ser usados como descrição automática do estado atual.

## Atlas

A transação conjunta de PNG e JSON já estava integrada antes desta etapa. O
código prepara os dois arquivos, preserva destinos anteriores, restaura o
primeiro arquivo quando o segundo commit falha e remove temporários. Os casos
de falha do segundo arquivo e falha na preparação do backup possuem testes
reais em tests/test_stage_10_engine_profiles.py.

Limite preservado: isso cobre falhas durante a execução normal do processo,
não crash-consistency contra perda de energia ou corrupção externa do
filesystem.

## CLI com múltiplas saídas

A CLI agora prepara cada saída em arquivo temporário no mesmo diretório,
executa todas as operações e publica o conjunto somente no commit final. Uma
falha durante esse commit restaura todos os destinos anteriores ou remove
todos os destinos novos parciais. Destinos duplicados são rejeitados antes da
publicação.

O contrato deliberadamente não promete transação após perda de energia,
corrupção do filesystem ou interrupção externa não controlada pelo processo.

## Documentação vigente e histórica

docs/CONTRATO_CLI.md e docs/MATRIZ_FUNCIONALIDADES_ATUAL.md foram atualizados
como documentos vigentes. Os relatórios de auditoria e evidência com datas
anteriores permanecem congelados; este adendo é a ponte explícita entre
aqueles registros e o estado atual.

## Evidência

Os testes específicos estão em tests/test_atomic_outputs.py, além da suíte
existente de substituição atômica e do contrato CLI. A aprovação final depende
da suíte completa, cobertura, baseline, higiene de referências e checks Linux
e Windows do PR correspondente.
