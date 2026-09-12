# Evidência pós-E13 — iluminação direcional e efeitos orientáveis

**Estado:** `TECHNICAL_CHECKPOINT_PASS / HUMAN_REVIEW_DEFERRED`  
**Data:** 2026-09-11  
**Base:** `Ailton/e08-renderer-20260908` em `59a21a0818d27df33d1aad3acd93facb7472e445`  
**Lote:** `POST-E13-SCENE-EDITOR-ASSET-PACKS`  
**Governança:** `docs/GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`  
**Mudança:** `docs/evidence/CHG_POST_E13_DIRECIONAL_ORIENTAVEL_20260911.md`  
**Decisão de revisão humana:** `docs/evidence/DECISAO_REVISAO_HUMANA_FINAL_POS_E13_20260911.md`

## Escopo e limite

Esta evidência fecha tecnicamente o incremento de iluminação direcional e sockets
orientáveis. Ela não encerra o lote pós-E13, não substitui a revisão humana e não
declara concluídos partículas completas, tilemap/tileset ou editor 3D.

## Requalificação automatizada

- Comando: `.venv/Scripts/python.exe -m pytest -q`
- Resultado: `2186 passed, 2 skipped, 1 warning` de `2188` testes coletados.
- O warning é o baseline já conhecido do construtor depreciado de `QMouseEvent`
  em `tests/test_merge_coverage_authoring_contracts.py:1341`.
- Os sete testes novos de `tests/test_post_e13_directional_orientable.py`
  passaram, além dos contratos de iluminação, preview, persistência e adapters.

## Build oficial e proveniência

Build limpa produzida no checkout pós-commit:

- Manifesto: `build/post-e13-directional-20260911/continuity-provenance.json`
- Executável: `build/post-e13-directional-20260911/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`
- SHA-256 do executável: `A561FAD41D048623D03BDFAF0E5EEE13916AC81A591F10E9E6BCD305A0C53B7D`
- Tamanho do executável: `8.809.664` bytes.
- Pacote: `build/post-e13-directional-20260911/NeoEng-D-Trace-0.3.0-win64-portable.zip`
- SHA-256 do pacote: `B9145E56791EF5BD9CC3DEDE3D625C7B52EC0E7589904FF66E047CEADD28EBC0`
- Smoke: `build/post-e13-directional-20260911/smoke/portable-smoke-report.json`,
  `SUCCESS`, 11 checks; o aviso de import oculto `tzdata` foi preservado.

O manifesto registra `source_commit=59a21a0818d27df33d1aad3acd93facb7472e445`,
branch `Ailton/e08-renderer-20260908` e o hash do registro no instante da build.

## Fluxo nativo reproduzido

O binário foi iniciado duas vezes com o executável acima e operado por handles
Win32 reais. O log completo contém 59 registros (`launch=2`, `click=32`,
`key=16`, `drag=1`, `maximize=2`, `list=6`) em
`artifacts/post-e13-native-flow-20260911-directional/actions.jsonl`.

### Luz direcional

1. Abrir projeto por menu real e carregar `tests/fixtures/e08_lighting_smoke.ndtproj`.
2. Abrir o Editor de Cenário e a aba `Efeitos`.
3. Alterar `Tipo de luz` de `Ponto` para `Direcional` e confirmar em
   `Atualizar posição do socket`.
4. Alterar `Rotação Z do socket` para `90°` e depois para `270°`.
5. Observar o gizmo: a haste/seta muda de orientação no viewport e o inspetor
   exibe os valores efetivamente aplicados.

Capturas principais, todas em `3866x2090` e hashadas:

| Estado | Captura | SHA-256 |
|---|---|---|
| Editor maximizado / PT-BR | `resume-maximize-scenario-18221036.png` | `8C1D2289640C40B2BF9161BAF5B40237926E0ED25AC7EC77E90AECC9FF9F54A5` |
| Tipo direcional confirmado | `resume-directional-kind-commit-18221036.png` | `BE33FC21C7EBCA5BD439913FB7500B1376BE1F416D7503A7DA2C03F3522F7BE4` |
| Direção em 90° | `resume-directional-rotation-commit-18221036.png` | `3C07EF2200F894AA95E9EC75F30427A859FE771A1B517AA99A1088C7BFE33874` |
| Direção em 270° | `resume-rotation-270-commit-18221036.png` | `661F40FAFF8C2DBDF756DA4F023BDDCDFF1ABF46BB2F4F58ABB9553F7907042B` |

