# Prompts de produção — Kit Modular de Floresta 2D

**ID:** `PREP-POS-E13-FOREST-PROMPTS-20260912`
**Status:** `IN_PROGRESS`
**Execução:** `PREPARATORY_ONLY`
**Data:** 2026-09-12
**Gizmo:** `DEFERRED`
**Destino dos masters:** ainda não promovido ao catálogo

## Direção comum

Todos os prompts abaixo usam a linguagem do piloto como referência de estilo:
ilustração pintada à mão para jogo 2D lateral, silhueta clara, detalhes
legíveis em escala de viewport, iluminação quente superior esquerda e fundo
genuinamente transparente. Cada chamada deve gerar um único asset isolado, sem
folha de sprites, texto, logotipo, marca d'água ou cenário adicional.

As imagens devem ser tratadas como `generate`, não como edição dos seis assets
existentes. Os assets do piloto são apenas referência visual de continuidade;
nenhum arquivo existente pode ser sobrescrito.

## Lote A — terreno e tileset

### `terrain-grass-soil-center-v1`

```text
Use case: stylized-concept
Asset type: isolated game terrain tile
Primary request: one hand-painted side-view forest terrain tile showing a grassy top edge over warm brown soil, designed as a clean modular center piece
Scene/backdrop: none, genuinely transparent outside the tile silhouette
Subject: one rectangular terrain piece with readable grass, soil strata and a restrained stone detail
Style/medium: painterly 2D game asset, consistent with the existing Floresta pilot
Composition/framing: single centered tile, straight modular edges, no perspective distortion
Lighting/mood: warm upper-left light, readable value separation
Constraints: transparent background; one asset only; no text; no logos; no watermark; no scenery; edges must be clean and suitable for deterministic tiling
Avoid: perspective, characters, repeated copies, decorative frame, artificial drop shadow outside the tile
```

### `terrain-stone-platform-edge-v1`

```text
Use case: stylized-concept
Asset type: isolated game terrain tile
Primary request: one hand-painted side-view forest stone platform edge for a modular tileset
Scene/backdrop: none, genuinely transparent outside the asset
Subject: one platform piece with a mossy top, layered stone face and a clean straight joining edge
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: single centered horizontal piece, consistent thickness, no perspective
Lighting/mood: warm upper-left light with clear stone planes
Constraints: transparent background; one asset only; no text; no logos; no watermark; no extra ground or scenery; clean joinable edge
Avoid: bevels that prevent tiling, cast shadow detached from the object, perspective, multiple variants in one image
```

### `terrain-water-grass-transition-v1`

```text
Use case: stylized-concept
Asset type: isolated game terrain transition tile
Primary request: one hand-painted side-view forest transition between grassy soil and shallow clear water
Scene/backdrop: none, genuinely transparent outside the transition
Subject: one modular transition piece with a readable grass bank, damp soil and a small water edge
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: single centered modular piece, no perspective, predictable joining boundaries
Lighting/mood: warm upper-left light, calm natural palette
Constraints: transparent background; one asset only; no text; no logos; no watermark; no scenery; no foam pattern that breaks repetition
Avoid: large focal stones, reflections that imply a full scene, characters, multiple pieces in a sheet
```

## Lote B — props de composição

