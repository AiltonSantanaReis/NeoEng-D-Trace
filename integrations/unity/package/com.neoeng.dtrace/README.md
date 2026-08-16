# NeoEng D-Trace — Unity UPM source-only package

Este pacote é o adaptador nativo Unity da Etapa 5. Ele é distribuído como um
pacote UPM local ou Git e contém somente fontes C#, assemblies `.asmdef`,
metadados e documentação. Não contém DLLs, executáveis, bibliotecas nativas,
download automático ou dependência de marketplace.

## Escopo aprovado nesta etapa

- identidade estável `com.neoeng.dtrace`, versão `0.2.0`;
- assembly Runtime com o contrato comum de manifesto;
- assembly Editor separado, carregado somente pelo Unity Editor;
- diagnóstico por menu e por `-executeMethod` em modo batch;
- verificação de resolução UPM, versão, assemblies, contrato e política
  source-only.

A importação de `Sprite`, `ScriptableObject`, `PolygonCollider2D` e prefabs
pertence à Etapa 6 e não é declarada implementada por este pacote.

## Instalação local

No `Packages/manifest.json` do projeto Unity, adicione uma referência UPM
local para este diretório:

```json
"com.neoeng.dtrace": "file:../../caminho/para/integrations/unity/package/com.neoeng.dtrace"
```

Também é possível referenciar o diretório do pacote por Git. A instalação real
e o diagnóstico batch são reproduzidos pelo harness da Etapa 5 e registrados
em `docs/evidence`.

## Diagnóstico

No editor: `NeoEng D-Trace > Diagnostics > Validate UPM Package`.

Em modo batch:

```text
-executeMethod NeoEng.DTrace.Editor.PackageDiagnostics.RunHeadless
```

O método falha fechado quando a identidade, a versão, os assemblies ou a
política source-only não correspondem ao contrato.
