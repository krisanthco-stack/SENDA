from pathlib import Path
import pandas as pd

from src.database import (
    init_db, save_movements, mark_registered, registered_ids,
    list_registered, audit_history, import_registered_records, save_dataset,
)


def movement(mid='m1'):
    return {
        'MOVIMIENTO_ID': mid,
        'EXPEDIENTE_ID': '280735',
        'FINCA_ID': '4-10-2-280735',
        'DERECHO': '1',
        'CEDULA_NORM': '112345678',
        'TITULAR': 'MARIA ROJAS SOLANO',
        'CODIGO_COMPLETO': 'IA2',
        'OPERACION': 'HIPOTECA',
        'CATEGORIA': 'GRAVAMEN / AFECTACION',
        'TIPO_MOVIMIENTO': 'HIPOTECA',
        'FUENTE': 'Historicos',
        'FECHA_MOVIMIENTO': '2020-01-01',
        'ANIO': '2026',
        'TRIMESTRE': 'T2',
    }


def test_mark_registered_persists_operator_timestamp_and_audit(tmp_path):
    db = tmp_path / 'registro.db'
    init_db(db)
    save_movements(db, pd.DataFrame([movement()]))
    mark_registered(db, movement(), usuario='Ana Operadora', observacion='Inscrito', registrado_en='2026-08-23T17:14:00-06:00')
    assert registered_ids(db) == {'m1'}
    rows = list_registered(db)
    assert rows.iloc[0]['REGISTRADO_POR'] == 'Ana Operadora'
    assert rows.iloc[0]['REGISTRADO_EN'] == '2026-08-23T17:14:00-06:00'
    assert rows.iloc[0]['OBSERVACION_REGISTRO'] == 'Inscrito'
    hist = audit_history(db, movimiento_id='m1')
    assert hist.iloc[0]['ACCION'] == 'REGISTRADO'
    assert hist.iloc[0]['USUARIO'] == 'Ana Operadora'


def test_mark_registered_is_idempotent_for_same_movement(tmp_path):
    db = tmp_path / 'registro.db'
    init_db(db)
    mark_registered(db, movement(), usuario='Ana', observacion='uno', registrado_en='2026-08-23T17:14:00-06:00')
    mark_registered(db, movement(), usuario='Otra', observacion='dos', registrado_en='2026-08-24T10:00:00-06:00')
    rows = list_registered(db)
    assert len(rows) == 1
    assert rows.iloc[0]['REGISTRADO_POR'] == 'Ana'
    assert len(audit_history(db, movimiento_id='m1')) == 1


def test_import_registered_records_avoids_duplicates(tmp_path):
    db = tmp_path / 'registro.db'
    init_db(db)
    rec = movement('m-import') | {
        'REGISTRADO_POR':'Luis',
        'REGISTRADO_EN':'2026-08-20T09:00:00-06:00',
        'OBSERVACION_REGISTRO':'importado'
    }
    assert import_registered_records(db, [rec], usuario_importacion='Admin') == 1
    assert import_registered_records(db, [rec], usuario_importacion='Admin') == 0
    rows = list_registered(db)
    assert len(rows) == 1
    assert rows.iloc[0]['REGISTRADO_POR'] == 'Luis'


def test_save_dataset_keeps_quarter_metadata_and_replaces_same_batch(tmp_path):
    db = tmp_path / 'registro.db'
    init_db(db)
    df = pd.DataFrame([{'FINCA_ID':'4-10-1-1','NUMERO':'1'}])
    save_dataset(db, 'Fincas', df, anio='2026', trimestre='T1', lote_id='lote-1')
    save_dataset(db, 'Fincas', df, anio='2026', trimestre='T1', lote_id='lote-1')
    import sqlite3
    with sqlite3.connect(db) as con:
        rows = pd.read_sql_query('SELECT * FROM fincas_folios', con)
    assert len(rows) == 1
    assert rows.iloc[0]['ANIO'] == '2026'
    assert rows.iloc[0]['TRIMESTRE'] == 'T1'
    assert rows.iloc[0]['LOTE_ID'] == 'lote-1'

