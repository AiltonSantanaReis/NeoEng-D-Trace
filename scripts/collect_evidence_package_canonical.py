#!/usr/bin/env python3
"""Canonical entry point for official evidence-package collection.

The implementation is shared with the collector module; this entry point fixes
the normative phase spelling so both F2 and F02 are represented as F02 in the
package identity while preserving the collector's no-overwrite behavior.
"""

from __future__ import annotations

import re
import sys

from scripts import collect_evidence_package as collector


collector.PHASE_PATTERN = re.compile(r"^F[0-9]+$", re.IGNORECASE)


if __name__ == "__main__":
    raise SystemExit(collector.main())
