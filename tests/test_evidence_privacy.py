"""Fail-closed privacy checks for versioned evidence artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.audit_native_advanced_stage8 import sanitize as sanitize_stage8
from scripts.audit_native_stage10 import sanitize_output as sanitize_stage10
from scripts.audit_unity_package_stage5 import _sanitize as sanitize_stage5

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "docs" / "evidence" / "artifacts"

FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)[A-Z]:[\\/]Users[\\/][^\r\n\"<>]+"),
    re.compile(r"(?i)LicenseClient-(?!<redacted>)[A-Za-z0-9_.-]+"),
    re.compile(r"(?i)\bPId:\s*\d+"),
    re.compile(r"(?i)\bprocessId\"?\s*[:=]\s*\d+"),
    re.compile(r"(?i)\bprocess\s+Id:\s*\d+"),
    re.compile(r"(?i)WindowsEditor\((?!<redacted>)[^)]*\)"),
    re.compile(r"(?im)^.*Player connection\s*\[\d+\].*$"),
    re.compile(
        r"(?im)^\s*(?:Machine Id|Session Id|Correlation Id|"
        r"External correlation Id):\s*(?!<redacted>).+"
    ),
)


def test_versioned_evidence_artifacts_contain_no_unredacted_host_data() -> None:
    violations: list[str] = []
    text_suffixes = {
        ".cfg",
        ".cs",
        ".gd",
        ".json",
        ".log",
        ".md",
        ".ndtproj",
        ".res",
        ".tres",
        ".tscn",
        ".txt",
        ".xml",
    }
    for path in sorted(ARTIFACTS.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                violations.append(
                    f"{path.relative_to(ROOT).as_posix()}: {pattern.pattern}"
                )
    assert violations == []


def test_stage5_and_stage8_sanitizers_redact_engine_host_data(tmp_path: Path) -> None:
    raw = (
        "LicenseClient-user-token PId: 1234 process Id: "
        "5678 "
        "WindowsEditor(7,user) Player connection [42]\n"
    )
    for sanitizer in (sanitize_stage5, sanitize_stage8):
        sanitized = sanitizer(raw, tmp_path)
        assert "LicenseClient-user-token" not in sanitized
        assert "PId: 1234" not in sanitized
        assert "process Id: 5678" not in sanitized
        assert "WindowsEditor(7,user)" not in sanitized
        assert "Player connection [42]" not in sanitized


def test_sanitizers_preserve_json_structure(tmp_path: Path) -> None:
    raw = json.dumps(
        {
            "output": (
                "Player connection [42]  Target information:\\n"
                "Date: secret\\ndebugger-agent: localhost"
            )
        }
    )
    for sanitizer in (sanitize_stage5, sanitize_stage8, sanitize_stage10):
        sanitized = sanitizer(raw, tmp_path)
        json.loads(sanitized)
        assert "Player connection [42]" not in sanitized
        assert "Date: secret" not in sanitized
        assert "debugger-agent" not in sanitized