A comparação objetiva entre as capturas de 90° e 270° produziu diferença média
absoluta de `4,0987` por canal, `5,9900%` de pixels alterados acima de limiar 5,
e, no recorte do viewport, diferença média `9,6183` com `14,0731%` de pixels
alterados. Isso comprova mudança observável de renderização, sem depender apenas
do texto do inspetor.

### Efeito orientável

1. Selecionar `VFX` no menu localizado.
2. Criar o socket `dust-vfx`, com posição `80/170/0` e rotação inicial `45°`.
3. Selecionar o novo socket no combo e confirmar a miniatura/indicador roxo no
   viewport.
4. Arrastar o handle circular real do gizmo. A rotação mudou para `-56,6585°`
   e o status nativo informou `Socket orientado — alterações não salvas`.
5. Atualizar, salvar, recarregar e confirmar os mesmos valores.

Capturas principais:

| Estado | Captura | SHA-256 |
|---|---|---|
| Menu VFX localizado | `vfx-type-menu-open-real-5310612.png` | `DCDCD80AFEC05308FE15DAC9B76992CCFF32A63E0462023A14AF0E9138A2E97C` |
| Socket criado | `vfx-add-socket-real-18221036.png` | `B065E89D3142375589D4017989F6645C6C1A4AE7DB2AC67A49B675D511944F5C` |
| Arraste real do handle | `vfx-rotation-handle-drag-real-18221036.png` | `4CFEDFFFC8A2A2A13463E97D01D918BF03538B0FEA6BAD81983757099580294C` |
| Recarregamento persistido | `reload-saved-directional-vfx-real-18221036.png` | `3A965BA181E03ECC8E0A94588486B1DD4186C6321DAD22720372DBE299D723AC` |

O documento salvo usado na prova está em
`artifacts/post-e13-native-flow-20260911-directional/saved-e08_lighting_smoke.ndtscene.json`.
Sua leitura confirmou:

```text
key-light: type=light, kind=directional, rotation.z=270.0,
           position=(160.0, 220.0, 0.0)
dust-vfx:  type=vfx, effect_id=default, rotation.z=-56.6585,
           position=(80.0, 170.0, 0.0)
```

## Integridade do fixture e encerramento da execução

O sidecar original do fixture foi restaurado após a prova de recarregamento e o
índice foi revalidado; não ficaram alterações rastreadas em
`tests/fixtures/e08_lighting_smoke.ndtscene.json`. O sidecar gerado e seu
recovery foram preservados dentro do pacote de evidências. Os dois processos
do binário foram fechados por `Alt+F4` e não há instância nativa pendente.

## Matriz de aceite técnico

| Critério da mudança | Resultado |
|---|---|
| Documento legado mantém defaults point/rotação zero | PASS — testes de compatibilidade |
| Luz direcional afeta pixels conforme orientação | PASS — 90°/270° e métrica de diferença |
| Gizmo de luz exibe e permite orientação | PASS — inspetor e captura nativa |
| VFX orientável via handle | PASS — drag real e valor `-56,6585°` |
| PT-BR do inspetor e menus | PASS — `Direcional`, `VFX`, `Rotação Z do socket` |
| Salvar/recarregar preserva estado | PASS — captura e JSON reaberto |
| Suíte oficial e build limpa | PASS — gates acima |

## Limitações e próximo passo

O controle CUA não estava disponível neste host; por isso a execução nativa usou
o fallback Win32 já autorizado e documentado (`mouse_event`, `keybd_event` e
`PrintWindow`). A captura prova o estado da execução, mas continua não sendo a
revisão humana final. O próximo lote permitido é completar partículas, tilemap/
tileset e editor 3D; só depois a revisão humana pós-E13 poderá ser reaberta pela
decisão formal.
