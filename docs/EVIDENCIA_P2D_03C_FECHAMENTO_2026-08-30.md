# NeoEng-D-Trace — Evidência de fechamento P2D-03C

**Sublote:** P2D-03C — navegação do viewport, fit e estados visuais
**Status:** `ACCEPTED / CLOSED`
**Data:** 30/08/2026 (UTC-03)
**Contrato:** `docs/DECISAO_P2D_03C_NAVEGACAO_CAMERA_ESTADOS_2026-08-30.md`
**Checkpoint de entrada:** `78f773583b0277fa9b970d1f849538b4fa3fdcc6`
**Commit técnico:** `58674dde87ba94082e84f066ebda21d144da65cd`
**Commit documental vigente antes deste registro:** `921ef61bd0e3022252c4561491dec41196209af7`
**Branch:** `modernization/multiaxis-ui`

Este documento consolida a qualificação pós-commit, a revisão humana adicional
e o aceite final explícito do proprietário. O proprietário registrou
**`P2D-03C ACEITO — entrega final`** em 30/08/2026, encerrando formalmente o
sublote dentro da fronteira aprovada. Não há autorização implícita para push,
tag, merge ou release público.

## 1. Escopo e fronteira

O commit técnico implementou exclusivamente a decisão P2D-03C:

- navegação transitória do viewport profissional;
- wheel zoom ancorado no cursor, pan por botão médio e limites de zoom;
- `Fit Selection` e `Fit All` no fluxo profissional;
- conversão determinística viewport ↔ mundo;
- estados hover, pressed, checked, focus e disabled;
- testes, auditoria de captura e documentação correspondentes.

### 1.1 Arquivos do commit técnico

Arquivos de produto, teste e evidência introduzidos ou alterados pelo commit
`58674dde87ba94082e84f066ebda21d144da65cd`:

- `src/core/scene_view_navigation.py`;
- `src/ui/scene_authoring_viewport.py`;
- `src/ui/scene_authoring_inspector.py`;
- `src/ui/scenario_editor_window.py`;
- `tests/test_p2d_03c_navigation_math.py`;
- `tests/test_p2d_03c_viewport.py`;
- `tests/test_p2d_03c_professional_flow.py`;
- `scripts/audit_p2d_03c_navigation.py`;
- `docs/DECISAO_P2D_03C_NAVEGACAO_CAMERA_ESTADOS_2026-08-30.md`;
- `docs/DECISAO_P2D_03_NAVEGACAO_SELECAO_PRODUTIVIDADE_2026-08-29.md`;
- `docs/EVIDENCIA_P2D_03C_IMPLEMENTACAO_PRECOMMIT_2026-08-30.md`;
- `docs/INDICE_DOCUMENTAL_ATIVO_CANONICO_2026-08-24.md`;
- `docs/PLANO_EVOLUCAO_EDITOR_2D_2_5D_3D_E_LINHAS_INDEPENDENTES_2026-08-29.md`.

O commit documental `921ef61bd0e3022252c4561491dec41196209af7` somente
sanitizou caminhos externos na evidência pré-commit. Este fechamento adiciona
o presente registro e as reconciliações documentais correspondentes.

Não foram alterados neste lote `CanvasView`, editor legado, visualizador de
máscara, schema V1/V2, menus globais, QAction globais, C3, tolerâncias ou
adaptadores canônicos G/V/B.

## 2. Matriz requisito → implementação → teste → evidência

| Requisito | Implementação | Teste/validação | Evidência pós-commit | Resultado |
|---|---|---|---|---|
| D03C-01 — navegação transitória sem dirty/undo/save | Estado de navegação separado da câmera persistida | fluxo profissional e assertions de estado | captura `01`, `03`, `05`; relatório de captura | PASS |
| D03C-02 — wheel ancorada, fator 1.15, limites 0.10x–8.00x | `src/core/scene_view_navigation.py` e viewport | matemática, round-trip, limites e deltas fracionários | focal + captura | PASS |
| D03C-03 — pan somente por botão médio | tratamento exclusivo de middle-button drag | eventos Qt reais e fluxo profissional | captura `04`; auditoria visual | PASS |
| D03C-04 — Fit Selection/Fit All | bounds transformados de objetos elegíveis e visíveis | seleção, rotação, escala, flip, vazio e exclusões | capturas `02` e `03`; relatório | PASS |
| D03C-05 — preview navegável e mutações bloqueadas | navegação reaplicada sem mutação do documento | authoring/preview, read-only e persistência | captura `05`; aggregate | PASS |
| D03C-06 — estados e acessibilidade operacional | foco, hover, pressed, checked, disabled e tab order | captura nativa Windows e revisão humana | sete estados capturados; auditoria visual | PASS COM LIMITAÇÃO DE HOST |

## 3. Invariantes e fronteira protegida

As verificações pré e pós-commit confirmaram:

- `protected_region_delta_count = 0`;
- `geometry_sensitive_delta_count = 0`;
- nenhum delta em transforms, IDs, assets, layers, groups, sockets, seleção ou
  membership causado por navegação;
- nenhuma alteração na câmera persistida ou no JSON por zoom, pan e fit;
- nenhuma operação inválida parcial em seleção vazia ou cena vazia;
- preview permaneceu read-only para mutações;
- nenhuma alteração no editor legado ou nos contratos C3/G/V/B.

## 4. Qualificação automatizada pós-commit

Ambiente de qualificação:

