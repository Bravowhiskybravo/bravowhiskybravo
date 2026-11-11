# Daily meme rotation starter

## Included
- `data/manifest.json`: 50 technical meme concepts, all marked `candidate`.
- `scripts/rotate_daily.py`: selects a GIF only when its manifest entry is `approved`, has a GIF asset, and has a non-empty verified license field.
- `.github/workflows/daily-meme.yml`: runs the rotation daily and can also be started manually.
- `README-snippet.md`: the compact README section.

## Add an asset
1. Put a GIF in `archive/tech-culture/` or `archive/internet-culture/`.
2. Add or edit an entry in `data/manifest.json`.
3. Set `asset_path` to its repository-relative path, e.g. `archive/tech-culture/arch-meme.gif`.
4. Fill in `source_url`, `license`, and `attribution` accurately.
5. Change `status` to `approved` only after checking that you have permission or a suitable license to redistribute the asset.
6. Commit the changes.

The workflow copies an approved GIF to `assets/daily.gif`. The README image path therefore stays unchanged.

## GitHub setup
1. Upload the contents of this ZIP into the root of `Bravowhiskybravo/bravowhiskybravo`, preserving folder paths.
2. Add the contents of `README-snippet.md` to your existing `README.md`.
3. In GitHub, open Settings -> Actions -> General -> Workflow permissions. Ensure the workflow has read and write permissions if repository policy requires enabling this.
4. Open Actions -> Daily meme rotation -> Run workflow to test it manually.

The scheduled workflow runs at 10:15 UTC daily. GitHub may delay scheduled starts, and scheduled workflows use the default branch.

## Important
The archive folders are intentionally empty. The 50 technical entries are candidate ideas, not cleared media assets. The internet-culture list still needs its duplicate and date cleanup before being added. Do not upload or redistribute GIFs just because they are easy to find; verify licensing/permission and attribution first.
