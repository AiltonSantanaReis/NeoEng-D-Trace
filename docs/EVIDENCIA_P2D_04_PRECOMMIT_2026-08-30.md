# Evidência P2D-04 — precommit

**Contrato:** P2D-04 — persistência, recovery, preview, exportação e coordenadas
**Data:** 30/08/2026
**Estado:** READY FOR OWNER PRECOMMIT ACCEPTANCE — não é aceite de commit nem encerramento da etapa

## 1. Fronteira comprovada

O lote altera somente os seguintes arquivos de produto e evidência:

- `docs/EVIDENCIA_P2D_04_PRECOMMIT_2026-08-30.md`
- `docs/DECISAO_P2D_04_PERSISTENCIA_RECOVERY_PREVIEW_EXPORT_COORDENADAS_2026-08-30.md`
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

Não foram alterados C3, os contratos G/V/B, o `CanvasView` legado ou as linhas
fora do escopo P2D-04. Arquivos untracked históricos existentes não fazem parte
desta evidência nem foram limpos.

## 2. Checks obrigatórios

| Check | Resultado |
|---|---:|
| Python 3.11.9 / PySide6 6.10.1 / pytest 9.1.1 | PASS |
| Compilação dos módulos Python alterados | PASS |
| Testes P2D-04 dedicados | 7 passed |
| Suítes relacionadas | 56 passed |
| Suíte completa | 1840 passed / 2 skipped / 0 failed |
| `git diff --check` | PASS |
| Varredura de caminhos pessoais, segredos e credenciais no lote | 0 findings |
| Godot 4.7 materialização + render nativo | PASS / exit 0 |
| Unity 6000.5.7f1 materialização + render nativo | PASS / exit 0 |

A suíte completa produziu uma warning de depreciação Qt em um teste existente;
ela não falhou e não pertence ao código P2D-04.

## 3. Cobertura funcional P2D-04

- Save V1/V2 permanece determinístico e V1 só é convertido por ação explícita.
- Save mantém o último documento estruturalmente válido em recovery sidecar.
- Recovery é explícito, não muta o arquivo atual e não substitui o documento sem Save.
- Falha de load/reload preserva o documento ativo e informa repair/recovery.
- Estado ativo, salvo e exportado são distintos; exportação usa o documento ativo.
- Asset ausente/adulterado bloqueia exportação dependente, com mensagem acionável.
- `source_path` local é removido do payload portátil; somente referência relativa/hash é publicada.
- O usuário escolhe Generic, Godot ou Unity no editor.
- O payload preserva layers, groups, objects, transforms, pivot, flip, z/order,
  câmera, parallax e sockets dentro do contrato suportado.
- O mapeamento Unity Y-up é explícito; Godot mantém Y-down; não há conversão implícita.

## 4. Validação Godot

Fixture assimétrica real: PNG não quadrado, posição X/Y distinta, rotação não
nula, escala não uniforme, pivot fora do centro, flip em um eixo, Z não nulo,
duas layers, grupo e parallax.

- Versão: `4.7-stable (official)`
- Diagnose/importação: PASS
- Câmera, posição, zoom e `Parallax2D`: PASS
- Objeto, rotação, escala/flip e pivot: PASS
- Captura nativa Windows/GPU: `14400` pixels renderizados
- Exit code: `0`

Artefatos externos da execução final:

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `godot-validation-report.json` | 3898 | `e41168ee168a8627740f4d0afcc8643042caeb62d7647e50e7e83ce40a6df8bd` |
| `godot-professional-capture.png` | 4414 | `7c86374e401b67c6cb41514cc30bfaead3174126ed6fb2034ceb0f2541345692` |

## 5. Validação Unity

- Versão: `6000.5.7f1`
- Importação como Sprite: PASS
- Câmera ortográfica e coordenadas Y-up: PASS
- Objeto, rotação normalizada, escala/flip e pivot visual: PASS
- Componente de parallax profissional: PASS
- Captura nativa por `Camera.Render`/D3D11: `266` pixels renderizados
- Exit code: `0`

Artefatos externos da execução final:

| Artefato | Bytes | SHA-256 |
|---|---:|---|
| `unity-validation-report.json` | 817 | `a3bfa03766a9e9be88a286ee7930f4724e4648143f87ecd7ddf32c3d33e99379` |
| `unity-professional-capture.png` | 5051 | `4f96feb7a3ca0681538a02108be0d4a1007c21429dbdf2d3783132bbce8d829c` |
| `unity-professional-validation-result.txt` | 92 | `1fa65e6b7279b6aee6682ddb780ee3897ba8fd56940331b6ea36804a74de3aae` |

## 6. Disposição

Os checks técnicos e as validações de engine estão verdes. Esta evidência não
autoriza automaticamente o commit: falta a revisão do proprietário e a mensagem
explícita `P2D-04 PRECOMMIT ACCEPT` antes do stage/commit técnico, seguida da
requalificação pós-commit e do ciclo remoto previsto pela governança.
