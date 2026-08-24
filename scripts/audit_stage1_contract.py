"""Audit the Stage 1 visual-token contract without changing production code.

The historical geometry comparator is intentionally kept separate from this
contract audit.  Stage 1 owns application-chrome tokens and QSS states; canvas,
gizmo, and scenario-rendering colors are content semantics and are recorded as
forward-compatibility scope rather than treated as chrome violations.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import platform
import re
import subprocess
import sys
from dataclasses import fields
from pathlib import Path
from typing import Any

from src.ui.theme_qss import QSS, build_qss
from src.ui.theme_tokens import THEME_TOKENS, token_contrast_ratios

HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
REQUIRED_TOKENS = (
    "window",
    "canvas",
    "surface",
    "surface_alt",
    "surface_raised",
    "border",
    "border_strong",
    "text_primary",
    "text_secondary",
    "text_disabled",
    "accent",
    "accent_hover",
    "accent_pressed",
    "selection",
    "focus",
    "error",
    "warning",
    "success",
)
REQUIRED_STATES = (
    "hover",
    "pressed",
    "checked",
    "disabled",
    "focus",
)
FORBIDDEN_COLORS = ("#FF4500", "#00BFFF")
CONTENT_COLOR_FILES = {
    "src/ui/scene_authoring_inspector.py",
    "src/ui/scene_authoring_viewport.py",
    "src/ui/viewport_chrome.py",
}
TOKEN_DEFINITION_FILES = {"src/ui/theme_tokens.py"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout.strip()


def _qss_state_presence() -> dict[str, bool]:
    return {
        state: f":{state}" in QSS
        for state in REQUIRED_STATES
    }


def _inline_style_files(repo_root: Path) -> list[str]:
    offenders: list[str] = []
    for root_name in ("src/ui", "src/tools"):
        root = repo_root / root_name
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in {"setStyleSheet", "setPalette"}:
                        offenders.append(path.relative_to(repo_root).as_posix())
                        break
    return sorted(set(offenders))


def _direct_color_inventory(repo_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for root_name in ("src/ui", "src/tools"):
        root = repo_root / root_name
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(repo_root).as_posix()
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                for match in HEX_RE.finditer(line):
                    entries.append(
                        {
                            "file": relative,
                            "line": line_number,
                            "color": match.group(0).upper(),
                            "classification": (
                                "TOKEN_DEFINITION"
                                if relative in TOKEN_DEFINITION_FILES
                                else (
                                    "CONTENT_SEMANTICS"
                                    if relative in CONTENT_COLOR_FILES
                                    else "APPLICATION_CHROME_REVIEW"
                                )
                            ),
                        }
                    )
    chrome = [item for item in entries if item["classification"] == "APPLICATION_CHROME_REVIEW"]
    return {
        "all_entries": entries,
        "application_chrome_review_entries": chrome,
        "content_semantics_entries": [
            item for item in entries if item["classification"] == "CONTENT_SEMANTICS"
        ],
        "token_definition_entries": [
            item for item in entries if item["classification"] == "TOKEN_DEFINITION"
        ],
        "pass": not chrome,
    }


def run(repo_root: Path, historical_report: Path | None = None) -> dict[str, Any]:
    fields_in_schema = tuple(field.name for field in fields(THEME_TOKENS))
    colors = THEME_TOKENS.colors
    ratios = token_contrast_ratios()
    qss_states = _qss_state_presence()
    inline_styles = _inline_style_files(repo_root)
    color_inventory = _direct_color_inventory(repo_root)
    checks = {
        "required_token_schema": fields_in_schema == REQUIRED_TOKENS,
        "hex_colors_valid": all(
            isinstance(color, str)
            and bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", color))
            for color in colors
        ),
        "token_colors_unique": len(colors) == len(set(colors)),
        "primary_text_contrast": ratios["primary_on_window"] >= 4.5,
        "secondary_text_contrast": ratios["secondary_on_surface"] >= 4.5,
        "focus_contrast": ratios["focus_on_window"] >= 3.0,
        "qss_is_generated_from_tokens": build_qss(THEME_TOKENS) == QSS,
        "qss_required_states": all(qss_states.values()),
        "qss_required_roles": 'QPushButton[uiRole="tool"]' in QSS,
        "forbidden_colors_absent": not any(
            color.upper() in QSS.upper() for color in FORBIDDEN_COLORS
        ),
        "no_inline_application_styles": not inline_styles,
        "no_unclassified_direct_chrome_colors": color_inventory["pass"],
    }
    historical: dict[str, Any]
    if historical_report and historical_report.exists():
        old = json.loads(historical_report.read_text(encoding="utf-8"))
        historical = {
            "source": historical_report.as_posix(),
            "sha256": _sha256(historical_report),
            "status": old.get("status", "UNKNOWN"),
            "finding_count": len(old.get("findings", [])),
            "unexpected_geometry_delta_count": len(old.get("unexpected_geometry_deltas", [])),
            "classification": "HISTORICAL_ONLY",
            "interpretation": (
                "Retained diagnostically. Its geometry reference predates the final-target "
                "UI architecture and is not evidence that the current token contract fails."
            ),
        }
    else:
        historical = {
            "source": None,
            "status": "NOT_AVAILABLE",
            "finding_count": None,
            "unexpected_geometry_delta_count": None,
            "classification": "REVIEW_REQUIRED",
            "interpretation": "Historical comparator report was not supplied.",
        }
    current_pass = all(checks.values())
    report = {
        "schema": "neoeng.stage1-contract-audit",
        "schema_version": 1,
        "stage": 1,
        "stage_name": "Sistema visual e tokens de tema",
        "decision_scope": "auditoria técnica da Etapa 1; não é aprovação humana ou de release",
        "source": {
            "commit": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "worktree_clean_tracked": not bool(_git("status", "--porcelain", "--untracked-files=no")),
        },
        "environment": {"platform": platform.platform(), "python": sys.version},
        "current_contract_result": "PASS" if current_pass else "FAIL",
        "historical_result": historical,
        "consolidated_decision": (
            "PASS_WITH_HISTORICAL_EVOLUTION" if current_pass else "REVIEW_REQUIRED"
        ),
        "classifications": [
            "HISTORICAL_ONLY",
            "EXPECTED_EVOLUTION",
            "INVARIANT_REGRESSION",
            "FORWARD_COMPATIBILITY_RISK",
            "UNCLASSIFIED_CHANGE",
        ],
        "checks": checks,
        "evidence": {
            "token_schema": list(fields_in_schema),
            "token_values": {name: getattr(THEME_TOKENS, name) for name in fields_in_schema},
            "contrast_ratios": ratios,
            "qss_sha256": hashlib.sha256(QSS.encode("utf-8")).hexdigest(),
            "qss_states": qss_states,
            "forbidden_colors": list(FORBIDDEN_COLORS),
            "inline_style_files": inline_styles,
            "direct_color_inventory": color_inventory,
        },
        "limitations": [
            "Canvas/gizmo/scenario literal colors are content semantics and require their own later-stage contracts.",
            "Visual geometry remains represented by the historical comparator and must be reviewed with the final-target visual evidence.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--historical-report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo_root.resolve(), args.historical_report.resolve() if args.historical_report else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"current_contract_result": report["current_contract_result"], "consolidated_decision": report["consolidated_decision"]}, sort_keys=True))
    return 0 if report["current_contract_result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
