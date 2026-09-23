import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from pyproj import Transformer
import io
import json
import os
import base64
import textwrap

# =============================================================================
# CONFIGURACION GENERAL
# =============================================================================

st.set_page_config(
    page_title="PRIMEBOX | Centro de Gravedad",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =============================================================================
# RENDERIZADOR HTML SEGURO / COMPATIBLE
# =============================================================================
# Streamlit puede interpretar bloques HTML indentados como Markdown/código en
# algunas combinaciones de versión/parser. Todos los bloques HTML de esta app
# pasan por aquí: se elimina la indentación accidental y, si está disponible,
# se usa st.html(), que renderiza HTML directamente.

def render_html(content):
    """Renderiza HTML real, evitando que el Markdown lo muestre como texto."""
    content = textwrap.dedent(str(content)).strip()

    if hasattr(st, "html"):
        st.html(content)
    else:
        # Compatibilidad con versiones antiguas de Streamlit.
        st.markdown(content, unsafe_allow_html=True)


HTML_DEBUG = os.getenv("PRIMEBOX_DEBUG_HTML", "1") == "1"

# =============================================================================
# PALETA PRIMEBOX
# =============================================================================

NAVY = "#0B3768"
NAVY_DARK = "#082A50"
BLUE = "#1565C0"
BLUE_BRIGHT = "#1E88E5"
BLUE_LIGHT = "#EAF3FF"

ORANGE = "#F76400"
ORANGE_DARK = "#DB5500"
ORANGE_LIGHT = "#FFF1E8"

WHITE = "#FFFFFF"
BACKGROUND = "#E3EBF5"
TEXT = "#172033"
TEXT_SECONDARY = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"


# =============================================================================
# LOGO
# =============================================================================

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except Exception:
        return None


LOGO_PATH = "image.png"
logo_base64 = get_image_base64(LOGO_PATH)
# =============================================================================
# ARCHIVOS DEL PROYECTO
# =============================================================================

SHAPEFILE_PATH = "provincias_EC/provincias_EC.shp"

# =============================================================================
# CSS PRIMEBOX
# =============================================================================

render_html(
    f"""

<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* -------------------------------------------------------------------------
   BASE
------------------------------------------------------------------------- */

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background: {BACKGROUND};
}}

.block-container {{
    padding-top: 1.15rem;
    padding-bottom: 3rem;
    max-width: 1600px;
}}

#MainMenu {{
    visibility: hidden;
}}

footer {{
    visibility: hidden;
}}

header[data-testid="stHeader"] {{
    background: transparent;
}}


/* -------------------------------------------------------------------------
   HEADER
------------------------------------------------------------------------- */

.primebox-header {{
    position: relative;
    overflow: hidden;

    background:
        radial-gradient(
            circle at 92% 15%,
            rgba(247,100,0,0.13),
            transparent 22%
        ),
        linear-gradient(
            135deg,
            #FFFFFF 0%,
            #FFFFFF 62%,
            #F7FAFE 100%
        );

    border: 1px solid {BORDER};
    border-radius: 22px;

    padding: 25px 30px;

    margin-bottom: 22px;

    box-shadow:
        0px 8px 30px rgba(11,55,104,0.07);

    display: flex;
    align-items: center;
    justify-content: space-between;

    min-height: 110px;
}}

.primebox-header::after {{
    content: "";
    width: 260px;
    height: 260px;

    border: 55px solid rgba(21,101,192,0.04);
    border-radius: 50%;

    position: absolute;

    right: -100px;
    top: -135px;
}}

.primebox-brand {{
    display: flex;
    align-items: center;
    gap: 26px;

    position: relative;
    z-index: 2;
}}

.primebox-logo {{
    max-width: 245px;
    width: 245px;
}}

.primebox-logo-fallback {{
    font-size: 32px;
    font-weight: 800;
    color: {NAVY};
}}

.primebox-logo-fallback span {{
    color: {ORANGE};
}}

.header-divider {{
    height: 55px;
    width: 1px;
    background: {BORDER};
}}

.header-info {{
    display: flex;
    flex-direction: column;
}}

.header-title {{
    font-size: 19px;
    font-weight: 700;
    color: {NAVY_DARK};
    margin-bottom: 5px;
    letter-spacing: -0.2px;
}}

.header-subtitle {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    font-weight: 400;
}}

.header-right {{
    position: relative;
    z-index: 2;

    text-align: right;
}}

.header-badge {{
    display: inline-flex;
    align-items: center;
    gap: 7px;

    padding: 8px 14px;

    border-radius: 100px;

    background: {ORANGE_LIGHT};
    color: {ORANGE_DARK};

    border: 1px solid rgba(247,100,0,.15);

    font-size: 10px;
    font-weight: 700;
    letter-spacing: .5px;
    text-transform: uppercase;

    margin-bottom: 7px;
}}

.header-country {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
}}


/* -------------------------------------------------------------------------
   TABS
------------------------------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {{
    gap: 7px;

    background: #FFFFFF;

    padding: 6px;

    border-radius: 13px;

    border: 1px solid {BORDER};

    box-shadow: 0px 2px 10px rgba(15,23,42,.04);
}}

.stTabs [data-baseweb="tab"] {{
    height: 43px;

    border: none;
    border-radius: 9px;

    padding: 7px 22px;

    color: {TEXT_SECONDARY};

    font-size: 13px;
    font-weight: 600;

    transition: all .2s ease;
}}

.stTabs [data-baseweb="tab"]:hover {{
    background: {BLUE_LIGHT};
    color: {NAVY};
}}

.stTabs [aria-selected="true"] {{
    background: {NAVY} !important;
    color: white !important;
}}

.stTabs [data-baseweb="tab-highlight"] {{
    display: none;
}}


/* -------------------------------------------------------------------------
   SECTION HEADERS
------------------------------------------------------------------------- */

.section-header {{
    display: flex;
    align-items: center;
    gap: 9px;

    color: {NAVY};

    font-size: 11px;
    font-weight: 800;

    letter-spacing: .9px;
    text-transform: uppercase;

    margin: 18px 0 12px;
}}

.section-header::before {{
    content: "";

    width: 4px;
    height: 16px;

    background: {ORANGE};

    border-radius: 4px;
}}

.section-subtitle {{
    color: {TEXT_SECONDARY};
    font-size: 12px;
    margin-top: -7px;
    margin-bottom: 14px;
}}


/* -------------------------------------------------------------------------
   PANEL
------------------------------------------------------------------------- */

.prime-panel {{
    background: #FFFFFF;

    border: 1px solid {BORDER};

    border-radius: 17px;

    padding: 18px;

    box-shadow:
        0px 3px 14px rgba(15,23,42,.045);

    margin-bottom: 14px;
}}


/* -------------------------------------------------------------------------
   KPI
------------------------------------------------------------------------- */

.kpi-card {{
    position: relative;

    background: white;

    border: 1px solid {BORDER};
    border-radius: 16px;

    padding: 18px 18px 17px 18px;

    overflow: hidden;

    min-height: 106px;

    box-shadow:
        0 3px 12px rgba(15,23,42,.04);
}}

.kpi-card::after {{
    content: "";

    width: 55px;
    height: 55px;

    border-radius: 50%;

    position: absolute;

    top: -24px;
    right: -17px;

    background: rgba(21,101,192,.05);
}}

.kpi-orange {{
    border-top: 3px solid {ORANGE};
}}

.kpi-blue {{
    border-top: 3px solid {BLUE};
}}

.kpi-navy {{
    border-top: 3px solid {NAVY};
}}

.kpi-label {{
    color: {TEXT_SECONDARY};

    font-size: 9.5px;
    font-weight: 700;

    letter-spacing: .55px;
    text-transform: uppercase;

    margin-bottom: 9px;
}}

.kpi-value {{
    color: {NAVY_DARK};

    font-size: 20px;
    font-weight: 750;

    letter-spacing: -.45px;

    margin-bottom: 6px;
}}

.kpi-bottom {{
    color: {TEXT_SECONDARY};
    font-size: 10px;
}}

.kpi-dot-blue {{
    display: inline-block;

    width: 6px;
    height: 6px;

    background: {BLUE};

    border-radius: 100%;

    margin-right: 5px;
}}

.kpi-dot-orange {{
    display: inline-block;

    width: 6px;
    height: 6px;

    background: {ORANGE};

    border-radius: 100%;

    margin-right: 5px;
}}


/* -------------------------------------------------------------------------
   CENTRAL RESULT CARD
------------------------------------------------------------------------- */

.result-card {{
    position: relative;
    overflow: hidden;

    background: linear-gradient(
        140deg,
        {NAVY_DARK},
        {NAVY}
    );

    color: white;

    padding: 22px;

    border-radius: 17px;

    margin-top: 13px;
    margin-bottom: 14px;

    box-shadow:
        0px 9px 25px rgba(11,55,104,.18);
}}

.result-card::after {{
    content: "";

    position: absolute;

    right: -35px;
    top: -60px;

    width: 150px;
    height: 150px;

    border-radius: 50%;

    background: rgba(247,100,0,.16);
}}

.result-label {{
    color: rgba(255,255,255,.65);

    text-transform: uppercase;

    font-size: 9px;
    font-weight: 700;

    letter-spacing: .75px;

    margin-bottom: 7px;
}}

.result-value {{
    color: white;

    font-size: 24px;
    font-weight: 750;

    margin-bottom: 4px;
}}

.result-sub {{
    color: rgba(255,255,255,.65);

    font-size: 10px;
}}

.result-cost {{
    color: #FFFFFF;

    font-size: 26px;
    font-weight: 800;

    margin-top: 2px;
}}

.result-cost span {{
    color: {ORANGE};
}}


/* -------------------------------------------------------------------------
   COORDINATE CARDS
------------------------------------------------------------------------- */

.coord-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;

    gap: 9px;

    margin-top: 10px;
}}

.coord-card {{
    background: white;

    border-radius: 11px;
    border: 1px solid {BORDER};

    padding: 11px 12px;
}}

.coord-label {{
    color: {TEXT_SECONDARY};

    text-transform: uppercase;

    font-size: 8.5px;
    font-weight: 700;

    letter-spacing: .4px;

    margin-bottom: 4px;
}}

.coord-value {{
    color: {NAVY};

    font-size: 12px;
    font-weight: 650;
}}


/* -------------------------------------------------------------------------
   BADGE
------------------------------------------------------------------------- */

.province-badge {{
    display: inline-flex;
    align-items: center;

    background: {BLUE_LIGHT};

    color: {NAVY};

    border: 1px solid rgba(21,101,192,.14);

    padding: 7px 11px;

    border-radius: 8px;

    font-size: 11px;
    font-weight: 600;

    margin: 3px 0 7px;
}}


/* -------------------------------------------------------------------------
   BUTTONS
------------------------------------------------------------------------- */

.stButton > button[kind="primary"] {{
    width: 100%;

    border: none !important;

    border-radius: 10px !important;

    background: linear-gradient(
        135deg,
        {ORANGE},
        {ORANGE_DARK}
    ) !important;

    color: #FFFFFF !important;

    min-height: 46px;

    font-size: 12px !important;
    font-weight: 700 !important;

    letter-spacing: .3px;

    box-shadow:
        0px 5px 15px rgba(247,100,0,.19) !important;

    transition: all .2s ease !important;
}}

.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);

    background: linear-gradient(
        135deg,
        #FF781F,
        {ORANGE}
    ) !important;

    box-shadow:
        0px 8px 20px rgba(247,100,0,.25) !important;
}}

.stButton > button:not([kind="primary"]) {{
    border-radius: 9px !important;

    border: 1px solid {BORDER} !important;

    background: #FFFFFF;

    color: {NAVY};

    font-weight: 600;

    transition: all .2s ease;
}}

.stButton > button:not([kind="primary"]):hover {{
    border-color: {BLUE} !important;

    color: {BLUE};

    background: {BLUE_LIGHT};
}}


/* -------------------------------------------------------------------------
   DOWNLOAD BUTTON
------------------------------------------------------------------------- */

.stDownloadButton > button {{
    background: {NAVY} !important;

    color: white !important;

    border: none !important;

    border-radius: 10px !important;

    min-height: 46px;

    font-weight: 650 !important;

    box-shadow:
        0px 5px 15px rgba(11,55,104,.16);

    transition: all .2s ease;
}}

.stDownloadButton > button:hover {{
    background: {BLUE} !important;

    transform: translateY(-1px);
}}


/* -------------------------------------------------------------------------
   INPUTS
------------------------------------------------------------------------- */

div[data-baseweb="select"] > div {{
    border-radius: 9px !important;

    border-color: {BORDER} !important;

    background: white;
}}

div[data-baseweb="input"] {{
    border-radius: 9px;
}}

.stTextInput input {{
    border-radius: 9px !important;
}}

label[data-testid="stWidgetLabel"] p {{
    color: {NAVY_DARK};

    font-size: 11px;

    font-weight: 600;
}}


/* -------------------------------------------------------------------------
   STREAMLIT METRICS
------------------------------------------------------------------------- */

div[data-testid="stMetric"] {{
    background: #FFFFFF;

    border: 1px solid {BORDER};

    border-radius: 13px;

    padding: 14px;

    box-shadow: 0 3px 10px rgba(15,23,42,.035);
}}

div[data-testid="stMetricLabel"] {{
    color: {TEXT_SECONDARY};

    font-size: 10px;
    font-weight: 600;
}}

div[data-testid="stMetricValue"] {{
    color: {NAVY_DARK};

    font-weight: 700;
}}


/* -------------------------------------------------------------------------
   ALERTS
------------------------------------------------------------------------- */

div[data-testid="stAlert"] {{
    border-radius: 10px;

    font-size: 11px;
}}


/* -------------------------------------------------------------------------
   DATAFRAME
------------------------------------------------------------------------- */

div[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};

    border-radius: 12px;

    overflow: hidden;
}}


/* -------------------------------------------------------------------------
   DIVIDER
------------------------------------------------------------------------- */

hr {{
    border: none;

    height: 1px;

    background: {BORDER};

    margin: 20px 0;
}}


/* -------------------------------------------------------------------------
   FOOTER
------------------------------------------------------------------------- */

.prime-footer {{
    margin-top: 35px;

    padding-top: 16px;

    border-top: 1px solid {BORDER};

    color: #94A3B8;

    font-size: 9.5px;

    text-align: center;

    letter-spacing: .15px;
}}


/* -------------------------------------------------------------------------
   RESPONSIVE
------------------------------------------------------------------------- */

@media (max-width: 850px) {{

    .primebox-header {{
        flex-direction: column;
        align-items: flex-start;
        padding: 22px;
    }}

    .primebox-brand {{
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
    }}

    .header-divider {{
        display: none;
    }}

    .header-right {{
        text-align: left;
    }}

    .primebox-logo {{
        max-width: 210px;
    }}

}}

</style>
"""
)


# =============================================================================
# HEADER
# =============================================================================

if logo_base64:
    logo_data = logo_base64.strip()
    logo_html = f"""
<img
    src="data:image/png;base64,{logo_data}"
    alt="PRIMEBOX"
    class="primebox-logo"
/>
"""
else:
    logo_html = """
    <div class="primebox-logo-fallback">
        PRIME<span>BOX</span>
    </div>
    """


header_html = f"""
<div class="primebox-header">
    <div class="primebox-brand">
        {logo_html}
        <div class="header-divider"></div>
        <div class="header-info">
            <div class="header-title">
                Centro de Gravedad Logístico
            </div>
            <div class="header-subtitle">
                Modelo de localización y optimización de la red logística
            </div>
        </div>
    </div>
    <div class="header-right">
        <div class="header-badge">
            ● Modelo de localización
        </div>
        <div class="header-country">
            Operación logística · Ecuador
        </div>
    </div>
</div>
"""

if HTML_DEBUG:
    st.sidebar.write("🐞 Debug HTML")
    st.sidebar.write({
        "renderer": "st.html" if hasattr(st, "html") else "st.markdown",
        "streamlit_version": getattr(st, "__version__", "desconocida"),
        "logo_encontrado": bool(logo_base64),
        "logo_base64_chars": len(logo_base64 or ""),
        "header_html_chars": len(header_html),
        "header_empieza_con": repr(header_html[:80]),
        "header_tiene_img": "<img" in header_html.lower(),
        "header_tiene_data_uri": "data:image/png;base64," in header_html,
    })

render_html(header_html)


# =============================================================================
# TRANSFORMADORES DE COORDENADAS
# =============================================================================

@st.cache_resource
def get_transformers():

    return (
        Transformer.from_crs(
            "EPSG:4326",
            "EPSG:32717",
            always_xy=True
        ),
        Transformer.from_crs(
            "EPSG:32717",
            "EPSG:4326",
            always_xy=True
        )
    )


TO_UTM, FROM_UTM = get_transformers()


def latlon_a_utm(lat, lon):

    x, y = TO_UTM.transform(lon, lat)

    return x, y


def utm_a_latlon(x, y):

    lon, lat = FROM_UTM.transform(x, y)

    return lat, lon


# =============================================================================
# SHAPEFILE
# =============================================================================

@st.cache_data(show_spinner="Cargando mapa de provincias...")
def cargar_shapefile(path):

    gdf = gpd.read_file(path)

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:

        gdf = gdf.to_crs(epsg=4326)

    gdf["geometry"] = gdf["geometry"].simplify(
        0.005,
        preserve_topology=True
    )

    return gdf


@st.cache_data(show_spinner=False)
def geojson_base(path, provincia_sel):

    gdf = cargar_shapefile(path)

    features = []

    for _, row in gdf.iterrows():

        nombre = row.get(
            "DPA_DESPRO",
            ""
        )

        geo = row["geometry"]

        if geo is None:
            continue

        feat = {

            "type": "Feature",

            "geometry": json.loads(
                gpd.GeoSeries([geo]).to_json()
            )["features"][0]["geometry"],

            "properties": {
                "nombre": nombre,
                "sel": nombre == provincia_sel
            }
        }

        features.append(feat)

    return {
        "type": "FeatureCollection",
        "features": features
    }


@st.cache_data(show_spinner=False)
def restricciones_provincia(
    path,
    provincia_sel,
    tolerancia_m=2000
):

    gdf_orig = gpd.read_file(path)

    if (
        gdf_orig.crs is None
        or gdf_orig.crs.to_epsg() != 4326
    ):

        gdf_orig = gdf_orig.to_crs(
            epsg=4326
        )

    fila = gdf_orig[
        gdf_orig["DPA_DESPRO"] == provincia_sel
    ]

    if len(fila) == 0:

        return None, None, None, 0

    polygon = fila.iloc[0].geometry

    if polygon.geom_type == "MultiPolygon":

        polygon = max(
            polygon.geoms,
            key=lambda g: g.area
        )

    poly_utm = (
        gpd.GeoSeries(
            [polygon],
            crs="EPSG:4326"
        )
        .to_crs("EPSG:32717")
        .iloc[0]
    )

    poly_simp = poly_utm.simplify(
        tolerancia_m,
        preserve_topology=True
    )

    if not poly_simp.is_valid:

        poly_simp = poly_utm

    cx = poly_simp.centroid.x
    cy = poly_simp.centroid.y

    coords = list(
        poly_simp.exterior.coords
    )

    restr = []

    for i in range(
        len(coords) - 1
    ):

        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]

        dx = x2 - x1
        dy = y2 - y1

        L = np.sqrt(
            dx**2 + dy**2
        )

        if L < 1e-6:
            continue

        nx = -dy / L
        ny = dx / L

        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2

        if (
            nx * (cx - mx)
            + ny * (cy - my)
            < 0
        ):

            nx = -nx
            ny = -ny

        restr.append(
            (
                float(nx),
                float(ny),
                float(
                    nx*x1
                    + ny*y1
                )
            )
        )

    return (
        restr,
        (cx, cy),
        poly_utm,
        len(coords) - 1
    )


