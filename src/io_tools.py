import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

import pandas as pd


SUPPORTED_UPLOAD_EXTENSIONS = {".xls", ".txt", ".TXT"}


@dataclass
class MemoryUpload:
    name: str
    data: bytes

    def getvalue(self):
        return self.data


def expand_uploads(uploads):
    """Expand ZIPs into in-memory files while preserving ordinary uploads."""
    out = []
    for upload in uploads or []:
        name = getattr(upload, "name", "")
        suffix = PurePosixPath(name).suffix.lower()
        if suffix != ".zip":
            out.append(upload)
            continue
        with zipfile.ZipFile(io.BytesIO(upload.getvalue())) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                inner_name = PurePosixPath(info.filename).name
                if PurePosixPath(inner_name).suffix.lower() not in {".xls", ".txt"}:
                    continue
                out.append(MemoryUpload(inner_name, zf.read(info)))
    return out


def _records(records):
    if isinstance(records, pd.DataFrame):
        return records.fillna("").to_dict("records")
    return list(records or [])


def records_to_json_bytes(records):
    return json.dumps(_records(records), ensure_ascii=False, indent=2, default=str).encode("utf-8")


def records_to_excel_bytes(records):
    df = pd.DataFrame(_records(records)).fillna("")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="GESTION")
        ws = writer.sheets["GESTION"]
        if len(df.columns):
            for idx, col in enumerate(df.columns):
                width = min(45, max(12, len(str(col)) + 2))
                ws.set_column(idx, idx, width)
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, max(0, len(df)), len(df.columns) - 1)
    return buf.getvalue()


def read_management_import(upload):
    name = getattr(upload, "name", "").lower()
    data = upload.getvalue()
    if name.endswith(".json"):
        obj = json.loads(data.decode("utf-8-sig"))
        if isinstance(obj, dict):
            obj = obj.get("registros", obj.get("records", [obj]))
        if not isinstance(obj, list):
            raise ValueError("El JSON debe contener una lista de registros")
        return obj
    if name.endswith(".xlsx") or name.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(data), dtype=str, keep_default_na=False)
        return df.fillna("").to_dict("records")
    raise ValueError("Formato no soportado. Use JSON o XLSX")


def database_to_excel_bytes(db_path):
    import sqlite3
    sheet_names = {
        "resumen":"Resumen",
        "fincas_folios":"Fincas_Folios",
        "historicos":"Historicos",
        "gravamenes":"Gravamenes",
        "segregaciones":"Segregaciones",
        "anotaciones":"Anotaciones",
        "planos_control":"Planos_Control",
        "alertas":"Alertas",
        "top_operaciones":"Top_Operaciones",
        "catalogo_operaciones":"Catalogo_Operaciones",
        "manual_codigos":"Manual_Codigos",
        "gestion_registrados":"Gestion",
        "auditoria":"Auditoria",
        "movimientos":"Movimientos",
        "fincas_cerradas":"Fincas_Cerradas",
        "cedulas_juridicas":"Cedulas_Juridicas",
    }
    buf = io.BytesIO()
    with sqlite3.connect(db_path) as con, pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for table in tables:
            df = pd.read_sql_query(f'SELECT * FROM "{table}"', con)
            sheet = sheet_names.get(table, table[:31])[:31]
            df.to_excel(writer, index=False, sheet_name=sheet)
            ws = writer.sheets[sheet]
            if len(df.columns):
                ws.freeze_panes(1, 0)
                ws.autofilter(0, 0, max(0, len(df)), len(df.columns) - 1)
                for idx, col in enumerate(df.columns):
                    sample = df[col].astype(str).head(100).map(len).max() if len(df) else 0
                    width = min(48, max(12, len(str(col)) + 2, int(sample) + 2 if pd.notna(sample) else 12))
                    ws.set_column(idx, idx, width)
    return buf.getvalue()
