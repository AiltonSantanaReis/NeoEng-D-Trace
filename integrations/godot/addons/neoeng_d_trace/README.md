# NeoEng D-Trace — Godot source-only adapter

Este addon importa manifestos de integração válidos produzidos pelo
NeoEng-D-Trace. A fonte da verdade continua sendo o manifesto e seus
metadados; o addon não contém binários, download automático ou dependências
externas.

## Capacidades validadas

- geração determinística de `Sprite2D` com `AtlasTexture`, região e pivô;
- conversão de colisão para `CollisionPolygon2D`, inclusive partes compostas;
- preservação de propriedades de sprite como camada, grupo, trimming, padding e
  pivô normalizado em metadados Godot;
- geração de `TileSet` com `TileSetAtlasSource`, margem, espaçamento e camada
  física;
- geração de `AnimatedSprite2D` com frames externos e sincronização opcional de
  colisões por frame usando o driver source-only;
- bloqueio de sobrescrita de recursos que não tenham a marca de geração;
- escrita canônica dos recursos gerados para permitir repetição byte a byte.

## Payloads opcionais

Os formatos existentes `neoeng-d-trace-tileset` versão 1 e
`neoeng-d-trace-animation` versão 1 podem ser incluídos em
`metadata.tileset` e `metadata.animation` do manifesto. Os caminhos de textura
em `animation.frames[].texture` devem ser referências relativas ao projeto
Godot (`res://` é acrescentado pelo importador). A velocidade da animação usa
12 FPS quando o payload não informa `speed`; um valor informado deve ser finito
e positivo.

O importador falha fechado para payloads incompatíveis, caminhos inseguros,
quadros ausentes, colisões inválidas e conflitos com recursos manuais.

## Instalação

Copie `addons/neoeng_d_trace` para um projeto Godot, extraia o ZIP source-only
na raiz do projeto ou use o diretório do repositório. Ative `NeoEng D-Trace` em
Project Settings > Plugins.

## Comandos do editor

- `NeoEng D-Trace: Diagnose integration manifests` faz uma varredura somente
  leitura de `res://NeoEngGenerated`.
- `NeoEng D-Trace: Import integration manifests` importa os manifestos e cria
  somente recursos gerados.

Os dois comandos imprimem o resultado estruturado. A execução real validada
está registrada em `docs/evidence` do repositório.