# =============================================================================
# DATOS PRIMEBOX
# =============================================================================

@st.cache_data
def nodos_default():

    raw = [

        {
            'ID': 'P1',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Papelera Nacional S. A.',
            'Latitud': -2.108505,
            'Longitud': -79.407321,
            'Tarifa': 1.822e-05,
            'Volumen': 122067
        },

        {
            'ID': 'P2',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Surpapelcorp S. A.',
            'Latitud': -2.202533,
            'Longitud': -79.814665,
            'Tarifa': 5.315e-05,
            'Volumen': 81378
        },

        {
            'ID': 'P3',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Nutec',
            'Latitud': -2.116317,
            'Longitud': -79.944281,
            'Tarifa': 0.00037556,
            'Volumen': 12150
        },

        {
            'ID': 'P4',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Indubras Ecuador S. A.',
            'Latitud': -2.06449,
            'Longitud': -79.949578,
            'Tarifa': 0.00174279,
            'Volumen': 2146.5
        },

        {
            'ID': 'P5',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Asmi Química',
            'Latitud': -2.065219,
            'Longitud': -79.938678,
            'Tarifa': 0.00059206,
            'Volumen': 6588
        },

        {
            'ID': 'P6',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Plásticos del Litoral S. A. (Plastlit)',
            'Latitud': -2.102696,
            'Longitud': -79.934435,
            'Tarifa': 0.00077249,
            'Volumen': 6075
        },

        {
            'ID': 'P7',
            'Tipo': 'Proveedor',
            'Ubicacion': 'Guayas',
            'Nombre': 'Plastiprint',
            'Latitud': -1.95611,
            'Longitud': -79.759942,
            'Tarifa': 0.00045518,
            'Volumen': 6075
        },

        {
            'ID': 'C8',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Mall del Sol',
            'Latitud': -2.154758,
            'Longitud': -79.891061,
            'Tarifa': 6.367e-05,
            'Volumen': 166045
        },

        {
            'ID': 'C9',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Durán',
            'Latitud': -2.177513,
            'Longitud': -79.825324,
            'Tarifa': 0.00044128,
            'Volumen': 12249
        },

        {
            'ID': 'C10',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Milagro',
            'Latitud': -2.135891,
            'Longitud': -79.594711,
            'Tarifa': 0.00038583,
            'Volumen': 6581
        },

        {
            'ID': 'C11',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Daule',
            'Latitud': -1.854495,
            'Longitud': -79.975986,
            'Tarifa': 0.00030078,
            'Volumen': 8219
        },

        {
            'ID': 'C12',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Playas',
            'Latitud': -2.642714,
            'Longitud': -80.385689,
            'Tarifa': 0.00149202,
            'Volumen': 1382
        },

        {
            'ID': 'C13',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pizza Hut – Riocentro Entre Ríos',
            'Latitud': -2.141236,
            'Longitud': -79.864472,
            'Tarifa': 0.00620713,
            'Volumen': 5296
        },

        {
            'ID': 'C14',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': "Papa John's – Urdesa",
            'Latitud': -2.170753,
            'Longitud': -79.908458,
            'Tarifa': 3.765e-05,
            'Volumen': 166045
        },

        {
            'ID': 'C15',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': "Papa John's – Alborada",
            'Latitud': -2.136605,
            'Longitud': -79.899899,
            'Tarifa': 5.555e-05,
            'Volumen': 166045
        },

        {
            'ID': 'C16',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': "Papa John's – Villa Club",
            'Latitud': -2.049535,
            'Longitud': -79.890505,
            'Tarifa': 0.00039839,
            'Volumen': 10273
        },

        {
            'ID': 'C17',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pastelería Adriana – Planta',
            'Latitud': -2.133409,
            'Longitud': -79.903442,
            'Tarifa': 0.00025018,
            'Volumen': 33209
        },

        {
            'ID': 'C18',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pastelería Adriana – Durán',
            'Latitud': -2.187642,
            'Longitud': -79.828093,
            'Tarifa': 0.00209281,
            'Volumen': 2450
        },

        {
            'ID': 'C19',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Chokolat – San Marino',
            'Latitud': -2.169115,
            'Longitud': -79.89792,
            'Tarifa': 0.0002461,
            'Volumen': 29519
        },

        {
            'ID': 'C20',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Chokolat – Riocentro Entre Ríos',
            'Latitud': -2.141769,
            'Longitud': -79.864444,
            'Tarifa': 0.03490279,
            'Volumen': 927
        },

        {
            'ID': 'C21',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Chokolat – Riocentro El Dorado',
            'Latitud': -2.054222,
            'Longitud': -79.873393,
            'Tarifa': 0.00238354,
            'Volumen': 1793
        },

        {
            'ID': 'C22',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Veredelicias',
            'Latitud': -2.225348,
            'Longitud': -79.922833,
            'Tarifa': 0.00021325,
            'Volumen': 18449
        },

        {
            'ID': 'C23',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pastelería Dolupa – Milagro',
            'Latitud': -2.127928,
            'Longitud': -79.592784,
            'Tarifa': 0.00240563,
            'Volumen': 1053
        },

        {
            'ID': 'C24',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Pyxis Industrias, Comercio y Representaciones S. A.',
            'Latitud': -2.121504,
            'Longitud': -79.93976,
            'Tarifa': 0.00010391,
            'Volumen': 46124
        },

        {
            'ID': 'C25',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Productora y Comercializadora Amigu S. A.',
            'Latitud': -2.196958,
            'Longitud': -79.884239,
            'Tarifa': 0.00014863,
            'Volumen': 36899
        },

        {
            'ID': 'C26',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Texalind S. A. S.',
            'Latitud': -2.188479,
            'Longitud': -79.890032,
            'Tarifa': 0.00017186,
            'Volumen': 34593
        },

        {
            'ID': 'C27',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Agilservicalza S. A. S.',
            'Latitud': -2.170607,
            'Longitud': -79.911496,
            'Tarifa': 0.00021843,
            'Volumen': 27674
        },

        {
            'ID': 'C28',
            'Tipo': 'Cliente',
            'Ubicacion': 'Guayas',
            'Nombre': 'Sportmedic S. A.',
            'Latitud': -2.132349,
            'Longitud': -79.903819,
            'Tarifa': 0.00029595,
            'Volumen': 27674
        },
    ]

    for n in raw:

        n["X_UTM"], n["Y_UTM"] = latlon_a_utm(
            n["Latitud"],
            n["Longitud"]
        )

    return pd.DataFrame(raw)


