# Etapa 4 — Escopo, auditoria e reconciliação

## Autoridade e cadeia

- Etapa: **4 — Barra superior agrupada**.
- Fonte normativa: plano profissional original e seção consolidada 11.7 do plano vivo.
- Snapshot pai: `STAGE_3_SNAPSHOT:ee15bcdb219cb1bd4e844f40eaa577cd23873627`.
- Escopo fora desta etapa: HUD, gizmo, painéis laterais, inspetor, cenário, parallax autoral, câmeras, luzes e partículas.

## Contrato comprovado

A auditoria verifica a toolbar realmente visível (`reference_top_toolbar`) e as superfícies de compatibilidade sem substituir ações existentes:

- Arquivo: Abrir projeto, Abrir imagem, Salvar e Exportar;
- Visualização: Fit, Pixel 1:1, Foco, Grid e Snap;
- Renderização/Máscara: Lit, X-Ray 1/2/3 e Mask Viewer;
- Edição: Undo, Redo, Clean All e Settings;
- comandos: menu global, menus nativos e busca `Ctrl+K`;
- separadores nativos e ordem dos grupos;
- modo compacto `IconOnly` e modo amplo `TextBesideIcon`;
- acessibilidade, foco, tooltips, ícones e nomes estáveis;
- geometria sem clipping nas três resoluções normativas.

## Achados reais corrigidos

1. A toolbar visível omitia Abrir imagem, Pixel 1:1 e rotas visíveis para Render/Máscara, Clean All e Settings. Os comandos existentes foram reorganizados em menus nativos e grupos explícitos.
2. O modo desktop usava `TextUnderIcon`, divergindo do contrato `TextBesideIcon`; o modo compacto mantinha texto no controle Focus. A resposta foi corrigida no controlador responsivo.
3. A camada visível não propagava acessibilidade, foco e metadados aos `QToolButton`s gerados para ações compartilhadas.
4. O Focus legado inserido diretamente na toolbar permanecia com geometria inválida; a camada visível passou a materializar um `QToolButton` próprio com o mesmo callback.
5. Fit, Focus, Pan/Move e Select/Selection eram controles visuais independentes para a mesma função. O topo agora reutiliza as ações canônicas da rail; menus continuam apenas como acessos alternativos às mesmas ações. Undo/Redo permanecem visíveis e não são repetidos no menu Edit visível.
6. O rótulo Clean All continha emoji; o texto foi normalizado para usar o ícone vetorial próprio e fallback textual.

A compatibilidade Stage 5 revelou e confirmou uma regressão intermediária: Seleção não desligava Pan quando acionada pela ação compartilhada. O estado foi corrigido no callback canônico do ToolPalette e todos os focados passaram.

## Evidência

Comandos executados após a implementação:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_stage4_ui_top_toolbar.py tests/test_stage3_ui_toolbar.py tests/test_stage5_viewport_hud.py tests/test_ui_responsive_layout.py -q
.\.venv\Scripts\python.exe scripts/audit_stage4_contract.py --output artifacts/stage4-snapshot-20260824
```

Resultado técnico atual:

- focados: **18 passed**;
- contrato live: **PASS**, 0 achados;
- auditoria visual: **PASS**, 0 achados;
- duplicidade visual: ações canônicas compartilhadas entre topo e rail; nenhum par independente para Fit, Focus, Pan/Move ou Select/Selection;
- capturas: 1280×720, 1366×768 e 1920×1080;
- compactação: `IconOnly`; desktop: `TextBesideIcon`;
- clipping: nenhum controle visível fora da geometria auditada.

## Decisão

O pacote técnico é `REVIEW_REQUIRED` até a revisão humana. Após aprovação, o commit, a suíte completa, a auditoria no SHA final, os validadores de cadeia/FINAL_TARGET e o registro formal de aprovação serão obrigatórios.
