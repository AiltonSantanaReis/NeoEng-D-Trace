# NeoEng-D-Trace — Evidência P2D-03B

**Sublote:** P2D-03B — operações de edição, histórico e clipboard
**Status:** ACCEPTED / CLOSED — aceite humano final registrado
**Data:** 29/08/2026 (UTC-03)
**Baseline de entrada:** `13f77f3f8c1593bfc52e292a726917871bf2cdc8`
**Baseline contratual auditada:** `24a3178d52f1096e55c73b40daf196bccfe0d8cc`
**Branch:** `modernization/multiaxis-ui`
**Ambiente:** Windows, Python `.venv\Scripts\python.exe` 3.11.9, PySide6 6.10.1, pytest 9.1.1

Este documento registra a implementação e a qualificação pré-commit do sublote.
Ele não declara o sublote fechado: ainda são obrigatórios o commit, a
requalificação pós-commit, a comparação commit-to-commit, o seal e a revisão
humana final do proprietário. C3, G/V/B, o editor legado e o schema permanecem
imutáveis nesta entrega.

## 1. Aceite e fronteira

O contrato foi aceito explicitamente pelo proprietário com:

> P2D-03B ACEITO — contrato de operações, histórico e clipboard

A fronteira implementada é exatamente:

- `src/core/scene_authoring_clipboard.py` — codec JSON/MIME estrito e versionado;
- `src/core/scene_authoring_model.py` — preflight de edição e remoção atômica;
- `src/core/scene_authoring_session.py` — nudge, duplicate, delete, copy/paste e histórico;
- `src/ui/scene_authoring_viewport.py` — comandos de teclado contextualizados no viewport;
- `src/ui/scene_authoring_inspector.py` — Delete Selected usando a seleção completa;
- `scripts/audit_p2d_03b_edit_operations.py` — auditor do fluxo Qt real;
- testes profissionais P2D-03B;
- documentação decisória e evidência deste sublote.

Não foram alterados `CanvasView`, `Scene`, `CommandManager`, ferramentas de
imagem, `QAction` global, menu principal, schema de persistência, C3, adapters
G/V/B, P2D-03A ou P2D-03C.

## 2. Matriz requisito → implementação → teste → evidência

| Requisito | Implementação | Testes | Evidência de fluxo |
|---|---|---|---|
| nudge em mundo | `SceneAuthoringSession.nudge_selected()` reutiliza `translate_selected()` e snap existente | operações, snap/no-op, viewport e limites | `02-nudge-right.png`, `03-nudge-shift-down.png` |
| duplicate | IDs determinísticos, offset `(16,16)`, cópia profunda, seleção exclusiva e sem membership implícito | operações, locks, colisão de IDs, snap e grupos | `04-duplicate.png` |
| delete | pré-validação da seleção inteira e remoção transacional | múltiplos objetos, locks, grupos e rollback | `09-delete.png`, `10-undo-delete.png` |
| clipboard | MIME próprio, JSON UTF-8 estrito, sem bytes/caminhos externos e referências fail-closed | payload inválido, versão, campos desconhecidos, asset/layer ausente | `05-copy.png`, `06-paste.png` |
| grupos no paste | clone apenas com membros diretos completos; hierarquia V2 remapeada | grupo completo/parcial e hierarquia aninhada V2 | relatório funcional |
| undo/redo | uma entrada por mutação real, restauração de documento/seleção e redo | combinação de operações, no-op e preview | `07-undo-paste.png`, `08-redo-paste.png` |
| foco contextual | teclas mutantes tratadas somente no viewport; campos do inspector conservam atalhos nativos | viewport e campo numérico do inspector | relatório funcional |
| preview read-only | bloqueio de nudge/duplicate/delete/paste/undo/redo sem mutação | teste de preview | relatório funcional |
| persistência | save/reopen preserva objetos e IDs; seleção/histórico não são persistidos como estado de cena | auditor funcional | `11-save-reopen.png` |

## 3. Qualificação automatizada

### 3.1 Testes focalizados

Resultado final do conjunto focalizado P2D-03B:

```text
27 passed, exit 0
```

Casos cobertos:

- domínio/sessão: nudge simples e múltiplo, Shift, snap, no-op, duplicate,
  seleção, IDs, campos preservados, delete atômico, grupos, clipboard,
  rejeições e undo/redo;
- Qt: comandos pelo viewport, preview read-only, Delete do inspector e foco
  em campo editável sem sequestrar clipboard/histórico nativos;
- negativos: locks de objeto/layer/grupo, referências ausentes, schema MIME
  incompatível, campos desconhecidos e colisões determinísticas;
- boundary V2/legado: hierarquia aninhada V2 e remoção unitária fail-closed.

### 3.2 Suíte completa

```text
1810 passed, 2 skipped, exit 0
```

Executada com o Python 3.11.9 da `.venv` e `QT_QPA_PLATFORM=offscreen`.

### 3.3 Auditor funcional Qt nativo

O auditor `scripts/audit_p2d_03b_edit_operations.py` executou o fluxo real de
`ScenarioEditorWindow` com `QT_QPA_PLATFORM=windows`:

```text
NATIVE_AUDIT_EXIT=0
logical window=1280x820
physical captures=2560x1640
device_pixel_ratio=2.0
initial_focus=true
```

O relatório foi gerado no artefato externo identificado como
`neoeng-p2d-03b-20260829-r1/report.json`.

```text
report.json bytes=5499
report.json sha256=0019eae3f40e93613a3805f747adf0c8f5c01b82d29ceb4b95e45ced09906a1f
16 files in audit root, including 12 PNG captures
```

