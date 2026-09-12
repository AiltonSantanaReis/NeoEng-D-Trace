"""Deterministic render planning for the professional scenario preview.

The plan is deliberately independent from Qt painting.  It gives the raster
viewport and a future accelerated backend the same explicit ordering, layer
bindings and invalidation semantics without making the authoring document
depend on a widget or a graphics API.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from typing import Literal

from src.persistence.scene_authoring_schema import SceneAuthoringDocumentV2

RenderBackend = Literal["raster", "opengl"]
RenderPass = Literal[
    "background",
    "layer_content",
    "entities",
    "shadows",
    "lighting",
    "particles",
    "postprocess",
    "overlays",
]

RENDER_PASSES: tuple[RenderPass, ...] = (
    "background",
    "layer_content",
    "entities",
    "shadows",
    "lighting",
    "particles",
    "postprocess",
    "overlays",
)


@dataclass(frozen=True)
class RenderBackendState:
    """Backend selection with a visible fallback reason."""

    requested: RenderBackend
    selected: RenderBackend
    status: Literal["native", "fallback"]
    reason: str


def select_render_backend(
    requested: RenderBackend = "raster", *, opengl_available: bool = False
) -> RenderBackendState:
    """Select a backend without hiding an unavailable accelerated path."""

    if requested == "opengl" and opengl_available:
        return RenderBackendState("opengl", "opengl", "native", "context available")
    if requested == "opengl":
        return RenderBackendState(
            "opengl",
            "raster",
            "fallback",
            "OpenGL context unavailable; raster reference active",
        )
    return RenderBackendState("raster", "raster", "native", "portable raster reference")


@dataclass(frozen=True)
class RenderLayerPlan:
    """Stable ordering and bindings for one authored layer."""

    layer_id: str
    order: int
    depth: float
    visible: bool
    object_ids: tuple[str, ...]
    entity_ids: tuple[str, ...]


@dataclass(frozen=True)
class SceneRenderPlan:
    """Immutable frame-independent plan consumed by a viewport backend."""

    backend: RenderBackendState
    passes: tuple[RenderPass, ...]
    layers: tuple[RenderLayerPlan, ...]
    viewport_size: tuple[int, int]
    document_fingerprint: str
    revision: int

    def layer_order(self) -> dict[str, int]:
        return {layer.layer_id: layer.order for layer in self.layers}

    def object_order(self) -> dict[str, tuple[int, int, float]]:
        order: dict[str, tuple[int, int, float]] = {}
        for layer in self.layers:
            for local_index, object_id in enumerate(layer.object_ids):
                order[object_id] = (layer.order, local_index, layer.depth)
        return order


def _fingerprint(document: SceneAuthoringDocumentV2) -> str:
    payload = document.model_dump_json(exclude_none=False, by_alias=True).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def build_scene_render_plan(
    document: SceneAuthoringDocumentV2,
    viewport_size: tuple[int, int],
    *,
    requested_backend: RenderBackend = "raster",
    opengl_available: bool = False,
    revision: int = 1,
) -> SceneRenderPlan:
    """Build a deterministic plan from the canonical V2 document."""

    width, height = viewport_size
    if isinstance(width, bool) or isinstance(height, bool) or width <= 0 or height <= 0:
        raise ValueError("render viewport dimensions must be positive integers")
    layer_depth = {
        item.layer_id: float(item.depth) for item in document.parallax_layers
    }
    layers: list[RenderLayerPlan] = []
    for order, layer in enumerate(document.layers):
        layers.append(
            RenderLayerPlan(
                layer_id=layer.id,
                order=order,
                depth=layer_depth.get(layer.id, 0.0),
                visible=layer.visible,
                object_ids=tuple(
                    item.id for item in document.objects if item.layer_id == layer.id
                ),
                entity_ids=tuple(
                    item.id for item in document.entities if item.layer_id == layer.id
                ),
            )
        )
    return SceneRenderPlan(
        backend=select_render_backend(
            requested_backend, opengl_available=opengl_available
        ),
        passes=RENDER_PASSES,
        layers=tuple(layers),
        viewport_size=(int(width), int(height)),
        document_fingerprint=_fingerprint(document),
        revision=int(revision),
    )


class RenderPlanCache:
    """Small explicit cache with deterministic invalidation and resize rules."""

    def __init__(self) -> None:
        self._plan: SceneRenderPlan | None = None
        self._revision = 0

    @property
    def plan(self) -> SceneRenderPlan | None:
        return self._plan

    def build(
        self,
        document: SceneAuthoringDocumentV2,
        viewport_size: tuple[int, int],
        *,
        requested_backend: RenderBackend = "raster",
        opengl_available: bool = False,
    ) -> SceneRenderPlan:
        candidate = build_scene_render_plan(
            document,
            viewport_size,
            requested_backend=requested_backend,
            opengl_available=opengl_available,
            revision=0,
        )
        if (
            self._plan is not None
            and candidate.document_fingerprint == self._plan.document_fingerprint
            and candidate.viewport_size == self._plan.viewport_size
            and candidate.backend == self._plan.backend
        ):
            return self._plan
        self._revision += 1
        self._plan = replace(candidate, revision=self._revision)
        return self._plan

    def invalidate(self) -> None:
        self._plan = None

    def cleanup(self) -> None:
        self.invalidate()


__all__ = [
    "RENDER_PASSES",
    "RenderBackendState",
    "RenderLayerPlan",
    "RenderPlanCache",
    "SceneRenderPlan",
    "build_scene_render_plan",
    "select_render_backend",
]
