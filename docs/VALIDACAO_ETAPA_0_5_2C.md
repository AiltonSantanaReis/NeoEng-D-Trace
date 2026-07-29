# Validação da Etapa 0.5.2C

## Arquivos modificados ou adicionados

- `src/ui/export_dialog.py`;
- `tests/test_export_dialog_metadata.py`;
- `docs/ETAPA_0_5_2C_INTEGRACAO_UI_EXPORTACAO.md`;
- `docs/VALIDACAO_ETAPA_0_5_2C.md`.

## Contratos protegidos

- os quatro perfis aparecem na interface em ordem estável;
- cada perfil gera a estrutura JSON correspondente;
- a extensão `.json` é adicionada quando omitida;
- a exportação exige um objeto selecionado;
- metadados podem ser exportados sem imagem carregada;
- os botões atuais de PNG, atlas e GLTF permanecem presentes e habilitados
  quando seus módulos estão disponíveis;
- nomes sugeridos para arquivos não contêm separadores de caminho.

## Limites da validação no ambiente de preparação

- sintaxe e testes não gráficos podem ser executados sem PySide6;
- os testes da interface devem ser executados no Windows/Python 3.11 com
  PySide6;
- a inspeção visual final deve confirmar que a nova seção cabe no diálogo e é
  legível com o tema atual.

## Critério de aprovação no Windows

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
    .\tests\test_export_dialog_metadata.py `
    .\tests\test_regression_core_contracts.py
```

Resultado esperado: todos os testes aprovados.
