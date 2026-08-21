# Evidência — Etapa 2 da Interface Moderna Profissional

## Identificação

- Data da execução local: 2026-08-21.
- Baseline/HEAD de origem: aea54aa93ddfaff7ea8a77df24df2f0aa127b4fb.
- Branch de trabalho: Ailton/interface-stage2-icons.
- Estado da árvore durante a coleta: modificada; cinco diretórios untracked históricos foram preservados e não foram incluídos.
- Decisão desta evidência: PASS_LOCAL / AGUARDANDO CI E PÓS-MERGE.
- Esta evidência não aprova release.

## Objetivo e escopo

Implementar a biblioteca interna de ícones e padronizar as ações previstas no plano vivo:

- Open, Open Image, Save, Save As, Export e Export Collision;
- Fit View, 1:1 Pixel, Lit e X-Ray 1/2/3;
- Gizmo, Focus Selected, Clean All e Language;
- ferramentas de seleção, laço, caneta, formas, edição poligonal e pincel de colisão.

O contrato preserva os textos dos controles, tooltips, nomes acessíveis, atalhos e fallback textual. Os ícones são SVGs embutidos no código e não dependem de caminho local, fonte externa, tema do sistema ou pacote de terceiros.

Fora do escopo desta etapa: migração estrutural da barra esquerda para QToolBar, redesign do viewport, painéis laterais, editor de cenário separado, alterações de matemática do gizmo, contratos de projeto e exportadores.

## Implementação verificada

- src/ui/icon_library.py: catálogo determinístico de 25 ícones, renderização QSvgRenderer, cache por tamanho, configuração de QAction/QWidget e fallback textual.
- src/ui/main_window.py: ações principais, toolbars com ícone de 18x18 e estilo TextBesideIcon, sem remoção dos textos.
- src/ui/tool_palette.py: ícones para as nove ferramentas existentes, mantendo seleção e textos traduzíveis.
- tests/test_stage2_ui_icons.py: testes positivos do catálogo, teste negativo do fallback e teste live da MainWindow.
- scripts/audit_stage2_ui_icons.py: auditor que encadeia captura real, auditoria Pillow/OpenCV/Qt, hashes e contrato live de ícones/atalhos.

A configuração da MainWindow foi centralizada em icon_library.py para preservar o gate estrutural de menos de 1200 linhas em main_window.py. O arquivo ficou com 1199 linhas; isso não removeu funcionalidade.

## Comandos e resultados

- Auditor completo da Etapa 2: PASS.
  - Captura real: PASS.
  - Auditoria visual: PASS, zero achados.
  - Contrato live Qt: PASS.
  - Catálogo: 25 ícones.
  - Atalhos observados: F, X, A, 1–6, Ctrl+K, Ctrl+Z e Ctrl+Y.
- Testes focados e gates de higiene/baseline: 10 passed.
- Suíte completa: 1586 passed, 2 skipped, 0 failed; cobertura de linhas 91,1607% (19693/21173), branches 85,1773% (5574/6544), 818 branches parciais.
- Black, Flake8 e mypy nos arquivos alterados e no auditor: PASS.
- py_compile do auditor: PASS.
- Privacy gate sobre artefatos: 3 passed.
- Capturas: 15 PNGs reais em 1920x1080, 1366x768 e 1280x720, com estados sem projeto, projeto/painéis, validação, modal de validação e feedback de gizmo.
- PNGs: Pillow e OpenCV decodificaram dimensões, alpha e pixels; geometrias Qt, clipping, sobreposição e paleta foram validados pelo auditor.

## Artefatos e hashes

- raw-captures/manifest.json — SHA-256: d0b90ce6ac70fd0dea29b2f0cc0aea76e7e8126660ee73e7bf012440e35de36e
- visual-audit/visual-audit-report.json — SHA-256: 304785975e79ed958e767f2e8c7b8c38c3bf347b2e66e5c72bf2880c6c0bf035
- stage2-icon-report.json — SHA-256: dad4e4bbb6c403ffbc9e7663bb00f87f845afda42794eec5f6b486db18bd9dd2
- artifact-index.json — SHA-256: 724e37f15064fbcd724e954a4c621f34ee39a277d8e756f627e32475d3af7e9a
- raw-captures/: capturas, fixture e manifesto.
- visual-audit/: relatórios e PNGs anotados.
- capture.log e visual-audit.log: saídas sanitizadas; caminhos de host não são preservados.

O índice de artefatos registra bytes e SHA-256 de cada arquivo do pacote. A validação final contra blobs Git será feita depois do staging, antes do commit.

## Falhas encontradas e correções

1. A primeira execução estática encontrou E501/W292 nos SVGs e um erro mypy no acesso a setIcon em QWidget. As linhas SVG foram reformatadas sem suprimir Flake8; o setter foi validado por getattr/callable preservando o fallback. Black, Flake8 e mypy passaram depois.
2. A primeira execução do auditor tratou QAction como QWidget e falhou ao chamar accessibleName(). O auditor foi corrigido para ler a propriedade Qt de QAction e o método de QWidget; a verificação não foi removida.
3. A primeira suíte completa encontrou caminho absoluto em capture.log e main_window.py com 1224 linhas. O log passou a ser sanitizado na origem; a configuração de ícones foi centralizada e main_window.py ficou com 1199 linhas. A suíte seguinte passou integralmente.
4. O ambiente emitiu avisos de CuPy ausente, diretório de fontes do PySide6 indisponível e propagateSizeHints não suportado pelo backend offscreen. Foram preservados nos logs sanitizados e não foram convertidos em PASS silencioso. A auditoria funcional continuou PASS porque esses avisos não produziram achado nos artefatos nem falha de contrato.

## Limitações

- A coleta foi local em Windows com Qt offscreen; não constitui evidência CI Linux/Windows nem pós-merge.
- A inspeção humana independente das imagens não foi executada; o auditor automatizado foi executado e retornou PASS. Nenhuma conclusão subjetiva de estética foi transformada em PASS.
- Os dois skips da suíte são existentes e não foram criados nesta etapa; não foram convertidos em xfail ou PASS artificial.
- A árvore não estava limpa durante a coleta. Isso é declarado e impede tratar este documento como validação pós-commit.

## Próximo gate obrigatório

Staging exato dos arquivos da Etapa 2, regeneração e verificação de baseline/evidência contra blobs Git, revisão de diff e privacidade, commit sem arquivos untracked históricos, push normal, PR, CI completo e validação pós-merge no main. A etapa só poderá ser formalmente aprovada após esses gates.

## Decisão

PASS_LOCAL / AGUARDANDO CI E PÓS-MERGE