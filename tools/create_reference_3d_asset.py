#!/usr/bin/env python3
"""Create a deterministic, original modular character asset for Unity validation.

The generator intentionally lives outside the canonical editor path.  It writes
only to a new output directory and refuses to overwrite an existing delivery.
The reference sheets guide the visual language; no reference pixels are used as
textures or geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import struct
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_RECORDS = [
    {
        "filename": "1-Foto-1.jpg",
        "sha256": "1EEE95F73802B6205B84097537E93B0434EE2EAEE1A52DAB17E24A618F11939E",
    },
    {
        "filename": "2-Foto-2.jpg",
        "sha256": "1EE40AD572538A177A6D31227C73343EB511C55DD0469B3E9597514FE941AB8D",
    },
    {
        "filename": "3-Foto-3.jpg",
        "sha256": "C8C2CC6C6FAFB45FA09AD1420D8F5F6D93B1946930FE36F39D59353E62F309C8",
    },
]

JOINT_SPECS = [
    ("root", None, (0.0, 0.0, 0.0)),
    ("pelvis", "root", (0.0, 2.05, 0.0)),
    ("spine", "pelvis", (0.0, 0.62, 0.0)),
    ("chest", "spine", (0.0, 0.64, 0.0)),
    ("neck", "chest", (0.0, 0.64, 0.0)),
    ("head", "neck", (0.0, 0.34, 0.0)),
    ("upper_arm_l", "chest", (-0.58, 0.29, 0.0)),
    ("lower_arm_l", "upper_arm_l", (-0.42, -0.56, 0.0)),
    ("hand_l", "lower_arm_l", (-0.10, -0.44, 0.0)),
    ("upper_arm_r", "chest", (0.58, 0.29, 0.0)),
    ("lower_arm_r", "upper_arm_r", (0.42, -0.56, 0.0)),
    ("hand_r", "lower_arm_r", (0.10, -0.44, 0.0)),
    ("upper_leg_l", "pelvis", (-0.29, -0.50, 0.0)),
    ("lower_leg_l", "upper_leg_l", (0.0, -0.91, 0.0)),
    ("foot_l", "lower_leg_l", (0.0, -0.55, 0.20)),
    ("upper_leg_r", "pelvis", (0.29, -0.50, 0.0)),
    ("lower_leg_r", "upper_leg_r", (0.0, -0.91, 0.0)),
    ("foot_r", "lower_leg_r", (0.0, -0.55, 0.20)),
]
JOINT_INDEX = {name: index for index, (name, _, _) in enumerate(JOINT_SPECS)}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _finite_tuple(values: Sequence[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _add(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Sequence[float], factor: float) -> tuple[float, float, float]:
    return (a[0] * factor, a[1] * factor, a[2] * factor)


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _normalize(value: Sequence[float]) -> tuple[float, float, float]:
    length = math.sqrt(_dot(value, value))
    if length <= 1e-8:
        return (0.0, 1.0, 0.0)
    return (value[0] / length, value[1] / length, value[2] / length)


def _normal(p0: Sequence[float], p1: Sequence[float], p2: Sequence[float]):
    return _normalize(_cross(_sub(p1, p0), _sub(p2, p0)))


Influence = Sequence[tuple[str, float]]


@dataclass
class MeshPart:
    name: str
    material: str
    positions: list[tuple[float, float, float]] = field(default_factory=list)
    normals: list[tuple[float, float, float]] = field(default_factory=list)
    uvs: list[tuple[float, float]] = field(default_factory=list)
    influences: list[Influence] = field(default_factory=list)
    indices: list[int] = field(default_factory=list)

    def add_vertex(
        self,
        position: Sequence[float],
        normal: Sequence[float],
        uv: Sequence[float],
        influence: Influence,
    ) -> int:
        index = len(self.positions)
        self.positions.append(_finite_tuple(position))
        self.normals.append(_normalize(normal))
        self.uvs.append(
            (
                min(1.0, max(0.0, float(uv[0]))),
                min(1.0, max(0.0, float(uv[1]))),
            )
        )
        self.influences.append(tuple(influence))
        return index

    def add_triangle(self, a: int, b: int, c: int) -> None:
        self.indices.extend((a, b, c))

    def add_face(
        self,
        corners: Sequence[Sequence[float]],
        normal: Sequence[float],
        uv_corners: Sequence[Sequence[float]],
        influence: Influence,
    ) -> None:
        start = len(self.positions)
        for position, uv in zip(corners, uv_corners):
            self.add_vertex(position, normal, uv, influence)
        self.indices.extend((start, start + 1, start + 2, start, start + 2, start + 3))

    def add_quad_auto_normal(
        self,
        corners: Sequence[Sequence[float]],
        uv_corners: Sequence[Sequence[float]],
        influence: Influence,
    ) -> None:
        self.add_face(
            corners,
            _normal(corners[0], corners[1], corners[2]),
            uv_corners,
            influence,
        )


def add_box(
    part: MeshPart,
    center: Sequence[float],
    size: Sequence[float],
    influence: Influence,
) -> None:
    cx, cy, cz = center
    sx, sy, sz = (float(value) / 2.0 for value in size)
    x0, x1 = cx - sx, cx + sx
    y0, y1 = cy - sy, cy + sy
    z0, z1 = cz - sz, cz + sz
    uv = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    faces = [
        (((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)), (1, 0, 0)),
        (((x0, y0, z1), (x0, y1, z1), (x0, y1, z0), (x0, y0, z0)), (-1, 0, 0)),
        (((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)), (0, 1, 0)),
        (((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)), (0, -1, 0)),
        (((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)), (0, 0, 1)),
        (((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)), (0, 0, -1)),
    ]
    for corners, normal in faces:
        part.add_face(corners, normal, uv, influence)


def add_cylinder(
    part: MeshPart,
    center: Sequence[float],
    radius: float,
    height: float,
    influence: Influence,
    segments: int = 16,
) -> None:
    cx, cy, cz = center
    half = height / 2.0
    for index in range(segments):
        a0 = 2.0 * math.pi * index / segments
        a1 = 2.0 * math.pi * (index + 1) / segments
        p0 = (cx + radius * math.cos(a0), cy - half, cz + radius * math.sin(a0))
        p1 = (cx + radius * math.cos(a1), cy - half, cz + radius * math.sin(a1))
        p2 = (cx + radius * math.cos(a1), cy + half, cz + radius * math.sin(a1))
        p3 = (cx + radius * math.cos(a0), cy + half, cz + radius * math.sin(a0))
        normal0 = (math.cos(a0), 0.0, math.sin(a0))
        normal1 = (math.cos(a1), 0.0, math.sin(a1))
        start = len(part.positions)
        for position, normal, uv in (
            (p0, normal0, (index / segments, 0.0)),
            (p1, normal1, ((index + 1) / segments, 0.0)),
            (p2, normal1, ((index + 1) / segments, 1.0)),
            (p3, normal0, (index / segments, 1.0)),
        ):
            part.add_vertex(position, normal, uv, influence)
        part.indices.extend((start, start + 1, start + 2, start, start + 2, start + 3))
    top_center = part.add_vertex((cx, cy + half, cz), (0, 1, 0), (0.5, 0.5), influence)
    bottom_center = part.add_vertex(
        (cx, cy - half, cz), (0, -1, 0), (0.5, 0.5), influence
    )
    for index in range(segments):
        a0 = 2.0 * math.pi * index / segments
        a1 = 2.0 * math.pi * (index + 1) / segments
        top0 = part.add_vertex(
            (cx + radius * math.cos(a0), cy + half, cz + radius * math.sin(a0)),
            (0, 1, 0),
            (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
            influence,
        )
        top1 = part.add_vertex(
            (cx + radius * math.cos(a1), cy + half, cz + radius * math.sin(a1)),
            (0, 1, 0),
            (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1)),
            influence,
        )
        bottom0 = part.add_vertex(
            (cx + radius * math.cos(a0), cy - half, cz + radius * math.sin(a0)),
            (0, -1, 0),
            (0.5 + 0.5 * math.cos(a0), 0.5 + 0.5 * math.sin(a0)),
            influence,
        )
        bottom1 = part.add_vertex(
            (cx + radius * math.cos(a1), cy - half, cz + radius * math.sin(a1)),
            (0, -1, 0),
            (0.5 + 0.5 * math.cos(a1), 0.5 + 0.5 * math.sin(a1)),
            influence,
        )
        part.indices.extend((top_center, top0, top1))
        part.indices.extend((bottom_center, bottom1, bottom0))


def add_uv_sphere(
    part: MeshPart,
    center: Sequence[float],
    scale: Sequence[float],
    influence: Influence,
    rings: int = 12,
    segments: int = 20,
) -> None:
    cx, cy, cz = center
    sx, sy, sz = scale
    grid: list[list[int]] = []
    for ring in range(rings + 1):
        theta = math.pi * ring / rings
        y = math.cos(theta)
        radial = math.sin(theta)
        row: list[int] = []
        for segment in range(segments):
            phi = 2.0 * math.pi * segment / segments
            unit = (radial * math.cos(phi), y, radial * math.sin(phi))
            position = (cx + sx * unit[0], cy + sy * unit[1], cz + sz * unit[2])
            row.append(
                part.add_vertex(
                    position,
                    unit,
                    (segment / segments, ring / rings),
                    influence,
                )
            )
        grid.append(row)
    for ring in range(rings):
        for segment in range(segments):
            next_segment = (segment + 1) % segments
            a = grid[ring][segment]
            b = grid[ring][next_segment]
            c = grid[ring + 1][next_segment]
            d = grid[ring + 1][segment]
            part.indices.extend((a, b, c, a, c, d))


def add_panel(
    part: MeshPart,
    center_x: float,
    top_y: float,
    bottom_y: float,
    width: float,
    base_z: float,
    top_influence: Influence,
    bottom_influence: Influence,
    rows: int = 5,
    columns: int = 5,
    wave: float = 0.10,
) -> None:
    grid: list[list[int]] = []
    for row in range(rows + 1):
        t = row / rows
        y = top_y + (bottom_y - top_y) * t
        row_indices: list[int] = []
        influence = top_influence if t < 0.38 else bottom_influence
        for column in range(columns + 1):
            u = column / columns
            x = center_x + (u - 0.5) * width
            z = base_z - wave * math.sin(math.pi * u) * (0.35 + 0.65 * t)
            row_indices.append(
                part.add_vertex((x, y, z), (0.0, 0.0, 1.0), (u, 1.0 - t), influence)
            )
        grid.append(row_indices)
    for row in range(rows):
        for column in range(columns):
            a = grid[row][column]
            b = grid[row][column + 1]
            c = grid[row + 1][column + 1]
            d = grid[row + 1][column]
            part.indices.extend((a, b, c, a, c, d))


def _basis_for_direction(direction: Sequence[float]) -> tuple[tuple[float, ...], ...]:
    y_axis = _normalize(direction)
    reference = (0.0, 0.0, 1.0)
    x_axis = _normalize(_cross(reference, y_axis))
    if abs(_dot(x_axis, x_axis)) < 1e-6:
        x_axis = (1.0, 0.0, 0.0)
    z_axis = _normalize(_cross(x_axis, y_axis))
    return x_axis, y_axis, z_axis


def _basis_point(
    origin: Sequence[float],
    basis: Sequence[Sequence[float]],
    x: float,
    y: float,
    z: float,
) -> tuple[float, float, float]:
    return _add(
        origin,
        _add(_mul(basis[0], x), _add(_mul(basis[1], y), _mul(basis[2], z))),
    )


def add_cylinder_between(
    part: MeshPart,
    start: Sequence[float],
    end: Sequence[float],
    radius: float,
    influence: Influence,
    segments: int = 12,
) -> None:
    direction = _sub(end, start)
    length = math.sqrt(_dot(direction, direction))
    basis = _basis_for_direction(direction)
    for index in range(segments):
        a0 = 2.0 * math.pi * index / segments
        a1 = 2.0 * math.pi * (index + 1) / segments
        points = [
            _basis_point(
                start, basis, radius * math.cos(a0), 0.0, radius * math.sin(a0)
            ),
            _basis_point(
                start, basis, radius * math.cos(a1), 0.0, radius * math.sin(a1)
            ),
            _basis_point(
                end, basis, radius * math.cos(a1), length, radius * math.sin(a1)
            ),
            _basis_point(
                end, basis, radius * math.cos(a0), length, radius * math.sin(a0)
            ),
        ]
        n0 = _normalize(
            _add(_mul(basis[0], math.cos(a0)), _mul(basis[2], math.sin(a0)))
        )
        n1 = _normalize(
            _add(_mul(basis[0], math.cos(a1)), _mul(basis[2], math.sin(a1)))
        )
        start_index = len(part.positions)
        for position, normal, uv in (
            (points[0], n0, (index / segments, 0.0)),
            (points[1], n1, ((index + 1) / segments, 0.0)),
            (points[2], n1, ((index + 1) / segments, 1.0)),
            (points[3], n0, (index / segments, 1.0)),
        ):
            part.add_vertex(position, normal, uv, influence)
        part.indices.extend(
            (
                start_index,
                start_index + 1,
                start_index + 2,
                start_index,
                start_index + 2,
                start_index + 3,
            )
        )


def add_blade(
    part: MeshPart,
    base: Sequence[float],
    tip: Sequence[float],
    influence: Influence,
) -> None:
    direction = _sub(tip, base)
    length = math.sqrt(_dot(direction, direction))
    basis = _basis_for_direction(direction)
    rings = ((0.0, 0.16, 0.055), (0.72, 0.11, 0.040), (1.0, 0.018, 0.008))
    ring_points: list[list[tuple[float, float, float]]] = []
    for t, width, thickness in rings:
        center = _add(base, _mul(direction, t))
        ring_points.append(
            [
                _basis_point(center, basis, -width, 0.0, -thickness),
                _basis_point(center, basis, width, 0.0, -thickness),
                _basis_point(center, basis, width, 0.0, thickness),
                _basis_point(center, basis, -width, 0.0, thickness),
            ]
        )
    uv = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for ring_index in range(len(ring_points) - 1):
        first = ring_points[ring_index]
        second = ring_points[ring_index + 1]
        for side in range(4):
            next_side = (side + 1) % 4
            corners = (first[side], first[next_side], second[next_side], second[side])
            part.add_quad_auto_normal(corners, uv, influence)
    part.add_face(ring_points[0][::-1], (0.0, -1.0, 0.0), uv, influence)
    part.add_face(ring_points[-1], basis[1], uv, influence)
    _ = length


def _make_part(name: str, material: str) -> MeshPart:
    return MeshPart(name=name, material=material)


def build_parts() -> list[MeshPart]:
    armor = "Armor_Metal"
    cloth = "Cloth_Cape"
    leather = "Leather_Belts"
    boots = "Leather_Boots"
    energy = "Energy_Rune"
    parts: list[MeshPart] = []

    torso = _make_part("Torso_Armor", armor)
    add_box(torso, (0.0, 3.12, 0.0), (1.18, 1.48, 0.74), (("chest", 1.0),))
    add_box(torso, (0.0, 3.62, 0.06), (0.95, 0.22, 0.82), (("chest", 1.0),))
    parts.append(torso)

    hood = _make_part("Hood", cloth)
    add_uv_sphere(hood, (0.0, 4.30, -0.01), (0.52, 0.62, 0.48), (("head", 1.0),))
    add_box(hood, (0.0, 3.93, -0.06), (0.78, 0.22, 0.60), (("neck", 1.0),))
    parts.append(hood)

    face = _make_part("Face_Plate", armor)
    add_box(face, (0.0, 4.26, 0.43), (0.50, 0.52, 0.13), (("head", 1.0),))
    add_box(face, (0.0, 4.20, 0.51), (0.24, 0.10, 0.04), (("head", 1.0),))
    parts.append(face)

    for side, label in ((-1, "L"), (1, "R")):
        shoulder = _make_part(f"Shoulder_{label}", armor)
        add_uv_sphere(
            shoulder,
            (side * 0.72, 3.68, 0.0),
            (0.42, 0.28, 0.48),
            ((f"upper_arm_{'l' if side < 0 else 'r'}", 1.0),),
        )
        parts.append(shoulder)
        upper = _make_part(f"UpperArm_Armor_{label}", armor)
        add_box(
            upper,
            (side * 0.94, 3.30, 0.0),
            (0.38, 0.78, 0.46),
            ((f"upper_arm_{'l' if side < 0 else 'r'}", 1.0),),
        )
        parts.append(upper)
        gauntlet = _make_part(f"Gauntlet_{label}", armor)
        add_box(
            gauntlet,
            (side * 1.10, 2.63, 0.08),
            (0.36, 0.50, 0.44),
            ((f"hand_{'l' if side < 0 else 'r'}", 1.0),),
        )
        add_cylinder(
            gauntlet,
            (side * 1.10, 2.38, 0.08),
            0.14,
            0.16,
            ((f"hand_{'l' if side < 0 else 'r'}", 1.0),),
        )
        parts.append(gauntlet)

    belt = _make_part("Belt", leather)
    add_box(belt, (0.0, 2.36, 0.0), (1.34, 0.24, 0.82), (("pelvis", 1.0),))
    add_box(belt, (0.0, 2.36, 0.44), (0.26, 0.28, 0.08), (("pelvis", 1.0),))
    parts.append(belt)

    skirt = _make_part("Cloth_Skirt_Front", cloth)
    add_panel(
        skirt,
        0.0,
        2.30,
        1.08,
        1.15,
        0.44,
        (("pelvis", 1.0),),
        (("pelvis", 1.0),),
        wave=0.04,
    )
    parts.append(skirt)

    for side, label in ((-1, "L"), (1, "R")):
        side_skirt = _make_part(f"Cloth_Skirt_{label}", cloth)
        add_panel(
            side_skirt,
            side * 0.42,
            2.29,
            1.15,
            0.60,
            0.02,
            (("pelvis", 1.0),),
            (("pelvis", 1.0),),
            wave=0.08,
        )
        parts.append(side_skirt)

        thigh = _make_part(f"Thigh_Armor_{label}", armor)
        add_box(
            thigh,
            (side * 0.29, 1.49, 0.0),
            (0.44, 0.76, 0.56),
            ((f"upper_leg_{'l' if side < 0 else 'r'}", 1.0),),
        )
        parts.append(thigh)
        boot = _make_part(f"Boot_{label}", boots)
        add_box(
            boot,
            (side * 0.29, 0.57, 0.03),
            (0.49, 0.80, 0.66),
            ((f"lower_leg_{'l' if side < 0 else 'r'}", 1.0),),
        )
        add_box(
            boot,
            (side * 0.29, 0.14, 0.32),
            (0.54, 0.24, 0.88),
            ((f"foot_{'l' if side < 0 else 'r'}", 1.0),),
        )
        parts.append(boot)

    cape = _make_part("Cape_Center", cloth)
    add_panel(
        cape,
        0.0,
        3.90,
        1.04,
        0.92,
        -0.46,
        (("chest", 1.0),),
        (("pelvis", 1.0),),
        wave=0.12,
    )
    for vertex_index, influence in enumerate(cape.influences):
        row = vertex_index // 6
        if row <= 1:
            cape.influences[vertex_index] = (("chest", 0.75), ("spine", 0.25))
        elif row <= 3:
            cape.influences[vertex_index] = (("spine", 0.65), ("pelvis", 0.35))
        else:
            cape.influences[vertex_index] = (("pelvis", 1.0),)
    parts.append(cape)
    for side, label in ((-1, "L"), (1, "R")):
        cape_side = _make_part(f"Cape_{label}", cloth)
        add_panel(
            cape_side,
            side * 0.60,
            3.70,
            1.36,
            0.70,
            -0.40,
            (("chest", 0.75), ("spine", 0.25)),
            (("spine", 0.65), ("pelvis", 0.35)),
            wave=0.16,
        )
        parts.append(cape_side)

    blade = _make_part("Sword_Blade", armor)
    blade_base = (1.22, 2.52, 0.18)
    blade_tip = (1.82, 0.48, 0.20)
    add_blade(blade, blade_base, blade_tip, (("hand_r", 1.0),))
    parts.append(blade)

    hilt = _make_part("Sword_Hilt", leather)
    direction = _normalize(_sub(blade_tip, blade_base))
    guard_start = _add(blade_base, _mul(direction, -0.09))
    guard_end = _add(guard_start, (0.0, 0.0, 0.48))
    add_cylinder_between(
        hilt,
        _add(blade_base, _mul(direction, 0.16)),
        _add(blade_base, _mul(direction, -0.30)),
        0.075,
        (("hand_r", 1.0),),
    )
    add_cylinder_between(
        hilt, guard_start, guard_end, 0.045, (("hand_r", 1.0),), segments=8
    )
    parts.append(hilt)

    rune = _make_part("Energy_Rune", energy)
    add_box(rune, (1.52, 1.52, 0.245), (0.045, 1.16, 0.025), (("hand_r", 1.0),))
    parts.append(rune)

    return parts


def _world_joint_transforms() -> list[tuple[float, float, float]]:
    result: list[tuple[float, float, float] | None] = [None] * len(JOINT_SPECS)
    for index, (_, parent, local) in enumerate(JOINT_SPECS):
        if parent is None:
            result[index] = local
        else:
            result[index] = _add(result[JOINT_INDEX[parent]] or (0.0, 0.0, 0.0), local)
    return [value or (0.0, 0.0, 0.0) for value in result]


def _influence_arrays(
    influence: Influence,
) -> tuple[tuple[int, int, int, int], tuple[float, float, float, float]]:
    ordered = [
        (JOINT_INDEX[name], float(weight))
        for name, weight in influence
        if name in JOINT_INDEX and weight > 0
    ]
    if not ordered:
        ordered = [(0, 1.0)]
    total = sum(weight for _, weight in ordered)
    ordered = [(index, weight / total) for index, weight in ordered[:4]]
    while len(ordered) < 4:
        ordered.append((0, 0.0))
    return (
        tuple(index for index, _ in ordered),
        tuple(weight for _, weight in ordered),
    )


def _pack_floats(values: Iterable[float]) -> bytes:
    values_list = list(values)
    return struct.pack("<" + "f" * len(values_list), *values_list)


def _pack_u8(values: Iterable[int]) -> bytes:
    values_list = list(values)
    return struct.pack("<" + "B" * len(values_list), *values_list)


def _pack_u16(values: Iterable[int]) -> bytes:
    values_list = list(values)
    return struct.pack("<" + "H" * len(values_list), *values_list)


class BinaryBuilder:
    def __init__(self) -> None:
        self.data = bytearray()
        self.views: list[dict] = []
        self.accessors: list[dict] = []

    def append(self, payload: bytes, *, target: int | None = None) -> int:
        while len(self.data) % 4:
            self.data.append(0)
        offset = len(self.data)
        self.data.extend(payload)
        view = {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        if target is not None:
            view["target"] = target
        self.views.append(view)
        return len(self.views) - 1

    def accessor(
        self,
        view_index: int,
        component_type: int,
        value_type: str,
        count: int,
        minimum: Sequence[float] | None = None,
        maximum: Sequence[float] | None = None,
    ) -> int:
        value = {
            "bufferView": view_index,
            "componentType": component_type,
            "count": count,
            "type": value_type,
        }
        if minimum is not None:
            value["min"] = list(minimum)
        if maximum is not None:
            value["max"] = list(maximum)
        self.accessors.append(value)
        return len(self.accessors) - 1


def _minmax(
    values: Sequence[Sequence[float]],
) -> tuple[list[float], list[float]]:
    dimensions = len(values[0])
    minimum = [
        min(float(value[dimension]) for value in values)
        for dimension in range(dimensions)
    ]
    maximum = [
        max(float(value[dimension]) for value in values)
        for dimension in range(dimensions)
    ]
    return minimum, maximum


def _encode_geometry(parts: Sequence[MeshPart]) -> tuple[bytes, list[dict], list[dict]]:
    builder = BinaryBuilder()
    mesh_records: list[dict] = []
    part_records: list[dict] = []
    for part in parts:
        positions = [value for vertex in part.positions for value in vertex]
        normals = [value for vertex in part.normals for value in vertex]
        uvs = [value for vertex in part.uvs for value in vertex]
        joints = [
            value
            for influence in part.influences
            for value in _influence_arrays(influence)[0]
        ]
        weights = [
            value
            for influence in part.influences
            for value in _influence_arrays(influence)[1]
        ]
        position_view = builder.append(_pack_floats(positions), target=34962)
        normal_view = builder.append(_pack_floats(normals), target=34962)
        uv_view = builder.append(_pack_floats(uvs), target=34962)
        joint_view = builder.append(_pack_u8(joints), target=34962)
        weight_view = builder.append(_pack_floats(weights), target=34962)
        index_view = builder.append(_pack_u16(part.indices), target=34963)
        position_min, position_max = _minmax(part.positions)
        uv_min, uv_max = _minmax(part.uvs)
        position_accessor = builder.accessor(
            position_view,
            5126,
            "VEC3",
            len(part.positions),
            position_min,
            position_max,
        )
        normal_accessor = builder.accessor(normal_view, 5126, "VEC3", len(part.normals))
        uv_accessor = builder.accessor(
            uv_view, 5126, "VEC2", len(part.uvs), uv_min, uv_max
        )
        joint_accessor = builder.accessor(joint_view, 5121, "VEC4", len(part.positions))
        weight_accessor = builder.accessor(
            weight_view, 5126, "VEC4", len(part.positions)
        )
        index_accessor = builder.accessor(
            index_view,
            5123,
            "SCALAR",
            len(part.indices),
            [0],
            [max(part.indices)],
        )
        primitive = {
            "attributes": {
                "POSITION": position_accessor,
                "NORMAL": normal_accessor,
                "TEXCOORD_0": uv_accessor,
                "JOINTS_0": joint_accessor,
                "WEIGHTS_0": weight_accessor,
            },
            "indices": index_accessor,
            "material": 0,
            "mode": 4,
        }
        mesh_records.append({"name": part.name, "primitives": [primitive]})
        part_records.append(
            {
                "name": part.name,
                "material": part.material,
                "vertex_count": len(part.positions),
                "triangle_count": len(part.indices) // 3,
                "uv0_range": {"min": uv_min, "max": uv_max},
            }
        )
    return bytes(builder.data), mesh_records, part_records, builder


def _procedural_texture(kind: str, size: int = 256) -> bytes:
    image = Image.new("RGB", (size, size))
    pixels = image.load()
    seed = {"armor": 11, "cloth": 23, "leather": 37, "energy": 53}[kind]
    for y in range(size):
        for x in range(size):
            wave = math.sin((x + seed) * 0.13) + math.sin((y + seed) * 0.19)
            noise = ((x * 17 + y * 31 + seed * 13) % 29) - 14
            if kind == "armor":
                value = max(0, min(255, int(53 + wave * 11 + noise)))
                pixels[x, y] = (value, max(0, value - 8), max(0, value + 16))
            elif kind == "cloth":
                value = max(0, min(255, int(31 + wave * 8 + noise // 2)))
                stripe = 10 if (x // 9 + y // 13) % 2 == 0 else 0
                pixels[x, y] = (value + stripe // 3, value, min(255, value + stripe))
            elif kind == "leather":
                value = max(0, min(255, int(46 + wave * 7 + noise // 2)))
                pixels[x, y] = (value + 18, max(0, value - 7), max(0, value - 20))
            else:
                glow = max(0, int(120 + 100 * math.sin((x + y) * 0.05)))
                pixels[x, y] = (5, min(255, glow // 2), glow)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _orm_texture(kind: str, size: int = 256) -> bytes:
    metallic = 220 if kind == "armor" else 0
    roughness = {"armor": 92, "cloth": 192, "leather": 148, "energy": 72}[kind]
    image = Image.new("RGB", (size, size), (255, roughness, metallic))
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _normal_texture(kind: str, size: int = 256) -> bytes:
    image = Image.new("RGB", (size, size), (128, 128, 255))
    pixels = image.load()
    for y in range(size):
        for x in range(size):
            detail = ((x * 7 + y * 11 + len(kind) * 19) % 9) - 4
            pixels[x, y] = (128 + detail, 128 - detail, 255)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=False, compress_level=9)
    return output.getvalue()


def _write_texture_set(output: Path) -> tuple[list[dict], dict[str, dict[str, str]]]:
    texture_dir = output / "textures"
    texture_dir.mkdir(parents=True, exist_ok=False)
    images: list[dict] = []
    texture_files: dict[str, dict[str, str]] = {}
    for kind in ("armor", "cloth", "leather", "energy"):
        files: dict[str, str] = {}
        for role, data in (
            ("basecolor", _procedural_texture(kind)),
            ("orm", _orm_texture(kind)),
            ("normal", _normal_texture(kind)),
        ):
            filename = f"{kind}_{role}.png"
            path = texture_dir / filename
            path.write_bytes(data)
            files[role] = f"textures/{filename}"
            images.append(
                {
                    "name": filename,
                    "uri": f"textures/{filename}",
                    "mimeType": "image/png",
                    "sha256": _sha256_bytes(data),
                }
            )
        texture_files[kind] = files
    return images, texture_files


def _translation_matrix_inverse(position: Sequence[float]) -> list[float]:
    return [
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        -position[0],
        -position[1],
        -position[2],
        1.0,
    ]


def _quaternion(axis: Sequence[float], angle: float) -> list[float]:
    normalized = _normalize(axis)
    half = angle / 2.0
    sine = math.sin(half)
    return [
        normalized[0] * sine,
        normalized[1] * sine,
        normalized[2] * sine,
        math.cos(half),
    ]


def _build_gltf(
    parts: Sequence[MeshPart],
    geometry: bytes,
    mesh_records: list[dict],
    builder: BinaryBuilder,
    images: list[dict],
    texture_files: dict[str, dict[str, str]],
) -> tuple[dict, bytes]:
    material_order = [
        "Armor_Metal",
        "Cloth_Cape",
        "Leather_Belts",
        "Leather_Boots",
        "Energy_Rune",
    ]
    material_kind = {
        "Armor_Metal": "armor",
        "Cloth_Cape": "cloth",
        "Leather_Belts": "leather",
        "Leather_Boots": "leather",
        "Energy_Rune": "energy",
    }
    image_index = {record["uri"]: index for index, record in enumerate(images)}
    textures: list[dict] = []
    texture_index: dict[str, int] = {}
    for material_name in material_order:
        kind = material_kind[material_name]
        for role in ("basecolor", "orm", "normal"):
            uri = texture_files[kind][role]
            texture_index[f"{kind}:{role}"] = len(textures)
            textures.append(
                {"sampler": 0, "source": image_index[uri], "name": f"{kind}_{role}"}
            )
    materials = []
    for material_name in material_order:
        kind = material_kind[material_name]
        material = {
            "name": material_name,
            "doubleSided": True,
            "pbrMetallicRoughness": {
                "baseColorTexture": {"index": texture_index[f"{kind}:basecolor"]},
                "metallicRoughnessTexture": {"index": texture_index[f"{kind}:orm"]},
                "metallicFactor": 0.86 if kind == "armor" else 0.05,
                "roughnessFactor": 0.42 if kind == "armor" else 0.72,
            },
            "normalTexture": {"index": texture_index[f"{kind}:normal"], "scale": 0.72},
            "extras": {"neoeng_role": kind, "source": "procedural_original"},
        }
        if material_name == "Energy_Rune":
            material["emissiveTexture"] = {"index": texture_index[f"{kind}:basecolor"]}
            material["emissiveFactor"] = [0.08, 0.42, 1.0]
            material["alphaMode"] = "BLEND"
        materials.append(material)
    material_indices = {name: index for index, name in enumerate(material_order)}
    for record, part in zip(mesh_records, parts):
        record["primitives"][0]["material"] = material_indices[part.material]

    nodes: list[dict] = [{"name": "EclipseWarden_Asset", "children": []}]
    joint_nodes: list[int] = []
    for name, parent, local in JOINT_SPECS:
        index = len(nodes)
        node = {"name": name, "translation": list(local), "children": []}
        nodes.append(node)
        joint_nodes.append(index)
    for index, (_, parent, _) in enumerate(JOINT_SPECS):
        if parent is None:
            nodes[0]["children"].append(joint_nodes[index])
        else:
            nodes[joint_nodes[JOINT_INDEX[parent]]]["children"].append(
                joint_nodes[index]
            )
    mesh_node_indices: list[int] = []
    for mesh_index, part in enumerate(parts):
        index = len(nodes)
        mesh_node_indices.append(index)
        nodes.append(
            {
                "name": part.name,
                "mesh": mesh_index,
                "skin": 0,
                "extras": {"neoeng_component": True, "neoeng_material": part.material},
            }
        )
        nodes[0]["children"].append(index)

    world_transforms = _world_joint_transforms()
    inverse_bind_payload = b"".join(
        _pack_floats(_translation_matrix_inverse(position))
        for position in world_transforms
    )
    inverse_bind_view = builder.append(inverse_bind_payload)
    inverse_bind_accessor = builder.accessor(
        inverse_bind_view, 5126, "MAT4", len(JOINT_SPECS)
    )

    gltf = {
        "asset": {
            "version": "2.0",
            "generator": "NeoEng-D-Trace reference asset generator 0.1.0",
            "extras": {
                "neoeng_asset_name": "Eclipse Warden",
                "neoeng_original_procedural_geometry": True,
                "neoeng_target_engine": "Unity",
            },
        },
        "scene": 0,
        "scenes": [{"name": "EclipseWarden_Scene", "nodes": [0]}],
        "nodes": nodes,
        "meshes": mesh_records,
        "materials": materials,
        "textures": textures,
        "images": images,
        "samplers": [
            {"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}
        ],
        "skins": [
            {
                "name": "EclipseWarden_Skeleton",
                "joints": joint_nodes,
                "skeleton": joint_nodes[0],
                "inverseBindMatrices": inverse_bind_accessor,
            }
        ],
        "animations": [
            {
                "name": "Idle",
                "samplers": [],
                "channels": [],
                "extras": {"loop": True, "intended_use": "Unity Animator idle state"},
            }
        ],
        "buffers": [{"byteLength": len(builder.data), "uri": "eclipse_warden.bin"}],
        "bufferViews": builder.views,
        "accessors": builder.accessors,
    }
    animation = gltf["animations"][0]
    times_view = builder.append(_pack_floats((0.0, 1.0, 2.0)))
    times_accessor = builder.accessor(times_view, 5126, "SCALAR", 3, [0.0], [2.0])
    animation_nodes = [
        (JOINT_INDEX["chest"], (0.0, 0.025, 0.0)),
        (JOINT_INDEX["upper_arm_l"], (0.0, 0.0, 0.08)),
        (JOINT_INDEX["upper_arm_r"], (0.0, 0.0, -0.08)),
    ]
    for joint_index, axis in animation_nodes:
        node_index = joint_nodes[joint_index]
        values = (
            _quaternion(axis, -0.025),
            _quaternion(axis, 0.025),
            _quaternion(axis, -0.025),
        )
        value_view = builder.append(
            _pack_floats(value for value in values for value in value)
        )
        value_accessor = builder.accessor(value_view, 5126, "VEC4", 3)
        sampler_index = len(animation["samplers"])
        animation["samplers"].append(
            {
                "input": times_accessor,
                "interpolation": "LINEAR",
                "output": value_accessor,
            }
        )
        animation["channels"].append(
            {
                "sampler": sampler_index,
                "target": {"node": node_index, "path": "rotation"},
            }
        )
    gltf["buffers"][0]["byteLength"] = len(builder.data)
    gltf["bufferViews"] = builder.views
    gltf["accessors"] = builder.accessors
    return gltf, bytes(builder.data)


def _make_glb(gltf: dict, geometry: bytes, texture_payloads: Sequence[bytes]) -> bytes:
    glb_gltf = json.loads(json.dumps(gltf))
    binary = bytearray(geometry)
    while len(binary) % 4:
        binary.append(0)
    for image, payload in zip(glb_gltf["images"], texture_payloads):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(payload)
        image["bufferView"] = len(glb_gltf["bufferViews"])
        image.pop("uri", None)
        glb_gltf["bufferViews"].append(
            {"buffer": 0, "byteOffset": offset, "byteLength": len(payload)}
        )
    glb_gltf["buffers"][0].pop("uri", None)
    glb_gltf["buffers"][0]["byteLength"] = len(binary)
    json_payload = json.dumps(
        glb_gltf, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    while len(json_payload) % 4:
        json_payload += b" "
    while len(binary) % 4:
        binary.append(0)
    total_length = 12 + 8 + len(json_payload) + 8 + len(binary)
    return (
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<I4s", len(json_payload), b"JSON")
        + json_payload
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + bytes(binary)
    )


def _write_obj(output: Path, parts: Sequence[MeshPart]) -> None:
    obj_lines = [
        "# Eclipse Warden static diagnostic export",
        "mtllib eclipse_warden.mtl",
    ]
    vertex_offset = 1
    uv_offset = 1
    normal_offset = 1
    for part in parts:
        obj_lines.append(f"o {part.name}")
        obj_lines.append(f"usemtl {part.material}")
        for position in part.positions:
            obj_lines.append("v " + " ".join(f"{value:.6f}" for value in position))
        for uv in part.uvs:
            obj_lines.append("vt " + " ".join(f"{value:.6f}" for value in uv))
        for normal in part.normals:
            obj_lines.append("vn " + " ".join(f"{value:.6f}" for value in normal))
        for index in range(0, len(part.indices), 3):
            face = []
            for local_index in part.indices[index : index + 3]:
                face.append(
                    f"{vertex_offset + local_index}/"
                    f"{uv_offset + local_index}/"
                    f"{normal_offset + local_index}"
                )
            obj_lines.append("f " + " ".join(face))
        vertex_offset += len(part.positions)
        uv_offset += len(part.uvs)
        normal_offset += len(part.normals)
    (output / "eclipse_warden.obj").write_text(
        "\n".join(obj_lines) + "\n", encoding="utf-8"
    )
    mtl_lines = ["# PBR texture references for the OBJ diagnostic export"]
    for material, kind in (
        ("Armor_Metal", "armor"),
        ("Cloth_Cape", "cloth"),
        ("Leather_Belts", "leather"),
        ("Leather_Boots", "leather"),
        ("Energy_Rune", "energy"),
    ):
        mtl_lines.extend(
            [
                f"newmtl {material}",
                "Kd 1.0 1.0 1.0",
                f"map_Kd textures/{kind}_basecolor.png",
                "",
            ]
        )
    (output / "eclipse_warden.mtl").write_text("\n".join(mtl_lines), encoding="utf-8")


def _write_readme(output: Path, manifest: dict) -> None:
    (output / "README.md").write_text(
        """# Eclipse Warden — Unity delivery