# =============================================================================
# SESSION STATE
# =============================================================================

if "nodos" not in st.session_state:

    st.session_state.nodos = nodos_default()


if "provincia_sel" not in st.session_state:

    st.session_state.provincia_sel = None


if "resultado" not in st.session_state:

    st.session_state.resultado = None


if "shp_path" not in st.session_state:
    st.session_state.shp_path = SHAPEFILE_PATH


# =============================================================================
# CALCULO ANALITICO
# =============================================================================

def calcular_cg_analitico(nodos_df):

    Xi = nodos_df["X_UTM"].values
    Yi = nodos_df["Y_UTM"].values

    Vi = (
        nodos_df["Volumen"]
        .values
        .astype(float)
    )

    Ri = (
        nodos_df["Tarifa"]
        .values
        .astype(float)
    )

    sum_xvr = np.sum(
        Xi * Vi * Ri
    )

    sum_yvr = np.sum(
        Yi * Vi * Ri
    )

    sum_vr = np.sum(
        Vi * Ri
    )

    return (
        sum_xvr / sum_vr,
        sum_yvr / sum_vr,
        sum_xvr,
        sum_yvr,
        sum_vr
    )


# =============================================================================
# OPTIMIZADOR
# =============================================================================

def fn_costo(
    xy,
    Xi,
    Yi,
    Vi,
    Ri
):

    dist = np.sqrt(
        (xy[0] - Xi)**2
        + (xy[1] - Yi)**2
    )

    dist = np.where(
        dist < 1e-6,
        1e-6,
        dist
    )

    return float(
        np.sum(
            Vi * Ri * dist
        )
    )


