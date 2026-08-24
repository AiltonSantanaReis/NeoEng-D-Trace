"""Create a deterministic portable archive and verifiable file manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import zipfile
from pathlib import Path

from PyInstaller import __version__ as PYINSTALLER_VERSION

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(REPOSITORY_ROOT))

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION

MANIFEST_NAME = "release-manifest.json"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(bundle: Path) -> list[dict[str, object]]:
    records = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_NAME:
            continue
        if path.is_symlink():
            raise ValueError(f"release bundle cannot contain symlinks: {path}")
        records.append(
            {
                "path": path.relative_to(bundle).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def canonical_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def write_manifest(bundle: Path, source_commit: str) -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    manifest = {
        "schema_version": 1,
        "product": APP_DISPLAY_NAME,
        "version": APP_VERSION,
        "platform": "windows-x86_64",
        "package_type": "portable-onedir",
        "source_commit": source_commit,
        "build_environment": {
            "python": platform.python_version(),
            "pyinstaller": PYINSTALLER_VERSION,
        },
        "build_inputs": {
            "poetry_lock_canonical_sha256": canonical_text_sha256(
                repository_root / "poetry.lock"
            ),
            "spec_canonical_sha256": canonical_text_sha256(
                repository_root / "packaging" / "NeoEng-D-Trace.spec"
            ),
        },
        "files": collect_files(bundle),
    }
    path = bundle / MANIFEST_NAME
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path


def write_deterministic_zip(bundle: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in sorted(bundle.rglob("*")):
                if not path.is_file():
                    continue
                relative = (Path(bundle.name) / path.relative_to(bundle)).as_posix()
                info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


def package_portable(
    bundle: Path, output: Path, source_commit: str
) -> dict[str, object]:
    if not bundle.is_dir():
        raise FileNotFoundError(f"portable bundle does not exist: {bundle}")
    write_manifest(bundle, source_commit)
    write_deterministic_zip(bundle, output)
    digest = sha256_file(output)
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(
        f"{digest}  {output.name}\n",
        encoding="ascii",
        newline="\n",
    )
    return {
        "archive": output.name,
        "sha256": digest,
        "size": output.stat().st_size,
        "manifest": MANIFEST_NAME,
        "files": len(collect_files(bundle)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    result = package_portable(
        args.bundle.resolve(),
        args.output.resolve(),
        args.source_commit,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