def test_load_movements_returns_oldest_first_and_can_filter_period(tmp_path):
    from src.database import load_movements
    db = tmp_path / 'registro.db'
    init_db(db)
    rows = pd.DataFrame([
        movement('m2') | {'FECHA_MOVIMIENTO':'2021-01-01','ANIO':'2026','TRIMESTRE':'T2'},
        movement('m1') | {'FECHA_MOVIMIENTO':'2020-01-01','ANIO':'2026','TRIMESTRE':'T2'},
        movement('m3') | {'FECHA_MOVIMIENTO':'2019-01-01','ANIO':'2025','TRIMESTRE':'T4'},
    ])
    save_movements(db, rows)
    out = load_movements(db, anio='2026', trimestre='T2')
    assert out['MOVIMIENTO_ID'].tolist() == ['m1','m2']

def test_load_dataset_returns_saved_quarter(tmp_path):
    from src.database import load_dataset
    db = tmp_path / 'registro.db'
    init_db(db)
    save_dataset(db, 'Fincas', pd.DataFrame([{'FINCA_ID':'4-10-1-1','NUMERO':'1'}]), anio='2026', trimestre='T1', lote_id='a')
    save_dataset(db, 'Fincas', pd.DataFrame([{'FINCA_ID':'4-10-1-2','NUMERO':'2'}]), anio='2026', trimestre='T2', lote_id='b')
    out = load_dataset(db, 'Fincas', anio='2026', trimestre='T2')
    assert out['FINCA_ID'].tolist() == ['4-10-1-2']


def test_finalize_finca_moves_all_pending_movements_to_gestion_and_audits(tmp_path):
    from src.database import finalize_finca
    db = tmp_path / 'registro.db'
    init_db(db)
    rows = pd.DataFrame([
        movement('m1') | {'FINCA_ID':'4-10-2-280735','DERECHO':'1','NUM_PLANO_NORM':'111'},
        movement('m2') | {'FINCA_ID':'4-10-2-280735','DERECHO':'1','NUM_PLANO_NORM':'222'},
        movement('m3') | {'FINCA_ID':'4-10-2-280735','DERECHO':'2','NUM_PLANO_NORM':'333'},
        movement('m4') | {'FINCA_ID':'4-10-2-999','DERECHO':'1','NUM_PLANO_NORM':'444'},
    ])
    save_movements(db, rows)
    count = finalize_finca(
        db, rows, finca_id='4-10-2-280735',
        usuario='Ana Operadora', observacion='Finca concluida',
        finalizado_en='2026-08-23T22:46:00-06:00'
    )
    assert count == 3
    reg = list_registered(db)
    assert set(reg['MOVIMIENTO_ID']) == {'m1','m2','m3'}
    assert set(reg['DERECHO']) == {'1','2'}
    assert set(reg['NUM_PLANO_NORM']) == {'111','222','333'}
    hist = audit_history(db)
    assert set(hist['ACCION']) == {'FINALIZADO'}
    assert set(hist['USUARIO']) == {'Ana Operadora'}


def test_finalize_finca_is_idempotent(tmp_path):
    from src.database import finalize_finca
    db = tmp_path / 'registro.db'
    init_db(db)
    rows = pd.DataFrame([movement('m1') | {'FINCA_ID':'4-10-2-280735','DERECHO':'1'}])
    save_movements(db, rows)
    first = finalize_finca(db, rows, finca_id='4-10-2-280735', usuario='Ana')
    second = finalize_finca(db, rows, finca_id='4-10-2-280735', usuario='Ana')
    assert first == 1
    assert second == 0
    assert len(list_registered(db)) == 1
    assert len(audit_history(db)) == 1
