"""Real, deterministic boundaries for the legacy-26 Phase 1 contracts.

This module deliberately contains no generic test doubles and no product
fallbacks.  It only creates the concrete objects and inputs that the Phase 1
replacement tests are required to exercise.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from PySide6.QtCore import (
    QEvent,
    QEventLoop,
    QObject,
    QPointF,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent

from src.core.commands import CommandManager
from src.models.scene import Scene
from src.ui.canvas_view import CanvasView


@dataclass(frozen=True)
class PolygonFixture:
    """Versioned polygon input with an explicit expected digest."""

    name: str
    classification: str
    points: tuple[tuple[int, int], ...]
    expected_sha256: str

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "name": self.name,
            "points": [list(point) for point in self.points],
        }

    @property
    def sha256(self) -> str:
        encoded = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


POLYGON_FIXTURES: tuple[PolygonFixture, ...] = (
    PolygonFixture(
        name="valid_rectangle",
        classification="valid",
        points=((0, 0), (40, 0), (40, 30), (0, 30)),
        expected_sha256=(
            "b8265ae9ee5689ecb369b10d40e3e5d3341ba26d573c70b0d360a0b4c327079c"
        ),
    ),
    PolygonFixture(
        name="valid_l_shape",
        classification="valid",
        points=((0, 0), (40, 0), (40, 30), (15, 30), (15, 15), (0, 15)),
        expected_sha256=(
            "28af06744716740f6d689d68e71bb511d2230cae5004071ae35b38f8a7526361"
        ),
    ),
    PolygonFixture(
        name="invalid_self_overlapping",
        classification="invalid_self_intersection",
        points=((0, 0), (40, 0), (40, 30), (15, 30), (15, 15), (0, 15), (0, 30)),
        expected_sha256=(
            "eef2a568bc4486a803d2922b1b80ccfea7367fe3537b27e25efebe0181f3ad0a"
        ),
    ),
    PolygonFixture(
        name="invalid_collinear",
        classification="invalid_zero_area",
        points=((0, 0), (20, 0), (40, 0)),
        expected_sha256=(
            "0f5918683d9350629d0ca078d5feae21d78a6e77bf3a33409ffff142d223cd52"
        ),
    ),
)


def synthetic_image_array(width: int = 32, height: int = 24) -> np.ndarray:
    """Return a fixed grayscale image with a deterministic high-contrast edge."""

    if width < 8 or height < 8:
        raise ValueError("synthetic image dimensions must be at least 8x8")
    image = np.zeros((height, width), dtype=np.uint8)
    image[3 : height - 3, width // 2 - 1 : width // 2 + 1] = 255
    image[height // 2 - 1 : height // 2 + 1, 3 : width - 3] = 180
    return image


def qimage_from_array(image: np.ndarray) -> QImage:
    """Copy a valid uint8 grayscale ndarray into an owned real QImage."""

    if image.dtype != np.uint8 or image.ndim != 2 or not image.flags.c_contiguous:
        raise ValueError("QImage fixture requires a contiguous uint8 grayscale array")
    height, width = image.shape
    return QImage(
        image.data,
        int(width),
        int(height),
        int(image.strides[0]),
        QImage.Format.Format_Grayscale8,
    ).copy()


def real_scene(
    *, image: object | None = None, image_path: str = "fixture://phase1"
) -> Scene:
    """Create a concrete Scene with a concrete CommandManager."""

    scene = Scene()
    scene.cmd = CommandManager(max_history=50)
    if image is not None:
        scene.load_image(image, image_path)
    return scene


def real_canvas(scene: Scene) -> CanvasView:
    """Create a concrete CanvasView bound to the supplied concrete Scene."""

    return CanvasView(scene)


def scene_state_token(scene: Scene) -> tuple[Any, ...]:
    """Capture only functional scene state needed for rollback assertions."""

    objects = tuple(
        (
            object_id,
            tuple(tuple(point) for point in object_value.polygon),
            object_value.layer_id,
        )
        for object_id, object_value in scene.objects.items()
    )
    layers = tuple(
        (layer.id, layer.name, bool(layer.visible), bool(layer.locked))
        for layer in scene.layers
    )
    return (
        objects,
        layers,
        tuple(scene.selected_ids),
        scene.selected_id,
        tuple(sorted(scene.collision_shapes)),
        tuple(sorted(scene.collision_parts)),
    )


def mouse_event(
    event_type: QEvent.Type,
    x: float,
    y: float,
    *,
    button: Qt.MouseButton = Qt.MouseButton.LeftButton,
    buttons: Qt.MouseButton | None = None,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> QMouseEvent:
    """Build a native Qt mouse event without a generic test double."""

    active_buttons = button if buttons is None else buttons
    position = QPointF(float(x), float(y))
    return QMouseEvent(
        event_type,
        position,
        position,
        position,
        button,
        active_buttons,
        modifiers,
    )


def key_event(
    key: Qt.Key,
    *,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> QKeyEvent:
    """Build a native Qt key event."""

    return QKeyEvent(QEvent.Type.KeyPress, key, modifiers)


class DeterministicSignalEmitter(QObject):
    """Concrete QObject used to verify event-loop synchronization."""

    ready = Signal(object)


def wait_for_signal(
    signal: Any,
    trigger: Callable[[], None],
    *,
    timeout_ms: int = 1000,
) -> tuple[Any, ...]:
    """Run a trigger and wait for its signal or raise an explicit timeout."""

    if timeout_ms <= 0:
        raise ValueError("timeout_ms must be positive")

    loop = QEventLoop()
    timeout = QTimer()
    timeout.setSingleShot(True)
    captured: tuple[Any, ...] | None = None

    def on_signal(*args: Any) -> None:
        nonlocal captured
        captured = args
        loop.quit()

    signal.connect(on_signal)
    try:
        trigger()
        if captured is None:
            timeout.timeout.connect(loop.quit)
            timeout.start(timeout_ms)
            loop.exec()
    finally:
        timeout.stop()
        try:
            signal.disconnect(on_signal)
        except (TypeError, RuntimeError):
            pass

    if captured is None:
        raise TimeoutError(f"signal was not received within {timeout_ms} ms")
    return captured


__all__ = [
    "DeterministicSignalEmitter",
    "POLYGON_FIXTURES",
    "PolygonFixture",
    "key_event",
    "mouse_event",
    "qimage_from_array",
    "real_canvas",
    "real_scene",
    "scene_state_token",
    "synthetic_image_array",
    "wait_for_signal",
]
