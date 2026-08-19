# NeoEng D-Trace — Unity UPM source-only package

Este pacote é o adaptador nativo Unity da Etapa 5. Ele é distribuído como um
pacote UPM local ou Git e contém somente fontes C#, assemblies `.asmdef`,
metadados e documentação. Não contém DLLs, executáveis, bibliotecas nativas,
download automático ou dependência de marketplace.

## Escopo aprovado na Etapa 5

- identidade estável `com.neoeng.dtrace`, versão `0.3.0`;
- assembly Runtime com o contrato comum de manifesto;
- assembly Editor separado, carregado somente pelo Unity Editor;
- diagnóstico por menu e por `-executeMethod` em modo batch;
- verificação de resolução UPM, versão, assemblies, contrato e política
  source-only.

## Importação da Etapa 6

O pacote também contém o importador Unity da Etapa 6. Ele lê manifestos Unity
válidos em `Assets`, cria `Sprite`, `NeoEngImportedSpriteMetadata`,
`PolygonCollider2D` e prefabs controlados em `Assets/NeoEngGenerated`, e valida
os recursos gerados por APIs do Unity Editor. O importador confere o hash da
imagem, rejeita caminhos inseguros, bloqueia conteúdo manual no diretório
gerado e falha fechado para manifestos inválidos.

Sincronização incremental por hash, overrides e rollback permanecem nas etapas
posteriores; esta etapa não declara essas capacidades.

## Instalação local

No `Packages/manifest.json` do projeto Unity, adicione uma referência UPM
local para este diretório:

```json
"com.neoeng.dtrace": "file:../../caminho/para/integrations/unity/package/com.neoeng.dtrace"
```

Também é possível referenciar o diretório do pacote por Git. A instalação real
o diagnóstico batch e a importação são reproduzidos pelos harnesses das etapas 5 e 6 e registrados
em `docs/evidence`.

## Diagnóstico

No editor: `NeoEng D-Trace > Diagnostics > Validate UPM Package`.

Em modo batch:

```text
-executeMethod NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless
```

O método falha fechado quando a identidade, a versão, os assemblies ou a
política source-only não correspondem ao contrato.
