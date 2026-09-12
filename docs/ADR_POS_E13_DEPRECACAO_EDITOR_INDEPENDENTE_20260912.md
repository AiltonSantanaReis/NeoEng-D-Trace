# ADR pós-E13 — descontinuação pública do Editor de Cenário Independente

**ID:** `ADR-POS-E13-INDEPENDENT-SCENE-DEPRECATION-20260912`
**Estado:** `DEPRECATED_PUBLIC / IN_PROGRESS_MIGRATION`
**Data:** 2026-09-12
**Decisão:** não manter `IndependentSceneWindow` como editor público paralelo.

## Contexto

O projeto possui uma janela independente para retângulos, elipses, polígonos,
edição de pontos, resolução e câmera simples. O Editor de Cenário profissional
já possui viewport V2, molduras, parallax, hierarquia, biblioteca, timeline,
tilemap, tileset, colisão, navegação, entidades e exportação.

Manter as duas superfícies como editores de cenário cria descoberta duplicada,
modelo mental inconsistente e risco de o usuário iniciar um arquivo que não
possui o contrato de parallax e runtime esperado.

## Decisão

O editor independente deixa de ser uma entrada pública de “cenário”. Suas
capacidades úteis serão reaproveitadas no Editor de Cenário profissional como
ferramentas de:

- blockout de formas;
- primitivas vetoriais;
- edição de contornos;
- criação de colisores e triggers;
- protótipos de layout sem asset;
- conversão de forma em objeto persistente da cena.

O código existente não será apagado nesta etapa. A ação de menu só poderá ser
removida depois de uma migração comprovada dos arquivos `.ndtscene` e de uma
execução real de regressão.

## Migração obrigatória

1. Criar no Editor de Cenário uma ferramenta `Formas / Blockout` com as
   primitivas existentes e o mesmo histórico transacional.
2. Ao abrir um `.ndtscene` antigo, oferecer `Abrir somente leitura` e
   `Converter para cenário profissional`; nunca sobrescrever silenciosamente o
   arquivo original.
3. Preservar resolução, câmera, primitivas, pontos, nomes e transformações.
4. Exportar a conversão para o schema profissional V2 com manifesto de origem.
5. Executar testes unitários, contrato, integração, persistência, erro e fluxo
   nativo com captura antes de retirar a ação pública.
6. Marcar o componente antigo como `DEPRECATED` somente depois do gate acima;
   mantê-lo em compatibilidade de leitura enquanto existirem arquivos válidos.

## Critérios de aceite

- nenhum `.ndtscene` válido perde informação;
- a ferramenta profissional cria primitivas sem imagem importada;
- undo/redo, salvar/reabrir e exportação permanecem funcionais;
- a ação antiga deixa de aparecer no fluxo principal somente após evidência;
- a suíte oficial permanece sem filtros e a build nativa comprova a conversão;
- falhas e arquivos históricos continuam preservados.

## Alternativa rejeitada

Apagar imediatamente a janela e seus modelos não é aceitável: isso removeria
uma capacidade de autoria de formas e poderia quebrar arquivos independentes
existentes. A substituição gradual é a opção de menor risco.
