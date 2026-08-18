# Plano de integração dos adaptadores nativos

Data da revisão: 2026-08-18
Estado: etapas 4, 5, 6, 7, 8 e 9 integradas nos escopos documentados; a etapa 10 está integrada pela PR #84 no merge `bca43f399928d69cb81e133e40991b7c011a0c10`; o CI pós-merge `32028639637` passou em Linux e Windows; release permanece não aprovada. A Etapa 8 foi integrada pela PR #79 no merge `8b40be3c72705cdd99c2e28849f030b7b3182bf0` e reproduzida no CI pós-merge `31995768720`. A Etapa 9 foi integrada pela PR #81 no merge `e1620571ab2f638ba671baa33ac508858e229313`; o CI pós-merge `32012110722` passou em Linux e Windows. A distinção entre plugins de terceiros e adaptadores first-party source-only foi formalizada em docs/evidence/DECISAO_ESCopo_ADAPTADORES_NATIVOS_2026-08-17.md.

## Reconciliação vigente da Etapa 4 de estabilização

O número “Etapa 4” usado nesta execução refere-se à estabilização posterior de transação global e rollback de múltiplos manifestos. Ele não reclassifica nem reescreve o snapshot histórico da Etapa 4 deste plano, cujo critério original era a importação Godot. A evidência vigente da estabilização é `docs/evidence/ETAPA_4_TRANSACAO_GLOBAL_MANIFESTOS_2026-08-17.md`, baseada no commit técnico `807af85`; o aceite original de importação Godot permanece histórico e separado.

## Reconciliação com o plano de cenários

O plano de cenários parallax e paleta de comandos é uma linha de produto
separada dos adaptadores nativos Godot/Unity. A PR `#92` não alterou os
contratos das engines nem promoveu as etapas 1–10 deste plano.

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
- a etapa 5 foi validada somente no escopo do pacote; sincronização e rollback permanecem posteriores;
- a etapa 6 possui importação Unity real de Sprite, ScriptableObject, PolygonCollider2D e prefab controlado, com hash de imagem e conflitos manuais testados;
- a etapa 6 foi validada somente no escopo documentado; sincronização e overrides foram implementados e validados na etapa 7; rollback permanece posterior;
- a etapa 7 foi validada em Godot 4.7 e Unity 6000.5.7f1 para todos os recursos gerados no escopo atual, com hashes, overrides, divergência, confirmação destrutiva e idempotência; PR 73, merge 283db2f e CI pós-merge 31971686798 foram concluídos; dry-run, rollback e etapas 8 a 10 permanecem posteriores;

- a etapa 8 foi integrada pela PR #79 no merge `8b40be3c72705cdd99c2e28849f030b7b3182bf0`; os checks pré-merge `31995537696` e o CI pós-merge `31995768720` passaram em Linux/Windows; os testes reais de Godot 4.7 e Unity 6000.5.7f1 permanecem documentados como evidência local reproduzível em docs/evidence/ETAPA_8_ENCERRAMENTO_POS_MERGE_2026-08-17.md e docs/evidence/artifacts/native-advanced-stage8-2026-08-17/;
- a etapa 9 foi integrada pela PR #81 no merge `e1620571ab2f638ba671baa33ac508858e229313`; os checks pré-merge `32011747754` e o CI pós-merge `32012110722` passaram em Linux/Windows; os testes reais de Godot 4.7 e Unity 6000.5.7f1, o dry-run, o drift de hash, a repetição determinística e o rollback estão documentados em docs/evidence/ETAPA_9_DRY_RUN_SEGURANCA_ROLLBACK_PRE_MERGE_2026-08-17.md e docs/evidence/ETAPA_9_ENCERRAMENTO_POS_MERGE_2026-08-17.md; a etapa 10 foi integrada pela PR #84 no merge `bca43f399928d69cb81e133e40991b7c011a0c10`; o CI pós-merge `32028639637` passou em Linux e Windows; o suplemento administrativo local dos dois testes de symlink registrou 2 passed, 0 skipped e está preservado no fechamento da Etapa 9;
## Regra de promoção

Cada etapa produzirá testes, artefatos e relatório em docs/evidence. A etapa só será promovida quando o critério de aceite passar em ambiente real ou for classificada explicitamente como BLOQUEADA/NÃO TESTADA. Um subescopo validado não promove automaticamente outra etapa.
