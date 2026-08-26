"""Generated dark theme for NeoEng-D-Trace.

All application-chrome colors come from :mod:`src.ui.theme_tokens`.
"""

from __future__ import annotations

from src.ui.theme_tokens import THEME_TOKENS, ThemeTokens


def build_qss(tokens: ThemeTokens = THEME_TOKENS) -> str:
    """Build the application stylesheet from semantic theme tokens."""

    accent_soft = tokens.rgba(tokens.accent, 40)
    accent_hover_soft = tokens.rgba(tokens.accent, 18)
    return f"""
QWidget {{
    background-color: {tokens.window};
    color: {tokens.text_primary};
    font-family: Arial, 'Segoe UI', Tahoma, Sans-Serif;
    selection-background-color: {tokens.selection};
    selection-color: {tokens.text_primary};
}}
QMainWindow::separator {{
    background: {tokens.surface_alt};
    width: 4px;
    height: 4px;
}}
QSplitter::handle {{ background: {tokens.border}; }}
QSplitter::handle:hover {{ background: {tokens.accent_hover}; }}

QToolBar {{
    background: {tokens.surface};
    border-bottom: 1px solid {tokens.border};
    spacing: 4px;
    padding: 4px;
}}
QToolBar::separator {{
    background: {tokens.border};
    width: 1px;
    margin: 5px 3px;
}}
QToolBar#reference_tool_palette {{
    min-width: 56px;
    max-width: 72px;
    padding: 2px 2px;
    spacing: 2px;
    background: {tokens.surface};
    border-right: 1px solid {tokens.border};
}}
QToolBar#reference_tool_palette QToolButton {{
    min-width: 44px;
    max-width: 56px;
    min-height: 32px;
    max-height: 36px;
    padding: 2px;
    border: 1px solid transparent;
    border-radius: 4px;
}}
QToolBar#reference_tool_palette QToolButton:hover {{
    background: {accent_hover_soft};
    border-color: {tokens.border_strong};
}}
QToolBar#reference_tool_palette QToolButton:checked {{
    background: {accent_soft};
    border-color: {tokens.accent};
    color: {tokens.accent};
}}QToolBar#reference_top_toolbar {{
    min-height: 74px;
    max-height: 82px;
    padding: 4px 8px;
    spacing: 6px;
    background: {tokens.surface};
    border-bottom: 1px solid {tokens.border};
}}
QToolBar#reference_top_toolbar QToolButton#reference_menu_button {{
    min-width: 46px;
    max-width: 46px;
    font-size: 20px;
    padding: 0px;
}}
QToolBar#reference_top_toolbar QToolButton {{
    min-width: 60px;
    min-height: 58px;
    padding: 3px 5px 2px;
    border: 1px solid transparent;
    border-radius: 4px;
}}
QToolBar#reference_top_toolbar QToolButton::menu-button {{
    width: 0px;
    border: 0px;
}}
QToolBar#reference_top_toolbar QToolButton::menu-indicator {{
    image: none;
    width: 0px;
    height: 0px;
}}
QToolBar#reference_top_toolbar QToolButton[referenceActive="true"] {{
    background: {accent_soft};
    border-color: {tokens.accent};
    color: {tokens.accent};
}}
QToolBar#reference_top_toolbar QToolButton:hover {{
    background: {accent_hover_soft};
    border-color: {tokens.border_strong};
}}
QToolBar#reference_top_toolbar QToolButton:checked {{
    background: {accent_soft};
    border-color: {tokens.accent};
    color: {tokens.accent};
}}
QLineEdit#reference_command_search {{
    min-height: 28px;
    padding: 5px 10px;
    background: {tokens.surface_alt};
    border: 1px solid {tokens.border_strong};
    border-radius: 5px;
    color: {tokens.text_primary};
}}
QLineEdit#reference_command_search:focus {{
    border-color: {tokens.focus};
}}
QTabWidget#reference_panel_tabs {{
    background: {tokens.surface};
    border-left: 1px solid {tokens.border};
}}
QTabWidget#reference_panel_tabs::pane {{
    border: 0px;
    background: {tokens.surface};
}}
QTabWidget#reference_panel_tabs QTabBar::tab {{
    min-width: 78px;
    padding: 9px 12px;
    color: {tokens.text_secondary};
    background: transparent;
    border: 0px;
    border-bottom: 2px solid transparent;
}}
QTabWidget#reference_panel_tabs QTabBar::tab:selected {{
    color: {tokens.text_primary};
    border-bottom-color: {tokens.accent};
    background: {tokens.surface};
}}
QWidget#viewport_chrome {{
    background: {tokens.window};
}}
QWidget#viewport_horizontal_ruler, QWidget#viewport_vertical_ruler {{
    background: {tokens.surface_alt};
    color: {tokens.text_secondary};
    border: 0px;
}}
QWidget#viewport_overlay_bar {{
    background: {tokens.surface_raised};
    border: 1px solid {tokens.border_strong};
    border-radius: 4px;
}}
QWidget#viewport_overlay_bar QToolButton {{
    background: transparent;
    border: 0px;
    padding: 5px 8px;
    color: {tokens.text_primary};
}}
QWidget#viewport_overlay_bar QToolButton:hover {{
    background: {accent_hover_soft};
}}
QWidget#viewport_overlay_bar QToolButton:checked {{
    color: {tokens.accent};
    background: {accent_soft};
}}
QStatusBar {{
    background: {tokens.surface};
    color: {tokens.text_secondary};
    border-top: 1px solid {tokens.border};
}}
QStatusBar QLabel#viewport_status {{
    background: transparent;
    color: {tokens.accent};
    padding: 0px 10px;
    font-family: 'Segoe UI', Arial, Sans-Serif;
    font-weight: 600;
}}

QMenuBar {{ background: {tokens.surface}; color: {tokens.text_primary}; }}
QMenuBar::item {{ background: transparent; padding: 4px 8px; }}
QMenuBar::item:selected {{ background: {accent_hover_soft}; }}
QMenu {{
    background: {tokens.surface_raised};
    border: 1px solid {tokens.border_strong};
    padding: 4px;
}}
QMenu::item {{ padding: 5px 20px 5px 8px; }}
QMenu::item:selected {{
    background: {tokens.selection};
    color: {tokens.text_primary};
}}
QMenu::separator {{
    height: 1px;
    background: {tokens.border};
    margin: 5px 0px;
}}

QPushButton, QToolButton {{
    background: {tokens.surface_alt};
    border: 1px solid {tokens.border};
    color: {tokens.text_primary};
    padding: 5px 12px;
    border-radius: 3px;
}}
QPushButton:hover, QToolButton:hover {{
    background: {tokens.surface_raised};
    border-color: {tokens.accent_hover};
}}
QPushButton:pressed, QToolButton:pressed {{
    background: {tokens.accent_pressed};
    border-color: {tokens.accent};
    color: {tokens.text_primary};
}}
QPushButton:checked, QToolButton:checked {{
    background: {accent_soft};
    border-color: {tokens.accent};
    color: {tokens.text_primary};
}}
QPushButton:focus, QToolButton:focus, QLineEdit:focus, QTextEdit:focus,
QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {tokens.focus};
}}
QPushButton:disabled, QToolButton:disabled {{
    background: {tokens.surface};
    color: {tokens.text_disabled};
    border: 1px solid {tokens.border};
}}
QPushButton[uiRole="tool"] {{ padding: 6px 8px; }}
QPushButton[uiRole="tool"]:checked {{
    background: {accent_soft};
    border: 1px solid {tokens.accent};
}}
QPushButton#collision_toggle:checked {{
    background: {tokens.accent_pressed};
    border-color: {tokens.accent};
    font-weight: bold;
}}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background: {tokens.surface_alt};
    border: 1px solid {tokens.border};
    color: {tokens.text_primary};
    padding: 2px;
    selection-background-color: {tokens.selection};
}}
QListWidget {{
    background: {tokens.surface};
    border: 1px solid {tokens.border};
    outline: 0;
}}
QListWidget::item {{ padding: 4px; }}
QListWidget::item:selected {{
    background: {tokens.selection};
    color: {tokens.text_primary};
}}
QListWidget::item:hover:!selected {{ background: {tokens.surface_raised}; }}

QGroupBox {{
    border: 1px solid {tokens.border};
    margin-top: 1.2em;
    padding-top: 10px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    left: 10px;
    color: {tokens.text_secondary};
}}
QLabel#panel_section_title {{
    color: {tokens.text_primary};
    font-weight: bold;
    font-size: 14px;
}}

QScrollBar:vertical {{
    background: {tokens.window};
    width: 12px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {tokens.border_strong};
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: {tokens.accent_hover}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {tokens.window};
    height: 12px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background: {tokens.border_strong};
    min-width: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{ background: {tokens.accent}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

QComboBox {{
    background: {tokens.surface_alt};
    border: 1px solid {tokens.border};
    padding: 4px;
    color: {tokens.text_primary};
}}
QComboBox QAbstractItemView {{
    background: {tokens.surface_alt};
    border: 1px solid {tokens.border_strong};
    color: {tokens.text_primary};
}}

QDialog#command_palette_dialog {{
    background: {tokens.surface};
    border: 1px solid {tokens.accent};
}}
QLabel#command_palette_title {{
    color: {tokens.text_primary};
    font-size: 16px;
    font-weight: bold;
    padding: 4px 2px;
}}
QLineEdit#command_palette_search {{
    background: {tokens.window};
    border: 1px solid {tokens.border};
    color: {tokens.text_primary};
    padding: 8px;
}}
QListWidget#command_palette_results {{
    background: {tokens.window};
    border: 1px solid {tokens.border};
}}
QListWidget#command_palette_results::item {{ padding: 8px; }}
QLabel#command_palette_hint {{
    color: {tokens.text_secondary};
    padding: 2px;
}}

QToolTip {{
    background-color: {tokens.surface_raised};
    color: {tokens.text_primary};
    border: 1px solid {tokens.border_strong};
    padding: 4px;
}}
QSlider::groove:horizontal {{
    border: 1px solid {tokens.border};
    height: 4px;
    background: {tokens.surface_alt};
    margin: 2px 0;
}}
QSlider::handle:horizontal {{
    background: {tokens.accent};
    border: 1px solid {tokens.accent};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
"""


QSS = build_qss()

__all__ = ["QSS", "build_qss"]
