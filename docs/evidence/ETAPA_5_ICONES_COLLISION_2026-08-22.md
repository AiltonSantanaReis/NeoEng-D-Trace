# Etapa 5 — Iconografia da barra esquerda e Collision — snapshot pré-merge

**Classificação:** evidência histórica preservada. O estado não aprovado para
merge abaixo descreve a execução local original; a implementação foi depois
incluída na PR #140 e integrada no commit de merge registrado no encerramento
pós-merge da Etapa 5.

**Estado do snapshot:** VALIDADO LOCALMENTE — NÃO APROVADO PARA MERGE naquele momento
**Data da execução:** 2026-08-22
**Base observada:** 5d45f6ed54a1cf21cb394e8a8d5d8974708e44c8
**Branch observada:** Ailton/interface-stage5-viewport-hud
**Árvore limpa:** não; havia alterações locais anteriores da Etapa 5.
**Escopo:** aumentar a paleta esquerda de 20×20 para 24×24 e substituir os três emojis da Collision por SVGs internos determinísticos.

## Causa confirmada

src/ui/collision_panel.py criava os botões com os glifos 🔍, 📤 e 🤖 diretamente no texto. Esses glifos dependem da fonte e do backend do sistema, produzem cores e métricas diferentes dos SVGs internos e quebram a consistência visual do projeto.

## Implementação

- adicionados os ícones SVG internos collision_test e collision_auto_generate em src/ui/icon_library.py;
- reutilizado o ícone interno export para Export Collisions;
- preservados os textos, tooltips, sinais e ações dos três botões;
- definido tamanho 20×20 para os ícones dos botões Collision;
- alterado o tamanho da paleta esquerda para 24×24;
- nenhum pacote externo, fonte baixada ou dependência de sistema foi introduzido.

## Testes e comandos executados

- .\.venv\Scripts\python.exe -m py_compile ...
- .\.venv\Scripts\python.exe -m flake8 src tests scripts/...
- .\.venv\Scripts\python.exe -m black --check ...
- .\.venv\Scripts\python.exe -m isort --check-only ...
- .\.venv\Scripts\python.exe -m pytest -q tests/test_stage2_ui_icons.py tests/test_stage5_viewport_hud.py tests/test_ui_responsive_layout.py tests/test_ui_defect_regressions.py tests/test_visual_artifact_auditor.py --tb=short
- .\.venv\Scripts\python.exe -m pytest --cov=src --cov-branch --cov-fail-under=90 -q --tb=short
- .\.venv\Scripts\python.exe scripts/audit_stage5_viewport_hud.py
- .\.venv\Scripts\python.exe scripts/audit_ui_page_visibility.py
- .\.venv\Scripts\python.exe scripts/audit_collision_panel_icons.py

## Resultados

- testes focados: 24 passed;
- suíte integral: 1600 passed, 2 skipped;
- cobertura total: 91,25%, gate de 90% atendido;
- Flake8, Black, isort e compilação sintática: PASS;
- auditoria Stage 5 Windows: PASS, functional_failures=0, reference_failures=0, visual_findings=0;
- auditoria de visibilidade Windows: PASS, 10 registros, 0 achados;
- auditoria Collision Windows: PASS, 3 resoluções, 0 achados;
- os testes confirmaram ícones não nulos, iconFallback=False, nomes acessíveis, 20×20 na Collision, 24×24 na paleta esquerda e ausência dos emojis.

## Artefatos hashados

Manifesto: docs/evidence/artifacts/ui-modernization-stage5-20260822/collision-icon-audit/manifest.json

- 1080p_FHD_collision.png: 123409 bytes, SHA-256 ed1667bb4ac9430ab19fccadc57019fcf12aaf6ba2a77b9263585e7ec89861c2
- 768p_Minima_collision.png: 106476 bytes, SHA-256 f1fb005dd1265c785f03109ed88d55766acc9b33abe683462830b2d88118b0fd
- 720p_Compacta_collision.png: 103755 bytes, SHA-256 3a0b1002e45dd682fd77dff5c5c5c3a2f33c583c851c33f55696c9e976e5b74a
- collision-icon-report.json: 4857 bytes, SHA-256 705a52ae55c7bfbcd3ebfbd3ce12d3381903551a568380136357e42847582972

## Preservado

- comportamento e sinais dos botões Collision;
- rótulos textuais e acessibilidade;
- fallback textual da biblioteca de ícones;
- largura e estrutura da paleta;
- contratos e ações existentes;
- alterações locais anteriores da Etapa 5.

## Limitações e pendências

- a validação foi local no Windows; CI Linux/Windows ainda não foi executado para esta alteração;
- não foi criado commit desta melhoria;
- não foi aberto PR nem realizado merge;
- a árvore permanece suja por alterações anteriores da Etapa 5;
- build empacotada pós-alteração ainda não foi gerada;
- a aprovação visual final do proprietário permanece pendente.

## Decisão

**APROVADO somente para revisão local do diff.**
**Decisão histórica:** NÃO APROVADO para commit, PR, merge ou encerramento da
Etapa 5 naquele momento. A decisão atual está registrada em
ETAPA_5_INTERFACE_MODERNA_ENCERRAMENTO_POS_MERGE_2026-08-22.md.
