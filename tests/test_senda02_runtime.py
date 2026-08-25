from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_pwa_files_exist():
    for p in ['manifest.webmanifest','sw.js','.github/workflows/pages.yml','.nojekyll']:
        assert (ROOT/p).exists(), p

def test_service_worker_isolated_cache():
    p=ROOT/'sw.js'
    if not p.exists():
        raise AssertionError('sw.js missing')
    t=p.read_text(encoding='utf-8')
    assert 'senda02' in t.lower()
    assert 'senda-r6' not in t.lower()

def test_data_asset_exists():
    assert (ROOT/'data/registro_inmobiliario_base.sqlite').exists()
