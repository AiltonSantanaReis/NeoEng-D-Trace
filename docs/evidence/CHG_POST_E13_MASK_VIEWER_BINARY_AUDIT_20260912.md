# Registro de evidência pós-E13 — Visualizador de Máscara no binário

**ID:** `CHG-POST-E13-MASK-VIEWER-BINARY-AUDIT-20260912`

**Estado:** `PASS`

**Data:** 2026-09-12

**Commit auditado:** `b61a279` (harness com modos nativos adicionados após a
qualificação do contorno vetorial)

**Governança:** [`GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md`](../GOVERNANCA_INTEGRIDADE_EXECUCAO_E_ANTIALUCINACAO_2026-08-24.md)

## Escopo

Verificar no binário real a entrada pelo menu `Visualizar`, a abertura da
janela nativa do Visualizador de Máscara, o comportamento sem asset, o
carregamento de uma imagem real e a troca dos presets/modos visuais. O caso
sem imagem e os lotes intermediários foram preservados; nenhum pacote foi
sobrescrito.

## Executável e método

- executável: `build/post-e13-final-build-20260912/release/post-e13-final-20260912/portable/NeoEng-D-Trace/NeoEng-D-Trace.exe`;
- versão `0.3.0`, idioma `Português (Brasil)`;
- SHA-256 `0A7E2BFF66F91B365D3D415B732A5C8C33265880E7678533F50E99F5A11F6229`;
- interação por cliques Win32 no binário e captura `PrintWindow`/`CopyFromScreen`;
- CUA nativo não estava disponível nesta sessão; isso não foi mascarado como
  um resultado positivo.

## Evidência real

O pacote final é `artifacts/audit-post-e13-binary-mask-viewer-20260912-r4/`.

| Caso | Evidência | SHA-256 | Resultado |
|---|---|---|---|
| menu em PT-BR | `../../artifacts/audit-post-e13-binary-mask-viewer-20260912-r2/03-view-menu-popup-screen.png` | `24856017C0E0A54E7F1FCAB5A42024D5C6FE506C175751EA4212C4A9ABE705B5` | item `Visualizador de Máscara (Auto-Detect)` visível |
| erro controlado sem imagem | `../../artifacts/audit-post-e13-binary-mask-viewer-20260912-r1/04-mask-viewer.png` | `D498CD336C354FDEBC0C9F9F52BBADCC8F7FCE76999FFBD42ABB8621617F8667` | janela abre e informa `Nenhuma imagem carregada` |
| imagem carregada | `04-mask-viewer.png` | `EC192D010DF04F65B619AE9C7C95793EF0910C50667712FD9CCE8231A3C77E98` | imagem real `144 x 96 pixels` renderizada |
| preset Perfeito | `04-mask-viewer-perfeito.png` | `7D9949AEC112C248D1F1D3EDE31DB9879E60EF1B443D3F4912236D96BD04F119` | aba ativa e controles de detecção visíveis |
| preset Aprim. | `04-mask-viewer-aprim.png` | `4F124B10ECA6685D20FD9D6BC8EB70C10722031E3CF557434BBB282D02BF7974` | aba ativa e `Área Mínima 50,00` observado |
| preset GrabCut | `04-mask-viewer-grabcut.png` | `D00662ADC53BA039983C4DA059968F93441568A5A89E0A8BC8CE1C570C074762` | aba ativa e `GrabCut (ROI)` observado |
| modo Sobel | `04-mask-viewer-sobel.png` | `4E875B250F296B851ED06C81C6E43AF7EEA94E2902DAA55E6B5602EA88BD3F7E` | botão `Sobel` ativo, imagem de bordas renderizada |
| modo Canny | `04-mask-viewer-canny.png` | `1EAF502C0B2FACCCCFB1470C2E3F365F856C02A9900EDF562556F7C395B2E16B` | botão `Canny` ativo, saída binária renderizada |
| modo Laplaciano | `04-mask-viewer-laplaciano.png` | `837CF715450B50DC486C49CFEA862D8982043669E218D1E7748EE70097737E2B` | botão `Laplaciano` ativo, saída renderizada |

## Verificação de domínio

Execução focada diagnóstica, separada da suíte oficial:

```text
tests/test_mask_viewer.py
tests/test_mask_viewer_compatibility.py
tests/test_grabcut_pipeline.py
tests/test_stage5_viewport_hud_contract.py
tests/test_stage9_functional_ui_audit.py
43 passed in 10.69s
```

## Resultado e limites

- A exposição, abertura, localização, mensagem de ausência e carregamento de
  imagem foram observados no executável real.
- As trocas de preset e modo produziram estados visuais distintos capturados
  no próprio diálogo nativo.
- O visualizador não possui um round-trip de cena próprio neste fluxo; o
  resultado aplicado à cena é responsabilidade do fluxo de máscara/contorno e
  continua coberto por seus próprios contratos.
- O pacote não afirma que esses modos são equivalentes a um algoritmo nativo
  de Godot ou Unity; equivalência de runtime permanece `PENDING_EVIDENCE`.
- A captura usa o fallback Win32 documentado, não uma simulação de widget.

## Classificação de governança

`PASS` para a superfície nativa, carregamento real, estados de erro e modos
visuais comprovados. Não houve remoção de falhas históricas nem uso de filtro
para converter resultado em aprovação.
