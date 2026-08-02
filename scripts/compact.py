#!/usr/bin/env python3
"""Pack aged raw facts into equivalent monthly rollups for archival transfer."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from common import read_json, write_json


def compact(root: Path, *, before: str) -> list[Path]:
    """Write rollups for facts completed before an ISO-8601 date without deleting facts."""
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in sorted((root / "results" / "raw").rglob("*.json")) if (root / "results" / "raw").exists() else []:
        record = read_json(path)
        if str(record.get("completedAt", ""))[:10] < before:
            date = str(record["completedAt"])[:7].split("-")
            grouped[(date[0], date[1])].append(record)
    written: list[Path] = []
    for (year, month), records in sorted(grouped.items()):
        target = root / "results" / "rollups" / year / f"{month}.json"
        write_json(target, {"schemaVersion": 1, "month": f"{year}-{month}", "results": sorted(records, key=lambda item: (str(item.get("completedAt")), str(item.get("payloadHash"))))})
        written.append(target)
    return written


def main() -> int:
    """Run compaction from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--before", required=True, help="exclusive ISO date, for example 2026-05-01")
    arguments = parser.parse_args()
    paths = compact(arguments.root.resolve(), before=arguments.before)
    print(f"wrote {len(paths)} rollup(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
