from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = (
    ROOT
    / "artifacts"
    / "audit-post-e13-unity-controlled-windows-sandbox-20260913-r1"
)
R15_RUNNER = HARNESS_ROOT / "control-r15" / "run.ps1"
R16_RUNNER = HARNESS_ROOT / "control-r16" / "run.ps1"
R16_WSB = HARNESS_ROOT / "unity-controlled-r16.wsb"


def test_r15_timeout_and_shutdown_remain_preserved_as_historical_evidence():
    source = R15_RUNNER.read_text(encoding="utf-8")
    assert "$activationWaitLimitSeconds = 1800" in source
    assert "shutdown.exe /s /t 0 /f" in source


def test_r16_wait_is_manual_and_has_no_automatic_shutdown_path():
    source = R16_RUNNER.read_text(encoding="utf-8")
    assert "Deliberately no elapsed-time cutoff" in source
    assert "$activationWaitLimitSeconds" not in source
    assert "automatic_timeout_seconds = $null" in source
    assert "automatic_shutdown_before_trigger = $false" in source
    assert "abort-wait.trigger" in source
    assert "MANUAL_HUB_LOGIN_CONFIRMED_BY_USER=true" in source
    assert "MANUAL_WAIT_ABORT_REQUESTED_BY_USER=true" in source
    shutdown = "shutdown.exe /s /t 0 /f"
    assert source.count(shutdown) == 2
    assert "if ($triggerObserved -or $waitAborted)" in source
    assert source.rfind("if ($triggerObserved -or $waitAborted)") < source.rfind(shutdown)


def test_r16_persists_installation_in_a_dedicated_writable_mount():
    tree = ET.parse(R16_WSB)
    mappings = {
        node.findtext("HostFolder"): node
        for node in tree.findall("./MappedFolders/MappedFolder")
    }
    install_host = next(
        host for host in mappings if host and host.endswith("\\unity-install-r16")
    )
    output_host = next(host for host in mappings if host and host.endswith("\\output-r16"))
    assert mappings[install_host].findtext("SandboxFolder") == r"C:\UnityInstall"
    assert mappings[install_host].findtext("ReadOnly") == "false"
    assert mappings[output_host].findtext("ReadOnly") == "false"


def test_r16_keeps_product_fixture_and_known_editor_read_only():
    tree = ET.parse(R16_WSB)
    mappings = tree.findall("./MappedFolders/MappedFolder")
    fixture = next(node for node in mappings if node.findtext("SandboxFolder") == r"C:\input")
    editor = next(node for node in mappings if node.findtext("SandboxFolder") == r"C:\Unity\Editor")
    assert fixture.findtext("ReadOnly") == "true"
    assert editor.findtext("ReadOnly") == "true"
    assert tree.findtext("./LogonCommand/Command") == (
        r"powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\control-r16\prepare-browser-and-run.ps1"
    )
