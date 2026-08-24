from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'app.py'
HTML = ROOT / 'SENDA_VISTA_SINCRONIZADA.html'


def test_release_has_shared_visible_version_and_html():
    app = APP.read_text(encoding='utf-8')
    assert 'RELEASE_ID = "SENDA-2026.08.24-R3"' in app
    assert HTML.exists()
    html = HTML.read_text(encoding='utf-8')
    assert 'SENDA-2026.08.24-R3' in html


def test_visible_ui_uses_only_folio_finca_and_required_actions():
    app = APP.read_text(encoding='utf-8')
    html = HTML.read_text(encoding='utf-8') if HTML.exists() else ''
    for src in (app, html):
        assert 'FOLIO / FINCA' in src
        assert 'GUARDAR FOLIO' in src
        assert 'ELIMINAR FOLIO' in src
        assert 'FINALIZADO' in src
    assert 'Expediente ' not in app
    assert 'EXP-2026-' not in app
    assert 'EXP-2026-' not in html


def test_alarmas_codigos_are_side_by_side_accordions_and_folio_alert_is_visible():
    app = APP.read_text(encoding='utf-8')
    assert '🚨 ALARMAS' in app
    assert '🏷️ CÓDIGOS' in app
    assert 'alerta_folio' in app
    html = HTML.read_text(encoding='utf-8') if HTML.exists() else ''
    assert '🚨 ALARMAS' in html
    assert '🏷️ CÓDIGOS' in html
    assert 'alert-folio' in html


def test_selected_icon_is_part_of_release():
    app = APP.read_text(encoding='utf-8')
    assert 'app_icon_propuesta2.png' in app
    assert (ROOT / 'assets' / 'app_icon_propuesta2.png').exists()
    html = HTML.read_text(encoding='utf-8') if HTML.exists() else ''
    assert 'app-icon-propuesta2' in html
