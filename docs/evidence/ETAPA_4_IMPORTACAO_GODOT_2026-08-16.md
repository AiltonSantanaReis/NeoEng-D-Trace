# Evidência — Etapa 4: importação Godot

## Decisão

**APROVADA LOCALMENTE NO GODOT, NO ESCOPO DOCUMENTADO.** A etapa foi
promovida somente depois de uma fixture headless real carregar e verificar os
recursos nativos gerados. Unity, sincronização contínua, dry-run e rollback
continuam pertencendo às etapas posteriores e não são declarados resolvidos.

## Implementação validada

- `Sprite2D` com `AtlasTexture`, região, pivô em pixels e pivô normalizado;
- metadados de camada, grupo, trimming e padding preservados no recurso Godot;
- colisão simples e colisão composta em múltiplos `CollisionPolygon2D`;
- `TileSet` nativo com `TileSetAtlasSource`, margem, espaçamento e camada física;
- `AnimatedSprite2D` com frames externos e velocidade configurável;
- driver source-only para habilitar somente a colisão correspondente ao frame
  ativo;
- importação pelo manifesto individual e pelo fluxo `import_project`;
- escrita canônica com referências e IDs estáveis;
- bloqueio de sobrescrita para cenas, tilesets e animações manuais.

Os payloads opcionais são incorporados em `metadata.tileset` e
`metadata.animation`, usando os formatos existentes do projeto:
`neoeng-d-trace-tileset` versão 1 e `neoeng-d-trace-animation` versão 1.

## Fixture e execução real

O harness criou um projeto Godot temporário com:

- addon source-only copiado para `addons/neoeng_d_trace`;
- folha PNG de 34×14 com tiles 16×12, margem 1 e espaçamento 1;
- dois frames PNG de animação;
- objetos com colisão simples e composta;
- manifesto real gerado por `build_integration_manifest` e salvo por
  `save_integration_manifest`.

O executor e os diretórios temporários foram sanitizados nos relatórios
persistidos para `<local-path>`.

O Godot `4.7.stable.official.5b4e0cb0f` retornou código `0` no carregamento do
editor e no validador dedicado. Marcadores emitidos pelo validador:

```text
NATIVE_PLUGIN_STAGE4_CORE=SUCCESS
GENERATED_SCENE=res://NeoEngGenerated/hero.tscn
COLLISION_POINTS=4
COMPOUND_COLLISION_POLYGONS=2
TILESET_NATIVE_LOADED=true
TILESET_COLLISION_POINTS=4
ANIMATION_FRAMES=2
ANIMATION_FRAME_COLLISION_SYNC=true
SPRITE_PROPERTIES_PRESERVED=true
REPEAT_IMPORT_DETERMINISTIC=true
MANUAL_OVERWRITE_BLOCKED=true
```

## Falhas reais encontradas e corrigidas

- O `ResourceSaver` gerava identificadores variáveis; a cena não era
  determinística. O gerador foi substituído por texto canônico estável. A
  falha inicial está preservada em
  `artifacts/godot-plugin-stage4-2026-08-16/initial-failure-nondeterminism.json`.
- O validador acessava um objeto depois de `free()`, produzindo erro real do
  Godot e impedindo o encerramento correto. A contagem passou a ser capturada
  antes da liberação.
- A primeira versão do driver de colisão não sincronizou o frame ativo na
  instanciação headless. O caso falho está preservado em
  `artifacts/godot-plugin-stage4-2026-08-16/initial-failure-animation-sync.json`.
  O driver foi corrigido para consultar a instância ativa a cada atualização.
- A fixture final foi repetida depois dessas correções, incluindo margem e
  espaçamento não triviais do tileset e conflitos manuais separados.

## Regressão e qualidade

Após a implementação final:

- suíte completa anterior: `1107 passed`, `10 warnings`, `0 failed`;
- política de cobertura: aprovada;
- testes focados de scaffold e manifesto: passaram antes da ampliação final;
- Black, isort e flake8 dos arquivos Python alterados: aprovados;
- fixture Godot ampliada: código `0`, sem erro de script no relatório final;
- pacote source-only: gerado deterministicamente e contendo somente fontes,
  configuração e documentação permitidas;
- verificação de higiene: nenhum endereço absoluto nos artefatos persistidos.

A suíte completa foi repetida após a implementação final, antes de qualquer
commit.

## Artefatos

Índice de tamanhos e SHA-256:
`artifacts/godot-plugin-stage4-2026-08-16/stage4-index.json`.

O conjunto inclui o relatório final, a falha de não determinismo, a falha de
sincronização preservada, o pacote source-only, a folha PNG, os dois frames e
as cenas/recursos `.tscn`/`.tres` efetivamente gerados e carregados pelo Godot.

## Limitações que permanecem fora desta promoção

- plugin e importação nativa Unity;
- sincronização contínua por hash e atualização incremental;
- dry-run, rollback transacional e política de recuperação de múltiplas saídas;
- bleed/extrusão de textura no fluxo nativo da engine;
- validação visual do editor Godot com interação manual do menu;
- CI em projeto externo ou distribuição por marketplace.

Esses pontos continuam explicitamente nas etapas 5 a 10 e não foram mascarados
como concluídos.
