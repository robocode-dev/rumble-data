#!/usr/bin/env python3
"""Extract the one required fenced JSON envelope from a GitHub issue body."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FENCED_JSON = re.compile(r"```json\s*\n(?P<payload>.*?)\n```", re.DOTALL)


def extract(body: str) -> dict:
    """Return the sole JSON block in body or raise a useful error."""
    matches = FENCED_JSON.findall(body)
    if len(matches) != 1:
        raise ValueError("issue body must contain exactly one fenced json block")
    value = json.loads(matches[0])
    if not isinstance(value, dict):
        raise ValueError("fenced json block must be an object")
    return value


def main() -> int:
    """Extract a body file into a JSON envelope file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        value = extract(arguments.body.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"envelope extraction failed: {error}")
        return 1
    arguments.output.write_text(json.dumps(value) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
