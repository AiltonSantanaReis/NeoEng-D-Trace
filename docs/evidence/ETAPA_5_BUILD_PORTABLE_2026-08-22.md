# Etapa 5 — build portátil pós-commit

**Estado:** build local reproduzível validada; CI, PR e merge ainda pendentes
**Commit de origem:** `96851f16cd27f7880c85f187139a98b88a9a8b84`
**Plataforma:** Windows 10 (`10.0.26200`), Python 3.11.9, PyInstaller 6.22.0
**Worktree de build:** worktree temporária limpa no commit de origem

## Comando executado

```powershell
.\scripts\build_windows.ps1 -OutputRoot release-stage5-clean
```

O script oficial exigiu árvore limpa, compilou o executável com PyInstaller,
executou `tools/validate_portable_release.py` e criou o ZIP portátil. Nenhum
arquivo da árvore principal foi usado como fonte suja da build.

## Resultado funcional

- PyInstaller: PASS.
- Smoke portátil: PASS (`SUCCESS`).
- Checks do smoke: 11, incluindo CLI, projeto headless, JSON, GLB, perfis
  Godot/Unity, GUI open/close e diretório de estado do usuário.
- Empacotamento: PASS.
- Arquivo do pacote: 355 arquivos.
- Árvore da worktree de build: limpa.

## Hashes dos artefatos reais

Os arquivos permaneceram na worktree temporária de build e não foram copiados
para o repositório. Os hashes abaixo permitem confrontar o pacote recebido
com a origem versionada.

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `NeoEng-D-Trace-0.3.0-win64-portable.zip` | 124324444 | `00d8635121564f198d1503eb723ad68e9ab50c45c1d75d8287f0eff0ec646977` |
| `NeoEng-D-Trace-0.3.0-win64-portable.zip.sha256` | 106 | `4c8797079fb5ff3346b821734dfe77284fb004e93f694273276dc23a21b3858a` |
| `portable/NeoEng-D-Trace/release-manifest.json` | 63078 | `b0e81464d66890c680d9d429c12fe3ca4676f000b74e9505071d569c55614e92` |
| `smoke/gui-validation.jsonl` | 1922 | `de60d081c8c75becbf0b2713e1ab80a6a9cf3ca0e4c59616ab57e2157388ee5b` |
| `smoke/smoke.glb` | 956 | `084e8c4bfbb0a421df24967b36e7776824a9506a7ee353fdf45914c2f230037a` |
| `smoke/smoke.json` | 1311 | `99c2e85247bf4c9fc1b2eda2ac298c2dc56b73e9b412793db25273f4c679e58b` |

O relatório JSON e o manifest versionados no diretório de artefatos
`build-validation` registram a mesma proveniência.

## Warning residual observado

O PyInstaller reportou `Hidden import "tzdata" not found`. O warning foi
preservado no log da build e não foi transformado em PASS artificialmente. A
dependência é opcional no pacote lockado; a busca no código fonte não encontrou
uso de `zoneinfo`, `tzdata` ou `ZoneInfo`, e o smoke funcional completo passou.
O warning continua sendo uma observação de manutenção, não uma falha de
execução comprovada nesta build.

## Limitações e decisão

Esta evidência prova a build e o smoke local do commit indicado. Ainda não
prova CI, PR ou merge; esses gates permanecem obrigatórios e serão executados
separadamente. A Etapa 5 só será declarada formalmente concluída após esses
gates e a validação pós-merge.
