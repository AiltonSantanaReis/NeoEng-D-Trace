"""Bilingual text catalog for the main application window."""

from src.core.app_identity import build_window_title

MAIN_WINDOW_TRANSLATIONS = {
    "en": {
        "window_title": build_window_title("en"),
        "file_menu": "File",
        "open_project": "Open Project...",
        "save_project": "Save",
        "save_project_as": "Save As...",
        "close_application": "Exit",
        "project_files": "NeoEng-D-Trace Projects (*.ndtproj)",
        "open_project_dialog": "Open Project",
        "save_project_dialog": "Save Project",
        "untitled_project": "Untitled",
        "unsaved_title": "Unsaved changes",
        "unsaved_message": "Save changes to the current project?",
        "project_saved": "Project saved successfully.",
        "autosave_saved": "Recovery snapshot updated.",
        "autosave_failed": (
            "Autosave failed; the previous recovery snapshot was preserved."
        ),
        "autosave_recovery_title": "Unsaved work recovery",
        "autosave_recovery_message": (
            "A recovery snapshot from {timestamp} is available. "
            "Choose Yes to recover it, Discard to remove it, or Cancel "
            "to decide later."
        ),
        "autosave_invalid": "The recovery snapshot is invalid.",
        "autosave_quarantined": " It was preserved at: {path}",
        "autosave_recovery_failed": "Failed to recover autosaved work: ",
        "autosave_source_changed": (
            "The original project changed or is unavailable. Use Save As to "
            "avoid overwriting unrelated data."
        ),
        "recovered_project": "Recovered project",
        "failed_open_project": "Failed to open project: ",
        "failed_save_project": "Failed to save project: ",
        "project_warnings_title": "Project opened with warnings",
        "project_image_missing": "Referenced image was not found: {path}",
        "project_image_unreadable": "Referenced image could not be read: {path}",
        "project_image_hash_mismatch": (
            "Referenced image differs from the saved SHA-256: {path}"
        ),
        "project_image_hash_unavailable": (
            "Referenced image was loaded, but its SHA-256 could not be "
            "verified: {path}"
        ),
        "open_image": "Open Image",
        "open_image_dialog": "Open Image",
        "image_files": "Images (*.png *.jpg *.jpeg *.bmp *.tiff)",
        "export": "Export...",
        "export_collision": "Export Collision",
        "export_collision_json": "Export Collision (JSON)",
        "export_collision_txt": "Export Collision (TXT)",
        "export_collision_json_dialog": "Export Collision JSON",
        "export_collision_txt_dialog": "Export Collision TXT",
        "export_collision_success": "Collision data exported to {path}",
        "failed_export_collision": "Failed to export collision data: ",
        "json_files": "JSON Files (*.json)",
        "text_files": "Text Files (*.txt)",
        "fit_view": "Fit View (F)",
        "pixel_1": "1:1 Pixel",
        "lit": "Lit",
        "xray_1": "X-Ray 1",
        "xray_2": "X-Ray 2",
        "xray_3": "X-Ray 3",
        "focus_selected": "Focus Selected",
        "clean_all": "🗑️ Clean All",
        "edit_menu": "Edit",
        "undo": "Undo",
        "redo": "Redo",
        "view_menu": "View",
        "mask_viewer": "Mask Viewer (Auto-Detect)",
        "collision_overlay": "Collision Overlay",
        "scenario_preview": "Scenario Preview (Read-Only)",
        "scenario_overlays": "Safe Frames and Crop Overlay",
        "info": "Info",
        "select_object": "Select an object in the list first.",
        "error": "Error",
        "failed_open_image": "Failed to open image: ",
        "failed_mask_viewer": "Failed to open Mask Viewer: ",
        "language": "Language",
        "objects_panel": "Objects",
        "layers_panel": "Layers",
        "groups_panel": "Groups",
        "collision_panel": "Collision",
        "english": "English",
        "portuguese": "Portuguese",
        "command_palette_title": "Command Palette",
        "command_palette_placeholder": "Search commands by name or ID...",
        "command_palette_no_results": "No matching commands.",
        "command_palette_hint": "Up/Down to navigate · Enter to run · Esc to close",
        "command_palette_search_name": "Command search",
        "command_palette_search_description": (
            "Type a command name, shortcut, or stable command ID."
        ),
        "command_palette_results_name": "Command results",
        "command_palette_results_description": (
            "Enabled commands can be run with Enter. Disabled commands are shown "
            "but cannot be run."
        ),
    },
    "pt": {
        "window_title": build_window_title("pt"),
        "file_menu": "Arquivo",
        "open_project": "Abrir Projeto...",
        "save_project": "Salvar",
        "save_project_as": "Salvar Como...",
        "close_application": "Sair",
        "project_files": "Projetos NeoEng-D-Trace (*.ndtproj)",
        "open_project_dialog": "Abrir Projeto",
        "save_project_dialog": "Salvar Projeto",
        "untitled_project": "Sem título",
        "unsaved_title": "Alterações não salvas",
        "unsaved_message": "Deseja salvar as alterações do projeto atual?",
        "project_saved": "Projeto salvo com sucesso.",
        "autosave_saved": "Snapshot de recuperação atualizado.",
        "autosave_failed": (
            "O autosave falhou; o snapshot de recuperação anterior foi preservado."
        ),
        "autosave_recovery_title": "Recuperação de trabalho não salvo",
        "autosave_recovery_message": (
            "Há um snapshot de recuperação de {timestamp}. Escolha Sim "
            "para recuperá-lo, Descartar para removê-lo ou Cancelar para "
            "decidir depois."
        ),
        "autosave_invalid": "O snapshot de recuperação é inválido.",
        "autosave_quarantined": " Ele foi preservado em: {path}",
        "autosave_recovery_failed": (
            "Falha ao recuperar o trabalho salvo automaticamente: "
        ),
        "autosave_source_changed": (
            "O projeto original mudou ou não está disponível. Use Salvar Como "
            "para evitar sobrescrever dados não relacionados."
        ),
        "recovered_project": "Projeto recuperado",
        "failed_open_project": "Falha ao abrir projeto: ",
        "failed_save_project": "Falha ao salvar projeto: ",
        "project_warnings_title": "Projeto aberto com avisos",
        "project_image_missing": "A imagem referenciada não foi encontrada: {path}",
        "project_image_unreadable": "A imagem referenciada não pôde ser lida: {path}",
        "project_image_hash_mismatch": (
            "A imagem referenciada difere do SHA-256 salvo: {path}"
        ),
        "project_image_hash_unavailable": (
            "A imagem referenciada foi carregada, mas seu SHA-256 não "
            "pôde ser verificado: {path}"
        ),
        "open_image": "Abrir Imagem",
        "open_image_dialog": "Abrir Imagem",
        "image_files": "Imagens (*.png *.jpg *.jpeg *.bmp *.tiff)",
        "export": "Exportar...",
        "export_collision": "Exportar Colisão",
        "export_collision_json": "Exportar Colisão (JSON)",
        "export_collision_txt": "Exportar Colisão (TXT)",
        "export_collision_json_dialog": "Exportar Colisão em JSON",
        "export_collision_txt_dialog": "Exportar Colisão em TXT",
        "export_collision_success": "Dados de colisão exportados para {path}",
        "failed_export_collision": "Falha ao exportar dados de colisão: ",
        "json_files": "Arquivos JSON (*.json)",
        "text_files": "Arquivos de Texto (*.txt)",
        "fit_view": "Ajustar Visão (F)",
        "pixel_1": "Pixel 1:1",
        "lit": "Iluminado",
        "xray_1": "Raio-X 1",
        "xray_2": "Raio-X 2",
        "xray_3": "Raio-X 3",
        "focus_selected": "Focar Selecionado",
        "clean_all": "🗑️ Limpar Tudo",
        "edit_menu": "Editar",
        "undo": "Desfazer",
        "redo": "Refazer",
        "view_menu": "Visualizar",
        "mask_viewer": "Visualizador de Máscara (Auto-Detect)",
        "collision_overlay": "Sobreposição de Colisão",
        "scenario_preview": "Preview de Cenário (Somente Leitura)",
        "scenario_overlays": "Molduras Seguras e Máscara de Corte",
        "info": "Info",
        "select_object": "Selecione um objeto na lista primeiro.",
        "error": "Erro",
        "failed_open_image": "Falha ao abrir imagem: ",
        "failed_mask_viewer": "Falha ao abrir Visualizador de Máscara: ",
        "language": "Idioma",
        "objects_panel": "Objetos",
        "layers_panel": "Camadas",
        "groups_panel": "Grupos",
        "collision_panel": "Colisão",
        "english": "Inglês",
        "portuguese": "Português",
        "command_palette_title": "Paleta de Comandos",
        "command_palette_placeholder": "Pesquisar comandos por nome ou ID...",
        "command_palette_no_results": "Nenhum comando encontrado.",
        "command_palette_hint": (
            "Cima/Baixo para navegar · Enter para executar · " "Esc para fechar"
        ),
        "command_palette_search_name": "Pesquisa de comandos",
        "command_palette_search_description": (
            "Digite o nome, atalho ou ID estável do comando."
        ),
        "command_palette_results_name": "Resultados de comandos",
        "command_palette_results_description": (
            "Comandos habilitados podem ser executados com Enter. Comandos "
            "desabilitados são exibidos, mas não podem ser executados."
        ),
    },
}