def optimizar_con_restriccion(
    nodos_df,
    restr,
    centroide,
    poly_utm
):

    from shapely.geometry import Point as SP

    Xi = (
        nodos_df["X_UTM"]
        .values
        .astype(float)
    )

    Yi = (
        nodos_df["Y_UTM"]
        .values
        .astype(float)
    )

    Vi = (
        nodos_df["Volumen"]
        .values
        .astype(float)
    )

    Ri = (
        nodos_df["Tarifa"]
        .values
        .astype(float)
    )

    sum_vr = np.sum(
        Vi * Ri
    )

    cgx_a = np.sum(
        Xi * Vi * Ri
    ) / sum_vr

    cgy_a = np.sum(
        Yi * Vi * Ri
    ) / sum_vr

    cx, cy = centroide

    constraints = [
        {
            "type": "ineq",
            "fun":
                lambda xy,
                nx=nx,
                ny=ny,
                c=c:
                    nx*xy[0]
                    + ny*xy[1]
                    - c
        }

        for nx, ny, c
        in restr
    ]

    opts = {
        "ftol": 1e-12,
        "maxiter": 5000,
        "disp": False
    }

    bounds = poly_utm.bounds

    xs = np.linspace(
        bounds[0] + 5000,
        bounds[2] - 5000,
        12
    )

    ys = np.linspace(
        bounds[1] + 5000,
        bounds[3] - 5000,
        12
    )

    grilla = []

    for gx in xs:

        for gy in ys:

            if poly_utm.contains(
                SP(gx, gy)
            ):

                d = np.sqrt(
                    (gx - Xi)**2
                    + (gy - Yi)**2
                )

                grilla.append(
                    (
                        float(
                            np.sum(
                                Vi * Ri * d
                            )
                        ),
                        [gx, gy]
                    )
                )

    grilla.sort(
        key=lambda x: x[0]
    )

    puntos = (
        [g[1] for g in grilla[:5]]
        + [
            [cgx_a, cgy_a],
            [cx, cy],
            [
                float(np.mean(Xi)),
                float(np.mean(Yi))
            ],
            [
                (cgx_a + cx) / 2,
                (cgy_a + cy) / 2
            ]
        ]
    )

    for ddx in [
        -20000,
        0,
        20000
    ]:

        for ddy in [
            -20000,
            0,
            20000
        ]:

            puntos.append(
                [
                    cgx_a + ddx,
                    cgy_a + ddy
                ]
            )

    mejor = None

    for x0 in puntos:

        try:

            res = minimize(
                fn_costo,
                x0=x0,
                args=(
                    Xi,
                    Yi,
                    Vi,
                    Ri
                ),
                method="SLSQP",
                constraints=constraints,
                options=opts
            )

            if poly_utm.contains(
                SP(
                    res.x[0],
                    res.x[1]
                )
            ):

                if (
                    mejor is None
                    or res.fun < mejor.fun
                ):

                    mejor = res

        except Exception:

            continue

    if mejor is None:

        for x0 in puntos:

            try:

                res = minimize(
                    fn_costo,
                    x0=x0,
                    args=(
                        Xi,
                        Yi,
                        Vi,
                        Ri
                    ),
                    method="SLSQP",
                    constraints=constraints,
                    options=opts
                )

                if (
                    res.success
                    and (
                        mejor is None
                        or res.fun < mejor.fun
                    )
                ):

                    mejor = res

            except Exception:

                continue

    return mejor


# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

def calcular_tabla(
    nodos_df,
    cgx,
    cgy
):

    rows = []

    for _, n in nodos_df.iterrows():

        xi = n["X_UTM"]
        yi = n["Y_UTM"]

        vi = float(
            n["Volumen"]
        )

        ri = float(
            n["Tarifa"]
        )

        dist = np.sqrt(
            (xi-cgx)**2
            + (yi-cgy)**2
        )

        rows.append({

            "ID": n["ID"],

            "Tipo": n["Tipo"],

            "Nombre": n["Nombre"],

            "Ubicacion":
                n["Ubicacion"],

            "Volumen":
                int(vi),

            "Tarifa":
                ri,

            "X UTM (m)":
                xi,

            "Y UTM (m)":
                yi,

            "Xi·Vi·Ri":
                xi*vi*ri,

            "Yi·Vi·Ri":
                yi*vi*ri,

            "Vi·Ri":
                vi*ri,

            "Distancia (m)":
                dist,

            "Costo (USD)":
                vi*ri*dist,
        })

    return pd.DataFrame(rows)


# =============================================================================
# MAPA PRIMEBOX
# =============================================================================

def construir_mapa(
    shp_path,
    nodos_df,
    prov_sel,
    resultado
):

    m = folium.Map(
        location=[
            -1.65,
            -78.5
        ],
        zoom_start=7,
        tiles="OpenStreetMap",
        prefer_canvas=True,
        control_scale=True
    )

    gj = geojson_base(
        shp_path,
        prov_sel
    )

    folium.GeoJson(
        gj,

        style_function=
        lambda f: {

            "fillColor":
                BLUE
                if f["properties"]["sel"]
                else "#EEF4FA",

            "color":
                NAVY
                if f["properties"]["sel"]
                else "#AFC1D4",

            "weight":
                2.2
                if f["properties"]["sel"]
                else 0.8,

            "fillOpacity":
                0.16
                if f["properties"]["sel"]
                else 0.08,
        },

        tooltip=
        folium.GeoJsonTooltip(
            fields=["nombre"],
            aliases=["Provincia:"]
        ),

    ).add_to(m)


    # -------------------------------------------------------------------------
    # NODOS
    # -------------------------------------------------------------------------

    for _, n in nodos_df.iterrows():

        proveedor = (
            n["Tipo"]
            == "Proveedor"
        )

        color = (
            ORANGE
            if proveedor
            else BLUE
        )

        tipo_label = (
            "PROVEEDOR"
            if proveedor
            else "CLIENTE"
        )

        tooltip = f"""
        <div style="
            font-family:Inter,Arial;
            min-width:210px;
            padding:4px;
        ">

            <div style="
                font-size:9px;
                color:{color};
                font-weight:700;
                letter-spacing:.7px;
                margin-bottom:4px;
            ">
                {tipo_label}
            </div>

            <div style="
                font-size:13px;
                font-weight:700;
                color:#0B3768;
                margin-bottom:8px;
            ">
                {n['Nombre']}
            </div>

            <div style="
                color:#64748B;
                font-size:10px;
                line-height:1.8;
            ">
                Volumen:
                <b>
                    {n['Volumen']:,.0f}
                </b>
                <br>

                Tarifa:
                <b>
                    ${n['Tarifa']:.6f}
                </b>
            </div>

        </div>
        """

        folium.CircleMarker(

            location=[
                n["Latitud"],
                n["Longitud"]
            ],

            radius=6.5,

            color=WHITE,

            weight=2,

            fill=True,

            fill_color=color,

            fill_opacity=1,

            tooltip=tooltip

        ).add_to(m)


    # -------------------------------------------------------------------------
    # RESULTADO
    # -------------------------------------------------------------------------

    if resultado is not None:

        cgx = resultado["cgx"]
        cgy = resultado["cgy"]

        lat_cg, lon_cg = utm_a_latlon(
            cgx,
            cgy
        )


        # LINEAS
        for _, n in nodos_df.iterrows():

            proveedor = (
                n["Tipo"]
                == "Proveedor"
            )

            folium.PolyLine(

                [
                    [lat_cg, lon_cg],
                    [
                        n["Latitud"],
                        n["Longitud"]
                    ]
                ],

                color=(
                    ORANGE
                    if proveedor
                    else BLUE
                ),

                weight=1,

                opacity=.25,

                dash_array="5,7"

            ).add_to(m)


        # HALO CG
        folium.CircleMarker(

            location=[
                lat_cg,
                lon_cg
            ],

            radius=17,

            color=ORANGE,

            weight=2,

            fill=True,

            fill_color=ORANGE,

            fill_opacity=.12

        ).add_to(m)


        tooltip_cg = f"""
        <div style="
            font-family:Inter,Arial;
            min-width:230px;
            padding:5px;
        ">

            <div style="
                font-size:9px;
                letter-spacing:.8px;
                color:{ORANGE};
                font-weight:800;
                margin-bottom:5px;
            ">
                CENTRO DE GRAVEDAD PRIMEBOX
            </div>

            <div style="
                font-size:12px;
                font-weight:700;
                color:{NAVY};
            ">
                Ubicación óptima
            </div>

            <div style="
                margin-top:7px;
                color:#64748B;
                font-size:10px;
                line-height:1.8;
            ">

                X UTM:
                <b>
                    {cgx:,.2f} m
                </b>
                <br>

                Y UTM:
                <b>
                    {cgy:,.2f} m
                </b>
                <br>

                Costo:
                <b style="color:{ORANGE}">
                    ${resultado['costo_total']:,.2f}
                </b>

            </div>

        </div>
        """


        folium.CircleMarker(

            location=[
                lat_cg,
                lon_cg
            ],

            radius=10,

            color=WHITE,

            weight=3,

            fill=True,

            fill_color=NAVY,

            fill_opacity=1,

            tooltip=tooltip_cg

        ).add_to(m)


        folium.CircleMarker(

            location=[
                lat_cg,
                lon_cg
            ],

            radius=3.5,

            color=ORANGE,

            fill=True,

            fill_color=ORANGE,

            fill_opacity=1

        ).add_to(m)


    return m


