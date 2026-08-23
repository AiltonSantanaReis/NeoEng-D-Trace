"""Audit the complete Stage 2 icon catalog across deterministic Qt DPI scales.

The worker runs in a fresh Qt process for every scale so that the scale factor
is applied before ``QApplication`` is created.  It reuses the real MainWindow
capture and the embedded production icon catalog; it does not monkeypatch
widgets, replace icons, or change any existing acceptance threshold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = (
    ROOT / "docs" / "evidence" / "artifacts" / "ui-modernization-stage2-dpi-20260823"
)

DPI_CASES: tuple[tuple[str, float], ...] = (
    ("100", 1.0),
    ("125", 1.25),
    ("150", 1.5),
    ("200", 2.0),
)
ICON_SIZES: tuple[int, ...] = (16, 20, 24, 32)
GALLERY_BACKGROUND = "#20262e"


def _digest(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _safe_command(command: list[str]) -> list[str]:
    result: list[str] = []
    for value in command:
        if value == sys.executable:
            result.append(".venv/Scripts/python.exe")
            continue
        try:
            result.append(Path(value).resolve().relative_to(ROOT).as_posix())
        except (OSError, ValueError):
            result.append(value)
    return result


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).strip()


def _source_state() -> dict[str, Any]:
    return {
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "worktree_clean": not bool(_git("status", "--porcelain")),
    }


def _validate_cases() -> None:
    if tuple(percent for percent, _ in DPI_CASES) != ("100", "125", "150", "200"):
        raise AssertionError("the Stage 2 DPI matrix must remain 100/125/150/200")
    if any(factor <= 0 for _, factor in DPI_CASES):
        raise AssertionError("DPI factors must be positive")
    if any(left[1] >= right[1] for left, right in zip(DPI_CASES, DPI_CASES[1:])):
        raise AssertionError("DPI factors must be strictly increasing")


def _run_worker(percent: str, factor: float, output: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--percent",
        percent,
        "--factor",
        str(factor),
        "--output",
        str(output),
    ]
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_SCALE_FACTOR"] = str(factor)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    log = output / "worker.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
    return {
        "command": _safe_command(command),
        "returncode": completed.returncode,
        "log": log.relative_to(ROOT).as_posix(),
    }


def _run_visual_audit(raw: Path, visual: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "audit_visual_artifacts.py"),
        "--input",
        str(raw),
        "--output",
        str(visual),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    log = visual.parent / "visual-audit.log"
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8", newline="\n")
    report = visual / "visual-audit-report.json"
    parsed = json.loads(report.read_text(encoding="utf-8")) if report.is_file() else {}
    return {
        "command": _safe_command(command),
        "returncode": completed.returncode,
        "log": log.relative_to(ROOT).as_posix(),
        "report": (
            {"path": report.relative_to(ROOT).as_posix(), **_digest(report)}
            if report.is_file()
            else None
        ),
        "status": parsed.get("status", "MISSING"),
        "finding_count": parsed.get("finding_count"),
    }


def _gallery_worker(output: Path, factor: float) -> dict[str, Any]:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ["QT_SCALE_FACTOR"] = str(factor)

    from PySide6.QtCore import QSize, Qt  # noqa: PLC0415
    from PySide6.QtWidgets import (  # noqa: PLC0415
        QApplication,
        QGridLayout,
        QLabel,
        QToolButton,
        QWidget,
    )

    from src.ui.icon_library import ICON_SPECS, icon_for  # noqa: PLC0415
    from src.ui.theme_qss import QSS  # noqa: PLC0415

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    gallery = QWidget()
    gallery.setStyleSheet(
        f"QWidget {{ background-color: {GALLERY_BACKGROUND}; }}"
        "QToolButton { background-color: #20262e; border: 0px; padding: 0px; }"
    )
    gallery.setWindowTitle("NeoEng-D-Trace Stage 2 icon DPI gallery")
    layout = QGridLayout(gallery)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setHorizontalSpacing(10)
    layout.setVerticalSpacing(4)

    layout.addWidget(QLabel("icon key"), 0, 0)
    for column, size in enumerate(ICON_SIZES, start=1):
        label = QLabel(f"{size}px")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, 0, column)

    records: list[dict[str, Any]] = []
    for row, key in enumerate(sorted(ICON_SPECS), start=1):
        name = QLabel(key)
        name.setObjectName(f"label_{key}")
        layout.addWidget(name, row, 0)
        icon = icon_for(key)
        for column, size in enumerate(ICON_SIZES, start=1):
            button = QToolButton()
            button.setObjectName(f"icon_{key}_{size}")
            button.setIcon(icon)
            button.setIconSize(QSize(size, size))
            button.setFixedSize(QSize(56, 44))
            button.setToolTip(key)
            button.setAccessibleName(f"{key} {size}px")
            layout.addWidget(button, row, column)
            records.append(
                {
                    "key": key,
                    "size": size,
                    "object_name": button.objectName(),
                    "logical_geometry": [
                        button.geometry().x(),
                        button.geometry().y(),
                        button.geometry().width(),
                        button.geometry().height(),
                    ],
                    "icon_available_sizes": [
                        [item.width(), item.height()] for item in icon.availableSizes()
                    ],
                }
            )

    gallery.adjustSize()
    gallery.show()
    app.processEvents()
    # Layout geometry is only final after the event loop has processed show().
    for record in records:
        button = gallery.findChild(QToolButton, record["object_name"])
        if button is None:
            raise RuntimeError(f"gallery button missing: {record['object_name']}")
        record["logical_geometry"] = [
            button.geometry().x(),
            button.geometry().y(),
            button.geometry().width(),
            button.geometry().height(),
        ]

    pixmap = gallery.grab()
    image_path = output / "icon-gallery.png"
    if not pixmap.save(str(image_path), "PNG"):
        raise RuntimeError("could not save the icon gallery")
    screen = app.primaryScreen()
    observed_dpr = float(pixmap.devicePixelRatio())
    if screen is not None:
        observed_dpr = float(screen.devicePixelRatio())
    runtime = {
        "requested_scale_factor": factor,
        "observed_device_pixel_ratio": observed_dpr,
        "logical_dpi": (
            [screen.logicalDotsPerInchX(), screen.logicalDotsPerInchY()]
            if screen is not None
            else None
        ),
        "physical_dpi": (
            [screen.physicalDotsPerInchX(), screen.physicalDotsPerInchY()]
            if screen is not None
            else None
        ),
        "gallery_logical_size": [gallery.width(), gallery.height()],
        "gallery_physical_size": [pixmap.width(), pixmap.height()],
        "catalog_keys": sorted(ICON_SPECS),
        "catalog_size": len(ICON_SPECS),
        "icon_sizes": list(ICON_SIZES),
        "buttons": records,
        "gallery": {"path": image_path.name, **_digest(image_path)},
    }
    (output / "gallery-runtime.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    gallery.close()
    return runtime


def _validate_gallery_png(path: Path, runtime: dict[str, Any]) -> dict[str, Any]:
    with Image.open(path) as source:
        source.verify()
    with Image.open(path) as source:
        image = source.convert("RGB")
    decoded = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if decoded is None:
        raise AssertionError("OpenCV could not decode icon gallery")
    if [image.width, image.height] != [decoded.shape[1], decoded.shape[0]]:
        raise AssertionError("Pillow/OpenCV dimensions disagree")

    array = np.asarray(image, dtype=np.int16)
    background = np.asarray([32, 38, 46], dtype=np.int16)
    border = np.concatenate(
        (
            array[0:2, :, :].reshape(-1, 3),
            array[-2:, :, :].reshape(-1, 3),
            array[:, 0:2, :].reshape(-1, 3),
            array[:, -2:, :].reshape(-1, 3),
        )
    )
    border_error = int(np.abs(border - background).max())
    if border_error > 0:
        raise AssertionError(f"gallery content reaches outer border: {border_error}")

    dpr = float(runtime["observed_device_pixel_ratio"])
    clipping_failures: list[str] = []
    for record in runtime["buttons"]:
        x, y, width, height = record["logical_geometry"]
        left = max(0, int(round(x * dpr)))
        top = max(0, int(round(y * dpr)))
        right = min(image.width, int(round((x + width) * dpr)))
        bottom = min(image.height, int(round((y + height) * dpr)))
        crop = array[top:bottom, left:right, :]
        if crop.size == 0:
            clipping_failures.append(f"{record['key']}/{record['size']}: empty cell")
            continue
        mask = np.any(np.abs(crop - background) > 8, axis=2)
        if int(mask.sum()) < 4:
            clipping_failures.append(f"{record['key']}/{record['size']}: icon absent")
            continue
        ys, xs = np.where(mask)
        margin = max(2, int(round(3 * dpr)))
        if (
            int(xs.min()) < margin
            or int(ys.min()) < margin
            or int(xs.max()) >= crop.shape[1] - margin
            or int(ys.max()) >= crop.shape[0] - margin
        ):
            clipping_failures.append(
                f"{record['key']}/{record['size']}: icon touches cell boundary"
            )
    return {
        "status": "PASS" if not clipping_failures else "FAIL",
        "size": [image.width, image.height],
        "sha256": _digest(path)["sha256"],
        "clipping_failures": clipping_failures,
        "checked_cells": len(runtime["buttons"]),
    }


def _worker_main(args: argparse.Namespace) -> int:
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    from scripts.audit_ui_capture import run as capture_run

    raw = output / "raw-captures"
    capture_run(raw)
    runtime = _gallery_worker(output, args.factor)
    gallery_validation = _validate_gallery_png(output / "icon-gallery.png", runtime)
    worker_report = {
        "schema_version": 1,
        "percent": args.percent,
        "factor": args.factor,
        "source_state": _source_state(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
            "qt_scale_factor": os.environ.get("QT_SCALE_FACTOR"),
        },
        "raw_manifest": {
            "path": "raw-captures/manifest.json",
            **_digest(raw / "manifest.json"),
        },
        "runtime": runtime,
        "gallery_validation": gallery_validation,
        "status": "PASS" if gallery_validation["status"] == "PASS" else "FAIL",
    }
    (output / "worker-report.json").write_text(
        json.dumps(worker_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": worker_report["status"], "percent": args.percent}))
    return 0 if worker_report["status"] == "PASS" else 1


def _write_index(root: Path, index_path: Path) -> None:
    files: dict[str, Any] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != index_path:
            files[path.relative_to(root).as_posix()] = _digest(path)
    index_path.write_text(
        json.dumps({"schema_version": 1, "files": files}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _main(args: argparse.Namespace) -> int:
    _validate_cases()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(
            f"Refusing to overwrite non-empty evidence directory: {output}"
        )
    output.mkdir(parents=True, exist_ok=True)
    cases: dict[str, Any] = {}
    failures: list[str] = []
    for percent, factor in DPI_CASES:
        case_root = output / f"dpi-{percent}"
        worker = _run_worker(percent, factor, case_root)
        raw = case_root / "raw-captures"
        visual = _run_visual_audit(raw, case_root / "visual-audit")
        worker_report_path = case_root / "worker-report.json"
        worker_report = json.loads(worker_report_path.read_text(encoding="utf-8"))
        if worker["returncode"] != 0:
            failures.append(f"dpi-{percent}: worker failed")
        if visual["returncode"] != 0 or visual["status"] != "PASS":
            failures.append(f"dpi-{percent}: visual audit failed")
        if worker_report["runtime"]["observed_device_pixel_ratio"] != factor:
            failures.append(
                f"dpi-{percent}: observed DPR differs from requested factor"
            )
        cases[percent] = {
            "factor": factor,
            "worker": worker,
            "worker_report": {
                "path": worker_report_path.relative_to(ROOT).as_posix(),
                **_digest(worker_report_path),
            },
            "visual_audit": visual,
        }

    report = {
        "schema_version": 1,
        "stage": "Etapa 2 — Matriz DPI da biblioteca de ícones",
        "source_state": _source_state(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "cases": cases,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
    }
    report_path = output / "stage2-dpi-matrix-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    lines = [
        "# Etapa 2 — Matriz DPI da biblioteca de ícones",
        "",
        f"Status local: **{report['status']}**",
        "",
        "A matriz executa a MainWindow e uma galeria do catálogo vetorial em "
        "processos Qt separados nas escalas 100%, 125%, 150% e 200%.",
        "",
        "| Escala | Fator | Worker | Auditor visual |",
        "|---:|---:|---|---|",
    ]
    for percent, factor in DPI_CASES:
        case = cases[percent]
        lines.append(
            f"| {percent}% | {factor} | "
            f"{case['worker']['returncode']} | {case['visual_audit']['status']} |"
        )
    lines += [
        "",
        "O relatório JSON, os manifests, as capturas, as galerias e os logs são "
        "indexados por SHA-256 no `artifact-index.json`.",
        "",
        "A árvore modificada durante a coleta não é tratada como validação pós-commit; "
        "o gate Git-blob e o CI permanecem obrigatórios.",
    ]
    (output / "stage2-dpi-matrix-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )
    _write_index(output, output / "artifact-index.json")
    print(json.dumps({"status": report["status"], "failures": failures}))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--percent")
    parser.add_argument("--factor", type=float)
    args = parser.parse_args()
    if args.worker:
        if not args.percent or args.factor is None:
            parser.error("--worker requires --percent and --factor")
        return _worker_main(args)
    return _main(args)


if __name__ == "__main__":
    raise SystemExit(main())
