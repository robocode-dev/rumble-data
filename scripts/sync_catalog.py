#!/usr/bin/env python3
"""Synchronize the published Rumble bot catalog into this repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, Any
from urllib.request import Request, urlopen

from common import normalized_catalog_bots, read_json, write_json

Fetch = Callable[[str], bytes]


def fetch_source(url: str) -> bytes:
    """Fetch the declared catalog source with an explicit user agent."""
    request = Request(url, headers={"User-Agent": "tank-royale-rumble-data-catalog-sync"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def source_catalog(url: str, fetch: Fetch) -> dict[str, Any]:
    """Load and minimally validate the generated Rumble bot catalog."""
    try:
        source = json.loads(fetch(url).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load catalog source `{url}`: {error}") from error
    if not isinstance(source, dict) or source.get("schemaVersion") != 1:
        raise ValueError("catalog source has an unsupported schema")
    source["bots"] = normalized_catalog_bots(source.get("bots"))
    return source


def synchronized_catalog(catalog: dict[str, Any], fetch: Fetch = fetch_source) -> dict[str, Any]:
    """Return the locally stored catalog refreshed from its declared source."""
    source_url = catalog.get("source")
    if not isinstance(source_url, str) or not source_url.startswith("https://"):
        raise ValueError("catalog.json must declare an HTTPS source URL")
    source = source_catalog(source_url, fetch)
    return {
        "schemaVersion": 1,
        "source": source_url,
        "sourceCommit": source.get("commit"),
        "sourceGeneratedAt": source.get("generatedAt"),
        "bots": source["bots"],
    }


def sync(root: Path, fetch: Fetch = fetch_source) -> None:
    """Refresh catalog.json from its declared generated source."""
    catalog_path = root / "catalog.json"
    write_json(catalog_path, synchronized_catalog(read_json(catalog_path), fetch))


def main() -> int:
    """Synchronize catalog.json from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        sync(arguments.root.resolve())
    except (OSError, ValueError) as error:
        print(f"catalog synchronization failed: {error}")
        return 1
    print("synchronized catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
