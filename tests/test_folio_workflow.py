import sqlite3
import pandas as pd


def sample_movements():
    return pd.DataFrame([
        {
            'MOVIMIENTO_ID':'m1','FINCA_ID':'4-10-1-200103','EXPEDIENTE_ID':'200103',
            'PROVINCIA':'4','NUMERO':'200103','DERECHO':'1','FOLIO_REAL':'4-200103-001',
            'TIPO_DERECHO':'USUFRUCTO','NUM_PLANO_NORM':'400000012026','OPERACION':'HIPOTECA'
        },
        {
            'MOVIMIENTO_ID':'m2','FINCA_ID':'4-10-1-200103','EXPEDIENTE_ID':'200103',
            'PROVINCIA':'4','NUMERO':'200103','DERECHO':'1','FOLIO_REAL':'4-200103-001',
            'TIPO_DERECHO':'USUFRUCTO','NUM_PLANO_NORM':'400000012026','OPERACION':'GRAVAMEN'
        },
        {
            'MOVIMIENTO_ID':'m3','FINCA_ID':'4-10-1-200103','EXPEDIENTE_ID':'200103',
            'PROVINCIA':'4','NUMERO':'200103','DERECHO':'2','FOLIO_REAL':'4-200103-002',
            'TIPO_DERECHO':'NUDA PROPIEDAD','NUM_PLANO_NORM':'400000012026','OPERACION':'COMPRAVENTA'
        },
    ])


def test_build_folio_real_uses_only_province_finca_and_three_digit_right():
    from src.senda import build_folio_real
    assert build_folio_real('4', '200103', '1') == '4-200103-001'
    assert build_folio_real('4', '200103', '0') == '4-200103-000'
    assert build_folio_real('4', '200103', '12') == '4-200103-012'
    assert build_folio_real('4', '200103', '') == ''


def test_enrich_fincas_exposes_real_folio_and_right_type():
    from src.senda import enrich_fincas
    df = pd.DataFrame([{
        'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'1',
        'COD_DERECHO':'U','NUMERO_IDENT':'1-1111-1111','NOMBRE':'ANA','APELLIDO_1':'LOPEZ',
        'APELLIDO_2':'MORA','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'400000012026'
    }])
    row = enrich_fincas(df).iloc[0]
    assert row['FOLIO_REAL'] == '4-200103-001'
    assert row['TIPO_DERECHO'] == 'USUFRUCTO'