Este pacote é um asset original procedural criado para validar o fluxo de
autoria e exportação do NeoEng-D-Trace. As imagens do usuário orientaram a
linguagem visual; nenhum pixel foi usado como textura.

## Arquivos

- eclipse_warden.glb: entrega principal, glTF 2.0 com texturas embarcadas,
  materiais PBR, skin, esqueleto e animação Idle.
- eclipse_warden.gltf + eclipse_warden.bin + textures/: entrega aberta para
  inspeção e pipelines que preferem recursos separados.
- eclipse_warden.obj + eclipse_warden.mtl: diagnóstico estático sem rig.
- manifest.json e SHA256SUMS.txt: contrato, proveniência e integridade.
- UNITY_IMPORT_GUIDE.md: orientação de importação no Unity.
- godot_preview/: preview executável de importação/renderização real.

## Critério de uso no Unity

Use um importador glTF 2.0 compatível com a versão do projeto. O GLB é a
opção recomendada para primeira importação. O rig está no contrato glTF como
Generic; o mapeamento Humanoid deve ser conferido no Unity e não é declarado
como validado neste pacote.

O manifesto registra explicitamente o que foi verificado neste ambiente e o
que ainda requer um ciclo Unity real autorizado.
""",
        encoding="utf-8",
    )
    (output / "UNITY_IMPORT_GUIDE.md").write_text(
        """# Guia de importação Unity — Eclipse Warden

