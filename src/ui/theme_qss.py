# src/ui/theme_qss.py
"""
Dark theme configuration for NeoEng-D-Trace v2.
"""

QSS = """
/* --- Global Settings --- */
QWidget {
    background-color: #1e1e1e;
    color: #e6e6e6;
    font-family: 'Segoe UI', Tahoma, Sans-Serif;
    selection-background-color: #2a6f97;
    selection-color: white;
}

/* --- Main Components --- */
QMainWindow::separator {
    background: #2d2d30;
    width: 4px;
    height: 4px;
}

QSplitter::handle {
    background: #3c3c3c;
}
QSplitter::handle:hover {
    background: #007acc;
}

QToolBar {
    background: #252526;
    border-bottom: 1px solid #3e3e42;
    spacing: 4px;
    padding: 4px;
}

QStatusBar {
    background: #007acc;
    color: white;
}

/* --- Menus --- */
QMenuBar {
    background: #2d2d30;
    color: #e6e6e6;
}
QMenuBar::item {
    background: transparent;
    padding: 4px 8px;
}
QMenuBar::item:selected {
    background: #3e3e42;
}
QMenu {
    background: #2d2d30;
    border: 1px solid #3f3f46;
    padding: 4px;
}
QMenu::item {
    padding: 4px 24px 4px 8px;
}
QMenu::item:selected {
    background: #094771;
    color: white;
}
QMenu::separator {
    height: 1px;
    background: #3f3f46;
    margin: 4px 0px;
}

/* --- Buttons & Interactions --- */
QPushButton, QToolButton {
    background: #3c3c3c;
    border: 1px solid #3c3c3c;
    color: #f0f0f0;
    padding: 5px 12px;
    border-radius: 0px; /* Flat engine style */
}
QPushButton:hover, QToolButton:hover {
    background: #4e4e4e;
}
QPushButton:pressed, QToolButton:pressed {
    background: #007acc;
    color: white;
}
QPushButton:disabled {
    background: #252526;
    color: #6d6d6d;
    border: 1px solid #2d2d30;
}

/* --- Inputs & Lists --- */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background: #3c3c3c;
    border: 1px solid #3f3f46;
    color: #f0f0f0;
    padding: 2px;
    selection-background-color: #264f78;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #007acc;
}

QListWidget {
    background: #252526;
    border: 1px solid #3f3f46;
    outline: 0;
}
QListWidget::item {
    padding: 4px;
}
QListWidget::item:selected {
    background: #094771;
    color: white;
}
QListWidget::item:hover:!selected {
    background: #2a2d2e;
}

/* --- Containers --- */
QGroupBox {
    border: 1px solid #3f3f46;
    margin-top: 1.2em;
    padding-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 3px;
    left: 10px;
    color: #cccccc;
}

/* --- ScrollBars (Modern Dark) --- */
QScrollBar:vertical {
    background: #1e1e1e;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #424242;
    min-height: 20px;
    border-radius: 0px;
}
QScrollBar::handle:vertical:hover {
    background: #4f4f4f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #1e1e1e;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #424242;
    min-width: 20px;
    border-radius: 0px;
}
QScrollBar::handle:horizontal:hover {
    background: #4f4f4f;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* --- ComboBox --- */
QComboBox {
    background: #3c3c3c;
    border: 1px solid #3f3f46;
    padding: 4px;
    color: #f0f0f0;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 0px;
}
QComboBox QAbstractItemView {
    background: #252526;
    border: 1px solid #3f3f46;
    color: #f0f0f0;
}

/* --- ToolTip --- */
QToolTip {
    background-color: #252526;
    color: #f0f0f0;
    border: 1px solid #3f3f46;
    padding: 2px;
}

/* --- Slider --- */
QSlider::groove:horizontal {
    border: 1px solid #3f3f46;
    height: 4px;
    background: #252526;
    margin: 2px 0;
}
QSlider::handle:horizontal {
    background: #007acc;
    border: 1px solid #007acc;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}
"""