def test_consolidate_movements_distinguishes_rights_of_same_finca():
    from src.senda import consolidate_movements
    fincas = pd.DataFrame([
        {'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'1','COD_DERECHO':'U','NUMERO_IDENT':'1','NOMBRE':'A','APELLIDO_1':'','APELLIDO_2':'','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'111'},
        {'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'2','COD_DERECHO':'N','NUMERO_IDENT':'2','NOMBRE':'B','APELLIDO_1':'','APELLIDO_2':'','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'111'},
    ])
    hist = pd.DataFrame([
        {'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'1','FECHA_PROCESO':'2020-01-01','CODIGO_COMPLETO':'IA2','OPERACION':'HIPOTECA','CATEGORIA':'GRAVAMEN / AFECTACION'},
        {'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'2','FECHA_PROCESO':'2020-02-01','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'},
    ])
    out = consolidate_movements({'Fincas':fincas,'Historicos':hist}, anio='2026', trimestre='T1')
    assert out['FOLIO_REAL'].tolist() == ['4-200103-001','4-200103-002']
    assert out['TIPO_DERECHO'].tolist() == ['USUFRUCTO','NUDA PROPIEDAD']


def test_select_folio_records_never_includes_sibling_right():
    from src.senda import select_folio_records
    out = select_folio_records(sample_movements(), folio_real='4-200103-001')
    assert out['MOVIMIENTO_ID'].tolist() == ['m1','m2']


def test_finalize_folio_moves_only_selected_real_folio(tmp_path):
    from src.database import finalize_folio, list_registered
    db = tmp_path / 'x.db'
    count = finalize_folio(db, sample_movements(), folio_real='4-200103-001', usuario='Ana', finalizado_en='2026-08-24T08:00:00-06:00')
    assert count == 2
    reg = list_registered(db)
    assert set(reg['MOVIMIENTO_ID']) == {'m1','m2'}
    assert set(reg['FOLIO_REAL']) == {'4-200103-001'}
    assert set(reg['TIPO_DERECHO']) == {'USUFRUCTO'}


def test_save_control_folio_persists_one_real_folio_without_sibling(tmp_path):
    from src.database import save_control_folio, list_saved_folios
    db = tmp_path / 'x.db'
    count = save_control_folio(db, sample_movements(), folio_real='4-200103-001', usuario='Ana', guardado_en='2026-08-24T08:05:00-06:00')
    assert count == 2
    saved = list_saved_folios(db)
    assert saved['FOLIO_REAL'].tolist() == ['4-200103-001']
    assert saved.iloc[0]['TIPO_DERECHO'] == 'USUFRUCTO'
    assert int(saved.iloc[0]['MOVIMIENTOS']) == 2


def test_delete_folio_removes_only_selected_folio_from_operational_tables(tmp_path):
    from src.database import init_db, save_movements, finalize_folio, save_control_folio, delete_folio, list_registered, list_saved_folios
    db = tmp_path / 'x.db'
    init_db(db)
    rows = sample_movements()
    save_movements(db, rows, lote_id='T1')
    save_control_folio(db, rows, folio_real='4-200103-001', usuario='Ana')
    finalize_folio(db, rows, folio_real='4-200103-001', usuario='Ana')

    deleted = delete_folio(db, folio_real='4-200103-001', usuario='Admin', observacion='Corrección')
    assert deleted['movimientos'] == 2
    assert list_registered(db).empty
    assert list_saved_folios(db).empty
    with sqlite3.connect(db) as con:
        remaining = pd.read_sql_query('SELECT MOVIMIENTO_ID,FOLIO_REAL FROM movimientos ORDER BY MOVIMIENTO_ID', con)
    assert remaining.to_dict('records') == [{'MOVIMIENTO_ID':'m3','FOLIO_REAL':'4-200103-002'}]


def test_app_ui_operates_on_folio_real_not_whole_finca():
    from pathlib import Path
    src = (Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8')
    assert 'finalize_folio(' in src
    assert 'finalize_finca(' not in src
    assert 'save_control_folio(' in src
    assert 'delete_folio(' in src
    assert 'FOLIO_REAL' in src
    assert 'Tipo de derecho' in src
    assert 'GUARDAR FOLIO' in src
    assert 'ELIMINAR FOLIO' in src
    assert 'FINALIZADO' in src


def test_existing_database_rows_are_backfilled_to_real_folio_and_right_type(tmp_path):
    from src.database import init_db, load_movements
    db = tmp_path / 'old.db'
    init_db(db)
    with sqlite3.connect(db) as con:
        con.execute('''
            INSERT INTO movimientos (
                MOVIMIENTO_ID,FINCA_ID,EXPEDIENTE_ID,DERECHO,FOLIO_REAL,TIPO_DERECHO
            ) VALUES (?,?,?,?,?,?)
        ''', ('old1','4-10-1-200103','200103','1','',''))
        con.execute('''
            CREATE TABLE fincas_folios (
                FINCA_ID TEXT, PROVINCIA TEXT, NUMERO TEXT, DERECHO TEXT, COD_DERECHO TEXT,
                ANIO TEXT, TRIMESTRE TEXT, LOTE_ID TEXT
            )
        ''')
        con.execute('INSERT INTO fincas_folios VALUES (?,?,?,?,?,?,?,?)', ('4-10-1-200103','4','200103','1','U','2026','T1','x'))
        con.commit()
    init_db(db)
    row = load_movements(db).iloc[0]
    assert row['FOLIO_REAL'] == '4-200103-001'
    assert row['TIPO_DERECHO'] == 'USUFRUCTO'


def test_unknown_sibling_right_never_inherits_wrong_right_type():
    from src.senda import consolidate_movements
    fincas = pd.DataFrame([{
        'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'1','COD_DERECHO':'U',
        'NUMERO_IDENT':'1','NOMBRE':'A','APELLIDO_1':'','APELLIDO_2':'','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'111'
    }])
    hist = pd.DataFrame([{
        'FINCA_ID':'4-10-1-200103','PROVINCIA':'4','NUMERO':'200103','DERECHO':'2',
        'FECHA_PROCESO':'2020-01-01','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'
    }])
    row = consolidate_movements({'Fincas':fincas,'Historicos':hist}).iloc[0]
    assert row['FOLIO_REAL'] == '4-200103-002'
    assert row['TIPO_DERECHO'] == ''
