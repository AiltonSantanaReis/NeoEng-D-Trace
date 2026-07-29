# Etapa 0.5.2E — Reconciliação controlada

## Mudanças funcionais incluídas

1. **Decomposição convexa:** triângulos só podem ser mesclados quando o resultado permanece realmente convexo. O comportamento anterior podia devolver o polígono côncavo original como uma única peça, contrariando o contrato da função.
2. **Laço poligonal:** um duplo clique conclui e limpa o estado somente após criação bem-sucedida; com menos de três vértices, o trabalho em andamento não é apagado.
3. **Zoom defensivo das ferramentas:** caneta e laço magnético usam um valor numérico seguro quando um adaptador, mock ou implementação incompleta não fornece zoom válido.
4. **Simplificação por curvatura:** foi adicionado `min_points` como opção. O padrão permanece `3`, preservando o comportamento 0.5.2D; valores maiores são opt-in.

## Itens deliberadamente não alterados

- Sobel continua retornando `float32`; o teste histórico exigindo `float64` foi classificado como contrato antigo sem benefício demonstrado.
- o teste histórico de alças usa três pontos colineares e permanece uma fixture inválida;
- a rotação de atlas continua ativa; o teste antigo esperava a ausência dessa funcionalidade;
- testes integrados baseados em `Mock` que simulam incorretamente o `CommandManager` não justificaram alteração do produto;
- o teste histórico de decomposição usa um contorno com aresta sobreposta; a correção foi validada com um L válido.

## Política de risco

Toda a entrega possui patch inverso e ZIP com os arquivos originais 0.5.2D. Nenhuma migração de projeto ou mudança de formato foi introduzida.
