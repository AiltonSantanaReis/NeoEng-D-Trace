# Etapa 8 — baseline e contrato antes da implementação

## Identificação

- etapa: 8 do plano de integração de adaptadores nativos;
- base técnica: `main` integrado em `86195af3203ba7092bae70161ededd064f2b718b`;
- branch de trabalho: `codex/stage8-native-advanced-implementation`;
- baseline de fonte: `baseline_manifest.json` verificado antes da implementação;
- escopo: bleed/extrusão do atlas, propriedades avançadas de engine e
  normalização de coordenadas entre Godot e Unity;
- etapas 9 e 10: não iniciadas.

## Estado encontrado

O núcleo já produzia atlas com `bleed`, `extrusion`, `packed_rect` e `rotated`,
e já possuía transação de escrita para PNG/JSON. O contrato v1, porém, não
transportava esses campos aos adaptadores; os plugins consumiam apenas a imagem
original, com propriedades fixas e conversão Unity em 100 pixels por unidade.

Essa diferença foi caracterizada antes da alteração. O trabalho desta etapa
não duplica o algoritmo de atlas e não altera o contrato v1 existente.

## Contrato v2 definido

O manifesto v2 mantém todos os campos comuns do v1 e adiciona somente
`advanced`, com schema próprio versão 1:

- `coordinate_system`: origem da imagem e do polígono, direção do eixo Y e
  pixels por unidade por perfil;
- `atlas`: bleed uniforme, páginas com caminho relativo, SHA-256, dimensões e
  entradas por sprite (`rect`, `packed_rect`, `extrusion`, `rotated`);
- `engine_properties.godot`: filtro, repetição, centralização e `z_index`;
- `engine_properties.unity`: pixels por unidade, filtro, wrap, sorting layer,
  sorting order e profundidade Z.

A validação exige chaves exatas, caminhos relativos seguros, hashes com 64
caracteres, dimensões positivas, números finitos, enumerações permitidas,
extrusão coerente e cobertura exata dos sprites do metadata. O v1 permanece
aceito sem `advanced`.

## Gates desta etapa

1. testes de contrato e negativos no Python;
2. geração do manifesto a partir de saída real de `build_atlas(..., bleed=1)`;
3. importação headless no Godot real e no Unity real;
4. repetição sem alteração, verificação das propriedades geradas e rejeição de
   alteração de hash;
5. logs e manifestos sanitizados, hashes e índice verificável;
6. diff, baseline, lint, cobertura e CI antes de promoção.

Este documento é um baseline de intenção e contrato; não é evidência de
execução nem aprovação de release.