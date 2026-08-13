#!/usr/bin/env python3
"""Enforce the integrated line, branch, and per-module coverage policy."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _percent(value: str) -> float:
    return float(value) * 100.0


def _branch_outcomes(class_node: ET.Element) -> int:
    outcomes = 0
    for line in class_node.findall("./lines/line[@branch='true']"):
        condition = line.get("condition-coverage", "")
        match = re.search(r"\((\d+)/(\d+)\)", condition)
        if match:
            outcomes += int(match.group(2))
    return outcomes


def evaluate_coverage(
    path: Path,
    *,
    min_lines: float = 90.0,
    min_branches: float = 85.0,
    min_module_lines: float = 30.0,
    min_module_branches: float = 30.0,
) -> list[str]:
    root = ET.parse(path).getroot()
    failures: list[str] = []

    line_rate = _percent(root.attrib["line-rate"])
    branch_rate = _percent(root.attrib["branch-rate"])
    if line_rate + 1e-9 < min_lines:
        failures.append(f"total line coverage {line_rate:.2f}% < {min_lines:.2f}%")
    if branch_rate + 1e-9 < min_branches:
        failures.append(
            f"total branch coverage {branch_rate:.2f}% < {min_branches:.2f}%"
        )

    for class_node in root.findall("./packages/package/classes/class"):
        filename = class_node.attrib["filename"].replace("\\", "/")
        module_line_rate = _percent(class_node.attrib["line-rate"])
        if module_line_rate + 1e-9 < min_module_lines:
            failures.append(
                f"module line coverage {filename} {module_line_rate:.2f}% "
                f"< {min_module_lines:.2f}%"
            )
        if _branch_outcomes(class_node):
            module_branch_rate = _percent(class_node.attrib["branch-rate"])
            if module_branch_rate + 1e-9 < min_module_branches:
                failures.append(
                    f"module branch coverage {filename} {module_branch_rate:.2f}% "
                    f"< {min_module_branches:.2f}%"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage_xml", type=Path)
    parser.add_argument("--min-lines", type=float, default=90.0)
    parser.add_argument("--min-branches", type=float, default=85.0)
    parser.add_argument("--min-module-lines", type=float, default=30.0)
    parser.add_argument("--min-module-branches", type=float, default=30.0)
    args = parser.parse_args()

    failures = evaluate_coverage(
        args.coverage_xml,
        min_lines=args.min_lines,
        min_branches=args.min_branches,
        min_module_lines=args.min_module_lines,
        min_module_branches=args.min_module_branches,
    )
    if failures:
        print("Coverage policy failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(
        "Coverage policy passed: total lines >= 90%, total branches >= 85%, "
        "measurable modules >= 30%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
