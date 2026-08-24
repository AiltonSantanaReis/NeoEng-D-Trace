from __future__ import annotations

from scripts.audit_stage9_responsive_dpi import (
    DPI_CASES,
    RESOLUTIONS,
    capture_dimensions,
    widget_presence,
)


def _snapshot() -> dict:
    return {
        "visible": True,
        "geometry": [0, 0, 10, 10],
    }


def _manifest() -> dict:
    widgets = {
        name: _snapshot()
        for name in (
            "main_splitter",
            "reference_tool_palette",
            "canvas",
            "panel_stack",
        )
    }
    pages = [
        {"title": title, "geometry": [0, 0, 10, 10]}
        for title in ("Objects", "Layers", "Groups", "Collision")
    ]
    widgets["tab_visibility"] = {
        "reference_panel_tabs": {
            "visible_to_root": True,
            "pages": pages,
        },
        "compact_panel_tabs": {
            "visible_to_root": False,
            "pages": [],
        },
    }
    return {
        "captures": {
            label: {
                "actual_capture_size": list(size),
                "widget_geometry": {"projeto_paineis": widgets},
            }
            for label, size in RESOLUTIONS.items()
        }
    }


def test_stage9_matrix_has_required_resolution_and_dpi_cases():
    assert RESOLUTIONS == {
        "720p_Compacta": (1280, 720),
        "768p_Minima": (1366, 768),
        "1080p_FHD": (1920, 1080),
    }
    assert DPI_CASES == (("100", 1.0), ("125", 1.25), ("150", 1.5), ("200", 2.0))


def test_stage9_capture_dimensions_reject_wrong_capture_size():
    manifest = _manifest()
    for capture in manifest["captures"].values():
        capture["actual_window_size"] = capture["actual_capture_size"]
    assert capture_dimensions(manifest, 1.0)["status"] == "PASS"
    manifest["captures"]["720p_Compacta"]["actual_capture_size"] = [1, 1]
    result = capture_dimensions(manifest, 1.0)
    assert result["status"] == "FAIL"
    assert result["failures"][0]["requested_logical"] == [1280, 720]
    assert result["failures"][0]["expected_physical"] == [1280, 720]


def test_stage9_widget_audit_requires_active_tab_pages():
    manifest = _manifest()
    assert widget_presence(manifest)["status"] == "PASS"
    manifest["captures"]["720p_Compacta"]["widget_geometry"]["projeto_paineis"][
        "tab_visibility"
    ]["reference_panel_tabs"]["pages"] = []
    result = widget_presence(manifest)
    assert result["status"] == "FAIL"
    assert any(
        item["widget"] == "reference_panel_tabs_pages" for item in result["failures"]
    )
