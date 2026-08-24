# Inventário público da interface — Etapas 0–9

Projeto: NeoEng-D-Trace  
Data: 2026-08-23  
Branch: Ailton/stage9-postmerge-documentation  
SHA auditado: 9903e82  
Merge funcional de referência: 98ffba1353941fd67ce46fc06be77f2f2abfcbb5

Este inventário fecha a lacuna de catalogação identificada na auditoria documental. Ele foi conferido contra o código de produção e os testes focados; não substitui a matriz de execução nem a revisão visual humana.

## 1. MainWindow e comandos

### Arquivo e aplicação

- open_project_action, open_image_action, save_project_action, save_project_as_action
- save_project_action, close_application_action
- act_export, act_export_collision_json, act_export_collision_txt

### Edição, viewport e renderização

- undo_action, redo_action, settings_action
- act_fit, act_100, act_grid, act_snap
- act_lit, act_xray1, act_xray2, act_xray3
- mask_viewer_action, collision_overlay_action
- act_clean, focus_button, language_button

### Cenário e preview

- scenario_open_action, scenario_save_action, scenario_load_action
- scenario_reset_action, scenario_export_action
- scenario_preview_action, scenario_overlays_action
- open_scenario_editor e janela dedicada scenario_editor_window

Os comandos estáveis são registrados em CommandRegistry; a palette Ctrl+K consulta os mesmos QAction e mantém recent_ids() em ordem mais recente primeiro.

## 2. ToolPalette e rail de referência

As nove ferramentas históricas continuam públicas e exclusivas:

- lasso_tool, polygonal_lasso, magnetic_lasso;
- pen_tool, rect_selection, ellipse_selection;
- polygon_edit, collision_brush, selection.

O contrato de compatibilidade preserva tool_buttons, btn_*, action_group, button_group, seleção exclusiva e atalhos existentes.

O rail visual também expõe cinco ações auxiliares reais:

- validation;
- move_viewport;
- zoom_viewport;
- fit_view;
- focus_selected.

A rail de referência usa ícones icon-only, largura efetiva entre 56 e 72 px e separadores de grupos. A barra textual histórica mantém largura suficiente para rótulos bilíngues.

## 3. Sinais e estados públicos

- MainWindow.command_palette_requested
- CanvasView.viewport_state_changed
- CanvasView.viewport_details_changed
- CanvasView.pan_mode_changed
- CanvasView.finished e CanvasView.progress
- ToolPalette.auxiliary_action_requested

Estados observáveis do viewport:

- modo LIT, X-RAY 1, X-RAY 2, X-RAY 3 e COLLISION;
- zoom;
- snap;
- grid;
- gizmo;
- seleção;
- cursor em coordenadas de imagem;
- modo pan.

## 4. Abas, painéis e inspetores

Painéis do editor principal:

- SidePanel / Objects;
- LayersPanel / Layers;
- GroupsPanel / Groups;
- CollisionPanel / Collision.

Contratos adicionais verificados:

- busca em Objects por ID/nome;
- busca em Layers por ID/nome;
- Transform com posição, rotação, escala e Pivot X/Y;
- checkbox de snap de vértices;
- metadata do objeto selecionado;
- rolagem do inspector;
- resumo de validação com vértices, convexidade e topologia;
- ações de teste, exportação e geração automática de colisão.

O editor de cenário mantém ScenarioEditorWindow separado, com viewport, layers, inspector, preview, parallax, sockets, overlays, histórico e exportação.

## 5. Menus e atalhos

Menus públicos: File, Edit e View, além do menu composto do chrome de referência.

Atalhos confirmados no código:

- abrir, abrir imagem, salvar, salvar como e sair;
- F para fit;
- X para X-Ray;
- A para LIT;
- atalhos numéricos 1–6 para ferramentas;
- undo/redo padrão;
- Ctrl+K para command palette.

Acessibilidade mínima conferida: texto não vazio, tooltip, nome acessível, fallback textual e foco de teclado nos controles de ferramenta.

## 6. Ícones

ICON_SPECS agora possui chaves explícitas para:

- seleção, laços, caneta, retângulo, elipse e edição de polígono;
- colisão, mover, zoom, fit e foco;
- abrir, salvar, salvar como, exportar, undo e redo;
- visibilidade, bloqueio, adicionar, remover, subir e descer;
- Lit, X-Ray, gizmo, snap, grid, cenário, validação e collider edit;
- language e settings.

Os ícones são SVG internos, versionados no código, sem dependência de fonte externa, com tooltip, nome acessível, fallback textual e renderização verificável em DPI Qt.

## 7. Exportadores e status

Exportadores catalogados:

- exportação geral;
- colisão JSON;
- colisão TXT;
- exportação runtime JSON do cenário;
- save/load/reset do cenário.

O status persistente é viewport_status na QStatusBar. A forma compacta cabe no layout mínimo; o tooltip conserva a forma completa com modo, zoom, snap, grid, gizmo, seleção e cursor.

## 8. Limites do inventário

Este documento comprova presença e identidade dos contratos. Não afirma, sozinho:

- aprovação visual humana;
- execução em monitor físico Windows;
- worktree limpo;
- CI para os commits locais de remediação;
- cobertura ou duração da suíte além dos relatórios citados na evidência de remediação.