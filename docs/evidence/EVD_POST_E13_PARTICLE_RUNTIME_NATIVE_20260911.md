# Evidência pós-E13 — consumo nativo do runtime de partículas

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`
**Data:** 2026-09-11
**Base do port v1:** `77b55dffbbe1a9dcb5f0a10ec2074918c344b3b5`
**Requalificação integrada:** `73b7fccd61f2673b6c5479581cb1645912755e22`
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`
**Mudança:** `docs/evidence/CHG_POST_E13_PARTICLE_RUNTIME_NATIVE_20260911.md`
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Decisões:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`, `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Resultado observado

O sidecar determinístico `runtime.particles` versão 1 foi consumido pelos
adapters nativos Godot e Unity. Após três passos fixos, ambos produziram sete
partículas e um emissor; o renderer Godot gerou PNG real e o Unity registrou a
mesma contagem em batchmode/nographics. Os contratos legados continuam aceitos
e a origem autorada V2 foi adicionada sem quebrar a origem runtime V1.

| Requisito/feature | Entrada e operação | Resultado | Estado |
|---|---|---|---|
| `REQ-F09-RUNTIME-EQUIVALENCE` / `FEAT-PARTICLE-EMIT` | sidecar V1, LCG, emissor, burst, taxa, vida, aceleração e três ticks | Godot=7, Unity=7, emitters=1 | `PASS` |
| `REQ-F08-PARTICLE-RENDER` / `FX-002` | runtime Godot fora da UI | `particle-runtime.png`, 1305 bytes, SHA `BF8B9C3165070096E30C6FEAD85807533B2200A28EDC4D1FDF96ACB8E344EF5F` | `PASS` |
| `REQ-F09-PLAYBACK-CONTROL` / `FEAT-PARTICLE-REPLAY` | reset/avanço do sistema nativo no harness | estado e contagem observáveis | `PASS` no contrato runtime |
| falha de integridade | sidecar removido/divergente | Python, Godot e Unity rejeitaram; Unity registrou `InvalidDataException` | `PASS` |

## Artefato primário

`artifacts/post-e13-particle-runtime-20260911-v8/post-e13-particle-runtime-report.json`
SHA-256: `0861C92E3716E07281D2E826C18335369DA8ED609F47EDD712022493B39D0464`

O relatório preservado registra `functional_status=PASS`, os hashes dos
sidecars, os marcadores dos dois engines e os guards negativos. O artefato de
entrada que demonstrava o estado metadata-only não foi removido:
`artifacts/post-e13-particles-runtime-baseline-20260911-v3/stage8-report.json`.

## Limitações mantidas

- A captura visual deste checkpoint é Godot; Unity foi executado em
  `batchmode/nographics`, portanto não há PNG Unity neste pacote.
- O sidecar V1 não possui textura, cor ou tamanho autorais; o material visual
  nativo é o default documentado.
- O checkpoint prova equivalência dos campos V1 do emissor. O caminho completo
  de autoria V2 até os exports profissionais é fechado pela evidência
  `EVD_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md`.
- A revisão humana final permanece deferida até iluminação direcional, efeitos
  orientáveis, partículas completas, tilemap/tileset e editor 3D/híbrido, como
  exigido pela decisão formal.