```text
Windows
Python: .venv\Scripts\python.exe 3.11.9
PySide6: 6.10.1
pytest: 9.1.1
commit-fonte: 921ef61bd0e3022252c4561491dec41196209af7
```

Resultados finais já executados no commit pós-commit:

```text
Suíte completa: 1821 passed, 2 skipped, 0 failed
Aggregate canônico: G60/60 + V12/12 + B21/21 = 93/93
Aggregate status: PASS
Aggregate blocking: false
V Stage1: PASS
G Stage9 producer: exit 1 — mixed legacy preservado
B Stage9 producer: exit 1 — mixed legacy preservado
Captura P2D-03C: exit 0 — PASS
Auditoria visual: exit 0 — PASS
finding_count: 0
Comparação pré/pós: PASS
PNG antes/depois: 7/7
PNG_NAME_DELTA: []
PNG_HASH_DELTA: []
PNG_SIZE_DELTA: []
MANIFEST_NONPIXEL_DELTA: 0
```

Os exits 1 dos produtores G/B são as condições mixed legacy já documentadas
(`visual_geometry`/`minimum_size_hint` e `source_tree_clean`). Eles não foram
apagados, relaxados ou reinterpretados. O aggregate canônico continua sendo o
gate bloqueante e decidiu `93/93`, `blocking=false`.

## 5. Captura Windows e auditoria visual

Artefatos externos pós-commit:

```text
<external-evidence-root>\neoeng-p2d-03c-postcommit-921ef61-20260830-run01\07-p2d03c-capture
<external-evidence-root>\neoeng-p2d-03c-postcommit-921ef61-20260830-run01\07-p2d03c-capture-visual-audit\visual-audit-report.json
<external-evidence-root>\neoeng-p2d-03c-postcommit-921ef61-20260830-run01\08-capture-compare.json
```

A matriz nativa contém os estados:

1. foco inicial do authoring;
2. hover de `Fit Selection`;
3. `Fit All`;
4. pan pressionado;
5. preview com edição desabilitada;
6. fluxo profissional em 1366x768;
7. fluxo profissional solicitado em 1920x1080.

O host Windows limitou a área disponível da janela lógica solicitada de
1920x1080 para 1920x1060. A captura física correspondente foi 3840x2120 em
DPR 2. A limitação foi preservada na evidência e não é apresentada como
cumprimento exato de 1920x1080. As capturas de 1366x768 e do fluxo 1280x820
mantiveram seus tamanhos físicos registrados nos manifests.

Não houve finding visual automatizado. A comparação pós-commit não mascara
pixels, não filtra diferenças por região e não encontrou alteração de nome,
hash, tamanho ou metadado não volátil nos sete frames.

## 6. Revisão humana registrada

O proprietário repetiu o teste da transição entre Fit e Focus na build
portátil. O comportamento funcionou normalmente na repetição. O relato
anterior de lentidão não foi reproduzido e é classificado como **observação
não reproduzível, sem finding confirmado**, sem alteração de código, limiar,
auditor ou baseline.

Esse registro confirma especificamente o item de responsividade percebida de
Fit/Focus. A revisão humana final da matriz foi concluída sem finding adicional,
e o proprietário registrou o aceite formal do pacote com
**`P2D-03C ACEITO — entrega final`** em 30/08/2026.

## 7. Build portátil e integridade

A build foi criada em checkout detached limpo do commit
`921ef61bd0e3022252c4561491dec41196209af7`, preservando os untracked do
workspace principal.

```text
Artefato: NeoEng-D-Trace-0.3.0-win64-portable.zip
Bytes: 124136052
SHA-256: e1d434597a744a2e122f29472d3e3f6be0d3f6f95f1818871bf53f83afb3fc00
Smoke test: PASS — 11 checks
Extração/re-hash independente: PASS
Manifest da build: 314 arquivos
Extraídos: 314 arquivos
Ausentes: 0
Extras: 0
Mismatch de hash/tamanho: 0
```

O entrypoint `scripts/build_windows.ps1` não pôde ser usado literalmente
porque `poetry` não estava disponível no ambiente. A sequência equivalente
com o spec oficial, Python 3.11.9 e PyInstaller 6.22.0 passou, e a limitação
de tooling está preservada aqui. A build é adequada para teste local; não é
promovida automaticamente a release pública.

## 8. Seal e estado de fechamento

O pacote final de seal foi gerado depois do aceite final e contém as seções
`00-baseline`, `01-tests`, `02-conformance`, `03-capture`, `04-visual-audit`,
`05-human-review`, `06-build`, `07-docs`, manifest, hash do manifest, ZIP e
hash do ZIP. A extração independente revalidou todos os artefatos, o manifest
e o tracked tree.

```text
Pacote final: artefato externo identificado pelo manifest; caminho local omitido por privacidade
Hash do ZIP: registrado no arquivo .zip.sha256 e no manifest do pacote
Verificação independente: PASS
Status formal: ACCEPTED / CLOSED
```

O seal não altera C3, as baselines canônicas ou os resultados mixed legacy.

## 9. Imutáveis e condições preservadas

- C3 continua imutável e não foi reescrito.
- Baselines, tolerâncias, auditores e seals anteriores continuam preservados.
- Falhas mixed legacy G/B permanecem visíveis.
- Nenhum resultado foi fabricado por mascaramento, filtro ou alteração de
  referência.
- P2D-03A e P2D-03B permanecem `ACCEPTED / CLOSED` em seus próprios registros.
- Push, tag, merge e release permanecem fora do escopo sem autorização
  explícita.
