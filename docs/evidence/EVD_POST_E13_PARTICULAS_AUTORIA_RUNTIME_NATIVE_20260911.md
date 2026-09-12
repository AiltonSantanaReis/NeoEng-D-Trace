# Evidência pós-E13 — autoria e preview nativo de partículas

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`
**Data:** 2026-09-11
**Base:** `Ailton/e08-renderer-20260908` em `5fe5d77aa223e248c883e22d0317d206619092c0`
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`
**Mudança:** `docs/evidence/CHG_POST_E13_PARTICULAS_AUTORIA_RUNTIME_20260911.md`
**Decisão de continuidade:** `docs/evidence/DECISAO_CONTINUIDADE_POS_E13_2026-09-10.md`
**Decisão de revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Escopo e limite

Esta evidência comprova o fluxo nativo de autoria, edição, preview e
persistência de partículas no Editor de Cenário. Ela não encerra o lote
pós-E13, não substitui revisão humana e não afirma paridade de exportação com
Godot/Unity. Os adapters não genéricos permanecem fail-closed para sistemas de
partículas autorados, conforme registrado abaixo.

## Rastreamento de requisitos e features

| Requisito/feature | Operação comprovada | Evidência | Estado |
|---|---|---|---|
| `REQ-F08-PARTICLE-RENDER` / `FX-002` / `FEAT-PARTICLE-EMIT` | emissor com taxa, vida, burst, velocidade, espalhamento e aceleração produz pixels no viewport | captura antes/depois do avanço de 750 ms e métrica de diferença | `PASS` no preview nativo |
| `REQ-F08-PARTICLE-REPLAY` / `FEAT-PARTICLE-REPLAY` | reproduzir e reiniciar a prévia | ações reais `Reproduzir partículas` e `Reiniciar prévia` | `PASS` no ciclo do editor |
| `REQ-F09-PLAYBACK-CONTROL` | controles de loop, duração e reprodução acessíveis no inspector localizado | captura de criação e captura do preview | `PASS` no editor |
| `REQ-F09-RUNTIME-EQUIVALENCE` / `FX-005` / `FX-006` | preview determinístico no editor, com limitação explícita de adapters externos | build, smoke e exportação fail-closed | `PENDING_EVIDENCE` fora do preview |

## Requalificação automatizada

- **Suíte oficial:** `.venv/Scripts/python.exe -m pytest -q`.
- **Resultado:** `2193 passed, 2 skipped, 1 warning` de `2195` testes
  coletados.
- **Focused diagnostic:** `14 passed` em conjunto que cobriu partículas e
  iluminação/efeitos orientáveis; o resultado focado não substitui a suíte
  oficial.
- **Log oficial:**
  `artifacts/post-e13-particles-20260911-fix/official-suite.log` — SHA-256
  `07B229165E43ABE9CDA80D475DF107C8F0BC25474184E7531EF0D907B7AE0648`.
- O único warning é o baseline conhecido do construtor depreciado de
  `QMouseEvent` em `tests/test_merge_coverage_authoring_contracts.py:1341`.
- A suíte sem filtros não removeu, mascarou ou reclassificou os dois skips
  locais; as limitações históricas continuam preservadas.

## Finding nativo e correção aplicada

Na primeira execução do binário de partículas, a conversão de um socket de luz
já selecionado para `VFX` deixava os campos de partículas desabilitados. O
socket podia ser adicionado, mas era persistido com `enabled=false` e valores
default; a prévia não produzia mudança observável. O finding está preservado em
`artifacts/post-e13-native-flow-20260911-particles/saved-particle-authoring-finding.ndtscene.json`.

A causa estava em `SceneAuthoringInspector._refresh_socket_type_fields`: a
habilitação dos widgets só era recalculada quando nenhum socket estava
selecionado. O commit `5fe5d77` sempre recalcula o estado conforme o tipo atual
e inicializa `socket_enabled=true` ao converter um socket não-VFX para VFX,
mantendo o estado autorado quando o socket já é VFX. O teste de regressão foi
adicionado em `tests/test_post_e13_particle_authoring.py`.

## Build oficial e proveniência

- **Método:** PyInstaller direto com
  `packaging/NeoEng-D-Trace.spec`, usando `SOURCE_DATE_EPOCH` do commit e
  `PYTHONHASHSEED=0`.