O relatório confirma seleção, nudge, Shift+nudge, duplicate, copy sem mutação,
paste, undo, redo, delete, undo de delete e save/reopen com IDs preservados.

### 3.4 Captura visual canônica e auditoria

O fluxo canônico existente também foi executado em Windows sem modificar a
baseline:

```text
CAPTURE_EXIT=0
VISUAL_AUDIT_EXIT=0
status=PASS
finding_count=0
```

Artefatos externos identificados como:

- `neoeng-p2d-03b-ui-capture-20260829-r1/captures/manifest.json`;
- `neoeng-p2d-03b-ui-capture-20260829-r1/visual-audit/visual-audit-report.json`;
- `neoeng-p2d-03b-ui-capture-20260829-r1/visual-audit/visual-audit-report.md`.

Hashes registrados:

```text
manifest.json bytes=124884 sha256=ffd3d02c8e4b63184f24c8ab3fee77e1a63765114a65ad023dcd525d6f976618
visual-audit-report.json bytes=15738 sha256=04fe0bc1f3cf7bc23af5b145b863c85e6ee53db0a380258e616d3b779dc309f7
visual-audit-report.md bytes=312 sha256=ce5541168956b475027949841ccf85530b7fa7e0514445a5acf62bcd12ad8fc0
```

Essa auditoria cobre a integridade visual/geométrica do shell canônico. O
auditor funcional acima é a evidência específica do editor profissional.

### 3.5 Requalificação pós-commit

O commit final do lote é `f7a7e61a297710d16f472e48f14caac974749d72` na branch
`modernization/multiaxis-ui`. A prova commit-to-commit confirmou os mesmos 17
arquivos previstos e o tracked tree ficou limpo (`git status --short
--untracked-files=no` sem saída).

- Testes focalizados P2D-03B: `26 passed`.
- Suíte completa: `1810 passed, 2 skipped, 0 failed` em 47,43 s.
- Auditoria Qt nativa: `NATIVE_AUDIT_EXIT=0`, janela lógica 1280x820,
  captura física 2560x1640, foco inicial confirmado; o relatório possui SHA-256
  `0019eae3f40e93613a3805f747adf0c8f5c01b82d29ceb4b95e45ced09906a1f`.
- Captura canônica Windows: `CAPTURE_EXIT=0`; auditor visual:
  `VISUAL_AUDIT_EXIT=0`, `finding_count=0`. O manifest possui 124884 bytes e
  SHA-256 `ffd3d02c8e4b63184f24c8ab3fee77e1a63765114a65ad023dcd525d6f976618`;
  o relatório visual JSON possui SHA-256
  `04fe0bc1f3cf7bc23af5b145b863c85e6ee53db0a380258e616d3b779dc309f7`.
- Comparação da captura geral pré/pós-commit: 16 PNGs antes, 16 depois,
  `PNG_NAME_DELTA=0`, `PNG_HASH_DELTA=0` e `MANIFEST_NONPIXEL_DELTA=False`.

Os produtores legacy G e B retornaram exit 1 por condições históricas de
`visual_geometry`/`source_tree_clean`; esses resultados foram preservados. Os
adapters canônicos decidiram `G=PASS` (60/60), `V=PASS` (12/12) e `B=PASS`
(21/21). O aggregate canônico retornou `status=PASS`, `blocking=false`,
93/93 checks; seu relatório possui SHA-256
`8a08eb6e714ff9c366f4f1c04522f62dde1508661471c50a69b8dad5fd27b49d`.

### 3.6 Build portátil pós-commit

A build foi produzida em checkout detached limpo do commit final, sem apagar
ou alterar os untracked do workspace principal. O script `scripts/build_windows.ps1`
não pôde ser usado literalmente porque `poetry` não está instalado; a rota
equivalente executou o spec oficial diretamente com PyInstaller 6.22.0 e Python
3.11.9. O smoke test da própria build retornou `SUCCESS` em 11 checks; o
relatório possui SHA-256 `7ce7881db0e4fd109808ccf0b490d9793ee0469851abfe43c867049262beb013`.

O arquivo portátil é `NeoEng-D-Trace-0.3.0-p2d-03b-f7a7e61-win64-portable.zip`,
com 124115458 bytes e SHA-256
`7df5e93a210435b06baa8757b603fe8aaa2dfdc35af1c118e5d2ab51b72bbef5`. A
extração independente revalidou `314/314` arquivos do manifest, com zero falhas,
e confirmou `source_commit=f7a7e61a297710d16f472e48f14caac974749d72`.

## 4. Regressão e limites

- `git diff --check` não encontrou erro de whitespace; os avisos recorrentes de
  conversão CRLF/LF foram apenas avisos do Git.
- O changeset não toca declarações de geometria, `setIconSize`, QSS, menu,
  QAction, atalhos globais ou o canvas legado.
- A única correção documental adicional removeu uma referência absoluta local
  que violava o teste de higiene do repositório; não alterou produto.
- O clipboard é customizado somente para objetos/relações declarativas; não
  copia bytes de assets, caminhos absolutos, scripts ou dependências implícitas.
- Rejeições são fail-closed e a operação inteira é restaurada antes de
  qualquer entrada de histórico.

## 5. Estado de aceite

O proprietário realizou a revisão humana final da build portátil, do review
package, das capturas Windows e dos fluxos de uso e registrou explicitamente:
`aceito` em 30/08/2026. Foram aceitos os resultados técnicos e a fronteira
documentada do lote.

Com esse aceite, P2D-03B está formalmente **ACCEPTED / CLOSED**. O seal final é
um artefato criptográfico externo identificado pelo manifest e pelo hash do
pacote; sua geração e revalidação fazem parte deste fechamento.

Push, tag, merge e release continuam expressamente fora deste sublote.
