# -*- coding: utf-8 -*-
"""
PANEL DE MATRICULADOS 2026
Tablero interactivo de Business Intelligence sobre la matricula academica 2026.

Ejecucion:
    python app.py

El script se relanza solo dentro del runtime de Streamlit, levanta el servidor
local y abre el navegador en http://localhost:8501 (o el primer puerto libre).
"""

from __future__ import annotations

import os
import sys
import socket
import threading
import webbrowser
import unicodedata
import hashlib
import io
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# 0. BOOTSTRAP: permite "python app.py" sin escribir "streamlit run"
# ---------------------------------------------------------------------------

DEFAULT_PORT = 8501


def _running_inside_streamlit() -> bool:
    """True si el script ya esta siendo ejecutado por el runtime de Streamlit."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
        return get_script_run_ctx() is not None
    except Exception:
        try:
            from streamlit.runtime import exists  # type: ignore
            return bool(exists())
        except Exception:
            return False


def _first_free_port(start: int = DEFAULT_PORT, tries: int = 25) -> int:
    for offset in range(tries):
        port = start + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def _launch() -> None:
    """Levanta el servidor Streamlit y abre el navegador."""
    from streamlit.web import cli as stcli  # type: ignore

    port = _first_free_port()
    url = f"http://localhost:{port}"

    banner = (
        "\n"
        "  PANEL DE MATRICULADOS 2026\n"
        "  ---------------------------------------------\n"
        f"  Servidor local  : {url}\n"
        "  Detener         : Ctrl + C\n"
        "  ---------------------------------------------\n"
    )
    print(banner, flush=True)

    threading.Timer(2.2, lambda: webbrowser.open_new_tab(url)).start()

    sys.argv = [
        "streamlit",
        "run",
        os.path.abspath(__file__),
        "--server.port", str(port),
        "--server.address", "localhost",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
        "--theme.base", "light",
        "--client.toolbarMode", "minimal",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__" and not _running_inside_streamlit():
    _launch()


# ---------------------------------------------------------------------------
# 1. IMPORTS DE LA APLICACION
# ---------------------------------------------------------------------------

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(APP_DIR, "assets", "sedes")

st.set_page_config(
    page_title="Panel de Matriculados 2026",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 2. PALETA Y TOKENS DE DISENO
# ---------------------------------------------------------------------------

LIGHT = {
    "primary": "#1D3461",
    "primary_soft": "#2B4A85",
    "accent": "#2CA6A4",
    "accent_alt": "#2563EB",
    "bg": "#F1F4F9",
    "surface": "#FFFFFF",
    "surface_alt": "#F7F9FC",
    "border": "#E6E9F0",
    "text": "#1B2333",
    "text_muted": "#63708B",
    "sidebar": "#0F1E38",
    "sidebar_text": "#E8EDF7",
    "grid": "#E6E9F0",
    "map_style": "carto-positron",
    "ok": "#16A34A",
    "warn": "#D97706",
    "risk": "#DC2626",
}

DARK = {
    "primary": "#3B6FD4",
    "primary_soft": "#274A76",
    "accent": "#2CA6A4",
    "accent_alt": "#60A5FA",
    "bg": "#0F172A",
    "surface": "#16223C",
    "surface_alt": "#1B2947",
    "border": "#27385C",
    "text": "#E8EDF7",
    "text_muted": "#9AAAC6",
    "sidebar": "#0A1527",
    "sidebar_text": "#E8EDF7",
    "grid": "#27385C",
    "map_style": "carto-darkmatter",
    "ok": "#34D399",
    "warn": "#FBBF24",
    "risk": "#F87171",
}

SERIES = ["#1D3461", "#2CA6A4", "#2563EB", "#7C3AED", "#F59E0B", "#DB2777", "#0EA5E9", "#059669"]
SERIES_DARK = ["#5B8DEF", "#2CA6A4", "#60A5FA", "#A78BFA", "#FBBF24", "#F472B6", "#38BDF8", "#34D399"]

SEX_COLORS = {"FEMENINO": "#DB2777", "MASCULINO": "#2563EB", "NO REGISTRA": "#94A3B8"}


def T() -> dict:
    """Tokens del tema activo."""
    return DARK if st.session_state.get("dark_mode", False) else LIGHT


def palette() -> list:
    return SERIES_DARK if st.session_state.get("dark_mode", False) else SERIES


# ---------------------------------------------------------------------------
# 3. GEOREFERENCIA DE SEDES
# ---------------------------------------------------------------------------

CAMPUS_COORDS = {
    "FRATERNIDAD MEDELLIN": (6.2385, -75.5657, "Medellin", "Boston"),
    "ROBLEDO": (6.2795, -75.5903, "Medellin", "Robledo"),
    "FLORESTA": (6.2560, -75.6021, "Medellin", "La Floresta"),
    "CASTILLA": (6.2905, -75.5730, "Medellin", "Castilla"),
    "CAMPUS C4TA": (6.2702, -75.5653, "Medellin", "Sevilla"),
    "UEMB CASTILLA": (6.2905, -75.5735, "Medellin", "Castilla"),
}

MUNICIPIOS = {
    "MEDELLIN": (6.2442, -75.5812),
    "BELLO": (6.3378, -75.5583),
    "CAREPA": (7.7556, -76.6556),
    "EL PENOL": (6.2200, -75.2436),
    "VALPARAISO": (5.6147, -75.6244),
    "SONSON": (5.7108, -75.3106),
    "JARDIN": (5.5981, -75.8194),
    "BELMIRA": (6.6053, -75.6672),
    "TARSO": (5.8639, -75.8236),
    "MACEO": (6.5519, -74.7867),
    "BETANIA": (5.7461, -75.9772),
    "ANDES": (5.6578, -75.8792),
    "HISPANIA": (5.7992, -75.9075),
    "GOMEZ PLATA": (6.6822, -75.2211),
    "NODO GOMEZ PLATA": (6.6822, -75.2211),
    "CANAS GORDAS": (6.7514, -76.0272),
    "BETULIA": (6.1153, -75.9842),
    "URRAO": (6.3172, -76.1331),
    "ITUANGO": (7.1708, -75.7644),
    "EBEJICO": (6.3258, -75.7669),
    "SAN JERONIMO": (6.4433, -75.7275),
    "ANGOSTURA": (6.8847, -75.3353),
    "BRICENO": (7.1119, -75.5511),
    "CAROLINA DEL PRINCIPE": (6.7261, -75.2822),
    "DONMATIAS": (6.4856, -75.3906),
    "YOLOMBO": (6.5936, -75.0136),
    "CISNEROS": (6.5386, -75.0872),
    "CAUCASIA": (7.9861, -75.1981),
    "VALDIVIA": (7.1636, -75.4392),
    "VEGACHI": (6.7739, -74.7986),
    "NODO VEGACHI": (6.7739, -74.7986),
    "TARAZA": (7.5817, -75.4000),
}

BARRIOS_MEDELLIN = {
    "SAN ANTONIO DE PRADO": (6.1861, -75.6564),
    "JORGE ROBLEDO": (6.2758, -75.5885),
    "MONTECARLO GUILLERMO GAVIRIA CORREA": (6.2262, -75.6001),
    "ALCALDIA DE MEDELLIN": (6.2518, -75.5636),
    "VILLA DEL SOCORRO": (6.2975, -75.5533),
    "MANUELA BELTRAN": (6.2419, -75.5478),
    "JOSE MARIA BRAVO": (6.2364, -75.5478),
    "ENRIQUE OLAYA HERRERA": (6.2314, -75.5944),
    "LA ESPERANZA": (6.2989, -75.5486),
    "FE Y ALEGRIA LA CIMA": (6.3033, -75.5450),
    "JUAN J. ESCOBAR": (6.2597, -75.5378),
    "JUAN J. ESCOBAR SAN CRISTOBAL": (6.2800, -75.6400),
    "CASD": (6.2394, -75.5786),
    "RAFAEL URIBE URIBE": (6.2452, -75.5751),
    "JOSE ANTONIO GALAN": (6.2950, -75.5801),
    "MANUEL J. BETANCUR": (6.1852, -75.6552),
    "MIRAFLORES": (6.2452, -75.5502),
    "ASAMBLEA DEPARTAMENTAL": (6.2831, -75.5601),
    "LA SALLE DE CAMPOAMOR": (6.2203, -75.5881),
    "GABRIELA GOMEZ CARVAJAL": (6.2901, -75.5601),
    "ROSALIA SUAREZ": (6.2852, -75.5452),
    "GUADALUPE": (6.2932, -75.5671),
    "GILBERTO ALZATE AVENDANO": (6.2812, -75.5921),
}

MEDELLIN_CENTER = (6.2442, -75.5812)


def strip_accents(text: str) -> str:
    if not isinstance(text, str):
        return ""
    norm = unicodedata.normalize("NFKD", text)
    return "".join(c for c in norm if not unicodedata.combining(c))


def classify_sede(name: str) -> str:
    up = strip_accents(str(name)).upper().strip()
    if up.startswith("UEMB"):
        return "Universidad en mi barrio"
    if up.startswith("UEMR"):
        return "Universidad en mi region"
    if "VIRTUAL" in up:
        return "Campus virtual"
    if "MOVILIDAD" in up:
        return "Movilidad academica"
    return "Campus principal"


def locate_sede(name: str):
    """Devuelve (lat, lon, ciudad, referencia, es_aproximada)."""
    up = strip_accents(str(name)).upper().strip()
    up = re.sub(r"\s+", " ", up)

    if up in CAMPUS_COORDS:
        lat, lon, city, ref = CAMPUS_COORDS[up]
        return lat, lon, city, ref, False

    tail = up
    for prefix in ("UEMB - I.E ", "UEMB - I.E. ", "UEMB- I.E. ", "UEMB - ", "UEMB- ", "UEMB ",
                   "UEMR - ", "UEMR- ", "UEMR "):
        if up.startswith(prefix):
            tail = up[len(prefix):].strip()
            break

    if up.startswith("UEMR"):
        if tail in MUNICIPIOS:
            lat, lon = MUNICIPIOS[tail]
            return lat, lon, tail.title(), "Universidad en mi region", False
        for key, (lat, lon) in MUNICIPIOS.items():
            if key in tail or tail in key:
                return lat, lon, key.title(), "Universidad en mi region", False

    if up.startswith("UEMB"):
        if tail in BARRIOS_MEDELLIN:
            lat, lon = BARRIOS_MEDELLIN[tail]
            return lat, lon, "Medellin", tail.title(), False
        for key, (lat, lon) in BARRIOS_MEDELLIN.items():
            if key in tail or tail in key:
                return lat, lon, "Medellin", key.title(), False
        return MEDELLIN_CENTER[0], MEDELLIN_CENTER[1], "Medellin", tail.title(), True

    if "VIRTUAL" in up or "MOVILIDAD" in up:
        return None, None, "Sin sede fisica", "Modalidad remota", False

    if tail in MUNICIPIOS:
        lat, lon = MUNICIPIOS[tail]
        return lat, lon, tail.title(), "Sede", False

    return MEDELLIN_CENTER[0], MEDELLIN_CENTER[1], "Medellin", "Ubicacion aproximada", True


# ---------------------------------------------------------------------------
# 4. CARGA Y PREPARACION DE DATOS
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = [
    "Ano", "Barrio", "Comuna", "Ciudad Nacimiento", "Pais Nacimiento", "Id Estrato",
    "Nombre Programa", "Sexo", "Tipo Inscripcion", "Sede", "Facultad",
    "Area Conocimiento", "Colegio_Procedencia", "Tipo_Colegio", "Modalidad", "Tipo Programa",
]

CANDIDATE_FILES = [
    "matriculados_2026_limpio.csv",
    "matriculados_2026.csv",
    "matriculados.csv",
]


def find_dataset() -> str | None:
    search_dirs = [APP_DIR, os.path.join(APP_DIR, "data"), os.getcwd()]
    for folder in search_dirs:
        if not os.path.isdir(folder):
            continue
        for candidate in CANDIDATE_FILES:
            path = os.path.join(folder, candidate)
            if os.path.isfile(path):
                return path
    for folder in search_dirs:
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            low = fname.lower()
            if low.endswith(".csv") and ("matricul" in low or "estudiant" in low):
                return os.path.join(folder, fname)
    return None


def _read_csv(source) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        for sep in (",", ";"):
            try:
                if hasattr(source, "seek"):
                    source.seek(0)
                frame = pd.read_csv(source, encoding=enc, sep=sep, dtype=str)
                if frame.shape[1] >= 5:
                    return frame
            except Exception as exc:  # pragma: no cover
                last_error = exc
    raise ValueError(f"No fue posible leer el archivo. Detalle: {last_error}")


@st.cache_data(show_spinner=False)
def load_data(path_or_bytes, signature: str) -> pd.DataFrame:
    """Lee el CSV y construye las columnas derivadas del tablero."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        raw = _read_csv(io.BytesIO(path_or_bytes))
    else:
        raw = _read_csv(path_or_bytes)

    raw.columns = [str(c).replace("\ufeff", "").strip() for c in raw.columns]
    df = raw.copy()

    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    text_cols = [c for c in df.columns if df[c].dtype == object]
    for col in text_cols:
        df[col] = df[col].astype("string").str.strip()
        df[col] = df[col].replace({"": pd.NA, "NAN": pd.NA, "nan": pd.NA, "NULL": pd.NA, "-": pd.NA})

    df["Id Estrato"] = pd.to_numeric(df["Id Estrato"], errors="coerce")
    df["Ano"] = pd.to_numeric(df["Ano"], errors="coerce").astype("Int64")

    # --- Columnas derivadas -------------------------------------------------
    df["Sede"] = df["Sede"].fillna("SIN REGISTRO")
    df["Tipo Sede"] = df["Sede"].map(classify_sede)

    geo = df["Sede"].drop_duplicates().to_frame("Sede")
    located = geo["Sede"].map(locate_sede)
    geo["lat"] = [v[0] for v in located]
    geo["lon"] = [v[1] for v in located]
    geo["Ciudad Sede"] = [v[2] for v in located]
    geo["Referencia"] = [v[3] for v in located]
    geo["Geo aproximada"] = [v[4] for v in located]
    df = df.merge(geo, on="Sede", how="left")

    df["Estrato"] = df["Id Estrato"].apply(
        lambda v: "Sin dato" if pd.isna(v) or v == 0 else f"Estrato {int(v)}"
    )
    df["Nivel"] = df["Tipo Programa"].fillna("SIN REGISTRO").str.title()
    df["Modalidad"] = df["Modalidad"].fillna("SIN REGISTRO")
    df["Sexo"] = df["Sexo"].fillna("NO REGISTRA")
    df["Facultad"] = df["Facultad"].fillna("SIN REGISTRO")
    df["Facultad corta"] = (
        df["Facultad"]
        .str.replace("FACULTAD DE ", "", regex=False)
        .str.title()
    )
    df["Nombre Programa"] = df["Nombre Programa"].fillna("SIN REGISTRO")
    df["Programa corto"] = df["Nombre Programa"].apply(
        lambda s: (s[:46] + "...") if isinstance(s, str) and len(s) > 49 else s
    )
    df["Origen"] = np.where(
        df["Pais Nacimiento"].fillna("").str.upper().str.contains("COLOMBIA"),
        "Nacional", "Internacional",
    )
    df["Es Medellin"] = df["Ciudad Nacimiento"].fillna("").map(
        lambda s: strip_accents(s).upper().startswith("MEDELLIN")
    )

    # Indicadores de calidad por fila
    quality_cols = ["Barrio", "Comuna", "Colegio_Procedencia", "Tipo_Colegio", "Sexo", "Nombre Programa"]
    df["Campos faltantes"] = df[quality_cols].isna().sum(axis=1)
    df["Registro completo"] = df["Campos faltantes"] == 0

    df = df.reset_index(drop=True)
    df.insert(0, "ID", ["M26-" + str(i + 1).zfill(5) for i in range(len(df))])
    return df


