# Mudança controlada — exportação e consumo nativo de partículas autoradas

**Estado:** `IN_PROGRESS`
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`
**Data:** 2026-09-11
**Autoridade:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Continuidade:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`
**Revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Motivo e estado de entrada

O checkpoint `CHG_POST_E13_PARTICLE_RUNTIME_NATIVE_20260911` comprovou o
consumo nativo do sidecar `runtime.particles` em Godot e Unity, mas a
auditoria do encadeamento completo encontrou uma barreira deliberada no
exportador profissional: cenas V2 com `particle_systems` eram aceitas apenas
no destino `generic`. Portanto, a autoria do editor ainda não chegava aos
engines por `scene-authoring.godot.json` ou `scene-authoring.unity.json`.

Esse registro trata somente da ponte autoria V2 → exportação profissional →
importador nativo. O checkpoint anterior, seus artefatos e findings continuam
preservados e não são reescritos.

## Objetivo controlado

Permitir que uma cena V2 com partículas autoradas seja exportada para Godot e
Unity e que cada sistema seja materializado no socket VFX correspondente,
usando o mesmo algoritmo determinístico v1 do runtime nativo. O fluxo deverá:

- preservar o formato legado quando `particle_systems` estiver vazio;
- declarar `runtime_particles` como capability suportada somente nesses dois
  destinos após a validação do consumidor;
- exigir um vínculo VFX não ambíguo por `effect_id == particle_system.id`;
- validar IDs, limites, vetores, hash de origem e emissores antes de criar nós;
- respeitar posição, rotação, escala e `enabled` do socket;
- aceitar explicitamente a origem `neoeng-d-trace-scene-authoring` versão 2 no
  componente nativo, sem deixar de aceitar a origem runtime v1 já publicada;
- registrar contagem, avanço fixo e falha controlada nos harnesses nativos.

## Limites e contratos preservados

- E13 permanece fechado e histórico.
- Não há remoção de assets, sidecars, campos autorados ou fixtures existentes.
- `SceneAuthoringDocumentV2`, sua persistência e o preview do editor continuam
  compatíveis; a alteração apenas libera o consumidor que já faltava.
- Exportações `generic` continuam declarando a capacidade atual e preservando
  seus dados; exportações Godot/Unity sem partículas mantêm as chaves legadas.
- Timeline/sequence, iluminação runtime, shaders e pós-processamento continuam
  fora desta mudança e permanecem fail-closed quando o destino não os suporta.
- A fonte de verdade da simulação segue sendo o algoritmo v1: LCG, emissão por
  passo, aceleração antes da posição, limite de partículas e descarte por vida.

## IDs afetados

`REQ-F08-PARTICLE-RENDER`, `REQ-F08-PARTICLE-REPLAY`,
`REQ-F09-PLAYBACK-CONTROL`, `REQ-F09-RUNTIME-EQUIVALENCE`, `FX-002`,
`FX-005`, `FX-006`, `FEAT-PARTICLE-EMIT`, `FEAT-PARTICLE-REPLAY` e
`CMP-PARTICLE-EMITTER`.

## Análise de impacto e proteções

**Módulos:** exportador de cena V2, validador/importador Godot, runtime
particles Godot, importador Unity, runtime particles Unity, testes de contrato
e auditoria nativa.

**Riscos:** descarte silencioso de partículas, socket ambíguo, divergência de
transformação entre engines, JSON permissivo, emissão duplicada pelo renderer
nativo e confusão entre o hash da cena autora e o hash do sidecar runtime.

**Proteções:** validação estrita antes da criação da árvore, origem versionada
explicitamente (`scene-authoring` v2 ou `scenario-runtime` v1), transformação
derivada do `coordinate_mapping`, avanço manual no harness e modo automático
somente no objeto nativo em runtime.

## Compatibilidade de empacotamento

A ponte nativa amplia conscientemente os contratos de distribuição: o pacote
Godot passa a incluir `runtime_particles.gd`; o UPM Unity declara os módulos
`com.unity.modules.jsonserialize` e `com.unity.modules.particlesystem`, e a
assembly runtime referencia os módulos correspondentes. Os contratos de
scaffold foram atualizados para exigir exatamente essa identidade source-only;
nenhuma dependência anterior foi removida.

## Critério de saída

Este registro só poderá mudar para `TECHNICAL_CHECKPOINT_PASS` depois de um
commit de código auditado, testes focados, suíte oficial sem filtros, build
limpa, exportação real para os dois destinos, execução nativa, captura real
quando suportada, persistência/hash, testes negativos e limitações declaradas.
Até lá, o estado correto é `IN_PROGRESS` ou `PENDING_EVIDENCE`.
