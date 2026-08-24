from pathlib import Path
import base64
import hashlib
from datetime import date

import pandas as pd
import streamlit as st

from src.registro import (
    classify_filename, load_operation_catalog, normalize_dataset,
    planos_sin_finca, read_tabular_upload, classify,
)
from src.senda import (
    consolidate_movements, enrich_fincas, filter_records,
    inactivity_level, paginate_records, build_analysis_tables,
    real_record_label, select_finca_records, select_folio_records, filter_month_column,
)
from src.database import (
    audit_history, finalize_folio, import_registered_records, init_db, list_registered,
    load_dataset, load_movements, registered_ids, save_dataset, save_movements,
    save_control_folio, list_saved_folios, delete_folio,
)
from src.io_tools import (
    expand_uploads, read_management_import, records_to_excel_bytes,
    records_to_json_bytes, database_to_excel_bytes,
)


MONTH_OPTIONS = [
    ("", "Todos"), ("01", "Enero"), ("02", "Febrero"), ("03", "Marzo"),
    ("04", "Abril"), ("05", "Mayo"), ("06", "Junio"), ("07", "Julio"),
    ("08", "Agosto"), ("09", "Septiembre"), ("10", "Octubre"),
    ("11", "Noviembre"), ("12", "Diciembre"),
]
MONTH_LABELS = dict(MONTH_OPTIONS)
MONTH_VALUES = [value for value, _ in MONTH_OPTIONS]

RELEASE_ID = "SENDA-2026.08.24-R3"

ROOT = Path(__file__).parent
CAT_PATH = ROOT / "catalogs" / "CATALOGO_COD_OPERACIONES.TXT"
DB_PATH = ROOT / "data" / "registro_inmobiliario.db"
ICON_PATH = ROOT / "assets" / "app_icon.svg"
APP_ICON = str(ROOT / "assets" / "app_icon_propuesta2.png")
APP_ICON_B64 = base64.b64encode(Path(APP_ICON).read_bytes()).decode("ascii")

st.set_page_config(
    page_title="Registro Inmobiliario · SENDA",
    page_icon=APP_ICON,
    layout="wide",
)

st.markdown(
    """
<style>
:root { --pearl:#92cbb8; --pearl-dark:#4f947d; --pearl-soft:#e9f5f1; --ink:#173d32; --surface:#ffffff; --surface-soft:#f8fbfa; --border:#d7e6e0; --shadow-soft:0 8px 24px rgba(23,61,50,.07); }
.block-container {padding-top: 1.05rem; padding-bottom: 3rem; max-width:1500px;}
.senda-card {background:linear-gradient(135deg,#ffffff 0%,#f8fbfa 100%);border:1px solid var(--border);border-radius:16px;padding:.75rem .9rem;box-shadow:var(--shadow-soft);}
[data-testid="stExpander"] {border:1px solid var(--border)!important;border-radius:12px!important;background:var(--surface)!important;box-shadow:0 2px 9px rgba(23,61,50,.035);overflow:hidden;}
[data-testid="stExpander"] summary {font-weight:800;color:var(--ink);}
[data-testid="stMetric"] {background:var(--surface-soft);border:1px solid var(--border);border-radius:12px;padding:.55rem .7rem;}
[data-testid="stDataFrame"] {border:1px solid var(--border);border-radius:12px;overflow:hidden;}
.stButton > button, .stDownloadButton > button {border-radius:10px!important;font-weight:800!important;min-height:2.45rem;transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease;}
.stButton > button:hover, .stDownloadButton > button:hover {transform:translateY(-1px);box-shadow:0 5px 14px rgba(23,61,50,.09);border-color:var(--pearl-dark)!important;}
[data-baseweb="input"] > div, [data-baseweb="select"] > div, textarea {border-radius:10px!important;}
hr {border-color:#e7efec!important;} 
div[data-testid="stRadio"] > div {gap:.45rem;}
div[data-testid="stRadio"] label {background:#f4f8f6;border:1px solid #d7e6e0;padding:.45rem .75rem;border-radius:.65rem;}
div[data-testid="stRadio"] label:has(input:checked) {background:var(--pearl-soft);border-color:var(--pearl-dark);color:var(--ink);font-weight:800;}
.senda-brand {display:flex;align-items:center;gap:12px;margin-bottom:.7rem;}
.senda-icon-img {width:46px;height:46px;display:block;object-fit:contain;border-radius:14px;box-shadow:0 3px 10px #173d3218;}
.senda-title {font-size:1.55rem;font-weight:900;color:#173d32;line-height:1.05;}
.senda-sub {font-size:.85rem;color:#6a7d76;}
.senda-version {display:inline-block;margin-top:.25rem;padding:.12rem .45rem;border-radius:999px;background:#e9f5f1;border:1px solid #92cbb8;color:#245c4c;font-size:.72rem;font-weight:800;}
.alarm-yellow {background:#fff3bd;border-left:5px solid #e0b400;padding:.55rem .75rem;border-radius:.45rem;}
.alarm-red {background:#fde3e1;border-left:5px solid #c63b35;padding:.55rem .75rem;border-radius:.45rem;}
.active-code {background:#e9f5f1;border:1px solid #92cbb8;padding:.55rem .75rem;border-radius:.55rem;color:#245c4c;font-weight:800;}
.small-note {color:#6b7d76;font-size:.82rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="senda-brand senda-card">
  <img class="senda-icon-img" src="data:image/png;base64,{APP_ICON_B64}" alt="SENDA Registro Inmobiliario">
  <div><div class="senda-title">Registro Inmobiliario · SENDA</div>
  <div class="senda-sub">Carga trimestral, control cronológico por FOLIO / FINCA y gestión auditada</div>
  <span class="senda-version">Versión {RELEASE_ID}</span></div>
</div>
""",
    unsafe_allow_html=True,
)