@st.cache_data(show_spinner=False)
def sede_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen por sede usado en mapa, catalogo y comparador."""
    grp = df.groupby("Sede", dropna=False)
    out = pd.DataFrame({
        "Estudiantes": grp.size(),
        "Programas": grp["Nombre Programa"].nunique(),
        "Facultades": grp["Facultad"].nunique(),
        "Estrato promedio": grp["Id Estrato"].mean().round(2),
        "lat": grp["lat"].first(),
        "lon": grp["lon"].first(),
        "Ciudad Sede": grp["Ciudad Sede"].first(),
        "Referencia": grp["Referencia"].first(),
        "Tipo Sede": grp["Tipo Sede"].first(),
        "Geo aproximada": grp["Geo aproximada"].first(),
    }).reset_index()

    fem = df[df["Sexo"] == "FEMENINO"].groupby("Sede").size()
    mas = df[df["Sexo"] == "MASCULINO"].groupby("Sede").size()
    out["Femenino"] = out["Sede"].map(fem).fillna(0).astype(int)
    out["Masculino"] = out["Sede"].map(mas).fillna(0).astype(int)
    out["% Femenino"] = (out["Femenino"] / out["Estudiantes"] * 100).round(1)
    out["% Masculino"] = (out["Masculino"] / out["Estudiantes"] * 100).round(1)

    virt = df[df["Modalidad"] == "VIRTUAL"].groupby("Sede").size()
    out["Virtuales"] = out["Sede"].map(virt).fillna(0).astype(int)
    out["% Virtual"] = (out["Virtuales"] / out["Estudiantes"] * 100).round(1)

    top_fac = grp["Facultad corta"].agg(lambda s: s.value_counts().idxmax() if len(s) else "Sin dato")
    top_prog = grp["Nombre Programa"].agg(lambda s: s.value_counts().idxmax() if len(s) else "Sin dato")
    out["Facultad lider"] = out["Sede"].map(top_fac)
    out["Programa lider"] = out["Sede"].map(top_prog)

    out["Participacion"] = (out["Estudiantes"] / out["Estudiantes"].sum() * 100).round(2)
    return out.sort_values("Estudiantes", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def quality_report(df: pd.DataFrame) -> dict:
    audit_cols = [c for c in EXPECTED_COLUMNS if c in df.columns]
    nulls = df[audit_cols].isna().sum().sort_values(ascending=False)
    dup_mask = df.duplicated(subset=audit_cols, keep=False)
    return {
        "total": int(len(df)),
        "completos": int(df["Registro completo"].sum()),
        "incompletos": int((~df["Registro completo"]).sum()),
        "duplicados": int(dup_mask.sum()),
        "duplicados_unicos": int(df.duplicated(subset=audit_cols, keep="first").sum()),
        "nulos_por_columna": nulls,
        "mask_duplicados": dup_mask,
        "columnas": audit_cols,
    }


# ---------------------------------------------------------------------------
# 5. CAPA VISUAL (CSS)
# ---------------------------------------------------------------------------

from string import Template

CSS_TEMPLATE = Template("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@500;600;700&display=swap');

:root {
  --c-primary: $primary;
  --c-primary-soft: $primary_soft;
  --c-accent: $accent;
  --c-accent-alt: $accent_alt;
  --c-bg: $bg;
  --c-surface: $surface;
  --c-surface-alt: $surface_alt;
  --c-border: $border;
  --c-text: $text;
  --c-muted: $text_muted;
  --c-sidebar: $sidebar;
  --c-ok: $ok;
  --c-warn: $warn;
  --c-risk: $risk;
  --radius: 14px;
  --shadow: 0 1px 2px rgba(15,30,56,.04), 0 8px 24px rgba(15,30,56,.06);
}

html, body, [class*="css"], .stApp, section.main {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.stApp { background: var(--c-bg); color: var(--c-text); }
header[data-testid="stHeader"], .stAppHeader {
  background: transparent !important; backdrop-filter: none; height: 2.4rem;
}
.block-container { padding-top: 3.1rem; padding-bottom: 3.2rem; max-width: 1560px; }

h1, h2, h3, h4 { font-family: 'Sora', 'Inter', sans-serif; color: var(--c-text); letter-spacing: -.015em; }
p, span, label, div { color: var(--c-text); }

/* ---------------- Sidebar ---------------- */
section[data-testid="stSidebar"] { background: var(--c-sidebar); border-right: 1px solid rgba(255,255,255,.06); }
section[data-testid="stSidebar"] * { color: #E8EDF7; }
section[data-testid="stSidebar"] .block-container { padding-top: 1.2rem; }

.brand { display:flex; align-items:center; gap:.7rem; padding: .2rem .1rem 1.1rem .1rem; }
.brand-mark {
  width:40px; height:40px; border-radius:11px; flex:0 0 40px;
  background: linear-gradient(140deg, var(--c-accent) 0%, #2563EB 100%);
  display:flex; align-items:center; justify-content:center;
  font-family:'Sora',sans-serif; font-weight:700; font-size:15px; color:#fff;
  box-shadow: 0 6px 18px rgba(44,166,164,.35);
}
.brand-title { font-family:'Sora',sans-serif; font-weight:600; font-size:15px; line-height:1.15; color:#FFFFFF; }
.brand-sub { font-size:11.5px; color:#8FA3C6; margin-top:2px; letter-spacing:.02em; }

.nav-label { font-size:10.5px; letter-spacing:.12em; color:#6F84AA; margin: .9rem 0 .35rem .15rem; text-transform:uppercase; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div {
  width:100%; border-radius:9px; border:1px solid transparent;
  transition: background .15s ease, border-color .15s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > div:hover { background: rgba(255,255,255,.07); }
section[data-testid="stSidebar"] div[role="radiogroup"] > div[data-selected="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] > div:has(input:checked) {
  background: linear-gradient(90deg, rgba(44,166,164,.26), rgba(37,99,235,.08));
  border-color: rgba(44,166,164,.45);
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] {
  padding:.5rem .7rem; margin:0; width:100%; cursor:pointer;
}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child { display:none !important; }
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] p {
  font-size:13.4px; font-weight:500; color:#C3D1E9 !important;
}
section[data-testid="stSidebar"] div[data-selected="true"] label[data-testid="stRadioOption"] p,
section[data-testid="stSidebar"] div:has(input:checked) > label[data-testid="stRadioOption"] p {
  color:#FFFFFF !important; font-weight:600;
}

section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
  background: rgba(255,255,255,.07); border-color: rgba(255,255,255,.14); color:#fff;
}
.side-foot { margin-top:1rem; padding-top:.8rem; border-top:1px solid rgba(255,255,255,.09); font-size:11px; color:#7B90B5; }

/* ---------------- Encabezado ---------------- */
.page-head {
  display:flex; justify-content:space-between; align-items:flex-end; gap:1rem;
  padding: 0 0 1.05rem 0; margin-bottom: 1.1rem; border-bottom: 1px solid var(--c-border);
}
.page-title { font-family:'Sora',sans-serif; font-size:27px; font-weight:600; margin:0; line-height:1.2; }
.page-sub { color: var(--c-muted); font-size:13.5px; margin-top:.35rem; }
.stamp {
  background: var(--c-surface); border:1px solid var(--c-border); border-radius:10px;
  padding:.5rem .85rem; font-size:12px; color:var(--c-muted); white-space:nowrap; box-shadow: var(--shadow);
}
.stamp b { color: var(--c-text); font-weight:600; }

/* ---------------- Tarjetas KPI ---------------- */
.kpi {
  background: var(--c-surface); border:1px solid var(--c-border); border-radius: var(--radius);
  padding: 1rem 1.1rem 1.05rem 1.25rem; position:relative; overflow:hidden;
  height:100%; min-height:118px; box-shadow: var(--shadow);
}
.kpi::before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background: var(--kpi-accent, var(--c-primary)); }
.kpi-label { font-size:11.5px; letter-spacing:.06em; color:var(--c-muted); font-weight:600; }
.kpi-value { font-family:'Sora',sans-serif; font-size:31px; font-weight:600; line-height:1.12; margin:.32rem 0 .1rem; letter-spacing:-.02em; }
.kpi-foot { font-size:12px; color:var(--c-muted); }
.chip { display:inline-block; padding:.12rem .45rem; border-radius:6px; font-size:11px; font-weight:600; margin-right:.35rem; }
.chip-up { background: rgba(22,163,74,.12); color: var(--c-ok); }
.chip-flat { background: rgba(37,99,235,.12); color: var(--c-accent-alt); }
.chip-warn { background: rgba(217,119,6,.14); color: var(--c-warn); }
.chip-risk { background: rgba(220,38,38,.12); color: var(--c-risk); }

/* ---------------- Paneles ---------------- */
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--c-surface); border:1px solid var(--c-border) !important;
  border-radius: var(--radius); box-shadow: var(--shadow);
}
div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: .25rem .35rem; }
.panel {
  background: var(--c-surface); border:1px solid var(--c-border); border-radius: var(--radius);
  padding: 1.1rem 1.2rem; box-shadow: var(--shadow); height:100%;
}
.panel-title { font-family:'Sora',sans-serif; font-size:15px; font-weight:600; margin:0 0 .15rem 0; }
.panel-sub { font-size:12.5px; color: var(--c-muted); margin-bottom:.7rem; }
.section-title { font-family:'Sora',sans-serif; font-size:17px; font-weight:600; margin: 1.4rem 0 .15rem; }
.section-sub { font-size:12.8px; color:var(--c-muted); margin-bottom:.85rem; }

/* ---------------- Tarjetas de sede ---------------- */
.sede-card {
  background: var(--c-surface); border:1px solid var(--c-border); border-radius: var(--radius);
  overflow:hidden; box-shadow: var(--shadow); margin-bottom:.55rem;
}
.sede-banner { height:104px; position:relative; display:flex; align-items:flex-end; padding:.7rem .9rem; }
.sede-banner .tag {
  position:absolute; top:.6rem; right:.6rem; background: rgba(255,255,255,.92); color:#1B2333;
  font-size:10.5px; font-weight:700; padding:.18rem .5rem; border-radius:6px; letter-spacing:.03em;
}
.sede-banner .initials { font-family:'Sora',sans-serif; font-size:30px; font-weight:700; color:rgba(255,255,255,.95); line-height:1; }
.sede-body { padding:.85rem .95rem 1rem; }
.sede-name { font-family:'Sora',sans-serif; font-size:14.5px; font-weight:600; line-height:1.25; }
.sede-city { font-size:12px; color:var(--c-muted); margin-top:.12rem; }
.sede-metrics { display:flex; gap:1.3rem; margin-top:.75rem; }
.metric-mini .v { font-family:'Sora',sans-serif; font-size:18px; font-weight:600; line-height:1; }
.metric-mini .k { font-size:11px; color:var(--c-muted); margin-top:.18rem; }
.bar-track { height:6px; background: var(--c-surface-alt); border-radius:99px; overflow:hidden; margin-top:.8rem; border:1px solid var(--c-border); }
.bar-fill { height:100%; background: linear-gradient(90deg, var(--c-accent), var(--c-accent-alt)); }

/* ---------------- Insights y alertas ---------------- */
.insight {
  background: var(--c-surface); border:1px solid var(--c-border); border-left:4px solid var(--c-accent);
  border-radius: 12px; padding:.95rem 1.05rem; box-shadow: var(--shadow); height:100%;
}
.insight .k { font-size:10.5px; letter-spacing:.1em; color:var(--c-accent); font-weight:700; text-transform:uppercase; }
.insight .t { font-family:'Sora',sans-serif; font-size:15px; font-weight:600; margin:.35rem 0 .3rem; line-height:1.3; }
.insight .d { font-size:12.8px; color:var(--c-muted); line-height:1.5; }

.alert { border-radius:12px; padding:.85rem 1rem; border:1px solid var(--c-border); background:var(--c-surface); margin-bottom:.6rem; box-shadow: var(--shadow); }
.alert.ok { border-left:4px solid var(--c-ok); }
.alert.warn { border-left:4px solid var(--c-warn); }
.alert.risk { border-left:4px solid var(--c-risk); }
.alert .h { font-weight:600; font-size:13.5px; }
.alert .b { font-size:12.5px; color:var(--c-muted); margin-top:.18rem; }

.legend-dot { display:inline-block; width:9px; height:9px; border-radius:99px; margin-right:.4rem; vertical-align:middle; }

/* ---------------- Controles ---------------- */
.stButton > button, .stDownloadButton > button {
  border-radius:10px; border:1px solid var(--c-border); font-weight:600; font-size:13px;
  background: var(--c-surface); color: var(--c-text); transition: all .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--c-accent); color: var(--c-accent); transform: translateY(-1px);
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-accent-alt) 100%);
  color:#fff; border:none;
}
div[data-testid="stMetricValue"] { font-family:'Sora',sans-serif; }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--c-border); }
.stTabs [data-baseweb="tab"] { border-radius:9px 9px 0 0; padding:.45rem .95rem; font-size:13px; font-weight:500; }
.stTabs [aria-selected="true"] { background: var(--c-surface); border:1px solid var(--c-border); border-bottom-color: var(--c-surface); color: var(--c-primary); }
div[data-testid="stDataFrame"] { border:1px solid var(--c-border); border-radius:12px; overflow:hidden; }
.stProgress > div > div > div > div { background: linear-gradient(90deg, var(--c-accent), var(--c-accent-alt)); }
div[data-testid="stExpander"] { border:1px solid var(--c-border); border-radius:12px; background:var(--c-surface); }
hr { border-color: var(--c-border); }

/* ---------------- Tabla resumen ---------------- */
.mini-table { width:100%; border-collapse:collapse; font-size:12.8px; }
.mini-table th { text-align:left; font-size:10.5px; letter-spacing:.07em; color:var(--c-muted); font-weight:700; padding:.4rem .55rem; border-bottom:1px solid var(--c-border); }
.mini-table td { padding:.48rem .55rem; border-bottom:1px solid var(--c-border); }
.mini-table tr:last-child td { border-bottom:none; }
.mini-table td.num { text-align:right; font-family:'Sora',sans-serif; font-weight:600; }

.vs-col { background:var(--c-surface); border:1px solid var(--c-border); border-radius:var(--radius); padding:1rem 1.15rem; box-shadow:var(--shadow); }
.vs-col .n { font-family:'Sora',sans-serif; font-size:15px; font-weight:600; line-height:1.25; }
.vs-col .c { font-size:12px; color:var(--c-muted); margin-bottom:.7rem; }
.vs-row { display:flex; justify-content:space-between; padding:.42rem 0; border-bottom:1px dashed var(--c-border); font-size:13px; }
.vs-row:last-child { border-bottom:none; }
.vs-row .val { font-family:'Sora',sans-serif; font-weight:600; }
.win { color: var(--c-ok); }

/* ---------------- Animaciones de entrada ---------------- */
@keyframes entrar { from { opacity:0; transform: translateY(16px); } to { opacity:1; transform:none; } }
@keyframes acercar { from { opacity:0; transform: scale(.97); } to { opacity:1; transform:none; } }
@keyframes fundir { from { opacity:0; } to { opacity:1; } }

.kpi { animation: entrar .5s cubic-bezier(.22,.8,.3,1) both; }
div[data-testid="stColumn"]:nth-child(1) .kpi { animation-delay: .00s; }
div[data-testid="stColumn"]:nth-child(2) .kpi { animation-delay: .07s; }
div[data-testid="stColumn"]:nth-child(3) .kpi { animation-delay: .14s; }
div[data-testid="stColumn"]:nth-child(4) .kpi { animation-delay: .21s; }
div[data-testid="stColumn"]:nth-child(5) .kpi { animation-delay: .28s; }

div[data-testid="stVerticalBlockBorderWrapper"] {
  animation: entrar .55s cubic-bezier(.22,.8,.3,1) both; animation-delay:.18s;
}
div[data-testid="stPlotlyChart"] { animation: fundir .8s ease both; animation-delay:.25s; }
.sede-card, .insight, .alert, .vs-col { animation: entrar .5s cubic-bezier(.22,.8,.3,1) both; }
.page-head { animation: entrar .45s ease both; }

.kpi, .sede-card, .insight { transition: transform .18s ease, box-shadow .18s ease; }
.kpi:hover, .sede-card:hover, .insight:hover {
  transform: translateY(-3px); box-shadow: 0 12px 30px rgba(15,30,56,.14);
}
.bar-fill { animation: crecer .9s cubic-bezier(.22,.8,.3,1) both; animation-delay:.3s; }
@keyframes crecer { from { width:0 !important; } }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}

footer, #MainMenu { visibility:hidden; }
div[data-testid="stToolbar"] { right: 1rem; }
</style>
""")


