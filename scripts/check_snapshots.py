#!/usr/bin/env python3
"""Reject pull requests that modify or delete an existing ranking snapshot."""

from __future__ import annotations

import argparse
import subprocess


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


def main() -> int:
    """Check snapshot changes from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    arguments = parser.parse_args()
    violations = changed_snapshots(arguments.base)
    if violations:
        print("existing snapshots are immutable:")
        for path in violations:
            print(f"- {path}")
        return 1
    print("snapshot changes are additive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
