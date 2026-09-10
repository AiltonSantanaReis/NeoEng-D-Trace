"""Deterministic sequence evaluation, independent of wall clock and UI."""

from dataclasses import dataclass
import math
import random

from src.persistence.project_schema import Point3Record, PointRecord
from src.persistence.scene_authoring_schema import (
    SceneAuthoringDocumentV2, SceneCameraAuthoringRecord, SceneLightSocketRecord, SceneMaterialAuthoringRecord,
)
from src.persistence.scene_sequence_schema import SceneClip, SceneSequence


def set_sequence(session, sequence: SceneSequence) -> bool:
    """Validate first and record exactly one undoable authoring transaction."""
    document = session.document
    if not isinstance(document, SceneAuthoringDocumentV2):
        raise ValueError("sequence requires a V2 scene")
    candidate = SceneAuthoringDocumentV2.model_validate(
        {**document.model_dump(), "sequence": sequence.model_dump()}, strict=True
    )
    return session.apply(lambda: setattr(session.model, "document", candidate), "Edit sequence")


def sequence_time(elapsed: float, sequence: SceneSequence) -> float:
    if not math.isfinite(elapsed) or elapsed < 0:
        raise ValueError("time must be finite and non-negative")
    return elapsed % sequence.duration if sequence.loop else min(elapsed, sequence.duration)


def active_clips(sequence: SceneSequence, time: float) -> tuple[SceneClip, ...]:
    return tuple(c for c in sequence.clips if c.enabled and c.start <= time < c.start + c.duration)


def evaluate_sequence(document: SceneAuthoringDocumentV2, time: float) -> SceneAuthoringDocumentV2:
    """Evaluate absolute time; authoring objects, camera and history stay intact.

    Transform endpoints hold after the clip ends. Text, audio, light and particles
    exist only inside their intervals. Rewinding always evaluates from authoring.
    """
    if not math.isfinite(time) or time < 0:
        raise ValueError("time must be finite and non-negative")
    result = document.model_copy(deep=True)
    if document.sequence is None:
        return result
    camera = result.camera
    objects = list(result.objects)
    sockets = list(result.sockets)
    for clip in sorted(document.sequence.clips, key=lambda c: (c.start, c.id)):
        if not clip.enabled or time < clip.start:
            continue
        phase = min(1.0, (time - clip.start) / clip.duration)
        # Smoothstep avoids velocity jumps at camera/cutscene boundaries.
        phase = phase * phase * (3 - 2 * phase)
        lerp = lambda a, b: a + (b - a) * phase
        if clip.kind == "camera":
            camera = SceneCameraAuthoringRecord(
                position=PointRecord(x=lerp(clip.x, clip.end_x), y=lerp(clip.y, clip.end_y)),
                zoom=lerp(clip.zoom, clip.end_zoom),
            )
        elif clip.kind == "motion":
            for index, obj in enumerate(objects):
                if obj.id != clip.target_id:
                    continue
                transform = obj.transform.model_copy(update={
                    "position": Point3Record(x=lerp(clip.x, clip.end_x), y=lerp(clip.y, clip.end_y), z=obj.transform.position.z),
                    "rotation": Point3Record(x=obj.transform.rotation.x, y=obj.transform.rotation.y, z=lerp(clip.rotation, clip.end_rotation)),
                    "scale": Point3Record(x=lerp(clip.zoom, clip.end_zoom), y=lerp(clip.zoom, clip.end_zoom), z=obj.transform.scale.z),
                })
                material = (obj.material or SceneMaterialAuthoringRecord()).model_copy(update={"opacity": lerp(clip.opacity, clip.end_opacity)})
                objects[index] = obj.model_copy(update={"transform": transform, "material": material})
        elif clip.kind == "light" and time < clip.start + clip.duration and clip.intensity > 0:
            intensity = clip.intensity
            if clip.loop:
                intensity *= 0.65 + 0.35 * math.cos((time - clip.start) * math.tau / 2)
            sockets.append(SceneLightSocketRecord(
                id=f"sequence_{clip.id}", layer_id=clip.layer_id or document.layers[0].id,
                position=Point3Record(x=clip.x, y=clip.y, z=0),
                color=clip.color, intensity=intensity, radius=128 * clip.zoom,
            ))
    return result.model_copy(update={"camera": camera, "objects": objects, "sockets": sockets})


@dataclass(frozen=True)
class SequenceParticle:
    x: float
    y: float
    size: float
    opacity: float


def particles_at(clip: SceneClip, time: float) -> tuple[SequenceParticle, ...]:
    """Bounded CPU emitter v1. Seeded, absolute-time, quantized to 60 Hz.

    The analytic trajectories allow backwards scrubbing without replaying hours
    of simulation; output is identical regardless of timer jitter or seek order.
    """
    if clip.kind not in {"rain", "snow", "dust", "fire"} or not clip.enabled:
        return ()
    elapsed = math.floor((time - clip.start) * 60) / 60
    if elapsed < 0 or elapsed >= clip.duration:
        return ()
    rng = random.Random(clip.seed)
    states = []
    for _ in range(min(1000, int(100 * clip.intensity))):
        initial_x, initial_y = rng.uniform(-400, 400), rng.uniform(-240, 240)
        lifetime = rng.uniform(1.5, 4)
        offset = rng.uniform(0, lifetime)
        age = elapsed + offset
        if not clip.loop and age > lifetime:
            continue
        age %= lifetime
        if clip.kind == "rain":
            x, y, size = initial_x + age * 18, -240 + age / lifetime * 480, 7
        elif clip.kind == "snow":
            x, y, size = initial_x + math.sin(age * 2 + offset) * 15, -240 + age / lifetime * 480, 3
        elif clip.kind == "fire":
            x, y, size = initial_x * 0.12 * (1 - age / lifetime), -age * 65, 5
        else:
            x, y, size = initial_x + age * 12, initial_y + math.sin(age + offset) * 15, 2
        states.append(SequenceParticle(clip.x + x * clip.zoom, clip.y + y * clip.zoom, size * clip.zoom, 1 - age / lifetime))
    return tuple(states)
