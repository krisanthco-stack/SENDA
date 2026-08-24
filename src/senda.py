import hashlib
import math
import re
from datetime import date, datetime
from typing import Dict, Optional

import pandas as pd

from src.registro import classify


RIGHT_TYPES = {
    "D": "DOMINIO",
    "H": "HABITACION",
    "N": "NUDA PROPIEDAD",
    "U": "USUFRUCTO",
    "S": "USO",
    "C": "USUFRUCTO CONJUNTO",
}


def build_folio_real(provincia, numero, derecho):
    """Build the visible registry folio: Provincia-Finca-Derecho(3 digits)."""
    provincia = _clean(provincia)
    numero = _clean(numero)
    derecho = _clean(derecho)
    if not provincia or not numero or derecho == "":
        return ""
    if derecho.isdigit():
        derecho = derecho.zfill(3)
    return f"{provincia}-{numero}-{derecho}"


def right_type(codigo):
    return RIGHT_TYPES.get(_clean(codigo).upper(), _clean(codigo).upper())


def _clean(value):
    return "" if value is None else str(value).strip()


def _digits(value):
    return re.sub(r"\D", "", _clean(value))


def _norm_text(value):
    return _clean(value).casefold()


def _date_text(value):
    raw = _clean(value)
    if not raw:
        return ""
    parsed = pd.to_datetime(raw, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.strftime("%Y-%m-%d")


def paginate_records(df: pd.DataFrame, page: int):
    """Page 1 has 25 rows; following pages have 20."""
    page = max(1, int(page or 1))
    total = len(df)
    total_pages = 1 if total <= 25 else 1 + math.ceil((total - 25) / 20)
    page = min(page, total_pages)
    if page == 1:
        start, size = 0, 25
    else:
        start, size = 25 + (page - 2) * 20, 20
    return df.iloc[start:start + size].copy(), total_pages


def inactivity_level(fecha, today: Optional[date] = None):
    fecha_txt = _date_text(fecha)
    if not fecha_txt:
        return "SIN FECHA"
    current = today or date.today()
    event = datetime.strptime(fecha_txt, "%Y-%m-%d").date()
    days = (current - event).days
    if days >= 90:
        return "ROJO"
    if days > 60:
        return "AMARILLO"
    return "SIN ALERTA"


def movement_type(description):
    text = _clean(description).upper()
    if "HIPOTECA" in text:
        return "HIPOTECA"
    if "SEGREGACION" in text:
        return "SEGREGACION"
    if "ANOTACION" in text or "PRACTICADO" in text:
        return "ANOTACION"
    if "CIERRE" in text:
        return "CIERRE"
    if "RECTIFICACION" in text or "MODIFICACION" in text:
        return "RECTIFICACION / MODIFICACION"
    if any(x in text for x in ["SERVIDUMBRE", "EMBARGO", "GRAVAMEN", "LIMITACION", "DEMANDA", "INMOVILIZACION", "HABITACION FAMILIAR", "ARRENDAMIENTO"]):
        return "GRAVAMEN"
    return "OTRO"


def enrich_fincas(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["FINCA_ID", "PROVINCIA", "NUMERO", "DERECHO", "COD_DERECHO", "NUMERO_IDENT", "NOMBRE", "APELLIDO_1", "APELLIDO_2", "NOMBRE_JURIDICO", "NUM_PLANO_NORM"]:
        if col not in out.columns:
            out[col] = ""
    physical = (
        out["NOMBRE"].map(_clean) + " " +
        out["APELLIDO_1"].map(_clean) + " " +
        out["APELLIDO_2"].map(_clean)
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    legal = out["NOMBRE_JURIDICO"].map(_clean)
    out["TITULAR"] = legal.where(legal != "", physical)
    out["NOMBRE_BUSQUEDA"] = out["TITULAR"].map(_clean)
    out["CEDULA_NORM"] = out["NUMERO_IDENT"].map(_digits)
    # EXPEDIENTE_ID is retained only as an internal compatibility field.
    out["EXPEDIENTE_ID"] = out["NUMERO"].map(_clean)
    out["PLANO_NORM"] = out["NUM_PLANO_NORM"].map(_digits)
    out["FOLIO_REAL"] = out.apply(lambda r: build_folio_real(r.get("PROVINCIA"), r.get("NUMERO"), r.get("DERECHO")), axis=1)
    out["TIPO_DERECHO"] = out["COD_DERECHO"].map(right_type)
    return out


def _merge_owner(target, payload):
    if target is None:
        target = {"CEDULA_NORM": "", "TITULAR": "", "NOMBRE_BUSQUEDA": "", "PLANO_NORM": "", "FOLIO_REAL": "", "TIPO_DERECHO": ""}
    for field in ("CEDULA_NORM", "TITULAR", "NOMBRE_BUSQUEDA"):
        current = [x.strip() for x in _clean(target.get(field)).split(" | ") if x.strip()]
        value = _clean(payload.get(field))
        if value and value not in current:
            current.append(value)
        target[field] = " | ".join(current)
    if not _clean(target.get("PLANO_NORM")):
        target["PLANO_NORM"] = _clean(payload.get("PLANO_NORM"))
    for field in ("FOLIO_REAL", "TIPO_DERECHO"):
        if not _clean(target.get(field)):
            target[field] = _clean(payload.get(field))
    return target


def _owner_indexes(fincas: pd.DataFrame):
    enriched = enrich_fincas(fincas) if fincas is not None else pd.DataFrame()
    by_folio = {}
    by_finca = {}
    if enriched.empty:
        return by_folio, by_finca
    for _, row in enriched.iterrows():
        payload = {
            "CEDULA_NORM": _clean(row.get("CEDULA_NORM")),
            "TITULAR": _clean(row.get("TITULAR")),
            "NOMBRE_BUSQUEDA": _clean(row.get("NOMBRE_BUSQUEDA")),
            "PLANO_NORM": _clean(row.get("PLANO_NORM")),
            "FOLIO_REAL": _clean(row.get("FOLIO_REAL")),
            "TIPO_DERECHO": _clean(row.get("TIPO_DERECHO")),
        }
        fid = _clean(row.get("FINCA_ID"))
        der = _clean(row.get("DERECHO"))
        if fid and der:
            by_folio[(fid, der)] = _merge_owner(by_folio.get((fid, der)), payload)
        if fid:
            by_finca[fid] = _merge_owner(by_finca.get(fid), payload)
    return by_folio, by_finca


def _stable_id(values):
    raw = "|".join(_clean(v) for v in values)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _source_rows(kind: str, df: pd.DataFrame):
    date_col = {
        "Historicos": "FECHA_PROCESO",
        "Gravamenes": "FECHA_INICIA",
        "Anotaciones": "FECHAPR",
        "Fincas": "FECHA_ULT_ACT",
        "Segregaciones": "",
    }.get(kind, "")
    rows = []
    for source_idx, r in df.iterrows():
        codigo = _clean(r.get("CODIGO_COMPLETO")) or _clean(r.get("COD_OPERACION"))
        operacion = _clean(r.get("OPERACION")) or _clean(r.get("DESCRIP_OPER"))
        categoria = _clean(r.get("CATEGORIA"))
        fecha = _date_text(r.get(date_col)) if date_col else ""
        rows.append({
            "FUENTE": kind,
            "SOURCE_ROW": str(source_idx),
            "FINCA_ID": _clean(r.get("FINCA_ID")),
            "PROVINCIA": _clean(r.get("PROVINCIA")),
            "NUMERO": _clean(r.get("NUMERO")),
            "EXPEDIENTE_ID": _clean(r.get("NUMERO")),
            "DERECHO": _clean(r.get("DERECHO")),
            "FOLIO_REAL": build_folio_real(r.get("PROVINCIA"), r.get("NUMERO"), r.get("DERECHO")),
            "TIPO_DERECHO": right_type(r.get("COD_DERECHO")),
            "FOLIO_DERECHO": _clean(r.get("FOLIO_DERECHO")),
            "FECHA_MOVIMIENTO": fecha,
            "CODIGO_COMPLETO": codigo,
            "OPERACION": operacion,
            "CATEGORIA": categoria,
            "TIPO_MOVIMIENTO": movement_type(operacion),
            "NUM_PLANO_NORM": _clean(r.get("NUM_PLANO_NORM")),
            "PRESENTACION": _clean(r.get("PRESENTACION")),
            "DESCRIP_OPER": _clean(r.get("DESCRIP_OPER")),
        })
    return rows


def consolidate_movements(datasets: Dict[str, pd.DataFrame], anio="", trimestre="") -> pd.DataFrame:
    fincas = datasets.get("Fincas", pd.DataFrame())
    by_folio, by_finca = _owner_indexes(fincas)
    all_rows = []
    for kind in ("Historicos", "Gravamenes", "Segregaciones", "Anotaciones"):
        df = datasets.get(kind)
        if df is None or df.empty:
            continue
        all_rows.extend(_source_rows(kind, df))
    if not all_rows:
        return pd.DataFrame(columns=[
            "MOVIMIENTO_ID","FUENTE","SOURCE_ROW","FINCA_ID","PROVINCIA","NUMERO","EXPEDIENTE_ID","DERECHO","FOLIO_REAL","TIPO_DERECHO","FOLIO_DERECHO",
            "FECHA_MOVIMIENTO","CODIGO_COMPLETO","OPERACION","CATEGORIA","TIPO_MOVIMIENTO",
            "CEDULA_NORM","TITULAR","NOMBRE_BUSQUEDA","NUM_PLANO_NORM","ANIO","TRIMESTRE"
        ])
    out = pd.DataFrame(all_rows)
    ceds, titulares, nombres, planos, folios_reales, tipos_derecho = [], [], [], [], [], []
    for _, row in out.iterrows():
        key = (_clean(row.get("FINCA_ID")), _clean(row.get("DERECHO")))
        exact_owner = by_folio.get(key) or {}
        owner = exact_owner or by_finca.get(key[0]) or {}
        ceds.append(owner.get("CEDULA_NORM", ""))
        titulares.append(owner.get("TITULAR", ""))
        nombres.append(owner.get("NOMBRE_BUSQUEDA", ""))
        planos.append(_clean(row.get("NUM_PLANO_NORM")) or owner.get("PLANO_NORM", ""))
        # Folio/type are right-specific and must never be inherited from a sibling right.
        folios_reales.append(_clean(row.get("FOLIO_REAL")) or exact_owner.get("FOLIO_REAL", ""))
        tipos_derecho.append(_clean(row.get("TIPO_DERECHO")) or exact_owner.get("TIPO_DERECHO", ""))
    out["CEDULA_NORM"] = ceds
    out["TITULAR"] = titulares
    out["NOMBRE_BUSQUEDA"] = nombres
    out["NUM_PLANO_NORM"] = planos
    out["FOLIO_REAL"] = folios_reales
    out["TIPO_DERECHO"] = tipos_derecho
    out["ANIO"] = _clean(anio)
    out["TRIMESTRE"] = _clean(trimestre)
    out["MOVIMIENTO_ID"] = out.apply(lambda r: _stable_id([
        r.get("FUENTE"), r.get("SOURCE_ROW"), r.get("FINCA_ID"), r.get("DERECHO"), r.get("FECHA_MOVIMIENTO"),
        r.get("CODIGO_COMPLETO"), r.get("OPERACION"), r.get("PRESENTACION"), r.get("ANIO"), r.get("TRIMESTRE")
    ]), axis=1)
    out["ORDEN_FECHA"] = pd.to_datetime(out["FECHA_MOVIMIENTO"], errors="coerce")
    out["_SOURCE_ORDER"] = pd.to_numeric(out["SOURCE_ROW"], errors="coerce").fillna(-1)
    out = out.sort_values(["ORDEN_FECHA", "FUENTE", "_SOURCE_ORDER", "MOVIMIENTO_ID"], na_position="last", kind="stable").drop(columns=["ORDEN_FECHA", "_SOURCE_ORDER"]).reset_index(drop=True)
    return out


def filter_records(
    df: pd.DataFrame, *, cedula="", nombre="", apellido="", finca="", expediente="", finca_o_expediente="",
    folio="", folio_real="", plano="", codigo="", operacion="", tipo="", fecha_desde="", fecha_hasta="",
    anio="", trimestre="", mes=""
) -> pd.DataFrame:
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    out = df.copy()

    def contains_series(col, value, digits=False):
        if not value:
            return pd.Series(True, index=out.index)
        if col not in out.columns:
            return pd.Series(False, index=out.index)
        needle = _digits(value) if digits else _norm_text(value)
        if digits:
            return out[col].map(_digits).str.contains(needle, regex=False, na=False)
        return out[col].map(_norm_text).str.contains(needle, regex=False, na=False)

    mask = pd.Series(True, index=out.index)
    mask &= contains_series("CEDULA_NORM", cedula, digits=True)
    mask &= contains_series("NOMBRE_BUSQUEDA", nombre)
    mask &= contains_series("NOMBRE_BUSQUEDA", apellido)
    mask &= contains_series("FINCA_ID", finca)
    mask &= contains_series("EXPEDIENTE_ID", expediente)
    mask &= contains_series("FOLIO_REAL", folio_real)
    if finca_o_expediente:
        finca_mask = contains_series("FINCA_ID", finca_o_expediente)
        expediente_mask = contains_series("EXPEDIENTE_ID", finca_o_expediente)
        folio_real_mask = contains_series("FOLIO_REAL", finca_o_expediente)
        mask &= (finca_mask | expediente_mask | folio_real_mask)
    if folio:
        mask &= out.get("DERECHO", pd.Series("", index=out.index)).map(_clean).eq(_clean(folio))
    mask &= contains_series("NUM_PLANO_NORM", plano, digits=True)
    mask &= contains_series("CODIGO_COMPLETO", codigo)
    mask &= contains_series("OPERACION", operacion)
    if tipo:
        mask &= out.get("TIPO_MOVIMIENTO", pd.Series("", index=out.index)).map(_clean).eq(_clean(tipo))
    if anio:
        mask &= out.get("ANIO", pd.Series("", index=out.index)).map(_clean).eq(_clean(anio))
    if trimestre:
        mask &= out.get("TRIMESTRE", pd.Series("", index=out.index)).map(_clean).eq(_clean(trimestre))
    if mes:
        dates_mes = pd.to_datetime(out.get("FECHA_MOVIMIENTO", pd.Series("", index=out.index)), errors="coerce")
        try:
            month_num = int(str(mes).strip())
        except (TypeError, ValueError):
            month_num = 0
        if 1 <= month_num <= 12:
            mask &= dates_mes.notna() & dates_mes.dt.month.eq(month_num)
    if fecha_desde or fecha_hasta:
        dates = pd.to_datetime(out.get("FECHA_MOVIMIENTO", pd.Series("", index=out.index)), errors="coerce")
        mask &= dates.notna()
        if fecha_desde:
            mask &= dates >= pd.to_datetime(fecha_desde)
        if fecha_hasta:
            mask &= dates <= pd.to_datetime(fecha_hasta)
    return out[mask].copy()



def filter_month_column(df: pd.DataFrame, column: str, mes="") -> pd.DataFrame:
    """Filter any date/datetime column by calendar month (1-12)."""
    if df is None or df.empty or not mes:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    if column not in df.columns:
        return df.iloc[0:0].copy()
    try:
        month_num = int(str(mes).strip())
    except (TypeError, ValueError):
        return df.copy()
    if not 1 <= month_num <= 12:
        return df.copy()
    dates = pd.to_datetime(df[column], errors="coerce")
    mask = dates.notna() & dates.dt.month.eq(month_num)
    return df[mask].copy()




def real_record_label(row):
    """Visible registral label without invented expediente/tramite numbering."""
    folio = _clean(row.get("FOLIO_REAL"))
    tipo = _clean(row.get("TIPO_DERECHO")) or "—"
    plano = _clean(row.get("NUM_PLANO_NORM")) or "—"
    return f"FOLIO / FINCA {folio or '—'} | {tipo} | Plano {plano}"


def select_folio_records(df: pd.DataFrame, *, folio_real="") -> pd.DataFrame:
    """Return movements only for the exact Provincia-Finca-Derecho folio."""
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    value = _clean(folio_real)
    if not value:
        return df.iloc[0:0].copy()
    return df[df.get("FOLIO_REAL", pd.Series("", index=df.index)).map(_clean).eq(value)].copy()


def select_finca_records(df: pd.DataFrame, *, finca_id="", finca_numero="") -> pd.DataFrame:
    """Return every movement belonging to the selected real finca/folio real."""
    if df is None or df.empty:
        return df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    if finca_id:
        return df[df.get("FINCA_ID", pd.Series("", index=df.index)).map(_clean).eq(_clean(finca_id))].copy()
    if finca_numero:
        return df[df.get("EXPEDIENTE_ID", pd.Series("", index=df.index)).map(_clean).eq(_clean(finca_numero))].copy()
    return df.iloc[0:0].copy()

def build_analysis_tables(datasets: Dict[str, pd.DataFrame], movements: pd.DataFrame, opmap: dict):
    fincas = datasets.get("Fincas", pd.DataFrame()).copy()
    cerradas = datasets.get("Cerradas", pd.DataFrame()).copy()
    seg = datasets.get("Segregaciones", pd.DataFrame()).copy()

    resumen_rows = [
        {"INDICADOR": "Fincas - filas", "VALOR": len(fincas)},
        {"INDICADOR": "Fincas activas únicas", "VALOR": fincas["FINCA_ID"].nunique() if "FINCA_ID" in fincas.columns else 0},
        {"INDICADOR": "Fincas cerradas únicas", "VALOR": cerradas["FINCA_ID"].nunique() if "FINCA_ID" in cerradas.columns else 0},
        {"INDICADOR": "Movimientos consolidados", "VALOR": len(movements)},
        {"INDICADOR": "Históricos", "VALOR": len(datasets.get("Historicos", pd.DataFrame()))},
        {"INDICADOR": "Gravámenes", "VALOR": len(datasets.get("Gravamenes", pd.DataFrame()))},
        {"INDICADOR": "Segregaciones", "VALOR": len(seg)},
        {"INDICADOR": "Anotaciones", "VALOR": len(datasets.get("Anotaciones", pd.DataFrame()))},
    ]
    resumen = pd.DataFrame(resumen_rows)

    plan_rows = []
    if not fincas.empty:
        if "NUM_PLANO_NORM" not in fincas.columns:
            fincas["NUM_PLANO_NORM"] = ""
        for _, r in fincas[fincas["NUM_PLANO_NORM"].map(_clean) == ""].drop_duplicates("FINCA_ID").iterrows():
            plan_rows.append({
                "TIPO_CONTROL": "FINCA ACTIVA SIN PLANO",
                "NUM_PLANO": "",
                "FINCA_O_DETALLE": _clean(r.get("FINCA_ID")),
                "RESULTADO": "REVISAR",
            })

    current_plans = set()
    pindex = {}
    for kind, frame in (("ACTIVA", fincas), ("CERRADA", cerradas)):
        if frame is None or frame.empty or "NUM_PLANO_NORM" not in frame.columns:
            continue
        for _, r in frame.iterrows():
            p = _clean(r.get("NUM_PLANO_NORM"))
            if not p:
                continue
            current_plans.add(p)
            pindex.setdefault(p, set()).add((_clean(r.get("FINCA_ID")), kind))
    if not seg.empty and "NUM_PLANO_NORM" in seg.columns:
        for _, r in seg.iterrows():
            p = _clean(r.get("NUM_PLANO_NORM"))
            if p and p not in current_plans:
                plan_rows.append({
                    "TIPO_CONTROL": "PLANO DE SEGREGACION SIN FINCA",
                    "NUM_PLANO": p,
                    "FINCA_O_DETALLE": _clean(r.get("FINCA_ID")),
                    "RESULTADO": "REVISAR",
                })
    for p, vals in sorted(pindex.items()):
        if len(vals) > 1:
            detail = "; ".join(f"{f} [{k}]" for f, k in sorted(vals))
            plan_rows.append({
                "TIPO_CONTROL": "PLANO EN MAS DE UNA MATRICULA",
                "NUM_PLANO": p,
                "FINCA_O_DETALLE": detail,
                "RESULTADO": "REVISAR ANTECEDENTE",
            })
    planos = pd.DataFrame(plan_rows, columns=["TIPO_CONTROL","NUM_PLANO","FINCA_O_DETALLE","RESULTADO"])
    alertas = planos.rename(columns={"TIPO_CONTROL": "TIPO", "FINCA_O_DETALLE": "REFERENCIA", "RESULTADO": "DETALLE"}).copy()
    if not alertas.empty:
        alertas.insert(0, "SEVERIDAD", alertas["TIPO"].map(lambda x: "ALTA" if "SIN FINCA" in x else "MEDIA"))

    if movements is None or movements.empty:
        top_ops = pd.DataFrame(columns=["FUENTE","CODIGO","DESCRIPCION","CANTIDAD"])
    else:
        top_ops = (
            movements.groupby(["FUENTE","CODIGO_COMPLETO","OPERACION"], dropna=False)
            .size().reset_index(name="CANTIDAD")
            .rename(columns={"CODIGO_COMPLETO":"CODIGO","OPERACION":"DESCRIPCION"})
            .sort_values(["CANTIDAD","FUENTE","CODIGO"], ascending=[False, True, True], kind="stable")
            .reset_index(drop=True)
        )

    catalogo = pd.DataFrame([
        {"CODIGO": code, "CLASE": clase, "CODIGO_COMPLETO": code + clase, "DESCRIPCION": desc, "CATEGORIA_ANALITICA": classify(desc)}
        for (code, clase), desc in opmap.items()
    ])
    manual = pd.DataFrame([
        {"ELEMENTO":"STATUS","LECTURA":"D=CERRADA; NULL=ACTIVA; B/blanco según regla del catálogo.","USO":"Estado registral del registro cargado."},
        {"ELEMENTO":"COD_OPERACION","LECTURA":"Código base + clase.","USO":"Traducir operaciones en Fincas, Gravámenes y Anotaciones."},
        {"ELEMENTO":"COD_OPER + CLASE_CODIGO","LECTURA":"Históricos separa ambos componentes.","USO":"Llave exacta del catálogo de operaciones."},
        {"ELEMENTO":"DERECHO","LECTURA":"Secuencial de derecho/folio.","USO":"Separar titulares y afectaciones dentro de una finca."},
        {"ELEMENTO":"NUM_PLANO","LECTURA":"Plano normalizado a dígitos.","USO":"Cruce catastral y control de segregaciones."},
        {"ELEMENTO":"FINCA_MADRE","LECTURA":"Referencia de antecedente en Segregaciones.","USO":"Reconstrucción de genealogía, sujeta a validación."},
    ])
    return {
        "Resumen": resumen,
        "Planos Control": planos,
        "Alertas": alertas,
        "Top Operaciones": top_ops,
        "Catalogo Operaciones": catalogo,
        "Manual Codigos": manual,
    }
