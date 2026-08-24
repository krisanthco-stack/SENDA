from pathlib import Path


def app_source():
    return (Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8')


def test_control_uses_exact_real_folio_and_right_type_without_invented_numbering():
    src = app_source()
    assert 'FOLIO / FINCA' in src
    assert 'Abrir FOLIO / FINCA' in src
    assert 'Tipo de derecho' in src
    assert 'FOLIO_REAL' in src
    assert 'EXP-2026-' not in src


def test_control_has_same_visual_quick_actions_and_month_filter():
    src = app_source()
    for label in ['Hipotecas', 'Gravámenes', 'Segregaciones', 'Anotaciones', 'Aplicar', 'Limpiar']:
        assert f'button("{label}"' in src
    assert 'Mes del movimiento' in src


def test_control_finalizado_moves_only_selected_real_folio_to_gestion():
    src = app_source()
    assert 'button("FINALIZADO"' in src
    assert 'finalize_folio(' in src
    assert 'finalize_finca(' not in src
    assert 'GUARDAR FOLIO' in src
    assert 'ELIMINAR FOLIO' in src


def test_control_warns_when_source_has_no_right_instead_of_inventing_one():
    src = app_source()
    assert 'sin folio real identificable' in src
    assert 'No se inventa un Derecho' in src


def test_ui_uses_single_folio_finca_identifier_without_split_finca_or_derecho_labels():
    src = app_source()
    assert 'FOLIO / FINCA' in src
    assert 'Número de finca' not in src
    assert 'text_input("Derecho"' not in src
    assert 'st.subheader(f"FOLIO / FINCA {selected_folio}")' in src
    assert '**Finca:**' not in src
    assert '**Derecho:**' not in src


def test_information_senda_detail_does_not_split_folio_finca_into_number_and_right():
    src = app_source()
    assert '"Folio / Finca": row.get("FOLIO_REAL", "")' in src
    assert '"Número de finca":' not in src
    assert '"Derecho": str(row.get("DERECHO"' not in src


def test_gestion_primary_identifier_is_folio_finca_not_split_columns():
    src = app_source()
    assert '"FOLIO_REAL": "FOLIO / FINCA"' in src
    assert '"NUMERO": "FINCA"' not in src
    assert '"DERECHO": "DERECHO"' not in src
