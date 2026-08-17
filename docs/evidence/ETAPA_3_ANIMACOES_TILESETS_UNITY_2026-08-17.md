# Etapa 3 — animações e tilesets nativos no adaptador Unity

Status: **APROVADA**.

## Escopo comprovado antes da implementação

- O núcleo Python já exportava os payloads versionados `neoeng-d-trace-animation` e `neoeng-d-trace-tileset`.
- O adaptador Godot já possuía suporte nativo a animação e TileSet; essa parte não foi duplicada nem alterada nesta etapa.
- O adaptador Unity cobria Sprite, ScriptableObject, PolygonCollider2D e prefab, mas não importava os payloads opcionais de animação e tileset.

## Implementação Unity

- Animações geram sprites por frame, metadata nativo, `AnimationClip`, `AnimatorController`, prefab e driver de colisão por frame.
- A troca de frame atualiza o path do `PolygonCollider2D` conforme o metadata correspondente.
- Tilesets geram sprites, `Tile` assets, `Grid`, `Tilemap`, `TilemapRenderer`, metadata e prefab.
- A colisão do tileset é gerada como `PolygonCollider2D` composto no prefab, com um path por tile que possui colisão. As coordenadas são convertidas para o espaço Unity usando tile size e pixels por unidade.
- A repetição do import compara fingerprint, cardinalidade e pontos dos paths físicos esperados; divergência manual é bloqueada.
- O runtime permanece source-only: o driver de animação resolve o componente 2D por reflexão para não impor dependências de módulos Unity ao assembly runtime.

## Limitação da plataforma e decisão técnica

O Unity `6000.5.7f1` recusou `Sprite.OverridePhysicsShape` para os Sprites criados programaticamente com `Sprite.Create`, inclusive usando `SpriteMeshType.Tight` e antes da serialização do asset. Isso é uma limitação da API/forma de criação do Sprite, não uma falha do Unity nem uma falha funcional do projeto.

A chamada recusada não é usada como evidência. A implementação não depende de shape implícito inexistente no Sprite: grava os paths físicos em um `PolygonCollider2D` composto do prefab do tileset e valida esses paths diretamente.

## Execução real e gates aprovados

Versão Unity detectada: `6000.5.7f1`.

O harness criou três projetos Unity temporários e executou o pacote nativo:

| Gate | Resultado observado |
|---|---|
| Animação nativa (`AnimationClip`, controller, prefab e metadata) | PASS |
| Colisão acompanha troca de frame | PASS |
| Tileset nativo (`Grid`, `Tilemap`, `Tile` assets e prefab) | PASS |
| Paths físicos do colisor composto por tile | PASS |
| Repetição sem alteração | PASS (`UNCHANGED`) |
| Divergência manual no prefab de animação | bloqueada |
| Divergência manual no prefab de tileset | bloqueada |
| Warning `Not allowed to override physics shape` no rerun final | 0 ocorrências |

Marcadores emitidos pelo Unity no rerun final:

- `UNITY_STAGE3_ANIMATION_NATIVE=PASS`
- `UNITY_STAGE3_FRAME_COLLISION=PASS`
- `UNITY_STAGE3_TILESET_NATIVE=PASS`
- `UNITY_STAGE3_TILE_COLLISION=PASS`
- `UNITY_STAGE3_REPEAT=PASS`
- `UNITY_STAGE3_ANIMATION_CONFLICT_BLOCKED=PASS`
- `UNITY_STAGE3_TILESET_CONFLICT_BLOCKED=PASS`

## Evidência final reproduzível

- Harness: `scripts/audit_unity_animation_tileset_stage3.py`
- Relatório: `docs/evidence/artifacts/native-animation-tileset-stage3-rerun3-2026-08-17/stage3-report.json`
- Índice: `docs/evidence/artifacts/native-animation-tileset-stage3-rerun3-2026-08-17/stage3-index.json`
- Logs sanitizados: `unity-stage3-positive.log`, `unity-stage3-animation-conflict.log` e `unity-stage3-tileset-conflict.log` no mesmo diretório.

Hashes finais registrados no índice:

- `stage3-report.json`: `0a810673cecd6903f1b06f4249717534868a3354759bb46e9505ff15dbf6c743`
- `unity-stage3-positive.log`: `54fac206a4123ba0208ef118f526bc3fe598681ce9c0797e5fc49efb4bbddc18`
- `unity-stage3-animation-conflict.log`: `fb3396e354484045b30cf591b1f58b4c643600fb847387b4d954208911f341b6`
- `unity-stage3-tileset-conflict.log`: `1cb1a908572ac7a717e2e7730371e83ff612adf22a9302e6bdd5ee191d75fbf2`

A verificação independente confirmou que bytes e SHA-256 coincidem com o índice, que não há caminhos Windows ou identificadores de máquina/processo sem sanitização e que o rerun não contém o warning recusado pela API.

## Falhas históricas preservadas

As tentativas abaixo permanecem no repositório para rastreabilidade e não foram convertidas em PASS:

- `docs/evidence/artifacts/native-stage3-regression-unity-basic-2026-08-17/`
- `docs/evidence/artifacts/native-stage3-regression-unity-basic-rerun-2026-08-17/`
- `docs/evidence/artifacts/native-stage3-regression-unity-basic-rerun2-2026-08-17/`
- `docs/evidence/artifacts/native-stage3-regression-unity-basic-rerun3-2026-08-17/`
- `docs/evidence/artifacts/native-stage3-regression-unity-basic-rerun4-2026-08-17/` — regressão básica final observada como PASS.
- `docs/evidence/artifacts/native-animation-tileset-stage3-2026-08-17/` — contém falhas reais de compilação/parser e a primeira execução opcional.
- `docs/evidence/artifacts/native-animation-tileset-stage3-rerun-2026-08-17/` — marcadores positivos, porém com warning da API limitada.
- `docs/evidence/artifacts/native-animation-tileset-stage3-rerun2-2026-08-17/` — demonstrou que o Sprite criado programaticamente não possuía physics shape.

## Regressão e limites declarados

- Suíte completa: `1189 passed, 2 skipped, 10 warnings`.
- Cobertura total de branch: `90,72%`, acima do gate de 90%.
- Testes focados de contratos, exportadores, integridade e privacidade: `33 passed`.
- Flake8, Black e isort do harness: PASS.
- Baseline integrity: `1369 files`, verificado.
- Godot não foi alterado nesta etapa porque o suporte nativo já existia e permaneceu coberto pelo estado anterior.
- A transação global de múltiplos manifestos continua reservada à Etapa 4 e não foi antecipada.