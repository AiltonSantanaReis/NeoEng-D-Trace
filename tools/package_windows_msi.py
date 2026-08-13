"""Build a deterministic per-user Windows MSI from the portable bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION

PRODUCT_NAMESPACE = uuid.UUID("6e69818d-93a3-5a86-953c-2326c536d06f")
UPGRADE_CODE = "{F13BFDC4-1445-56D9-A72E-8812CA7F9E87}"
MANUFACTURER = "NeoEng-D-Trace"


def stable_guid(name: str) -> str:
    return "{" + str(uuid.uuid5(PRODUCT_NAMESPACE, name)).upper() + "}"


def stable_identifier(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def short_directory_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", name).upper() or "DIR"
    if len(normalized) <= 8 and normalized == name.upper():
        return name
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:2].upper()
    return f"{normalized[:4]}{digest}~1|{name}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_portable_manifest(bundle: Path, manifest: dict[str, object]) -> None:
    records = manifest.get("files")
    if not isinstance(records, list):
        raise ValueError("portable manifest files must be a list")
    expected: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("portable manifest contains an invalid file record")
        relative = record["path"]
        if relative in expected:
            raise ValueError(f"portable manifest repeats file: {relative}")
        expected[relative] = record
    actual = {
        path.relative_to(bundle).as_posix()
        for path in bundle.rglob("*")
        if path.is_file() and path.name != "release-manifest.json"
    }
    if set(expected) != actual:
        raise ValueError("portable bundle file set does not match its manifest")
    for relative, record in expected.items():
        path = bundle / Path(relative)
        if path.stat().st_size != record.get("size"):
            raise ValueError(f"portable file size mismatch: {relative}")
        if sha256_file(path) != record.get("sha256"):
            raise ValueError(f"portable file hash mismatch: {relative}")


def _set_summary_package_code(database, package_code: str) -> None:
    from msilib import PID_APPNAME, PID_REVNUMBER

    summary = database.GetSummaryInformation(20)
    summary.SetProperty(PID_REVNUMBER, package_code)
    summary.SetProperty(PID_APPNAME, "NeoEng-D-Trace MSI Builder")
    summary.Persist()


def _add_bundle_tree(database, cabinet, bundle: Path, feature) -> tuple[str, int]:
    from msilib import Directory, add_data

    target = Directory(
        database,
        cabinet,
        None,
        str(bundle.parent),
        "TARGETDIR",
        "SourceDir",
        componentflags=0,
    )
    local_app_data = Directory(
        database,
        cabinet,
        target,
        ".",
        "LocalAppDataFolder",
        ".",
        componentflags=0,
    )
    programs = Directory(
        database,
        cabinet,
        local_app_data,
        ".",
        "ProgramsFolder",
        "Programs",
        componentflags=0,
    )
    install = Directory(
        database,
        cabinet,
        programs,
        bundle.name,
        "INSTALLDIR",
        short_directory_name(APP_DISPLAY_NAME),
        componentflags=0,
    )
    install.absolute = str(bundle)
    add_data(
        database,
        "Directory",
        [
            ("ProgramMenuFolder", "TARGETDIR", "."),
            (
                "ApplicationProgramsFolder",
                "ProgramMenuFolder",
                short_directory_name(APP_DISPLAY_NAME),
            ),
        ],
    )

    directory_objects = {Path("."): install}
    for relative in sorted(
        (path.relative_to(bundle) for path in bundle.rglob("*") if path.is_dir()),
        key=lambda path: path.as_posix(),
    ):
        parent = directory_objects[relative.parent]
        logical = stable_identifier("dir", relative.as_posix())
        directory = Directory(
            database,
            cabinet,
            parent,
            relative.name,
            logical,
            short_directory_name(relative.name),
            componentflags=0,
        )
        directory.absolute = str(bundle / relative)
        directory_objects[relative] = directory

    root_component = ""
    gui_file_id = ""
    file_count = 0
    for relative, directory in directory_objects.items():
        physical = bundle if relative == Path(".") else bundle / relative
        files = sorted(path for path in physical.iterdir() if path.is_file())
        if not files:
            continue
        relative_key = relative.as_posix()
        component = stable_identifier("cmp", relative_key)
        key_file = "NeoEng-D-Trace.exe" if relative == Path(".") else files[0].name
        directory.start_component(
            component=component,
            feature=feature,
            flags=0,
            keyfile=key_file,
            uuid=stable_guid(f"component:{relative_key}"),
        )
        for path in files:
            logical = directory.add_file(path.name)
            file_count += 1
            if relative == Path(".") and path.name == "NeoEng-D-Trace.exe":
                gui_file_id = logical
        if relative == Path("."):
            root_component = component

    if not root_component or not gui_file_id:
        raise ValueError("portable bundle is missing NeoEng-D-Trace.exe")
    add_data(
        database,
        "Shortcut",
        [
            (
                "NeoEngDTraceStartMenu",
                "ApplicationProgramsFolder",
                short_directory_name(APP_DISPLAY_NAME),
                root_component,
                f"[#{gui_file_id}]",
                None,
                "Prepare 2D game assets and collision geometry",
                None,
                None,
                None,
                1,
                "INSTALLDIR",
            )
        ],
    )
    add_data(
        database,
        "RemoveFile",
        [
            (
                "RemoveApplicationProgramsFolder",
                root_component,
                None,
                "ApplicationProgramsFolder",
                2,
            )
        ],
    )
    return root_component, file_count


def build_msi(
    bundle: Path,
    output: Path,
    source_commit: str,
    source_epoch: int,
) -> dict[str, object]:
    if sys.platform != "win32":
        raise RuntimeError("MSI creation is supported only on Windows")
    if not bundle.is_dir():
        raise FileNotFoundError(f"portable bundle does not exist: {bundle}")
    manifest_path = bundle / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_commit") != source_commit:
        raise ValueError("portable manifest source commit does not match MSI source")
    verify_portable_manifest(bundle, manifest)

    import msilib
    from msilib import CAB, Feature, add_data, add_tables, schema, sequence, text

    product_code = stable_guid(f"product:{APP_VERSION}:{source_commit}")
    package_code = stable_guid(f"package:{APP_VERSION}:{source_commit}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    timestamps: dict[Path, tuple[int, int]] = {}
    for path in sorted(bundle.rglob("*")):
        if path.is_file():
            stat = path.stat()
            timestamps[path] = (stat.st_atime_ns, stat.st_mtime_ns)
            os.utime(path, (source_epoch, source_epoch))

    database = None
    try:
        database = msilib.init_database(
            str(output),
            schema,
            APP_DISPLAY_NAME,
            product_code,
            APP_VERSION,
            MANUFACTURER,
        )
        _set_summary_package_code(database, package_code)
        add_tables(database, sequence)
        add_tables(database, text)
        add_data(
            database,
            "Property",
            [
                ("UpgradeCode", UPGRADE_CODE),
                ("ALLUSERS", "2"),
                ("MSIINSTALLPERUSER", "1"),
                ("LIMITUI", "1"),
                ("ARPNOMODIFY", "1"),
                ("ARPNOREPAIR", "1"),
                ("REBOOT", "ReallySuppress"),
            ],
        )
        add_data(
            database,
            "LaunchCondition",
            [("VersionNT64", "NeoEng-D-Trace requires 64-bit Windows.")],
        )
        cabinet = CAB("product.cab")
        feature = Feature(
            database,
            "MainFeature",
            APP_DISPLAY_NAME,
            "NeoEng-D-Trace application files",
            1,
            directory="INSTALLDIR",
        )
        feature.set_current()
        _, file_count = _add_bundle_tree(database, cabinet, bundle, feature)
        cabinet.commit(database)
        database.Commit()
    finally:
        database = None
        for path, (access_time, modified_time) in timestamps.items():
            os.utime(path, ns=(access_time, modified_time))

    digest = sha256_file(output)
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(
        f"{digest}  {output.name}\n", encoding="ascii", newline="\n"
    )
    result = {
        "schema_version": 1,
        "status": "BUILT",
        "product": APP_DISPLAY_NAME,
        "version": APP_VERSION,
        "source_commit": source_commit,
        "source_epoch": source_epoch,
        "product_code": product_code,
        "package_code": package_code,
        "upgrade_code": UPGRADE_CODE,
        "package_type": "windows-msi-per-user",
        "builder": f"python-msilib-{sys.version_info.major}.{sys.version_info.minor}",
        "portable_manifest_sha256": sha256_file(manifest_path),
        "files": file_count,
        "installer": output.name,
        "installer_size": output.stat().st_size,
        "installer_sha256": digest,
    }
    manifest_output = output.with_suffix(".manifest.json")
    manifest_output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-epoch", type=int, required=True)
    args = parser.parse_args()
    result = build_msi(
        args.bundle.resolve(),
        args.output.resolve(),
        args.source_commit,
        args.source_epoch,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