1. Instale ou habilite um importador glTF 2.0 compatível com a versão Unity
   usada pelo projeto.
2. Importe eclipse_warden.glb como primeira opção; use o par
   eclipse_warden.gltf/eclipe_warden.bin somente para diagnóstico aberto.
3. Confirme escala em metros, orientação Y-up e que os objetos aparecem
   separadamente no hierarchy/outliner.
4. No import de rig, comece com Animation Type Generic. Só altere para
   Humanoid depois de verificar manualmente quadril, coluna, cabeça, braços,
   mãos, pernas e pés.
5. Verifique os mapas Base Color, Metallic/Roughness e Normal nos materiais.
   O material Energy_Rune também usa o mapa emissivo.
6. Reproduza Idle e verifique deformação de capa, ombreiras e espada.
7. Para URP/HDRP, remapeie os mapas para o shader lit do pipeline e preserve
   emissão da Energy_Rune.

Este guia é um contrato operacional, não uma prova de importação Unity.
O campo compatibility.unity.status do manifesto permanece PENDING_EVIDENCE
até a execução real no Unity.
""",
        encoding="utf-8",
    )


def _git_context() -> dict[str, str]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ).stdout.strip()
    except OSError:
        commit = ""
    return {"commit": commit or "unavailable"}


def generate(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    parts = build_parts()
    images, texture_files = _write_texture_set(output)
    texture_payloads = [(output / record["uri"]).read_bytes() for record in images]
    geometry, mesh_records, part_records, builder = _encode_geometry(parts)
    gltf, binary = _build_gltf(
        parts, geometry, mesh_records, builder, images, texture_files
    )
    (output / "eclipse_warden.bin").write_bytes(binary)
    (output / "eclipse_warden.gltf").write_text(
        json.dumps(gltf, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "eclipse_warden.glb").write_bytes(
        _make_glb(gltf, binary, texture_payloads)
    )
    _write_obj(output, parts)
    manifest = {
        "schema": "neoeng-d-trace-reference-3d-asset",
        "schema_version": 1,
        "lifecycle_status": "IN_PROGRESS",
        "asset": {
            "name": "Eclipse Warden",
            "version": "0.1.0",
            "units": "meters",
            "coordinate_system": "glTF 2.0 Y-up right-handed",
            "source_method": "procedural_original",
        },
        "source": {
            "references": REFERENCE_RECORDS,
            "reference_license_status": "USER_SUPPLIED_UNVERIFIED",
            "geometry_and_textures_use_reference_pixels": False,
        },
        "files": {
            "glb": "eclipse_warden.glb",
            "gltf": "eclipse_warden.gltf",
            "bin": "eclipse_warden.bin",
            "obj": "eclipse_warden.obj",
            "mtl": "eclipse_warden.mtl",
            "unity_guide": "UNITY_IMPORT_GUIDE.md",
            "godot_preview": "godot_preview",
        },
        "components": part_records,
        "materials": [
            {
                "name": name,
                "base_color": texture_files[kind]["basecolor"],
                "metallic_roughness": texture_files[kind]["orm"],
                "normal": texture_files[kind]["normal"],
                "emissive": (
                    texture_files[kind]["basecolor"] if name == "Energy_Rune" else None
                ),
            }
            for name, kind in (
                ("Armor_Metal", "armor"),
                ("Cloth_Cape", "cloth"),
                ("Leather_Belts", "leather"),
                ("Leather_Boots", "leather"),
                ("Energy_Rune", "energy"),
            )
        ],
        "textures": images,
        "rig": {
            "type": "skinned_generic",
            "joint_count": len(JOINT_SPECS),
            "joints": [name for name, _, _ in JOINT_SPECS],
            "inverse_bind_matrices": True,
        },
        "animations": [
            {
                "name": "Idle",
                "duration_seconds": 2.0,
                "loop": True,
                "channels": 3,
            }
        ],
        "compatibility": {
            "unity": {
                "status": "PENDING_EVIDENCE",
                "format": "glTF 2.0 / GLB",
                "rig_import_hint": (
                    "Generic first; Humanoid requires manual mapping validation"
                ),
                "urp_hdrp_material_remap": "required per project pipeline",
            },
            "godot": {"status": "PLANNED", "version_tested": "4.7"},
        },
        "validation": {"status": "PLANNED", "report": "structural-validation.json"},
        "provenance": _git_context(),
    }
    _write_readme(output, manifest)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    checksums = []
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        if path.name == "SHA256SUMS.txt":
            continue
        checksums.append(f"{_sha256_file(path)}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS.txt").write_text(
        "\n".join(checksums) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    output = arguments.output.resolve()
    try:
        manifest = generate(output)
    except Exception as exc:
        print(f"asset generation failed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "status": "IN_PROGRESS",
                "output": str(output),
                "components": len(manifest["components"]),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
