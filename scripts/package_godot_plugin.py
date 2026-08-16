"""Create a deterministic ZIP containing the Godot source-only addon."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = ROOT / "integrations" / "godot"
ALLOWED_SUFFIXES = {".gd", ".cfg", ".md"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    files = sorted(path for path in PLUGIN_ROOT.rglob("*") if path.is_file())
    if not files:
        raise SystemExit("Godot addon source is empty")
    for path in files:
        if path.suffix not in ALLOWED_SUFFIXES:
            raise SystemExit(f"unsupported addon file: {path.name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(PLUGIN_ROOT).as_posix()
            info = ZipInfo(f"neoeng-d-trace-godot/{relative}")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    print(output.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
