# Mudança controlada — consumo nativo do runtime de partículas

**Estado:** `TECHNICAL_CHECKPOINT_PASS`
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`
**Data:** 2026-09-11
**Autoridade:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Decisão de continuidade:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`
**Decisão de revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`
**Base auditada:** `b20f2f1fa08824e87b8ddb090a893c3d4afb3f7a`

**Fechamento técnico:** `73b7fccd61f2673b6c5479581cb1645912755e22`,
requalificado junto da exportação profissional V2 em
`docs/evidence/EVD_POST_E13_PARTICLE_SCENE_EXPORT_NATIVE_20260911.md`.

## Motivo e evidência de entrada

O checkpoint anterior comprovou autoria, preview determinístico, persistência
e o contrato canônico do sidecar, mas deixou `REQ-F09-RUNTIME-EQUIVALENCE` em
`PENDING_EVIDENCE`. A auditoria real dos adaptadores executou Godot 4.7 e Unity
6000.5.7f1 e demonstrou que ambos apenas validavam o arquivo e criavam um
registro de metadados para `runtime.particles`; nenhum emissor era consumido
por um renderer de runtime. O relatório de entrada foi preservado em
`artifacts/post-e13-particles-runtime-baseline-20260911-v3/stage8-report.json`.

## Objetivo controlado

Consumir o mesmo sidecar determinístico em Godot e Unity, criar um sistema de
partículas nativo por engine, avançar o ciclo de vida em passos fixos e expor
contagem/estado observáveis para o harness. A prova deverá incluir:

- leitura com hash e validação fail-closed do sidecar já vinculado ao bundle;
- emissão, burst, taxa, vida, velocidade, espalhamento, aceleração e limite;
- avanço determinístico e remoção por tempo de vida;
- saída visual rasterizada por renderer real do engine, quando o ambiente
  permitir captura;
- falha controlada para sidecar ausente, inválido ou divergente;
- execução nativa real em Godot e Unity, persistência dos artefatos e hashes.

## Limites e contratos preservados

- Não reabre nem altera o E13.
- Não altera `SceneAuthoringDocumentV2`, a serialização legada ou o preview do
  editor nesta mudança.
- Não transforma o exportador de autoria `godot`/`unity` em um exportador que
  silenciosamente descarte partículas; a decisão fail-closed desse exportador
  permanece inalterada.
- Não remove assets, sidecars, fixtures ou findings históricos.
- O algoritmo do runtime continua o v1 já publicado: LCG de 32 bits, emissão
  no passo, integração de aceleração antes da posição e descarte quando
  `age < lifetime` deixa de ser verdadeiro.
- Se um engine não puder ser executado ou renderizado no host, o estado correto
  será `PENDING_EVIDENCE`; não haverá promoção por inspeção de código.

O checkpoint foi fechado: Godot 4.7 e Unity 6000.5.7f1 consumiram o sidecar
v1, avançaram três passos fixos, produziram sete partículas e passaram os
guards de sidecar ausente/divergente. A extensão V2 autoria→exportação é
registrada separadamente para não misturar os dois contratos.

## Análise de impacto

**Módulos afetados:** adaptador Godot de runtime, script de sistema de
partículas Godot, gerador/editor adapter Unity, componente runtime Unity,
harness de auditoria nativa, testes de contrato e evidência pós-E13.

**Requisitos/features:** `REQ-F08-PARTICLE-RENDER`, `REQ-F08-PARTICLE-REPLAY`,
`REQ-F09-PLAYBACK-CONTROL`, `REQ-F09-RUNTIME-EQUIVALENCE`, `FX-002`, `FX-005`,
`FX-006`, `FEAT-PARTICLE-EMIT`, `FEAT-PARTICLE-REPLAY` e
`CMP-PARTICLE-EMITTER`.

**Riscos principais:** divergência entre o passo Python e o passo nativo,
render invisível em modo sem GPU, emissão duplicada pelo sistema nativo,
desserialização permissiva do JSON e falsa promoção de uma captura de
metadados como prova visual.

**Proteções:** port do algoritmo com estado explícito, sistema nativo
alimentado por estado determinístico, testes de contagem/limite, validação
estrita dos campos, sidecar e bundle hashados, execução headless dos dois
engines, captura PNG quando suportada e preservação do baseline anterior.

**Migração:** nenhuma; o bundle v1 e o sidecar v1 permanecem compatíveis. A
matriz de capability só poderá declarar `native` para partículas no novo
artefato depois de os dois engines produzirem os marcadores funcionais e o
teste de falha passar.

## Critério de saída

O critério de saída foi atendido pela evidência vinculada, que identifica
commit, testes, build/engine, artefatos, hashes, resultado observado, falhas
deliberadas e limitações. A revisão humana final continua deferida até os
demais blocos previstos na decisão formal.