- **Manifesto:** `build/post-e13-particles-20260911-fix/continuity-provenance.json` —
  SHA-256 `9712CC07D657DCF444532793D8AE0C3A54864A0F0C7919C5FEB43D5011DF63B8`.
- **Executável:**
  `build/post-e13-particles-20260911-fix/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe` —
  SHA-256 `AC96E89A6F1215A0136CF530257DF2B96F3C4AD519A594FF1E869D081086D164`;
  8.826.362 bytes.
- **Pacote:** `build/post-e13-particles-20260911-fix/NeoEng-D-Trace-0.3.0-win64-portable.zip` —
  SHA-256 `1857459E3BAD3A773A68531ADC91144F63685B2C8106A66CCD014FBFCCA813B3`.
- **Smoke:** `build/post-e13-particles-20260911-fix/smoke/portable-smoke-report.json` —
  SHA-256 `A12DC6DF56F059D2A8889D6AFC777266E9AC3C6F8BA0E2C9B76364079E4FEE4D`,
  `SUCCESS`, 11 checks.
- O wrapper portátil oficial não foi executado porque o checkout compartilhado
  contém artefatos não rastreados preexistentes; nenhum arquivo foi removido ou
  mascarado. A limitação está no manifesto e não converte o build direto em um
  release publicado.
- O warning de empacotamento `Hidden import "tzdata" not found` foi preservado;
  não impediu o smoke.

## Fluxo nativo reproduzido

O executável acima foi iniciado e operado com cliques, teclas, rolagens,
seletores, salvar e recarregar em handles Win32 reais. O CUA não estava
disponível neste host; o fallback aprovado e declarado foi
`mouse_event`/`keybd_event`/`PrintWindow`. Não houve janela de erro observada.

**Pacote de ações:**
`artifacts/post-e13-native-flow-20260911-particles-fix/actions.jsonl` —
SHA-256 `4F06CFC567F9AFC3CC5B9A8D773EBF0E60BEF916E79DD6282F6BDF52BE386A22`.
O log possui 37 registros: `launch=1`, `click=21`, `key=9`, `capture=2`,
`maximize=1` e `scroll=3`.

### Sequência real

1. Abrir o projeto pela janela nativa e carregar
   `tests/fixtures/e08_lighting_smoke.ndtproj`.
2. Abrir o Editor de Cenário, aba `Efeitos`, selecionar o tipo `VFX` no combo
   localizado e observar `Efeito habilitado` marcado.
3. Preencher por teclado real o socket `particle-fountain`, posição `260/260/0`,
   sistema `fountain`, taxa `36`, vida `1,5` e burst `10`.
4. Rolar o inspector e acionar `Adicionar socket`; o status exibiu
   `Socket adicionado — alterações não salvas` e o viewport mostrou o marker
   VFX.
5. Acionar `Atualizar posição do socket`, depois `Reproduzir partículas`.
6. Capturar imediatamente e após 750 ms; o segundo estado mostrou partículas
   douradas visíveis no viewport.
7. Acionar `Reiniciar prévia`, salvar, recarregar e voltar ao inspector para
   confirmar os valores persistidos.
8. Fechar o binário e restaurar o fixture original; o sidecar rastreado voltou
   ao hash original.

O valor `1,5` foi inserido com vírgula por causa da entrada PT-BR. A primeira
  tentativa com ponto exibiu `15,0000`; isso foi corrigido no próprio fluxo
  nativo e fica registrado como detalhe de usabilidade/localização, não como
  falha silenciosa do produto.

## Capturas e observações objetivas

Todas as capturas foram feitas da janela nativa em `3866x2090`:

| Estado | Artefato | SHA-256 | Observação |
|---|---|---|---|
| Tipo VFX confirmado após a correção | `particle-type-select-vfx-fix-real-15927728.png` | `8C2F2A001E7CBB7CE47C17E4B429DC2C022563EE34D399055A1C3B1B69FC16D6` | combo em `VFX`, `Efeito habilitado` marcado e controles ativos |
| Socket criado | `particle-add-socket-fix-real-15927728.png` | `42375CB8E4B9063D7FB266B6A41DFAF09BE41E04B32DA6090AD035A8F089C787` | status de adição, marker e parâmetros preenchidos |
| Preview acionado | `particle-preview-play-fix-real-15927728.png` | `4B9891BB82AF43B61F582BC0E8321E0FB0D120BA25767E2E479E4F406F7B08CD` | estado `PREVIEW` |
| Preview após 750 ms | `particle-preview-after-750ms-fix-real-15927728.png` | `FC431ABC3D8EDBA3168E497B7A17009D7A6BF52D4CA609F9E352FE291186FA84` | partículas visíveis em torno do socket |
| Inspector após salvar/recarregar | `particle-inspector-scroll-up-reload-fix-real-15927728.png` | `ED55ED426AC7E7AA33B796E351C0028A72672B306F8A6639E5FEE9B81507A092` | socket VFX, sistema `fountain`, taxa 36, vida 1,5000 e burst 10 |

