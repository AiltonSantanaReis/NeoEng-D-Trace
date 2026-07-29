# Etapa 0.5.2C — Integração dos perfis à interface de exportação

## Objetivo

Tornar acessíveis pela interface os perfis de metadados já existentes e
validados internamente, sem alterar ou remover os fluxos atuais de PNG, atlas e
GLTF/GLB.

## Escopo implementado

O grupo **2D Sprites & Atlas** passa a exibir uma seção
**Engine Metadata (JSON)** com os alvos:

- Generic JSON;
- Godot 4;
- Unity;
- Phaser 3.

O botão **Export Selected Object Metadata** gera um arquivo JSON para o objeto
selecionado utilizando o perfil escolhido.

## Limite funcional explícito

Esta entrega exporta metadados estruturados de um objeto 2D. Ela não cria:

- projeto completo de Godot, Unity ou Phaser;
- plugin ou importador automático para a engine;
- cena pronta da engine;
- pacote contendo sprite e metadados em uma única operação;
- metadados específicos de atlas para todas as engines.

Essas capacidades exigem contratos próprios e serão tratadas em etapas
posteriores.

## Preservação de funcionalidades

Continuam disponíveis sem mudança de fluxo:

- Export Selected Sprite;
- Batch Export All Sprites;
- Build Texture Atlas;
- Export Full Scene to GLTF;
- Export Selected Object to GLTF.

A exportação de metadados não exige a imagem original carregada, pois utiliza a
geometria, camada e grupo do objeto existente na cena. Os demais exportadores
continuam exigindo imagem quando necessário.

## Segurança e confiabilidade

- somente perfis predefinidos podem ser selecionados;
- nenhum nome de módulo fornecido pelo usuário é carregado dinamicamente;
- o arquivo recebe extensão `.json` quando ela for omitida;
- o nome sugerido é higienizado para evitar separadores de caminho;
- erros são registrados e apresentados ao usuário;
- a gravação continua utilizando o mecanismo atômico de `save_json_metadata`.
