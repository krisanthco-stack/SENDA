from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'index.html'

def txt():
    return HTML.read_text(encoding='utf-8') if HTML.exists() else ''

def test_index_exists():
    assert HTML.exists(), 'Falta index.html oficial de SENDA 02'

def test_identity_and_navigation():
    t=txt()
    assert 'SENDA 02' in t
    for x in ['INICIO','INFORMACIÓN SENDA','CONTROL','GESTIÓN']:
        assert x in t

def test_visual_blue_shell_and_kpis():
    t=txt()
    for x in ['--navy','kpi-strip','sidebar','workspace','INSTALAR SENDA','FOLIOS / FINCAS','PENDIENTES','EN REVISIÓN','FINALIZADOS','GESTIONES']:
        assert x in t

def test_no_legacy_visible_terms():
    t=txt()
    assert 'EXP-2026' not in t
    assert 'Número de finca' not in t
    assert '>Expediente<' not in t
    assert not re.search(r'4-\d+-000', t)

def test_senda_review_flow_present():
    t=txt()
    for x in ['SELECCIONAR EN CONTROL','DESELECCIONAR','FINALIZAR','selectedReviewFolio','finishReviewFolio','REGRESAR A INFORMACIÓN SENDA']:
        assert x in t

def test_control_exclusive_accordion_and_juridicas():
    t=txt()
    for x in ['controlSelectedFolio','control-accordion','CÉDULAS JURÍDICAS','DESELECCIONAR','GUARDAR FOLIO','ELIMINAR FOLIO','FINALIZAR']:
        assert x in t

def test_gestion_exports_and_audit():
    t=txt()
    for x in ['BASE GESTIÓN JSON','BASE GESTIÓN EXCEL','gestionBaseRows','tipo_gestion','auditoria']:
        assert x in t

def test_archive_and_install_support():
    t=txt()
    assert 'accept=".xls,.txt,.csv,.json,.zip,.rar"' in t
    assert 'installSenda' in t
    assert 'serviceWorker' in t
