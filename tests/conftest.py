"""Shared pytest bootstrap for deterministic headless Qt tests."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
