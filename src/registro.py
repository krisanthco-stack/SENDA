import csv, io, re
from collections import defaultdict
import pandas as pd

ENCODINGS = ("utf-8-sig", "cp850", "latin1", "cp1252")

def decode_bytes(data: bytes):
    for enc in ENCODINGS:
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return data.decode("latin1", errors="replace"), "latin1-replace"

def read_tabular_upload(upload):
    data = upload.getvalue()
    text, enc = decode_bytes(data)
    name = upload.name.lower()
    if "catalogo" in name:
        rows = list(csv.reader(io.StringIO(text), delimiter=";", quotechar='"'))
        return pd.DataFrame(rows), enc
    return pd.read_csv(io.StringIO(text), sep="\t", dtype=str, keep_default_na=False), enc

def clean(s):
    return "" if s is None else str(s).strip()

def only_digits(s):
    return re.sub(r"\D", "", clean(s))

def finca_id_df(df):
    for c in ["PROVINCIA","CANTON","DISTRITO","NUMERO","DUPLICADO","HORIZONTAL"]:
        if c not in df.columns: df[c] = ""
    base = df["PROVINCIA"].map(clean)+"-"+df["CANTON"].map(clean)+"-"+df["DISTRITO"].map(clean)+"-"+df["NUMERO"].map(clean)
    dup = df["DUPLICADO"].map(clean)
    hor = df["HORIZONTAL"].map(clean)
    base = base + dup.map(lambda x: f"-DUP{x}" if x else "") + hor.map(lambda x: f"-H{x}" if x else "")
    return base

def load_operation_catalog(path_or_text):
    if hasattr(path_or_text, "read"):
        text = path_or_text.read()
    else:
        with open(path_or_text, "rb") as f: text = f.read()
    if isinstance(text, bytes): text,_ = decode_bytes(text)
    out={}
    for r in csv.reader(io.StringIO(text), delimiter=";", quotechar='"'):
        if len(r)>=3: out[(clean(r[0]),clean(r[1]))]=clean(r[2])
    return out

def split_operation(code, opmap):
    code=clean(code)
    if len(code)>=2 and code[-1].isdigit() and (code[:-1], code[-1]) in opmap:
        return code[:-1], code[-1]
    return code, ""

def classify(desc):
    t=clean(desc).upper()
    if "SEGREGACION" in t: return "SEGREGACION"
    if "DIVISION MATERIAL" in t: return "DIVISION MATERIAL"
    if "REUNION" in t: return "REUNION / AGRUPACION"
    if "CIERRE" in t: return "CIERRE"
    if any(x in t for x in ["HIPOTECA","EMBARGO","SERVIDUMBRE","LIMITACION","DEMANDA","INMOVILIZACION","HABITACION FAMILIAR","ARRENDAMIENTO","GRAVAMEN","CONCESION","PREVENCION","ANOTACION","PROHIBICION"]):
        return "GRAVAMEN / AFECTACION"
    if any(x in t for x in ["COMPRAVENTA","DONACION","ADJUDICACION","TRASPASO","APORTE","PERMUTA","DACION","RETROVENTA","CESION"]):
        return "TRASPASO / TITULARIDAD"
    if any(x in t for x in ["RECTIFICACION","MODIFICACION","INCLUSION","EXCLUSION","SUSTITUCION"]):
        return "MODIFICACION / RECTIFICACION"
    if any(x in t for x in ["CANCELACION","CANCELADA","RENUNCIA"]):
        return "CANCELACION / RENUNCIA"
    return "OTRO"

def classify_filename(name):
    n=name.lower()
    rules=[("anotaciones","Anotaciones"),("segregaciones","Segregaciones"),("gravamenes","Gravamenes"),("historicos","Historicos"),("cerradas","Cerradas"),("ced_juridicas","Cedulas Juridicas"),("fincas","Fincas"),("catalogo","Catalogo")]
    for k,v in rules:
        if k in n: return v
    return "Otro"

def normalize_dataset(kind, df, opmap):
    out=df.copy()
    if all(c in out.columns for c in ["PROVINCIA","CANTON","DISTRITO","NUMERO"]):
        out.insert(0,"FINCA_ID",finca_id_df(out))
    if "DERECHO" in out.columns and "FINCA_ID" in out.columns:
        out.insert(1,"FOLIO_DERECHO",out["FINCA_ID"]+out["DERECHO"].map(lambda x: f"-DER{clean(x)}" if clean(x) else ""))
    if kind=="Historicos" and {"COD_OPER","CLASE_CODIGO"}.issubset(out.columns):
        out["CODIGO_COMPLETO"]=out["COD_OPER"].map(clean)+out["CLASE_CODIGO"].map(clean)
        out["OPERACION"]=out.apply(lambda r: clean(r.get("DESCRIP_OPER")) or opmap.get((clean(r.get("COD_OPER")),clean(r.get("CLASE_CODIGO"))),""), axis=1)
        out["CATEGORIA"]=out["OPERACION"].map(classify)
    elif "COD_OPERACION" in out.columns:
        pairs=out["COD_OPERACION"].map(lambda x: split_operation(x,opmap))
        out["CODIGO_BASE"]=[p[0] for p in pairs]
        out["CLASE"]=[p[1] for p in pairs]
        out["OPERACION"]=[opmap.get(p,"") for p in pairs]
        out["CATEGORIA"]=out["OPERACION"].map(classify)
    elif "DESCRIP_OPER" in out.columns:
        out["OPERACION"]=out["DESCRIP_OPER"].map(clean)
        out["CATEGORIA"]=out["OPERACION"].map(classify)
    if "NUM_PLANO" in out.columns: out["NUM_PLANO_NORM"]=out["NUM_PLANO"].map(only_digits)
    return out

def planos_sin_finca(datasets):
    plans=set()
    for k in ("Fincas","Cerradas"):
        if k in datasets and "NUM_PLANO_NORM" in datasets[k].columns:
            plans.update(x for x in datasets[k]["NUM_PLANO_NORM"] if x)
    if "Segregaciones" not in datasets or "NUM_PLANO_NORM" not in datasets["Segregaciones"].columns:
        return pd.DataFrame(columns=["NUM_PLANO","FINCA_REFERENCIADA","RESULTADO"])
    s=datasets["Segregaciones"]
    bad=s[(s["NUM_PLANO_NORM"]!="") & (~s["NUM_PLANO_NORM"].isin(plans))].copy()
    if bad.empty: return pd.DataFrame(columns=["NUM_PLANO","FINCA_REFERENCIADA","RESULTADO"])
    return bad[["NUM_PLANO_NORM","FINCA_ID"]].drop_duplicates().rename(columns={"NUM_PLANO_NORM":"NUM_PLANO","FINCA_ID":"FINCA_REFERENCIADA"}).assign(RESULTADO="PLANO SIN FINCA LOCALIZADA")
