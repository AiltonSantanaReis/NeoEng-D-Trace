# Matriz de limites e suporte — Godot/Unity pós-E13

**ID:** `MATRIX-POS-E13-ENGINE-SUPPORT-20260912`
**Estado:** `IN_PROGRESS / PENDING_EVIDENCE_FOR_EXACT_TARGET_VERSIONS`
**Data:** 2026-09-12
**Produto:** NeoEng-D-Trace

Esta matriz separa capacidade nativa da engine, contrato do adaptador e
capacidade efetivamente comprovada no projeto. A existência de uma API oficial
não é aceite do produto; cada linha ainda exige fluxo, persistência, runtime,
erro e captura quando aplicável.

## Versões e regra de confiança

- o seletor do produto declara Godot `4.7` e Unity `6000.5.7f1`;
- a documentação oficial Godot 4.7 foi usada para Parallax2D e GPUParticles2D;
- a documentação Unity consultada publicamente nesta etapa está publicada
  para Unity 6.0/6000.0 em várias páginas; isso não comprova sozinho
  compatibilidade com `6000.5.7f1`;
- a matriz exata de Unity 6000.5.7f1 permanece `PENDING_EVIDENCE` até executar
  essa versão localmente com o pacote de destino fixado.

## Godot 4.7

| Área | Suporte nativo e limite relevante | Contrato de produto |
|---|---|---|
| Câmera 2D | `Camera2D` controla a rolagem do viewport; há uma câmera ativa por viewport, zoom, limites, margens e smoothing. A posição efetiva da tela pode divergir da posição do nó quando há smoothing/limites. | exportar câmera semântica, limites, zoom, smoothing e shots; validar posição efetiva no runtime | `SUPPORTED_ADAPTER_REQUIRED` |
| Parallax | `Parallax2D` oferece `scroll_scale`, `repeat_size`, `repeat_times`, offsets e limites; valores de posição podem ser sobrescritos pelo próprio comportamento da node. | mapear profundidade/velocidade relativa para `scroll_scale`, repetição e bounds; não rasterizar a cena | `SUPPORTED_WITH_MAPPING` |
| Luz 2D | Point/Directional Light2D, CanvasModulate, receptores e occluders. Sombras direcionais têm limitação documentada de comprimento infinito. | declarar tipo, intensidade, máscara, occluder e fallback; não prometer sombra física equivalente em todos os estilos | `SUPPORTED_WITH_LIMITS` |
| Partículas 2D | `GPUParticles2D` usa material de processo, seed, emissão, lifetime, local coordinates, trails e seek; não colide com `PhysicsBody2D`, apenas com recursos de luz/oclusão compatíveis. | separar partículas visuais de colisão física; validar seed, seek e custo GPU | `SUPPORTED_WITH_LIMITS` |
| Tilemap | `TileMapLayer` é o caminho atual; `TileMap` é depreciado. Layers adicionais são nodes separadas; atualizações são agrupadas no fim do frame e a serialização possui limites de coordenadas. | exportar uma camada explícita por camada lógica e testar atualização/reabertura | `SUPPORTED_WITH_MAPPING` |
| 2.5D/3D | a engine oferece nodes 3D, mas o adapter do projeto é deliberadamente um vertical slice. | não anunciar editor 3D completo por causa do runtime híbrido | `VERTICAL_SLICE_ONLY` |

## Unity 6000.x

| Área | Suporte nativo e limite relevante | Contrato de produto |
|---|---|---|
| Câmera 2D/shot | Unity possui Camera; Cinemachine é pacote separado para composição, follow, blend e shots. A versão do pacote precisa ser fixada por projeto. | exportar câmera base e clips; declarar se o destino usa Camera, Cinemachine ou Timeline | `ADAPTER_REQUIRED / VERSIONED` |
| Parallax | não há um equivalente único que substitua o modelo de autoria do NeoEng; o adapter usa transform, camada e componente próprio de parallax. | manter profundidade e strengths no contrato, com componente nativo verificável | `SUPPORTED_BY_ADAPTER` |
| Luz 2D | o sistema `Light 2D` documentado pertence ao URP e depende de renderer, sorting layers, blend styles, shaders e shadow casters compatíveis. | exigir URP para o perfil de luz 2D; oferecer diagnóstico explícito para Built-in/HDRP | `URP_REQUIRED_FOR_2D_LIGHTING` |
| Partículas | Unity possui Particle System, mas o consumo do sidecar e a equivalência de módulos precisam ser verificadas na versão-alvo. | mapear emissão, seed, lifetime, textura e direção; marcar módulo sem equivalente como fallback | `ADAPTER_REQUIRED / PENDING_TARGET_RUNTIME` |
| Tilemap | Tilemap/Tilemap Renderer/Collider são componentes e pacotes distintos; a instalação e pipeline do projeto destino importam. | gerar assets e componentes reais, não apenas JSON; testar Package Manager e renderer | `PACKAGE_AND_PIPELINE_DEPENDENT` |
| Timeline | Timeline é pacote versionado para conteúdo cinematográfico, áudio e sequências. | converter clips com semântica conhecida; não chamar metadata de Timeline executável | `PACKAGE_VERSIONED` |
| 2.5D/3D | o adapter atual materializa o vertical slice limitado e não substitui colisão 3D, partículas 3D completas, tilemap 3D, import geral de modelos ou editor 3D completo. | manter `VERTICAL_SLICE_ONLY` no manifest e na UI | `VERTICAL_SLICE_ONLY` |

## Política de publicação

Cada exportação deverá mostrar a matriz de capabilities do destino:

- `NATIVE`: objeto/componente real e comportamento comprovado;
- `ADAPTED`: componente real criado por adapter com diferença documentada;
- `METADATA_ONLY`: informação persistida, sem comportamento equivalente;
- `FALLBACK`: comportamento alternativo explicitamente informado;
- `UNSUPPORTED`: rejeição segura com mensagem acionável.

Nenhum perfil de engine será anunciado como “suporte completo” enquanto a
versão exata, o renderer/pipeline, o runtime e o round-trip visual não tiverem
evidência vinculada ao commit.

## Fontes oficiais

- [Godot 4.7 Parallax2D](https://docs.godotengine.org/en/4.7/classes/class_parallax2d.html)
- [Godot 4.7 GPUParticles2D](https://docs.godotengine.org/en/4.7/classes/class_gpuparticles2d.html)
- [Godot Camera2D estável](https://docs.godotengine.org/en/stable/classes/class_camera2d.html)
- [Godot iluminação 2D](https://docs.godotengine.org/en/stable/tutorials/2d/2d_lights_and_shadows.html)
- [Godot TileMapLayer](https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html)
- [Unity 6 iluminação 2D em URP](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/2d-index.html)
- [Unity 6 Light 2D](https://docs.unity3d.com/6000.0/Documentation/Manual/urp/2DLightProperties.html)
- [Unity 6 Tilemap](https://docs.unity3d.com/6000.0/Documentation/Manual/tilemaps/tilemaps.html)
- [Unity 6 Timeline](https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.timeline.html)
- [Unity 6 Cinemachine](https://docs.unity3d.com/6000.0/Documentation/Manual/com.unity.cinemachine.html)
