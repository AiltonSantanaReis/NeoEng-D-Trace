# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

repository_root = Path(SPECPATH).parent
entry_point = repository_root / "app.py"
icon_path = repository_root / "assets" / "branding" / "neoeng-d-trace-icon.ico"
version_resource = Path(SPECPATH) / "windows_version_info.txt"

analysis = Analysis(
    [str(entry_point)],
    pathex=[str(repository_root)],
    binaries=[],
    datas=[(str(icon_path), "assets/branding")],
    hiddenimports=["pygltflib"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # CuPy is an optional GPU accelerator. The portable Windows build must
    # use the deterministic CPU fallback instead of shipping CUDA runtimes
    # that can shadow the host Windows CRT and Qt dependencies.
    excludes=["cupy", "cupyx"],
    noarchive=False,
    optimize=0,
)

# API-set and Universal CRT DLLs are Windows system components. They can be
# discovered from developer-toolkit PATH entries during PyInstaller analysis,
# but must never be copied into a portable bundle where they can shadow the
# host runtime and break Qt loading.
analysis.binaries = [
    item
    for item in analysis.binaries
    if not (
        Path(item[0]).name.lower().startswith("api-ms-win-")
        or Path(item[0]).name.lower() == "ucrtbase.dll"
    )
]

python_archive = PYZ(analysis.pure)

gui_executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="NeoEng-D-Trace",
    icon=str(icon_path),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(version_resource),
)

cli_executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="NeoEng-D-Trace-CLI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=str(version_resource),
)

collection = COLLECT(
    gui_executable,
    cli_executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="NeoEng-D-Trace",
)
