import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


DATASET_TABLES = {
    "Fincas": "fincas_folios",
    "Cerradas": "fincas_cerradas",
    "Historicos": "historicos",
    "Gravamenes": "gravamenes",
    "Segregaciones": "segregaciones",
    "Anotaciones": "anotaciones",
    "Cedulas Juridicas": "cedulas_juridicas",
    "Resumen": "resumen",
    "Planos Control": "planos_control",
    "Alertas": "alertas",
    "Top Operaciones": "top_operaciones",
    "Catalogo Operaciones": "catalogo_operaciones",
    "Manual Codigos": "manual_codigos",
}


def _db_path(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _ensure_core_column(con, table, column, sql_type="TEXT"):
    if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is None:
        return
    cols = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
    if column not in cols:
        con.execute(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {sql_type}')


RIGHT_TYPES = {
    "D": "DOMINIO", "H": "HABITACION", "N": "NUDA PROPIEDAD",
    "U": "USUFRUCTO", "S": "USO", "C": "USUFRUCTO CONJUNTO",
}


def _folio_real(provincia, numero, derecho):
    provincia = str(provincia or "").strip()
    numero = str(numero or "").strip()
    derecho = str(derecho or "").strip()
    if not provincia or not numero or derecho == "":
        return ""
    if derecho.isdigit():
        derecho = derecho.zfill(3)
    return f"{provincia}-{numero}-{derecho}"


def _backfill_folio_metadata(con):
    """Migrate previous databases to the approved Provincia-Finca-Derecho folio."""
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    owner_map = {}
    if "fincas_folios" in tables:
        cols = {r[1] for r in con.execute('PRAGMA table_info("fincas_folios")')}
        needed = ["FINCA_ID", "PROVINCIA", "NUMERO", "DERECHO", "COD_DERECHO"]
        if all(c in cols for c in needed):
            for fid, prov, num, der, cod in con.execute('SELECT FINCA_ID,PROVINCIA,NUMERO,DERECHO,COD_DERECHO FROM fincas_folios'):
                key = (str(fid or "").strip(), str(der or "").strip())
                owner_map[key] = (
                    str(prov or "").strip(), str(num or "").strip(),
                    _folio_real(prov, num, der), RIGHT_TYPES.get(str(cod or "").strip().upper(), str(cod or "").strip().upper())
                )

    for table in ("movimientos", "gestion_registrados"):
        if table not in tables:
            continue
        cols = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
        required = {"FINCA_ID", "EXPEDIENTE_ID", "DERECHO", "PROVINCIA", "NUMERO", "FOLIO_REAL", "TIPO_DERECHO"}
        if not required.issubset(cols):
            continue
        rows = con.execute(f'SELECT rowid,FINCA_ID,PROVINCIA,NUMERO,EXPEDIENTE_ID,DERECHO,FOLIO_REAL,TIPO_DERECHO FROM "{table}"').fetchall()
        for rowid, fid, prov, num, exp, der, folio, tipo in rows:
            fid_s = str(fid or "").strip()
            der_s = str(der or "").strip()
            meta = owner_map.get((fid_s, der_s), ("", "", "", ""))
            province = str(prov or "").strip() or meta[0] or (fid_s.split("-", 1)[0] if fid_s else "")
            number = str(num or "").strip() or meta[1] or str(exp or "").strip()
            folio_value = str(folio or "").strip() or meta[2] or _folio_real(province, number, der_s)
            tipo_value = str(tipo or "").strip() or meta[3]
            con.execute(
                f'UPDATE "{table}" SET PROVINCIA=?,NUMERO=?,FOLIO_REAL=?,TIPO_DERECHO=? WHERE rowid=?',
                (province, number, folio_value, tipo_value, rowid),
            )


def init_db(path):
    path = _db_path(path)
    with sqlite3.connect(path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                MOVIMIENTO_ID TEXT PRIMARY KEY,
                FUENTE TEXT, SOURCE_ROW TEXT, FINCA_ID TEXT, PROVINCIA TEXT, NUMERO TEXT, EXPEDIENTE_ID TEXT, DERECHO TEXT,
                FOLIO_REAL TEXT, TIPO_DERECHO TEXT, FOLIO_DERECHO TEXT, FECHA_MOVIMIENTO TEXT, CODIGO_COMPLETO TEXT,
                OPERACION TEXT, CATEGORIA TEXT, TIPO_MOVIMIENTO TEXT,
                CEDULA_NORM TEXT, TITULAR TEXT, NOMBRE_BUSQUEDA TEXT,
                NUM_PLANO_NORM TEXT, PRESENTACION TEXT, DESCRIP_OPER TEXT,
                ANIO TEXT, TRIMESTRE TEXT, LOTE_ID TEXT
            )
        """)
        _ensure_core_column(con, "movimientos", "SOURCE_ROW", "TEXT")
        for col in ("PROVINCIA", "NUMERO", "FOLIO_REAL", "TIPO_DERECHO"):
            _ensure_core_column(con, "movimientos", col, "TEXT")
        con.execute("""
            CREATE TABLE IF NOT EXISTS gestion_registrados (
                MOVIMIENTO_ID TEXT PRIMARY KEY,
                EXPEDIENTE_ID TEXT, FINCA_ID TEXT, PROVINCIA TEXT, NUMERO TEXT, DERECHO TEXT, FOLIO_REAL TEXT, TIPO_DERECHO TEXT, FOLIO_DERECHO TEXT,
                CEDULA_NORM TEXT, TITULAR TEXT, NOMBRE_BUSQUEDA TEXT,
                CODIGO_COMPLETO TEXT, OPERACION TEXT, CATEGORIA TEXT, TIPO_MOVIMIENTO TEXT,
                FUENTE TEXT, FECHA_MOVIMIENTO TEXT, NUM_PLANO_NORM TEXT,
                ANIO TEXT, TRIMESTRE TEXT, REGISTRADO_POR TEXT, REGISTRADO_EN TEXT,
                OBSERVACION_REGISTRO TEXT, PAYLOAD_JSON TEXT
            )
        """)
        for col in ("PROVINCIA", "NUMERO", "FOLIO_REAL", "TIPO_DERECHO"):
            _ensure_core_column(con, "gestion_registrados", col, "TEXT")
        con.execute("""
            CREATE TABLE IF NOT EXISTS folios_guardados (
                FOLIO_REAL TEXT PRIMARY KEY, FINCA_ID TEXT, PROVINCIA TEXT, NUMERO TEXT, DERECHO TEXT,
                TIPO_DERECHO TEXT, NUM_PLANO_NORM TEXT, TITULAR TEXT, CEDULA_NORM TEXT,
                MOVIMIENTOS INTEGER, GUARDADO_POR TEXT, GUARDADO_EN TEXT, OBSERVACION TEXT
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS auditoria (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                MOVIMIENTO_ID TEXT NOT NULL,
                EXPEDIENTE_ID TEXT,
                FOLIO_REAL TEXT,
                ACCION TEXT NOT NULL,
                USUARIO TEXT NOT NULL,
                FECHA_HORA TEXT NOT NULL,
                OBSERVACION TEXT
            )
        """)
        _ensure_core_column(con, "auditoria", "FOLIO_REAL", "TEXT")
        _backfill_folio_metadata(con)
        con.commit()
    return path


def _safe_table(name):
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Nombre de tabla no válido")
    return name


def _table_exists(con, table):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _ensure_dataframe_columns(con, table, columns):
    table = _safe_table(table)
    if not _table_exists(con, table):
        return
    existing = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
    for col in columns:
        if col not in existing:
            safe_col = str(col).replace('"', '""')
            con.execute(f'ALTER TABLE "{table}" ADD COLUMN "{safe_col}" TEXT')


def save_dataset(path, kind, df: pd.DataFrame, *, anio="", trimestre="", lote_id=""):
    init_db(path)
    if df is None or df.empty:
        return 0
    table = DATASET_TABLES.get(kind)
    if not table:
        return 0
    payload = df.copy()
    payload["ANIO"] = str(anio or "")
    payload["TRIMESTRE"] = str(trimestre or "")
    payload["LOTE_ID"] = str(lote_id or "")
    payload = payload.fillna("").astype(str)
    with sqlite3.connect(path) as con:
        if _table_exists(con, table):
            _ensure_dataframe_columns(con, table, payload.columns)
            con.execute(f'DELETE FROM "{table}" WHERE LOTE_ID=?', (str(lote_id or ""),))
        payload.to_sql(table, con, if_exists="append", index=False)
        con.commit()
    return len(payload)


def save_movements(path, df: pd.DataFrame, *, lote_id=""):
    init_db(path)
    if df is None or df.empty:
        return 0
    cols = [
        "MOVIMIENTO_ID","FUENTE","SOURCE_ROW","FINCA_ID","PROVINCIA","NUMERO","EXPEDIENTE_ID","DERECHO","FOLIO_REAL","TIPO_DERECHO","FOLIO_DERECHO",
        "FECHA_MOVIMIENTO","CODIGO_COMPLETO","OPERACION","CATEGORIA","TIPO_MOVIMIENTO",
        "CEDULA_NORM","TITULAR","NOMBRE_BUSQUEDA","NUM_PLANO_NORM","PRESENTACION","DESCRIP_OPER",
        "ANIO","TRIMESTRE"
    ]
    payload = df.copy()
    for col in cols:
        if col not in payload.columns:
            payload[col] = ""
    payload = payload[cols].fillna("").astype(str)
    with sqlite3.connect(path) as con:
        for _, row in payload.iterrows():
            values = row.to_dict() | {"LOTE_ID": str(lote_id or "")}
            con.execute("""
                INSERT INTO movimientos (
                    MOVIMIENTO_ID,FUENTE,SOURCE_ROW,FINCA_ID,PROVINCIA,NUMERO,EXPEDIENTE_ID,DERECHO,FOLIO_REAL,TIPO_DERECHO,FOLIO_DERECHO,
                    FECHA_MOVIMIENTO,CODIGO_COMPLETO,OPERACION,CATEGORIA,TIPO_MOVIMIENTO,
                    CEDULA_NORM,TITULAR,NOMBRE_BUSQUEDA,NUM_PLANO_NORM,PRESENTACION,DESCRIP_OPER,
                    ANIO,TRIMESTRE,LOTE_ID
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(MOVIMIENTO_ID) DO UPDATE SET
                    FUENTE=excluded.FUENTE, SOURCE_ROW=excluded.SOURCE_ROW, FINCA_ID=excluded.FINCA_ID, PROVINCIA=excluded.PROVINCIA, NUMERO=excluded.NUMERO, EXPEDIENTE_ID=excluded.EXPEDIENTE_ID,
                    DERECHO=excluded.DERECHO, FOLIO_REAL=excluded.FOLIO_REAL, TIPO_DERECHO=excluded.TIPO_DERECHO, FOLIO_DERECHO=excluded.FOLIO_DERECHO,
                    FECHA_MOVIMIENTO=excluded.FECHA_MOVIMIENTO, CODIGO_COMPLETO=excluded.CODIGO_COMPLETO,
                    OPERACION=excluded.OPERACION, CATEGORIA=excluded.CATEGORIA,
                    TIPO_MOVIMIENTO=excluded.TIPO_MOVIMIENTO, CEDULA_NORM=excluded.CEDULA_NORM,
                    TITULAR=excluded.TITULAR, NOMBRE_BUSQUEDA=excluded.NOMBRE_BUSQUEDA,
                    NUM_PLANO_NORM=excluded.NUM_PLANO_NORM, PRESENTACION=excluded.PRESENTACION,
                    DESCRIP_OPER=excluded.DESCRIP_OPER, ANIO=excluded.ANIO, TRIMESTRE=excluded.TRIMESTRE,
                    LOTE_ID=excluded.LOTE_ID
            """, tuple(values[c] for c in cols + ["LOTE_ID"]))
        con.commit()
    return len(payload)


def registered_ids(path):
    init_db(path)
    with sqlite3.connect(path) as con:
        return {r[0] for r in con.execute("SELECT MOVIMIENTO_ID FROM gestion_registrados")}


def mark_registered(path, movement: dict, *, usuario: str, observacion="", registrado_en=None, accion="REGISTRADO"):

    if not str(usuario or "").strip():
        raise ValueError("El usuario/operador es obligatorio")
    init_db(path)
    movement_id = str(movement.get("MOVIMIENTO_ID") or "").strip()
    if not movement_id:
        raise ValueError("MOVIMIENTO_ID es obligatorio")
    timestamp = registrado_en or _now_iso()
    payload_json = json.dumps(movement, ensure_ascii=False, default=str)
    cols = [
        "MOVIMIENTO_ID","EXPEDIENTE_ID","FINCA_ID","PROVINCIA","NUMERO","DERECHO","FOLIO_REAL","TIPO_DERECHO","FOLIO_DERECHO","CEDULA_NORM",
        "TITULAR","NOMBRE_BUSQUEDA","CODIGO_COMPLETO","OPERACION","CATEGORIA","TIPO_MOVIMIENTO",
        "FUENTE","FECHA_MOVIMIENTO","NUM_PLANO_NORM","ANIO","TRIMESTRE"
    ]
    values = [str(movement.get(c, "") or "") for c in cols]
    with sqlite3.connect(path) as con:
        cur = con.execute(f"""
            INSERT OR IGNORE INTO gestion_registrados (
                {','.join(cols)},REGISTRADO_POR,REGISTRADO_EN,OBSERVACION_REGISTRO,PAYLOAD_JSON
            ) VALUES ({','.join(['?'] * (len(cols)+4))})
        """, tuple(values + [str(usuario).strip(), timestamp, str(observacion or ""), payload_json]))
        inserted = cur.rowcount == 1
        if inserted:
            con.execute("""
                INSERT INTO auditoria (MOVIMIENTO_ID,EXPEDIENTE_ID,FOLIO_REAL,ACCION,USUARIO,FECHA_HORA,OBSERVACION)
                VALUES (?,?,?,?,?,?,?)
            """, (movement_id, str(movement.get("EXPEDIENTE_ID", "") or ""), str(movement.get("FOLIO_REAL", "") or ""), str(accion or "REGISTRADO"), str(usuario).strip(), timestamp, str(observacion or "")))
        con.commit()
    return inserted



def _folio_subset(movements: pd.DataFrame, folio_real: str) -> pd.DataFrame:
    if movements is None or movements.empty:
        return pd.DataFrame()
    folio_real = str(folio_real or "").strip()
    if not folio_real:
        return movements.iloc[0:0].copy()
    return movements[movements.get("FOLIO_REAL", pd.Series("", index=movements.index)).astype(str).str.strip().eq(folio_real)].copy()


def finalize_folio(path, movements: pd.DataFrame, *, folio_real: str, usuario: str, observacion="", finalizado_en=None):
    """Move only the selected real folio (Provincia-Finca-Derecho) to GESTIÓN."""
    subset = _folio_subset(movements, folio_real)
    if subset.empty:
        return 0
    existing = registered_ids(path)
    inserted = 0
    for _, row in subset.iterrows():
        movement = row.to_dict()
        mid = str(movement.get("MOVIMIENTO_ID") or "").strip()
        if not mid or mid in existing:
            continue
        if mark_registered(path, movement, usuario=usuario, observacion=observacion, registrado_en=finalizado_en, accion="FINALIZADO"):
            existing.add(mid)
            inserted += 1
    return inserted


def save_control_folio(path, movements: pd.DataFrame, *, folio_real: str, usuario: str, observacion="", guardado_en=None):
    """Persist a control bookmark/snapshot for exactly one real folio."""
    if not str(usuario or "").strip():
        raise ValueError("El usuario/operador es obligatorio")
    init_db(path)
    subset = _folio_subset(movements, folio_real)
    if subset.empty:
        return 0
    first = subset.iloc[0]
    timestamp = guardado_en or _now_iso()
    values = (
        str(folio_real), str(first.get("FINCA_ID", "") or ""), str(first.get("PROVINCIA", "") or ""),
        str(first.get("NUMERO", "") or first.get("EXPEDIENTE_ID", "") or ""), str(first.get("DERECHO", "") or ""),
        str(first.get("TIPO_DERECHO", "") or ""),
        " | ".join(sorted({str(x) for x in subset.get("NUM_PLANO_NORM", pd.Series(dtype=str)).fillna("").astype(str) if str(x).strip()})),
        " | ".join(sorted({str(x) for x in subset.get("TITULAR", pd.Series(dtype=str)).fillna("").astype(str) if str(x).strip()})),
        " | ".join(sorted({str(x) for x in subset.get("CEDULA_NORM", pd.Series(dtype=str)).fillna("").astype(str) if str(x).strip()})),
        int(len(subset)), str(usuario).strip(), timestamp, str(observacion or "")
    )
    with sqlite3.connect(path) as con:
        con.execute("""
            INSERT INTO folios_guardados (FOLIO_REAL,FINCA_ID,PROVINCIA,NUMERO,DERECHO,TIPO_DERECHO,NUM_PLANO_NORM,TITULAR,CEDULA_NORM,MOVIMIENTOS,GUARDADO_POR,GUARDADO_EN,OBSERVACION)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(FOLIO_REAL) DO UPDATE SET
                FINCA_ID=excluded.FINCA_ID, PROVINCIA=excluded.PROVINCIA, NUMERO=excluded.NUMERO, DERECHO=excluded.DERECHO,
                TIPO_DERECHO=excluded.TIPO_DERECHO, NUM_PLANO_NORM=excluded.NUM_PLANO_NORM, TITULAR=excluded.TITULAR,
                CEDULA_NORM=excluded.CEDULA_NORM, MOVIMIENTOS=excluded.MOVIMIENTOS, GUARDADO_POR=excluded.GUARDADO_POR,
                GUARDADO_EN=excluded.GUARDADO_EN, OBSERVACION=excluded.OBSERVACION
        """, values)
        con.execute("""
            INSERT INTO auditoria (MOVIMIENTO_ID,EXPEDIENTE_ID,FOLIO_REAL,ACCION,USUARIO,FECHA_HORA,OBSERVACION)
            VALUES (?,?,?,?,?,?,?)
        """, (f"FOLIO:{folio_real}", str(first.get("EXPEDIENTE_ID", "") or ""), str(folio_real), "GUARDADO", str(usuario).strip(), timestamp, str(observacion or "")))
        con.commit()
    return len(subset)


def list_saved_folios(path):
    init_db(path)
    with sqlite3.connect(path) as con:
        return pd.read_sql_query("SELECT * FROM folios_guardados ORDER BY GUARDADO_EN ASC, FOLIO_REAL ASC", con)


def delete_folio(path, *, folio_real: str, usuario: str, observacion="", eliminado_en=None):
    """Delete one folio from operational control/management only; source datasets remain intact."""
    if not str(usuario or "").strip():
        raise ValueError("El usuario/operador es obligatorio")
    folio_real = str(folio_real or "").strip()
    if not folio_real:
        raise ValueError("FOLIO_REAL es obligatorio")
    init_db(path)
    timestamp = eliminado_en or _now_iso()
    with sqlite3.connect(path) as con:
        row = con.execute("SELECT EXPEDIENTE_ID FROM movimientos WHERE FOLIO_REAL=? LIMIT 1", (folio_real,)).fetchone()
        expediente = row[0] if row else ""
        mov = con.execute("DELETE FROM movimientos WHERE FOLIO_REAL=?", (folio_real,)).rowcount
        gest = con.execute("DELETE FROM gestion_registrados WHERE FOLIO_REAL=?", (folio_real,)).rowcount
        saved = con.execute("DELETE FROM folios_guardados WHERE FOLIO_REAL=?", (folio_real,)).rowcount
        con.execute("""
            INSERT INTO auditoria (MOVIMIENTO_ID,EXPEDIENTE_ID,FOLIO_REAL,ACCION,USUARIO,FECHA_HORA,OBSERVACION)
            VALUES (?,?,?,?,?,?,?)
        """, (f"FOLIO:{folio_real}", str(expediente or ""), folio_real, "ELIMINADO", str(usuario).strip(), timestamp, str(observacion or "")))
        con.commit()
    return {"movimientos": int(mov), "gestion": int(gest), "guardados": int(saved)}


def finalize_finca(path, movements: pd.DataFrame, *, finca_id: str, usuario: str, observacion="", finalizado_en=None):
    """Move every pending movement of a real finca/folio real to GESTIÓN."""
    if movements is None or movements.empty:
        return 0
    finca_id = str(finca_id or "").strip()
    if not finca_id:
        raise ValueError("FINCA_ID es obligatorio")
    subset = movements[movements.get("FINCA_ID", pd.Series("", index=movements.index)).astype(str).str.strip().eq(finca_id)].copy()
    if subset.empty:
        return 0
    existing = registered_ids(path)
    inserted = 0
    for _, row in subset.iterrows():
        movement = row.to_dict()
        mid = str(movement.get("MOVIMIENTO_ID") or "").strip()
        if not mid or mid in existing:
            continue
        if mark_registered(
            path, movement, usuario=usuario, observacion=observacion,
            registrado_en=finalizado_en, accion="FINALIZADO"
        ):
            existing.add(mid)
            inserted += 1
    return inserted

def list_registered(path):
    init_db(path)
    with sqlite3.connect(path) as con:
        return pd.read_sql_query("SELECT * FROM gestion_registrados ORDER BY REGISTRADO_EN ASC, MOVIMIENTO_ID ASC", con)


def audit_history(path, *, movimiento_id="", expediente_id="", folio_real=""):
    init_db(path)
    sql = "SELECT * FROM auditoria WHERE 1=1"
    params = []
    if movimiento_id:
        sql += " AND MOVIMIENTO_ID=?"
        params.append(movimiento_id)
    if expediente_id:
        sql += " AND EXPEDIENTE_ID=?"
        params.append(expediente_id)
    if folio_real:
        sql += " AND FOLIO_REAL=?"
        params.append(folio_real)
    sql += " ORDER BY FECHA_HORA ASC, ID ASC"
    with sqlite3.connect(path) as con:
        return pd.read_sql_query(sql, con, params=params)


def import_registered_records(path, records: Iterable[dict], *, usuario_importacion="IMPORTACION"):
    init_db(path)
    inserted = 0
    existing = registered_ids(path)
    for record in records:
        movement_id = str(record.get("MOVIMIENTO_ID") or "").strip()
        if not movement_id or movement_id in existing:
            continue
        usuario = str(record.get("REGISTRADO_POR") or usuario_importacion or "IMPORTACION")
        timestamp = str(record.get("REGISTRADO_EN") or _now_iso())
        observacion = str(record.get("OBSERVACION_REGISTRO") or "Importado")
        if mark_registered(path, record, usuario=usuario, observacion=observacion, registrado_en=timestamp):
            with sqlite3.connect(path) as con:
                con.execute("UPDATE auditoria SET ACCION='IMPORTADO' WHERE MOVIMIENTO_ID=? AND FECHA_HORA=?", (movement_id, timestamp))
                con.commit()
            existing.add(movement_id)
            inserted += 1
    return inserted


def load_movements(path, *, anio="", trimestre=""):
    init_db(path)
    sql = "SELECT * FROM movimientos WHERE 1=1"
    params = []
    if anio:
        sql += " AND ANIO=?"
        params.append(str(anio))
    if trimestre:
        sql += " AND TRIMESTRE=?"
        params.append(str(trimestre))
    sql += " ORDER BY CASE WHEN FECHA_MOVIMIENTO='' THEN 1 ELSE 0 END, FECHA_MOVIMIENTO ASC, MOVIMIENTO_ID ASC"
    with sqlite3.connect(path) as con:
        return pd.read_sql_query(sql, con, params=params)


def load_dataset(path, kind, *, anio="", trimestre=""):
    init_db(path)
    table = DATASET_TABLES.get(kind)
    if not table:
        return pd.DataFrame()
    with sqlite3.connect(path) as con:
        if not _table_exists(con, table):
            return pd.DataFrame()
        sql = f'SELECT * FROM "{table}" WHERE 1=1'
        params = []
        cols = {r[1] for r in con.execute(f'PRAGMA table_info("{table}")')}
        if anio and "ANIO" in cols:
            sql += " AND ANIO=?"
            params.append(str(anio))
        if trimestre and "TRIMESTRE" in cols:
            sql += " AND TRIMESTRE=?"
            params.append(str(trimestre))
        return pd.read_sql_query(sql, con, params=params)
