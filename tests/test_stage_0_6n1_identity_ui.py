"""Qt identity and bilingual UI contracts for Etapa 0.6N1.

Execute on Windows with Python 3.11 and PySide6.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from app import build_parser
from src.core.app_identity import APP_DISPLAY_NAME
from src.models.scene import Scene
from src.ui.main_window import MainWindow


class _ConfigStub:
    def get(self, key, default=None):
        return default


@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance() or QApplication([])
    yield app


def test_main_window_identity_is_correct_in_english_and_portuguese(qt_app):
    window = MainWindow(Scene(), _ConfigStub())

    window.set_language("en")
    assert window.windowTitle() == "NeoEng-D-Trace"
    assert window.act_export_collision_json.text() == "Export Collision (JSON)"
    assert window.act_lit.text() == "Lit"
    assert window.language_action.text() == "Language"
    assert window.act_english.text() == "English"
    assert window.act_english.isChecked()

    window.set_language("pt")
    assert window.windowTitle() == "NeoEng-D-Trace"
    assert window.act_export_collision_json.text() == "Exportar Colisão (JSON)"
    assert window.act_lit.text() == "Iluminado"
    assert window.act_open.text() == "Abrir Imagem"
    assert window.language_action.text() == "Idioma"
    assert window.act_portuguese.text() == "Português"
    assert window.act_portuguese.isChecked()

    assert APP_DISPLAY_NAME in window.windowTitle()
    window.close()


def test_loaded_document_title_remains_branded_in_both_languages(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    window._document_name = "personagem.png"

    window.set_language("en")
    assert window.windowTitle() == "NeoEng-D-Trace - personagem.png"

    window.set_language("pt")
    assert window.windowTitle() == "NeoEng-D-Trace - personagem.png"
    window.close()


def test_cli_help_uses_new_identity(qt_app):
    parser = build_parser()
    assert parser.description == ("NeoEng-D-Trace - Game Asset Preparation Tool")


def test_main_window_translation_catalogs_have_identical_keys(qt_app):
    window = MainWindow(Scene(), _ConfigStub())
    assert set(window.translations["en"]) == set(window.translations["pt"])
    window.close()
