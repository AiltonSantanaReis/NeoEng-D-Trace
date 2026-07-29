# Consolidação da renomeação — árvore única `src/`

## Decisão

A linha de migração física 0.6N2/0.6N3 foi encerrada. A identidade NeoEng-D-Trace e as melhorias funcionais são preservadas, mas a arquitetura volta a ter uma única fonte de verdade em `src/`.

## Preservado

- identidade central e interface bilíngue;
- Laço Magnético e melhorias 0.5.2F3;
- seleção automática e sincronização lateral;
- diálogo de exportação compacto;
- perfis Generic, Godot, Unity e Phaser;
- sprite, atlas e JSON;
- GLTF/GLB com generator NeoEng-D-Trace, `save_binary()`, escrita atômica, metadados, padding e reabertura real;
- entrada headless, testes e histórico funcional.

## Removido explicitamente

- diretório duplicado `neoeng_d_trace/`;
- aliases que redirecionavam `src.*`;
- testes e documentos cujo único objetivo era validar a migração física;
- entrada `python -m neoeng_d_trace`.

Nada disso representa remoção de funcionalidade do produto. A entrada de desenvolvimento permanece `python app.py`; a entrada instalada é `neoeng-d-trace`, apontando para `src.launcher:main`.

## Configuração

A configuração continua em `<raiz>/config.json`, preservando o comportamento anterior. Mudança futura para AppData não faz parte desta etapa.

## Rollback

O instalador transacional salva todos os arquivos modificados e removidos antes da consolidação. O rollback restaura a árvore dupla anterior somente para recuperação técnica.
