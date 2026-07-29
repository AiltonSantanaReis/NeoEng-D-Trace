# Validação da Etapa 0.5.2E

## Escopo

A entrega altera seis módulos funcionais e adiciona testes, manifestos e documentação. Nenhum formato de projeto, campo persistido ou exportador existente foi removido.

## Validações executadas no ambiente de preparação

- compilação sintática dos seis módulos e dos testes: aprovada;
- 40 testes ativos não gráficos: aprovados;
- 8 testes específicos da Etapa 0.5.2E: aprovados;
- decomposição de um L válido: área preservada e todas as peças convexas;
- contorno histórico com aresta sobreposta: nenhuma peça degenerada é retornada;
- simplificação com `min_points=8`: piso respeitado;
- comportamento padrão da simplificação: preservado;
- patch de avanço: validado com `git apply --check --whitespace=error`;
- patch de rollback: validado com `git apply --check --whitespace=error`;
- rollback: hashes dos seis arquivos funcionais idênticos ao checkpoint 0.5.2D;
- rollback: arquivos exclusivos da 0.5.2E removidos.

## Testes históricos restantes

A suíte histórica selecionada permanece com cinco divergências intencionais ou inválidas:

1. contorno de decomposição com aresta sobreposta e expectativa exata de cinco peças;
2. Sobel exigindo `float64`, enquanto o contrato atual usa `float32`;
3. atlas esperando que rotação não exista;
4. comando de alça construído sobre polígono colinear inválido;
5. simplificação circular esperando oito pontos sem solicitar o novo piso opcional.

Nenhum desses testes foi apagado ou alterado.

## Limite de validação

Os testes Qt da Etapa 0.5.2E foram preparados, mas precisam ser executados no Windows com PySide6. A etapa só será aprovada funcionalmente após teste manual do laço poligonal, caneta e laço magnético.
