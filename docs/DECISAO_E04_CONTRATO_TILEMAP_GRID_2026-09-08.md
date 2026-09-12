# Decisão E04 — contrato de TileSet, TileMap e grids

**Data:** 2026-09-08  
**Estado:** `ACTIVE_TECHNICAL_CONTRACT`  
**Base:** Plano Mestre `52e9896d2ecf1bc928fb27aca5b8091890c580d7`, seção 11;
Governança de integridade; decisão de dependências E00; E03 técnico selado em
`464f7c9`.

## Escopo autorizado

E04 implementa somente o domínio de tilemap: biblioteca de tiles, mapas
esparsos por chunks, camadas, ferramentas transacionais, transformações dos
grids ortogonal/isométrico/hexagonal, regras de terreno, persistência e um
destino representativo. Não altera colisão de cenário, NavMesh, entidades,
prefabs, renderer externo ou os gates de E00–E03.

## Contrato de dados

- `TileSet` é separado de `TileMap`; o ID estável do tile não depende da
  posição no atlas. Cada tile referencia asset próprio, recorte, pivô, variante,
  animação e propriedades versionadas.
- `TileMap` mantém camadas ordenadas e independentes, com nome, visibilidade,
  lock e opacidade contratada. A célula é identificada por coordenadas inteiras
  assinadas e carrega somente tile ID e metadados mínimos.
- O armazenamento é esparso por chunks. O tamanho será escolhido por benchmark
  entre candidatos explícitos (16, 32 e 64), sem criar um widget Qt por célula.
  No benchmark Windows do E04-A, com 3 repetições e 4096 células, o resultado
  foi 16→27.7265 ms/16 chunks, 32→26.5834 ms/4 chunks e 64→26.1121 ms/1
  chunk; o padrão técnico selecionado é 64, sujeito a requalificação se o
  perfil de edição real mostrar outra necessidade. Nenhuma operação pode
  preencher um vazio ilimitado.
- Todas as mutações geram deltas de células e regras afetadas dentro de uma
  transação; Undo/Redo não copia o mapa inteiro por pincelada.

## Contrato espacial

- Ortogonal: coordenadas `(x, y)` assinadas, origem explícita e célula retangular.
- Isométrico: projeção ortográfica com base `(cell_width/2, cell_height/2)`;
  picking usa a inversa da mesma base e desempate determinístico em bordas.
- Hexagonal: coordenadas axiais `(q, r)`, orientação pointy-top explícita,
  conversão por coordenadas cúbicas e arredondamento determinístico.
- Cada grid expõe célula→mundo e mundo→célula, vizinhança, limites e origem;
  zoom/DPI não alteram o contrato lógico.

## Regras de terreno

Regras são neutras ao destino e declaram vizinhos, prioridade, rotações,
espelhamento, pesos e fallback. Ambiguidade e ciclo são rejeitados antes da
escrita. A resolução usa seed explícita, é reproduzível e invalida apenas as
células vizinhas e fronteiras de chunks que podem ter mudado.

## Limites e negativos obrigatórios

O contrato rejeita tile inexistente, atlas alterado, coordenadas fora do limite,
regra ambígua/cíclica, preenchimento ilimitado, resultado assíncrono obsoleto,
falta de memória controlada e escrita parcial. Cancelamento não deixa estado
intermediário.

## Fluxo de aceite

Criar mapas nos três grids → pintar caminho/terreno → preencher região limitada
→ apagar → editar regra → revisar bordas → bloquear camada → Undo/Redo →
salvar/reabrir → exportar/importar caso representativo. Cada sublote terá
testes focados, suíte oficial, gates estáticos, build e captura real quando
houver UI executável.
