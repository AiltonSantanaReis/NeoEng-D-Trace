# Evidência P2D-04 — pós-commit

**Contrato:** P2D-04 — persistência, recovery, preview, exportação e coordenadas
**Data:** 30/08/2026
**Estado:** POSTCOMMIT ACCEPT — requalificação pós-commit concluída

## 1. Identificação

- Branch: `Ailton/p2d-04`
- Commit técnico: `b9e9043f98c58752e8e322a7627b4d17e145d6d3`
- Commit predecessor: `9135dc74e7d7d1429e9bae48d004651ce160fcaa`
- Mensagem: `feat(scenario): complete P2D-04 persistence and exports`
- Arquivos no commit: 14
- Push, tag e merge: não realizados

## 2. Fronteira do commit

O commit contém exatamente os 14 arquivos aprovados no PRECOMMIT ACCEPT:

- `docs/DECISAO_P2D_04_PERSISTENCIA_RECOVERY_PREVIEW_EXPORT_COORDENADAS_2026-08-30.md`
- `docs/EVIDENCIA_P2D_04_PRECOMMIT_2026-08-30.md`
- `integrations/godot/addons/neoeng_d_trace/professional_scene_importer.gd`
- `integrations/unity/package/com.neoeng.dtrace/Editor/ProfessionalSceneImportGenerator.cs`
- `integrations/unity/package/com.neoeng.dtrace/Runtime/NeoEngProfessionalParallax.cs`
- `src/core/scene_authoring_session.py`
- `src/exporters/scene_authoring_export.py`
- `src/persistence/scene_authoring_io.py`
- `src/ui/scenario_authoring_actions.py`
- `src/ui/scenario_editor_window.py`
- `tests/test_p2d_04_persistence_recovery_export.py`
- `tools/godot_professional_scene_validator.gd`
- `tools/unity_professional_scene_validator.cs`
- `tools/validate_professional_scene_exports.py`

## 3. Gates pós-commit

| Gate | Resultado |
|---|---|
| `git diff --check` | PASS |
| Tracked tree após commit | CLEAN |
| Suíte completa | `1840 passed, 2 skipped, 0 failed` |
| Warning | 1 warning de depreciação Qt já existente; não bloqueante |
| Persistência/recovery/exportação/Qt real | PASS na suíte completa |
| Privacidade do conteúdo versionado | PASS; nenhum caminho pessoal, segredo ou credencial encontrado |

A suíte foi executada com Python 3.11.9 da `.venv`, pytest 9.1.1 e coletou
1842 testes. Os dois skips pertencem a cobertura existente. O warning foi
emitido por uma construção deprecated de `QMouseEvent` em teste legado e não
é introduzido por este commit.

## 4. Validação real Godot

- Engine: `4.7-stable (official)`
- Importação: PASS
- Camera2D, posição, zoom e `Parallax2D`: PASS
- Objeto, rotação, escala/flip, pivot e Z: PASS
- Render nativo Windows/OpenGL: `14400` pixels
- Resultado: `P2D04_GODOT_VALIDATION=SUCCESS`
- Diretório lógico dos artefatos: `neoeng-p2d04-godot-postcommit-b9e9043-20260830`

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `godot-validation-report.json` | 3910 | `0598f0137ff4bd3ad83f217ad9d96b321eecca25e0c3058db80f004e94f6aca7` |
| `godot-professional-capture.png` | 4414 | `7c86374e401b67c6cb41514cc30bfaead3174126ed6fb2034ceb0f2541345692` |

## 5. Validação real Unity

- Engine: `6000.5.7f1`
- Importação como Sprite: PASS
- Camera ortográfica e coordenadas Y-up: PASS
- Objeto, rotação, escala/flip, pivot visual e Z: PASS
- Componente de parallax profissional: PASS
- Render nativo por `Camera.Render`/D3D11: `266` pixels
- Resultado: `P2D04_UNITY_VALIDATION=SUCCESS`
- Diretório lógico dos artefatos: `neoeng-p2d04-unity-postcommit-b9e9043-20260830`

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `unity-validation-report.json` | 817 | `a3bfa03766a9e9be88a286ee7930f4724e4648143f87ecd7ddf32c3d33e99379` |
| `unity-professional-capture.png` | 5051 | `4f96feb7a3ca0681538a02108be0d4a1007c21429dbdf2d3783132bbce8d829c` |
| `unity-professional-validation-result.txt` | 92 | `1fa65e6b7279b6aee6682ddb780ee3897ba8fd56940331b6ea36804a74de3aae` |

## 6. Disposição formal

P2D-04 está tecnicamente fechado neste commit: persistência atômica com
recovery explícito, proteção contra exportação de assets ausentes ou alterados,
preview/exportação por alvo, publicação sem `source_path` local, mapeamento
explícito de coordenadas e materialização validada nas duas engines instaladas.

Os artefatos externos de validação permanecem fora do repositório. O repositório
mantém seus untracked locais preexistentes; nenhum untracked foi removido ou
limpo. A publicação remota continua pendente de autorização específica.
