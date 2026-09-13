#!/usr/bin/env python3
"""Reject pull requests that modify or delete an existing ranking snapshot."""

from __future__ import annotations

import argparse
import json
import subprocess
from typing import Any

HISTORY_PATH = "site/data/history.json"


def changed_snapshots(base: str) -> list[str]:
    """Return non-additive snapshot changes relative to a git base."""
    result = subprocess.run(
        ["git", "diff", "--name-status", f"{base}...HEAD", "--", "site/data/snapshots"],
        check=True,
        capture_output=True,
        text=True,
    )
    violations = []
    for line in result.stdout.splitlines():
        status, _, path = line.partition("\t")
        if status != "A":
            violations.append(path or line)
    return violations


def manifest_snapshots(revision: str) -> list[Any] | None:
    """Return the history manifest's snapshot entries at a revision, or None when it has no manifest."""
    result = subprocess.run(
        ["git", "show", f"{revision}:{HISTORY_PATH}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = json.loads(result.stdout)
    snapshots = value.get("snapshots") if isinstance(value, dict) else None
    return snapshots if isinstance(snapshots, list) else []


def changed_manifest_entries(base_entries: list[Any] | None, head_entries: list[Any] | None) -> list[str]:
    """Return base manifest snapshot entries that the head manifest no longer carries unchanged."""
    head = head_entries or []
    violations = []
    for entry in base_entries or []:
        if entry not in head:
            month = entry.get("month") if isinstance(entry, dict) else None
            violations.append(f"{HISTORY_PATH} snapshot entry {month or json.dumps(entry)}")
    return violations


def main() -> int:
    """Check snapshot changes from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    arguments = parser.parse_args()
    violations = changed_snapshots(arguments.base)
    merge_base = subprocess.run(
        ["git", "merge-base", arguments.base, "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    violations += changed_manifest_entries(manifest_snapshots(merge_base), manifest_snapshots("HEAD"))
    if violations:
        print("existing snapshots are immutable:")
        for path in violations:
            print(f"- {path}")
        return 1
    print("snapshot changes are additive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
