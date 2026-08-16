# Evidência — Etapa 7: sincronização e overrides

Data da execução: 2026-08-16
Estado: aprovada localmente no escopo validado; ainda não integrada por commit/push/merge.

## Escopo implementado

A Etapa 7 cobre todos os recursos atualmente gerados pelos adaptadores:

- Godot: Sprite2D/AtlasTexture, sprites compostos, TileSet e animação;
- Unity: Sprite, ScriptableObject, PolygonCollider2D e prefab controlado;
- hash da imagem e dos metadados;
- fingerprint determinístico do texto/estrutura gerada;
- override *.ndt.override.json preservado e aplicado;
- divergência manual bloqueada;
- atualização destrutiva somente com NEOENG_STAGE7_CONFIRM_DESTRUCTIVE=1 ou true;
- repetição idempotente reportada como UNCHANGED;
- escrita continua atômica pelo mecanismo existente do adaptador.

O contrato comum não foi alterado. No Unity, foi acrescentado um parser local para polygon_in_sprite no formato comum [[x, y], ...], pois JsonUtility não desserializa esse formato para Vector2[].

## Testes reais executados

Godot 4.7 headless:

~~~
NATIVE_SYNC_STAGE7_GODOT=SUCCESS
INITIAL_UPDATE=PASS
REPEAT_UNCHANGED=PASS
OVERRIDE_PRESERVED=PASS
MANUAL_DIVERGENCE_BLOCKED=PASS
DESTRUCTIVE_CONFIRMATION=PASS
HASH_DRIFT_REJECTED=PASS
~~~

A repetição foi verificada individualmente para os quatro resultados gerados: sprite principal, sprite composto, TileSet e animação.

Unity 6000.5.7f1:

~~~
NATIVE_SYNC_STAGE7_UNITY=SUCCESS
INITIAL_UPDATE=PASS
REPEAT_UNCHANGED=PASS
OVERRIDE_PRESERVED=PASS
MANUAL_DIVERGENCE_BLOCKED=PASS
DESTRUCTIVE_CONFIRMATION=PASS
HASH_DRIFT_REJECTED=PASS
~~~

Regressões reais:

~~~
NATIVE_PLUGIN_STAGE4_CORE=SUCCESS
NATIVE_IMPORT_STAGE6=SUCCESS
~~~

## Artefatos

- docs/evidence/artifacts/godot-sync-stage7-2026-08-16/stage7-report.json
- docs/evidence/artifacts/godot-sync-stage7-2026-08-16/stage7-index.json
- docs/evidence/artifacts/unity-sync-stage7-2026-08-16/stage7-report.json
- docs/evidence/artifacts/unity-sync-stage7-2026-08-16/stage7-index.json
- docs/evidence/artifacts/godot-plugin-stage4-regression-2026-08-16.json
- docs/evidence/artifacts/unity-import-stage6-regression-2026-08-16/
- artefatos históricos da Etapa 6 preservados sem alteração de conteúdo.

Os artefatos novos passaram por varredura de caminhos locais, identificadores de usuário, portas, PIDs e endereços. Resultado: SENSITIVE_SCAN=CLEAN.

## Regressões e refatorações auditadas

1. A execução inicial removeu seis artefatos versionados da Etapa 6. Foi uma regressão do processo de teste, não uma mudança funcional; os arquivos foram restaurados exatamente do HEAD e os hashes de conteúdo foram conferidos.
2. Uma edição intermediária removeu o pré-import do harness Godot. Isso reduziria a validade da prova; o pré-import foi restaurado com encerramento determinístico (quit-after 5) e a Etapa 4 foi reexecutada com sucesso.
3. O Unity apresentou uma falha funcional real: JsonUtility carregava o manifesto, mas não convertia o polígono no formato comum. O adaptador passou a interpretar explicitamente os pares numéricos, sem alterar o contrato ou os fixtures.
4. A comparação de fingerprint Unity revelou instabilidade de representação decimal entre execuções. A normalização limitada a seis casas e cultura invariável foi necessária para que a idempotência refletisse a geometria, não a representação binária do float.
5. O primeiro uso de hash Godot com método inexistente foi rejeitado pelo Godot 4.7. A implementação foi corrigida para HashingContext.HASH_SHA256 e comprovada no engine real.
6. Houve erros intermediários de edição nos harnesses (quebra de linha, escapes e indentação GDScript). Todos foram detectados por py_compile ou pelo parser real do Godot e corrigidos antes da geração da evidência final. Nenhum desses estados foi usado para declarar PASS.

As refatorações mantidas no diff final são necessárias para centralizar a decisão de sincronização, preservar o estado gerado e tornar os cenários reais reproduzíveis. Não há alteração funcional sem justificativa no diff final.

## Limitações honestas

- dry-run, rollback transacional de múltiplas saídas e recursos avançados de atlas permanecem nas etapas 8 e 9;
- a Etapa 7 não aprova release nem substitui CI pós-merge;
- não houve commit, push ou merge nesta evidência.