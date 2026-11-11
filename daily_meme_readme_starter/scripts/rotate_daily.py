#!/usr/bin/env python3
"""Select today's approved GIF from data/manifest.json and publish assets/daily.gif."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "manifest.json"
OUTPUT = ROOT / "assets" / "daily.gif"


def main() -> int:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read manifest: {exc}", file=sys.stderr)
        return 1

    eligible = []
    for entry in data.get("entries", []):
        if entry.get("status") != "approved":
            continue
        if entry.get("license") in (None, "", "unknown", "unverified"):
            continue
        asset = entry.get("asset_path")
        if not asset:
            continue
        asset_path = (ROOT / asset).resolve()
        try:
            asset_path.relative_to(ROOT.resolve())
        except ValueError:
            print(f"Skipping path outside repository: {asset}", file=sys.stderr)
            continue
        if asset_path.is_file() and asset_path.suffix.lower() == ".gif":
            eligible.append((entry, asset_path))

    if not eligible:
        print("No approved, licensed GIFs are ready. Add an asset and approve its manifest entry.")
        return 0

    eligible.sort(key=lambda item: item[0]["id"])
    day_number = datetime.now(timezone.utc).date().toordinal()
    entry, source = eligible[day_number % len(eligible)]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, OUTPUT)

    current = {
        "date_utc": datetime.now(timezone.utc).date().isoformat(),
        "entry_id": entry["id"],
        "title": entry["title"],
        "collection": entry["collection"]
    }
    (ROOT / "data" / "current.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Selected {entry['id']}: {entry['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
