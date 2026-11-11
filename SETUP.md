# Daily Meme setup

## Repository structure

- `assets/daily.gif`: the generated display image used in the profile README.
- `assets/archive/internet-culture/`: archived GIFs for the rotation library.
- `data/manifest.json`: approved and test candidates for the selector.
- `data/current.json`: metadata for the current daily pick.
- `scripts/rotate_daily.py`: selection and copy logic.
- `.github/workflows/daily-meme.yml`: scheduled and manual GitHub Action.

## Adding a new meme entry

1. Add the GIF file under the appropriate archive folder.
2. Add a manifest object to the `entries` array in `data/manifest.json`.
3. Include:
   - `id`
   - `title`
   - `collection`
   - `category`
   - `year`
   - `asset_path`
   - `source_url`
   - `license`
   - `attribution`
   - `status`
4. Use `approved` status only for production candidates.

## Production approval rules

- Production entries must be `approved`.
- License values must not be blank, `unknown`, `unverified`, `null`, or `none`.
- GIF file paths must resolve inside the repository.
- Test entries are only allowed in test mode.

## manual test rotation

```bash
python scripts/rotate_daily.py --mode test
```

## manual production rotation

```bash
python scripts/rotate_daily.py --mode production
```

## GitHub Actions permissions

GitHub must allow the workflow to write repository contents:

1. Open GitHub repository Settings.
2. Go to Actions > General.
3. Set Workflow permissions to Read and write permissions.
4. Save the changes.

## Triggering GitHub Actions manually

1. Open the repository on GitHub.
2. Go to Actions.
3. Select `Daily Meme`.
4. Choose `Run workflow`.
5. Set the mode to `production` or `test`.

## Notes

- The scheduled workflow runs in production mode.
- Manual workflow dispatch can choose `test` mode, but the cron job remains production-only.
- The script fails clearly if there are no eligible entries or if a referenced GIF is missing or invalid.
