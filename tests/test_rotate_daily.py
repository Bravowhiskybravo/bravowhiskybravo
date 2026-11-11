import importlib.util
import json
from datetime import date
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'rotate_daily.py'
SPEC = importlib.util.spec_from_file_location('rotate_daily', SCRIPT_PATH)
rotate_daily = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rotate_daily)


def _make_gif_bytes():
    return b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'


def _repo_setup(tmp_path, *, entries=None):
    repo = tmp_path / 'repo'
    (repo / 'assets' / 'archive' / 'internet-culture').mkdir(parents=True)
    (repo / 'data').mkdir(parents=True)
    (repo / 'scripts').mkdir(parents=True)

    gif_bytes = _make_gif_bytes()
    installed = []
    if entries is None:
        entries = [
            {
                'id': 'prod-001',
                'title': 'Approved Cat Meme',
                'collection': 'test-assets',
                'category': 'internet-culture',
                'year': 2024,
                'asset_path': 'assets/archive/internet-culture/cat.gif',
                'source_url': 'https://example.com/cat',
                'license': 'CC BY 4.0',
                'attribution': 'Example author, CC BY 4.0.',
                'status': 'approved',
            },
            {
                'id': 'prod-002',
                'title': 'Approved Dog Meme',
                'collection': 'test-assets',
                'category': 'internet-culture',
                'year': 2024,
                'asset_path': 'assets/archive/internet-culture/dog.gif',
                'source_url': 'https://example.com/dog',
                'license': 'CC BY 4.0',
                'attribution': 'Another author, CC BY 4.0.',
                'status': 'approved',
            },
        ]

    for i, entry in enumerate(entries, start=1):
        rel = Path(entry['asset_path'])
        asset_path = repo / rel
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        if not asset_path.exists():
            asset_path.write_bytes(gif_bytes)
        installed.append(entry)

    manifest = {'entries': installed}
    (repo / 'data' / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return repo


def test_valid_production_entries_are_selected(tmp_path):
    repo = _repo_setup(tmp_path)
    selected = rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))
    assert selected['id'] in {'prod-001', 'prod-002'}


def test_candidates_are_excluded_in_production_mode(tmp_path):
    repo = _repo_setup(tmp_path, entries=[{
        'id': 'draft-001',
        'title': 'Draft meme',
        'collection': 'test-assets',
        'category': 'internet-culture',
        'year': 2024,
        'asset_path': 'assets/archive/internet-culture/draft.gif',
        'source_url': 'https://example.com/draft',
        'license': 'unknown',
        'attribution': 'Unknown source.',
        'status': 'draft'
    }])
    with pytest.raises(ValueError, match='No eligible entries'):
        rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))


def test_test_entries_can_be_selected_in_test_mode(tmp_path):
    repo = _repo_setup(tmp_path, entries=[{
        'id': 'test-001',
        'title': 'Open Access Meme',
        'collection': 'test-assets',
        'category': 'internet-culture',
        'year': 2020,
        'asset_path': 'assets/archive/internet-culture/open-access-meme.gif',
        'source_url': 'https://commons.wikimedia.org/wiki/File:Open_access_meme.gif',
        'license': 'CC0 1.0',
        'attribution': 'Georg Reimer; minor improvements by Thomas Shafee. CC0 1.0.',
        'status': 'test'
    }])
    selected = rotate_daily.select_entry(repo, mode='test', utc_date=date(2026, 1, 1))
    assert selected['id'] == 'test-001'


def test_unknown_licenses_are_rejected_in_production_mode(tmp_path):
    repo = _repo_setup(tmp_path, entries=[{
        'id': 'prod-001',
        'title': 'Bad License',
        'collection': 'test-assets',
        'category': 'internet-culture',
        'year': 2024,
        'asset_path': 'assets/archive/internet-culture/bad.gif',
        'source_url': 'https://example.com/bad',
        'license': 'unknown',
        'attribution': 'Unknown.',
        'status': 'approved',
    }])
    with pytest.raises(ValueError, match='license'):
        rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))


def test_missing_gifs_are_rejected(tmp_path):
    repo = _repo_setup(tmp_path, entries=[{
        'id': 'prod-missing',
        'title': 'Missing GIF',
        'collection': 'test-assets',
        'category': 'internet-culture',
        'year': 2024,
        'asset_path': 'assets/archive/internet-culture/missing.gif',
        'source_url': 'https://example.com/missing',
        'license': 'CC BY 4.0',
        'attribution': 'Example author, CC BY 4.0.',
        'status': 'approved',
    }])
    missing_path = repo / 'assets' / 'archive' / 'internet-culture' / 'missing.gif'
    if missing_path.exists():
        missing_path.unlink()
    with pytest.raises(ValueError, match='missing|does not exist'):
        rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))


def test_invalid_manifest_data_errors_usefully(tmp_path):
    repo = tmp_path / 'repo'
    (repo / 'assets' / 'archive' / 'internet-culture').mkdir(parents=True)
    (repo / 'data').mkdir(parents=True)
    (repo / 'data' / 'manifest.json').write_text('{"entries": "not-a-list"}', encoding='utf-8')
    with pytest.raises(ValueError, match='entries'):
        rotate_daily.load_manifest(repo / 'data' / 'manifest.json')


def test_asset_paths_cannot_escape_repo(tmp_path):
    repo = _repo_setup(tmp_path, entries=[{
        'id': 'prod-001',
        'title': 'Escape',
        'collection': 'test-assets',
        'category': 'internet-culture',
        'year': 2024,
        'asset_path': '../outside.gif',
        'source_url': 'https://example.com/escape',
        'license': 'CC BY 4.0',
        'attribution': 'Someone, CC BY 4.0.',
        'status': 'approved',
    }])
    with pytest.raises(ValueError, match='inside the repository'):
        rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))


def test_same_date_selects_same_entry(tmp_path):
    repo = _repo_setup(tmp_path)
    first = rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))
    second = rotate_daily.select_entry(repo, mode='production', utc_date=date(2026, 1, 1))
    assert first['id'] == second['id']


def test_run_rotation_generates_daily_files(tmp_path):
    repo = _repo_setup(tmp_path)
    metadata = rotate_daily.run_rotation(repo, mode='production', utc_date=date(2026, 1, 1))
    assert (repo / 'assets' / 'daily.gif').exists()
    assert (repo / 'data' / 'current.json').exists()
    assert metadata['id'] in {'prod-001', 'prod-002'}
    assert metadata['date'] == '2026-01-01'
