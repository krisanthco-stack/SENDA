import io
import pandas as pd

from src.registro import (
    decode_bytes, finca_id_df, split_operation, classify,
    normalize_dataset, planos_sin_finca,
)


def test_finca_id_preserves_existing_format():
    df = pd.DataFrame([{
        'PROVINCIA':'4','CANTON':'10','DISTRITO':'2','NUMERO':'280735','DUPLICADO':'','HORIZONTAL':''
    }])
    assert finca_id_df(df).iloc[0] == '4-10-2-280735'


def test_split_operation_and_historical_normalization_preserve_catalog_logic():
    opmap = {('PG','7'):'DONACION DE DERECHO', ('PE','1'):'COMPRAVENTA'}
    assert split_operation('PG7', opmap) == ('PG','7')
    df = pd.DataFrame([{
        'PROVINCIA':'4','CANTON':'10','DISTRITO':'2','NUMERO':'1','DUPLICADO':'','HORIZONTAL':'',
        'DERECHO':'1','COD_OPER':'PE','CLASE_CODIGO':'1','DESCRIP_OPER':'COMPRAVENTA'
    }])
    out = normalize_dataset('Historicos', df, opmap)
    assert out.iloc[0]['FINCA_ID'] == '4-10-2-1'
    assert out.iloc[0]['CODIGO_COMPLETO'] == 'PE1'
    assert out.iloc[0]['OPERACION'] == 'COMPRAVENTA'
    assert out.iloc[0]['CATEGORIA'] == 'TRASPASO / TITULARIDAD'


def test_planos_sin_finca_behavior_is_preserved():
    datasets = {
        'Fincas': pd.DataFrame([{'NUM_PLANO_NORM':'111'}]),
        'Cerradas': pd.DataFrame([{'NUM_PLANO_NORM':'222'}]),
        'Segregaciones': pd.DataFrame([
            {'NUM_PLANO_NORM':'111','FINCA_ID':'4-10-1-1'},
            {'NUM_PLANO_NORM':'333','FINCA_ID':'4-10-1-3'},
        ])
    }
    out = planos_sin_finca(datasets)
    assert len(out) == 1
    assert out.iloc[0]['NUM_PLANO'] == '333'
    assert out.iloc[0]['FINCA_REFERENCIADA'] == '4-10-1-3'


def test_existing_classification_still_recognizes_hipoteca_as_gravamen():
    assert classify('HIPOTECA') == 'GRAVAMEN / AFECTACION'
