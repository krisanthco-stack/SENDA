import io
import json
import zipfile

from src.io_tools import MemoryUpload, expand_uploads, records_to_json_bytes, records_to_excel_bytes, read_management_import


def test_expand_uploads_extracts_supported_files_from_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('Fincas_SARAPIQUI_T1.xls', 'A\tB\n1\t2\n')
        z.writestr('docs/nota.pdf', b'no')
        z.writestr('CATALOGO_COD_OPERACIONES.TXT', '"PE";1;"COMPRAVENTA"')
    upload = MemoryUpload('T1_2026.zip', buf.getvalue())
    files = expand_uploads([upload])
    assert [f.name for f in files] == ['Fincas_SARAPIQUI_T1.xls', 'CATALOGO_COD_OPERACIONES.TXT']
    assert files[0].getvalue().startswith(b'A\tB')


def test_json_roundtrip_management_records():
    records = [{'MOVIMIENTO_ID':'m1','FINCA_ID':'4-10-1-1','REGISTRADO_POR':'Ana'}]
    payload = records_to_json_bytes(records)
    parsed = read_management_import(MemoryUpload('gestion.json', payload))
    assert parsed == records


def test_excel_roundtrip_management_records():
    records = [{'MOVIMIENTO_ID':'m1','FINCA_ID':'4-10-1-1','REGISTRADO_POR':'Ana'}]
    payload = records_to_excel_bytes(records)
    parsed = read_management_import(MemoryUpload('gestion.xlsx', payload))
    assert parsed[0]['MOVIMIENTO_ID'] == 'm1'
    assert parsed[0]['FINCA_ID'] == '4-10-1-1'
    assert parsed[0]['REGISTRADO_POR'] == 'Ana'

def test_database_to_excel_bytes_exports_organized_sheets(tmp_path):
    import sqlite3
    import pandas as pd
    from src.io_tools import database_to_excel_bytes
    db = tmp_path / 'registro.db'
    with sqlite3.connect(db) as con:
        pd.DataFrame([{'FINCA_ID':'4-10-1-1'}]).to_sql('fincas_folios', con, index=False)
        pd.DataFrame([{'INDICADOR':'Fincas','VALOR':'1'}]).to_sql('resumen', con, index=False)
    payload = database_to_excel_bytes(db)
    book = pd.ExcelFile(io.BytesIO(payload))
    assert 'Fincas_Folios' in book.sheet_names
    assert 'Resumen' in book.sheet_names