# =============================================================================
# CONFIGURACION GRAFICOS PLOTLY
# =============================================================================

def aplicar_estilo_plotly(
    fig,
    height=400,
    bottom=40
):
    COLOR_TEXTO = "#111827"
    COLOR_GRID = "#CBD5E1"

    fig.update_layout(
        height=height,

        margin=dict(
            l=15,
            r=15,
            t=20,
            b=bottom
        ),

        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Inter",
            color=COLOR_TEXTO,
            size=11
        ),

        xaxis=dict(
            color=COLOR_TEXTO,

            tickfont=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=10
            ),

            title_font=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=11
            ),

            gridcolor=COLOR_GRID,
            zerolinecolor=COLOR_GRID
        ),

        yaxis=dict(
            color=COLOR_TEXTO,

            tickfont=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=10
            ),

            title_font=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=11
            ),

            gridcolor=COLOR_GRID,
            zerolinecolor=COLOR_GRID
        ),

        legend=dict(
            font=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=10
            )
        ),

        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=COLOR_GRID,

            font=dict(
                family="Inter",
                color=COLOR_TEXTO,
                size=11
            )
        )
    )

    fig.update_traces(
        textfont=dict(
            family="Inter",
            color=COLOR_TEXTO
        )
    )

    return fig

# =============================================================================
# TABS
# =============================================================================

tab1, tab2, tab3 = st.tabs(
    [
        "⌖  Mapa y Optimización",
        "▦  Red Logística",
        "◫  Resultados"
    ]
)


# =============================================================================
# TAB 2 - RED LOGISTICA
# =============================================================================

with tab2:

    render_html(
        """
        <div class="section-header">
            Configuración de la Red
        </div>

        <div class="section-subtitle">
            Administra la cartografía y los nodos que forman parte
            del modelo logístico.
        </div>
        """
    )


    render_html(
        """
        <div class="section-header">
            Nodos de la Red Logística
        </div>
        """
    )


    df_n = st.session_state.nodos

    total_nodos = len(df_n)

    proveedores = len(
        df_n[
            df_n["Tipo"]
            == "Proveedor"
        ]
    )

    clientes = len(
        df_n[
            df_n["Tipo"]
            == "Cliente"
        ]
    )

    volumen_total = float(
        df_n["Volumen"]
        .sum()
    )

    demanda = float(
        df_n[
            df_n["Tipo"]
            == "Cliente"
        ]["Volumen"]
        .sum()
    )


    k1, k2, k3, k4, k5 = st.columns(5)


    cards = [

        (
            k1,
            "Total de nodos",
            f"{total_nodos:,}",
            "Red completa",
            "navy"
        ),

        (
            k2,
            "Proveedores",
            f"{proveedores:,}",
            "Nodos de suministro",
            "orange"
        ),

        (
            k3,
            "Clientes",
            f"{clientes:,}",
            "Nodos de demanda",
            "blue"
        ),

        (
            k4,
            "Volumen total",
            f"{volumen_total:,.0f}",
            "unidades",
            "navy"
        ),

        (
            k5,
            "Demanda total",
            f"{demanda:,.0f}",
            "unidades clientes",
            "blue"
        )
    ]


    for (
        col,
        label,
        value,
        sub,
        color
    ) in cards:

        with col:

            render_html(
                f"""
                <div class="kpi-card kpi-{color}">
                    <div class="kpi-label">
                        {label}
                    </div>
                    <div class="kpi-value">
                        {value}
                    </div>
                    <div class="kpi-bottom">
                        {sub}
                    </div>
                </div>
                """
            )


    st.write("")


    df_edit = st.data_editor(

        st.session_state.nodos,

        num_rows="dynamic",

        use_container_width=True,

        height=530,

        column_config={

            "ID":
                st.column_config.TextColumn(
                    "ID",
                    width="small"
                ),

            "Tipo":
                st.column_config.SelectboxColumn(
                    "Tipo",
                    options=[
                        "Cliente",
                        "Proveedor"
                    ]
                ),

            "Nombre":
                st.column_config.TextColumn(
                    "Nombre",
                    width="large"
                ),

            "Ubicacion":
                st.column_config.TextColumn(
                    "Provincia"
                ),

            "Tarifa":
                st.column_config.NumberColumn(
                    "Tarifa",
                    format="$%.6f"
                ),

            "Volumen":
                st.column_config.NumberColumn(
                    "Volumen",
                    format="%.0f"
                ),

            "Latitud":
                st.column_config.NumberColumn(
                    "Latitud",
                    format="%.7f"
                ),

            "Longitud":
                st.column_config.NumberColumn(
                    "Longitud",
                    format="%.7f"
                ),

            "X_UTM":
                st.column_config.NumberColumn(
                    "X UTM",
                    format="%.3f"
                ),

            "Y_UTM":
                st.column_config.NumberColumn(
                    "Y UTM",
                    format="%.3f"
                ),
        }
    )


    save_col, blank = st.columns(
        [1.2, 4]
    )

    with save_col:

        if st.button(
            "💾 Guardar cambios",
            use_container_width=True
        ):

            st.session_state.nodos = (
                df_edit.copy()
            )

            st.session_state.resultado = None

            st.success(
                "Red logística actualizada."
            )


# =============================================================================
# TAB 1 - MAPA Y OPTIMIZACION
# =============================================================================

