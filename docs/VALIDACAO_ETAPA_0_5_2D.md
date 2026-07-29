# Validação da Etapa 0.5.2D

## Arquivos funcionais modificados

- `src/models/scene.py`;
- `src/core/commands.py`;
- `src/ui/side_panel.py`;
- `src/ui/export_dialog.py`.

## Testes adicionados

- `tests/test_creation_auto_selection.py`;
- `tests/test_stage_0_5_2d_ui.py`.

## Critérios

- novo polígono torna-se a seleção ativa;
- criação notifica a interface uma única vez;
- `add_object()` não muda silenciosamente de semântica;
- undo remove a seleção e redo restaura objeto e seleção;
- lista lateral acompanha `scene.selected_id`;
- desmarcar no canvas limpa a seleção visual da lista;
- grupos e botões do diálogo não expandem verticalmente;
- exportadores existentes permanecem disponíveis.

## Limite do ambiente de preparação

Os testes Qt devem ser executados no Windows/Python 3.11 com PySide6. Os testes
não gráficos são executáveis no ambiente de preparação.
