"""Read-only, versioned bundled art catalogs; assets become project-owned on import."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from src.core.scene_asset_library import SceneAssetError, sha256_file


def bundled_pack_root() -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return root / "assets" / "scene" / "packs"


def search_key(value: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(c)
    )


def contained_file(root: Path, relative: str) -> Path:
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or ":" in relative
    ):
        raise SceneAssetError("Caminho de pacote inválido")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        raise SceneAssetError("Caminho fora do pacote")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise SceneAssetError(f"Arquivo ausente ou fora do pacote: {relative}")
    return resolved


@dataclass(frozen=True)
class PackAsset:
    id: str
    name: str
    category: str
    path: str
    sha256: str
    width: int
    height: int
    tags: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class AssetPack:
    id: str
    name: str
    version: str
    root: Path
    description: str
    provenance: str
    assets: tuple[PackAsset, ...]

    def resolve_asset(self, asset: PackAsset) -> Path:
        if asset not in self.assets:
            raise SceneAssetError("Asset não pertence ao pacote")
        path = contained_file(self.root, asset.path)
        if sha256_file(path) != asset.sha256:
            raise SceneAssetError(f"Integridade inválida: {asset.name}")
        return path


def read_pack(manifest: Path) -> AssetPack:
    if manifest.stat().st_size > 2 * 1024 * 1024:
        raise SceneAssetError("Manifesto de pacote excede 2 MiB")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise SceneAssetError("Versão de pacote incompatível")
    for field in ("id", "name", "version", "description", "provenance"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise SceneAssetError(f"Campo de pacote inválido: {field}")
    entries = data.get("assets")
    if not isinstance(entries, list) or not 1 <= len(entries) <= 10000:
        raise SceneAssetError("Lista de assets inválida")
    assets = []
    ids = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise SceneAssetError("Entrada de asset inválida")
        for field in ("id", "name", "category", "path", "sha256", "description"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise SceneAssetError(f"Campo de asset inválido: {field}")
        if entry["id"] in ids or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise SceneAssetError("ID duplicado ou hash inválido")
        ids.add(entry["id"])
        for dimension in ("width", "height"):
            if (
                type(entry.get(dimension)) is not int
                or not 1 <= entry[dimension] <= 16384
            ):
                raise SceneAssetError("Dimensão de asset inválida")
        tags = entry.get("tags", [])
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            raise SceneAssetError("Tags inválidas")
        contained_file(manifest.parent, entry["path"])
        assets.append(
            PackAsset(
                **{
                    k: entry[k]
                    for k in (
                        "id",
                        "name",
                        "category",
                        "path",
                        "sha256",
                        "width",
                        "height",
                        "description",
                    )
                },
                tags=tuple(tags),
            )
        )
    return AssetPack(
        data["id"],
        data["name"],
        data["version"],
        manifest.parent,
        data["description"],
        data["provenance"],
        tuple(assets),
    )


def discover_packs(root: Path | None = None) -> tuple[list[AssetPack], list[str]]:
    packs: list[AssetPack] = []
    errors: list[str] = []
    for manifest in sorted((root or bundled_pack_root()).glob("*/manifest.json")):
        try:
            pack = read_pack(manifest)
            if any(p.id == pack.id and p.version == pack.version for p in packs):
                raise SceneAssetError("Pacote e versão duplicados")
            packs.append(pack)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"{manifest.parent.name}: {exc}")
    return packs, errors
