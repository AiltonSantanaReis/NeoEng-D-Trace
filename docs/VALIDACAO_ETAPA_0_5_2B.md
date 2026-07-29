# Validação da Etapa 0.5.2B

## Arquivos funcionais alterados

- `src/exporters/json_exporter.py`;
- `src/physics/sat2d.py`;
- `src/ui/mask_viewer.py`.

## Testes adicionados

- `tests/test_regression_core_contracts.py`;
- `tests/test_mask_viewer_compatibility.py`.

## Validações executadas no ambiente de auditoria

- compilação sintática dos arquivos alterados: aprovada;
- 29 testes ativos não gráficos: aprovados;
- 8 novos testes de contrato: aprovados;
- 113 testes históricos não gráficos: 108 aprovados e 5 divergências classificadas;
- 13 testes históricos SAT: aprovados após restauração da API;
- 3 testes históricos de perfis de engine: aprovados após correção do despacho;
- perfis Godot, Unity e Phaser: restaurados;
- API histórica SAT: restaurada;
- código Qt: compilação sintática aprovada.

## Limite explícito

Os novos testes do `MaskViewer` não foram executados no ambiente de auditoria
porque PySide6 não está instalado nele. Eles devem ser executados no
Windows/Python 3.11 antes da consolidação do baseline.

Nenhuma falha histórica baseada apenas em mock foi usada para alterar
comportamento de produção.
