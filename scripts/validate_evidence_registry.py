#!/usr/bin/env python3
"""Validate the canonical ID registry and active-document links.

This is an independent gate. It intentionally does not modify documents,
repair IDs, rewrite links or offer a force/bypass option.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ID_RE = re.compile(
    r"\b(?:MOD|REQ|FEAT|CMP|TEST|EVID|BUILD|BASE|ADR|RISK)-[A-Z0-9]+(?:-[A-Z0-9]+)+\b"
)
DECL_RE = re.compile(r"^\s*-\s+id:\s*([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\]\(([^)]+)\)")


class ContractError(RuntimeError):
    pass


def validate_registry(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ContractError(f"registry not found: {path}")
    text = path.read_text(encoding="utf-8")
    declarations = DECL_RE.findall(text)
    if not declarations:
        raise ContractError("registry has no YAML ID declarations")
    duplicates = sorted({identifier for identifier in declarations if declarations.count(identifier) > 1})
    if duplicates:
        raise ContractError(f"duplicate declared IDs: {duplicates}")
    all_ids = set(ID_RE.findall(text))
    declared = set(declarations)
    undeclared = sorted(all_ids - declared)
    # References are allowed, but they must resolve to a declared identifier.
    if undeclared:
        raise ContractError(f"IDs referenced but not declared: {undeclared}")
    return {
        "status": "PASS",
        "declared_ids": len(declared),
        "registry": str(path),
    }


def validate_document_index(path: Path, workspace: Path) -> dict[str, object]:
    if not path.is_file():
        raise ContractError(f"document index not found: {path}")
    text = path.read_text(encoding="utf-8")
    links = []
    missing = []
    for raw_target in LINK_RE.findall(text):
        if raw_target.startswith(("http://", "https://", "#")):
            continue
        target = raw_target.replace("%20", " ")
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = workspace / candidate
        links.append(str(candidate))
        if not candidate.is_file():
            missing.append(str(candidate))
    if missing:
        raise ContractError(f"document index has missing links: {missing}")
    return {"status": "PASS", "linked_documents": len(links), "index": str(path)}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--document-index", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        workspace = args.workspace.resolve()
        report = {
            "status": "PASS",
            "registry": validate_registry(args.registry.resolve()),
            "documents": validate_document_index(args.document_index.resolve(), workspace),
        }
    except ContractError as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
