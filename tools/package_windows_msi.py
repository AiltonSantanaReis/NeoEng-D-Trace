"""Build a deterministic per-user Windows MSI from the portable bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import tempfile
import uuid
from pathlib import Path
from xml.sax.saxutils import quoteattr

from src.core.app_identity import APP_DISPLAY_NAME, APP_VERSION

PRODUCT_NAMESPACE = uuid.UUID("6e69818d-93a3-5a86-953c-2326c536d06f")
UPGRADE_CODE = "{F13BFDC4-1445-56D9-A72E-8812CA7F9E87}"
MANUFACTURER = "NeoEng-D-Trace"
WIX_VERSION = "4.0.6"
ROOT = Path(__file__).resolve().parents[1]


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


def _cfb_sector_offset(sector_id: int, sector_size: int) -> int:
    return (sector_id + 1) * sector_size


def _cfb_fat_sector_ids(data: bytearray, sector_size: int) -> list[int]:
    number_of_fat_sectors = struct.unpack_from("<I", data, 44)[0]
    first_difat_sector = struct.unpack_from("<I", data, 68)[0]
    number_of_difat_sectors = struct.unpack_from("<I", data, 72)[0]
    sector_ids = [
        struct.unpack_from("<I", data, 76 + index * 4)[0] for index in range(109)
    ]
    sector_ids = [sector_id for sector_id in sector_ids if sector_id < 0xFFFFFFFA]
    current = first_difat_sector
    for _ in range(number_of_difat_sectors):
        offset = _cfb_sector_offset(current, sector_size)
        if offset + sector_size > len(data):
            raise ValueError("MSI DIFAT sector is outside the output")
        for index in range((sector_size // 4) - 1):
            sector_id = struct.unpack_from("<I", data, offset + index * 4)[0]
            if sector_id < 0xFFFFFFFA:
                sector_ids.append(sector_id)
        current = struct.unpack_from("<I", data, offset + sector_size - 4)[0]
    if len(sector_ids) < number_of_fat_sectors:
        raise ValueError("MSI FAT directory is incomplete")
    return sector_ids[:number_of_fat_sectors]


def _cfb_directory_sector_ids(data: bytearray, sector_size: int) -> list[int]:
    fat_sector_ids = _cfb_fat_sector_ids(data, sector_size)
    fat: list[int] = []
    for sector_id in fat_sector_ids:
        offset = _cfb_sector_offset(sector_id, sector_size)
        if offset + sector_size > len(data):
            raise ValueError("MSI FAT sector is outside the output")
        fat.extend(
            struct.unpack_from("<I", data, offset + index * 4)[0]
            for index in range(sector_size // 4)
        )
    current = struct.unpack_from("<I", data, 48)[0]
    sectors: list[int] = []
    visited: set[int] = set()
    while current < 0xFFFFFFFA:
        if current in visited or current >= len(fat):
            raise ValueError("MSI directory chain is invalid")
        offset = _cfb_sector_offset(current, sector_size)
        if offset + sector_size > len(data):
            raise ValueError("MSI directory sector is outside the output")
        visited.add(current)
        sectors.append(current)
        current = fat[current]
    return sectors


def normalize_msi_storage_timestamps(path: Path) -> None:
    data = bytearray(path.read_bytes())
    if data[:8] != bytes.fromhex("D0CF11E0A1B11AE1"):
        raise ValueError("MSI output is not a Compound File Binary document")
    sector_shift = struct.unpack_from("<H", data, 30)[0]
    if sector_shift not in (9, 12):
        raise ValueError(f"unsupported MSI sector shift: {sector_shift}")
    sector_size = 1 << sector_shift
    first_directory_sector = struct.unpack_from("<I", data, 48)[0]
    if first_directory_sector >= 0xFFFFFFFA:
        raise ValueError("MSI output has no valid directory sector")
    root_offset = _cfb_sector_offset(first_directory_sector, sector_size)
    if root_offset + 128 > len(data):
        raise ValueError("MSI root directory entry is outside the output")
    name_length = struct.unpack_from("<H", data, root_offset + 64)[0]
    object_type = data[root_offset + 66]
    root_name = data[root_offset : root_offset + name_length - 2].decode("utf-16le")
    if root_name != "Root Entry" or object_type != 5:
        raise ValueError("MSI root directory entry is invalid")
    try:
        directory_sectors = _cfb_directory_sector_ids(data, sector_size)
    except ValueError as error:
        raise ValueError(f"MSI directory chain is invalid: {error}") from error
    for sector_id in directory_sectors:
        sector_offset = _cfb_sector_offset(sector_id, sector_size)
        for entry_offset in range(0, sector_size, 128):
            object_type = data[sector_offset + entry_offset + 66]
            if object_type in (1, 2, 5):
                data[
                    sector_offset
                    + entry_offset
                    + 100 : sector_offset
                    + entry_offset
                    + 116
                ] = bytes(16)
    temporary = path.with_suffix(path.suffix + ".normalizing")
    try:
        temporary.write_bytes(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _xml_attribute(name: str, value: str) -> str:
    return f"{name}={quoteattr(value)}"


def _component_xml(relative: Path) -> tuple[str, int]:
    relative_key = relative.as_posix()
    component_id = stable_identifier("cmp", relative_key)
    file_id = stable_identifier("fil", relative_key)
    source = relative_key
    return (
        f"      <Component Id={quoteattr(component_id)} "
        f"Guid={quoteattr(stable_guid(f'component:{relative_key}'))}>\n"
        f"        <File Id={quoteattr(file_id)} Source={quoteattr(source)} "
        'KeyPath="yes" />\n'
        "      </Component>",
        1,
    )


def _directory_xml(bundle: Path) -> tuple[str, list[str], int]:
    files = sorted(
        path.relative_to(bundle) for path in bundle.rglob("*") if path.is_file()
    )
    directory_set: set[Path] = set()
    for relative in files:
        current = relative.parent
        while current != Path("."):
            directory_set.add(current)
            current = current.parent
    directories = sorted(
        directory_set,
        key=lambda path: (len(path.parts), path.as_posix()),
    )
    files_by_directory: dict[Path, list[Path]] = {}
    for relative in files:
        files_by_directory.setdefault(relative.parent, []).append(relative)
    component_refs: list[str] = []

    def render(directory: Path, indent: str) -> tuple[list[str], int]:
        lines: list[str] = []
        count = 0
        for relative in files_by_directory.get(directory, []):
            component, component_count = _component_xml(relative)
            lines.extend(component.replace("      ", indent + "  ").splitlines())
            component_refs.append(stable_identifier("cmp", relative.as_posix()))
            count += component_count
        children = [child for child in directories if child.parent == directory]
        for child in children:
            directory_id = stable_identifier("dir", child.as_posix())
            lines.append(
                f"{indent}<Directory {_xml_attribute('Id', directory_id)} "
                f"{_xml_attribute('Name', child.name)}>"
            )
            child_lines, child_count = render(child, indent + "  ")
            lines.extend(child_lines)
            lines.append(f"{indent}</Directory>")
            count += child_count
        return lines, count

    body, file_count = render(Path("."), "      ")
    return "\n".join(body), component_refs, file_count


def _write_wix_source(bundle: Path, path: Path, product_code: str) -> int:
    directory_body, component_refs, file_count = _directory_xml(bundle)
    shortcut_component = stable_identifier("cmp", "start-menu")
    icon_id = "NeoEngDTraceIcon.ico"
    component_refs.append(shortcut_component)
    lines = [
        '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">',
        f"  <Package {_xml_attribute('Name', APP_DISPLAY_NAME)} "
        f"{_xml_attribute('Manufacturer', MANUFACTURER)} "
        f"{_xml_attribute('Version', APP_VERSION)} "
        f"{_xml_attribute('ProductCode', product_code)} "
        f"{_xml_attribute('UpgradeCode', UPGRADE_CODE)} "
        'Scope="perUser" Compressed="yes">',
        (
            "    <MajorUpgrade "
            'DowngradeErrorMessage="A newer version is already installed." />'
        ),
        '    <MediaTemplate EmbedCab="yes" />',
        (
            '    <Launch Condition="VersionNT64" '
            'Message="NeoEng-D-Trace requires 64-bit Windows." />'
        ),
        '    <Property Id="ALLUSERS" Value="2" />',
        '    <Property Id="MSIINSTALLPERUSER" Value="1" />',
        '    <Property Id="LIMITUI" Value="1" />',
        '    <Property Id="ARPNOMODIFY" Value="1" />',
        '    <Property Id="ARPNOREPAIR" Value="1" />',
        '    <Property Id="REBOOT" Value="ReallySuppress" />',
        '    <StandardDirectory Id="LocalAppDataFolder">',
        f'      <Directory Id="INSTALLDIR" Name={quoteattr(APP_DISPLAY_NAME)}>',
        directory_body,
        "      </Directory>",
        "    </StandardDirectory>",
        '    <StandardDirectory Id="ProgramMenuFolder">',
        (
            '      <Directory Id="ApplicationProgramsFolder" '
            f"Name={quoteattr(APP_DISPLAY_NAME)}>"
        ),
        (
            f"        <Component Id={quoteattr(shortcut_component)} "
            f'Guid={quoteattr(stable_guid("component:start-menu"))}>'
        ),
        (
            f'          <Shortcut Id="NeoEngDTraceStartMenu" '
            f"Name={quoteattr(APP_DISPLAY_NAME)} "
            f'Target="[#{stable_identifier("fil", "NeoEng-D-Trace.exe")}]" '
            'WorkingDirectory="INSTALLDIR" '
            f'Description="Prepare 2D game assets and collision geometry" '
            f'Icon={quoteattr(icon_id)} IconIndex="0">'
        ),
        (
            f"            <Icon Id={quoteattr(icon_id)} "
            f'SourceFile={quoteattr("assets/branding/neoeng-d-trace-icon.ico")} />'
        ),
        "          </Shortcut>",
        (
            "          <RemoveFolder "
            'Id="RemoveApplicationProgramsFolder" On="uninstall" />'
        ),
        (
            '          <RegistryValue Root="HKCU" Key="Software\\NeoEng-D-Trace" '
            'Name="Installed" Type="integer" Value="1" KeyPath="yes" />'
        ),
        "        </Component>",
        "      </Directory>",
        "    </StandardDirectory>",
        '    <Feature Id="MainFeature" Title="NeoEng-D-Trace" Level="1">',
    ]
    lines.extend(
        f"      <ComponentRef Id={quoteattr(component_id)} />"
        for component_id in component_refs
    )
    lines.extend(["    </Feature>", "  </Package>", "</Wix>"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return file_count


def _run_wix(source: Path, bundle: Path, output: Path, intermediate: Path) -> None:
    version = subprocess.run(
        ["dotnet", "tool", "run", "wix", "--version"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if version.returncode != 0:
        raise RuntimeError(
            "WiX tool is unavailable; run 'dotnet tool restore' before building"
        )
    reported = (version.stdout or version.stderr).strip()
    if not reported.startswith(WIX_VERSION + "+"):
        raise RuntimeError(f"unsupported WiX version: {reported}")
    command = [
        "dotnet",
        "tool",
        "run",
        "wix",
        "build",
        str(source),
        "-b",
        str(bundle),
        "-out",
        str(output),
        "-arch",
        "x64",
        "-pdbtype",
        "none",
        "-intermediatefolder",
        str(intermediate),
    ]
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"WiX build failed with exit code {result.returncode}")


def _set_package_code(output: Path, package_code: str) -> None:
    script = ROOT / "tools" / "set_msi_package_code.ps1"
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Path",
            str(output),
            "-PackageCode",
            package_code,
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Windows Installer Summary Information update failed with "
            f"exit code {result.returncode}"
        )


def build_msi(
    bundle: Path,
    output: Path,
    source_commit: str,
    source_epoch: int,
) -> dict[str, object]:
    if os.name != "nt":
        raise RuntimeError("MSI creation is supported only on Windows")
    if not bundle.is_dir():
        raise FileNotFoundError(f"portable bundle does not exist: {bundle}")
    manifest_path = bundle / "release-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_commit") != source_commit:
        raise ValueError("portable manifest source commit does not match MSI source")
    verify_portable_manifest(bundle, manifest)

    product_code = stable_guid(f"product:{APP_VERSION}:{source_commit}")
    package_code = stable_guid(f"package:{APP_VERSION}:{source_commit}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="neoeng-wix-") as temporary:
        temporary_path = Path(temporary)
        source = temporary_path / "package.wxs"
        intermediate = temporary_path / "obj"
        file_count = _write_wix_source(bundle, source, product_code)
        _run_wix(source, bundle, output, intermediate)
    _set_package_code(output, package_code)
    normalize_msi_storage_timestamps(output)
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
        "builder": f"wix-{WIX_VERSION}",
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