def inject_css() -> None:
    st.markdown(CSS_TEMPLATE.substitute(T()), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 6. HELPERS DE UI Y GRAFICOS
# ---------------------------------------------------------------------------

import inspect as _inspect

_PLOTLY_HAS_WIDTH = "width" in _inspect.signature(st.plotly_chart).parameters
_DF_HAS_WIDTH = "width" in _inspect.signature(st.dataframe).parameters
_BTN_HAS_WIDTH = "width" in _inspect.signature(st.button).parameters


def chart(fig, key=None, **kwargs):
    """st.plotly_chart compatible con versiones nuevas y antiguas de Streamlit."""
    try:
        if _PLOTLY_HAS_WIDTH:
            return st.plotly_chart(fig, width="stretch", key=key,
                                   config={"displayModeBar": False}, **kwargs)
        return st.plotly_chart(fig, use_container_width=True, key=key,
                               config={"displayModeBar": False}, **kwargs)
    except TypeError:
        return st.plotly_chart(fig, use_container_width=True, key=key)


def table(df, **kwargs):
    try:
        if _DF_HAS_WIDTH:
            return st.dataframe(df, width="stretch", **kwargs)
        return st.dataframe(df, use_container_width=True, **kwargs)
    except TypeError:
        return st.dataframe(df)


def wide_kwargs() -> dict:
    return {"width": "stretch"} if _BTN_HAS_WIDTH else {"use_container_width": True}


def fmt(n) -> str:
    try:
        return f"{int(round(float(n))):,}".replace(",", ".")
    except Exception:
        return str(n)


def pct(n, decimals: int = 1) -> str:
    try:
        return f"{float(n):.{decimals}f}".replace(".", ",") + " %"
    except Exception:
        return "-"


def page_head(title: str, subtitle: str, stamp_right: str | None = None) -> None:
    right = stamp_right or (
        "Actualizado <b>" + datetime.now().strftime("%d/%m/%Y %H:%M") + "</b>"
    )
    st.markdown(
        f"""<div class="page-head">
              <div><div class="page-title">{title}</div>
                   <div class="page-sub">{subtitle}</div></div>
              <div class="stamp">{right}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, foot: str = "", accent: str | None = None,
             chip: str | None = None, chip_class: str = "chip-flat") -> None:
    accent = accent or T()["primary"]
    chip_html = f'<span class="chip {chip_class}">{chip}</span>' if chip else ""
    st.markdown(
        f"""<div class="kpi" style="--kpi-accent:{accent}">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{value}</div>
              <div class="kpi-foot">{chip_html}{foot}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def panel(title: str = "", sub: str = ""):
    """Contenedor con borde nativo de Streamlit y encabezado propio."""
    try:
        box = st.container(border=True)
    except TypeError:
        box = st.container()
    if title:
        box.markdown(
            f'<div class="panel-title">{title}</div><div class="panel-sub">{sub}</div>',
            unsafe_allow_html=True,
        )
    return box


def section(title: str, sub: str = "") -> None:
    st.markdown(
        f'<div class="section-title">{title}</div><div class="section-sub">{sub}</div>',
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 330, legend: bool = True, margin=None):
    t = T()
    fig.update_layout(
        template="plotly_dark" if st.session_state.get("dark_mode") else "plotly_white",
        height=height,
        margin=margin or dict(l=10, r=14, t=18, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color=t["text"]),
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["border"],
                        font=dict(family="Inter, sans-serif", size=12, color=t["text"])),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1,
                    font=dict(size=11.5, color=t["text"]), bgcolor="rgba(0,0,0,0)"),
        colorway=palette(),
        bargap=0.22,
    )
    fig.update_xaxes(gridcolor=t["grid"], zeroline=False, linecolor=t["border"],
                     tickfont=dict(size=11.5, color=t["text_muted"]), title_font=dict(size=11.5))
    fig.update_yaxes(gridcolor=t["grid"], zeroline=False, linecolor=t["border"],
                     tickfont=dict(size=11.5, color=t["text_muted"]), title_font=dict(size=11.5))
    return fig


def gradient_for(name: str) -> tuple:
    """Gradiente estable derivado del nombre de la sede."""
    h = int(hashlib.md5(strip_accents(name).encode("utf-8")).hexdigest()[:8], 16)
    pairs = [
        ("#1D3461", "#2CA6A4"), ("#123B63", "#2563EB"), ("#0F3057", "#3E7CB1"),
        ("#164E63", "#0EA5E9"), ("#1E3A8A", "#7C3AED"), ("#134E4A", "#14B8A6"),
        ("#312E81", "#4F46E5"), ("#0B3954", "#087E8B"),
    ]
    return pairs[h % len(pairs)]


def initials(name: str) -> str:
    clean = re.sub(r"[^A-Za-z ]", " ", strip_accents(str(name)))
    parts = [p for p in clean.split() if len(p) > 1 and p.upper() not in ("DE", "LA", "EL", "IE")]
    if not parts:
        return "SD"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def sede_image_html(name: str, tipo: str) -> str:
    """Banner de la sede: usa foto real si existe en assets/sedes, si no un grafico generado."""
    slug = re.sub(r"[^a-z0-9]+", "-", strip_accents(str(name)).lower()).strip("-")
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(ASSETS_DIR, slug + ext)
        if os.path.isfile(path):
            import base64
            mime = "image/png" if ext == ".png" else ("image/webp" if ext == ".webp" else "image/jpeg")
            with open(path, "rb") as fh:
                b64 = base64.b64encode(fh.read()).decode()
            return (f'<div class="sede-banner" style="background-image:linear-gradient('
                    f'rgba(15,30,56,.25),rgba(15,30,56,.72)),url(data:{mime};base64,{b64});'
                    f'background-size:cover;background-position:center">'
                    f'<span class="tag">{tipo}</span></div>')
    c1, c2 = gradient_for(name)
    pattern = (
        "radial-gradient(circle at 18% 22%, rgba(255,255,255,.16) 0 18%, transparent 18.5%),"
        "radial-gradient(circle at 78% 68%, rgba(255,255,255,.10) 0 24%, transparent 24.5%),"
        "linear-gradient(135deg, " + c1 + " 0%, " + c2 + " 100%)"
    )
    return (f'<div class="sede-banner" style="background:{pattern}">'
            f'<span class="tag">{tipo}</span>'
            f'<span class="initials">{initials(name)}</span></div>')


# ---------------------------------------------------------------------------
# 7. FILTROS GLOBALES
# ---------------------------------------------------------------------------

FILTER_DEFS = [
    ("Sede", "f_sede", "Sede"),
    ("Facultad corta", "f_fac", "Facultad"),
    ("Nombre Programa", "f_prog", "Programa"),
    ("Modalidad", "f_mod", "Modalidad"),
    ("Nivel", "f_niv", "Nivel de formacion"),
    ("Sexo", "f_sexo", "Sexo"),
    ("Estrato", "f_estrato", "Estrato"),
    ("Tipo_Colegio", "f_colegio", "Tipo de colegio"),
]


def init_filters() -> None:
    for _, key, _ in FILTER_DEFS:
        st.session_state.setdefault(key, [])


def reset_filters() -> None:
    for _, key, _ in FILTER_DEFS:
        st.session_state[key] = []


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    out = df
    for col, key, _ in FILTER_DEFS:
        chosen = st.session_state.get(key) or []
        if chosen:
            out = out[out[col].isin(chosen)]
    return out


def filters_active() -> int:
    return sum(1 for _, key, _ in FILTER_DEFS if st.session_state.get(key))


def sidebar_filters(df: pd.DataFrame, show_widgets: bool = True) -> None:
    st.markdown('<div class="nav-label">Filtros del analisis</div>', unsafe_allow_html=True)
    if not show_widgets:
        st.caption(f"{filters_active()} filtro(s) activos. La segmentacion de este modulo "
                   f"esta en la barra superior.")
        return
    with st.expander(f"Segmentacion ({filters_active()} activos)", expanded=False):
        for col, key, label in FILTER_DEFS:
            opciones = sorted([o for o in df[col].dropna().unique().tolist()])
            st.multiselect(label, opciones, key=key, placeholder="Todos")
        st.button("Limpiar filtros", on_click=reset_filters, key="btn_reset_filters",
                  **wide_kwargs())


