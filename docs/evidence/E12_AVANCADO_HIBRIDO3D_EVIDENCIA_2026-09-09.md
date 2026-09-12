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
| E12-A contrato/schema e limites | `CONCLUÍDO_TECNICAMENTE` | pacote determinístico, hashes e negativos |
| E12-B animação e playback | `CONCLUÍDO_TECNICAMENTE` | frames coerentes, timeline, timestep e destino |
| E12-C vertical slice híbrida 3D | `CONCLUÍDO_TECNICAMENTE` | Godot e Unity reais materializando câmera, mesh, material e luz |
| E12-D UX/documentação | `CONCLUÍDO_TECNICAMENTE` | mensagens, limitação explícita e captura do binário |
| E12-E fechamento técnico | `CONCLUÍDO_TECNICAMENTE` | suíte, build r69, smoke, manifesto e promoção |

Symlinks e revisão humana permanecem reservados exclusivamente à auditoria
final. Nenhum `SKIP` será promovido a `PASS` neste lote.

## Implementação e evidência técnica

O commit `6275baf` adiciona o exportador determinístico
`src/exporters/hybrid_composition_export.py`, a operação `--export-hybrid` do
launcher, a fixture `scripts/prepare_e12_hybrid_fixture.py` e o harness real
`scripts/audit_e12_hybrid_engines.py`. O contrato falha fechado para schema,
perspectiva, limites de câmera, IDs duplicados, triângulos inválidos,
componentes fora do pacote, symlinks, manifests aninhados e divergência de
hash. O status `VERTICAL_SLICE_ONLY` é obrigatório e não representa o release
3D profissional completo.

O pacote foi gerado a partir do pacote E11 validado e asset real `hero.png` em:

`artifacts/e12-hybrid-fixture-20260909-r3/package/`

- manifest híbrido SHA-256: `98ED8A92EFA9372504E0D683BE608B14FEE166DD1F8A720DC906B7765426BFC3`;
- 11 componentes vinculados, 2 frames PNG e 1 clip com keyframes `0.0 → 1.0`;
- exportação pelo CLI do produto: `Hybrid composition exported successfully (VERTICAL_SLICE_ONLY)`;
- testes focados de composição/animação/CLI: `55 passed`;
- compileall, Black, Flake8 focado e `git diff --check`: `PASS`.

## Destinos reais

O harness `scripts/audit_e12_hybrid_engines.py` executou o mesmo pacote em
Godot `4.7-stable (official)` e Unity `6000.5.7f1`. O relatório final é
`artifacts/e12-engine-audit-20260909-r4/e12-engine-report.json`, SHA-256
`FF67312CFF83E07173D26B2067021E844AB5F91B00039AE53403628604646119`.

Ambos retornaram `SUCCESS` com câmera perspectiva, 1 mesh, 1 material, 1 luz,
1 clip, 2 frames, asset carregado e playback em `y=0.125`. Unity também gerou
a captura real renderizada
`artifacts/e12-engine-audit-20260909-r4/e12-hybrid-unity-capture.png`, SHA-256
`3A46871D37989370D472E6D05F4E06CADED0485C32EA3ABB90D883A108A970D6`. Godot
foi validado em modo headless com rendering dummy; por isso a captura visual
de destino Godot permanece ausente e não é inferida como existente. As mensagens
externas de UnityConnect/debugger permanecem limitações ambientais conhecidas,
sem falha do relatório do harness.

## Findings corrigidos durante o lote

1. A primeira fixture registrava caminhos absolutos nos componentes copiados;
   o exporter foi corrigido para registrar caminhos relativos ao pacote e a
   validação positiva foi repetida.
2. A primeira execução real encontrou acesso inválido à textura headless do
   Godot e erro de compilação no harness Unity. O harness foi corrigido,
   repetido em nova pasta de auditoria e o relatório final acima passou.

## Fechamento técnico E12-E

Após a correção de governança `510cee7`, a suíte oficial final registrou
`2104 passed, 2 skipped, 1 warning`. Compileall, Black, Flake8 focado,
`git diff --check` e o validador de continuidade passaram. A build oficial
final é:

- release: `release/e12-hybrid-20260909-r69/`;
- source commit: `510cee7166eb90026c22e3b922d45d3624bb4c91`;
- executável SHA-256: `07D3B3FBFAD22518628A8E8405FEA69E783750BBBD9593786A8E049781203152`;
- ZIP portátil SHA-256: `82713FBDC7B47578C49AA357F9E013CD407B9AF5EC031032AC9DFFFF0E8166A1`;
- smoke portátil: `SUCCESS`, 11 checks; relatório SHA-256
  `82160C4425C8C504D1A18DC9CB25088331BEF681F5FA370327A2DAB1A2C2132C`.

O CLI do executável r69 retornou `NeoEng-D-Trace-CLI.exe 0.3.0` e
`Hybrid composition exported successfully (VERTICAL_SLICE_ONLY)`. O manifest
gerado pelo binário manteve SHA-256
`98ED8A92EFA9372504E0D683BE608B14FEE166DD1F8A720DC906B7765426BFC3`.

A captura nativa do r69 está em
`artifacts/e12-binary-capture-r69-20260909/`: janela principal `1933x1045`,
SHA `28AA060935049CD6CED2195351ACF18E94B8A2661429873CA4BEE23683BA5D64`, e
Cena Independente `993x716`, SHA
`2464B49EBA3378ED0252A5EE941C00746E56F8A94FD11B82C7D1C7CC17BE0A6F`. A
inspeção automatizada da captura não apontou regressão de tradução, toolbar ou
painel Objetos. A revisão humana final permanece deferida e não foi inferida.
