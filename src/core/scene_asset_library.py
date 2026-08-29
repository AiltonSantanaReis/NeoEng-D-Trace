"""Controlled asset lifecycle for professional 2D scene authoring.

The scene document stores only project-relative paths.  Files dragged from
outside the project are copied into ``assets/scene`` before a document record
is created, while the original local path is retained as non-resolving
provenance.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from src.persistence.scene_authoring_schema import AssetReferenceRecord

SCENE_ASSET_DIRECTORY = PurePosixPath("assets/scene")
SUPPORTED_SCENE_ASSET_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".svg"}
)


class SceneAssetError(ValueError):
    """Raised when an authored scene asset cannot be imported or resolved."""


@dataclass(frozen=True)
class PreparedSceneAsset:
    """Validated project-relative asset ready to be added to a scene."""

    path: str
    sha256: str
    source_path: str | None
    resolved_path: Path


def sha256_file(path: Path) -> str:
    """Hash a regular file without loading it wholly into memory."""

    if not path.is_file():
        raise SceneAssetError(f"asset file does not exist: {path}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise SceneAssetError(f"cannot read asset {path}: {exc}") from exc
    return digest.hexdigest()


def validate_scene_asset_source(path: Path) -> Path:
    """Return a resolved supported source path or raise an actionable error."""

    candidate = path.resolve(strict=False)
    if candidate.suffix.lower() not in SUPPORTED_SCENE_ASSET_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SCENE_ASSET_SUFFIXES))
        raise SceneAssetError(
            f"unsupported scene asset format '{candidate.suffix or '<none>'}'; "
            f"supported formats: {supported}"
        )
    if not candidate.is_file():
        raise SceneAssetError(f"asset file does not exist: {candidate}")
    return candidate


def _relative_to_project(project_root: Path, candidate: Path) -> str | None:
    try:
        relative = candidate.relative_to(project_root)
    except ValueError:
        return None
    portable = PurePosixPath(relative.as_posix())
    if portable.is_absolute() or ".." in portable.parts or not portable.parts:
        return None
    return portable.as_posix()


def _safe_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return (stem or "asset")[:48]


def _copy_content_addressed(source: Path, project_root: Path, digest: str) -> Path:
    destination_dir = project_root / Path(*SCENE_ASSET_DIRECTORY.parts)
    try:
        destination_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SceneAssetError(
            f"cannot create controlled asset directory {destination_dir}: {exc}"
        ) from exc

    suffix = source.suffix.lower()
    base_name = f"{_safe_stem(source.stem)}-{digest[:16]}{suffix}"
    destination = destination_dir / base_name
    if destination.exists():
        if sha256_file(destination) == digest:
            return destination
        # A 64-character fallback makes a truncated-hash collision explicit
        # without overwriting an unrelated file.
        destination = destination_dir / f"{_safe_stem(source.stem)}-{digest}{suffix}"
        if destination.exists() and sha256_file(destination) == digest:
            return destination
        if destination.exists():
            raise SceneAssetError(
                f"controlled asset destination collision: {destination.name}"
            )

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination_dir,
            prefix=".neoeng-asset-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            with source.open("rb") as source_handle:
                shutil.copyfileobj(source_handle, handle, length=1024 * 1024)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
    except OSError as exc:
        raise SceneAssetError(f"cannot copy asset into project: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    if sha256_file(destination) != digest:
        raise SceneAssetError(
            f"copied asset failed integrity verification: {destination}"
        )
    return destination


def prepare_scene_asset(
    source_path: str | os.PathLike[str], project_root: Path
) -> PreparedSceneAsset:
    """Validate and make a source asset project-controlled.

    Assets already inside ``project_root`` keep their existing relative path.
    External assets are copied atomically into ``assets/scene`` and retain the
    original absolute path only as provenance metadata.
    """

    root = project_root.resolve(strict=False)
    source = validate_scene_asset_source(Path(source_path))
    relative = _relative_to_project(root, source)
    digest = sha256_file(source)
    if relative is not None:
        return PreparedSceneAsset(relative, digest, None, source)

    destination = _copy_content_addressed(source, root, digest)
    managed_relative = _relative_to_project(root, destination)
    if managed_relative is None:
        raise SceneAssetError("controlled asset path is outside project root")
    return PreparedSceneAsset(managed_relative, digest, str(source), destination)


def resolve_scene_asset(
    asset: AssetReferenceRecord,
    project_root: Path | None,
) -> tuple[Path | None, str | None]:
    """Resolve and hash-check one asset for rendering.

    The returned message is suitable for a user-facing diagnostic.  Provenance
    is deliberately ignored: loading never depends on the original source.
    """

    if project_root is None:
        return None, "project root is unavailable"
    root = project_root.resolve(strict=False)
    candidate = (root / Path(asset.path)).resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"asset path escapes project: {asset.path}"
    if not candidate.is_file():
        return None, f"asset file is missing: {asset.path}"
    try:
        actual = sha256_file(candidate)
    except SceneAssetError as exc:
        return None, str(exc)
    if actual != asset.sha256:
        return None, (
            f"asset hash mismatch for {asset.path}: "
            f"expected {asset.sha256[:16]}…, got {actual[:16]}…"
        )
    return candidate, None


__all__ = [
    "PreparedSceneAsset",
    "SCENE_ASSET_DIRECTORY",
    "SUPPORTED_SCENE_ASSET_SUFFIXES",
    "SceneAssetError",
    "prepare_scene_asset",
    "resolve_scene_asset",
    "sha256_file",
    "validate_scene_asset_source",
]
