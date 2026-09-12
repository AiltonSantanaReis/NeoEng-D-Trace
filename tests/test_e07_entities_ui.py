from __future__ import annotations

from src.core.scene_authoring_model import SceneAuthoringModel
from src.core.scene_authoring_session import SceneAuthoringSession
from src.ui.entity_prefab_panel import EntityPrefabPanel
from PySide6.QtWidgets import QApplication

from tests.test_e07_entities_contract import _document, _entity


def test_e07_panel_drives_prefab_acceptance_flow():
    qt_app = QApplication.instance() or QApplication([])
    session = SceneAuthoringSession(SceneAuthoringModel(_document(_entity("root"))))
    panel = EntityPrefabPanel(session)
    panel.show()
    qt_app.processEvents()
    try:
        panel.create_prefab_button.click()
        panel.instantiate_button.click()
        panel.override_button.click()
        panel.update_button.click()
        assert session.document.prefabs[0].version == 2
        assert len(session.document.prefab_instances[0].overrides) == 1
        panel.revert_button.click()
        panel.detach_button.click()
        assert session.document.prefab_instances[0].detached is True
        assert panel.status_label.text() == "Instância desvinculada"
    finally:
        panel.close()
        qt_app.processEvents()
