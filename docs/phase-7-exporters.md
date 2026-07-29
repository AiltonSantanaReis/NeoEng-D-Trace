# Fase 7: Exportadores

## Visão Geral
Exportadores modulares para sprites, atlas e metadados.

## Uso
- Importe e chame funções core.
- Use perfis para engines específicas.

## Extensibilidade
Adicione novos perfis em `src/exporters/profiles/`.

## APIs
- `extract_masked_sprite`: Extrai sprite mascarado com antialiasing e trim.
- `export_scene_metadata`: Gera JSON com rects, pivots normalizados.
- `pack_sprites_to_atlas`: Empacota em atlas múltiplos se necessário.

## Edge Cases
- Polígonos fora da imagem: Clippados.
- Polígonos vazios: Erro ou sprite vazio.
- Atlas cheio: Novo atlas criado.