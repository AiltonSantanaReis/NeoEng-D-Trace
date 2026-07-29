# Etapa 0.5.2F — Laço Magnético Funcional

## Objetivo

Substituir o comportamento instável percebido no laço magnético por um modo preciso, preservando o algoritmo anterior como opção Legado e mantendo retorno integral para a 0.5.2E.

## Modos disponíveis

### Preciso — padrão da interface

A ferramenta selecionada pela paleta usa, por padrão:

- detecção combinada de gradiente Sobel e bordas Canny;
- atração da âncora para a borda próxima;
- caminho Live Wire orientado pela força e direção do gradiente;
- penalidade para mudanças bruscas de direção;
- região de busca adaptativa;
- redução controlada da região em segmentos muito extensos;
- refinamento do caminho reduzido sobre a borda original;
- limitação de frequência da pré-visualização;
- simplificação do contorno antes da criação;
- rejeição de auto-interseções;
- limite configurável de vértices.

### Legado — preservado

Mantém o `dijkstra_pathfinding()` histórico, incluindo o corredor de 20 pixels e o custo baseado na intensidade Sobel. A construção direta de `MagneticLassoTool(canvas)` continua usando Legado para preservar integrações antigas. A paleta oficial passa um objeto de configuração compartilhado cujo padrão é Preciso.

## Interação

- clique esquerdo: fixa uma âncora atraída para a borda no modo Preciso;
- movimento: mostra o caminho até a próxima âncora;
- clique na primeira âncora: conclui quando há pelo menos três âncoras;
- duplo clique ou Enter: conclui a seleção;
- Backspace ou Delete: remove a última âncora;
- Ctrl+Z durante o desenho: remove a última âncora, sem desfazer o projeto;
- Ctrl+Y/Ctrl+Shift+Z durante o desenho: restaura a última âncora removida;
- Esc: cancela integralmente a seleção em andamento;
- botão direito: concluir, remover âncora, cancelar, escolher modo, escolher preset e mostrar mapa de bordas.

## Presets

- **Rápido:** região e custo reduzidos, maior simplificação;
- **Equilibrado:** padrão recomendado;
- **Preciso:** raio de atração e região maiores, maior preservação de detalhes.

A mudança de modo ou preset cancela uma seleção em andamento para impedir que um único polígono misture caminhos calculados por parâmetros incompatíveis.

## Conclusão segura

O estado só é apagado depois que o modelo confirma a criação do objeto. Caso o fechamento, a validação geométrica ou o comando falhe, as âncoras permanecem disponíveis para correção ou cancelamento.

## Compatibilidade

Não foram alterados:

- formato dos projetos;
- exportadores PNG, atlas, metadados ou GLTF;
- seleção automática do objeto criado;
- detecção automática;
- física e decomposição convexa;
- dados persistidos.
