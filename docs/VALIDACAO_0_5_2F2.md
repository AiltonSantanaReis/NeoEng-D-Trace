# Validação da correção 0.5.2F2

## Validação no ambiente de preparação

- compilação sintática dos arquivos alterados: aprovada;
- 12 testes do motor do laço magnético: aprovados;
- 31 contratos não gráficos da etapa e regressões anteriores: aprovados;
- 3 módulos Qt ignorados pela ausência de PySide6 no ambiente Linux;
- integridade do pacote e dos payloads: validada por SHA-256;
- aplicação e rollback: simulados byte a byte.

## Validação obrigatória no Windows

Executar:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
    .\tests\test_magnetic_lasso_engine.py `
    .\tests\test_stage_0_5_2f_ui.py
```

Resultado esperado: `23 passed`.

Depois abrir `app.py`, importar a mesma imagem que revelou a falha e confirmar:

1. primeiro clique cria a âncora;
2. mover o mouse mostra a pré-visualização magnética;
3. novos cliques adicionam segmentos;
4. Enter, duplo clique ou clique na primeira âncora conclui;
5. o terminal não repete `convertToFormat` para `numpy.ndarray`.
