# Etapa 0.5.2D — Seleção automática e diálogo compacto

## Objetivo

Corrigir dois problemas observados na validação manual da interface:

1. o polígono recém-criado não permanecia selecionado;
2. o diálogo de exportação distribuía os controles por uma altura excessiva.

## Seleção automática

`Scene.add_polygon()` agora cria e seleciona o novo objeto antes de emitir a
notificação da cena. A alteração central protege todas as ferramentas que usam
essa API:

- desenho direto no canvas;
- caneta;
- laço livre;
- laço poligonal;
- laço magnético;
- retângulo;
- elipse;
- detecção e criação por comandos.

`Scene.add_object()` mantém o comportamento anterior por padrão. Objetos
carregados ou inseridos explicitamente só são selecionados quando o chamador
usa `select=True`.

O painel lateral agora usa `scene.selected_id` como fonte de verdade. Isso
impede que a lista mostre uma seleção antiga quando o canvas já desmarcou o
objeto.

## Diálogo de exportação

O diálogo passa a usar:

- grupos com política vertical `Maximum`;
- botões com política vertical `Fixed`;
- espaçamento interno de 8 px;
- margens consistentes;
- tamanho calculado pelo conteúdo.

Nenhuma opção de exportação foi removida ou renomeada.

## Fora do escopo

Esta entrega não altera:

- formatos de saída;
- perfis Godot, Unity, Phaser ou Genérico;
- PNG, atlas ou GLTF;
- ferramentas de desenho;
- regras geométricas;
- atalhos e menus.
