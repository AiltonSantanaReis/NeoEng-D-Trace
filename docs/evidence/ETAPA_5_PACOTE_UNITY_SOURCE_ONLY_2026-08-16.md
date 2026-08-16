# Evidência — Etapa 5: pacote Unity source-only

## Identificação

- Etapa: 5 — Pacote Unity source-only
- Estado: validação local real concluída; promoção ainda depende do fluxo de revisão/merge
- Data: 2026-08-16
- Pacote: `com.neoeng.dtrace` versão `0.2.0`
- Engine real: Unity `6000.5.7f1`

## Objetivo e escopo

Foi criado um pacote UPM local/Git sem DLLs, executáveis ou bibliotecas nativas,
com assembly Runtime, assembly Editor e metadados versionados. O assembly Editor
expõe diagnóstico por menu e por `-executeMethod` em modo batch.

A importação de Sprite, ScriptableObject, PolygonCollider2D e prefabs não foi
implementada nesta etapa; permanece explicitamente na Etapa 6.

## Implementação

- `integrations/unity/package/com.neoeng.dtrace/package.json` com identidade UPM
  e versão `0.2.0`;
- `Runtime/NeoEngDTrace.Runtime.asmdef` e `Runtime/PackageIdentity.cs`;
- `Editor/NeoEngDTrace.Editor.asmdef` referenciando o Runtime;
- `Editor/PackageDiagnostics.cs` com diagnóstico do pacote resolvido, versão,
  assemblies, contrato e política source-only;
- `README.md` com instalação local/Git e limite explícito da Etapa 5;
- `scripts/audit_unity_package_stage5.py` com duas instalações positivas e um
  caso negativo real.

Os arquivos `.meta` foram gerados pelo Unity durante a importação local e são
metadados de fonte do pacote; não há artefatos nativos ou executáveis.

## Comandos executados

```text
python -m py_compile scripts/audit_unity_package_stage5.py tests/test_unity_package_scaffold.py
python -m pytest -q tests/test_unity_package_scaffold.py tests/test_integration_manifest.py
python -m black --check scripts/audit_unity_package_stage5.py tests/test_unity_package_scaffold.py
python scripts/audit_unity_package_stage5.py
```

O harness criou projetos Unity temporários e referenciou o pacote por `file:`
no `Packages/manifest.json`. Os caminhos temporários não foram persistidos.

## Resultados reais

- testes Python focados: `28 passed`;
- Unity positivo: retorno `0`, manifesto UPM resolvido e compilado;
- assembly Editor: carregado e executado por `-executeMethod`;
- diagnóstico: `UNITY_NATIVE_PACKAGE_STAGE5=SUCCESS`;
- repetição em projeto limpo: retorno `0` e relatório byte a byte idêntico;
- caso negativo: arquivo `forbidden.exe` injetado numa cópia temporária;
  retorno `1`, `UNITY_NATIVE_PACKAGE_STAGE5=FAILURE` e check `source_only`
  reprovado;
- política source-only positiva: aprovada sem extensões nativas/executáveis;
- nenhum caminho absoluto, endereço IP ou identificador de máquina ficou nos
  artefatos persistidos.

## Falhas reais encontradas e correções

1. A primeira execução falhou porque o caminho `file:` foi calculado relativo à
   raiz do projeto. O Unity resolve esse campo a partir de `Packages/`; o
   harness foi corrigido para calcular a referência a partir desse diretório.
2. A segunda execução alcançou a compilação real e falhou com ambiguidade entre
   `UnityEditor.PackageManager.PackageInfo` e `UnityEditor.PackageInfo`. O
   namespace do tipo foi qualificado por alias explícito.
3. A terceira execução passou nos casos positivo, repetido e negativo. As duas
   falhas anteriores estão preservadas nos logs sanitizados
   `initial-failure-path-resolution.log` e `initial-failure-editor-compile.log`;
   eles não são tratados como sucesso.

## Artefatos

O índice com tamanhos e SHA-256 está em:
`docs/evidence/artifacts/unity-package-stage5-2026-08-16/stage5-index.json`.

O conjunto inclui o relatório final, relatório repetido, relatório negativo,
`package.json` e cinco logs Unity sanitizados.

## Limitações e riscos residuais

- não há importação de assets ou geração de colisores Unity nesta etapa;
- a validação foi realizada no Unity `6000.5.7f1`; compatibilidade com outras
  versões ainda requer execução própria;
- a sincronização por hash, overrides, dry-run e rollback permanecem nas etapas
  7 e 9;
- não foi feita validação visual do Inspector, pois pertence ao escopo da Etapa
  6.

## Decisão

**APROVADO LOCALMENTE NO ESCOPO DA ETAPA 5.** A etapa só deve ser promovida no
fluxo do repositório após a revisão, regressão completa e CI correspondente.