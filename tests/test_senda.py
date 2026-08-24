import pandas as pd
from datetime import date

from src.senda import (
    paginate_records, inactivity_level, movement_type,
    enrich_fincas, consolidate_movements, filter_records,
)


def test_paginate_records_first_page_25_then_20():
    df = pd.DataFrame({'x': range(70)})
    p1, pages = paginate_records(df, 1)
    p2, _ = paginate_records(df, 2)
    p3, _ = paginate_records(df, 3)
    assert len(p1) == 25
    assert p1['x'].tolist() == list(range(25))
    assert len(p2) == 20
    assert p2['x'].tolist() == list(range(25, 45))
    assert len(p3) == 20
    assert pages == 4


def test_inactivity_level_thresholds():
    today = date(2026, 8, 23)
    assert inactivity_level('2026-07-01', today) == 'SIN ALERTA'
    assert inactivity_level('2026-06-20', today) == 'AMARILLO'
    assert inactivity_level('2026-05-23', today) == 'ROJO'
    assert inactivity_level('', today) == 'SIN FECHA'


def test_movement_type_distinguishes_key_groups():
    assert movement_type('HIPOTECA') == 'HIPOTECA'
    assert movement_type('CANCELACION DE HIPOTECA') == 'HIPOTECA'
    assert movement_type('SEGREGACION DE LOTE') == 'SEGREGACION'
    assert movement_type('SERVIDUMBRE') == 'GRAVAMEN'
    assert movement_type('DECRETO DE EMBARGO') == 'GRAVAMEN'


def test_enrich_fincas_builds_person_search_fields_and_expediente():
    df = pd.DataFrame([{
        'FINCA_ID': '4-10-2-280735', 'NUMERO': '280735', 'DERECHO': '1',
        'NUMERO_IDENT': '1-1234-5678', 'NOMBRE': 'MARIA', 'APELLIDO_1': 'ROJAS',
        'APELLIDO_2': 'SOLANO', 'NOMBRE_JURIDICO': '', 'NUM_PLANO_NORM': '400617672025'
    }])
    out = enrich_fincas(df)
    row = out.iloc[0]
    assert row['EXPEDIENTE_ID'] == '280735'
    assert row['CEDULA_NORM'] == '112345678'
    assert row['TITULAR'] == 'MARIA ROJAS SOLANO'
    assert row['NOMBRE_BUSQUEDA'] == 'MARIA ROJAS SOLANO'


def test_filter_records_keeps_all_same_name_matches_and_filters_cedula():
    df = pd.DataFrame([
        {'CEDULA_NORM':'112345678','NOMBRE_BUSQUEDA':'ANA LOPEZ MORA','FINCA_ID':'4-10-1-1','DERECHO':'1','CODIGO_COMPLETO':'IA2','OPERACION':'HIPOTECA'},
        {'CEDULA_NORM':'223456789','NOMBRE_BUSQUEDA':'ANA LOPEZ VEGA','FINCA_ID':'4-10-1-2','DERECHO':'1','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA'},
        {'CEDULA_NORM':'334567890','NOMBRE_BUSQUEDA':'PEDRO RUIZ LOPEZ','FINCA_ID':'4-10-1-3','DERECHO':'2','CODIGO_COMPLETO':'PG1','OPERACION':'DONACION'},
    ])
    same_name = filter_records(df, nombre='ANA')
    assert same_name['FINCA_ID'].tolist() == ['4-10-1-1','4-10-1-2']
    same_surname = filter_records(df, apellido='LOPEZ')
    assert len(same_surname) == 3
    by_id = filter_records(df, cedula='1-1234-5678')
    assert by_id['FINCA_ID'].tolist() == ['4-10-1-1']


def test_consolidate_movements_enriches_owner_and_orders_oldest_first():
    fincas = pd.DataFrame([{
        'FINCA_ID':'4-10-2-280735','NUMERO':'280735','DERECHO':'1','NUMERO_IDENT':'1-1234-5678',
        'NOMBRE':'MARIA','APELLIDO_1':'ROJAS','APELLIDO_2':'SOLANO','NOMBRE_JURIDICO':'',
        'NUM_PLANO_NORM':'400617672025','OPERACION':'COMPRAVENTA','COD_OPERACION':'PE1',
        'FECHA_ULT_ACT':'2026-06-01'
    }])
    historicos = pd.DataFrame([
        {'FINCA_ID':'4-10-2-280735','NUMERO':'280735','DERECHO':'1','FECHA_PROCESO':'2020-01-02','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'},
        {'FINCA_ID':'4-10-2-280735','NUMERO':'280735','DERECHO':'1','FECHA_PROCESO':'2019-01-02','CODIGO_COMPLETO':'IA2','OPERACION':'HIPOTECA','CATEGORIA':'GRAVAMEN / AFECTACION'},
    ])
    out = consolidate_movements({'Fincas': fincas, 'Historicos': historicos}, anio='2026', trimestre='T2')
    assert out['FECHA_MOVIMIENTO'].tolist()[:2] == ['2019-01-02','2020-01-02']
    assert out.iloc[0]['EXPEDIENTE_ID'] == '280735'
    assert out.iloc[0]['CEDULA_NORM'] == '112345678'
    assert out.iloc[0]['TITULAR'] == 'MARIA ROJAS SOLANO'
    assert out.iloc[0]['TIPO_MOVIMIENTO'] == 'HIPOTECA'
    assert out.iloc[0]['ANIO'] == '2026'
    assert out.iloc[0]['TRIMESTRE'] == 'T2'

