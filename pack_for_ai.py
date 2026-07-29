"""Create a bounded, deterministic text snapshot of the project.

The snapshot intentionally excludes environments, caches, generated reports,
and backup directories. It is a support artifact, not a source-of-truth backup.
"""

from __future__ import annotations

from pathlib import Path

OUTPUT_FILE = Path("project_context.txt")
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".toml", ".ini", ".yaml", ".yml"}
IGNORE_DIRS = {
    ".git",
    ".github",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vscode",
    "__pycache__",
    "backup",
    "backups",
    "build",
    "dist",
    "env",
    "images",
    "output",
    "venv",
}
IGNORE_FILES = {
    "pack_for_ai.py",
    "project_context.txt",
    "poetry.lock",
    "uv.lock",
    "config.json",
    "config.json.corrupted",
    "report_api_locations.json",
    "tests_compat_report.json",
}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024


def _is_ignored(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return any(part in IGNORE_DIRS for part in relative.parts)


def _eligible_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or _is_ignored(path, root):
            continue
        if path.name in IGNORE_FILES or path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix().lower())


def pack_project(root_dir: Path | None = None, output_file: Path | None = None) -> Path:
    root = (root_dir or Path.cwd()).resolve()
    output = output_file or (root / OUTPUT_FILE)
    files = _eligible_files(root)

    with output.open("w", encoding="utf-8", newline="\n") as outfile:
        outfile.write("# Snapshot técnico do projeto\n")
        outfile.write("# Gerado automaticamente; não substitui Git nem backup validado.\n\n")
        outfile.write("# --- ARQUIVOS INCLUÍDOS ---\n")
        for path in files:
            outfile.write(f"- {path.relative_to(root).as_posix()}\n")

        outfile.write("\n# --- CONTEÚDO DOS ARQUIVOS ---\n")
        for path in files:
            relative = path.relative_to(root).as_posix()
            outfile.write(f"\n{'=' * 80}\nFILE: {relative}\n{'=' * 80}\n")
            try:
                outfile.write(path.read_text(encoding="utf-8-sig", errors="replace"))
            except OSError as exc:
                outfile.write(f"Erro ao ler arquivo: {exc}\n")
            outfile.write("\n")

    return output


if __name__ == "__main__":
    generated = pack_project()
    print(f"Snapshot criado em: {generated}")