def filter_banner(df_all: pd.DataFrame, df_f: pd.DataFrame) -> None:
    share = len(df_f) / max(len(df_all), 1)
    activos = filters_active()
    cols = st.columns([3, 1])
    with cols[0]:
        st.progress(min(share, 1.0))
    with cols[1]:
        st.markdown(
            f'<div style="text-align:right;font-size:12.5px;color:var(--c-muted);padding-top:.2rem">'
            f'<b style="color:var(--c-text)">{fmt(len(df_f))}</b> de {fmt(len(df_all))} registros '
            f'({pct(share*100)}) con {activos} filtro(s)</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# 8. MODULO 1 - INICIO / DASHBOARD
# ---------------------------------------------------------------------------

def view_dashboard(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Panel de matriculados 2026",
              "Vision consolidada de la matricula academica del periodo 2026")
    filter_banner(df_all, df)

    if df.empty:
        st.warning("La combinacion de filtros no devuelve registros. "
                   "Ajusta la segmentacion en el panel izquierdo.")
        return

    total = len(df)
    estrato_prom = df["Id Estrato"].replace(0, np.nan).mean()
    fem = int((df["Sexo"] == "FEMENINO").sum())
    base_share = total / max(len(df_all), 1)

    c = st.columns(5)
    with c[0]:
        kpi_card("Estudiantes matriculados", fmt(total),
                 f"{pct(base_share * 100)} del periodo",
                 accent=T()["primary"], chip="2026")
    with c[1]:
        principales = df[df["Tipo Sede"] == "Campus principal"]["Sede"].nunique()
        kpi_card("Sedes activas", fmt(df["Sede"].nunique()),
                 f"{principales} campus principales", accent=T()["accent"])
    with c[2]:
        kpi_card("Programas academicos", fmt(df["Nombre Programa"].nunique()),
                 f"{df['Facultad'].nunique()} facultades", accent=T()["accent_alt"])
    with c[3]:
        kpi_card("Estrato promedio", f"{estrato_prom:.2f}".replace(".", ","),
                 "Escala socioeconomica 1 a 6", accent="#7C3AED")
    with c[4]:
        kpi_card("Participacion femenina", pct(fem / total * 100),
                 f"{fmt(fem)} estudiantes", accent="#DB2777")

    st.write("")
    left, right = st.columns([1.55, 1])

    with left:
        with panel("Matricula por facultad y sexo",
                   "Estudiantes de cada facultad segun el sexo registrado"):
            piv = df.groupby(["Facultad corta", "Sexo"]).size().reset_index(name="Estudiantes")
            orden = piv.groupby("Facultad corta")["Estudiantes"].sum().sort_values().index.tolist()
            fig = go.Figure()
            for sexo in ["FEMENINO", "MASCULINO", "NO REGISTRA"]:
                sub = piv[piv["Sexo"] == sexo]
                if sub.empty:
                    continue
                sub = sub.set_index("Facultad corta").reindex(orden).reset_index()
                fig.add_bar(y=sub["Facultad corta"], x=sub["Estudiantes"].fillna(0),
                            name=sexo.title(), orientation="h",
                            marker=dict(color=SEX_COLORS.get(sexo, "#94A3B8")),
                            hovertemplate="%{y}<br>" + sexo.title() +
                                          ": %{x:,.0f}<extra></extra>")
            fig.update_layout(barmode="group")
            style_fig(fig, height=330, margin=dict(l=10, r=14, t=26, b=10))
            fig.update_yaxes(tickfont=dict(size=10.5))
            chart(fig, key="dash_fac_sexo")

    with right:
        with panel("Modalidad de estudio", "Peso relativo de cada modalidad"):
            mod = df["Modalidad"].value_counts().reset_index()
            mod.columns = ["Modalidad", "Estudiantes"]
            fig = go.Figure(go.Pie(
                labels=mod["Modalidad"].str.title(), values=mod["Estudiantes"], hole=0.62,
                marker=dict(colors=palette()[:len(mod)],
                            line=dict(color=T()["surface"], width=2)),
                textinfo="percent", textfont=dict(size=12),
                hovertemplate="%{label}<br>%{value:,.0f} estudiantes (%{percent})<extra></extra>"))
            style_fig(fig, height=330, margin=dict(l=10, r=10, t=26, b=10))
            fig.update_layout(annotations=[dict(
                text=f"<b>{fmt(total)}</b><br><span style='font-size:11px'>matriculados</span>",
                showarrow=False, font=dict(size=17, family="Sora", color=T()["text"]))])
            chart(fig, key="dash_modalidad")

    st.write("")
    a, b, c3 = st.columns([1.25, 1, 1])

    with a:
        with panel("Programas con mayor demanda", "Diez programas con mas matriculados"):
            top = df["Programa corto"].value_counts().head(10).sort_values()
            fig = go.Figure(go.Bar(
                x=top.values, y=top.index, orientation="h",
                marker=dict(color=list(top.values),
                            colorscale=[[0, T()["accent"]], [1, T()["primary"]]]),
                text=[fmt(v) for v in top.values], textposition="outside",
                textfont=dict(size=10.5, color=T()["text_muted"]),
                hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
            style_fig(fig, height=345, legend=False, margin=dict(l=10, r=75, t=10, b=10))
            fig.update_yaxes(tickfont=dict(size=10))
            fig.update_xaxes(visible=False)
            chart(fig, key="dash_top_prog")

    with b:
        with panel("Distribucion por estrato", "Composicion socioeconomica"):
            est = df["Estrato"].value_counts().sort_index()
            fig = go.Figure(go.Bar(
                x=list(est.index), y=list(est.values),
                marker=dict(color=T()["accent_alt"]),
                hovertemplate="%{x}<br>%{y:,.0f} estudiantes<extra></extra>"))
            style_fig(fig, height=345, legend=False)
            fig.update_xaxes(tickangle=-30, tickfont=dict(size=10))
            chart(fig, key="dash_estrato")

    with c3:
        with panel("Concentracion por sede", "Cinco sedes con mayor volumen"):
            prof = sede_profile(df).head(5)
            rows = "".join(
                f"<tr><td>{str(r['Sede']).title()}"
                f"<div style='font-size:11px;color:var(--c-muted)'>{r['Ciudad Sede']}</div></td>"
                f"<td class='num'>{fmt(r['Estudiantes'])}"
                f"<div style='font-size:11px;color:var(--c-muted);font-weight:500'>"
                f"{pct(r['Participacion'])}</div></td></tr>"
                for _, r in prof.iterrows())
            st.markdown(
                '<table class="mini-table"><thead><tr><th>Sede</th>'
                '<th style="text-align:right">Estudiantes</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 9. MODULO 2 - MAPA INTERACTIVO DE SEDES
# ---------------------------------------------------------------------------

_HAS_SCATTERMAP = hasattr(go, "Scattermap")
TraceMap = go.Scattermap if _HAS_SCATTERMAP else go.Scattermapbox
MAP_LAYOUT_KEY = "map" if _HAS_SCATTERMAP else "mapbox"

TIPO_COLORS = {
    "Campus principal": "#1D3461",
    "Universidad en mi barrio": "#2CA6A4",
    "Universidad en mi region": "#F59E0B",
    "Campus virtual": "#7C3AED",
    "Movilidad academica": "#94A3B8",
}


def map_figure(prof: pd.DataFrame, selected: str | None):
    geo = prof.dropna(subset=["lat", "lon"]).copy()
    if geo.empty:
        return None
    vmax = geo["Estudiantes"].max()
    geo["size"] = 13 + 46 * np.sqrt(geo["Estudiantes"] / vmax)
    geo["opacity"] = 0.45 + 0.45 * (geo["Estudiantes"] / vmax) ** 0.4

    fig = go.Figure()
    for tipo, sub in geo.groupby("Tipo Sede"):
        fig.add_trace(TraceMap(
            lat=sub["lat"], lon=sub["lon"], mode="markers", name=tipo,
            marker=dict(size=sub["size"], color=TIPO_COLORS.get(tipo, "#2563EB"),
                        opacity=float(sub["opacity"].mean())),
            customdata=np.stack([
                sub["Sede"].astype(str), sub["Ciudad Sede"].astype(str),
                sub["Estudiantes"], sub["Programas"],
                sub["Facultad lider"].astype(str), sub["% Femenino"],
            ], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                "Estudiantes: %{customdata[2]:,.0f}<br>"
                "Programas: %{customdata[3]}<br>"
                "Facultad lider: %{customdata[4]}<br>"
                "Participacion femenina: %{customdata[5]:.1f} %<extra></extra>"),
        ))

    if selected and selected in set(geo["Sede"]):
        row = geo[geo["Sede"] == selected].iloc[0]
        fig.add_trace(TraceMap(
            lat=[row["lat"]], lon=[row["lon"]], mode="markers", name="Seleccionada",
            marker=dict(size=float(row["size"]) + 16, color="#DB2777", opacity=0.35),
            hoverinfo="skip", showlegend=False))
        center = dict(lat=float(row["lat"]), lon=float(row["lon"]))
        zoom = 10.2
    else:
        center = dict(lat=float(geo["lat"].mean()), lon=float(geo["lon"].mean()))
        zoom = 6.4

    fig.update_layout(
        **{MAP_LAYOUT_KEY: dict(style=T()["map_style"], center=center, zoom=zoom)},
        margin=dict(l=0, r=0, t=0, b=0), height=520,
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="top", y=1.0, x=0.01,
                    bgcolor="rgba(255,255,255,.82)" if not st.session_state.get("dark_mode")
                    else "rgba(15,23,42,.82)",
                    bordercolor=T()["border"], borderwidth=1, font=dict(size=11)),
        font=dict(family="Inter, sans-serif", color=T()["text"]),
        hoverlabel=dict(bgcolor=T()["surface"], bordercolor=T()["border"],
                        font=dict(family="Inter, sans-serif", size=12, color=T()["text"])),
    )
    return fig


def sede_detail_card(row: pd.Series, df: pd.DataFrame) -> None:
    st.markdown(f'<div class="sede-card">{sede_image_html(row["Sede"], row["Tipo Sede"])}'
                f'<div class="sede-body">'
                f'<div class="sede-name">{str(row["Sede"]).title()}</div>'
                f'<div class="sede-city">{row["Ciudad Sede"]} &middot; {row["Referencia"]}</div>'
                f'<div class="sede-metrics">'
                f'<div class="metric-mini"><div class="v">{fmt(row["Estudiantes"])}</div>'
                f'<div class="k">Estudiantes</div></div>'
                f'<div class="metric-mini"><div class="v">{fmt(row["Programas"])}</div>'
                f'<div class="k">Programas</div></div>'
                f'<div class="metric-mini"><div class="v">'
                f'{str(row["Estrato promedio"]).replace(".", ",")}</div>'
                f'<div class="k">Estrato prom.</div></div></div>'
                f'<div class="bar-track"><div class="bar-fill" '
                f'style="width:{min(float(row["Participacion"]) * 4, 100):.1f}%"></div></div>'
                f'<div style="font-size:11.5px;color:var(--c-muted);margin-top:.35rem">'
                f'{pct(row["Participacion"], 2)} de la matricula total</div>'
                f'</div></div>', unsafe_allow_html=True)

    sub = df[df["Sede"] == row["Sede"]]
    st.markdown(
        f'<div style="font-size:12.6px;line-height:1.85;padding:.1rem .2rem">'
        f'<b>Facultad lider</b><br>{row["Facultad lider"]}<br>'
        f'<b>Programa mas demandado</b><br>{row["Programa lider"]}<br>'
        f'<b>Composicion</b><br>'
        f'<span class="legend-dot" style="background:{SEX_COLORS["FEMENINO"]}"></span>'
        f'Femenino {pct(row["% Femenino"])} &nbsp;'
        f'<span class="legend-dot" style="background:{SEX_COLORS["MASCULINO"]}"></span>'
        f'Masculino {pct(row["% Masculino"])}<br>'
        f'<b>Modalidad virtual</b> {pct(row["% Virtual"])}<br>'
        f'<b>Colegio publico</b> '
        f'{pct((sub["Tipo_Colegio"] == "PÚBLICO").mean() * 100)}'
        f'</div>', unsafe_allow_html=True)


def view_mapa(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Mapa interactivo de sedes",
              "Cartografia de la red academica: el tamano de cada nodo es proporcional al volumen de matricula")

    if df.empty:
        st.warning("Sin registros para los filtros seleccionados.")
        return

    prof = sede_profile(df)
    geo = prof.dropna(subset=["lat", "lon"])
    st.session_state.setdefault("sede_sel", geo["Sede"].iloc[0] if not geo.empty else None)

    top_bar = st.columns([2, 1, 1, 1])
    with top_bar[0]:
        opciones = geo["Sede"].tolist()
        idx = opciones.index(st.session_state["sede_sel"]) if st.session_state.get("sede_sel") in opciones else 0
        elegida = st.selectbox("Sede en foco", opciones, index=idx, key="map_select")
        st.session_state["sede_sel"] = elegida
    with top_bar[1]:
        kpi_card("Nodos en el mapa", fmt(len(geo)), "Sedes georreferenciadas", accent=T()["accent"])
    with top_bar[2]:
        kpi_card("Municipios cubiertos", fmt(geo["Ciudad Sede"].nunique()),
                 "Presencia territorial", accent=T()["accent_alt"])
    with top_bar[3]:
        sin_geo = int(prof["lat"].isna().sum())
        kpi_card("Sin sede fisica", fmt(sin_geo), "Virtual y movilidad", accent="#7C3AED")

    st.write("")
    map_col, side_col = st.columns([2.35, 1])

    with map_col:
        with panel():
            fig = map_figure(prof, st.session_state.get("sede_sel"))
            if fig is None:
                st.info("No hay sedes georreferenciadas en la seleccion actual.")
            else:
                evento = None
                try:
                    evento = st.plotly_chart(fig, key="mapa_sedes", on_select="rerun",
                                             selection_mode="points",
                                             config={"displayModeBar": False},
                                             **({"width": "stretch"} if _PLOTLY_HAS_WIDTH
                                                else {"use_container_width": True}))
                except Exception:
                    chart(fig, key="mapa_sedes_fallback")
                if evento is not None:
                    puntos = getattr(evento, "selection", {}) or {}
                    puntos = puntos.get("points", []) if isinstance(puntos, dict) else []
                    if puntos:
                        cd = puntos[0].get("customdata")
                        if cd and cd[0] in set(prof["Sede"]):
                            if cd[0] != st.session_state.get("sede_sel"):
                                st.session_state["sede_sel"] = cd[0]
                                st.rerun()
            st.caption("Haz clic en un nodo para fijarlo, o pasa el cursor para ver el detalle. "
                       "Las coordenadas de las sedes en barrios y municipios son referenciales.")

    with side_col:
        actual = st.session_state.get("sede_sel")
        if actual and actual in set(prof["Sede"]):
            with panel("Detalle de la sede", "Informacion consolidada del nodo seleccionado"):
                sede_detail_card(prof[prof["Sede"] == actual].iloc[0], df)
        else:
            st.info("Selecciona una sede para ver el detalle.")

    st.write("")
    with panel("Cobertura territorial",
               "Estudiantes agrupados por municipio o localidad de la sede"):
        ciudad = (prof.dropna(subset=["lat"]).groupby("Ciudad Sede")["Estudiantes"]
                  .sum().sort_values(ascending=False).head(15).sort_values())
        fig = go.Figure(go.Bar(
            x=ciudad.values, y=ciudad.index, orientation="h",
            marker=dict(color=list(ciudad.values),
                        colorscale=[[0, T()["accent"]], [1, T()["primary"]]]),
            text=[fmt(v) for v in ciudad.values], textposition="outside",
            textfont=dict(size=10.5, color=T()["text_muted"]),
            hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
        style_fig(fig, height=430, legend=False, margin=dict(l=10, r=64, t=10, b=10))
        chart(fig, key="mapa_ciudades")


# ---------------------------------------------------------------------------
# 10. MODULO 3 - EXPLORAR SEDES
# ---------------------------------------------------------------------------

def view_sedes(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Explorar sedes",
              "Catalogo de la red academica con el detalle de programas y poblacion de cada sede")

    if df.empty:
        st.warning("Sin registros para los filtros seleccionados.")
        return

    prof = sede_profile(df)

    ctrl = st.columns([2, 1.2, 1.2, 1])
    with ctrl[0]:
        busca = st.text_input("Buscar sede", placeholder="Nombre de la sede o municipio",
                              key="sede_search")
    with ctrl[1]:
        tipos = ["Todas"] + sorted(prof["Tipo Sede"].unique().tolist())
        tipo_sel = st.selectbox("Tipo de sede", tipos, key="sede_tipo")
    with ctrl[2]:
        orden = st.selectbox("Ordenar por",
                             ["Mas estudiantes", "Menos estudiantes", "Mas programas",
                              "Nombre", "Estrato promedio"], key="sede_orden")
    with ctrl[3]:
        limite = st.selectbox("Mostrar", [9, 18, 30, "Todas"], key="sede_limite")

    vista = prof.copy()
    if busca:
        needle = strip_accents(busca).upper()
        vista = vista[vista.apply(
            lambda r: needle in strip_accents(str(r["Sede"])).upper()
            or needle in strip_accents(str(r["Ciudad Sede"])).upper(), axis=1)]
    if tipo_sel != "Todas":
        vista = vista[vista["Tipo Sede"] == tipo_sel]

    orden_map = {
        "Mas estudiantes": ("Estudiantes", False), "Menos estudiantes": ("Estudiantes", True),
        "Mas programas": ("Programas", False), "Nombre": ("Sede", True),
        "Estrato promedio": ("Estrato promedio", False),
    }
    col_o, asc = orden_map[orden]
    vista = vista.sort_values(col_o, ascending=asc)
    if limite != "Todas":
        vista = vista.head(int(limite))

    st.caption(f"{len(vista)} sedes en el catalogo actual "
               f"({fmt(vista['Estudiantes'].sum())} estudiantes representados)")
    st.write("")

    if vista.empty:
        st.info("Ninguna sede coincide con la busqueda.")
        return

    registros = list(vista.iterrows())
    for inicio in range(0, len(registros), 3):
        cols = st.columns(3, gap="medium")
        for col, (_, row) in zip(cols, registros[inicio:inicio + 3]):
            with col:
                st.markdown(
                    f'<div class="sede-card">{sede_image_html(row["Sede"], row["Tipo Sede"])}'
                    f'<div class="sede-body">'
                    f'<div class="sede-name">{str(row["Sede"]).title()}</div>'
                    f'<div class="sede-city">{row["Ciudad Sede"]} &middot; {row["Referencia"]}</div>'
                    f'<div class="sede-metrics">'
                    f'<div class="metric-mini"><div class="v">{fmt(row["Estudiantes"])}</div>'
                    f'<div class="k">Estudiantes</div></div>'
                    f'<div class="metric-mini"><div class="v">{fmt(row["Programas"])}</div>'
                    f'<div class="k">Programas</div></div>'
                    f'<div class="metric-mini"><div class="v">{pct(row["% Femenino"], 0)}</div>'
                    f'<div class="k">Femenino</div></div></div>'
                    f'<div class="bar-track"><div class="bar-fill" '
                    f'style="width:{min(float(row["Participacion"]) * 4, 100):.1f}%"></div></div>'
                    f'</div></div>', unsafe_allow_html=True)

                with st.expander("Ver detalles"):
                    sub = df[df["Sede"] == row["Sede"]]
                    m1, m2 = st.columns(2)
                    m1.metric("Estrato promedio", str(row["Estrato promedio"]).replace(".", ","))
                    m2.metric("Modalidad virtual", pct(row["% Virtual"], 0))
                    st.markdown(f"**Facultad lider**  \n{row['Facultad lider']}")
                    st.markdown("**Programas ofertados**")
                    progs = (sub["Nombre Programa"].value_counts()
                             .rename_axis("Programa").reset_index(name="Estudiantes"))
                    table(progs, hide_index=True, height=min(240, 40 + 35 * len(progs)))
                    st.markdown("**Distribucion por estrato**")
                    est = (sub["Estrato"].value_counts().sort_index()
                           .rename_axis("Estrato").reset_index(name="Estudiantes"))
                    fig = go.Figure(go.Bar(x=est["Estrato"], y=est["Estudiantes"],
                                           marker=dict(color=T()["accent"])))
                    style_fig(fig, height=210, legend=False)
                    fig.update_xaxes(tickangle=-30, tickfont=dict(size=9.5))
                    chart(fig, key=f"sede_est_{strip_accents(str(row['Sede']))[:22]}_{inicio}")


# ---------------------------------------------------------------------------
# 11. MODULO 4 - ESTADISTICAS INTERACTIVAS
# ---------------------------------------------------------------------------

def view_estadisticas(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Estadisticas interactivas",
              "Cruces analiticos sobre la poblacion filtrada del periodo 2026")

    # Etiqueta fija: si cambiara con el numero de filtros, el panel se cerraria al elegir uno
    with st.expander("Filtros de segmentacion", expanded=False):
        fila1 = st.columns(4)
        fila2 = st.columns([1, 1, 1, 1])
        celdas = list(fila1) + list(fila2)
        for celda, (col, key, label) in zip(celdas, FILTER_DEFS):
            with celda:
                st.multiselect(label, sorted(df_all[col].dropna().unique().tolist()),
                               key=key, placeholder="Todos")
        st.button("Limpiar filtros", on_click=reset_filters, key="btn_reset_est")

    df = apply_filters(df_all)
    filter_banner(df_all, df)

    if df.empty:
        st.warning("Sin registros para los filtros seleccionados.")
        return

    tabs = st.tabs(["Programas", "Perfil socioeconomico", "Nivel y modalidad",
                    "Origen y procedencia"])

    with tabs[0]:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            with panel("Top 10 de programas", "Programas con mayor numero de matriculados"):
                top10 = df["Programa corto"].value_counts().head(10).sort_values()
                fig = go.Figure(go.Bar(
                    x=top10.values, y=top10.index, orientation="h",
                    marker=dict(color=list(top10.values),
                                colorscale=[[0, T()["accent"]], [1, T()["primary"]]]),
                    text=[fmt(v) for v in top10.values], textposition="outside",
                    textfont=dict(size=10.5, color=T()["text_muted"]),
                    hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
                style_fig(fig, height=400, legend=False, margin=dict(l=10, r=60, t=10, b=10))
                chart(fig, key="est_top10")
        with c2:
            with panel("Area de conocimiento", "Participacion de cada area"):
                area = df["Area Conocimiento"].fillna("SIN REGISTRO").value_counts()
                etiquetas = [a.title()[:34] for a in area.index]
                fig = go.Figure(go.Pie(labels=etiquetas, values=area.values, hole=0.55,
                                       marker=dict(colors=palette(),
                                                   line=dict(color=T()["surface"], width=2)),
                                       textinfo="percent", textfont=dict(size=11),
                                       hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
                style_fig(fig, height=400, margin=dict(l=6, r=6, t=40, b=6))
                fig.update_layout(legend=dict(orientation="v", x=1.02, y=0.5,
                                              xanchor="left", yanchor="middle",
                                              font=dict(size=10)))
                chart(fig, key="est_area")

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            with panel("Distribucion por estrato", "Composicion socioeconomica de la matricula"):
                est = df["Estrato"].value_counts().sort_index()
                fig = go.Figure(go.Pie(
                    labels=list(est.index), values=list(est.values), hole=0.6,
                    marker=dict(colors=palette(), line=dict(color=T()["surface"], width=2)),
                    textinfo="percent", textfont=dict(size=11.5),
                    hovertemplate="%{label}<br>%{value:,.0f} estudiantes (%{percent})<extra></extra>"))
                style_fig(fig, height=360, margin=dict(l=6, r=6, t=34, b=6))
                prom = df["Id Estrato"].replace(0, np.nan).mean()
                fig.update_layout(annotations=[dict(
                    text=f"<b>{prom:.2f}</b>".replace(".", ",") +
                         "<br><span style='font-size:11px'>promedio</span>",
                    showarrow=False, font=dict(size=17, family="Sora", color=T()["text"]))])
                chart(fig, key="est_estrato_donut")
        with c2:
            with panel("Estrato por facultad",
                       "Estrato promedio y volumen de estudiantes en cada facultad"):
                agg = (df.groupby("Facultad corta")
                       .agg(Estudiantes=("ID", "size"),
                            Estrato=("Id Estrato", lambda s: s.replace(0, np.nan).mean()))
                       .reset_index().sort_values("Estudiantes"))
                fig = go.Figure()
                fig.add_bar(x=agg["Estudiantes"], y=agg["Facultad corta"], orientation="h",
                            name="Estudiantes", marker=dict(color=T()["primary"]),
                            hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>")
                fig.add_trace(go.Scatter(
                    x=agg["Estrato"], y=agg["Facultad corta"], mode="markers+text",
                    name="Estrato promedio", xaxis="x2",
                    marker=dict(size=13, color=T()["accent"], line=dict(width=2, color=T()["surface"])),
                    text=[f"{v:.2f}".replace(".", ",") for v in agg["Estrato"]],
                    textposition="top center", textfont=dict(size=10, color=T()["text_muted"]),
                    hovertemplate="%{y}<br>Estrato promedio %{x:.2f}<extra></extra>"))
                style_fig(fig, height=360, margin=dict(l=10, r=16, t=34, b=10))
                fig.update_layout(xaxis2=dict(overlaying="x", side="top", range=[1, 4],
                                              showgrid=False, tickfont=dict(size=10)))
                fig.update_yaxes(tickfont=dict(size=10))
                chart(fig, key="est_estrato_fac")

    with tabs[2]:
        c1, c2, c3 = st.columns(3)
        with c1:
            with panel("Nivel de formacion", "Pregrado frente a posgrado"):
                niv = df["Nivel"].value_counts()
                fig = go.Figure(go.Bar(x=list(niv.index), y=list(niv.values),
                                       marker=dict(color=[T()["primary"], T()["accent"]][:len(niv)]),
                                       text=[fmt(v) for v in niv.values], textposition="outside",
                                       textfont=dict(size=11, color=T()["text_muted"]),
                                       hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
                style_fig(fig, height=330, legend=False)
                chart(fig, key="est_nivel")
        with c2:
            with panel("Modalidad", "Presencial, virtual y semipresencial"):
                mod = df["Modalidad"].value_counts()
                fig = go.Figure(go.Bar(x=[m.title() for m in mod.index], y=list(mod.values),
                                       marker=dict(color=T()["accent_alt"]),
                                       text=[fmt(v) for v in mod.values], textposition="outside",
                                       textfont=dict(size=11, color=T()["text_muted"]),
                                       hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
                style_fig(fig, height=330, legend=False)
                chart(fig, key="est_mod")
        with c3:
            with panel("Colegio de procedencia", "Origen escolar de los matriculados"):
                col = df["Tipo_Colegio"].fillna("SIN REGISTRO").value_counts()
                fig = go.Figure(go.Pie(labels=list(col.index), values=list(col.values), hole=0.58,
                                       marker=dict(colors=[T()["primary"], T()["accent"], "#94A3B8"],
                                                   line=dict(color=T()["surface"], width=2)),
                                       textinfo="percent", textfont=dict(size=11.5),
                                       hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
                style_fig(fig, height=330, margin=dict(l=6, r=6, t=34, b=6))
                chart(fig, key="est_colegio")

        with panel("Modalidad por facultad", "Como se distribuye cada facultad entre modalidades"):
            cross = pd.crosstab(df["Facultad corta"], df["Modalidad"])
            cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100
            fig = go.Figure()
            for i, mod in enumerate(cross_pct.columns):
                fig.add_bar(y=cross_pct.index, x=cross_pct[mod], orientation="h",
                            name=str(mod).title(), marker=dict(color=palette()[i % len(palette())]),
                            hovertemplate="%{y}<br>" + str(mod).title() + ": %{x:.1f} %<extra></extra>")
            fig.update_layout(barmode="stack")
            style_fig(fig, height=300, margin=dict(l=10, r=14, t=30, b=10))
            fig.update_xaxes(ticksuffix=" %")
            fig.update_yaxes(tickfont=dict(size=10.5))
            chart(fig, key="est_mod_fac")

    with tabs[3]:
        c1, c2 = st.columns([1, 1])
        with c1:
            with panel("Ciudades de nacimiento", "Quince ciudades con mayor aporte de estudiantes"):
                ciudad = df["Ciudad Nacimiento"].value_counts().head(15).sort_values()
                fig = go.Figure(go.Bar(x=ciudad.values, y=ciudad.index, orientation="h",
                                       marker=dict(color=list(ciudad.values),
                                                   colorscale=[[0, T()["accent"]], [1, T()["primary"]]]),
                                       hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
                style_fig(fig, height=420, legend=False)
                fig.update_yaxes(tickfont=dict(size=10.5))
                chart(fig, key="est_ciudad")
        with c2:
            with panel("Comunas y barrios de residencia",
                       "Quince territorios con mayor concentracion"):
                comuna = df["Comuna"].dropna().value_counts().head(15).sort_values()
                fig = go.Figure(go.Bar(x=comuna.values, y=comuna.index, orientation="h",
                                       marker=dict(color=T()["accent"]),
                                       hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
                style_fig(fig, height=420, legend=False)
                fig.update_yaxes(tickfont=dict(size=10.5))
                chart(fig, key="est_comuna")

        with panel("Colegios de procedencia", "Instituciones que mas estudiantes aportan"):
            cole = df["Colegio_Procedencia"].dropna().value_counts().head(12).sort_values()
            fig = go.Figure(go.Bar(x=cole.values, y=[c[:52] for c in cole.index], orientation="h",
                                   marker=dict(color=T()["primary"]),
                                   hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>"))
            style_fig(fig, height=380, legend=False)
            fig.update_yaxes(tickfont=dict(size=10))
            chart(fig, key="est_colegios_top")


# ---------------------------------------------------------------------------
# 12. MODULO 5 - BUSCADOR INTELIGENTE
# ---------------------------------------------------------------------------

SEARCH_FIELDS = {
    "Programa": "Nombre Programa",
    "Sede": "Sede",
    "Colegio de procedencia": "Colegio_Procedencia",
    "Barrio o comuna": "Comuna",
    "Ciudad de nacimiento": "Ciudad Nacimiento",
    "Facultad": "Facultad corta",
}


@st.cache_data(show_spinner=False)
def search_index(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for etiqueta, col in SEARCH_FIELDS.items():
        conteo = df[col].dropna().value_counts()
        for valor, n in conteo.items():
            filas.append({"Categoria": etiqueta, "Columna": col, "Valor": str(valor),
                          "Estudiantes": int(n),
                          "Clave": strip_accents(str(valor)).upper()})
    return pd.DataFrame(filas)


def view_buscador(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Buscador inteligente",
              "Consulta cruzada sobre programas, sedes, colegios y territorios del dataset")

    idx = search_index(df_all)

    c1, c2 = st.columns([3, 1.1])
    with c1:
        consulta = st.text_input("Escribe tu busqueda",
                                 placeholder="Ejemplo: software, robledo, CEFA, ingenieria",
                                 key="q_global")
    with c2:
        categorias = st.multiselect("Categorias", list(SEARCH_FIELDS.keys()),
                                    default=list(SEARCH_FIELDS.keys()), key="q_cat")

    if not consulta or len(consulta.strip()) < 2:
        st.info("Escribe al menos dos caracteres. La busqueda recorre simultaneamente "
                "programas academicos, sedes, colegios de procedencia, territorios y facultades.")
        with panel("Consultas frecuentes", "Los valores con mayor volumen en cada categoria"):
            cols = st.columns(3)
            for i, (etiqueta, col) in enumerate(list(SEARCH_FIELDS.items())[:6]):
                with cols[i % 3]:
                    top = df_all[col].dropna().value_counts().head(4)
                    filas = "".join(
                        f"<tr><td>{str(k)[:40]}</td><td class='num'>{fmt(v)}</td></tr>"
                        for k, v in top.items())
                    st.markdown(f'<div style="font-size:11px;letter-spacing:.08em;'
                                f'color:var(--c-muted);font-weight:700;margin-top:.6rem">'
                                f'{etiqueta.upper()}</div>'
                                f'<table class="mini-table"><tbody>{filas}</tbody></table>',
                                unsafe_allow_html=True)
        return

    needle = strip_accents(consulta.strip()).upper()
    res = idx[idx["Categoria"].isin(categorias) & idx["Clave"].str.contains(needle, regex=False)]
    res = res.sort_values("Estudiantes", ascending=False)

    if res.empty:
        st.warning(f"Sin coincidencias para \"{consulta}\". Prueba con un termino mas corto.")
        return

    alcance = int(res["Estudiantes"].sum())
    k = st.columns(4)
    with k[0]:
        kpi_card("Coincidencias", fmt(len(res)), "Valores distintos encontrados", accent=T()["primary"])
    with k[1]:
        kpi_card("Categorias", fmt(res["Categoria"].nunique()), "Dimensiones con resultados",
                 accent=T()["accent"])
    with k[2]:
        kpi_card("Registros alcanzados", fmt(alcance), "Suma por coincidencia", accent=T()["accent_alt"])
    with k[3]:
        mejor = res.iloc[0]
        kpi_card("Mejor resultado", str(mejor["Valor"])[:22],
                 f"{fmt(mejor['Estudiantes'])} estudiantes", accent="#DB2777")

    st.write("")
    for categoria in [c for c in SEARCH_FIELDS if c in set(res["Categoria"])]:
        grupo = res[res["Categoria"] == categoria].head(9)
        with panel(categoria, f"{len(res[res['Categoria'] == categoria])} coincidencias"):
            cols = st.columns(3, gap="small")
            for i, (_, r) in enumerate(grupo.iterrows()):
                with cols[i % 3]:
                    col_real = r["Columna"]
                    sub = df_all[df_all[col_real].astype(str) == r["Valor"]]
                    extra = ""
                    if len(sub):
                        extra = (f"{sub['Sede'].nunique()} sede(s) &middot; "
                                 f"{sub['Nombre Programa'].nunique()} programa(s)")
                    st.markdown(
                        f'<div class="insight" style="margin-bottom:.55rem">'
                        f'<div class="k">{categoria}</div>'
                        f'<div class="t">{str(r["Valor"])[:60]}</div>'
                        f'<div class="d"><b>{fmt(r["Estudiantes"])}</b> estudiantes<br>{extra}</div>'
                        f'</div>', unsafe_allow_html=True)

    st.write("")
    with panel("Registros que coinciden", "Detalle de los estudiantes asociados a la busqueda"):
        mask = pd.Series(False, index=df_all.index)
        for col in set(res["Columna"]):
            mask |= df_all[col].fillna("").astype(str).map(
                lambda s: needle in strip_accents(s).upper())
        detalle = df_all[mask]
        st.caption(f"{fmt(len(detalle))} registros coinciden con la busqueda")
        cols_show = ["ID", "Sede", "Nombre Programa", "Facultad corta", "Modalidad",
                     "Nivel", "Sexo", "Estrato", "Comuna", "Colegio_Procedencia"]
        table(detalle[cols_show].head(400), hide_index=True, height=340)


# ---------------------------------------------------------------------------
# 13. MODULO 6 - TABLA DE DATOS
# ---------------------------------------------------------------------------

TABLE_COLUMNS = ["ID", "Sede", "Tipo Sede", "Ciudad Sede", "Nombre Programa", "Facultad corta",
                 "Area Conocimiento", "Nivel", "Modalidad", "Sexo", "Estrato", "Tipo Inscripcion",
                 "Comuna", "Barrio", "Ciudad Nacimiento", "Pais Nacimiento",
                 "Colegio_Procedencia", "Tipo_Colegio"]


def view_tabla(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Tabla de datos",
              "Vista administrativa del dataset con paginacion, orden y filtros por columna")

    ctrl = st.columns([1.3, 1.3, 1.3, 1, 1])
    with ctrl[0]:
        f_sede = st.multiselect("Sede", sorted(df["Sede"].unique()), key="t_sede", placeholder="Todas")
    with ctrl[1]:
        f_prog = st.multiselect("Programa", sorted(df["Nombre Programa"].unique()),
                                key="t_prog", placeholder="Todos")
    with ctrl[2]:
        f_estado = st.selectbox("Estado del registro",
                                ["Todos", "Completos", "Con campos faltantes"], key="t_estado")
    with ctrl[3]:
        orden_col = st.selectbox("Ordenar por", TABLE_COLUMNS, key="t_ordcol")
    with ctrl[4]:
        orden_dir = st.selectbox("Sentido", ["Ascendente", "Descendente"], key="t_orddir")

    vista = df.copy()
    if f_sede:
        vista = vista[vista["Sede"].isin(f_sede)]
    if f_prog:
        vista = vista[vista["Nombre Programa"].isin(f_prog)]
    if f_estado == "Completos":
        vista = vista[vista["Registro completo"]]
    elif f_estado == "Con campos faltantes":
        vista = vista[~vista["Registro completo"]]

    texto = st.text_input("Filtro rapido en todas las columnas",
                          placeholder="Texto libre, por ejemplo: virtual, robledo, contaduria",
                          key="t_query")
    if texto and len(texto) >= 2:
        needle = strip_accents(texto).upper()
        texto_fila = (vista[TABLE_COLUMNS].fillna("").astype(str)
                      .agg(" ".join, axis=1)
                      .map(lambda s: needle in strip_accents(s).upper()))
        vista = vista[texto_fila]

    vista = vista.sort_values(orden_col, ascending=(orden_dir == "Ascendente"))

    pag = st.columns([1, 1, 4])
    with pag[0]:
        por_pagina = st.selectbox("Registros por pagina", [10, 25, 50, 100], index=1, key="t_size")
    total_pag = max(1, int(np.ceil(len(vista) / por_pagina)))
    with pag[1]:
        pagina = st.number_input("Pagina", min_value=1, max_value=total_pag, value=1, step=1,
                                 key="t_page")
    inicio = (int(pagina) - 1) * int(por_pagina)
    fin = inicio + int(por_pagina)
    with pag[2]:
        st.markdown(
            f'<div style="padding-top:1.9rem;font-size:12.5px;color:var(--c-muted)">'
            f'Pagina <b style="color:var(--c-text)">{int(pagina)}</b> de {total_pag} &nbsp;&middot;&nbsp; '
            f'mostrando <b style="color:var(--c-text)">{fmt(min(fin, len(vista)) - inicio)}</b> '
            f'registros de <b style="color:var(--c-text)">{fmt(len(vista))}</b> filtrados '
            f'({fmt(len(df_all))} en el dataset completo)</div>', unsafe_allow_html=True)

    table(vista[TABLE_COLUMNS].iloc[inicio:fin], hide_index=True, height=520)

    foot = st.columns([1, 1, 1, 1])
    with foot[0]:
        st.metric("Registros filtrados", fmt(len(vista)))
    with foot[1]:
        st.metric("Sedes en la vista", fmt(vista["Sede"].nunique()))
    with foot[2]:
        st.metric("Programas en la vista", fmt(vista["Nombre Programa"].nunique()))
    with foot[3]:
        st.download_button("Descargar esta vista en CSV",
                           vista[TABLE_COLUMNS].to_csv(index=False).encode("utf-8-sig"),
                           file_name="matriculados_2026_vista.csv", mime="text/csv",
                           key="t_dl", **wide_kwargs())


# ---------------------------------------------------------------------------
# 14. MODULO 7 - COMPARADOR DE SEDES
# ---------------------------------------------------------------------------

def vs_block(row: pd.Series, otra: pd.Series, campos: list) -> str:
    filas = ""
    for etiqueta, clave, formato, mayor_mejor in campos:
        v1, v2 = row[clave], otra[clave]
        try:
            gana = (float(v1) > float(v2)) if mayor_mejor else (float(v1) < float(v2))
        except Exception:
            gana = False
        clase = "val win" if gana else "val"
        filas += (f'<div class="vs-row"><span>{etiqueta}</span>'
                  f'<span class="{clase}">{formato(v1)}</span></div>')
    return filas


def view_comparador(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Comparador de sedes",
              "Contraste directo entre dos sedes de la red academica")

    prof = sede_profile(df)
    if len(prof) < 2:
        st.warning("Se necesitan al menos dos sedes en la seleccion actual.")
        return

    opciones = prof["Sede"].tolist()
    c1, c2, c3 = st.columns([1.4, 0.35, 1.4])
    with c1:
        sede_a = st.selectbox("Sede A", opciones, index=0, key="cmp_a")
    with c2:
        st.markdown('<div style="text-align:center;padding-top:2rem;font-family:Sora;'
                    'font-weight:700;color:var(--c-muted)">VS</div>', unsafe_allow_html=True)
    with c3:
        sede_b = st.selectbox("Sede B", opciones, index=1 if len(opciones) > 1 else 0, key="cmp_b")

    if sede_a == sede_b:
        st.info("Selecciona dos sedes distintas para ver la comparacion.")
        return

    ra = prof[prof["Sede"] == sede_a].iloc[0]
    rb = prof[prof["Sede"] == sede_b].iloc[0]

    campos = [
        ("Estudiantes matriculados", "Estudiantes", lambda v: fmt(v), True),
        ("Programas ofertados", "Programas", lambda v: fmt(v), True),
        ("Facultades presentes", "Facultades", lambda v: fmt(v), True),
        ("Estrato promedio", "Estrato promedio", lambda v: str(v).replace(".", ","), True),
        ("Participacion femenina", "% Femenino", lambda v: pct(v), True),
        ("Participacion masculina", "% Masculino", lambda v: pct(v), True),
        ("Matricula virtual", "% Virtual", lambda v: pct(v), True),
        ("Participacion en el total", "Participacion", lambda v: pct(v, 2), True),
    ]

    col_a, col_mid, col_b = st.columns([1.4, 0.35, 1.4])
    with col_a:
        st.markdown(f'<div class="vs-col"><div class="n">{str(sede_a).title()}</div>'
                    f'<div class="c">{ra["Ciudad Sede"]} &middot; {ra["Tipo Sede"]}</div>'
                    f'{vs_block(ra, rb, campos)}</div>', unsafe_allow_html=True)
    with col_mid:
        st.markdown('<div style="text-align:center;padding-top:6rem">'
                    '<div style="width:1px;height:150px;margin:0 auto;background:var(--c-border)"></div>'
                    '<div style="font-size:11px;color:var(--c-muted);margin-top:.6rem;line-height:1.5">'
                    'En verde el<br>mejor indicador</div></div>', unsafe_allow_html=True)
    with col_b:
        st.markdown(f'<div class="vs-col"><div class="n">{str(sede_b).title()}</div>'
                    f'<div class="c">{rb["Ciudad Sede"]} &middot; {rb["Tipo Sede"]}</div>'
                    f'{vs_block(rb, ra, campos)}</div>', unsafe_allow_html=True)

    st.write("")
    with panel("Contraste programa por programa",
               "Barras divergentes: a la izquierda la sede A, a la derecha la sede B"):
        sa = df[df["Sede"] == sede_a]["Nombre Programa"].value_counts()
        sb = df[df["Sede"] == sede_b]["Nombre Programa"].value_counts()
        comp = pd.DataFrame({"A": sa, "B": sb}).fillna(0)
        comp["total"] = comp["A"] + comp["B"]
        comp = comp.sort_values("total", ascending=False).head(14).sort_values("total")
        etiquetas = [p[:44] + ("..." if len(p) > 44 else "") for p in comp.index]

        fig = go.Figure()
        fig.add_bar(y=etiquetas, x=-comp["A"], orientation="h", name=str(sede_a).title(),
                    marker=dict(color=T()["primary"]),
                    customdata=comp["A"],
                    hovertemplate="%{y}<br>%{customdata:,.0f} estudiantes<extra></extra>")
        fig.add_bar(y=etiquetas, x=comp["B"], orientation="h", name=str(sede_b).title(),
                    marker=dict(color=T()["accent"]),
                    hovertemplate="%{y}<br>%{x:,.0f} estudiantes<extra></extra>")
        fig.update_layout(barmode="relative")
        style_fig(fig, height=470, margin=dict(l=10, r=14, t=34, b=10))
        limite = float(max(comp["A"].max(), comp["B"].max())) * 1.12 + 1
        fig.update_xaxes(range=[-limite, limite],
                         tickvals=np.linspace(-limite, limite, 7),
                         ticktext=[fmt(abs(v)) for v in np.linspace(-limite, limite, 7)])
        fig.update_yaxes(tickfont=dict(size=10))
        chart(fig, key="cmp_diverging")

    c1, c2 = st.columns(2)
    with c1:
        with panel("Perfil socioeconomico comparado", "Distribucion de estratos en cada sede"):
            ea = df[df["Sede"] == sede_a]["Estrato"].value_counts(normalize=True).sort_index() * 100
            eb = df[df["Sede"] == sede_b]["Estrato"].value_counts(normalize=True).sort_index() * 100
            niveles = sorted(set(ea.index) | set(eb.index))
            fig = go.Figure()
            fig.add_bar(x=niveles, y=[ea.get(n, 0) for n in niveles], name=str(sede_a).title(),
                        marker=dict(color=T()["primary"]),
                        hovertemplate="%{x}<br>%{y:.1f} %<extra></extra>")
            fig.add_bar(x=niveles, y=[eb.get(n, 0) for n in niveles], name=str(sede_b).title(),
                        marker=dict(color=T()["accent"]),
                        hovertemplate="%{x}<br>%{y:.1f} %<extra></extra>")
            style_fig(fig, height=330, margin=dict(l=10, r=14, t=34, b=10))
            fig.update_yaxes(ticksuffix=" %")
            fig.update_xaxes(tickangle=-25, tickfont=dict(size=10))
            chart(fig, key="cmp_estrato")
    with c2:
        with panel("Radar de indicadores", "Comparacion normalizada de los principales indicadores"):
            metricas = ["Estudiantes", "Programas", "Facultades", "% Femenino", "% Virtual"]
            maximos = {m: max(float(ra[m]), float(rb[m]), 1) for m in metricas}
            fig = go.Figure()
            for nombre, fila, color in ((sede_a, ra, T()["primary"]), (sede_b, rb, T()["accent"])):
                valores = [float(fila[m]) / maximos[m] * 100 for m in metricas]
                fig.add_trace(go.Scatterpolar(
                    r=valores + [valores[0]], theta=metricas + [metricas[0]], fill="toself",
                    name=str(nombre).title(), line=dict(color=color, width=2),
                    opacity=0.45,
                    hovertemplate="%{theta}: %{r:.0f} sobre 100<extra></extra>"))
            style_fig(fig, height=330, margin=dict(l=40, r=40, t=34, b=20))
            fig.update_layout(polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0, 100], gridcolor=T()["grid"],
                                tickfont=dict(size=9, color=T()["text_muted"])),
                angularaxis=dict(gridcolor=T()["grid"], tickfont=dict(size=10))))
            chart(fig, key="cmp_radar")


# ---------------------------------------------------------------------------
# 15. MODULO 8 - DESCUBRE LOS DATOS
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def build_insights(df: pd.DataFrame) -> list:
    """Hallazgos calculados directamente sobre el dataset."""
    ins = []
    total = len(df)
    if total == 0:
        return ins
    prof = sede_profile(df)

    top_sede = prof.iloc[0]
    ins.append(("Concentracion", "Una sede concentra la mayor parte de la matricula",
                f"{str(top_sede['Sede']).title()} reune {fmt(top_sede['Estudiantes'])} estudiantes, "
                f"equivalentes al {pct(top_sede['Participacion'])} del total del periodo."))

    tres = prof.head(3)["Participacion"].sum()
    ins.append(("Distribucion", "Las tres sedes principales sostienen la operacion",
                f"Entre las tres primeras sedes suman {pct(tres)} de la matricula, "
                f"mientras las {len(prof) - 3} restantes reparten el {pct(100 - tres)}."))

    prog = df["Nombre Programa"].value_counts()
    ins.append(("Demanda", f"{prog.index[0]} lidera la oferta",
                f"Con {fmt(prog.iloc[0])} matriculados representa el "
                f"{pct(prog.iloc[0] / total * 100)} de la matricula y supera en "
                f"{fmt(prog.iloc[0] - prog.iloc[1])} estudiantes al segundo programa."))

    virt = df[df["Modalidad"] == "VIRTUAL"]
    if len(virt):
        pv = virt["Nombre Programa"].value_counts()
        ins.append(("Virtualidad", f"{pv.index[0]} domina la modalidad virtual",
                    f"La modalidad virtual agrupa {fmt(len(virt))} estudiantes "
                    f"({pct(len(virt) / total * 100)} del total) y este programa aporta "
                    f"{fmt(pv.iloc[0])} de ellos."))

    est = df["Id Estrato"].replace(0, np.nan)
    bajo = float((est <= 2).mean() * 100)
    ins.append(("Perfil socioeconomico", "La matricula se concentra en estratos 1 y 2",
                f"{pct(bajo)} de los estudiantes pertenece a estratos 1 o 2, con un estrato "
                f"promedio de {est.mean():.2f}".replace(".", ",") + " en toda la poblacion."))

    fem = float((df["Sexo"] == "FEMENINO").mean() * 100)
    fac_f = (df[df["Sexo"] == "FEMENINO"]["Facultad corta"].value_counts(normalize=True) * 100)
    fac_share = (df["Facultad corta"].value_counts(normalize=True) * 100)
    brecha = (fac_f - fac_share).sort_values(ascending=False)
    if len(brecha):
        ins.append(("Equidad", f"La participacion femenina llega a {pct(fem)}",
                    f"{brecha.index[0]} es la facultad con mayor sobrerrepresentacion femenina "
                    f"frente a su peso en la matricula total."))

    publico = float((df["Tipo_Colegio"] == "PÚBLICO").mean() * 100)
    ins.append(("Procedencia", "El colegio publico es la principal puerta de entrada",
                f"{pct(publico)} de los matriculados proviene de instituciones publicas, "
                f"frente a {pct(100 - publico)} de colegios privados."))

    ext = df[df["Origen"] == "Internacional"]
    if len(ext):
        pais = ext["Pais Nacimiento"].value_counts()
        ins.append(("Internacionalizacion", f"{fmt(len(ext))} estudiantes nacieron fuera del pais",
                    f"Representan el {pct(len(ext) / total * 100)} de la matricula y provienen de "
                    f"{pais.shape[0]} paises, liderados por {str(pais.index[0]).title()} "
                    f"con {fmt(pais.iloc[0])} estudiantes."))

    region = prof[prof["Tipo Sede"] == "Universidad en mi region"]
    if len(region):
        ins.append(("Territorio", "La presencia regional llega a municipios pequenos",
                    f"{len(region)} sedes regionales atienden {fmt(region['Estudiantes'].sum())} "
                    f"estudiantes en {region['Ciudad Sede'].nunique()} municipios distintos."))

    peque = prog[prog < 15]
    if len(peque):
        ins.append(("Alerta de oferta", f"{len(peque)} programas tienen menos de 15 matriculados",
                    f"Suman apenas {fmt(peque.sum())} estudiantes en total, lo que sugiere revisar "
                    f"su viabilidad o su estrategia de promocion."))

    medellin = float(df["Es Medellin"].mean() * 100)
    ins.append(("Origen geografico", "La matricula tiene una base metropolitana marcada",
                f"{pct(medellin)} de los estudiantes nacio en Medellin y el resto proviene de "
                f"{df['Ciudad Nacimiento'].nunique() - 1} ciudades diferentes."))
    return ins


def view_insights(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Descubre los datos",
              "Hallazgos generados automaticamente a partir de la lectura del dataset")

    if df.empty:
        st.warning("Sin registros para los filtros seleccionados.")
        return

    ins = build_insights(df)
    for inicio in range(0, len(ins), 3):
        cols = st.columns(3, gap="medium")
        for col, (k, t, d) in zip(cols, ins[inicio:inicio + 3]):
            with col:
                st.markdown(f'<div class="insight" style="margin-bottom:.9rem">'
                            f'<div class="k">{k}</div><div class="t">{t}</div>'
                            f'<div class="d">{d}</div></div>', unsafe_allow_html=True)

    st.write("")
    with panel("Curva de concentracion de la matricula",
               "Porcentaje acumulado de estudiantes segun el numero de sedes consideradas"):
        prof = sede_profile(df)
        acumulado = prof["Estudiantes"].cumsum() / prof["Estudiantes"].sum() * 100
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(prof) + 1)), y=acumulado, mode="lines",
            line=dict(color=T()["accent"], width=3), fill="tozeroy",
            fillcolor="rgba(44,166,164,.16)",
            hovertemplate="%{x} sedes acumulan %{y:.1f} % de la matricula<extra></extra>"))
        fig.add_hline(y=80, line=dict(color=T()["text_muted"], dash="dot", width=1),
                      annotation_text="80 % de la matricula",
                      annotation_font=dict(size=10, color=T()["text_muted"]))
        style_fig(fig, height=320, legend=False)
        fig.update_xaxes(title="Sedes ordenadas de mayor a menor volumen")
        fig.update_yaxes(title="Matricula acumulada", ticksuffix=" %")
        chart(fig, key="ins_lorenz")


# ---------------------------------------------------------------------------
# 16. MODULO 9 - INDICADORES Y ALERTAS
# ---------------------------------------------------------------------------

def view_alertas(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Indicadores y alertas",
              "Semaforo de gestion sobre oferta academica, cobertura y consistencia del registro")

    if df.empty:
        st.warning("Sin registros para los filtros seleccionados.")
        return

    prof = sede_profile(df)
    prog = df["Nombre Programa"].value_counts()

    criticos = prog[prog < 15]
    vigilancia = prog[(prog >= 15) & (prog < 40)]
    sedes_bajas = prof[prof["Estudiantes"] < 20]
    desbalance = prof[(prof["Estudiantes"] >= 50) &
                      ((prof["% Femenino"] < 25) | (prof["% Femenino"] > 75))]
    sobrecarga = prof[prof["Participacion"] > 35]
    concentracion_media = prof[prof["Participacion"].between(20, 35)]
    incompletos = int((~df["Registro completo"]).sum())
    sin_sexo = int((df["Sexo"] == "NO REGISTRA").sum())
    estrato_cero = int((df["Id Estrato"].fillna(0) == 0).sum())

    total_alertas = (len(criticos) + len(sedes_bajas) + len(desbalance)
                     + len(sobrecarga) + len(concentracion_media))
    riesgo_alto = len(sobrecarga) + (1 if estrato_cero or sin_sexo else 0)

    k = st.columns(4)
    with k[0]:
        kpi_card("Alertas activas", fmt(total_alertas), "Situaciones que requieren revision",
                 accent=T()["warn"], chip="Monitoreo", chip_class="chip-warn")
    with k[1]:
        kpi_card("Programas en riesgo", fmt(len(criticos)), "Menos de 15 matriculados",
                 accent=T()["risk"], chip="Critico", chip_class="chip-risk")
    with k[2]:
        kpi_card("Sedes con baja ocupacion", fmt(len(sedes_bajas)), "Menos de 20 estudiantes",
                 accent=T()["warn"])
    with k[3]:
        kpi_card("Registros inconsistentes", fmt(incompletos),
                 f"{pct(incompletos / len(df) * 100)} del total", accent=T()["accent_alt"])

    st.write("")
    st.markdown(
        f'<div style="font-size:12.5px;color:var(--c-muted);margin-bottom:.6rem">'
        f'<span class="legend-dot" style="background:{T()["ok"]}"></span>Normal &nbsp;&nbsp;'
        f'<span class="legend-dot" style="background:{T()["warn"]}"></span>Atencion &nbsp;&nbsp;'
        f'<span class="legend-dot" style="background:{T()["risk"]}"></span>Alto</div>',
        unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        with panel("Nivel alto", "Requieren accion inmediata"):
            hay = False
            for _, r in sobrecarga.iterrows():
                hay = True
                st.markdown(f'<div class="alert risk"><div class="h">'
                            f'Concentracion critica en {str(r["Sede"]).title()}</div>'
                            f'<div class="b">Absorbe {pct(r["Participacion"])} de toda la matricula '
                            f'({fmt(r["Estudiantes"])} estudiantes). Revisar capacidad instalada '
                            f'y distribucion de cupos.</div></div>', unsafe_allow_html=True)
            if estrato_cero:
                hay = True
                st.markdown(f'<div class="alert risk"><div class="h">Estrato sin clasificar</div>'
                            f'<div class="b">{fmt(estrato_cero)} registros tienen estrato 0 o vacio, '
                            f'lo que afecta los indicadores socioeconomicos.</div></div>',
                            unsafe_allow_html=True)
            if sin_sexo:
                hay = True
                st.markdown(f'<div class="alert risk"><div class="h">Sexo sin registrar</div>'
                            f'<div class="b">{fmt(sin_sexo)} registros no tienen el campo de sexo '
                            f'diligenciado.</div></div>', unsafe_allow_html=True)
            if not hay:
                st.markdown('<div class="alert ok"><div class="h">Sin alertas de nivel alto</div>'
                            '<div class="b">No se detectaron inconsistencias criticas en la '
                            'seleccion actual.</div></div>', unsafe_allow_html=True)

    with c2:
        with panel("Nivel de atencion", "Seguimiento recomendado"):
            if len(criticos):
                muestra = ", ".join([str(p)[:34] for p in criticos.index[:4]])
                st.markdown(f'<div class="alert warn"><div class="h">'
                            f'{len(criticos)} programas con baja matricula</div>'
                            f'<div class="b">Menos de 15 estudiantes cada uno. Ejemplos: '
                            f'{muestra}.</div></div>', unsafe_allow_html=True)
            if len(vigilancia):
                st.markdown(f'<div class="alert warn"><div class="h">'
                            f'{len(vigilancia)} programas en zona de vigilancia</div>'
                            f'<div class="b">Entre 15 y 39 matriculados. Conviene monitorear su '
                            f'evolucion en el proximo periodo.</div></div>', unsafe_allow_html=True)
            for _, r in concentracion_media.iterrows():
                st.markdown(f'<div class="alert warn"><div class="h">'
                            f'Alta concentracion en {str(r["Sede"]).title()}</div>'
                            f'<div class="b">Concentra {pct(r["Participacion"])} de la matricula '
                            f'({fmt(r["Estudiantes"])} estudiantes). Conviene vigilar la capacidad '
                            f'instalada.</div></div>', unsafe_allow_html=True)
            for _, r in desbalance.head(4).iterrows():
                st.markdown(f'<div class="alert warn"><div class="h">'
                            f'Desbalance de genero en {str(r["Sede"]).title()}</div>'
                            f'<div class="b">Participacion femenina de {pct(r["% Femenino"])} '
                            f'sobre {fmt(r["Estudiantes"])} estudiantes.</div></div>',
                            unsafe_allow_html=True)
            if not len(criticos) and not len(vigilancia) and not len(desbalance) \
                    and not len(concentracion_media):
                st.markdown('<div class="alert ok"><div class="h">Sin alertas de atencion</div>'
                            '<div class="b">La oferta academica se comporta dentro de los rangos '
                            'esperados.</div></div>', unsafe_allow_html=True)

    with c3:
        with panel("Operacion normal", "Indicadores dentro de rango"):
            saludables = prof[(prof["Estudiantes"] >= 20) &
                              (prof["% Femenino"].between(25, 75))]
            st.markdown(f'<div class="alert ok"><div class="h">{len(saludables)} sedes en rango optimo</div>'
                        f'<div class="b">Con volumen suficiente y distribucion de genero '
                        f'equilibrada.</div></div>', unsafe_allow_html=True)
            fuertes = prog[prog >= 100]
            st.markdown(f'<div class="alert ok"><div class="h">{len(fuertes)} programas consolidados</div>'
                        f'<div class="b">Cada uno supera los 100 matriculados y concentra '
                        f'{pct(fuertes.sum() / len(df) * 100)} de la matricula.</div></div>',
                        unsafe_allow_html=True)
            completos = float(df["Registro completo"].mean() * 100)
            st.markdown(f'<div class="alert ok"><div class="h">Integridad del registro</div>'
                        f'<div class="b">{pct(completos)} de los registros tiene todos los campos '
                        f'clave diligenciados.</div></div>', unsafe_allow_html=True)

    st.write("")
    with panel("Mapa de riesgo de la oferta academica",
               "Cada punto es un programa: volumen de matricula frente al numero de sedes donde se ofrece"):
        agg = (df.groupby("Nombre Programa")
               .agg(Estudiantes=("ID", "size"), Sedes=("Sede", "nunique"),
                    Estrato=("Id Estrato", lambda s: s.replace(0, np.nan).mean()))
               .reset_index())
        agg["Nivel"] = np.where(agg["Estudiantes"] < 15, "Alto",
                                np.where(agg["Estudiantes"] < 40, "Atencion", "Normal"))
        colores = {"Alto": T()["risk"], "Atencion": T()["warn"], "Normal": T()["ok"]}
        fig = go.Figure()
        for nivel, sub in agg.groupby("Nivel"):
            fig.add_trace(go.Scatter(
                x=sub["Sedes"], y=sub["Estudiantes"], mode="markers", name=nivel,
                marker=dict(size=np.clip(sub["Estudiantes"] / 45 + 8, 8, 32),
                            color=colores[nivel], opacity=0.8,
                            line=dict(width=1, color=T()["surface"])),
                customdata=sub["Nombre Programa"],
                hovertemplate="%{customdata}<br>%{y:,.0f} estudiantes en %{x} sede(s)<extra></extra>"))
        fig.add_hline(y=15, line=dict(color=T()["risk"], dash="dot", width=1))
        fig.add_hline(y=40, line=dict(color=T()["warn"], dash="dot", width=1))
        style_fig(fig, height=400)
        fig.update_xaxes(title="Sedes donde se ofrece el programa")
        fig.update_yaxes(title="Estudiantes matriculados", type="log")
        chart(fig, key="alert_scatter")


# ---------------------------------------------------------------------------
# 17. MODULO 10 - CALIDAD DE DATOS
# ---------------------------------------------------------------------------

def view_calidad(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Calidad de datos",
              "Auditoria del archivo fuente: completitud, duplicados y consistencia de los campos")

    rep = quality_report(df_all)
    completitud = rep["completos"] / max(rep["total"], 1) * 100

    k = st.columns(4)
    with k[0]:
        kpi_card("Registros analizados", fmt(rep["total"]), "Filas leidas del archivo",
                 accent=T()["primary"])
    with k[1]:
        kpi_card("Registros completos", fmt(rep["completos"]),
                 f"{pct(completitud)} de completitud", accent=T()["ok"],
                 chip="Optimo" if completitud > 90 else "Revisar",
                 chip_class="chip-up" if completitud > 90 else "chip-warn")
    with k[2]:
        kpi_card("Registros incompletos", fmt(rep["incompletos"]),
                 "Con al menos un campo clave vacio", accent=T()["warn"])
    with k[3]:
        kpi_card("Filas duplicadas", fmt(rep["duplicados_unicos"]),
                 f"{fmt(rep['duplicados'])} filas involucradas", accent=T()["risk"])

    st.write("")
    c1, c2 = st.columns([1.3, 1])

    with c1:
        with panel("Completitud por columna", "Porcentaje de valores presentes en cada campo"):
            nulos = rep["nulos_por_columna"]
            comp = ((1 - nulos / rep["total"]) * 100).sort_values()
            colores = [T()["risk"] if v < 90 else (T()["warn"] if v < 99 else T()["ok"])
                       for v in comp.values]
            fig = go.Figure(go.Bar(
                x=comp.values, y=comp.index, orientation="h", marker=dict(color=colores),
                text=[f"{v:.1f} %".replace(".", ",") for v in comp.values],
                textposition="outside", textfont=dict(size=10, color=T()["text_muted"]),
                hovertemplate="%{y}<br>%{x:.2f} % de completitud<extra></extra>"))
            style_fig(fig, height=470, legend=False, margin=dict(l=10, r=64, t=10, b=10))
            fig.update_xaxes(range=[0, 108], ticksuffix=" %")
            fig.update_yaxes(tickfont=dict(size=10.5))
            chart(fig, key="cal_completitud")

    with c2:
        with panel("Resumen de la auditoria", "Detalle de los campos con mayor ausencia de datos"):
            faltantes = rep["nulos_por_columna"]
            faltantes = faltantes[faltantes > 0]
            if faltantes.empty:
                st.success("Ningun campo presenta valores faltantes.")
            else:
                filas = "".join(
                    f"<tr><td>{col}</td><td class='num'>{fmt(v)}</td>"
                    f"<td class='num'>{pct(v / rep['total'] * 100, 2)}</td></tr>"
                    for col, v in faltantes.items())
                st.markdown('<table class="mini-table"><thead><tr><th>Campo</th>'
                            '<th style="text-align:right">Vacios</th>'
                            '<th style="text-align:right">Peso</th></tr></thead>'
                            f'<tbody>{filas}</tbody></table>', unsafe_allow_html=True)

            st.write("")
            fig = go.Figure(go.Pie(
                labels=["Completos", "Incompletos"],
                values=[rep["completos"], rep["incompletos"]], hole=0.62,
                marker=dict(colors=[T()["ok"], T()["warn"]],
                            line=dict(color=T()["surface"], width=2)),
                textinfo="percent", textfont=dict(size=12),
                hovertemplate="%{label}<br>%{value:,.0f} registros<extra></extra>"))
            style_fig(fig, height=250, margin=dict(l=6, r=6, t=30, b=6))
            fig.update_layout(annotations=[dict(
                text=f"<b>{completitud:.1f} %</b>".replace(".", ",") +
                     "<br><span style='font-size:10px'>completitud</span>",
                showarrow=False, font=dict(size=15, family="Sora", color=T()["text"]))])
            chart(fig, key="cal_donut")

    st.write("")
    acciones = st.columns([1, 1, 1, 2])
    with acciones[0]:
        ver_problemas = st.toggle("Ver registros con problemas", key="cal_ver")
    with acciones[1]:
        limpiar = st.toggle("Auto limpiar dataset", key="cal_limpiar",
                            help="Elimina duplicados exactos y filas sin campos clave")
    with acciones[2]:
        st.session_state.setdefault("dataset_limpio", False)

    if ver_problemas:
        problemas = df_all[(~df_all["Registro completo"]) | rep["mask_duplicados"]].copy()
        problemas["Motivo"] = np.where(
            rep["mask_duplicados"].reindex(problemas.index, fill_value=False),
            "Fila duplicada", "Campos faltantes")
        with panel("Registros inconsistentes",
                   f"{fmt(len(problemas))} filas requieren revision manual"):
            cols_show = ["ID", "Motivo", "Campos faltantes", "Sede", "Nombre Programa",
                         "Sexo", "Estrato", "Comuna", "Barrio", "Colegio_Procedencia"]
            table(problemas[cols_show].head(500), hide_index=True, height=380)
            st.download_button("Descargar registros con problemas",
                               problemas.to_csv(index=False).encode("utf-8-sig"),
                               file_name="registros_inconsistentes_2026.csv", mime="text/csv",
                               key="cal_dl_prob")

    if limpiar:
        limpio = df_all.drop_duplicates(subset=rep["columnas"], keep="first")
        limpio = limpio[limpio["Nombre Programa"].notna() & limpio["Sede"].notna()]
        eliminados = len(df_all) - len(limpio)
        with panel("Resultado de la limpieza automatica",
                   "Se eliminan duplicados exactos y filas sin programa o sede"):
            m = st.columns(3)
            m[0].metric("Registros originales", fmt(len(df_all)))
            m[1].metric("Registros conservados", fmt(len(limpio)))
            m[2].metric("Registros eliminados", fmt(eliminados),
                        delta=f"-{pct(eliminados / max(len(df_all), 1) * 100, 2)}")
            st.download_button("Descargar dataset limpio",
                               limpio.drop(columns=["Campos faltantes", "Registro completo"],
                                           errors="ignore").to_csv(index=False).encode("utf-8-sig"),
                               file_name="matriculados_2026_autolimpio.csv", mime="text/csv",
                               key="cal_dl_limpio", type="primary")

    with panel("Consistencia de la georreferenciacion",
               "Sedes cuya ubicacion en el mapa es aproximada o no aplica"):
        prof = sede_profile(df_all)
        sin_geo = prof[prof["lat"].isna() | prof["Geo aproximada"].fillna(False)]
        if sin_geo.empty:
            st.success("Todas las sedes tienen coordenadas verificadas.")
        else:
            vista = sin_geo[["Sede", "Tipo Sede", "Ciudad Sede", "Estudiantes"]].copy()
            vista["Estado"] = np.where(sin_geo["lat"].isna(), "Sin sede fisica",
                                       "Coordenada aproximada")
            table(vista, hide_index=True, height=min(300, 60 + 35 * len(vista)))


# ---------------------------------------------------------------------------
# 18. MODULO 11 - EXPORTAR ANALISIS
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def build_excel(df: pd.DataFrame, prof: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        cols = [c for c in TABLE_COLUMNS if c in df.columns]
        df[cols].to_excel(writer, sheet_name="Matriculados", index=False)
        prof.to_excel(writer, sheet_name="Resumen por sede", index=False)
        (df["Nombre Programa"].value_counts().rename_axis("Programa")
         .reset_index(name="Estudiantes")).to_excel(writer, sheet_name="Programas", index=False)
        (df.groupby(["Facultad corta", "Sexo"]).size().reset_index(name="Estudiantes")
         ).to_excel(writer, sheet_name="Facultad y sexo", index=False)
        (df["Estrato"].value_counts().sort_index().rename_axis("Estrato")
         .reset_index(name="Estudiantes")).to_excel(writer, sheet_name="Estratos", index=False)
    return buffer.getvalue()


def build_report_html(df: pd.DataFrame, prof: pd.DataFrame, filtros: str) -> str:
    total = len(df)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    filas_sede = "".join(
        f"<tr><td>{str(r['Sede']).title()}</td><td>{r['Ciudad Sede']}</td>"
        f"<td class='n'>{fmt(r['Estudiantes'])}</td><td class='n'>{fmt(r['Programas'])}</td>"
        f"<td class='n'>{pct(r['Participacion'], 2)}</td></tr>"
        for _, r in prof.head(20).iterrows())
    filas_prog = "".join(
        f"<tr><td>{p}</td><td class='n'>{fmt(v)}</td>"
        f"<td class='n'>{pct(v / total * 100, 2)}</td></tr>"
        for p, v in df["Nombre Programa"].value_counts().head(20).items())
    estrato = df["Id Estrato"].replace(0, np.nan).mean()
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Reporte de matriculados 2026</title>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;color:#1B2333;margin:0;background:#F1F4F9}}
.wrap{{max-width:980px;margin:0 auto;padding:36px 28px}}
h1{{font-size:26px;margin:0 0 4px}} h2{{font-size:17px;margin:28px 0 10px;color:#1D3461}}
.sub{{color:#63708B;font-size:13px}}
.cards{{display:flex;gap:12px;margin:22px 0;flex-wrap:wrap}}
.card{{flex:1;min-width:170px;background:#fff;border:1px solid #E6E9F0;border-left:4px solid #2CA6A4;
border-radius:12px;padding:14px 16px}}
.card .l{{font-size:11px;color:#63708B;letter-spacing:.05em}}
.card .v{{font-size:25px;font-weight:700;margin-top:4px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #E6E9F0;border-radius:10px;
overflow:hidden;font-size:13px}}
th{{background:#1D3461;color:#fff;text-align:left;padding:9px 11px;font-size:12px}}
td{{padding:8px 11px;border-bottom:1px solid #E6E9F0}} td.n{{text-align:right;font-weight:600}}
.foot{{margin-top:26px;font-size:11.5px;color:#63708B;border-top:1px solid #E6E9F0;padding-top:12px}}
</style></head><body><div class="wrap">
<h1>Reporte de matriculados 2026</h1>
<div class="sub">Generado el {fecha} &middot; {filtros}</div>
<div class="cards">
<div class="card"><div class="l">ESTUDIANTES</div><div class="v">{fmt(total)}</div></div>
<div class="card"><div class="l">SEDES</div><div class="v">{fmt(df['Sede'].nunique())}</div></div>
<div class="card"><div class="l">PROGRAMAS</div><div class="v">{fmt(df['Nombre Programa'].nunique())}</div></div>
<div class="card"><div class="l">ESTRATO PROMEDIO</div><div class="v">{estrato:.2f}</div></div>
<div class="card"><div class="l">PARTICIPACION FEMENINA</div>
<div class="v">{(df['Sexo'] == 'FEMENINO').mean() * 100:.1f} %</div></div>
</div>
<h2>Matricula por sede</h2>
<table><tr><th>Sede</th><th>Ciudad</th><th>Estudiantes</th><th>Programas</th><th>Participacion</th></tr>
{filas_sede}</table>
<h2>Programas con mayor demanda</h2>
<table><tr><th>Programa</th><th>Estudiantes</th><th>Participacion</th></tr>{filas_prog}</table>
<div class="foot">Panel de Matriculados 2026 &middot; Reporte generado automaticamente a partir del
archivo fuente de matricula. Las cifras corresponden a la seleccion vigente al momento de la
exportacion.</div>
</div></body></html>"""


def view_exportar(df_all: pd.DataFrame, df: pd.DataFrame) -> None:
    page_head("Exportar analisis",
              "Descarga el resultado del analisis en los formatos de trabajo mas comunes")

    if df.empty:
        st.warning("Sin registros para exportar con los filtros actuales.")
        return

    activos = [f"{label}: {', '.join(map(str, st.session_state.get(key)))}"
               for _, key, label in FILTER_DEFS if st.session_state.get(key)]
    resumen_filtros = " | ".join(activos) if activos else "Sin filtros aplicados"

    k = st.columns(4)
    with k[0]:
        kpi_card("Registros a exportar", fmt(len(df)),
                 f"{pct(len(df) / len(df_all) * 100)} del dataset", accent=T()["primary"])
    with k[1]:
        kpi_card("Sedes incluidas", fmt(df["Sede"].nunique()), "En la seleccion actual",
                 accent=T()["accent"])
    with k[2]:
        kpi_card("Programas incluidos", fmt(df["Nombre Programa"].nunique()), "Oferta cubierta",
                 accent=T()["accent_alt"])
    with k[3]:
        kpi_card("Columnas disponibles", fmt(len(TABLE_COLUMNS)), "Campos del reporte",
                 accent="#7C3AED")

    st.write("")
    with panel("Seleccion vigente", "Filtros aplicados al conjunto que se va a exportar"):
        st.code(resumen_filtros, language=None)

    prof = sede_profile(df)
    cols = st.columns(3, gap="medium")

    with cols[0]:
        with panel("Datos en CSV", "Archivo plano con los registros filtrados"):
            st.caption("Codificacion UTF-8 con BOM, compatible con Excel en espanol.")
            st.download_button("Descargar CSV",
                               df[TABLE_COLUMNS].to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"matriculados_2026_{datetime.now():%Y%m%d_%H%M}.csv",
                               mime="text/csv", key="exp_csv", type="primary", **wide_kwargs())
            st.download_button("Descargar resumen por sede en CSV",
                               prof.to_csv(index=False).encode("utf-8-sig"),
                               file_name="resumen_sedes_2026.csv", mime="text/csv",
                               key="exp_csv_sede", **wide_kwargs())

    with cols[1]:
        with panel("Libro de Excel", "Cinco hojas con datos y tablas resumen"):
            st.caption("Incluye matriculados, resumen por sede, programas, facultad y estratos.")
            if st.button("Generar libro de Excel", key="exp_gen_xlsx", **wide_kwargs()):
                st.session_state["xlsx_listo"] = True
            if st.session_state.get("xlsx_listo"):
                try:
                    with st.spinner("Construyendo el libro..."):
                        xlsx = build_excel(df, prof)
                    st.download_button(
                        "Descargar Excel", xlsx,
                        file_name=f"analisis_matriculados_2026_{datetime.now():%Y%m%d_%H%M}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="exp_xlsx", type="primary", **wide_kwargs())
                except Exception as exc:
                    st.error(f"No fue posible generar el Excel. Revisa que openpyxl este "
                             f"instalado. Detalle: {exc}")

    with cols[2]:
        with panel("Reporte visual", "Documento HTML listo para imprimir o convertir a PDF"):
            st.caption("Abrelo en el navegador y usa la opcion imprimir para generar un PDF.")
            reporte = build_report_html(df, prof, resumen_filtros)
            st.download_button("Descargar reporte", reporte.encode("utf-8"),
                               file_name=f"reporte_matriculados_2026_{datetime.now():%Y%m%d}.html",
                               mime="text/html", key="exp_html", type="primary", **wide_kwargs())

    st.write("")
    with panel("Vista previa del conjunto exportado", "Primeras filas del archivo que se descargara"):
        table(df[TABLE_COLUMNS].head(25), hide_index=True, height=340)


# ---------------------------------------------------------------------------
# 19. NAVEGACION Y APLICACION PRINCIPAL
# ---------------------------------------------------------------------------

PAGES = [
    ("Inicio y dashboard", view_dashboard),
    ("Mapa interactivo de sedes", view_mapa),
    ("Explorar sedes", view_sedes),
    ("Estadisticas interactivas", view_estadisticas),
    ("Buscador inteligente", view_buscador),
    ("Tabla de datos", view_tabla),
    ("Comparador de sedes", view_comparador),
    ("Descubre los datos", view_insights),
    ("Indicadores y alertas", view_alertas),
    ("Calidad de datos", view_calidad),
    ("Exportar analisis", view_exportar),
]

PAGE_NAMES = [p[0] for p in PAGES]


def sidebar_brand() -> None:
    st.markdown(
        '<div class="brand">'
        '<div class="brand-mark">M26</div>'
        '<div><div class="brand-title">Estudiantes matriculados en 2026</div></div>'
        '</div>', unsafe_allow_html=True)


def data_source_panel():
    """Resuelve el origen de datos: archivo local o carga manual."""
    ruta = find_dataset()
    if ruta:
        firma = f"{ruta}:{os.path.getmtime(ruta)}"
        return ruta, firma, os.path.basename(ruta)

    st.markdown("### Carga del archivo de matricula")
    st.info("No se encontro el archivo CSV junto a app.py. Puedes cargarlo aqui o dejarlo "
            "en la misma carpeta del script con el nombre matriculados_2026_limpio.csv.")
    subido = st.file_uploader("Archivo CSV de matriculados", type=["csv"], key="uploader")
    if subido is None:
        st.stop()
    datos = subido.getvalue()
    return datos, hashlib.md5(datos).hexdigest(), subido.name


def main() -> None:
    st.session_state.setdefault("dark_mode", False)
    st.session_state.setdefault("pagina", PAGE_NAMES[0])
    init_filters()
    inject_css()

    origen, firma, nombre_archivo = data_source_panel()

    with st.spinner("Preparando el tablero..."):
        try:
            df_all = load_data(origen, firma)
        except Exception as exc:
            st.error(f"No fue posible leer el archivo de datos. Detalle: {exc}")
            st.stop()

    with st.sidebar:
        sidebar_brand()
        st.markdown('<div class="nav-label">Navegacion</div>', unsafe_allow_html=True)
        pagina = st.radio("Navegacion", PAGE_NAMES, key="pagina",
                          label_visibility="collapsed")

        st.markdown('<div class="nav-label">Apariencia</div>', unsafe_allow_html=True)
        st.toggle("Modo oscuro", key="dark_mode")

        sidebar_filters(df_all, show_widgets=(pagina != "Estadisticas interactivas"))

        st.markdown(
            f'<div class="side-foot">Fuente: {nombre_archivo}<br>'
            f'{fmt(len(df_all))} registros &middot; {df_all["Sede"].nunique()} sedes<br>'
            f'Sesion iniciada {datetime.now():%d/%m/%Y %H:%M}</div>',
            unsafe_allow_html=True)

    df_filtrado = apply_filters(df_all)
    vista = dict(PAGES)[pagina]
    vista(df_all, df_filtrado)


main()
