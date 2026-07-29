# Validação — Etapa 0.5.2F

## Validações executadas no ambiente de preparação

- compilação sintática de todos os arquivos Python modificados: aprovada;
- 9 testes headless específicos do motor magnético: aprovados;
- 40 contratos não gráficos anteriores: aprovados;
- total executado no conjunto combinado: **49 aprovados, 0 falhas**;
- círculo sintético: erro radial médio inferior a 3 pixels;
- caminho circular: aderência média à borda superior a 0,55;
- baixo contraste: caminho produzido e aderente;
- região extensa com redução: endpoints preservados e execução inferior a 3 segundos;
- simplificação: limite de vértices respeitado;
- auto-interseção: detectada e rejeitada.

O arquivo `quality/magnetic_lasso_0_5_2f_benchmark.json` registra medições do ambiente de preparação. Ele não representa promessa de tempo idêntico no computador do usuário.

## Pendente de validação no Windows

O ambiente de preparação não possui PySide6 utilizável. Portanto, os seguintes itens precisam ser confirmados no Windows:

- 7 contratos Qt em `tests/test_stage_0_5_2f_ui.py`;
- leitura de `QImage` com padding por `bytesPerLine()`;
- menu de opções do botão direito;
- Esc, Backspace, Ctrl+Z e Ctrl+Y;
- atualização visual da prévia;
- mapa de bordas opcional;
- desempenho em imagens reais;
- comparação manual entre Preciso e Legado;
- criação, seleção automática e undo/redo do objeto final.

## Critério de aprovação manual

A etapa só deve ser consolidada depois de o usuário confirmar que:

1. as âncoras são atraídas para o contorno esperado;
2. o caminho não corta o interior em curvas comuns;
3. o cursor e a interface permanecem responsivos;
4. a quantidade de vértices é editável;
5. o modo Legado continua acessível;
6. o rollback para 0.5.2E é reconhecido como válido.
