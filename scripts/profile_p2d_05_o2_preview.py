"""Produce local-only CPU profiles for the accepted P2D-05/O-2 baseline."""

from __future__ import annotations

import argparse
import cProfile
import os
import subprocess
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QApplication

from scripts.benchmark_p2d_05_o2_preview_reuse import (
    _Harness,
    _operation,
    _representative_document,
)

O2_HEAD = "15300a0d580a57110828d8511ae48a0f68326e3a"


def _git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
    ).strip()


def _profile(
    *,
    output: Path,
    operation_name: str,
    count: int,
    asset_mode: str,
    calls: int,
    application: QApplication,
) -> None:
    with tempfile.TemporaryDirectory(prefix="neoeng-p2d05-o2-profile-") as name:
        root = Path(name)
        document = _representative_document(root, count, asset_mode)
        harness = _Harness(document, root, application, 1920, 1080)
        try:
            harness.reset()
            operation, _ = _operation(operation_name, harness)
            for _ in range(2):
                operation()
            harness.reset()
            profiler = cProfile.Profile()
            profiler.enable()
            for _ in range(calls):
                operation()
            profiler.disable()
            output.parent.mkdir(parents=True, exist_ok=True)
            profiler.dump_stats(str(output))
        finally:
            harness.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if _git_head() != O2_HEAD:
        parser.error("O-2 profiles must run at the accepted O-2 HEAD")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    application = QApplication.instance() or QApplication([])
    profiles = (
        ("o2-full-sync-512-unique.prof", "full_sync", 512, "unique", 5),
        (
            "o2-incremental-refresh-512-shared.prof",
            "incremental_refresh",
            512,
            "shared",
            20,
        ),
        (
            "o2-preview-frame-512-shared.prof",
            "preview_frame_build",
            512,
            "shared",
            50,
        ),
        (
            "o2-structural-isolation-512-unique.prof",
            "group_isolation_toggle",
            512,
            "unique",
            5,
        ),
    )
    for filename, operation, count, asset_mode, calls in profiles:
        _profile(
            output=args.output_dir / filename,
            operation_name=operation,
            count=count,
            asset_mode=asset_mode,
            calls=calls,
            application=application,
        )
        print(filename)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
