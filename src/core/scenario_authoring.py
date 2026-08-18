"""Qt-independent authoring state for the lateral scenario sidecar.

The authoring document is intentionally separate from :class:`Scene`.  This
module provides the transactional state and history used by the UI while the
versioned JSON contract and atomic file replacement remain in
``src.persistence.scenario_io``.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable, Iterable

from src.core.commands import Command, CommandResult, CommandStatus
from src.core.parallax_camera import OrthographicCamera, ParallaxLayer
from src.core.scenario_preview import ScenarioPreviewLayer
from src.models.scene import Scene
from src.persistence.project_schema import PointRecord
from src.persistence.scenario_io import (
    load_scenario,
    project_reference_for,
    save_scenario,
    scenario_sha256,
)
from src.persistence.scenario_schema import (
    SCENARIO_FILE_EXTENSION,
    ScenarioCameraRecord,
    ScenarioDocumentV1,
    ScenarioLayerRecord,
    ScenarioParallaxRecord,
    default_scenario_metadata,
)


class ScenarioAuthoringError(ValueError):
    """Raised when a scenario authoring operation cannot be applied safely."""


def _validated(payload: dict[str, Any]) -> ScenarioDocumentV1:
    return ScenarioDocumentV1.model_validate(payload, strict=True)


def _copy_payload(document: ScenarioDocumentV1) -> dict[str, Any]:
    return copy.deepcopy(document.model_dump(mode="python"))


def _with_layers(
    document: ScenarioDocumentV1,
    layers: Iterable[ScenarioLayerRecord],
) -> ScenarioDocumentV1:
    payload = _copy_payload(document)
    payload["layers"] = [layer.model_dump(mode="python") for layer in layers]
    return _validated(payload)


def _layer(document: ScenarioDocumentV1, layer_id: str) -> ScenarioLayerRecord:
    for item in document.layers:
        if item.id == layer_id:
            return item
    raise ScenarioAuthoringError(f"scenario layer not found: {layer_id}")


def _replace_layer(
    document: ScenarioDocumentV1,
    layer_id: str,
    replacement: ScenarioLayerRecord,
) -> ScenarioDocumentV1:
    return _with_layers(
        document,
        (replacement if item.id == layer_id else item for item in document.layers),
    )


def _default_document(project_path: Path, scene: Scene) -> ScenarioDocumentV1:
    if not project_path.is_file() or project_path.suffix.lower() != ".ndtproj":
        raise ScenarioAuthoringError(
            "a saved .ndtproj is required before authoring a scenario"
        )
    object_ids_by_layer: dict[str, list[str]] = {layer.id: [] for layer in scene.layers}
    fallback = scene.layers[0].id if scene.layers else "layer_default"
    for object_id, obj in scene.objects.items():
        object_ids_by_layer.setdefault(obj.layer_id or fallback, []).append(object_id)
    layers = [
        ScenarioLayerRecord(
            id=layer.id,
            name=layer.name,
            visible=bool(layer.visible),
            object_ids=object_ids_by_layer.get(layer.id, []),
            parallax=ScenarioParallaxRecord(),
        )
        for layer in scene.layers
    ]
    if not layers:
        layers = [
            ScenarioLayerRecord(
                id="layer_default",
                name="Default",
                object_ids=[],
                parallax=ScenarioParallaxRecord(),
            )
        ]
    name = project_path.stem[:64] or "Scenario"
    return ScenarioDocumentV1(
        metadata=default_scenario_metadata(name),
        project=project_reference_for(project_path),
        camera=ScenarioCameraRecord(position=PointRecord(x=0.0, y=0.0), zoom=1.0),
        layers=layers,
    )


class ReplaceScenarioDocumentCommand(Command):
    """Replace one validated document with exact Undo/Redo preconditions."""

    def __init__(
        self,
        before: ScenarioDocumentV1,
        after: ScenarioDocumentV1,
        description: str,
    ) -> None:
        self.before = before
        self.after = after
        self.description = description

    def execute(self, state: "ScenarioAuthoringState") -> CommandResult:
        if state.document != self.before:
            return CommandResult.rejected(
                self,
                "execute",
                "Scenario changed before Redo; the operation was rejected.",
            )
        state._set_document(self.after)
        return CommandResult.applied(self, "execute", self.description)

    def undo(self, state: "ScenarioAuthoringState") -> CommandResult:
        if state.document != self.after:
            return CommandResult.rejected(
                self,
                "undo",
                "Scenario changed before Undo; the operation was rejected.",
            )
        state._set_document(self.before)
        return CommandResult.applied(self, "undo", self.description)


class ScenarioCommandManager:
    """Small transactional history dedicated to the scenario sidecar."""

    def __init__(self, max_history: int = 100) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.max_history = int(max_history)
        self._undo: list[ReplaceScenarioDocumentCommand] = []
        self._redo: list[ReplaceScenarioDocumentCommand] = []
        self._listeners: list[Callable[[], None]] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    @property
    def undo_count(self) -> int:
        return len(self._undo)

    @property
    def redo_count(self) -> int:
        return len(self._redo)

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback()

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._notify()

    def execute(
        self,
        command: ReplaceScenarioDocumentCommand,
        state: "ScenarioAuthoringState",
    ) -> CommandResult:
        before = state.document_or_raise()
        try:
            result = command.execute(state)
        except Exception as exc:
            if state.document != before:
                state._set_document(before)
            return CommandResult.failed(
                command,
                "execute",
                type(exc).__name__,
                "The scenario operation failed and was restored.",
            )
        if result.status is not CommandStatus.APPLIED:
            return result
        self._undo.append(command)
        if len(self._undo) > self.max_history:
            del self._undo[: len(self._undo) - self.max_history]
        self._redo.clear()
        self._notify()
        return result

    def undo(self, state: "ScenarioAuthoringState") -> CommandResult:
        if not self._undo:
            return CommandResult.no_change(
                ReplaceScenarioDocumentCommand(
                    state.document_or_raise(),
                    state.document_or_raise(),
                    "empty history",
                ),
                "undo",
                "Scenario Undo history is empty.",
            )
        command = self._undo[-1]
        result = command.undo(state)
        if result.status is not CommandStatus.APPLIED:
            return result
        self._undo.pop()
        self._redo.append(command)
        self._notify()
        return result

    def redo(self, state: "ScenarioAuthoringState") -> CommandResult:
        if not self._redo:
            return CommandResult.no_change(
                ReplaceScenarioDocumentCommand(
                    state.document_or_raise(),
                    state.document_or_raise(),
                    "empty history",
                ),
                "redo",
                "Scenario Redo history is empty.",
            )
        command = self._redo[-1]
        result = command.execute(state)
        if result.status is not CommandStatus.APPLIED:
            return result
        self._redo.pop()
        self._undo.append(command)
        self._notify()
        return result


class ScenarioAuthoringState:
    """Validated scenario document plus isolated Undo/Redo and file state."""

    def __init__(self, scene: Scene, *, max_history: int = 100) -> None:
        self.scene = scene
        self.document: ScenarioDocumentV1 | None = None
        self.project_path: Path | None = None
        self.scenario_path: Path | None = None
        self.saved_digest: str | None = None
        self.commands = ScenarioCommandManager(max_history=max_history)
        self._listeners: list[Callable[[], None]] = []

    def subscribe(self, callback: Callable[[], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback()

    def _set_document(self, document: ScenarioDocumentV1) -> None:
        self.document = ScenarioDocumentV1.model_validate(document, strict=True)
        self._notify()

    @property
    def is_available(self) -> bool:
        return self.document is not None and self.project_path is not None

    @property
    def is_dirty(self) -> bool:
        return (
            self.document is not None
            and scenario_sha256(self.document) != self.saved_digest
        )

    def bind_project(self, project_path: Path | None) -> None:
        if project_path is None:
            self.project_path = None
            self.scenario_path = None
            self.document = None
            self.saved_digest = None
            self.commands.clear()
            self._notify()
            return
        project = Path(project_path).resolve(strict=False)
        if self.project_path == project and self.document is not None:
            self._rebind_project_hash(project)
            return
        previous = (
            self.project_path,
            self.scenario_path,
            self.document,
            self.saved_digest,
        )
        self.project_path = project
        self.scenario_path = project.with_name(project.stem + SCENARIO_FILE_EXTENSION)
        try:
            if self.scenario_path.is_file():
                self.load(self.scenario_path)
            else:
                self._set_document(_default_document(project, self.scene))
                self.commands.clear()
                self.saved_digest = None
                self._notify()
        except Exception:
            (
                self.project_path,
                self.scenario_path,
                self.document,
                self.saved_digest,
            ) = previous
            raise

    def _rebind_project_hash(self, project: Path) -> None:
        if self.document is None:
            return
        reference = project_reference_for(project)
        if self.document.project == reference:
            return
        payload = _copy_payload(self.document)
        payload["project"] = reference.model_dump(mode="python")
        self._set_document(_validated(payload))
        self.commands.clear()
        self.saved_digest = None

    def reset(self) -> None:
        if self.project_path is None:
            raise ScenarioAuthoringError("a saved project is required")
        self._set_document(_default_document(self.project_path, self.scene))
        self.commands.clear()
        self.saved_digest = None

    def load(self, path: Path | None = None) -> None:
        if self.project_path is None:
            raise ScenarioAuthoringError("a saved project is required")
        destination = Path(path or self.scenario_path or "").resolve(strict=False)
        document = load_scenario(destination, project_path=self.project_path)
        self.scenario_path = destination
        self._set_document(document)
        self.commands.clear()
        self.saved_digest = scenario_sha256(document)

    def save(self, path: Path | None = None) -> Path:
        if self.project_path is None or self.document is None:
            raise ScenarioAuthoringError("a saved project is required")
        self._rebind_project_hash(self.project_path)
        destination = Path(path or self.scenario_path or "").resolve(strict=False)
        save_scenario(self.document, destination)
        self.scenario_path = destination
        self.saved_digest = scenario_sha256(self.document)
        self._notify()
        return destination

    def apply(self, after: ScenarioDocumentV1, description: str) -> CommandResult:
        before = self.document_or_raise()
        validated = ScenarioDocumentV1.model_validate(after, strict=True)
        if validated == before:
            return CommandResult.no_change(
                ReplaceScenarioDocumentCommand(before, validated, description),
                "execute",
                "The scenario operation made no change.",
            )
        return self.commands.execute(
            ReplaceScenarioDocumentCommand(before, validated, description),
            self,
        )

    def rename_layer(self, layer_id: str, name: str) -> CommandResult:
        clean = str(name).strip()
        if not clean:
            raise ScenarioAuthoringError("scenario layer name must not be empty")
        item = _layer(self.document_or_raise(), layer_id)
        return self.apply(
            _replace_layer(
                self.document_or_raise(),
                layer_id,
                item.model_copy(update={"name": clean}),
            ),
            "Rename scenario layer",
        )

    def set_layer_visible(self, layer_id: str, visible: bool) -> CommandResult:
        document = self.document_or_raise()
        item = _layer(document, layer_id)
        return self.apply(
            _replace_layer(
                document, layer_id, item.model_copy(update={"visible": bool(visible)})
            ),
            "Toggle scenario layer visibility",
        )

    def set_layer_parallax(self, layer_id: str, **values: float) -> CommandResult:
        document = self.document_or_raise()
        item = _layer(document, layer_id)
        parallax = item.parallax.model_copy(update=values)
        return self.apply(
            _replace_layer(
                document, layer_id, item.model_copy(update={"parallax": parallax})
            ),
            "Edit scenario layer parallax",
        )

    def move_layer(self, layer_id: str, new_index: int) -> CommandResult:
        document = self.document_or_raise()
        layers = list(document.layers)
        current = next(
            (index for index, item in enumerate(layers) if item.id == layer_id), None
        )
        if current is None:
            raise ScenarioAuthoringError(f"scenario layer not found: {layer_id}")
        target = max(0, min(int(new_index), len(layers) - 1))
        item = layers.pop(current)
        layers.insert(target, item)
        return self.apply(_with_layers(document, layers), "Reorder scenario layer")

    def add_layer(self, name: str = "Scenario Layer") -> str:
        document = self.document_or_raise()
        base = "scenario_layer"
        index = 1
        existing = {item.id for item in document.layers}
        while f"{base}_{index}" in existing:
            index += 1
        layer_id = f"{base}_{index}"
        new_layer = ScenarioLayerRecord(
            id=layer_id,
            name=str(name).strip() or "Scenario Layer",
            object_ids=[],
            parallax=ScenarioParallaxRecord(),
        )
        self.apply(
            _with_layers(document, [*document.layers, new_layer]), "Add scenario layer"
        )
        return layer_id

    def remove_layer(self, layer_id: str) -> CommandResult:
        document = self.document_or_raise()
        if len(document.layers) <= 1:
            raise ScenarioAuthoringError("the last scenario layer cannot be removed")
        removed = _layer(document, layer_id)
        remaining = [item for item in document.layers if item.id != layer_id]
        survivor = remaining[0]
        reassigned = survivor.model_copy(
            update={
                "object_ids": [
                    *survivor.object_ids,
                    *[
                        object_id
                        for object_id in removed.object_ids
                        if object_id not in survivor.object_ids
                    ],
                ]
            }
        )
        remaining[0] = reassigned
        return self.apply(
            _with_layers(document, remaining),
            "Remove scenario layer",
        )

    def assign_object(self, object_id: str, layer_id: str) -> CommandResult:
        document = self.document_or_raise()
        if object_id not in self.scene.objects:
            raise ScenarioAuthoringError(f"scene object not found: {object_id}")
        _layer(document, layer_id)
        layers = []
        for item in document.layers:
            ids = [value for value in item.object_ids if value != object_id]
            if item.id == layer_id:
                ids.append(object_id)
            layers.append(item.model_copy(update={"object_ids": ids}))
        return self.apply(
            _with_layers(document, layers), "Assign object to scenario layer"
        )

    def set_camera(self, *, x: float, y: float, zoom: float) -> CommandResult:
        document = self.document_or_raise()
        camera = document.camera.model_copy(
            update={
                "position": PointRecord(x=float(x), y=float(y)),
                "zoom": float(zoom),
            }
        )
        payload = _copy_payload(document)
        payload["camera"] = camera.model_dump(mode="python")
        return self.apply(_validated(payload), "Edit scenario camera")

    def undo(self) -> CommandResult:
        return self.commands.undo(self)

    def redo(self) -> CommandResult:
        return self.commands.redo(self)

    def document_or_raise(self) -> ScenarioDocumentV1:
        if self.document is None:
            raise ScenarioAuthoringError("no scenario is loaded")
        return self.document

    def preview_layers(self) -> tuple[ScenarioPreviewLayer, ...]:
        document = self.document_or_raise()
        return tuple(
            ScenarioPreviewLayer(
                item.id,
                tuple(item.object_ids),
                ParallaxLayer(
                    depth=float(item.parallax.depth),
                    translation_strength=float(item.parallax.translation_strength),
                    zoom_strength=float(item.parallax.zoom_strength),
                ),
                item.visible,
            )
            for item in document.layers
        )

    def preview_camera(self, viewport: tuple[float, float]) -> OrthographicCamera:
        camera = self.document_or_raise().camera
        return OrthographicCamera(
            viewport,
            position=(float(camera.position.x), float(camera.position.y)),
            zoom=float(camera.zoom),
        )
