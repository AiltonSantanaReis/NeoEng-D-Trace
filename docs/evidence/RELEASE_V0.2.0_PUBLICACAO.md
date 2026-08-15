# Evidência de publicação — NeoEng-D-Trace v0.2.0

**Estado:** RELEASE OFICIAL PUBLICADA
**Data:** 15 de agosto de 2026
**Commit-fonte:** `1feb2d134cea8c5a1d2346665280b31c051f5574`
**Tag:** `v0.2.0`
**URL:** https://github.com/AiltonSantanaReis/NeoEng-D-Trace/releases/tag/v0.2.0

## Artefatos publicados

| Artefato | SHA-256 | Tamanho |
|---|---|---:|
| `NeoEng-D-Trace-0.2.0-win64-portable.zip` | `fa48c8f6596b0d36c7ecbb0c6d80be3f33e0bdd9f9200d54a78b39cf6e4c6b15` | 122552280 |
| `NeoEng-D-Trace-0.2.0-win64.msi` | `0550b30e4f3c954d8e8b2d459f0675dfba504ae729ec49d766501681b33f43c8` | 103034880 |
| `NeoEng-D-Trace-0.2.0-win64.manifest.json` | `e4c9281614995626d84098791821d0b9d812be9e0a377e02599483bf75d81ab3` | 725 |
| `NeoEng-D-Trace-0.2.0-validation-evidence.zip` | `10b1ec07a1d12bd56897e3005319aa45b739f1a5c04f4ef8ca68ef75e7e9a005` | 18587 |
| `SHA256SUMS.txt` | publicado junto com os artefatos | 502 |

## Validações reais

- Build portátil gerada no Windows/Python 3.11.9 com PyInstaller 6.22.0.
- WiX 4.0.6 restaurado pelo manifesto e MSI per-user gerado para Windows x64.
- Smoke do bundle: CLI, projeto versionado, JSON, GLB, perfis Godot/Unity e GUI: `SUCCESS`.
- MSI: instalação exit code `0`, execução instalada, exportações, GUI, desinstalação exit code `0` e preservação do estado do usuário.
- CI pós-merge `31907891488`: Linux e Windows concluídos com sucesso.

## Limitações declaradas

- GUI, CLI e MSI estão `NotSigned`; nenhum certificado foi inventado ou aplicado.
- `R-014` permanece deferido para futuras builds/releases.
- `R-015` permanece com formalização jurídica, licenciamento e atribuições futuras; o ícone gerado por IA foi autorizado pelo proprietário.
- A publicação oficial não constitui parecer jurídico nem certificação de conformidade.