with tab1:

    col_config, col_map = st.columns(
        [1.05, 2.95],
        gap="large"
    )


    # -------------------------------------------------------------------------
    # CONFIGURACION
    # -------------------------------------------------------------------------

    with col_config:

        render_html(
            """
            <div class="section-header">
                Configuración
            </div>
            """
        )


        shp_ok = os.path.exists(
            st.session_state.shp_path
        )   


        if shp_ok:

            gdf_c = cargar_shapefile(
                st.session_state.shp_path
            )

            provincias = sorted(
                gdf_c[
                    "DPA_DESPRO"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            idx = 0

            if (
                st.session_state.provincia_sel
                in provincias
            ):

                idx = (
                    provincias.index(
                        st.session_state.provincia_sel
                    )
                    + 1
                )

            opcion = st.selectbox(

                "Restricción geográfica",

                [
                    "Sin restricción · Modelo libre"
                ]
                + provincias,

                index=idx
            )

            st.session_state.provincia_sel = (

                None

                if opcion.startswith(
                    "Sin restricción"
                )

                else opcion
            )


            if st.session_state.provincia_sel:

                render_html(
                    f"""
                    <div class="province-badge">
                        📍 &nbsp;
                        {st.session_state.provincia_sel}
                    </div>
                    """
                )

                st.caption(
                    "El centro óptimo permanecerá dentro de esta provincia."
                )

            else:

                st.caption(
                    "Modelo libre mediante fórmula analítica."
                )

        st.write("")


        # ---------------------------------------------------------------------
        # LEYENDA
        # ---------------------------------------------------------------------

        render_html(
            """
            <div class="section-header">
                Leyenda
            </div>
            """
        )


        render_html(
            f"""
            <div style="
                background:white;
                border:1px solid {BORDER};
                border-radius:12px;
                padding:13px 15px;
                margin-bottom:14px;
            ">

                <div style="
                    display:flex;
                    align-items:center;
                    font-size:11px;
                    color:{TEXT_SECONDARY};
                    margin-bottom:9px;
                ">

                    <span style="
                        display:inline-block;
                        width:10px;
                        height:10px;
                        border-radius:50%;
                        background:{ORANGE};
                        margin-right:9px;
                    ">
                    </span>

                    Proveedor

                </div>


                <div style="
                    display:flex;
                    align-items:center;
                    font-size:11px;
                    color:{TEXT_SECONDARY};
                    margin-bottom:9px;
                ">

                    <span style="
                        display:inline-block;
                        width:10px;
                        height:10px;
                        border-radius:50%;
                        background:{BLUE};
                        margin-right:9px;
                    ">
                    </span>

                    Cliente

                </div>


                <div style="
                    display:flex;
                    align-items:center;
                    font-size:11px;
                    color:{TEXT_SECONDARY};
                ">

                    <span style="
                        display:inline-block;
                        width:10px;
                        height:10px;
                        border-radius:50%;
                        background:{NAVY};
                        border:2px solid {ORANGE};
                        margin-right:9px;
                    ">
                    </span>

                    Centro de gravedad

                </div>

            </div>
            """
        )


        # ---------------------------------------------------------------------
        # CALCULO
        # ---------------------------------------------------------------------

        if st.button(
            "Calcular Centro de Gravedad",
            type="primary",
            use_container_width=True
        ):

            nodos_df = (
                st.session_state.nodos.copy()
            )

            try:

                if (
                    st.session_state.provincia_sel
                    and shp_ok
                ):

                    with st.spinner(
                        "Preparando restricciones geográficas..."
                    ):

                        (
                            restr,
                            centroide,
                            poly_utm,
                            n_restr
                        ) = restricciones_provincia(

                            st.session_state.shp_path,

                            st.session_state.provincia_sel
                        )


                    if restr is None:

                        st.error(
                            "Provincia no encontrada."
                        )

                        st.stop()


                    with st.spinner(
                        "Optimizando localización..."
                    ):

                        opt = optimizar_con_restriccion(

                            nodos_df,

                            restr,

                            centroide,

                            poly_utm
                        )


                    if opt is None:

                        raise ValueError(
                            "El optimizador no encontró una solución válida."
                        )


                    if not opt.success:

                        st.warning(
                            f"Solver: {opt.message}"
                        )


                    cgx = opt.x[0]
                    cgy = opt.x[1]


                else:

                    (
                        cgx,
                        cgy,
                        _,
                        _,
                        _
                    ) = calcular_cg_analitico(
                        nodos_df
                    )


                df_tabla = calcular_tabla(
                    nodos_df,
                    cgx,
                    cgy
                )


                costo_total = float(
                    df_tabla[
                        "Costo (USD)"
                    ]
                    .sum()
                )


                st.session_state.resultado = {

                    "cgx":
                        cgx,

                    "cgy":
                        cgy,

                    "costo_total":
                        costo_total,

                    "df_tabla":
                        df_tabla,

                    "provincia":
                        st.session_state.provincia_sel,
                }


                st.success(
                    "Optimización completada correctamente."
                )


            except Exception as e:

                st.error(
                    f"No fue posible completar el cálculo: {e}"
                )


        # ---------------------------------------------------------------------
        # RESULTADO
        # ---------------------------------------------------------------------

        if (
            st.session_state.resultado
            is not None
        ):

            r = (
                st.session_state.resultado
            )


            lat_r, lon_r = utm_a_latlon(
                r["cgx"],
                r["cgy"]
            )

            google_maps_url = (
                  f"https://www.google.com/maps/search/?api=1"
                  f"&query={lat_r:.8f}%2C{lon_r:.8f}"
            )

            street_view_url = (
                 f"https://www.google.com/maps/@?api=1"
                 f"&map_action=pano"
                 f"&viewpoint={lat_r:.8f}%2C{lon_r:.8f}"
            )
            render_html(
                """
                <div class="section-header">
                    Resultado Óptimo
                </div>
                """
            )


            render_html(
                f"""
                <div class="result-card">

                    <div class="result-label">
                        Costo logístico óptimo
                    </div>

                    <div class="result-cost">
                        <span>$</span>
                        {r['costo_total']:,.2f}
                    </div>

                    <div class="result-sub">
                        USD · costo ponderado total
                    </div>

                </div>


                <div class="coord-grid">

                    <div class="coord-card">

                        <div class="coord-label">
                            CGx · UTM 17S
                        </div>

                        <div class="coord-value">
                            {r['cgx']:,.2f} m
                        </div>

                    </div>


                    <div class="coord-card">

                        <div class="coord-label">
                            CGy · UTM 17S
                        </div>

                        <div class="coord-value">
                            {r['cgy']:,.2f} m
                        </div>

                    </div>


                    <div class="coord-card">

                        <div class="coord-label">
                            Latitud
                        </div>

                        <div class="coord-value">
                            {lat_r:.6f}°
                        </div>

                    </div>


                    <div class="coord-card">

                        <div class="coord-label">
                            Longitud
                        </div>

                        <div class="coord-value">
                            {lon_r:.6f}°
                        </div>

                    </div>

                </div>
                """
            )

            st.write("")

            map_col1, map_col2 = st.columns(2)

            with map_col1:
                 st.link_button(
                 "📍 Abrir en Google Maps",
                 google_maps_url,
                 use_container_width=True
            )

            with map_col2:
                  st.link_button(
                  "🚶 Ver en Street View",
                  street_view_url,
                  use_container_width=True
            )
    # -------------------------------------------------------------------------
    # MAPA
    # -------------------------------------------------------------------------

    with col_map:

        render_html(
            """
            <div class="section-header">
                Localización Geográfica
            </div>
            """
        )


        render_html(
            """
            <div class="section-subtitle">
                Distribución espacial de proveedores, clientes y
                ubicación óptima calculada.
            </div>
            """
        )


        if shp_ok:

            with st.spinner(
                "Generando mapa..."
            ):

                mapa = construir_mapa(

                    st.session_state.shp_path,

                    st.session_state.nodos,

                    st.session_state.provincia_sel,

                    st.session_state.resultado
                )


            st_folium(
                mapa,
                width=None,
                height=650,
                returned_objects=[]
            )


        else:

            render_html(
                f"""
                <div style="
                    height:500px;
                    display:flex;
                    align-items:center;
                    justify-content:center;

                    background:white;

                    border-radius:16px;

                    border:1px solid {BORDER};

                    box-shadow:
                        0px 3px 14px
                        rgba(15,23,42,.04);
                ">

                    <div style="
                        text-align:center;
                        max-width:300px;
                    ">

                        <div style="
                            width:60px;
                            height:60px;

                            display:flex;
                            align-items:center;
                            justify-content:center;

                            margin:0 auto 16px;

                            border-radius:15px;

                            background:{BLUE_LIGHT};

                            color:{BLUE};

                            font-size:26px;
                        ">
                            ⌖
                        </div>

                        <div style="
                            font-size:14px;
                            font-weight:700;

                            color:{NAVY};

                            margin-bottom:5px;
                        ">
                            Mapa no disponible
                        </div>

                        <div style="
                            color:{TEXT_SECONDARY};

                            font-size:11px;

                            line-height:1.6;
                        ">
                            Carga el shapefile de provincias desde
                            la pestaña Red Logística para visualizar
                            la red.
                        </div>

                    </div>

                </div>
                """
            )


# =============================================================================
# TAB 3 - RESULTADOS
# =============================================================================

with tab3:

    if (
        st.session_state.resultado
        is not None
    ):

        import plotly.express as px
        import plotly.graph_objects as go


        r = st.session_state.resultado

        df_res = r[
            "df_tabla"
        ]


        lat_r, lon_r = utm_a_latlon(
            r["cgx"],
            r["cgy"]
        )


        modo = (

            f"Restricción geográfica · {r['provincia']}"

            if r["provincia"]

            else "Modelo libre · Fórmula analítica"
        )


        render_html(
            """
            <div class="section-header">
                Dashboard Ejecutivo
            </div>

            <div class="section-subtitle">
                Indicadores principales del modelo de localización
                y desempeño de la red logística.
            </div>
            """
        )


        render_html(
            f"""
            <div style="
                display:inline-flex;
                align-items:center;

                background:{BLUE_LIGHT};

                color:{NAVY};

                border-radius:8px;

                padding:7px 12px;

                font-size:10px;

                font-weight:600;

                margin-bottom:13px;
            ">

                <span style="
                    width:6px;
                    height:6px;

                    background:{BLUE};

                    border-radius:50%;

                    margin-right:7px;
                ">
                </span>

                {modo}

            </div>
            """
        )


        # ---------------------------------------------------------------------
        # KPIS
        # ---------------------------------------------------------------------

        costo_prov = (
            df_res[
                df_res["Tipo"]
                == "Proveedor"
            ]["Costo (USD)"]
            .sum()
        )


        costo_cli = (
            df_res[
                df_res["Tipo"]
                == "Cliente"
            ]["Costo (USD)"]
            .sum()
        )


        dist_max = (
            df_res[
                "Distancia (m)"
            ].max()
            / 1000
        )


        dist_min = (
            df_res[
                "Distancia (m)"
            ].min()
            / 1000
        )


        dist_prom = (
            df_res[
                "Distancia (m)"
            ].mean()
            / 1000
        )


        nodo_critico = (
            df_res.loc[
                df_res[
                    "Costo (USD)"
                ].idxmax(),
                "Nombre"
            ]
        )


        k1, k2, k3, k4, k5, k6 = (
            st.columns(6)
        )


        dashboard_cards = [

            (
                k1,
                "Costo Total",
                f"${r['costo_total']:,.0f}",
                "Costo óptimo",
                "navy"
            ),

            (
                k2,
                "Proveedores",
                f"${costo_prov:,.0f}",
                "Costo suministro",
                "orange"
            ),

            (
                k3,
                "Clientes",
                f"${costo_cli:,.0f}",
                "Costo distribución",
                "blue"
            ),

            (
                k4,
                "Distancia Máx.",
                f"{dist_max:,.1f} km",
                "Nodo más lejano",
                "orange"
            ),

            (
                k5,
                "Distancia Mín.",
                f"{dist_min:,.1f} km",
                "Nodo más cercano",
                "blue"
            ),

            (
                k6,
                "Distancia Media",
                f"{dist_prom:,.1f} km",
                "Promedio red",
                "navy"
            )
        ]


        for (
            col,
            label,
            value,
            sub,
            color
        ) in dashboard_cards:

            with col:

                render_html(
                    f"""
                    <div class="kpi-card kpi-{color}">

                        <div class="kpi-label">
                            {label}
                        </div>

                        <div class="kpi-value"
                            style="font-size:18px">
                            {value}
                        </div>

                        <div class="kpi-bottom">
                            {sub}
                        </div>

                    </div>
                    """
                )


        render_html("<br>")


        # =====================================================================
        # GRAFICOS FILA 1
        # =====================================================================

        ga, gb = st.columns(
            2,
            gap="large"
        )


        # ---------------------------------------------------------------------
        # COSTO POR NODO
        # ---------------------------------------------------------------------

        with ga:

            render_html(
                """
                <div class="section-header">
                    Costo por Nodo
                </div>
                """
            )


            df_bar = (
                df_res
                .sort_values(
                    "Costo (USD)",
                    ascending=True
                )
                .copy()
            )


            df_bar["color"] = (
                df_bar["Tipo"]
                .map({
                    "Proveedor":
                        ORANGE,

                    "Cliente":
                        BLUE
                })
            )


            fig_bar = go.Figure(

                go.Bar(

                    x=
                        df_bar[
                            "Costo (USD)"
                        ],

                    y=
                        df_bar[
                            "Nombre"
                        ],

                    orientation="h",

                    marker=dict(
                        color=
                            df_bar[
                                "color"
                            ].tolist()
                    ),

                    text=
                        df_bar[
                            "Costo (USD)"
                        ]
                        .apply(
                            lambda v:
                                f"${v:,.0f}"
                        ),

                    textposition="outside",

                    textfont=dict(
                        size=9,
                        color= "#172033"
                    ),

                    hovertemplate=
                        "<b>%{y}</b>"
                        "<br>Costo: $%{x:,.2f}"
                        "<extra></extra>"
                )
            )


            aplicar_estilo_plotly(
                fig_bar,
                height=510
            )


            fig_bar.update_layout(

                xaxis=dict(
                    showgrid=True,
                    gridcolor="#EEF2F7",
                    zeroline=False,
                    title=None,
                    tickprefix="$"
                ),

                yaxis=dict(
                    showgrid=False,
                    title=None,
                    tickfont=dict(
                        size=9
                    )
                ),

                showlegend=False
            )


            st.plotly_chart(
                fig_bar,
                use_container_width=True
            )


        # ---------------------------------------------------------------------
        # DONUT
        # ---------------------------------------------------------------------

        with gb:

            render_html(
                """
                <div class="section-header">
                    Distribución del Costo
                </div>
                """
            )


            df_tipo = (

                df_res

                .groupby(
                    "Tipo"
                )["Costo (USD)"]

                .sum()

                .reset_index()
            )


            color_map = {

                "Proveedor":
                    ORANGE,

                "Cliente":
                    BLUE
            }


            fig_pie = go.Figure(

                go.Pie(

                    labels=
                        df_tipo[
                            "Tipo"
                        ],

                    values=
                        df_tipo[
                            "Costo (USD)"
                        ],

                    hole=.67,

                    sort=False,

                    marker=dict(

                        colors=[
                            color_map[x]
                            for x
                            in df_tipo[
                                "Tipo"
                            ]
                        ],

                        line=dict(
                            color=WHITE,
                            width=4
                        )
                    ),

                    textinfo=
                        "label+percent",

                    textfont=dict(
                        size=11
                    ),

                    hovertemplate=
                        "<b>%{label}</b>"
                        "<br>$%{value:,.2f}"
                        "<br>%{percent}"
                        "<extra></extra>"
                )
            )


            aplicar_estilo_plotly(
                fig_pie,
                height=510
            )


            fig_pie.update_layout(

                showlegend=True,

                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-.05,
                    xanchor="center",
                    x=.5
                )
            )


            fig_pie.add_annotation(

                text=(
                    "<span style='font-size:10px;color:#64748B'>"
                    "COSTO TOTAL"
                    "</span>"
                    f"<br><b>${r['costo_total']:,.0f}</b>"
                ),

                x=.5,
                y=.5,

                showarrow=False,

                font=dict(
                    size=18,
                    color=NAVY
                )
            )


            st.plotly_chart(
                fig_pie,
                use_container_width=True
            )


        # =====================================================================
        # GRAFICOS FILA 2
        # =====================================================================

        gc, gd = st.columns(
            2,
            gap="large"
        )


        # ---------------------------------------------------------------------
        # DISTANCIAS
        # ---------------------------------------------------------------------

        with gc:

            render_html(
                """
                <div class="section-header">
                    Distancia al Centro de Gravedad
                </div>
                """
            )


            df_dist = (
                df_res
                .sort_values(
                    "Distancia (m)",
                    ascending=False
                )
                .copy()
            )


            df_dist["Dist_km"] = (
                df_dist[
                    "Distancia (m)"
                ]
                / 1000
            )


            df_dist["color"] = (
                df_dist["Tipo"]
                .map({
                    "Proveedor":
                        ORANGE,

                    "Cliente":
                        BLUE
                })
            )


            fig_dist = go.Figure(

                go.Bar(

                    x=
                        df_dist[
                            "Nombre"
                        ],

                    y=
                        df_dist[
                            "Dist_km"
                        ],

                    marker_color=
                        df_dist[
                            "color"
                        ].tolist(),

                    text=
                        df_dist[
                            "Dist_km"
                        ]
                        .apply(
                            lambda v:
                                f"{v:,.1f}"
                        ),

                    textposition=
                        "outside",

                    textfont=dict(
                        size=8
                    ),

                    hovertemplate=
                        "<b>%{x}</b>"
                        "<br>Distancia: %{y:.2f} km"
                        "<extra></extra>"
                )
            )


            aplicar_estilo_plotly(
                fig_dist,
                height=390,
                bottom=115
            )


            fig_dist.update_layout(

                xaxis=dict(
                    showgrid=False,
                    tickangle=-42,
                    tickfont=dict(
                        size=8
                    ),
                    title=None
                ),

                yaxis=dict(
                    showgrid=True,
                    gridcolor="#EEF2F7",
                    zeroline=False,
                    title="km"
                ),

                showlegend=False
            )


            st.plotly_chart(
                fig_dist,
                use_container_width=True
            )


        # ---------------------------------------------------------------------
        # VOLUMEN VS COSTO
        # ---------------------------------------------------------------------

        with gd:

            render_html(
                """
                <div class="section-header">
                    Volumen vs. Costo
                </div>
                """
            )


            fig_scat = px.scatter(

                df_res,

                x="Volumen",

                y="Costo (USD)",

                color="Tipo",

                size="Distancia (m)",

                hover_name="Nombre",

                hover_data={

                    "Ubicacion": True,

                    "Tarifa": ":.6f",

                    "Distancia (m)": ":.0f",

                    "Volumen": ":,.0f",

                    "Costo (USD)": ":,.2f"
                },

                color_discrete_map={

                    "Proveedor":
                        ORANGE,

                    "Cliente":
                        BLUE
                },

                size_max=32
            )


            aplicar_estilo_plotly(
                fig_scat,
                height=390
            )


            fig_scat.update_layout(

                xaxis=dict(
                    showgrid=True,
                    gridcolor="#EEF2F7",
                    zeroline=False,
                    title="Volumen"
                ),

                yaxis=dict(
                    showgrid=True,
                    gridcolor="#EEF2F7",
                    zeroline=False,
                    title="Costo (USD)"
                ),

                legend=dict(
                    title="",
                    orientation="h",
                    x=.5,
                    xanchor="center",
                    y=1.08,
                    yanchor="bottom"
                )
            )


            fig_scat.update_traces(

                marker=dict(
                    line=dict(
                        color=WHITE,
                        width=1.2
                    )
                )
            )


            st.plotly_chart(
                fig_scat,
                use_container_width=True
            )


        # =====================================================================
        # INFLUENCIA
        # =====================================================================

        render_html(
            """
            <div class="section-header">
                Influencia de Cada Nodo en la Localización
            </div>

            <div class="section-subtitle">
                Peso ponderado Vi·Ri utilizado por el modelo para
                determinar el centro de gravedad.
            </div>
            """
        )


        df_peso = (
            df_res
            .sort_values(
                "Vi·Ri",
                ascending=False
            )
            .copy()
        )


        df_peso["color"] = (
            df_peso["Tipo"]
            .map({

                "Proveedor":
                    ORANGE,

                "Cliente":
                    BLUE
            })
        )


        fig_peso = go.Figure(

            go.Bar(

                x=
                    df_peso[
                        "Nombre"
                    ],

                y=
                    df_peso[
                        "Vi·Ri"
                    ],

                marker_color=
                    df_peso[
                        "color"
                    ].tolist(),

                hovertemplate=
                    "<b>%{x}</b>"
                    "<br>Vi·Ri: %{y:.5f}"
                    "<extra></extra>"
            )
        )


        aplicar_estilo_plotly(
            fig_peso,
            height=350,
            bottom=115
        )


        fig_peso.update_layout(

            xaxis=dict(
                showgrid=False,
                tickangle=-42,
                tickfont=dict(
                    size=8
                ),
                title=None
            ),

            yaxis=dict(
                showgrid=True,
                gridcolor="#EEF2F7",
                zeroline=False,
                title="Vi·Ri"
            ),

            showlegend=False
        )


        st.plotly_chart(
            fig_peso,
            use_container_width=True
        )


        # =====================================================================
        # NODO CRITICO
        # =====================================================================

        costo_nodo_critico = float(

            df_res.loc[
                df_res[
                    "Costo (USD)"
                ].idxmax(),
                "Costo (USD)"
            ]
        )


        porcentaje_critico = (

            costo_nodo_critico
            / r["costo_total"]
            * 100

            if r["costo_total"] > 0

            else 0
        )


        render_html(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:space-between;

                background:{ORANGE_LIGHT};

                border:1px solid rgba(247,100,0,.15);

                border-radius:13px;

                padding:15px 18px;

                margin-top:5px;
                margin-bottom:20px;
            ">

                <div>

                    <div style="
                        font-size:9px;
                        color:{ORANGE_DARK};
                        font-weight:800;
                        text-transform:uppercase;
                        letter-spacing:.7px;
                        margin-bottom:4px;
                    ">
                        Nodo con mayor incidencia en costo
                    </div>

                    <div style="
                        font-size:13px;
                        color:{NAVY_DARK};
                        font-weight:700;
                    ">
                        {nodo_critico}
                    </div>

                </div>

                <div style="
                    text-align:right;
                ">

                    <div style="
                        color:{NAVY_DARK};
                        font-size:17px;
                        font-weight:800;
                    ">
                        ${costo_nodo_critico:,.2f}
                    </div>

                    <div style="
                        color:{TEXT_SECONDARY};
                        font-size:9px;
                    ">
                        {porcentaje_critico:.1f}% del costo total
                    </div>

                </div>

            </div>
            """
        )


        # =====================================================================
        # TABLA
        # =====================================================================

        render_html(
            """
            <div class="section-header">
                Detalle General de Resultados
            </div>

            <div class="section-subtitle">
                Desglose técnico de las variables utilizadas en el
                cálculo del centro de gravedad.
            </div>
            """
        )


        df_display = (
            df_res.copy()
        )


        for col in [

            "X UTM (m)",
            "Y UTM (m)",
            "Xi·Vi·Ri",
            "Yi·Vi·Ri",
            "Vi·Ri",
            "Distancia (m)",
            "Costo (USD)"

        ]:

            df_display[col] = (
                df_display[col]
                .round(6)
            )


        def color_tipo(val):

            if val == "Proveedor":

                return (
                    "background-color:#FFF1E8;"
                    "color:#DB5500;"
                    "font-weight:700"
                )

            return (
                "background-color:#EAF3FF;"
                "color:#0B3768;"
                "font-weight:700"
            )


        st.dataframe(

            df_display
            .style
            .map(
                color_tipo,
                subset=["Tipo"]
            ),

            use_container_width=True,

            height=440
        )


        # =====================================================================
        # TOTALES
        # =====================================================================

        render_html(
            """
            <div class="section-header">
                Totales del Modelo
            </div>
            """
        )


        ct1, ct2, ct3, ct4 = (
            st.columns(4)
        )


        total_cards = [

            (
                ct1,
                "Σ Xi·Vi·Ri",
                f"{df_res['Xi·Vi·Ri'].sum():,.2f}",
                "Componente X",
                "blue"
            ),

            (
                ct2,
                "Σ Yi·Vi·Ri",
                f"{df_res['Yi·Vi·Ri'].sum():,.2f}",
                "Componente Y",
                "blue"
            ),

            (
                ct3,
                "Σ Vi·Ri",
                f"{df_res['Vi·Ri'].sum():,.6f}",
                "Peso total",
                "orange"
            ),

            (
                ct4,
                "Costo Total",
                f"${df_res['Costo (USD)'].sum():,.2f}",
                "USD",
                "navy"
            )
        ]


        for (
            col,
            label,
            value,
            sub,
            color
        ) in total_cards:

            with col:

                render_html(
                    f"""
                    <div class="kpi-card kpi-{color}">

                        <div class="kpi-label">
                            {label}
                        </div>

                        <div class="kpi-value"
                             style="font-size:17px">
                            {value}
                        </div>

                        <div class="kpi-bottom">
                            {sub}
                        </div>

                    </div>
                    """
                )


        # =====================================================================
        # EXPORTACION EXCEL
        # =====================================================================

        render_html("<br>")


        buf = io.BytesIO()


        with pd.ExcelWriter(
            buf,
            engine="openpyxl"
        ) as writer:


            df_res.to_excel(

                writer,

                index=False,

                sheet_name="Resultados"
            )


            pd.DataFrame({

                "Variable": [

                    "CGx (UTM)",

                    "CGy (UTM)",

                    "Latitud",

                    "Longitud",

                    "Costo Total (USD)",

                    "Modo",

                    "Empresa"
                ],

                "Valor": [

                    round(
                        r["cgx"],
                        6
                    ),

                    round(
                        r["cgy"],
                        6
                    ),

                    round(
                        lat_r,
                        8
                    ),

                    round(
                        lon_r,
                        8
                    ),

                    round(
                        r["costo_total"],
                        4
                    ),

                    modo,

                    "PRIMEBOX"
                ]

            }).to_excel(

                writer,

                index=False,

                sheet_name="Resumen"
            )


        download_col, blank = (
            st.columns(
                [1.5, 3]
            )
        )


        with download_col:

            st.download_button(

                "↓ Exportar resultados a Excel",

                data=buf.getvalue(),

                file_name=
                    "PRIMEBOX_centro_gravedad.xlsx",

                mime=
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

                use_container_width=True
            )


    # =========================================================================
    # SIN RESULTADOS
    # =========================================================================

    else:

        render_html(
            f"""
            <div style="
                height:360px;

                display:flex;
                align-items:center;
                justify-content:center;

                background:#FFFFFF;

                border-radius:17px;

                border:1px solid {BORDER};

                margin-top:20px;

                box-shadow:
                    0px 3px 14px
                    rgba(15,23,42,.035);
            ">

                <div style="
                    text-align:center;
                    max-width:340px;
                ">

                    <div style="
                        width:66px;
                        height:66px;

                        border-radius:17px;

                        display:flex;
                        align-items:center;
                        justify-content:center;

                        margin:0 auto 17px auto;

                        background:linear-gradient(
                            135deg,
                            {BLUE_LIGHT},
                            {ORANGE_LIGHT}
                        );

                        color:{NAVY};

                        font-size:29px;
                    ">
                        ◫
                    </div>

                    <div style="
                        color:{NAVY_DARK};

                        font-size:15px;

                        font-weight:700;

                        margin-bottom:6px;
                    ">
                        Resultados pendientes
                    </div>

                    <div style="
                        color:{TEXT_SECONDARY};

                        font-size:11px;

                        line-height:1.7;
                    ">
                        Ejecuta el cálculo del Centro de Gravedad
                        desde la pestaña
                        <b>Mapa y Optimización</b>
                        para visualizar el dashboard.
                    </div>

                </div>

            </div>
            """
        )


# =============================================================================
# FOOTER
# =============================================================================

render_html(
    """
    <div class="prime-footer">

        PRIMEBOX · Modelo de Localización Logística
        &nbsp;&nbsp;|&nbsp;&nbsp;
        Centro de Gravedad

    </div>
    """
)