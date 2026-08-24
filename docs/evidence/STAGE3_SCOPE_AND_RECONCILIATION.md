# Etapa 3 — Escopo, auditoria e reconciliação

## Autoridade e cadeia

- Etapa: **3 — Barra lateral de ferramentas**.
- Escopo normativo: `pasted-text.txt`, Etapa 3; o plano vivo do projeto permanece subordinado às governanças globais.
- Snapshot pai obrigatório: `STAGE_2_SNAPSHOT:5eb6aea05b4cd76bbde9df2be098a24a5aea3a86`.
- Branch de trabalho: `Ailton/stage9-postmerge-documentation`.
- Estado durante a auditoria: alterações rastreadas da Etapa 3 presentes; artefatos históricos não rastreados preexistentes foram preservados e não são tratados como evidência de árvore limpa.

## O que esta etapa comprova

A auditoria atual verifica a barra efetivamente visível (`reference_tool_palette`) e a camada de compatibilidade (`tool_palette`) usando a MainWindow real:

- rail vertical, não móvel e não flutuável;
- largura renderizada entre 56 e 72 px nas três resoluções normativas;
- botões materializados para nove ferramentas e cinco ações auxiliares;
- ordem e separadores dos grupos Seleção, Contorno, Colisão e Navegação;
- seleção exclusiva, criação de ferramenta real no canvas e estado compartilhado entre as duas rails;
- nomes públicos, textos, tooltips, acessibilidade, foco e ícones;
- feedback de ferramenta desabilitada e idioma português;
- atalhos `1`–`6`;
- geometria Qt sem clipping;
- capturas reais em `1280×720`, `1366×768` e `1920×1080`, auditadas por Pillow/OpenCV/Qt.

## Achados reais corrigidos

1. A rail visível criava novos `QToolButton`s para as ações compartilhadas, mas não copiava explicitamente acessibilidade e foco. A correção propaga nome humano, tooltip/status, foco forte, `iconKey`, `objectName` estável e papel visual para o botão realmente apresentado ao usuário.
2. A ordem anterior misturava Seleção, Contorno e Colisão. A sequência foi reorganizada conforme o plano, preservando IDs, atalhos, sinais, callbacks e compatibilidade pública.

A primeira execução do novo harness produziu onze achados de interação. A reprodução isolada confirmou que eram duas deficiências do próprio harness: ele clicava numa barra ainda desabilitada e comparava nomes de ferramentas com teclas. O harness foi corrigido; nenhuma asserção de produto foi enfraquecida. A execução posterior passou com zero achados.

## Evidência reproduzida

Comandos executados:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_stage3_ui_toolbar.py tests/test_stage2_ui_icons.py tests/test_ui_responsive_layout.py -q
.\.venv\Scripts\python.exe scripts/audit_stage3_contract.py --output artifacts/stage3-snapshot-20260824
```

Resultado observado após a correção:

- testes focados: **11 passed**;
- contrato live: **PASS**, 0 achados;
- auditoria visual: **PASS**, 0 achados;
- rail visível: 61 px renderizados nas três resoluções;
- clipping: nenhum botão fora da geometria da rail;
- atalhos `1`, `2`, `3`, `4`, `5`, `6`: presentes;
- grupos: 3 separadores nas fronteiras normativas;
- seleção: nove ferramentas ativadas individualmente, com exclusividade e ferramenta real no canvas.

## Fora do escopo desta etapa

Não são contados como evidência da Etapa 3: inspetor, parallax, cenário, câmeras, luz, partículas, gizmo, máscaras, HUD, painéis laterais, toolbar superior e matriz DPI completa. Esses itens pertencem às etapas previstas posteriormente e permanecem disponíveis para seus próprios gates. A matriz DPI 100/125/150/200 é uma compatibilidade transversal já auditada na cadeia anterior; não é convertida em conclusão antecipada de etapas posteriores.

## Decisão

O pacote técnico atual é **REVIEW_REQUIRED**: a evidência automatizada da Etapa 3 passou, mas a aprovação humana e o ciclo formal de commit ainda são obrigatórios. Nenhuma declaração formal de conclusão deve ser feita antes da revisão humana, do commit autorizado e da repetição dos checks no SHA exato final.