init_db(DB_PATH)
opmap = load_operation_catalog(CAT_PATH)

if "datasets" not in st.session_state:
    st.session_state.datasets = {}
if "carga_meta" not in st.session_state:
    st.session_state.carga_meta = []
if "carga_periodo" not in st.session_state:
    st.session_state.carga_periodo = ("", "")
if "senda_page" not in st.session_state:
    st.session_state.senda_page = 1


def lote_id_for(files, anio, trimestre):
    parts = [str(anio), str(trimestre)]
    for f in files:
        parts.extend([getattr(f, "name", ""), str(len(f.getvalue()))])
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def safe_cols(df, cols):
    return [c for c in cols if c in df.columns]


def alarm_icon(fecha):
    level = inactivity_level(fecha)
    return {"ROJO": "🔴", "AMARILLO": "🟡", "SIN FECHA": "⚪", "SIN ALERTA": "🟢"}.get(level, "⚪")


def show_alarm_summary(df):
    if df is None or df.empty:
        return
    levels = df["FECHA_MOVIMIENTO"].map(inactivity_level)
    yellow = int((levels == "AMARILLO").sum())
    red = int((levels == "ROJO").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Pendientes", len(df))
    c2.metric("🟡 Más de 2 meses", yellow)
    c3.metric("🔴 3 meses o más", red)


def render_folio_alert(df):
    """Show the inactivity alert for the selected FOLIO / FINCA using its latest valid movement."""
    if df is None or df.empty:
        return
    dates = pd.to_datetime(df.get("FECHA_MOVIMIENTO", pd.Series(dtype=str)), errors="coerce").dropna()
    if dates.empty:
        st.markdown('<div class="small-note">⚪ Sin fecha válida para calcular alerta.</div>', unsafe_allow_html=True)
        return
    last_date = dates.max().date().isoformat()
    alerta_folio = inactivity_level(last_date)
    if alerta_folio == "ROJO":
        st.markdown(f'<div class="alarm-red"><b>🔴 ALERTA ROJA</b> · 3 meses o más sin movimiento · Último movimiento: {last_date}</div>', unsafe_allow_html=True)
    elif alerta_folio == "AMARILLO":
        st.markdown(f'<div class="alarm-yellow"><b>🟡 ALERTA AMARILLA</b> · Más de 2 meses sin movimiento · Último movimiento: {last_date}</div>', unsafe_allow_html=True)
    else:
        st.success(f"🟢 Sin alerta de inactividad · Último movimiento: {last_date}")


def period_datasets(anio, trimestre):
    if st.session_state.datasets and st.session_state.carga_periodo == (str(anio), str(trimestre)):
        return st.session_state.datasets
    return {
        k: load_dataset(DB_PATH, k, anio=str(anio) if anio else "", trimestre=trimestre)
        for k in ("Fincas", "Cerradas", "Historicos", "Gravamenes", "Segregaciones", "Anotaciones", "Cedulas Juridicas")
    }


def display_original_views(datasets, movements):
    with st.expander("Vistas registrales originales (funcionalidad preservada)", expanded=False):
        tabs = st.tabs(["Fincas/Folios", "Movimientos", "Segregaciones", "Planos", "Gravámenes", "Históricos", "Anotaciones", "Jurídicas", "Códigos"])
        with tabs[0]:
            st.dataframe(datasets.get("Fincas", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[1]:
            mov = movements.copy()
            if not mov.empty:
                cats = st.multiselect("Categoría", sorted(mov["CATEGORIA"].dropna().astype(str).unique()), default=[], key="orig_cats")
                if cats:
                    mov = mov[mov["CATEGORIA"].isin(cats)]
            st.dataframe(mov, use_container_width=True, height=430)
            if not mov.empty:
                st.download_button("Descargar movimientos CSV", mov.to_csv(index=False).encode("utf-8-sig"), "movimientos_consolidados.csv", "text/csv", key="orig_csv")
        with tabs[2]:
            st.dataframe(datasets.get("Segregaciones", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[3]:
            pf = planos_sin_finca(datasets)
            st.metric("Planos sin finca localizada", len(pf))
            st.dataframe(pf, use_container_width=True)
        with tabs[4]:
            st.dataframe(datasets.get("Gravamenes", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[5]:
            st.dataframe(datasets.get("Historicos", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[6]:
            st.dataframe(datasets.get("Anotaciones", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[7]:
            st.dataframe(datasets.get("Cedulas Juridicas", pd.DataFrame()), use_container_width=True, height=430)
        with tabs[8]:
            rows = [{"CODIGO": k[0], "CLASE": k[1], "CODIGO_COMPLETO": k[0] + k[1], "DESCRIPCION": v, "CATEGORIA": classify(v)} for k, v in opmap.items()]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, height=480)


module = st.radio(
    "Módulo",
    ["INICIO", "INFORMACIÓN SENDA", "CONTROL", "GESTIÓN"],
    horizontal=True,
    label_visibility="collapsed",
)

all_movements = load_movements(DB_PATH)
reg_ids = registered_ids(DB_PATH)

if module == "INICIO":
    st.header("INICIO")
    st.caption("Carga trimestral de archivos registrales. Se conserva el flujo existente y los registros se identifican por FOLIO / FINCA.")

    with st.expander("1. Cargar corte trimestral", expanded=all_movements.empty):
        c1, c2 = st.columns([1, 1])
        anio_carga = c1.number_input("Año del corte", min_value=2000, max_value=2100, value=2026, step=1)
        trimestre_carga = c2.selectbox("Trimestre", ["T1", "T2", "T3", "T4"], index=1)
        uploads = st.file_uploader(
            "Archivos o ZIP trimestral",
            accept_multiple_files=True,
            type=["xls", "txt", "TXT", "zip"],
            help="Puede cargar los archivos por separado o un ZIP que los contenga.",
        )
        if st.button("Procesar y guardar carga", type="primary", disabled=not uploads):
            expanded = expand_uploads(uploads)
            raw = {}
            meta = []
            for f in expanded:
                kind = classify_filename(f.name)
                try:
                    df, enc = read_tabular_upload(f)
                    raw.setdefault(kind, []).append(df)
                    meta.append({"Archivo": f.name, "Clase": kind, "Registros": len(df), "Codificación": enc})
                except Exception as exc:
                    meta.append({"Archivo": f.name, "Clase": kind, "Registros": 0, "Codificación": f"ERROR: {exc}"})
            datasets = {}
            for kind, dfs in raw.items():
                if kind in ("Catalogo", "Otro"):
                    continue
                merged = pd.concat(dfs, ignore_index=True) if len(dfs) > 1 else dfs[0]
                datasets[kind] = normalize_dataset(kind, merged, opmap)
            lote_id = lote_id_for(expanded, anio_carga, trimestre_carga)
            for kind, df in datasets.items():
                save_dataset(DB_PATH, kind, df, anio=str(anio_carga), trimestre=trimestre_carga, lote_id=lote_id)
            mov = consolidate_movements(datasets, anio=str(anio_carga), trimestre=trimestre_carga)
            save_movements(DB_PATH, mov, lote_id=lote_id)
            analysis_tables = build_analysis_tables(datasets, mov, opmap)
            for table_kind, table_df in analysis_tables.items():
                save_dataset(DB_PATH, table_kind, table_df, anio=str(anio_carga), trimestre=trimestre_carga, lote_id=lote_id)
            st.session_state.datasets = datasets
            st.session_state.carga_meta = meta
            st.session_state.carga_periodo = (str(anio_carga), trimestre_carga)
            st.session_state.senda_page = 1
            st.success(f"Carga guardada: {len(mov):,} movimientos consolidados. Lote {lote_id}.")
            st.rerun()

    if st.session_state.carga_meta:
        with st.expander("Inventario de la última carga", expanded=False):
            st.dataframe(pd.DataFrame(st.session_state.carga_meta), use_container_width=True)

    if all_movements.empty:
        st.info("Todavía no hay movimientos guardados. Cargue un corte trimestral para crear la base de datos.")
    else:
        st.success(f"Base disponible: {len(all_movements):,} movimientos guardados.")

elif module == "INFORMACIÓN SENDA":
    st.header("INFORMACIÓN SENDA")
    st.caption("Consulta la base organizada, filtra por FOLIO / FINCA, agrupa códigos y controla alarmas de inactividad.")

    if all_movements.empty:
        st.info("Todavía no hay movimientos guardados. Cargue un corte trimestral para crear la base de datos.")
        st.stop()

    with st.expander("Base de datos organizada y exportaciones", expanded=False):
        b1, b2 = st.columns(2)
        if DB_PATH.exists():
            b1.download_button(
                "Descargar base SQLite", DB_PATH.read_bytes(), "registro_inmobiliario.db",
                mime="application/vnd.sqlite3", use_container_width=True,
            )
            b2.download_button(
                "Exportar base completa a Excel", database_to_excel_bytes(DB_PATH),
                "registro_inmobiliario_base.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        st.caption("La base contiene las tablas fuente normalizadas y las secciones analíticas equivalentes al Excel: Resumen, Fincas/Folios, Históricos, Gravámenes, Segregaciones, Anotaciones, Planos_Control, Alertas, Top_Operaciones, Catálogo y Manual de Códigos.")

    st.subheader("2. Consulta, códigos y alarmas")
    f1, f2, f3, f4, f5 = st.columns(5)
    years = sorted([x for x in all_movements["ANIO"].dropna().astype(str).unique() if x])
    year_filter = f1.selectbox("Año", [""] + years, index=0, format_func=lambda x: "Todos" if x == "" else x)
    quarter_filter = f2.selectbox("Trimestre", ["", "T1", "T2", "T3", "T4"], index=0, format_func=lambda x: "Todos" if x == "" else x)
    month_filter = f3.selectbox("Mes del movimiento", MONTH_VALUES, index=0, format_func=lambda x: MONTH_LABELS[x], key="senda_mes")
    cedula = f4.text_input("Buscar por cédula")
    finca = f5.text_input("FOLIO / FINCA", placeholder="Ej. 4-200103-001")
    f6, f7, f8 = st.columns(3)
    nombre = f6.text_input("Nombre")
    apellido = f7.text_input("Apellidos")
    plano = f8.text_input("Plano")

    # CÓDIGOS y ALARMAS se muestran en una misma fila y ambos pueden abrirse/cerrarse.
    alarm_col, code_col = st.columns(2)
    active_code = ""
    mode = "Mostrar"
    with code_col:
        with st.expander("🏷️ CÓDIGOS", expanded=False):
            code_counts = all_movements.groupby("CODIGO_COMPLETO").size().to_dict() if not all_movements.empty else {}
            code_catalog = pd.DataFrame([
                {"CODIGO": code + clase, "SIGNIFICADO": desc, "REGISTROS": int(code_counts.get(code + clase, 0))}
                for (code, clase), desc in opmap.items()
            ]).sort_values(["CODIGO", "SIGNIFICADO"])
            code_options = [""] + [f"{r.CODIGO} — {r.SIGNIFICADO}" for r in code_catalog.itertuples(index=False)]
            active_label = st.selectbox("Código activo", code_options, index=0, format_func=lambda x: "Seleccione un código" if not x else x)
            active_code = active_label.split(" — ", 1)[0] if active_label else ""
            mode = st.radio("Lista de códigos", ["Mostrar", "Ocultar", "MS"], horizontal=True, help="MS = Mostrar Seleccionado")
            if active_label:
                st.markdown(f'<div class="active-code">Código activo: {active_label}</div>', unsafe_allow_html=True)
            if mode == "Mostrar":
                st.dataframe(code_catalog, use_container_width=True, hide_index=True, height=260)
            elif mode == "MS":
                if active_code:
                    st.dataframe(code_catalog[code_catalog["CODIGO"] == active_code], use_container_width=True, hide_index=True)
                else:
                    st.warning("Seleccione un código para usar MS (Mostrar Seleccionado).")
            if active_code:
                code_download = filter_records(all_movements, codigo=active_code, anio=year_filter, trimestre=quarter_filter, mes=month_filter)
                d1, d2 = st.columns(2)
                d1.download_button(
                    f"Descargar {active_code} en Excel",
                    records_to_excel_bytes(code_download),
                    file_name=f"codigo_{active_code}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
                d2.download_button(
                    f"Descargar {active_code} en JSON",
                    records_to_json_bytes(code_download),
                    file_name=f"codigo_{active_code}.json",
                    mime="application/json",
                    use_container_width=True,
                )

    base = filter_records(
        all_movements,
        cedula=cedula, nombre=nombre, apellido=apellido, finca_o_expediente=finca,
        plano=plano, anio=year_filter, trimestre=quarter_filter, mes=month_filter,
        codigo=active_code if mode == "MS" else "",
    )
    # Mostrar pendientes para alarmas, pero la consulta SENDA conserva también los finalizados.
    pending = base[~base["MOVIMIENTO_ID"].isin(reg_ids)].copy()
    with alarm_col:
        with st.expander("🚨 ALARMAS", expanded=True):
            show_alarm_summary(pending)
            st.caption("Las alertas por color también aparecen dentro de cada FOLIO / FINCA en CONTROL.")

    # Coincidencias de personas: todas, aunque existan nombres iguales.
    current_sets = period_datasets(year_filter, quarter_filter)
    fincas_df = current_sets.get("Fincas", pd.DataFrame())
    if not fincas_df.empty and any([cedula, nombre, apellido]):
        personas = enrich_fincas(fincas_df)
        personas = filter_records(personas, cedula=cedula, nombre=nombre, apellido=apellido, finca_o_expediente=finca, plano=plano)
        if not personas.empty:
            with st.expander(f"Coincidencias de personas ({len(personas)})", expanded=True):
                cols = safe_cols(personas, ["FOLIO_REAL", "TIPO_DERECHO", "CEDULA_NORM", "TITULAR", "DERECHO", "NUM_PLANO_NORM"])
                st.dataframe(personas[cols].drop_duplicates(), use_container_width=True, hide_index=True)

    # Los códigos permanecen agrupados consecutivamente.
    base = base.assign(_SIN_CODIGO=base["CODIGO_COMPLETO"].replace("", "(SIN CÓDIGO)"))
    base = base.sort_values(["_SIN_CODIGO", "FECHA_MOVIMIENTO", "MOVIMIENTO_ID"], na_position="last", kind="stable")
    page_df, total_pages = paginate_records(base, st.session_state.senda_page)
    if st.session_state.senda_page > total_pages:
        st.session_state.senda_page = total_pages
        page_df, total_pages = paginate_records(base, total_pages)
    st.markdown(f"**Resultados:** {len(base):,} · Página {st.session_state.senda_page} de {total_pages}")

    for code_key, group in page_df.groupby("_SIN_CODIGO", sort=False):
        real_code = "" if code_key == "(SIN CÓDIGO)" else code_key
        operation = group["OPERACION"].replace("", pd.NA).dropna().iloc[0] if not group["OPERACION"].replace("", pd.NA).dropna().empty else "Sin descripción"
        global_count = int((base["_SIN_CODIGO"] == code_key).sum())
        st.markdown(f"#### {code_key} — {operation} · {global_count} registro(s)")
        for _, row in group.iterrows():
            status = "REGISTRADO" if row["MOVIMIENTO_ID"] in reg_ids else "PENDIENTE"
            icon = "✅" if status == "REGISTRADO" else alarm_icon(row.get("FECHA_MOVIMIENTO"))
            label = f"{icon} {row.get('FECHA_MOVIMIENTO') or 'Sin fecha'} | {real_record_label(row)} | {row.get('TITULAR') or 'Sin titular'}"
            with st.expander(label, expanded=False):
                detail = pd.DataFrame([{
                    "Folio / Finca": row.get("FOLIO_REAL", ""),
                    "Tipo de derecho": row.get("TIPO_DERECHO", ""),
                    "Cédula(s)": row.get("CEDULA_NORM", ""),
                    "Titular(es)": row.get("TITULAR", ""),
                    "Código": row.get("CODIGO_COMPLETO", ""),
                    "Operación": row.get("OPERACION", ""),
                    "Tipo": row.get("TIPO_MOVIMIENTO", ""),
                    "Plano": row.get("NUM_PLANO_NORM", ""),
                    "Fuente": row.get("FUENTE", ""),
                    "Año": row.get("ANIO", ""),
                    "Trimestre": row.get("TRIMESTRE", ""),
                    "Estado": "FINALIZADO / GESTIÓN" if status == "REGISTRADO" else status,
                }])
                st.dataframe(detail, use_container_width=True, hide_index=True)

    p1, p2, p3 = st.columns([1, 2, 1])
    if p1.button("← Anterior", disabled=st.session_state.senda_page <= 1, use_container_width=True):
        st.session_state.senda_page -= 1
        st.rerun()
    new_page = p2.number_input("Página", min_value=1, max_value=max(1, total_pages), value=min(st.session_state.senda_page, max(1, total_pages)), step=1, label_visibility="collapsed")
    if int(new_page) != st.session_state.senda_page:
        st.session_state.senda_page = int(new_page)
        st.rerun()
    if p3.button("Siguiente →", disabled=st.session_state.senda_page >= total_pages, use_container_width=True):
        st.session_state.senda_page += 1
        st.rerun()

    display_original_views(current_sets, base.drop(columns=["_SIN_CODIGO"], errors="ignore"))

elif module == "CONTROL":
    st.header("CONTROL DE MOVIMIENTOS")
    st.caption("Control por FOLIO / FINCA registral. Se utiliza la conformación real de la fuente; no se inventan números adicionales.")
    if all_movements.empty:
        st.info("No hay movimientos en la base. Cárguelos desde INICIO.")
        st.stop()

    pending = all_movements[~all_movements["MOVIMIENTO_ID"].isin(reg_ids)].copy()
    show_alarm_summary(pending)

    types = sorted([x for x in pending["TIPO_MOVIMIENTO"].dropna().astype(str).unique() if x])
    if "ctrl_tipo_select" not in st.session_state:
        st.session_state.ctrl_tipo_select = ""
    q1, q2, q3, q4, q5, q6 = st.columns(6)
    if q1.button("Hipotecas", use_container_width=True):
        st.session_state.ctrl_tipo_select = "HIPOTECA" if "HIPOTECA" in types else ""
        st.rerun()
    if q2.button("Gravámenes", use_container_width=True):
        st.session_state.ctrl_tipo_select = "GRAVAMEN" if "GRAVAMEN" in types else ""
        st.rerun()
    if q3.button("Segregaciones", use_container_width=True):
        st.session_state.ctrl_tipo_select = "SEGREGACION" if "SEGREGACION" in types else ""
        st.rerun()
    if q4.button("Anotaciones", use_container_width=True):
        st.session_state.ctrl_tipo_select = "ANOTACION" if "ANOTACION" in types else ""
        st.rerun()
    if q5.button("Aplicar", use_container_width=True):
        st.rerun()
    if q6.button("Limpiar", use_container_width=True):
        for key, value in {
            "ctrl_desde": None, "ctrl_hasta": None, "ctrl_cedula": "", "ctrl_exp": "",
            "ctrl_nombre": "", "ctrl_apellido": "", "ctrl_folio": "", "ctrl_plano": "",
            "ctrl_tipo_select": "", "ctrl_mes": "",
        }.items():
            st.session_state[key] = value
        st.rerun()

    c1, c2, c3, c4, c5 = st.columns(5)
    desde = c1.date_input("Fecha desde", value=None, key="ctrl_desde")
    hasta = c2.date_input("Fecha hasta", value=None, key="ctrl_hasta")
    mes_movimiento = c3.selectbox("Mes del movimiento", MONTH_VALUES, format_func=lambda x: MONTH_LABELS[x], key="ctrl_mes")
    cedula = c4.text_input("Cédula", key="ctrl_cedula")
    folio_search = c5.text_input("FOLIO / FINCA", key="ctrl_exp", placeholder="Ej. 4-200103-001")
    c6, c7, c8 = st.columns(3)
    nombre = c6.text_input("Nombre", key="ctrl_nombre")
    apellido = c7.text_input("Apellidos", key="ctrl_apellido")
    plano = c8.text_input("Plano", key="ctrl_plano")
    valid_type_options = [""] + types
    if st.session_state.get("ctrl_tipo_select", "") not in valid_type_options:
        st.session_state.ctrl_tipo_select = ""
    tipo = st.selectbox("Tipo de movimiento", valid_type_options, format_func=lambda x: "Todos" if not x else x, key="ctrl_tipo_select")

    filtered = filter_records(
        pending, cedula=cedula, nombre=nombre, apellido=apellido,
        finca_o_expediente=folio_search, plano=plano, tipo=tipo,
        fecha_desde=desde.isoformat() if desde else "", fecha_hasta=hasta.isoformat() if hasta else "", mes=mes_movimiento,
    )
    filtered = filtered.sort_values(["FECHA_MOVIMIENTO", "MOVIMIENTO_ID"], na_position="last", kind="stable")
    st.markdown(f"**Movimientos pendientes encontrados:** {len(filtered):,}")

    if "FOLIO_REAL" not in filtered.columns:
        filtered["FOLIO_REAL"] = ""
    valid_folios = filtered[filtered["FOLIO_REAL"].astype(str).str.strip() != ""].copy()
    missing_folio_count = int((filtered["FOLIO_REAL"].astype(str).str.strip() == "").sum())
    if missing_folio_count:
        st.warning(f"{missing_folio_count} movimiento(s) quedan sin folio real identificable porque la fuente no aporta Derecho suficiente. No se inventa un Derecho ni una numeración 000.")
    folio_opts_df = valid_folios[["FOLIO_REAL", "TIPO_DERECHO"]].drop_duplicates() if not valid_folios.empty else pd.DataFrame(columns=["FOLIO_REAL", "TIPO_DERECHO"])
    folio_labels = {str(r.FOLIO_REAL): str(r.TIPO_DERECHO or "SIN TIPO") for r in folio_opts_df.itertuples(index=False)}
    folio_options = sorted(folio_labels, key=lambda x: [int(part) if part.isdigit() else part for part in x.split("-")])
    selected_folio = st.selectbox(
        "Abrir FOLIO / FINCA", [""] + folio_options,
        format_func=lambda x: "Seleccione FOLIO / FINCA" if not x else f"{x} · {folio_labels.get(x, 'SIN TIPO')}",
    )

    if selected_folio:
        all_folio = select_folio_records(all_movements, folio_real=selected_folio)
        all_folio = all_folio.sort_values(["FECHA_MOVIMIENTO", "MOVIMIENTO_ID"], na_position="last", kind="stable")
        first = all_folio.iloc[0]
        tipo_derecho = str(first.get("TIPO_DERECHO", "") or "SIN TIPO")
        st.subheader(f"FOLIO / FINCA {selected_folio}")
        st.markdown(f"**Tipo de derecho:** {tipo_derecho}")
        planos = sorted({str(x) for x in all_folio.get("NUM_PLANO_NORM", pd.Series(dtype=str)).dropna().astype(str) if str(x).strip()})
        st.markdown(f"**Plano(s):** {', '.join(planos) if planos else '—'}")
        pending_for_alert = all_folio[~all_folio["MOVIMIENTO_ID"].isin(reg_ids)].copy()
        render_folio_alert(pending_for_alert if not pending_for_alert.empty else all_folio)

        finca_base = load_dataset(DB_PATH, "Fincas")
        if not finca_base.empty:
            fb = enrich_fincas(finca_base)
            fb = fb[fb.get("FOLIO_REAL", pd.Series("", index=fb.index)).astype(str) == selected_folio].copy()
            if not fb.empty:
                cols = safe_cols(fb, ["FOLIO_REAL", "TIPO_DERECHO", "TITULAR", "CEDULA_NORM", "NUM_PLANO_NORM", "MEDIDA", "NATURALEZA", "AVALUO", "ANIO", "TRIMESTRE"])
                st.dataframe(fb[cols].drop_duplicates(), use_container_width=True, hide_index=True)

        type_order = ["SEGREGACION", "HIPOTECA", "GRAVAMEN", "ANOTACION", "CIERRE", "RECTIFICACION / MODIFICACION", "OTRO"]
        for t in type_order:
            grp = all_folio[all_folio["TIPO_MOVIMIENTO"] == t]
            if grp.empty:
                continue
            title = {
                "SEGREGACION": "Segregaciones", "HIPOTECA": "Hipotecas", "GRAVAMEN": "Gravámenes",
                "ANOTACION": "Anotaciones", "CIERRE": "Cierres", "RECTIFICACION / MODIFICACION": "Rectificaciones / Modificaciones",
                "OTRO": "Otros movimientos",
            }[t]
            with st.expander(f"{title} ({len(grp)})", expanded=len(grp) == 1):
                tmp = grp.copy()
                tmp["ESTADO"] = tmp["MOVIMIENTO_ID"].map(lambda x: "FINALIZADO / GESTIÓN" if x in reg_ids else "PENDIENTE")
                cols = safe_cols(tmp, ["FECHA_MOVIMIENTO", "FOLIO_REAL", "TIPO_DERECHO", "CODIGO_COMPLETO", "OPERACION", "FUENTE", "NUM_PLANO_NORM", "ESTADO"])
                st.dataframe(tmp[cols], use_container_width=True, hide_index=True)

        saved_folios = list_saved_folios(DB_PATH)
        saved_row = saved_folios[saved_folios["FOLIO_REAL"].astype(str) == selected_folio] if not saved_folios.empty else pd.DataFrame()
        if not saved_row.empty:
            sr = saved_row.iloc[-1]
            st.success(f"Folio guardado en CONTROL por {sr.get('GUARDADO_POR','')} · {sr.get('GUARDADO_EN','')}")

        st.markdown("#### Acciones del folio")
        operador = st.text_input("Operador", key=f"operador_{selected_folio}")
        observacion = st.text_area("Observación (opcional)", key=f"obs_{selected_folio}")
        a1, a2, a3 = st.columns(3)
        if a1.button("GUARDAR FOLIO", use_container_width=True, key=f"save_{selected_folio}"):
            if not operador.strip():
                st.error("Debe indicar el operador que guarda el folio.")
            else:
                count = save_control_folio(DB_PATH, all_folio, folio_real=selected_folio, usuario=operador.strip(), observacion=observacion)
                st.success(f"Folio {selected_folio} guardado en CONTROL con {count} movimiento(s).")
                st.rerun()

        pending_folio = all_folio[~all_folio["MOVIMIENTO_ID"].isin(reg_ids)].copy()
        if a3.button("FINALIZADO", type="primary", use_container_width=True, key=f"final_{selected_folio}"):
            if not operador.strip():
                st.error("Debe indicar quién finaliza / registra el folio.")
            elif pending_folio.empty:
                st.info("Este folio ya está finalizado en GESTIÓN.")
            else:
                count = finalize_folio(DB_PATH, pending_folio, folio_real=selected_folio, usuario=operador.strip(), observacion=observacion)
                st.success(f"Folio {selected_folio} finalizado: {count} movimiento(s) transferidos a GESTIÓN.")
                st.rerun()

        confirm_delete = st.checkbox(f"Confirmo eliminar sólo el folio {selected_folio} de CONTROL/GESTIÓN (la fuente original se conserva)", key=f"confirm_del_{selected_folio}")
        if a2.button("ELIMINAR FOLIO", use_container_width=True, key=f"delete_{selected_folio}"):
            if not operador.strip():
                st.error("Debe indicar el operador que elimina el folio.")
            elif not confirm_delete:
                st.error("Marque la confirmación antes de eliminar.")
            else:
                result = delete_folio(DB_PATH, folio_real=selected_folio, usuario=operador.strip(), observacion=observacion)
                st.success(f"Folio {selected_folio} eliminado del control operativo. Movimientos: {result['movimientos']}; Gestión: {result['gestion']}.")
                st.rerun()

        with st.expander("Ver cuándo y quién guardó / finalizó / eliminó", expanded=False):
            hist = audit_history(DB_PATH, folio_real=selected_folio)
            if hist.empty:
                st.info("Este folio todavía no tiene acciones auditadas.")
            else:
                st.dataframe(hist, use_container_width=True, hide_index=True)

    with st.expander("Historial general de acciones por folio", expanded=False):
        hist_all = audit_history(DB_PATH)
        st.dataframe(hist_all, use_container_width=True, hide_index=True)

elif module == "GESTIÓN":
    st.header("GESTIÓN")
    st.caption("Sólo FOLIO / FINCA FINALIZADOS. Se conserva el tipo de derecho y se visualiza quién y cuándo lo finalizó/registró.")
    reg = list_registered(DB_PATH)

    with st.expander("Importar / Exportar Gestión", expanded=False):
        imp = st.file_uploader("Importar registrados", type=["json", "xlsx", "xls"], key="gestion_import")
        if st.button("Importar a GESTIÓN", disabled=imp is None):
            try:
                records = read_management_import(imp)
                inserted = import_registered_records(DB_PATH, records, usuario_importacion="IMPORTACIÓN GESTIÓN")
                st.success(f"Importación completada: {inserted} registro(s) nuevo(s). Los duplicados fueron omitidos.")
                st.rerun()
            except Exception as exc:
                st.error(f"No se pudo importar: {exc}")

    if reg.empty:
        st.info("Aún no hay trámites registrados. Regístrelos desde CONTROL o impórtelos aquí.")
        st.stop()

    g1, g2, g3, g4 = st.columns(4)
    cedula = g1.text_input("Cédula", key="gest_cedula")
    exp = g2.text_input("FOLIO / FINCA", key="gest_exp", placeholder="Ej. 4-200103-001")
    codigo = g3.text_input("Código", key="gest_codigo")
    mes_movimiento_gestion = g4.selectbox("Mes del movimiento", MONTH_VALUES, format_func=lambda x: MONTH_LABELS[x], key="gest_mes_movimiento")
    g6, g7, g8, g9, g10 = st.columns(5)
    nombre = g6.text_input("Nombre", key="gest_nombre")
    apellido = g7.text_input("Apellidos", key="gest_apellido")
    reg_desde = g8.date_input("Registrado desde", value=None, key="gest_reg_desde")
    reg_hasta = g9.date_input("Registrado hasta", value=None, key="gest_reg_hasta")
    mes_registro = g10.selectbox("Mes finalizado / registrado", MONTH_VALUES, format_func=lambda x: MONTH_LABELS[x], key="gest_mes_registro")

    filtered = filter_records(reg, cedula=cedula, nombre=nombre, apellido=apellido, finca_o_expediente=exp, codigo=codigo, mes=mes_movimiento_gestion)
    filtered = filter_month_column(filtered, "REGISTRADO_EN", mes_registro)
    if reg_desde or reg_hasta:
        dates = pd.to_datetime(filtered["REGISTRADO_EN"], errors="coerce")
        mask = dates.notna()
        if reg_desde:
            mask &= dates.dt.date >= reg_desde
        if reg_hasta:
            mask &= dates.dt.date <= reg_hasta
        filtered = filtered[mask]

    st.markdown(f"**Finalizados encontrados:** {len(filtered):,}")
    cols = safe_cols(filtered, [
        "FOLIO_REAL", "TIPO_DERECHO", "NUM_PLANO_NORM", "CEDULA_NORM", "TITULAR",
        "FECHA_MOVIMIENTO", "CODIGO_COMPLETO", "OPERACION", "TIPO_MOVIMIENTO",
        "REGISTRADO_POR", "REGISTRADO_EN", "OBSERVACION_REGISTRO",
    ])
    gestion_view = filtered[cols].copy().rename(columns={
        "FOLIO_REAL": "FOLIO / FINCA", "TIPO_DERECHO": "TIPO DE DERECHO", "NUM_PLANO_NORM": "PLANO",
        "REGISTRADO_POR": "FINALIZADO / REGISTRADO POR",
        "REGISTRADO_EN": "FINALIZADO / REGISTRADO EN",
        "OBSERVACION_REGISTRO": "OBSERVACIÓN",
    })
    st.dataframe(gestion_view, use_container_width=True, hide_index=True, height=440)

    d1, d2 = st.columns(2)
    d1.download_button(
        "Exportar resultados JSON",
        records_to_json_bytes(filtered),
        file_name="gestion_registrados.json",
        mime="application/json",
        use_container_width=True,
    )
    d2.download_button(
        "Exportar resultados Excel",
        records_to_excel_bytes(filtered),
        file_name="gestion_registrados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    exp_options = sorted([x for x in filtered.get("FOLIO_REAL", pd.Series(dtype=str)).dropna().astype(str).unique() if x])
    selected = st.selectbox("Ver auditoría de FOLIO / FINCA", [""] + exp_options, format_func=lambda x: "Seleccione FOLIO / FINCA" if not x else x)
    if selected:
        hist = audit_history(DB_PATH, folio_real=selected)
        st.dataframe(hist, use_container_width=True, hide_index=True)

st.divider()
st.caption("Herramienta de control y apoyo analítico. No sustituye certificaciones registrales, estudio de título ni revisión jurídica del asiento original.")
