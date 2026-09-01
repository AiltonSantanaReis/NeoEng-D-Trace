"""Print sanitized top cumulative functions from local O-2 cProfile files."""

from __future__ import annotations

import argparse
import pstats
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    args = parser.parse_args()
    profiles = sorted(args.input_dir.glob("o2-*.prof"))
    if not profiles:
        raise SystemExit("no O-2 profile files found")
    for profile_path in profiles:
        stats = pstats.Stats(str(profile_path))
        rows = []
        for (filename, line, function), values in stats.stats.items():
            primitive, calls, total, cumulative, _callers = values
            rows.append(
                (
                    float(cumulative),
                    Path(filename).name,
                    int(line),
                    str(function),
                    int(calls),
                    float(total),
                    int(primitive),
                )
            )
        print(f"PROFILE={profile_path.name}")
        for cumulative, filename, line, function, calls, total, primitive in sorted(
            rows, reverse=True
        )[:25]:
            print(
                "FUNCTION cumulative_s={:.6f} total_s={:.6f} calls={} "
                "primitive={} file={} line={} name={}".format(
                    cumulative, total, calls, primitive, filename, line, function
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
