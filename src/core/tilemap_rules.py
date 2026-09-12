"""Deterministic, destination-neutral terrain/Rule Tile resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from src.core.tilemap_grids import GridSpec
from src.core.tilemap_model import (
    TileCell,
    TileCellDelta,
    TileMapDocument,
    TileMapError,
)
from src.core.tilemap_tools import TileEditTransaction

EMPTY = "<empty>"


@dataclass(frozen=True)
class NeighborCondition:
    offset: tuple[int, int]
    allowed_tile_ids: tuple[str, ...] = ()
    allow_empty: bool = False

    def __post_init__(self) -> None:
        if self.offset == (0, 0):
            raise TileMapError("neighbor condition cannot target its own cell")
        if len(self.offset) != 2 or any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in self.offset
        ):
            raise TileMapError("neighbor condition offsets must be integer pairs")
        if not self.allowed_tile_ids and not self.allow_empty:
            raise TileMapError("neighbor condition must allow a tile or empty cell")
        if any(not value for value in self.allowed_tile_ids):
            raise TileMapError("neighbor condition tile IDs must be non-empty")

    def matches(self, cell: TileCell | None) -> bool:
        if cell is None:
            return self.allow_empty
        return cell.tile_id in self.allowed_tile_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "offset": {"x": self.offset[0], "y": self.offset[1]},
            "allowed_tile_ids": list(self.allowed_tile_ids),
            "allow_empty": self.allow_empty,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NeighborCondition":
        if not isinstance(payload, Mapping):
            raise TileMapError("neighbor condition must be an object")
        offset = payload.get("offset")
        if not isinstance(offset, Mapping):
            raise TileMapError("neighbor condition offset must be an object")
        offset_x = offset.get("x")
        offset_y = offset.get("y")
        if (
            isinstance(offset_x, bool)
            or not isinstance(offset_x, int)
            or isinstance(offset_y, bool)
            or not isinstance(offset_y, int)
        ):
            raise TileMapError("neighbor condition offsets must be integers")
        allowed = payload.get("allowed_tile_ids", [])
        if not isinstance(allowed, list) or any(
            not isinstance(value, str) for value in allowed
        ):
            raise TileMapError("neighbor condition tile IDs must be a list")
        allow_empty = payload.get("allow_empty", False)
        if not isinstance(allow_empty, bool):
            raise TileMapError("neighbor condition allow_empty must be boolean")
        return cls(
            (offset_x, offset_y),
            tuple(allowed),
            allow_empty,
        )


@dataclass(frozen=True)
class TerrainRule:
    id: str
    target_tile_id: str
    conditions: tuple[NeighborCondition, ...] = ()
    priority: int = 0
    weight: int = 1
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.target_tile_id:
            raise TileMapError("terrain rule ID and target tile ID are required")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise TileMapError("terrain rule priority must be an integer")
        if (
            isinstance(self.weight, bool)
            or not isinstance(self.weight, int)
            or self.weight <= 0
        ):
            raise TileMapError("terrain rule weight must be positive")
        offsets = [condition.offset for condition in self.conditions]
        if len(offsets) != len(set(offsets)):
            raise TileMapError("terrain rule conditions must use unique offsets")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target_tile_id": self.target_tile_id,
            "conditions": [condition.to_dict() for condition in self.conditions],
            "priority": self.priority,
            "weight": self.weight,
            "depends_on": list(self.depends_on),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TerrainRule":
        if not isinstance(payload, Mapping):
            raise TileMapError("terrain rule must be an object")
        conditions = payload.get("conditions", [])
        depends_on = payload.get("depends_on", [])
        if not isinstance(conditions, list) or not isinstance(depends_on, list):
            raise TileMapError("terrain rule conditions and dependencies must be lists")
        if any(not isinstance(value, str) for value in depends_on):
            raise TileMapError("terrain rule dependencies must be strings")
        identifier = payload.get("id", "")
        target_tile_id = payload.get("target_tile_id", "")
        priority = payload.get("priority", 0)
        weight = payload.get("weight", 1)
        if not isinstance(identifier, str) or not isinstance(target_tile_id, str):
            raise TileMapError("terrain rule IDs must be strings")
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise TileMapError("terrain rule priority must be an integer")
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise TileMapError("terrain rule weight must be an integer")
        return cls(
            id=identifier,
            target_tile_id=target_tile_id,
            conditions=tuple(
                NeighborCondition.from_dict(condition) for condition in conditions
            ),
            priority=priority,
            weight=weight,
            depends_on=tuple(depends_on),
        )


@dataclass(frozen=True)
class RuleResolution:
    coordinate: tuple[int, int]
    tile_id: str
    rule_id: str | None
    invalidated: tuple[tuple[int, int], ...]


class TileRuleSet:
    """Validated rule graph with deterministic resolution and invalidation."""

    def __init__(
        self,
        rules: Iterable[TerrainRule],
        *,
        fallback_tile_id: str,
    ) -> None:
        self.rules = tuple(rules)
        if not isinstance(fallback_tile_id, str) or not fallback_tile_id:
            raise TileMapError("rule fallback tile ID is required")
        ids = [rule.id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise TileMapError("terrain rule IDs must be unique")
        self.fallback_tile_id = fallback_tile_id
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        known = {rule.id for rule in self.rules}
        graph = {rule.id: rule.depends_on for rule in self.rules}
        if any(
            dependency not in known
            for values in graph.values()
            for dependency in values
        ):
            raise TileMapError("terrain rule depends on an unknown rule")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(rule_id: str) -> None:
            if rule_id in visiting:
                raise TileMapError("terrain rule dependency cycle")
            if rule_id in visited:
                return
            visiting.add(rule_id)
            for dependency in graph[rule_id]:
                visit(dependency)
            visiting.remove(rule_id)
            visited.add(rule_id)

        for rule_id in graph:
            visit(rule_id)

    def _matches(
        self,
        document: TileMapDocument,
        layer_id: str,
        coordinate: tuple[int, int],
        rule: TerrainRule,
    ) -> bool:
        if not document.tileset.has_tile(rule.target_tile_id):
            raise TileMapError(f"unknown target tile ID in rule: {rule.target_tile_id}")

        def neighbor_cell(condition: NeighborCondition) -> TileCell | None:
            neighbor = (
                coordinate[0] + condition.offset[0],
                coordinate[1] + condition.offset[1],
            )
            if document.bounds is not None and not document.bounds.contains(neighbor):
                return None
            return document.get_cell(layer_id, neighbor)

        return all(
            condition.matches(neighbor_cell(condition)) for condition in rule.conditions
        )

    def resolve(
        self,
        document: TileMapDocument,
        layer_id: str,
        coordinate: tuple[int, int],
        *,
        grid: GridSpec,
        seed: int = 0,
    ) -> RuleResolution:
        if not document.tileset.has_tile(self.fallback_tile_id):
            raise TileMapError(f"unknown fallback tile ID: {self.fallback_tile_id}")
        matches = [
            rule
            for rule in self.rules
            if self._matches(document, layer_id, coordinate, rule)
        ]
        if matches:
            highest = max(rule.priority for rule in matches)
            ranked = [rule for rule in matches if rule.priority == highest]
            targets = {rule.target_tile_id for rule in ranked}
            if len(targets) > 1:
                raise TileMapError(
                    f"ambiguous terrain rules at {coordinate}: "
                    + ", ".join(sorted(rule.id for rule in ranked))
                )
            generator = random.Random(
                (seed * 1_000_003) ^ coordinate[0] ^ coordinate[1] * 9176
            )
            chosen = generator.choices(
                ranked, weights=[rule.weight for rule in ranked], k=1
            )[0]
            rule_id = chosen.id
            tile_id = chosen.target_tile_id
        else:
            rule_id = None
            tile_id = self.fallback_tile_id
        invalidated = tuple(dict.fromkeys((coordinate, *grid.neighbors(coordinate))))
        return RuleResolution(coordinate, tile_id, rule_id, invalidated)

    def apply(
        self,
        document: TileMapDocument,
        layer_id: str,
        coordinates: Iterable[tuple[int, int]],
        *,
        grid: GridSpec,
        seed: int = 0,
    ) -> tuple[tuple[RuleResolution, ...], TileEditTransaction]:
        resolutions = tuple(
            self.resolve(document, layer_id, coordinate, grid=grid, seed=seed)
            for coordinate in dict.fromkeys(coordinates)
        )
        deltas = tuple(
            TileCellDelta(
                layer_id,
                result.coordinate,
                document.get_cell(layer_id, result.coordinate),
                TileCell(result.tile_id),
            )
            for result in resolutions
            if document.get_cell(layer_id, result.coordinate)
            != TileCell(result.tile_id)
        )
        transaction = TileEditTransaction(document, deltas)
        transaction.apply()
        return resolutions, transaction

    def to_dict(self) -> dict[str, Any]:
        return {
            "fallback_tile_id": self.fallback_tile_id,
            "rules": [rule.to_dict() for rule in self.rules],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TileRuleSet":
        if not isinstance(payload, Mapping):
            raise TileMapError("terrain rule set must be an object")
        rules = payload.get("rules", [])
        if not isinstance(rules, list):
            raise TileMapError("terrain rule set rules must be a list")
        fallback = payload.get("fallback_tile_id")
        if not isinstance(fallback, str):
            raise TileMapError("terrain rule fallback tile ID must be a string")
        return cls(
            tuple(TerrainRule.from_dict(rule) for rule in rules),
            fallback_tile_id=fallback,
        )


__all__ = [
    "EMPTY",
    "NeighborCondition",
    "RuleResolution",
    "TerrainRule",
    "TileRuleSet",
]