### `prop-forest-bridge-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D game prop
Primary request: one hand-painted wooden footbridge for a side-view forest game
Scene/backdrop: none, genuinely transparent
Subject: complete small bridge with planks, simple supports, moss accents and a readable silhouette
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: full object visible, centered, side view, generous transparent padding, stable ground baseline
Lighting/mood: warm upper-left light, soft contact shading contained within the object
Constraints: transparent background; one prop only; no text; no logos; no watermark; no characters; no scenery
Avoid: perspective-heavy composition, cropped ends, detached glow, duplicate objects
```

### `prop-wood-fence-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D game prop
Primary request: one modular wooden forest fence segment for a side-view game
Scene/backdrop: none, genuinely transparent
Subject: a short fence segment with two posts, uneven planks, subtle moss and a clean ground baseline
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: side view, straight modular segment, centered, no perspective
Lighting/mood: warm upper-left light with readable wood grain
Constraints: transparent background; one prop only; no text; no logos; no watermark; no scenery; ends must support repetition
Avoid: characters, multiple fence segments, ground plane, excessive blur, decorative frame
```

### `prop-forest-sign-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D game prop
Primary request: one blank wooden signpost for a side-view forest game
Scene/backdrop: none, genuinely transparent
Subject: small carved signboard and post with moss, intentionally blank surface
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: complete object visible, upright, centered, stable ground baseline
Lighting/mood: warm upper-left light, subtle contact shading
Constraints: transparent background; one prop only; absolutely no letters or symbols; no logos; no watermark; no scenery
Avoid: readable text, arrows, characters, multiple signs, cropped post
```

## Lote C — vegetação e foreground

### `vegetation-pine-small-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D game vegetation asset
Primary request: one small full pine tree for a hand-painted side-view forest game
Scene/backdrop: none, genuinely transparent
Subject: complete tree with readable trunk, layered branches and visible base
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: full silhouette visible, centered, generous padding, stable ground baseline
Lighting/mood: warm upper-left light, darker interior foliage for depth
Constraints: transparent background; one tree only; no text; no logos; no watermark; no scenery; do not crop crown or base
Avoid: identical copy of the existing Pinheiro asset, multiple trees, ground plane, haze outside the silhouette
```

### `vegetation-grass-clump-foreground-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D foreground vegetation asset
Primary request: one low clump of layered forest grass and small leaves for foreground composition
Scene/backdrop: none, genuinely transparent
Subject: compact asymmetric grass clump with readable blades and a few small leaves
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: centered low silhouette, stable bottom baseline, generous transparent padding
Lighting/mood: warm upper-left light, clear silhouette at small viewport scale
Constraints: transparent background; one clump only; no text; no logos; no watermark; no soil patch or scenery
Avoid: large shrub, repeated copies, artificial outline, detached glow
```

### `vegetation-flower-patch-v1`

```text
Use case: stylized-concept
Asset type: isolated 2D foreground vegetation asset
Primary request: one small patch of woodland flowers and leaves for a hand-painted side-view game
Scene/backdrop: none, genuinely transparent
Subject: compact asymmetric patch with a few pale flowers, green leaves and a readable base
Style/medium: painterly 2D game asset matching the Floresta pilot
Composition/framing: centered low profile, complete silhouette visible, stable baseline
Lighting/mood: warm upper-left light, restrained color contrast
Constraints: transparent background; one patch only; no text; no logos; no watermark; no scenery; no large soil plane
Avoid: bouquet, vase, multiple patches, excessive bloom, detached shadow
```

## Proveniência e validação após geração

Para cada saída real, registrar imediatamente:

- ID do asset, nome do arquivo, data e ferramenta/modelo de geração;
- prompt final usado e referência visual, quando houver;
- hash SHA-256, dimensões, modo RGBA e bounding box alpha;
- inspeção visual em fundo quadriculado e em composição de parallax;
- resultado de decodificação, miniatura e busca em português;
- teste de importação, arraste, transformação, salvar/reabrir e undo/redo;
- licença e classificação de distribuição.

Nenhum prompt deste documento é evidência de asset gerado. A geração permanece
`PENDING_EVIDENCE` até que o arquivo real seja produzido, inspecionado e
hashado. O fallback CLI só poderá ser usado após autorização explícita do
usuário e configuração local de `OPENAI_API_KEY`.

## Dependências

- [Gate do Kit Modular de Floresta](ETAPA_MODELOS_KIT_FLORESTA_2D_GATE_20260912.md)
- [Auditoria do catálogo piloto](AUDITORIA_MODELOS_PILOTO_E_PLANO_PRODUCAO_POS_E13_20260912.md)
- [Checkpoint canônico](CHECKPOINT_CANONICAL_PRE_GIZMO_20260912.md)
- [Governança](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
