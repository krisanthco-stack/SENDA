from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app.py'
HTML = ROOT / 'SENDA_VISTA_SINCRONIZADA.html'


def sources():
    return APP.read_text(encoding='utf-8'), HTML.read_text(encoding='utf-8')


def test_inicio_module_is_restored_without_removing_existing_modules():
    app, html = sources()
    assert '["INICIO", "INFORMACIÓN SENDA", "CONTROL", "GESTIÓN"]' in app
    assert 'data-sec="inicio">INICIO</button>' in html
    for label in ('INFORMACIÓN SENDA', 'CONTROL', 'GESTIÓN'):
        assert label in app
        assert label in html


def test_inicio_keeps_real_quarterly_upload_flow():
    app, html = sources()
    inicio_pos = app.index('if module == "INICIO":')
    info_pos = app.index('elif module == "INFORMACIÓN SENDA":')
    inicio_block = app[inicio_pos:info_pos]
    assert 'Cargar corte trimestral' in inicio_block
    assert 'Archivos o ZIP trimestral' in inicio_block
    assert 'Procesar y guardar carga' in inicio_block
    assert 'save_dataset(' in inicio_block
    assert 'save_movements(' in inicio_block
    assert '<section id="inicio"' in html
    assert 'Archivos o ZIP trimestral' in html
    assert 'Procesar y guardar carga' in html


def test_visible_identity_is_folio_finca_and_never_expediente_numbering():
    app, html = sources()
    for src in (app, html):
        assert 'FOLIO / FINCA' in src
        assert 'EXP-2026-' not in src
        assert '>Expediente<' not in src
        assert 'Expediente ' not in src


def test_visual_refresh_is_css_only_and_keeps_core_actions():
    app, html = sources()
    # visual tokens added without changing module order/functionality
    for token in ('--surface', '--border', '--shadow-soft', '.senda-card'):
        assert token in app
    for label in ('GUARDAR FOLIO', 'ELIMINAR FOLIO', 'FINALIZADO', 'Hipotecas', 'Gravámenes', 'Segregaciones', 'Anotaciones'):
        assert label in app
        assert label in html
    assert 'app_icon_propuesta2.png' in app
    assert 'app-icon-propuesta2' in html


def test_release_r3_is_shared_between_app_and_html():
    app, html = sources()
    assert 'RELEASE_ID = "SENDA-2026.08.24-R3"' in app
    assert 'SENDA-2026.08.24-R3' in html
