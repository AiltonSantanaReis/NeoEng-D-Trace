# E12 — recursos avançados e híbrido 3D

**Worktree:** `build/e01-independent-scene-20260908`
**Branch:** `Ailton/e08-renderer-20260908`
**Status:** `EM_EXECUÇÃO`
**Gate de entrada:** E11 checkpoint técnico PASS no r67

## Contrato aprovado para este lote

E12 implementa uma extensão versionada e separada para uma cena híbrida: o
pacote preserva a composição 2D/2.5D de E11, adiciona uma sequência de
animação hash-bound e descreve uma vertical slice 3D mínima com câmera
perspectiva, malha, material, luz, profundidade e playback determinístico.

Isso não declara o Release Profissional 3D completo. O contrato 3D continua
explicitamente limitado à vertical slice, com rejeição de payloads inválidos e
sem inferir suporte a rigging, UV editing, culling ou desempenho de produção.

## Fila rastreável

| Meta | Estado | Saída obrigatória |
|---|---|---|
| E12-A contrato/schema e limites | `EM_EXECUÇÃO` | pacote determinístico, hashes e negativos |
| E12-B animação e playback | `PENDENTE` | frames, timeline, seed/timestep e destino |
| E12-C vertical slice híbrida 3D | `PENDENTE` | Godot e Unity reais materializando câmera, mesh, material e luz |
| E12-D UX/documentação | `PENDENTE` | mensagens, limitação explícita e captura do binário |
| E12-E fechamento técnico | `PENDENTE` | suíte, build, smoke, manifesto e promoção |

Symlinks e revisão humana permanecem reservados exclusivamente à auditoria
final. Nenhum `SKIP` será promovido a `PASS` neste lote.
