# Evidência — propostas visuais do gizmo pós-E13

**ID:** `EVIDENCE-POS-E13-GIZMO-VISUAL-20260912`  
**Status:** `PLANNED`  
**Data:** 2026-09-12  
**Commit dos vetores:** `c1090f5`  
**Commit dos previews PNG:** `779513d`  
**Integração no editor:** `PENDING_EVIDENCE`

## Escopo

Este pacote registra propostas visuais vetoriais para substituir o gizmo atual
por uma linguagem mais legível, consistente com o Editor de Cenário e extensível
para 2D, 2.5D e 3D. Ele é uma referência de design reutilizável; não afirma que
o gizmo já foi integrado ou que os gestos já funcionam no produto.

## Propostas

| Variante | Uso recomendado | Semântica visual |
|---|---|---|
| `Studio Axis 2D` | sprites, tiles, objetos 2D e camadas | X vermelho, Y verde, rotação ciano, pivô violeta, alça amarela de snap/escala |
| `Camera / Light Handle` | câmera, luz direcional e VFX orientável | moldura/safe area ciano, alça de rotação amarela, alvo violeta, direção vermelha |
| `Hybrid Depth` | somente modo 2.5D/3D | X/Y/Z explícitos, plano de profundidade, anel ciano e pivô violeta |

O padrão 2D permanece simples e não recebe elementos 3D. A variante híbrida é
uma extensão explícita, evitando que profundidade seja confundida com escala ou
com a ordem visual do parallax.

## Artefatos

Fontes vetoriais:

- `docs/design/gizmo-proposals-20260912.svg` — prancha comparativa, 1800×1180;
- `docs/design/gizmo-studio-axis-2d.svg` — proposta 2D, 600×600;
- `docs/design/gizmo-hybrid-depth.svg` — proposta 2.5D/3D, 700×600.

Previews rasterizados pelo renderer Qt nativo no backend Windows:

| Arquivo | Dimensão | SHA-256 |
|---|---:|---|
| `docs/design/gizmo-proposals-20260912.png` | 1800×1180 | `8C32A6BDA8210EDF7C8601B9BBAD506D2D8E7C2DBA3A4D1B8E45E96F090781C9` |
| `docs/design/gizmo-studio-axis-2d.png` | 600×600 | `FB77000FA26E9E50AECCC0EECCB2B925A5270CC827C94BDF5288F3B97380FC11` |
| `docs/design/gizmo-hybrid-depth.png` | 700×600 | `423DD5CA0EEF0CA8C666ED6561CCD144C3590659CBA73C61F4B4A83028743C9D` |

## Verificações realizadas

- parsing XML dos três SVGs: `PASS`;
- rasterização dos três SVGs com fontes Windows disponíveis: `PASS`;
- dimensões e salvamento dos três PNGs: `PASS`;
- inspeção visual das três imagens: `PASS` para legibilidade e coerência geométrica;
- tentativa anterior com Qt `offscreen`: `FAIL` diagnóstico, pois esse backend não
  expôs fontes e gerou glifos quadrados; a falha foi preservada como limitação do
  renderer de pré-visualização e não foi usada como evidência do produto;
- integração em `SceneTransformGizmo`, hit-testing, arraste, teclado,
  multiseleção, coordenadas local/mundo e persistência: `PENDING_EVIDENCE`;
- captura nativa do gizmo integrado no produto: `PENDING_EVIDENCE`;
- revisão humana/aprovação de variante: `PENDING_EVIDENCE`.

## Critério para integração futura

Antes de substituir a implementação atual, a variante escolhida deverá ser
implementada sem remover o comportamento existente e comprovada por teste
unitário/contrato, fluxo nativo, teste visual, persistência, undo/redo e
regressão. O pacote final deverá demonstrar que os handles têm hitbox real,
modificadores de teclado, escala em zoom, modo local/mundo, pivô editável e
feedback de estado sem depender de uma captura estática.

## Dependências

- [Governança de integridade](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)
- [ADR de descontinuação pública do editor independente](../ADR_POS_E13_DEPRECACAO_EDITOR_INDEPENDENTE_20260912.md)
- [Matriz de limites Godot/Unity](MATRIZ_LIMITES_ENGINES_GODOT_UNITY_POS_E13_20260912.md)