Para não depender apenas da aparência, a comparação entre as capturas de
preview foi medida por pixels:

- imagem completa: média absoluta `0,0187799`, pixels acima de 5:
  `0,0322032%`, acima de 20: `0,0279334%`;
- recorte do viewport: média `0,0431290`, acima de 5: `0,0739562%`, acima de
  20: `0,0641503%`;
- recorte apertado da região das partículas: média `3,4486515`, acima de 5:
  `5,9136364%`, acima de 20: `5,1295455%`.

O recorte apertado e a captura posterior mostram uma mudança observável após o
avanço do tempo; a captura de persistência confirma os valores, não apenas a
existência dos widgets.

## Persistência e integridade

O snapshot salvo está em
`artifacts/post-e13-native-flow-20260911-particles-fix/saved-particle-authoring.ndtscene.json` —
SHA-256 `7C72BB56B67176D684364B76AFDFD792AE7C80EA919B11D77811B68EB43EF535`.
Sua leitura confirmou:

```text
particle-fountain: type=vfx, effect_id=fountain, enabled=true,
                   position=(260.0, 260.0, 0.0), rotation.z=0.0, scale=1.0
particle_system fountain: fixed_dt=1/60, max_substeps=8, loop=true,
                          duration=2.0
emitter main: seed=1, emission_rate=36, lifetime=1.5, max_particles=64,
              burst=10, initial_velocity=(0,-42,0),
              velocity_spread=(34,24,0), acceleration=(0,42,0)
```

O backup antes do save e o fixture restaurado possuem SHA-256
`A0E7C7774508F006C5923EA1439393AF353174BFD938116A4B285AB3996D5035`.
O sidecar rastreado não ficou alterado após o teste; o arquivo de recovery
gerado pelo fluxo foi preservado como artefato não rastreado.

## Matriz de aceite observado

| Critério | Resultado |
|---|---|
| Cena legada abre e continua compatível | `PASS` — testes de schema e fixture |
| Conversão de socket existente para VFX habilita controles | `PASS` — teste de regressão e captura nativa |
| Criação/configuração de emissor | `PASS` — ação real, snapshot e captura |
| Partículas mudam após avanço do tempo | `PASS` — captura pós-750 ms e métrica de pixels |
| Play/reset/update no editor | `PASS` — ações reais e status nativo |
| Salvar/recarregar preserva estado | `PASS` — JSON e inspector após reload |
| Suíte, build e smoke | `PASS` — gates hashados acima |
| Equivalência de runtime Godot/Unity | `PENDING_EVIDENCE` — adapters não genéricos fail-closed |

## Limitações e próximo passo

- A simulação comprovada é o preview determinístico CPU do editor; ainda não é
  prova de equivalência GPU/engine em Godot ou Unity.
- Exportações não genéricas preservam a integridade sem aceitar silenciosamente
  sistemas de partículas não suportados: elas falham explicitamente quando os
  encontram. O exportador `Generic` é o caminho que preserva o documento.
- O teste nativo confirmou `Reiniciar prévia` como ação executável, mas o timer
  permanece ativo enquanto o preview está ligado; esse comportamento deve ser
  refinado quando o ciclo completo de runtime for tratado.
- O checkpoint não libera a revisão humana. Os blocos de tilemap/tileset e
  editor 3D/híbrido ainda precisam de implementação, testes, build e captura;
  iluminação direcional e efeitos orientáveis já têm checkpoint técnico próprio.

O próximo passo permitido é atacar o bloco de tilemap/tileset do plano, sempre
com nova leitura da governança, análise de impacto, fluxo nativo real,
persistência, build, hashes e commit separado.
