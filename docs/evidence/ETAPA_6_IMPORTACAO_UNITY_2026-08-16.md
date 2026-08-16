# Evidência — Etapa 6: importação Unity

## Identificação

- Etapa: 6 — Importação Unity
- Estado: validação local real concluída; promoção ainda depende do fluxo de revisão/merge
- Data: 2026-08-16
- Engine real: Unity `6000.5.7f1`
- Pacote: `com.neoeng.dtrace` versão `0.2.0`

## Objetivo e escopo

Implementar a importação do manifesto Unity para recursos nativos controlados:
`Sprite`, `NeoEngImportedSpriteMetadata`, `PolygonCollider2D` e prefab. A
validação é feita pelo próprio Unity Editor após salvar e recarregar os recursos
pelo `AssetDatabase`.

A etapa não declara sincronização incremental, overrides, rollback, colisores
compostos ou dry-run completos; esses itens permanecem nas etapas posteriores.

## Implementação

- `Editor/UnityImportGenerator.cs` com menu e método batch;
- `Runtime/NeoEngImportedSpriteMetadata.cs` para o ScriptableObject nativo;
- `Runtime/NeoEngGeneratedMarker.cs` para identificar prefabs gerados;
- validação do contrato, referências relativas, hash da imagem e política de
  diretório gerado;
- criação de `Sprite` com rect e pivô do manifesto;
- criação de ScriptableObject com pivô, rect, layer, grupo, padding e polígono;
- criação de prefab com `SpriteRenderer`, `PolygonCollider2D` e marker;
- bloqueio fechado quando `Assets/NeoEngGenerated` contém conteúdo manual;
- falha fechada para hash da imagem divergente, caminhos inseguros e manifesto
  inválido.

## Comandos executados

```text
python -m py_compile scripts/audit_unity_import_stage6.py tests/test_unity_import_scaffold.py
python -m pytest -q tests/test_unity_import_scaffold.py tests/test_unity_package_scaffold.py tests/test_integration_manifest.py
python scripts/audit_unity_import_stage6.py
```

O harness criou quatro projetos Unity temporários: dois positivos, um com hash
modificado e um com prefab manual real criado por `PrefabUtility` antes da
importação. Os caminhos temporários não foram persistidos.

## Resultados reais

- Unity positivo: retorno `0`, `UNITY_NATIVE_IMPORT_STAGE6=SUCCESS`;
- Sprite: criado e recarregado pelo `AssetDatabase`;
- ScriptableObject: criado e recarregado com identidade, pivô e polígono;
- PolygonCollider2D: um path com quatro pontos validado no prefab recarregado;
- prefab: `SpriteRenderer`, collider e marker validados;
- repetição em projeto limpo: relatório semântico idêntico;
- hash de imagem alterado: retorno `1`, falha explícita e zero recursos gerados;
- prefab manual: retorno `1`, conteúdo manual bloqueado e zero recursos gerados;
- nenhum caminho absoluto, IP ou identificador de máquina ficou nos artefatos.

## Falhas reais encontradas e correções

1. A primeira compilação real falhou com `CS1012` porque `TrimStart('./')`
   usava um literal C# inválido. Foi corrigido para `TrimStart('.', '/')`.
2. A segunda execução criou os assets, mas o marker do prefab foi recarregado
   como `m_Script: fileID: 0`. A causa foi o `MonoBehaviour` estar como tipo
   secundário no arquivo do ScriptableObject. Ele foi separado em
   `NeoEngGeneratedMarker.cs`.
3. A fixture final repetiu os casos positivos e negativos após as correções.
   Os logs sanitizados das falhas estão preservados como
   `initial-failure-csharp-compile.log` e
   `initial-failure-marker-script-binding.log`.

## Artefatos

O índice com tamanhos e SHA-256 está em:
`docs/evidence/artifacts/unity-import-stage6-2026-08-16/stage6-index.json`.

O conjunto contém o manifesto de fixture, relatório positivo, repetição,
relatórios negativos, logs positivos/negativos e logs das duas falhas reais.

## Regressão e limitações

- os testes focados da integração e do contrato continuam aprovados;
- a suíte completa e os gates globais serão executados antes do commit;
- a importação atual gera um `PolygonCollider2D` por sprite usando o polígono
  principal; decomposição/colisores compostos não são declarados concluídos;
- a sincronização por hash de metadados, preservação de overrides e rollback
  continuam nas etapas 7 e 9;
- a validação foi realizada no Unity `6000.5.7f1`; outras versões requerem
  execução própria.

## Decisão

**APROVADO LOCALMENTE NO ESCOPO DA ETAPA 6.** A etapa só deve ser promovida
após regressão completa, revisão, commit, push e CI remoto aprovados.