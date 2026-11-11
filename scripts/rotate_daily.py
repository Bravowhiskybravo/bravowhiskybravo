#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifest.json"
OUTPUT_PATH = ROOT / "assets" / "daily.gif"
CURRENT_PATH = ROOT / "data" / "current.json"
UNVERIFIED = {"", "unknown", "unverified", "none", "null"}


def load_manifest(path):
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise ValueError(f"Manifest file not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    if not isinstance(manifest, dict):
        raise ValueError("Manifest root must be a JSON object.")

    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Manifest 'entries' must be a list.")

    return manifest


def _looks_like_test_entry(entry):
    if not isinstance(entry, dict):
        return False
    entry_id = str(entry.get("id", ""))
    status_value = str(entry.get("status", "")).lower()
    return entry_id.startswith("test-") or status_value == "test"


def _infer_mode(mode):
    normalized = str(mode or "production").strip().lower()
    if normalized not in {"production", "test"}:
        raise ValueError(f"Unsupported mode: {mode!r}. Expected 'production' or 'test'.")
    return normalized


def _validate_gif_file(asset_path, entry_id):
    if not asset_path.exists():
        raise ValueError(f"Missing GIF for entry '{entry_id}': {asset_path}")
    if not asset_path.is_file():
        raise ValueError(f"GIF path for entry '{entry_id}' is not a file: {asset_path}")
    if asset_path.suffix.lower() != ".gif":
        raise ValueError(f"Entry '{entry_id}' does not reference a .gif file: {asset_path}")
    try:
        header = asset_path.read_bytes()[:6]
        if header[:3] not in {b"GIF"}:
            raise ValueError
        if not header.startswith((b"GIF87a", b"GIF89a")):
            raise ValueError
    except (OSError, ValueError) as exc:
        raise ValueError(f"Invalid GIF file for entry '{entry_id}': {asset_path}") from exc


def _candidate_entries(manifest, mode, repo_root):
    repo_root = Path(repo_root).resolve()
    mode_name = _infer_mode(mode)
    candidates = []

    for index, entry in enumerate(manifest.get("entries", [])):
        if not isinstance(entry, dict):
            raise ValueError(f"Manifest entry at index {index} is not an object.")

        entry_id = entry.get("id", f"entry-{index}")
        entry_status = str(entry.get("status", "")).strip().lower()
        is_test = _looks_like_test_entry(entry)

        if mode_name == "production":
            if entry_status != "approved":
                continue
            if is_test:
                continue
        elif mode_name == "test":
            if not is_test:
                continue

        license_value = str(entry.get("license", "")).strip()
        if mode_name == "production":
            if license_value.lower() in UNVERIFIED:
                raise ValueError(f"Production entry '{entry_id}' is missing or has an unknown license value.")
            if not license_value:
                raise ValueError(f"Production entry '{entry_id}' requires a license value.")

        asset_value = entry.get("asset_path")
        if not isinstance(asset_value, str) or not asset_value.strip():
            raise ValueError(f"Entry '{entry_id}' is missing an asset_path value.")

        asset_path = (repo_root / asset_value).resolve()
        try:
            asset_path.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(f"Entry '{entry_id}' asset_path must stay inside the repository: {asset_value}") from exc

        _validate_gif_file(asset_path, entry_id)

        candidates.append((entry, asset_path))

    if not candidates:
        raise ValueError(f"No eligible entries found for mode '{mode_name}'.")

    candidates.sort(key=lambda item: str(item[0].get("id", "")))
    return candidates


def select_entry(repo_root, mode="production", utc_date=None):
    repo_root = Path(repo_root).resolve()
    manifest = load_manifest(repo_root / "data" / "manifest.json")
    candidates = _candidate_entries(manifest, mode=mode, repo_root=repo_root)

    if utc_date is None:
        utc_date = datetime.now(timezone.utc).date()
    if not isinstance(utc_date, date):
        raise ValueError(f"utc_date must be a date object, got {type(utc_date)!r}.")

    selected_index = utc_date.toordinal() % len(candidates)
    entry, asset_path = candidates[selected_index]

    selection = {
        "date": utc_date.isoformat(),
        "id": entry.get("id"),
        "title": entry.get("title"),
        "category": entry.get("category"),
        "source_url": entry.get("source_url"),
        "license": entry.get("license"),
        "attribution": entry.get("attribution", ""),
        "asset_path": entry.get("asset_path"),
        "mode": _infer_mode(mode),
        "asset_file": str(asset_path),
    }
    return selection


def run_rotation(repo_root, mode="production", utc_date=None):
    repo_root = Path(repo_root).resolve()
    selection = select_entry(repo_root, mode=mode, utc_date=utc_date)

    output_path = repo_root / "assets" / "daily.gif"
    current_path = repo_root / "data" / "current.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.parent.mkdir(parents=True, exist_ok=True)

    source_path = Path(selection["asset_file"]).resolve()
    shutil.copy2(source_path, output_path)

    metadata = {
        "date": selection["date"],
        "id": selection["id"],
        "title": selection["title"],
        "category": selection["category"],
        "source_url": selection["source_url"],
        "license": selection["license"],
        "attribution": selection["attribution"],
        "asset_path": selection["asset_path"],
        "mode": selection["mode"],
    }

    with current_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Selected in {selection['mode']} mode: {selection['id']} - {selection['title']}")
    print(f"Date: {selection['date']}")
    return metadata


def main(argv=None):
    parser = argparse.ArgumentParser(description="Select a daily meme GIF for the profile README.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root to operate on.")
    parser.add_argument("--mode", choices=["production", "test"], default=os.environ.get("DAILY_MEME_MODE", "production"), help="Rotation mode to use.")
    parser.add_argument("--test", action="store_true", help="Alias for --mode test.")
    parser.add_argument("--date", type=str, help="Override the UTC date (YYYY-MM-DD).")
    args = parser.parse_args(argv)

    mode = "test" if args.test else args.mode
    date_value = None
    if args.date:
        try:
            date_value = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise SystemExit(f"Invalid date: {args.date!r}. Use YYYY-MM-DD.") from exc

    try:
        run_rotation(args.root, mode=mode, utc_date=date_value)
        return 0
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
