# Plano de integração dos adaptadores nativos

Data: 2026-08-16
Estado: etapas 4 e 5 aprovadas localmente nos escopos documentados; etapas 6 a 10 não iniciadas; nenhuma sincronização nativa completa é declarada integrada sem testes reais no ambiente correspondente.

## Objetivo

Adicionar adaptadores source-only para Godot e Unity, integrados ao NeoEng-D-Trace pelo contrato JSON/manifesto versionado. O núcleo do D-Trace continua sendo a fonte da verdade para imagem, máscara, geometria, colisão, pivô, atlas, tileset e animação.

## Regras de arquitetura

- nenhum DLL, executável auxiliar, biblioteca nativa ou download automático;
- fluxo unidirecional: imagem e metadados do D-Trace produzem recursos da engine;
- arquivos gerados separados dos recursos editados pelo usuário;
- overrides manuais nunca são sobrescritos silenciosamente;
- hash da imagem, hash dos metadados, versão do schema e versão do gerador são obrigatórios;
- importação determinística, dry-run e rollback antes de declarar sucesso;
- instalação por Git, ZIP ou diretório local, sem marketplace obrigatório;
- nenhuma etapa pode declarar engine real validada usando apenas mocks.

## Dez etapas e critérios de aceite

1. **Contrato comum e manifesto** — definir schema, engine target, hashes,
   referências relativas, diretório de geração, overrides e compatibilidade.
2. **Manifesto implementado** — gerar, validar e salvar manifesto determinístico
   com escrita atômica; testar entradas reais e falhas negativas.
3. **Plugin Godot source-only** — criar addon instalável por pasta/ZIP/Git,
   com identificação, versão e comandos de diagnóstico.
4. **Importação Godot** — gerar e carregar no Godot real `Sprite2D`,
   `AtlasTexture`, pivô, propriedades, colisores simples e compostos, `TileSet`
   com atlas/margem/espaçamento, `AnimatedSprite2D` e colisões sincronizadas por
   frame. A importação deve ser determinística e bloquear recursos manuais.
5. **Pacote Unity source-only** — criar pacote UPM local/Git sem binários,
   com assembly de editor e metadados versionados.
6. **Importação Unity** — gerar Sprite, ScriptableObject, PolygonCollider2D,
   prefabs controlados e validação no Inspector.
7. **Sincronização e overrides** — atualizar por hash, preservar overrides,
   detectar divergências e bloquear atualização destrutiva sem confirmação.
8. **Recursos avançados** — integrar bleed/extrusão de atlas, propriedades
   avançadas de engine e normalização adicional de coordenadas entre perfis.
9. **Dry-run, segurança e rollback** — listar mudanças antes de aplicar,
   validar schema/hash, impedir caminhos inseguros e remover artefatos parciais.
10. **Fixtures e fechamento** — validar projetos reais Godot/Unity, CI,
    determinismo, regressão, documentação, hashes e decisão formal de release.

## Estado inicial comprovado

- formato de projeto v1 e perfis JSON existentes permanecem contratos ativos;
- transação do atlas já existe e foi revalidada em etapa anterior;
- rollback multi-saída da CLI já está integrado e testado;
- o addon Godot source-only e a importação da etapa 4 foram validados em fixture headless real;
- etapas 1 e 2 possuem implementação e testes locais; a etapa 3 possui addon Godot source-only e fixture headless real;
- a etapa 4 foi promovida somente no escopo validado deste plano;
- a etapa 5 possui pacote Unity UPM source-only, assemblies Runtime/Editor e diagnóstico batch validados no Unity real `6000.5.7f1`;
- a etapa 5 foi validada somente no escopo do pacote; importação Unity, sincronização e rollback permanecem posteriores;
- etapas 6 a 10 permanecem NÃO INICIADAS e sem declaração de sincronização nativa.

## Regra de promoção

Cada etapa produzirá testes, artefatos e relatório em docs/evidence. A etapa só será promovida quando o critério de aceite passar em ambiente real ou for classificada explicitamente como BLOQUEADA/NÃO TESTADA. Um subescopo validado não promove automaticamente outra etapa.