def test_consolidate_movements_keeps_multiple_owners_searchable():
    fincas = pd.DataFrame([
        {'FINCA_ID':'4-10-2-99','NUMERO':'99','DERECHO':'1','NUMERO_IDENT':'1-1111-1111','NOMBRE':'ANA','APELLIDO_1':'LOPEZ','APELLIDO_2':'MORA','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'123'},
        {'FINCA_ID':'4-10-2-99','NUMERO':'99','DERECHO':'1','NUMERO_IDENT':'2-2222-2222','NOMBRE':'ANA','APELLIDO_1':'LOPEZ','APELLIDO_2':'VEGA','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'123'},
    ])
    hist = pd.DataFrame([{'FINCA_ID':'4-10-2-99','NUMERO':'99','DERECHO':'1','FECHA_PROCESO':'2020-01-01','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'}])
    out = consolidate_movements({'Fincas':fincas,'Historicos':hist}, anio='2026', trimestre='T2')
    row = out.iloc[0]
    assert '111111111' in row['CEDULA_NORM']
    assert '222222222' in row['CEDULA_NORM']
    assert 'ANA LOPEZ MORA' in row['TITULAR']
    assert 'ANA LOPEZ VEGA' in row['TITULAR']
    assert len(filter_records(out, cedula='2-2222-2222')) == 1
    assert len(filter_records(out, apellido='VEGA')) == 1

def test_filter_records_finca_or_expediente_accepts_full_or_number():
    df = pd.DataFrame([
        {'FINCA_ID':'4-10-2-280735','EXPEDIENTE_ID':'280735','CEDULA_NORM':'','NOMBRE_BUSQUEDA':'','DERECHO':'1','NUM_PLANO_NORM':'','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA'},
        {'FINCA_ID':'4-10-2-999','EXPEDIENTE_ID':'999','CEDULA_NORM':'','NOMBRE_BUSQUEDA':'','DERECHO':'1','NUM_PLANO_NORM':'','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA'},
    ])
    assert len(filter_records(df, finca_o_expediente='4-10-2-280735')) == 1
    assert len(filter_records(df, finca_o_expediente='280735')) == 1

def test_build_analysis_tables_matches_excel_logical_sections():
    from src.senda import build_analysis_tables
    fincas = pd.DataFrame([
        {'FINCA_ID':'4-10-1-1','NUMERO':'1','DERECHO':'1','NUM_PLANO_NORM':'111'},
        {'FINCA_ID':'4-10-1-2','NUMERO':'2','DERECHO':'1','NUM_PLANO_NORM':''},
    ])
    cerradas = pd.DataFrame([{'FINCA_ID':'4-10-1-9','NUMERO':'9','NUM_PLANO_NORM':'111'}])
    seg = pd.DataFrame([{'FINCA_ID':'4-10-1-3','NUMERO':'3','NUM_PLANO_NORM':'333','DESCRIP_OPER':'SEGREGACION'}])
    mov = pd.DataFrame([
        {'FUENTE':'Historicos','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','FECHA_MOVIMIENTO':'2026-01-01','EXPEDIENTE_ID':'1'},
        {'FUENTE':'Historicos','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','FECHA_MOVIMIENTO':'2026-01-02','EXPEDIENTE_ID':'2'},
    ])
    tables = build_analysis_tables({'Fincas':fincas,'Cerradas':cerradas,'Segregaciones':seg}, mov, {('PE','1'):'COMPRAVENTA'})
    assert {'Resumen','Planos Control','Alertas','Top Operaciones','Catalogo Operaciones','Manual Codigos'} <= set(tables)
    assert (tables['Planos Control']['TIPO_CONTROL'] == 'FINCA ACTIVA SIN PLANO').any()
    assert (tables['Planos Control']['TIPO_CONTROL'] == 'PLANO DE SEGREGACION SIN FINCA').any()
    assert (tables['Planos Control']['TIPO_CONTROL'] == 'PLANO EN MAS DE UNA MATRICULA').any()
    top = tables['Top Operaciones'].iloc[0]
    assert top['CODIGO'] == 'PE1' and int(top['CANTIDAD']) == 2

def test_consolidate_movements_preserves_duplicate_looking_source_rows_with_unique_ids():
    fincas = pd.DataFrame([{'FINCA_ID':'4-10-1-1','NUMERO':'1','DERECHO':'1','NUMERO_IDENT':'1','NOMBRE':'A','APELLIDO_1':'B','APELLIDO_2':'C','NOMBRE_JURIDICO':'','NUM_PLANO_NORM':'1'}])
    hist = pd.DataFrame([
        {'FINCA_ID':'4-10-1-1','NUMERO':'1','DERECHO':'1','FECHA_PROCESO':'2020-01-01','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'},
        {'FINCA_ID':'4-10-1-1','NUMERO':'1','DERECHO':'1','FECHA_PROCESO':'2020-01-01','CODIGO_COMPLETO':'PE1','OPERACION':'COMPRAVENTA','CATEGORIA':'TRASPASO / TITULARIDAD'},
    ])
    out = consolidate_movements({'Fincas':fincas,'Historicos':hist}, anio='2026', trimestre='T2')
    assert len(out) == 2
    assert out['MOVIMIENTO_ID'].nunique() == 2
    assert out['SOURCE_ROW'].tolist() == ['0','1']


def test_real_record_label_uses_registry_folio_and_never_internal_movement_id():
    from src.senda import real_record_label
    row = {
        'PROVINCIA': '4',
        'NUMERO': '280735',
        'EXPEDIENTE_ID': '280735',
        'FINCA_ID': '4-10-2-280735',
        'DERECHO': '3',
        'FOLIO_REAL': '4-280735-003',
        'TIPO_DERECHO': 'USUFRUCTO',
        'NUM_PLANO_NORM': '400617672025',
        'MOVIMIENTO_ID': 'abc123internal',
    }
    label = real_record_label(row)
    assert label == 'FOLIO / FINCA 4-280735-003 | USUFRUCTO | Plano 400617672025'
    assert 'abc123internal' not in label
    assert 'Expediente' not in label


def test_select_finca_records_selects_all_rows_for_real_finca():
    from src.senda import select_finca_records
    df = pd.DataFrame([
        {'FINCA_ID':'4-10-2-280735','EXPEDIENTE_ID':'280735','DERECHO':'1','MOVIMIENTO_ID':'a'},
        {'FINCA_ID':'4-10-2-280735','EXPEDIENTE_ID':'280735','DERECHO':'1','MOVIMIENTO_ID':'b'},
        {'FINCA_ID':'4-10-2-280735','EXPEDIENTE_ID':'280735','DERECHO':'2','MOVIMIENTO_ID':'c'},
        {'FINCA_ID':'4-10-2-999','EXPEDIENTE_ID':'999','DERECHO':'1','MOVIMIENTO_ID':'d'},
    ])
    out = select_finca_records(df, finca_id='4-10-2-280735')
    assert out['MOVIMIENTO_ID'].tolist() == ['a','b','c']


def test_filter_records_filters_movement_month_without_changing_year_or_quarter_filters():
    df = pd.DataFrame([
        {'FECHA_MOVIMIENTO':'2026-01-05','ANIO':'2026','TRIMESTRE':'T1','FINCA_ID':'4-10-1-1'},
        {'FECHA_MOVIMIENTO':'2026-02-10','ANIO':'2026','TRIMESTRE':'T1','FINCA_ID':'4-10-1-2'},
        {'FECHA_MOVIMIENTO':'2025-02-15','ANIO':'2025','TRIMESTRE':'T1','FINCA_ID':'4-10-1-3'},
        {'FECHA_MOVIMIENTO':'','ANIO':'2026','TRIMESTRE':'T1','FINCA_ID':'4-10-1-4'},
    ])
    feb = filter_records(df, mes='02')
    assert feb['FINCA_ID'].tolist() == ['4-10-1-2','4-10-1-3']
    feb_2026 = filter_records(df, mes='02', anio='2026', trimestre='T1')
    assert feb_2026['FINCA_ID'].tolist() == ['4-10-1-2']


def test_filter_month_column_filters_registration_month():
    from src.senda import filter_month_column
    df = pd.DataFrame([
        {'REGISTRADO_EN':'2026-07-31T10:00:00-06:00','MOVIMIENTO_ID':'a'},
        {'REGISTRADO_EN':'2026-08-01T11:00:00-06:00','MOVIMIENTO_ID':'b'},
        {'REGISTRADO_EN':'2025-08-03T09:00:00-06:00','MOVIMIENTO_ID':'c'},
        {'REGISTRADO_EN':'','MOVIMIENTO_ID':'d'},
    ])
    out = filter_month_column(df, 'REGISTRADO_EN', '08')
    assert out['MOVIMIENTO_ID'].tolist() == ['b','c']
