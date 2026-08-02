#!/usr/bin/env python3
"""Move aged raw facts to an archive and retain equivalent verified rollups."""

from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from pathlib import Path

from aggregate import aggregate
from common import read_json, write_json


def projection_snapshot(root: Path) -> dict[str, bytes]:
    """Capture every generated projection for compaction equivalence checking."""
    paths = [root / "clients.json"] + [path for directory in ("leaderboard", "matchmaking", "site/data") for path in (root / directory).rglob("*.json") if (root / directory).exists()]
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in paths if path.is_file()}


def compact(root: Path, *, before: str, archive_root: Path) -> list[Path]:
    """Archive selected raw facts, write rollups, and roll back if projections differ."""
    selected: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path in sorted((root / "results" / "raw").rglob("*.json")) if (root / "results" / "raw").exists() else []:
        record = read_json(path)
        if str(record.get("completedAt", ""))[:10] < before:
            date = str(record["completedAt"])[:7].split("-")
            selected[(date[0], date[1])].append(path)
    aggregate(root)
    before_snapshot = projection_snapshot(root)
    rollups: list[Path] = []
    moved: list[tuple[Path, Path]] = []
    try:
        for (year, month), paths in sorted(selected.items()):
            records = [read_json(path) for path in paths]
            target = root / "results" / "rollups" / year / f"{month}.json"
            write_json(target, {"schemaVersion": 1, "month": f"{year}-{month}", "results": sorted(records, key=lambda item: (str(item.get("completedAt")), str(item.get("payloadHash"))))})
            rollups.append(target)
            for source in paths:
                destination = archive_root / source.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                moved.append((source, destination))
        aggregate(root)
        if projection_snapshot(root) != before_snapshot:
            raise ValueError("compaction changed a derived projection")
    except Exception:
        for source, destination in reversed(moved):
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
        for rollup in rollups:
            rollup.unlink(missing_ok=True)
        aggregate(root)
        raise
    return rollups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--before", required=True, help="exclusive ISO date, for example 2026-05-01")
    parser.add_argument("--archive-root", type=Path, required=True, help="checkout of the archive branch")
    arguments = parser.parse_args()
    paths = compact(arguments.root.resolve(), before=arguments.before, archive_root=arguments.archive_root.resolve())
    print(f"wrote {len(paths)} verified rollup(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
