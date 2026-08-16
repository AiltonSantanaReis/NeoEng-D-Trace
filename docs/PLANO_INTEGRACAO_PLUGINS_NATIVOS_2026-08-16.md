# Plano de integração dos adaptadores nativos

Data: 2026-08-16
Estado: etapas 1 e 2 aprovadas localmente; etapas 3 a 10 não iniciadas; nenhuma engine é declarada integrada até possuir testes reais no ambiente correspondente.

## Objetivo

Adicionar adaptadores source-only para Godot e Unity, integrados ao
NeoEng-D-Trace pelo contrato JSON/manifesto versionado. O núcleo do D-Trace
continua sendo a fonte da verdade para imagem, máscara, geometria, colisão,
pivô, atlas, tileset e animação.

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
4. **Importação Godot** — gerar Sprite2D, pivô, CollisionPolygon2D, tiles,
   animação e propriedades sem alterar recursos não gerados.
5. **Pacote Unity source-only** — criar pacote UPM local/Git sem binários,
   com assembly de editor e metadados versionados.
6. **Importação Unity** — gerar Sprite, ScriptableObject, PolygonCollider2D,
   prefabs controlados e validação no Inspector.
7. **Sincronização e overrides** — atualizar por hash, preservar overrides,
   detectar divergências e bloquear atualização destrutiva sem confirmação.
8. **Recursos avançados** — integrar atlas/bleed, tileset, animações,
   colisores compostos e normalização de coordenadas.
9. **Dry-run, segurança e rollback** — listar mudanças antes de aplicar,
   validar schema/hash, impedir caminhos inseguros e remover artefatos parciais.
10. **Fixtures e fechamento** — validar projetos reais Godot/Unity, CI,
   determinismo, regressão, documentação, hashes e decisão formal de release.

## Estado inicial comprovado

- formato de projeto v1 e perfis JSON existentes permanecem contratos ativos;
- transação do atlas já existe e foi revalidada em etapa anterior;
- rollback multi-saída da CLI já está integrado e testado;
- plugins Godot/Unity ainda não estão implementados e permanecem NÃO TESTADOS;
- etapas 1 e 2 possuem implementação e testes locais; nenhum adaptador de engine foi executado;
- etapas 3 a 10 permanecem NÃO INICIADAS e sem declaração de integração nativa.

## Regra de promoção

Cada etapa produzirá testes, artefatos e relatório em docs/evidence. A etapa
só será promovida quando o critério de aceite passar em ambiente real ou for
classificada explicitamente como BLOQUEADA/NÃO TESTADA.
