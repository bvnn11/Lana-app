# ═══════════════════════════════════════════════════════════════════════════════
#  MIA · Restaurant Intelligence Platform  —  app.py
#  Design: Apple Light Mode · alb + mov (violet) · Inter font
#  Auth: hardcoded (serban / mia)
#  Connections: st.secrets → gcp_service_account, spreadsheet_id, GEMINI_API_KEY
#  v3: Scanare Facturi → Stoc | Scanare Raport Z → Scădere Stoc | Food Cost auto
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import json
import base64
import io
import urllib.request
import urllib.error
import urllib.parse
import time
from datetime import datetime, date
from PIL import Image

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTE
# ─────────────────────────────────────────────────────────────────────────────
UNITATI_VALIDE = {
    "kg", "g", "l", "ml", "buc", "bucata", "bucăți",
    "bucati", "litri", "grame", "kilograme", "pcs", "piece"
}

def _strip_diacritics(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFD', s)
    return ''.join(c for c in s if unicodedata.category(c) != 'Mn')

_UNITATI_VALIDE_NORM = {_strip_diacritics(u.lower().strip()) for u in UNITATI_VALIDE}

def unitate_valida(u: str) -> bool:
    """Verifică o unitate de măsură ignorând diferențele de diacritice/case."""
    return _strip_diacritics(str(u).lower().strip()) in _UNITATI_VALIDE_NORM
SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# Paleta MIA — Apple Light cu accente mov
MIA_PURPLE      = "#7C3AED"   # violet principal
MIA_PURPLE_SOFT = "#EDE9FE"   # violet foarte deschis (fundal badge)
MIA_PURPLE_MID  = "#DDD6FE"   # violet mediu
MIA_BG          = "#F9F9FB"   # fundal pagină (aproape alb)
MIA_SURFACE     = "#FFFFFF"   # carduri
MIA_BORDER      = "#E5E7EB"   # borduri subtile
MIA_TEXT        = "#111827"   # text principal
MIA_MUTED       = "#6B7280"   # text secundar
MIA_FAINT       = "#9CA3AF"   # text terțiar
MIA_GREEN       = "#059669"
MIA_RED         = "#DC2626"
MIA_AMBER       = "#D97706"
MIA_BLUE        = "#2563EB"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MIA · Restaurant Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Apple Light, Inter, mov/violet accent
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"], [class*="st-"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"] {{ display: none !important; }}

.stApp {{ background: {MIA_BG} !important; }}
[data-testid="stSidebar"] {{ display: none !important; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: #F3F4F6; }}
::-webkit-scrollbar-thumb {{ background: #D1D5DB; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #9CA3AF; }}

/* Animations */
@keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
.animate-in {{ animation: fadeUp 0.3s cubic-bezier(0.16,1,0.3,1) both; }}
.animate-in-delay-1 {{ animation-delay: 0.06s; }}
.animate-in-delay-2 {{ animation-delay: 0.12s; }}
.animate-in-delay-3 {{ animation-delay: 0.18s; }}

/* ── Typography ── */
.mia-eyebrow {{
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: {MIA_PURPLE}; margin-bottom: 0.35rem;
}}
.mia-title {{
    font-size: 2rem; font-weight: 800; letter-spacing: -0.04em;
    color: {MIA_TEXT}; line-height: 1.1; margin-bottom: 0.3rem;
}}
.mia-subtitle {{ font-size: 0.9rem; color: {MIA_MUTED}; margin-bottom: 1.6rem; }}

/* ── Cards ── */
.mia-card {{
    background: {MIA_SURFACE};
    border: 1px solid {MIA_BORDER};
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.04);
    margin-bottom: 1rem;
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}}
.mia-card:hover {{
    box-shadow: 0 2px 8px rgba(124,58,237,.08), 0 8px 24px rgba(0,0,0,.06);
    border-color: {MIA_PURPLE_MID};
}}
.mia-card-sm {{
    background: {MIA_SURFACE};
    border: 1px solid {MIA_BORDER};
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.05);
}}

/* ── Metric cards ── */
.metric-card {{
    background: {MIA_SURFACE};
    border: 1px solid {MIA_BORDER};
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
    height: 100%;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}}
.metric-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(124,58,237,.1);
    border-color: {MIA_PURPLE_MID};
}}
.metric-label {{
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: {MIA_PURPLE}; margin-bottom: 0.5rem;
}}
.metric-value {{
    font-size: 1.85rem; font-weight: 800; color: {MIA_TEXT};
    letter-spacing: -0.04em; line-height: 1.1;
}}
.metric-sub {{ font-size: 0.78rem; color: {MIA_MUTED}; margin-top: 0.4rem; }}

/* ── Badges ── */
.badge {{
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
    margin-top: 0.5rem;
}}
.badge-purple {{ background: {MIA_PURPLE_SOFT}; color: {MIA_PURPLE}; }}
.badge-green  {{ background: #D1FAE5; color: {MIA_GREEN}; }}
.badge-red    {{ background: #FEE2E2; color: {MIA_RED}; }}
.badge-blue   {{ background: #DBEAFE; color: {MIA_BLUE}; }}
.badge-amber  {{ background: #FEF3C7; color: {MIA_AMBER}; }}

/* ── Header ── */
.mia-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.85rem 2rem;
    background: rgba(255,255,255,0.88);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid {MIA_BORDER};
    position: sticky; top: 0; z-index: 999;
    margin: -3rem -4rem 2rem -4rem;
}}
.mia-header-logo {{
    font-size: 1.1rem; font-weight: 800; color: {MIA_TEXT}; letter-spacing: -0.03em;
}}
.mia-header-logo span {{ color: {MIA_PURPLE}; }}
.mia-header-meta {{
    font-size: 0.8rem; color: {MIA_MUTED}; text-align: right; line-height: 1.5;
}}
.mia-header-meta strong {{ color: {MIA_TEXT}; font-weight: 600; }}

/* ── Tabs ── */
[data-testid="stTabs"] > div:first-child {{
    background: transparent !important;
    border-bottom: 1px solid {MIA_BORDER} !important;
    gap: 0 !important;
    margin-bottom: 1.5rem !important;
    padding: 0 !important;
}}
[data-testid="stTabs"] button {{
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: {MIA_MUTED} !important;
    padding: 0.6rem 1.1rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    border-radius: 0 !important;
    transition: color .15s, border-color .15s !important;
}}
[data-testid="stTabs"] button:hover {{ color: {MIA_TEXT} !important; }}
[data-testid="stTabs"] button[aria-selected="true"] {{
    color: {MIA_PURPLE} !important;
    font-weight: 700 !important;
    border-bottom: 2px solid {MIA_PURPLE} !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ display: none !important; }}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {{
    background: {MIA_SURFACE} !important;
    border: 1.5px solid {MIA_BORDER} !important;
    border-radius: 10px !important;
    color: {MIA_TEXT} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.85rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.04) !important;
    transition: border-color .15s, box-shadow .15s !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {{
    border-color: {MIA_PURPLE} !important;
    box-shadow: 0 0 0 3px {MIA_PURPLE_SOFT} !important;
    outline: none !important;
}}
.stTextInput > div > div > input::placeholder {{ color: {MIA_FAINT} !important; }}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stFileUploader label, .stTextArea label,
.stSlider label {{
    color: {MIA_MUTED} !important; font-size: 0.78rem !important;
    font-weight: 600 !important; letter-spacing: 0.03em !important;
}}

/* Selectbox */
.stSelectbox > div > div {{
    background: {MIA_SURFACE} !important;
    border: 1.5px solid {MIA_BORDER} !important;
    border-radius: 10px !important;
    color: {MIA_TEXT} !important;
}}
.stSelectbox > div > div > div {{ color: {MIA_TEXT} !important; }}

/* File uploader */
[data-testid="stFileUploader"] {{
    border: 1.5px dashed {MIA_PURPLE_MID} !important;
    border-radius: 14px !important;
    background: {MIA_PURPLE_SOFT} !important;
    padding: 1.2rem !important;
    color: {MIA_MUTED} !important;
    transition: border-color 0.2s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {MIA_PURPLE} !important;
    background: {MIA_PURPLE_MID} !important;
}}

/* Buttons */
.stButton > button {{
    border-radius: 10px !important;
    border: 1.5px solid {MIA_BORDER} !important;
    background: {MIA_SURFACE} !important;
    color: {MIA_TEXT} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.08) !important;
    transition: all .15s ease !important;
}}
.stButton > button:hover {{
    background: {MIA_BG} !important;
    border-color: {MIA_PURPLE_MID} !important;
    box-shadow: 0 2px 8px rgba(124,58,237,.12) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button[kind="primary"] {{
    background: {MIA_PURPLE} !important;
    color: #ffffff !important;
    border-color: {MIA_PURPLE} !important;
    box-shadow: 0 2px 8px rgba(124,58,237,.35) !important;
}}
.stButton > button[kind="primary"]:hover {{
    background: #6D28D9 !important;
    border-color: #6D28D9 !important;
    box-shadow: 0 4px 14px rgba(124,58,237,.45) !important;
    transform: translateY(-1px) !important;
}}

/* Slider */
.stSlider > div > div > div > div {{ background: {MIA_PURPLE} !important; }}
.stSlider [data-baseweb="slider"] [data-testid="stSliderTrack"] {{
    background: {MIA_PURPLE_MID} !important;
}}

/* Alerts */
.stSuccess {{ background: #D1FAE5 !important; color: {MIA_GREEN} !important; border-color: #A7F3D0 !important; border-radius: 10px !important; }}
.stWarning {{ background: #FEF3C7 !important; color: {MIA_AMBER} !important; border-color: #FDE68A !important; border-radius: 10px !important; }}
.stError   {{ background: #FEE2E2 !important; color: {MIA_RED} !important; border-color: #FECACA !important; border-radius: 10px !important; }}
.stInfo    {{ background: {MIA_PURPLE_SOFT} !important; color: {MIA_PURPLE} !important; border-color: {MIA_PURPLE_MID} !important; border-radius: 10px !important; }}

/* Dataframe */
[data-testid="stDataFrame"] {{
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid {MIA_BORDER} !important;
}}
[data-testid="stDataFrame"] table {{ background: {MIA_SURFACE} !important; color: {MIA_TEXT} !important; }}

/* Spinner */
.stSpinner > div {{ border-top-color: {MIA_PURPLE} !important; }}

/* Login */
.login-wrap {{
    max-width: 420px; margin: 6vh auto 0; padding: 2.5rem;
    background: {MIA_SURFACE}; border: 1px solid {MIA_BORDER};
    border-radius: 20px; box-shadow: 0 8px 40px rgba(124,58,237,.12);
}}
.login-logo {{
    font-size: 1.6rem; font-weight: 800; letter-spacing: -0.04em;
    color: {MIA_TEXT}; text-align: center; margin-bottom: 0.2rem;
}}
.login-logo span {{ color: {MIA_PURPLE}; }}
.login-tagline {{
    font-size: 0.82rem; color: {MIA_MUTED}; text-align: center; margin-bottom: 2rem;
}}

/* Cascadă row */
.casc-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0; border-bottom: 1px solid #F3F4F6;
}}
.casc-label {{ font-size: 0.88rem; color: {MIA_MUTED}; }}
.casc-val   {{ font-size: 0.88rem; font-weight: 600; font-variant-numeric: tabular-nums; }}

/* Bon fiscal */
.bon-wrap {{
    background: {MIA_SURFACE}; border: 1px solid {MIA_BORDER}; border-radius: 16px;
    padding: 1.8rem; max-width: 400px;
    box-shadow: 0 2px 12px rgba(124,58,237,.08);
}}
.bon-title {{
    font-size: 0.65rem; font-weight: 800; letter-spacing: 0.18em;
    text-transform: uppercase; color: {MIA_PURPLE}; text-align: center;
    margin-bottom: 0.3rem;
}}
.bon-date  {{ font-size: 0.72rem; color: {MIA_FAINT}; text-align: center; margin-bottom: 1.2rem; }}
.bon-sep   {{ border: none; border-top: 1px dashed {MIA_BORDER}; margin: 0.8rem 0; }}
.bon-line  {{
    display: flex; justify-content: space-between;
    padding: 0.28rem 0; font-size: 0.86rem;
}}
.bon-net   {{
    display: flex; justify-content: space-between; align-items: center; padding-top: 0.8rem;
}}
.bon-net-label {{ font-size: 0.95rem; font-weight: 700; color: {MIA_TEXT}; }}
.bon-net-val   {{ font-size: 1.5rem; font-weight: 800; }}

/* Match row (Z) */
.match-badge-ok  {{ background: #D1FAE5; color: {MIA_GREEN}; padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }}
.match-badge-err {{ background: #FEE2E2; color: {MIA_RED};   padding: 2px 8px; border-radius: 6px; font-size: 0.72rem; font-weight: 700; }}

/* Stoc alert */
.stoc-low {{
    background: #FEF3C7; border: 1px solid #FDE68A;
    border-radius: 10px; padding: 0.7rem 1rem;
    font-size: 0.85rem; color: {MIA_AMBER}; font-weight: 500;
    margin-bottom: 0.4rem;
}}
.stoc-ok {{
    background: #D1FAE5; border: 1px solid #A7F3D0;
    border-radius: 10px; padding: 0.7rem 1rem;
    font-size: 0.85rem; color: {MIA_GREEN}; font-weight: 500;
    margin-bottom: 0.4rem;
}}

/* Progress bar stoc */
.stoc-bar-wrap {{
    background: #F3F4F6; border-radius: 4px; height: 6px; margin-top: 6px; overflow: hidden;
}}
.stoc-bar-fill {{
    height: 6px; border-radius: 4px; transition: width 0.4s ease;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTENTIFICARE
# ─────────────────────────────────────────────────────────────────────────────
if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

if not st.session_state.auth_ok:
    st.markdown(f"""
    <div class="login-wrap animate-in">
        <div class="login-logo">M<span>IA</span></div>
        <div class="login-tagline">Gestiune restaurant · simplă și rapidă</div>
    </div>
    """, unsafe_allow_html=True)
    col_l, col_m, col_r = st.columns([1, 1.2, 1])
    with col_m:
        u = st.text_input("Utilizator", placeholder="username")
        p = st.text_input("Parolă", type="password", placeholder="••••••")
        if st.button("Intră în MIA →", type="primary", use_container_width=True):
            if u == "serban" and p == "mia":
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Date incorecte. Încearcă din nou.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="mia-header">
    <div class="mia-header-logo">M<span>IA</span> · Restaurant Intelligence</div>
    <div class="mia-header-meta">
        <strong>{datetime.now().strftime("%d %b %Y · %H:%M")}</strong><br>
        Bun venit, serban
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# RSA / JWT helpers (identic cu Lana)
# ─────────────────────────────────────────────────────────────────────────────
def _load_rsa_key_obj(pem: str):
    """Încarcă cheia privată RSA direct din PEM (fără conversie DER manuală)."""
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    pem_bytes = pem.strip().encode("utf-8")
    return load_pem_private_key(pem_bytes, password=None)

def _rsa_sign(msg: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    sa  = dict(st.secrets["gcp_service_account"])
    key = _load_rsa_key_obj(sa["private_key"])
    return key.sign(msg, padding.PKCS1v15(), hashes.SHA256())

def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _make_jwt(sa: dict) -> str:
    now = int(time.time())
    hdr = b64u(json.dumps({"alg":"RS256","typ":"JWT"}, separators=(',',':')).encode())
    pld = b64u(json.dumps({
        "iss": sa["client_email"], "sub": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }, separators=(',',':')).encode())
    msg = f"{hdr}.{pld}".encode()
    return f"{hdr}.{pld}.{b64u(_rsa_sign(msg))}"

@st.cache_resource(ttl=3000)
def get_access_token() -> str:
    sa   = dict(st.secrets["gcp_service_account"])
    jwt  = _make_jwt(sa)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
    }).encode()
    req  = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]

# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE SHEETS helpers
# ─────────────────────────────────────────────────────────────────────────────
def sheets_get(rng: str) -> list:
    token = get_access_token()
    sid   = st.secrets["spreadsheet_id"]
    url   = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(rng)}"
    req   = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()).get("values", [])
    except Exception as e:
        st.error(f"Eroare citire Sheet ({rng}): {e}"); return []

def sheets_clear_write(sheet: str, rows: list):
    token = get_access_token()
    sid   = st.secrets["spreadsheet_id"]
    req = urllib.request.Request(
        f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}:clear",
        data=b"{}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    try: urllib.request.urlopen(req)
    except Exception as e: st.error(f"Eroare clear: {e}"); return
    body = json.dumps({"values": rows}).encode()
    req2 = urllib.request.Request(
        f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}?valueInputOption=RAW",
        data=body, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT"
    )
    try: urllib.request.urlopen(req2)
    except Exception as e: st.error(f"Eroare scriere: {e}")

def sheets_append(sheet: str, rows: list):
    token = get_access_token()
    sid   = st.secrets["spreadsheet_id"]
    body  = json.dumps({"values": rows}).encode()
    url   = (f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}:append"
             f"?valueInputOption=RAW&insertDataOption=INSERT_ROWS")
    req   = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    try: urllib.request.urlopen(req)
    except Exception as e: st.error(f"Eroare append: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CRUD — Sheet → DataFrame
# ─────────────────────────────────────────────────────────────────────────────
def _sheet_to_df(sheet: str, cols: list) -> pd.DataFrame:
    rows = sheets_get(sheet)
    if len(rows) <= 1:
        return pd.DataFrame(columns=cols)
    hdr  = rows[0]
    data = [dict(zip(hdr, row + [""]*(len(hdr)-len(row)))) for row in rows[1:]]
    df   = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df[cols]

def citeste_config() -> dict:
    rows = sheets_get("Config")
    cfg  = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            try:    cfg[row[0].strip()] = float(row[1].strip())
            except: cfg[row[0].strip()] = row[1].strip()
    return cfg

def salveaza_config(cfg: dict):
    sheets_clear_write("Config", [["Cheie","Valoare"]] + [[k,str(v)] for k,v in cfg.items()])
    st.cache_resource.clear()

def citeste_stoc() -> pd.DataFrame:
    return _sheet_to_df("Stoc", ["Produs","Cantitate","Unitate","Pret_Unitar","Data","Stoc_Minim"])

def salveaza_stoc(df: pd.DataFrame):
    rows = [["Produs","Cantitate","Unitate","Pret_Unitar","Data","Stoc_Minim"]]
    for _, r in df.iterrows():
        rows.append([
            str(r.get("Produs","")), str(r.get("Cantitate",0)),
            str(r.get("Unitate","")), str(r.get("Pret_Unitar",0)),
            str(r.get("Data","")),    str(r.get("Stoc_Minim",0)),
        ])
    sheets_clear_write("Stoc", rows)

def citeste_vanzari() -> pd.DataFrame:
    return _sheet_to_df("Vanzari", ["Preparat","Cantitate_Vanduta","Data"])

def salveaza_vanzari(rows_data: list):
    sheets_append("Vanzari",
        [[r["Preparat"], str(r["Cantitate_Vanduta"]), str(r["Data"])] for r in rows_data])

def citeste_retetar() -> pd.DataFrame:
    return _sheet_to_df("Retetar", ["Preparat","Ingredient","Gramaj","Pret_Vanzare"])

def citeste_facturi_log() -> pd.DataFrame:
    return _sheet_to_df("FacturiLog", ["Data","Furnizor","NrFactura","Total","Produse"])

def salveaza_factura_log(data: str, furnizor: str, nr: str, total: float, produse_json: str):
    sheets_append("FacturiLog", [[data, furnizor, nr, str(total), produse_json]])

# ─────────────────────────────────────────────────────────────────────────────
# LOGICĂ FINANCIARĂ
# ─────────────────────────────────────────────────────────────────────────────
def _f(x) -> float:
    try: return float(x)
    except: return 0.0

def calculeaza_food_cost(vanzari_df, retetar_df, stoc_df) -> float:
    if vanzari_df.empty or retetar_df.empty or stoc_df.empty:
        return 0.0
    idx = {str(r.get("Produs","")).lower().strip(): _f(r.get("Pret_Unitar",0))
           for _, r in stoc_df.iterrows()}
    total = 0.0
    for _, vrow in vanzari_df.iterrows():
        prep  = str(vrow.get("Preparat","")).lower().strip()
        cant  = _f(vrow.get("Cantitate_Vanduta",0))
        ings  = retetar_df[retetar_df["Preparat"].astype(str).str.lower().str.strip() == prep]
        for _, irow in ings.iterrows():
            kg    = _f(irow.get("Gramaj",0)) / 1000.0
            total += cant * kg * idx.get(str(irow.get("Ingredient","")).lower().strip(), 0.0)
    return round(total, 2)

def cascada(vanzari_brute: float, food_cost: float, cfg: dict) -> dict:
    tva       = _f(cfg.get("cota_tva", 0.09))
    chirie    = _f(cfg.get("chirie_lunara", 0))
    salarii   = _f(cfg.get("salarii_lunare", 0))
    utilitati = _f(cfg.get("utilitati_lunare", 0))
    regim     = cfg.get("regim_fiscal", "micro1")
    div       = _f(cfg.get("cota_dividend", 0.08))
    ci        = {"micro1": 0.01, "micro3": 0.03, "profit16": 0.16}.get(str(regim), 0.01)
    tva_col   = vanzari_brute - vanzari_brute / (1 + tva)
    net_tva   = vanzari_brute / (1 + tva)
    fixe_zi   = (chirie + salarii + utilitati) / 30.0
    fc_eff    = food_cost if food_cost > 0 else net_tva * 0.30
    fc_sursa  = "calculat din rețetar" if food_cost > 0 else "estimat 30%"
    profit_brut = net_tva - fc_eff - fixe_zi
    imp_firma   = max(profit_brut * ci, 0.0)
    dupa_imp    = profit_brut - imp_firma
    imp_div     = max(dupa_imp * div, 0.0)
    net         = dupa_imp - imp_div
    marja       = (net / vanzari_brute * 100) if vanzari_brute > 0 else 0.0
    return {
        "vanzari_brute":           round(vanzari_brute, 2),
        "tva_colectat":            round(tva_col, 2),
        "vanzari_fara_tva":        round(net_tva, 2),
        "cheltuieli_fixe_zilnice": round(fixe_zi, 2),
        "food_cost":               round(fc_eff, 2),
        "food_cost_sursa":         fc_sursa,
        "profit_brut":             round(profit_brut, 2),
        "impozit_firma":           round(imp_firma, 2),
        "profit_dupa_impozit":     round(dupa_imp, 2),
        "impozit_dividend":        round(imp_div, 2),
        "profit_net_real":         round(net, 2),
        "marja_neta":              round(marja, 2),
    }

# ─────────────────────────────────────────────────────────────────────────────
# FUZZY MATCHING
# ─────────────────────────────────────────────────────────────────────────────
def _normalize(s: str) -> str:
    import unicodedata
    s = s.lower().strip()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s

def _similarity(a: str, b: str) -> float:
    a, b = _normalize(a), _normalize(b)
    if a == b: return 1.0
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb: return 0.0
    overlap = len(ta & tb) / max(len(ta), len(tb))
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    prefix_bonus = 0.3 if longer.startswith(shorter) else 0.0
    return min(1.0, overlap + prefix_bonus)

def fuzzy_match_preparat(nume_detectat: str, preparate_list: list, threshold: float = 0.35):
    best, best_score = None, 0.0
    for prep in preparate_list:
        sc = _similarity(nume_detectat, prep)
        if sc > best_score:
            best_score = sc
            best = prep
    return (best, best_score) if best_score >= threshold else (None, 0.0)

# ─────────────────────────────────────────────────────────────────────────────
# AI — GEMINI 1.5 Flash
# ─────────────────────────────────────────────────────────────────────────────
def _gemini_call(img_bytes: bytes, prompt: str) -> dict | None:
    try:
        key    = st.secrets["GEMINI_API_KEY"]
        b64img = base64.b64encode(img_bytes).decode()
        payload = json.dumps({"contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": b64img}},
            {"text": prompt},
        ]}]}).encode()
        req = urllib.request.Request(
            f"{GEMINI_BASE}?key={key}", data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
        raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("Extragerea nu a returnat date valide. Încearcă cu o imagine mai clară sau mai bine luminată.")
        return None
    except Exception as e:
        st.error(f"Eroare procesare: {e}"); return None

def extrage_factura_ai(img_bytes: bytes) -> dict | None:
    prompt = (
        "Ești un sistem specializat în extragerea datelor din facturi fiscale românești. "
        "Analizează imaginea și extrage: furnizorul (numele firmei), numărul facturii, "
        "data facturii și TOATE produsele cu cantitate, unitate de măsură și preț unitar. "
        "Returnează EXCLUSIV JSON valid, fără text extra, fără markdown. "
        'Format: {"furnizor":"Firma SRL","nr_factura":"F001","data":"2024-01-15",'
        '"total":150.0,"produse":[{"produs":"Făină","cantitate":50.0,"unitate":"kg","pret_unitar":2.5}]}'
    )
    return _gemini_call(img_bytes, prompt)

def extrage_raport_z_ai(img_bytes: bytes) -> dict | None:
    prompt = (
        "Ești un sistem OCR specializat pentru bonuri fiscale și Rapoarte Z din restaurante românești. "
        "Analizează imaginea și extrage TOATE produsele/preparatele vândute cu cantitățile lor. "
        "Ignoră taxe, subtotaluri, TVA, totaluri — extrage doar produsele individuale. "
        "Returnează EXCLUSIV JSON valid, fără text extra, fără markdown. "
        'Format: {"vanzari":[{"produs":"Burger Clasic","cantitate":5}]} '
        "Cantitățile trebuie să fie numere. Sumează dacă același produs apare de mai multe ori."
    )
    return _gemini_call(img_bytes, prompt)

# ─────────────────────────────────────────────────────────────────────────────
# LOGICĂ STOC
# ─────────────────────────────────────────────────────────────────────────────
def adauga_in_stoc(produse_list: list):
    """Adaugă sau actualizează produsele din factură în stoc."""
    stoc_df = citeste_stoc()
    for prod in produse_list:
        nu  = str(prod.get("Produs","")).strip()
        can = _f(prod.get("Cantitate", 0))
        un  = str(prod.get("Unitate","")).strip()
        pr  = _f(prod.get("Pret_Unitar", 0))
        dat = str(prod.get("Data", date.today().strftime("%Y-%m-%d")))
        sm  = _f(prod.get("Stoc_Minim", 0))
        if not nu: continue
        mask = (stoc_df["Produs"].astype(str).str.lower().str.strip() == nu.lower().strip()
                if not stoc_df.empty else pd.Series([], dtype=bool))
        if not stoc_df.empty and mask.any():
            idx2 = stoc_df[mask].index[0]
            # Adaugă cantitatea (nu înlocui) + actualizează prețul
            stoc_df.at[idx2, "Cantitate"]   = round(_f(stoc_df.at[idx2, "Cantitate"]) + can, 4)
            stoc_df.at[idx2, "Pret_Unitar"] = pr
            stoc_df.at[idx2, "Data"]        = dat
        else:
            new_row = {"Produs": nu, "Cantitate": can, "Unitate": un,
                       "Pret_Unitar": pr, "Data": dat, "Stoc_Minim": sm}
            stoc_df = pd.concat([stoc_df, pd.DataFrame([new_row])], ignore_index=True)
    salveaza_stoc(stoc_df)
    return stoc_df

def scade_stoc_din_vanzari(vanzari_input: list, retetar_df: pd.DataFrame):
    """Scade ingredientele din stoc pe baza rețetarului + vânzări din Z."""
    stoc_df = citeste_stoc()
    if retetar_df.empty or stoc_df.empty:
        return stoc_df, []
    scazut = []
    for v in vanzari_input:
        prep_v = str(v["Preparat"]).lower().strip()
        cant_v = _f(v["Cantitate_Vanduta"])
        ings   = retetar_df[retetar_df["Preparat"].astype(str).str.lower().str.strip() == prep_v]
        for _, irow in ings.iterrows():
            ing    = str(irow.get("Ingredient","")).lower().strip()
            gramaj = _f(irow.get("Gramaj",0)) / 1000.0
            consum = cant_v * gramaj
            mask   = stoc_df["Produs"].astype(str).str.lower().str.strip() == ing
            if mask.any():
                idx3 = stoc_df[mask].index[0]
                cur  = _f(stoc_df.at[idx3,"Cantitate"])
                nou  = max(0, round(cur - consum, 4))
                stoc_df.at[idx3,"Cantitate"] = nou
                scazut.append({
                    "ingredient": stoc_df.at[idx3,"Produs"],
                    "inainte": cur, "dupa": nou, "consum": round(consum, 4),
                    "unitate": stoc_df.at[idx3,"Unitate"],
                    "minim": _f(stoc_df.at[idx3,"Stoc_Minim"]),
                })
    return stoc_df, scazut

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTE UI
# ─────────────────────────────────────────────────────────────────────────────
def card_metric(titlu: str, valoare: str, sub: str = "", badge: str = "", tip: str = "purple"):
    cls_map = {"purple":"badge-purple","green":"badge-green","red":"badge-red",
               "blue":"badge-blue","amber":"badge-amber"}
    cls = cls_map.get(tip, "badge-purple")
    badge_html = f'<div><span class="badge {cls}">{badge}</span></div>' if badge else ""
    sub_html   = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card animate-in">
        <div class="metric-label">{titlu}</div>
        <div class="metric-value">{valoare}</div>
        {sub_html}{badge_html}
    </div>""", unsafe_allow_html=True)

def casc_row(label: str, valoare: float, plus: bool = False):
    color = MIA_GREEN if plus else (MIA_RED if valoare > 0 else MIA_FAINT)
    sign  = "+" if plus else "−"
    st.markdown(f"""
    <div class="casc-row">
        <span class="casc-label">{label}</span>
        <span class="casc-val" style="color:{color};">{sign} {abs(valoare):,.2f} RON</span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(d: dict, titlu: str = "BON FISCAL"):
    net = d["profit_net_real"]
    nc  = MIA_GREEN if net >= 0 else MIA_RED
    linii = [
        ("Încasări brute",  MIA_TEXT,  f"{d['vanzari_brute']:,.2f} RON"),
        ("TVA colectat",    MIA_RED,   f"− {d['tva_colectat']:,.2f} RON"),
        ("Food Cost",       MIA_RED,   f"− {d['food_cost']:,.2f} RON"),
        ("Cheltuieli fixe", MIA_RED,   f"− {d['cheltuieli_fixe_zilnice']:,.2f} RON"),
        ("Impozit firmă",   MIA_RED,   f"− {d['impozit_firma']:,.2f} RON"),
        ("Impozit div.",    MIA_RED,   f"− {d['impozit_dividend']:,.2f} RON"),
    ]
    rows_html = "".join(
        f'<div class="bon-line"><span style="color:{MIA_MUTED};">{l}</span>'
        f'<span style="color:{c};">{v}</span></div>'
        for l, c, v in linii
    )
    badge_cls = "badge-green" if net >= 0 else "badge-red"
    st.markdown(f"""
    <div class="bon-wrap animate-in">
        <div class="bon-title">{titlu}</div>
        <div class="bon-date">{datetime.now().strftime("%d.%m.%Y · %H:%M")}</div>
        <hr class="bon-sep">
        {rows_html}
        <hr class="bon-sep">
        <div class="bon-net">
            <span class="bon-net-label">BANI ÎN MÂNĂ</span>
            <span class="bon-net-val" style="color:{nc};">{net:,.2f} RON</span>
        </div>
        <div style="text-align:right;margin-top:0.6rem;">
            <span class="badge {badge_cls}">Marjă {d['marja_neta']:.1f}%</span>
        </div>
    </div>""", unsafe_allow_html=True)

def stoc_bar(cantitate: float, minim: float, unitate: str):
    """Bara vizuală de stoc."""
    if minim > 0:
        pct = min(100, int(cantitate / minim * 100))
        color = MIA_GREEN if pct > 150 else (MIA_AMBER if pct > 80 else MIA_RED)
        st.markdown(f"""
        <div class="stoc-bar-wrap">
            <div class="stoc-bar-fill" style="width:{pct}%;background:{color};"></div>
        </div>
        <div style="font-size:0.72rem;color:{MIA_FAINT};margin-top:3px;">
            {cantitate:.2f} {unitate} · minim: {minim:.2f}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="font-size:0.82rem;color:{MIA_MUTED};">{cantitate:.2f} {unitate}</div>',
                    unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NAVIGARE — Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_dash, tab_stoc, tab_facturi, tab_z, tab_retetar, tab_setari, tab_sim = st.tabs([
    "✦ Dashboard",
    "📦 Stoc",
    "🧾 Scanare Facturi",
    "📊 Raport Z",
    "📋 Rețetar & Food Cost",
    "⚙️ Setări",
    "🧮 Simulator",
])

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.markdown('<p class="mia-eyebrow">Situație financiară</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Actualizat live · date din Google Sheets</p>',
                unsafe_allow_html=True)

    cfg        = citeste_config()
    stoc_df    = citeste_stoc()
    vanzari_df = citeste_vanzari()
    retetar_df = citeste_retetar()

    azi = date.today().strftime("%Y-%m-%d")
    v_azi = (vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)]
             if not vanzari_df.empty else pd.DataFrame(columns=["Preparat","Cantitate_Vanduta","Data"]))

    # Calculează vânzări brute azi
    vb = 0.0
    if not v_azi.empty and not retetar_df.empty:
        for _, row in v_azi.iterrows():
            prep = str(row.get("Preparat","")).lower().strip()
            cant = _f(row.get("Cantitate_Vanduta",0))
            m    = retetar_df[retetar_df["Preparat"].astype(str).str.lower().str.strip() == prep]
            if not m.empty:
                vb += cant * _f(m.iloc[0].get("Pret_Vanzare",0))

    fc_zi = calculeaza_food_cost(v_azi, retetar_df, stoc_df)
    c     = cascada(vb, fc_zi, cfg)

    # Alerte stoc scăzut
    stoc_alerte = []
    if not stoc_df.empty:
        for _, row in stoc_df.iterrows():
            cant_s = _f(row.get("Cantitate",0))
            min_s  = _f(row.get("Stoc_Minim",0))
            if min_s > 0 and cant_s <= min_s:
                stoc_alerte.append(row.get("Produs",""))

    if stoc_alerte:
        st.markdown(f"""
        <div class="mia-card animate-in" style="border-color:#FDE68A;background:#FFFBEB;">
            <div style="font-size:0.85rem;font-weight:600;color:{MIA_AMBER};">
                ⚠ Stoc scăzut · {len(stoc_alerte)} produse sub limita minimă
            </div>
            <div style="font-size:0.82rem;color:{MIA_MUTED};margin-top:4px;">
                {', '.join(stoc_alerte[:6])}{'…' if len(stoc_alerte) > 6 else ''}
            </div>
        </div>""", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tip = "green" if c["profit_net_real"] >= 0 else "red"
        card_metric("Profit Net · Bani în mână", f"{c['profit_net_real']:,.2f} RON",
                    sub=f"Azi · {azi}", badge=f"Marjă {c['marja_neta']:.1f}%", tip=tip)
    with col2:
        fc_pct = (c["food_cost"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] > 0 else 0
        card_metric("Food Cost", f"{c['food_cost']:,.2f} RON",
                    sub=f"{fc_pct:.1f}% din vânzări", tip="purple")
    with col3:
        card_metric("Vânzări Brute", f"{c['vanzari_brute']:,.2f} RON",
                    sub="inclusiv TVA", tip="blue")
    with col4:
        nr_stoc = len(stoc_df) if not stoc_df.empty else 0
        card_metric("Produse în Stoc", str(nr_stoc),
                    sub=f"{len(stoc_alerte)} sub limită" if stoc_alerte else "Stoc OK",
                    badge="⚠ Alertă" if stoc_alerte else "✓ OK",
                    tip="amber" if stoc_alerte else "green")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.markdown('<div class="mia-card animate-in">', unsafe_allow_html=True)
        st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:1rem;">Cascadă Financiară · Azi</div>',
                    unsafe_allow_html=True)
        casc_row("Încasări brute (cu TVA)", c["vanzari_brute"], plus=True)
        casc_row("TVA colectat (→ ANAF)",   c["tva_colectat"])
        casc_row("Food Cost ingrediente",   c["food_cost"])
        casc_row("Cheltuieli fixe zilnice", c["cheltuieli_fixe_zilnice"])
        st.markdown(f"""
        <div class="casc-row">
            <span class="casc-label" style="color:{MIA_TEXT};font-weight:600;">Profit brut operațional</span>
            <span class="casc-val" style="color:{MIA_PURPLE};font-weight:700;">{c['profit_brut']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        casc_row("Impozit firmă",     c["impozit_firma"])
        casc_row("Impozit dividende", c["impozit_dividend"])
        nc = MIA_GREEN if c["profit_net_real"] >= 0 else MIA_RED
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.9rem 0 0.2rem;">
            <span style="font-size:0.95rem;font-weight:700;color:{MIA_TEXT};">✦ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:800;color:{nc};font-variant-numeric:tabular-nums;">
                {c['profit_net_real']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        if not v_azi.empty:
            st.markdown('<div class="mia-card animate-in animate-in-delay-1">', unsafe_allow_html=True)
            st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:1rem;">Vânzări de azi</div>',
                        unsafe_allow_html=True)
            for _, row in v_azi.iterrows():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.45rem 0;
                    border-bottom:1px solid #F3F4F6;font-size:0.88rem;">
                    <span style="color:{MIA_MUTED};">{row.get('Preparat','')}</span>
                    <span style="color:{MIA_PURPLE};font-weight:600;">{row.get('Cantitate_Vanduta',0)} buc</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="mia-card animate-in" style="text-align:center;padding:2.5rem;">
                <div style="font-size:2.2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:{MIA_MUTED};font-weight:500;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.78rem;color:{MIA_FAINT};margin-top:4px;">
                    Mergi la Raport Z pentru a înregistra
                </div>
            </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2 — STOC
# ═════════════════════════════════════════════════════════════════════════════
with tab_stoc:
    st.markdown('<p class="mia-eyebrow">Gestiune inventar</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Stoc</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Adaugă produse manual sau prin scanare facturi. Stocul se scade automat din Raportul Z.</p>',
                unsafe_allow_html=True)

    stoc_df = citeste_stoc()

    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s2:
        if st.button("➕ Adaugă produs", type="primary", use_container_width=True, key="btn_show_add"):
            st.session_state["show_add_stoc"] = not st.session_state.get("show_add_stoc", False)
    with col_s3:
        if st.button("🔄 Reîncarcă", use_container_width=True):
            st.cache_resource.clear()
            st.rerun()

    # Formular adăugare manuală — vizibil dacă butonul e apăsat
    if st.session_state.get("show_add_stoc", False):
        st.markdown(f"""
        <div class="mia-card animate-in" style="border-color:{MIA_PURPLE_MID};background:#FAFAFF;">
            <div class="mia-eyebrow" style="margin-bottom:0.75rem;">➕ Adaugă / Actualizează produs în stoc</div>
        </div>""", unsafe_allow_html=True)
        ca, cb, cc, cd, ce = st.columns([2.5, 1, 1, 1, 1])
        with ca: nm = st.text_input("Produs *", key="stoc_nm2", placeholder="ex: Făină albă")
        with cb: qm = st.number_input("Cantitate", min_value=0.0, step=0.1, key="stoc_qm2")
        with cc: um = st.selectbox("UM", ["kg","g","l","ml","buc"], key="stoc_um2")
        with cd: pm = st.number_input("Preț/UM (RON)", min_value=0.0, step=0.1, key="stoc_pm2")
        with ce: sm = st.number_input("Stoc minim", min_value=0.0, step=0.1, key="stoc_sm2",
                                      help="Cantitate minimă sub care primești alertă")
        col_btn_a, col_btn_b, _ = st.columns([1.2, 1, 3])
        with col_btn_a:
            if st.button("💾 Salvează produs", type="primary", key="btn_stoc_save2"):
                if nm.strip():
                    adauga_in_stoc([{"Produs": nm.strip(), "Cantitate": qm, "Unitate": um,
                                     "Pret_Unitar": pm, "Data": date.today().strftime("%Y-%m-%d"),
                                     "Stoc_Minim": sm}])
                    st.success(f"✓ '{nm}' salvat în stoc.")
                    st.session_state["show_add_stoc"] = False
                    st.rerun()
                else:
                    st.warning("Completează numele produsului.")
        with col_btn_b:
            if st.button("Anulează", key="btn_stoc_cancel"):
                st.session_state["show_add_stoc"] = False
                st.rerun()
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    if stoc_df.empty:
        st.markdown(f"""
        <div class="mia-card" style="text-align:center;padding:3rem;">
            <div style="font-size:2.5rem;margin-bottom:0.8rem;">📦</div>
            <div style="font-size:1rem;font-weight:600;color:{MIA_TEXT};">Stocul este gol</div>
            <div style="font-size:0.85rem;color:{MIA_MUTED};margin-top:6px;">
                Apasă <strong>➕ Adaugă produs</strong> pentru a adăuga manual,<br>
                sau scanează o factură din tab-ul <em>Scanare Facturi</em>.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Grupare stoc cu alerte
        stoc_ok   = []
        stoc_alert = []
        for _, row in stoc_df.iterrows():
            cant_s = _f(row.get("Cantitate",0))
            min_s  = _f(row.get("Stoc_Minim",0))
            if min_s > 0 and cant_s <= min_s:
                stoc_alert.append(row)
            else:
                stoc_ok.append(row)

        if stoc_alert:
            st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:0.5rem;">⚠ Sub limita minimă</div>',
                        unsafe_allow_html=True)
            for row in stoc_alert:
                cant = _f(row.get("Cantitate",0))
                minim = _f(row.get("Stoc_Minim",0))
                pct = int(cant/minim*100) if minim > 0 else 0
                st.markdown(f"""
                <div class="mia-card-sm" style="border-color:#FDE68A;margin-bottom:0.5rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;color:{MIA_TEXT};">{row.get('Produs','')}</span>
                        <span class="badge badge-amber">{cant:.2f} {row.get('Unitate','')}</span>
                    </div>
                    <div class="stoc-bar-wrap" style="margin-top:8px;">
                        <div class="stoc-bar-fill" style="width:{pct}%;background:{MIA_RED};"></div>
                    </div>
                    <div style="font-size:0.72rem;color:{MIA_FAINT};margin-top:3px;">
                        {pct}% din stocul minim ({minim:.2f}) · Preț: {_f(row.get('Pret_Unitar',0)):.2f} RON/{row.get('Unitate','')}
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:0.5rem;">Toate produsele ({len(stoc_df)})</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            stoc_df.rename(columns={
                "Produs":"Produs", "Cantitate":"Cant.", "Unitate":"UM",
                "Pret_Unitar":"Preț/UM (RON)", "Data":"Ultima actualizare", "Stoc_Minim":"Minim"
            }),
            use_container_width=True, hide_index=True
        )

        st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3 — SCANARE FACTURI → STOC
# ═════════════════════════════════════════════════════════════════════════════
with tab_facturi:
    st.markdown('<p class="mia-eyebrow">Procesare automată · Gemini Vision</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Scanare Facturi</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Fotografiază factura → produsele sunt extrase automat → Se adaugă în stoc.</p>',
                unsafe_allow_html=True)

    if "produse_factura" not in st.session_state:
        st.session_state.produse_factura = []
    if "meta_factura" not in st.session_state:
        st.session_state.meta_factura = {}

    uploaded = st.file_uploader("Imagine factură (JPG, PNG, WEBP)", type=["jpg","jpeg","png","webp"],
                                 key="fact_upload")

    if uploaded:
        img_bytes = uploaded.read()
        try:
            img_preview = Image.open(io.BytesIO(img_bytes))
        except Exception:
            st.error("Fișierul nu este o imagine validă. Încearcă alt JPG/PNG/WEBP.")
            img_preview = None
        if img_preview is not None:
            col_img, col_act = st.columns([1, 2])
            with col_img:
                st.image(img_preview, use_container_width=True, caption="Factură")
            with col_act:
                st.markdown('<div class="mia-card-sm">', unsafe_allow_html=True)
                st.markdown(f'<div class="mia-eyebrow">Extragere automată date</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<p style="font-size:0.88rem;color:{MIA_MUTED};margin-bottom:1rem;">'
                    'Sistemul identifică furnizorul, numărul facturii, '
                    'produsele, cantitățile și prețurile unitare.</p>', unsafe_allow_html=True)
                if st.button("🔍 Extrage date din factură", type="primary", key="btn_extrage_fact",
                             disabled=img_preview is None):
                    with st.spinner("Gemini analizează factura…"):
                        rez = extrage_factura_ai(img_bytes)
                        if rez and "produse" in rez:
                            st.session_state.produse_factura = rez["produse"]
                            st.session_state.meta_factura = {
                                "furnizor": rez.get("furnizor",""),
                                "nr_factura": rez.get("nr_factura",""),
                                "data": rez.get("data", date.today().strftime("%Y-%m-%d")),
                                "total": rez.get("total", 0.0),
                            }
                            st.success(f"✓ {len(rez['produse'])} produse identificate.")
                        else:
                            st.session_state.produse_factura = []
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.meta_factura:
        meta = st.session_state.meta_factura
        st.markdown(f"""
        <div class="mia-card animate-in" style="margin-top:1rem;">
            <div class="mia-eyebrow">Date factură</div>
            <div style="display:flex;gap:2rem;flex-wrap:wrap;margin-top:0.5rem;">
                <div><span style="color:{MIA_MUTED};font-size:0.8rem;">Furnizor</span><br>
                     <strong style="color:{MIA_TEXT};">{meta.get('furnizor','—')}</strong></div>
                <div><span style="color:{MIA_MUTED};font-size:0.8rem;">Nr. Factură</span><br>
                     <strong style="color:{MIA_TEXT};">{meta.get('nr_factura','—')}</strong></div>
                <div><span style="color:{MIA_MUTED};font-size:0.8rem;">Data</span><br>
                     <strong style="color:{MIA_TEXT};">{meta.get('data','—')}</strong></div>
                <div><span style="color:{MIA_MUTED};font-size:0.8rem;">Total</span><br>
                     <strong style="color:{MIA_PURPLE};">{_f(meta.get('total',0)):,.2f} RON</strong></div>
            </div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.produse_factura:
        stoc_df_f = citeste_stoc()
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(f'<div class="mia-eyebrow">Produse extrase · Verifică și editează</div>',
                    unsafe_allow_html=True)

        produse_editate = []
        alerte          = []
        are_invalide    = False

        for i, prod in enumerate(st.session_state.produse_factura):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2.5, 1, 1.2, 1.2, 1])
                with c1:
                    nume = st.text_input("Produs", value=str(prod.get("produs","")), key=f"pn_{i}")
                with c2:
                    cant = st.number_input("Cantitate", value=_f(prod.get("cantitate",0)),
                                           key=f"pc_{i}", min_value=0.0)
                with c3:
                    unit_ai = str(prod.get("unitate","")).lower().strip()
                    unit_invalid = not unitate_valida(unit_ai)
                    unit = st.text_input("Unitate", value="" if unit_invalid else unit_ai,
                                         key=f"pu_{i}", placeholder="kg/g/l/buc")
                    if unit_invalid:
                        st.markdown(f'<p style="font-size:0.72rem;color:{MIA_RED};margin-top:-8px;">⚠ Unitate necunoscută</p>',
                                    unsafe_allow_html=True)
                        are_invalide = True
                    if unit and not unitate_valida(unit):
                        are_invalide = True
                with c4:
                    pret = st.number_input("Preț/UM", value=_f(prod.get("pret_unitar",0)),
                                           key=f"pp_{i}", min_value=0.0)
                with c5:
                    sm_val = 0.0
                    if not stoc_df_f.empty:
                        mask_sm = stoc_df_f["Produs"].astype(str).str.lower().str.strip() == str(nume).lower().strip()
                        if mask_sm.any():
                            sm_val = _f(stoc_df_f[mask_sm].iloc[0].get("Stoc_Minim",0))
                    stoc_min = st.number_input("Minim", value=sm_val,
                                               key=f"sm_{i}", min_value=0.0, help="Stoc minim alertă")

                # Alertă scumpire
                if not stoc_df_f.empty and "Produs" in stoc_df_f.columns:
                    m = stoc_df_f[stoc_df_f["Produs"].astype(str).str.lower().str.strip() == str(nume).lower().strip()]
                    if not m.empty:
                        try:
                            pret_v = _f(m.iloc[0].get("Pret_Unitar",0))
                            if pret > pret_v > 0:
                                alerte.append({"produs": nume, "vechi": pret_v, "nou": pret})
                        except: pass

                produse_editate.append({
                    "Produs": nume, "Cantitate": cant, "Unitate": unit,
                    "Pret_Unitar": pret, "Data": date.today().strftime("%Y-%m-%d"),
                    "Stoc_Minim": stoc_min,
                })

        for a in alerte:
            diff_pct = (a['nou'] - a['vechi']) / a['vechi'] * 100
            badge_cls = "badge-red" if diff_pct > 5 else "badge-amber"
            st.markdown(f"""
            <div class="mia-card-sm" style="border-color:#FDE68A;margin-bottom:0.5rem;">
                ⚠️ <strong style="color:{MIA_TEXT};">{a['produs']}</strong>
                <span style="color:{MIA_MUTED};"> s-a scumpit de la </span>
                <strong>{a['vechi']:.2f}</strong>
                <span style="color:{MIA_MUTED};"> la </span>
                <strong style="color:{MIA_PURPLE};">{a['nou']:.2f} RON</strong>
                &nbsp;<span class="badge {badge_cls}">+{diff_pct:.1f}%</span>
            </div>""", unsafe_allow_html=True)

        if are_invalide:
            st.warning("Completează unitățile marcate cu ⚠ pentru a activa salvarea.")

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("📦 Adaugă în Stoc →", disabled=are_invalide, type="primary", key="btn_save_stoc"):
            adauga_in_stoc(produse_editate)
            # Log factură
            meta = st.session_state.meta_factura
            salveaza_factura_log(
                meta.get("data", date.today().strftime("%Y-%m-%d")),
                meta.get("furnizor",""),
                meta.get("nr_factura",""),
                _f(meta.get("total",0)),
                json.dumps([p["Produs"] for p in produse_editate])
            )
            st.success(f"✓ {len(produse_editate)} produse adăugate/actualizate în Stoc.")
            st.session_state.produse_factura = []
            st.session_state.meta_factura = {}
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4 — RAPORT Z → SCĂDERE STOC
# ═════════════════════════════════════════════════════════════════════════════
with tab_z:
    st.markdown('<p class="mia-eyebrow">Închidere de zi · scanare automată</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Raport Z</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Fotografiază Raportul Z → vânzările sunt extrase automat → Stocul se scade pe baza rețetarului.</p>',
                unsafe_allow_html=True)

    retetar_df_z = citeste_retetar()
    preparate_z  = sorted(retetar_df_z["Preparat"].dropna().unique().tolist()) if not retetar_df_z.empty else []

    if "raport_z_rezultate" not in st.session_state:
        st.session_state.raport_z_rezultate = []

    # Subtab: Scanare / Manual
    if "z_subtab" not in st.session_state:
        st.session_state.z_subtab = "scanare"

    col_st1, col_st2, _ = st.columns([1.2, 1.2, 5])
    with col_st1:
        if st.button("📷 Scanare Raport Z",
                     type="primary" if st.session_state.z_subtab == "scanare" else "secondary",
                     key="btn_z_scan"):
            st.session_state.z_subtab = "scanare"; st.rerun()
    with col_st2:
        if st.button("✏️ Introducere Manuală",
                     type="primary" if st.session_state.z_subtab == "manual" else "secondary",
                     key="btn_z_manual"):
            st.session_state.z_subtab = "manual"; st.rerun()

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # ── SCANARE ──────────────────────────────────────────────────────────────
    if st.session_state.z_subtab == "scanare":
        st.markdown(f"""
        <div class="mia-card animate-in">
            <div class="mia-eyebrow" style="margin-bottom:0.4rem;">Pas 1 · Încarcă imaginea</div>
            <p style="font-size:0.88rem;color:{MIA_MUTED};margin:0;">
                Fotografiază Raportul Z sau bonurile zilei. Gemini extrage preparatele și cantitățile,
                le potrivește cu rețetarul și scade automat ingredientele din stoc.
            </p>
        </div>""", unsafe_allow_html=True)

        uploaded_z = st.file_uploader("Imagine Raport Z / Bon (JPG, PNG, WEBP)",
                                       type=["jpg","jpeg","png","webp"], key="z_upload")

        if uploaded_z:
            img_bytes_z = uploaded_z.read()
            try:
                img_preview_z = Image.open(io.BytesIO(img_bytes_z))
            except Exception:
                st.error("Fișierul nu este o imagine validă. Încearcă alt JPG/PNG/WEBP.")
                img_preview_z = None
            col_zi, col_za = st.columns([1, 2])
            with col_zi:
                if img_preview_z is not None:
                    st.image(img_preview_z, use_container_width=True, caption="Raport Z")
            with col_za:
                st.markdown('<div class="mia-card-sm">', unsafe_allow_html=True)
                st.markdown(f'<div class="mia-eyebrow">Recunoaștere text · Gemini Vision</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<p style="font-size:0.85rem;color:{MIA_MUTED};margin-bottom:1rem;">'
                    'Sistemul extrage preparatele vândute și le cuplează automat cu rețetarul.</p>',
                    unsafe_allow_html=True)
                if st.button("🔍 Scanează Raportul Z", type="primary", key="btn_scan_z",
                             disabled=img_preview_z is None):
                    if not preparate_z:
                        st.warning("Rețetarul este gol. Adaugă preparate în foaia 'Retetar'.")
                    else:
                        with st.spinner("Gemini analizează raportul…"):
                            rez_z = extrage_raport_z_ai(img_bytes_z)
                        if rez_z and "vanzari" in rez_z:
                            rezultate = []
                            for item in rez_z["vanzari"]:
                                ai_name = str(item.get("produs","")).strip()
                                ai_cant = _f(item.get("cantitate", 0))
                                matched, score = fuzzy_match_preparat(ai_name, preparate_z)
                                rezultate.append({
                                    "ai_name": ai_name, "preparat": matched if matched else "",

                                    "cant": ai_cant, "score": score, "matched": matched is not None,
                                })
                            st.session_state.raport_z_rezultate = rezultate
                            st.success(f"✓ {len(rezultate)} preparate detectate.")
                        else:
                            st.session_state.raport_z_rezultate = []
                st.markdown('</div>', unsafe_allow_html=True)

        # Tabel confirmare
        if st.session_state.raport_z_rezultate:
            st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="mia-card animate-in">
                <div class="mia-eyebrow" style="margin-bottom:0.5rem;">Pas 2 · Confirmă și corectează</div>
                <p style="font-size:0.85rem;color:{MIA_MUTED};margin:0 0 1rem;">
                    Verifică preparatele cuplate automat. Ajustează dacă e nevoie, apoi salvează.
                </p>
            </div>""", unsafe_allow_html=True)

            vanzari_confirmate = []
            for i, row in enumerate(st.session_state.raport_z_rezultate):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    badge = (f'<span class="match-badge-ok">✓ {row["score"]*100:.0f}%</span>'
                             if row["matched"]
                             else '<span class="match-badge-err">⚠ Necuplat</span>')
                    st.markdown(
                        f'<div style="padding-top:1.6rem;">'
                        f'<span style="font-size:0.78rem;color:{MIA_FAINT};">Detectat: {row["ai_name"]}</span>'
                        f'&nbsp;{badge}</div>',
                        unsafe_allow_html=True)
                with col_b:
                    prep_opts = ["— alege —"] + preparate_z
                    def_idx   = (prep_opts.index(row["preparat"])
                                 if row["preparat"] in prep_opts else 0)
                    sel_prep  = st.selectbox("Preparat", prep_opts, index=def_idx, key=f"zp_{i}")
                with col_c:
                    sel_cant = st.number_input("Cantitate", value=float(row["cant"]),
                                               min_value=0.0, step=1.0, key=f"zc_{i}")
                if sel_prep and sel_prep != "— alege —" and sel_cant > 0:
                    vanzari_confirmate.append({
                        "Preparat": sel_prep,
                        "Cantitate_Vanduta": sel_cant,
                        "Data": date.today().strftime("%Y-%m-%d"),
                    })

            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns([1, 2])
            with col_btn1:
                data_z = st.date_input("Data raportului", value=date.today(), key="z_date")

            if vanzari_confirmate and st.button("💾 Salvează Vânzările + Scade Stoc →",
                                                 type="primary", key="btn_z_save"):
                # 1) Scade stocul
                stoc_nou, scazut = scade_stoc_din_vanzari(
                    [{"Preparat":v["Preparat"],"Cantitate_Vanduta":v["Cantitate_Vanduta"]}
                     for v in vanzari_confirmate],
                    retetar_df_z
                )
                salveaza_stoc(stoc_nou)
                # 2) Salvează vânzările
                vz_cu_data = [{**v, "Data": str(data_z)} for v in vanzari_confirmate]
                salveaza_vanzari(vz_cu_data)
                st.success(f"✓ {len(vanzari_confirmate)} vânzări salvate. "
                           f"{len(scazut)} ingrediente scăzute din stoc.")
                # Arată ce s-a scăzut
                if scazut:
                    for item in scazut:
                        minim = item["minim"]
                        cls   = "stoc-low" if minim > 0 and item["dupa"] <= minim else "stoc-ok"
                        st.markdown(f"""
                        <div class="{cls}">
                            <strong>{item['ingredient']}</strong>:
                            {item['inainte']:.3f} → {item['dupa']:.3f} {item['unitate']}
                            (−{item['consum']:.3f})
                            {'⚠ Sub minim!' if minim > 0 and item["dupa"] <= minim else ''}
                        </div>""", unsafe_allow_html=True)
                st.session_state.raport_z_rezultate = []
                st.rerun()

    # ── MANUAL ───────────────────────────────────────────────────────────────
    else:
        st.markdown(f"""
        <div class="mia-card animate-in">
            <div class="mia-eyebrow" style="margin-bottom:0.4rem;">Introducere manuală</div>
            <p style="font-size:0.88rem;color:{MIA_MUTED};margin:0;">
                Adaugă manual vânzările zilei. Stocul se va scădea automat pe baza rețetarului.
            </p>
        </div>""", unsafe_allow_html=True)

        if not preparate_z:
            st.warning("Rețetarul este gol. Adaugă preparate mai întâi.")
        else:
            nr_prep = st.number_input("Număr de preparate vândute azi", min_value=1, max_value=30,
                                      value=3, step=1, key="z_nr_man")
            data_z_m = st.date_input("Data", value=date.today(), key="z_date_man")
            vanzari_man = []
            for i in range(int(nr_prep)):
                ca, cb = st.columns([3, 1])
                with ca:
                    prep_m = st.selectbox("Preparat", ["— alege —"] + preparate_z, key=f"zm_p_{i}")
                with cb:
                    cant_m = st.number_input("Cantitate", min_value=0.0, step=1.0, key=f"zm_c_{i}")
                if prep_m and prep_m != "— alege —" and cant_m > 0:
                    vanzari_man.append({"Preparat": prep_m, "Cantitate_Vanduta": cant_m,
                                        "Data": str(data_z_m)})

            if vanzari_man and st.button("💾 Salvează + Scade Stoc →", type="primary", key="btn_z_man_save"):
                stoc_nou, scazut = scade_stoc_din_vanzari(
                    [{"Preparat":v["Preparat"],"Cantitate_Vanduta":v["Cantitate_Vanduta"]}
                     for v in vanzari_man],
                    retetar_df_z
                )
                salveaza_stoc(stoc_nou)
                salveaza_vanzari(vanzari_man)
                st.success(f"✓ {len(vanzari_man)} vânzări salvate. "
                           f"{len(scazut)} ingrediente scăzute din stoc.")
                for item in scazut:
                    minim = item["minim"]
                    cls   = "stoc-low" if minim > 0 and item["dupa"] <= minim else "stoc-ok"
                    st.markdown(f"""
                    <div class="{cls}">
                        <strong>{item['ingredient']}</strong>:
                        {item['inainte']:.3f} → {item['dupa']:.3f} {item['unitate']}
                        (−{item['consum']:.3f})
                        {'⚠ Sub minim!' if minim > 0 and item["dupa"] <= minim else ''}
                    </div>""", unsafe_allow_html=True)
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5 — REȚETAR & FOOD COST
# ═════════════════════════════════════════════════════════════════════════════
with tab_retetar:
    st.markdown('<p class="mia-eyebrow">Gestiune rețetar</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Rețetar & Food Cost</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Pe baza rețetarului se calculează food costul și se scade stocul automat.</p>',
                unsafe_allow_html=True)

    retetar_df_r = citeste_retetar()
    stoc_df_r    = citeste_stoc()

    col_r1, col_r2 = st.columns([2, 1])
    with col_r1:
        if not retetar_df_r.empty:
            st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:0.5rem;">Rețetar ({len(retetar_df_r)} înregistrări)</div>',
                        unsafe_allow_html=True)
            # Food cost per preparat
            stoc_idx_r = {str(r.get("Produs","")).lower().strip(): _f(r.get("Pret_Unitar",0))
                          for _, r in stoc_df_r.iterrows()} if not stoc_df_r.empty else {}
            preparate_r = retetar_df_r["Preparat"].dropna().unique().tolist()
            for prep in sorted(preparate_r):
                ings_p = retetar_df_r[retetar_df_r["Preparat"] == prep]
                pret_vz = _f(ings_p.iloc[0].get("Pret_Vanzare",0)) if not ings_p.empty else 0
                fc_p = sum(
                    (_f(r.get("Gramaj",0))/1000.0)*stoc_idx_r.get(str(r.get("Ingredient","")).lower().strip(),0)
                    for _, r in ings_p.iterrows()
                )
                fc_pct_p = (fc_p/pret_vz*100) if pret_vz > 0 else 0
                fc_color = MIA_GREEN if fc_pct_p < 30 else (MIA_AMBER if fc_pct_p < 40 else MIA_RED)
                with st.expander(f"🍽 {prep} · Food Cost: {fc_p:.2f} RON ({fc_pct_p:.1f}%)"):
                    for _, ing_r in ings_p.iterrows():
                        st.markdown(f"""
                        <div style="display:flex;justify-content:space-between;
                            padding:0.3rem 0;border-bottom:1px solid #F3F4F6;font-size:0.86rem;">
                            <span style="color:{MIA_MUTED};">{ing_r.get('Ingredient','')}</span>
                            <span style="color:{MIA_TEXT};">{_f(ing_r.get('Gramaj',0)):.0f}g</span>
                        </div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;padding:0.5rem 0;
                        font-size:0.9rem;font-weight:600;">
                        <span style="color:{MIA_TEXT};">Food Cost total</span>
                        <span style="color:{fc_color};">{fc_p:.2f} RON
                            ({fc_pct_p:.1f}% din preț {pret_vz:.2f} RON)</span>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("Rețetarul este gol. Adaugă preparate în foaia 'Retetar' din Google Sheets.")

    with col_r2:
        st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:0.5rem;">Adaugă ingredient în rețetar</div>',
                    unsafe_allow_html=True)
        with st.container():
            prep_new  = st.text_input("Preparat", key="ret_prep", placeholder="ex: Burger Clasic")
            ing_new   = st.text_input("Ingredient", key="ret_ing", placeholder="ex: Carne Vită")
            gram_new  = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key="ret_gram")
            pret_new  = st.number_input("Preț vânzare (RON)", min_value=0.0, step=0.5, key="ret_pret")
            if st.button("Adaugă →", type="primary", key="btn_ret_add"):
                if prep_new and ing_new and gram_new > 0:
                    sheets_append("Retetar", [[prep_new, ing_new, str(gram_new), str(pret_new)]])
                    st.success(f"✓ Ingredientul adăugat în rețetar.")
                    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 6 — SETĂRI
# ═════════════════════════════════════════════════════════════════════════════
with tab_setari:
    st.markdown('<p class="mia-eyebrow">Configurare</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Setări & Cheltuieli</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Parametrii financiari folosiți în cascadă și simulator.</p>',
                unsafe_allow_html=True)

    cfg_set = citeste_config()

    col_sa, col_sb = st.columns(2)
    with col_sa:
        st.markdown('<div class="mia-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:1rem;">Fiscal</div>',
                    unsafe_allow_html=True)
        regim_opts = {"Microîntreprindere 1%": "micro1",
                      "Microîntreprindere 3%": "micro3",
                      "Impozit pe profit 16%": "profit16"}
        regim_sel  = st.selectbox("Regim fiscal",
                                   list(regim_opts.keys()),
                                   index=list(regim_opts.values()).index(
                                       str(cfg_set.get("regim_fiscal","micro1"))
                                   ) if cfg_set.get("regim_fiscal","micro1") in regim_opts.values() else 0)
        tva_opts = {"TVA 9% (restaurante)": 0.09, "TVA 19% (standard)": 0.19}
        tva_sel  = st.selectbox("Cotă TVA", list(tva_opts.keys()),
                                 index=0 if _f(cfg_set.get("cota_tva",0.09)) == 0.09 else 1)
        div_opts = {"Dividende 8%": 0.08, "Dividende 10%": 0.10}
        div_sel  = st.selectbox("Impozit dividende", list(div_opts.keys()),
                                 index=0 if _f(cfg_set.get("cota_dividend",0.08)) == 0.08 else 1)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_sb:
        st.markdown('<div class="mia-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="mia-eyebrow" style="margin-bottom:1rem;">Cheltuieli Lunare</div>',
                    unsafe_allow_html=True)
        chirie    = st.number_input("Chirie lunară (RON)", value=_f(cfg_set.get("chirie_lunara",0)),
                                     min_value=0.0, step=100.0)
        salarii   = st.number_input("Salarii lunare (RON)", value=_f(cfg_set.get("salarii_lunare",0)),
                                     min_value=0.0, step=100.0)
        utilitati = st.number_input("Utilități lunare (RON)", value=_f(cfg_set.get("utilitati_lunare",0)),
                                     min_value=0.0, step=50.0)
        nr_clienti= st.number_input("Nr. clienți/lună (estimat)", value=int(_f(cfg_set.get("nr_clienti_lunar",500))),
                                     min_value=1, step=10)
        st.markdown('</div>', unsafe_allow_html=True)

    # Preview
    fixe_zi   = (chirie + salarii + utilitati) / 30.0
    regie_bon = fixe_zi / max(nr_clienti / 30, 1)
    st.markdown(f"""
    <div class="mia-card-sm animate-in" style="border-color:{MIA_PURPLE_MID};">
        <span style="font-size:0.8rem;color:{MIA_MUTED};">Cheltuieli fixe / zi: </span>
        <span style="font-size:1.1rem;font-weight:700;color:{MIA_PURPLE};">{fixe_zi:.2f} RON</span>
        &nbsp;&nbsp;
        <span style="font-size:0.8rem;color:{MIA_MUTED};">Regie per bon: </span>
        <span style="font-size:1.1rem;font-weight:700;color:{MIA_PURPLE};">{regie_bon:.2f} RON</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    if st.button("Salvează Configurația →", type="primary"):
        salveaza_config({
            "regim_fiscal":    regim_opts[regim_sel],
            "cota_tva":        tva_opts[tva_sel],
            "cota_dividend":   div_opts[div_sel],
            "chirie_lunara":   chirie,
            "salarii_lunare":  salarii,
            "utilitati_lunare":utilitati,
            "nr_clienti_lunar":nr_clienti,
        })
        st.success("✓ Configurația a fost salvată.")

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 7 — SIMULATOR
# ═════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown('<p class="mia-eyebrow">Analiză profitabilitate</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="mia-title">Simulator Preparat</h1>', unsafe_allow_html=True)
    st.markdown('<p class="mia-subtitle">Testează profitabilitatea unui preparat nou înainte de a-l introduce în meniu.</p>',
                unsafe_allow_html=True)

    cfg_sim   = citeste_config()
    stoc_sim  = citeste_stoc()
    produse_s = sorted(stoc_sim["Produs"].dropna().unique().tolist()) if not stoc_sim.empty else []

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger Clasic")
    with col_s2:
        pret_vz = st.number_input("Preț vânzare (cu TVA) · RON", min_value=0.0, step=0.5, format="%.2f")

    st.markdown(f'<div class="mia-eyebrow" style="margin-top:0.25rem;">Ajustare rapidă preț</div>',
                unsafe_allow_html=True)
    # Sliderul ajustează prețul DOAR dacă inputul numeric de mai sus e încă pe 0
    # (preparat nou, fără preț fixat). Dacă userul a introdus un preț, acela e cel activ.
    sl_min = max(1.0, pret_vz - 20) if pret_vz > 0 else 1.0
    sl_max = pret_vz + 40 if pret_vz > 0 else 100.0
    sl_default = float(pret_vz) if pret_vz > 0 else 20.0
    pret_slider = st.slider("Preț", min_value=sl_min, max_value=sl_max, value=sl_default,
                             step=0.5, label_visibility="collapsed",
                             help="Activ doar când câmpul de preț de mai sus e 0 — altfel folosește valoarea tastată")
    pret_calc = pret_vz if pret_vz > 0 else pret_slider

    st.markdown(f"""
    <div style="font-size:0.82rem;color:{MIA_MUTED};margin-bottom:1rem;">
        Preț activ: <strong style="color:{MIA_PURPLE};font-size:1rem;">{pret_calc:.2f} RON</strong>
        &nbsp;·&nbsp;
        <span style="color:{MIA_FAINT};">{'Tastat sus' if pret_vz > 0 else 'Setat din slider'}</span>
    </div>""", unsafe_allow_html=True)

    nr_ing = st.number_input("Nr. ingrediente", min_value=1, max_value=20, value=3, step=1)
    st.markdown(f'<div class="mia-eyebrow" style="margin-top:0.5rem;margin-bottom:0.8rem;">Ingrediente & Gramaje</div>',
                unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ing)):
        ca, cb = st.columns([2.5, 1])
        with ca:
            if produse_s:
                ing = st.selectbox("Ingredient", ["— alege —"] + produse_s, key=f"si_{i}")
            else:
                ing = st.text_input("Ingredient", key=f"si_{i}", placeholder="Ingredient")
        with cb:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sg_{i}")
        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    if ingrediente_sim and pret_calc > 0:
        stoc_idx_sim = {str(r.get("Produs","")).lower().strip(): _f(r.get("Pret_Unitar",0))
                        for _, r in stoc_sim.iterrows()}
        fc_sim = sum(
            (x["gramaj_g"] / 1000.0) * stoc_idx_sim.get(x["ingredient"].lower().strip(), 0.0)
            for x in ingrediente_sim
        )
        nr_cl   = _f(cfg_sim.get("nr_clienti_lunar", 500))
        fixe    = (_f(cfg_sim.get("chirie_lunara",0)) + _f(cfg_sim.get("salarii_lunare",0))
                   + _f(cfg_sim.get("utilitati_lunare",0)))
        regie_s = fixe / nr_cl if nr_cl > 0 else 0
        # IMPORTANT: regie_s e deja cota din cheltuielile fixe lunare alocată acestui preparat.
        # cascada() ar scădea ÎN PLUS cheltuielile fixe ale întregii zile (fixe_zi), ceea ce ar
        # dubla acest cost pentru un singur preparat simulat. De aceea trimitem o config cu
        # cheltuielile fixe lunare zerouite — regia e deja inclusă manual în food_cost.
        cfg_sim_fara_fixe = {**cfg_sim, "chirie_lunara": 0, "salarii_lunare": 0, "utilitati_lunare": 0}
        c_sim   = cascada(pret_calc, fc_sim + regie_s, cfg_sim_fara_fixe)
        c_sim["food_cost"]               = round(fc_sim, 2)
        c_sim["cheltuieli_fixe_zilnice"]  = round(regie_s, 2)

        col_bon, col_rec = st.columns([1, 1])
        with col_bon:
            bon_fiscal(c_sim, titlu=f"SIMULARE · {(nume_prep or 'PREPARAT').upper()}")
        with col_rec:
            marja = c_sim["marja_neta"]
            if marja < 10:
                cota_tva  = _f(cfg_sim.get("cota_tva", 0.09))
                ci_s      = {"micro1":0.01,"micro3":0.03,"profit16":0.16}.get(
                    str(cfg_sim.get("regim_fiscal","micro1")), 0.01)
                cd_s      = _f(cfg_sim.get("cota_dividend", 0.08))
                factor    = (1 - ci_s) * (1 - cd_s)
                pret_rec  = (((fc_sim + regie_s) / (factor * 0.8)) * (1 + cota_tva)
                             if factor > 0 else (fc_sim + regie_s) * 3)
                st.markdown(f"""
                <div class="mia-card-sm animate-in" style="border-color:#FECACA;">
                    <div style="font-size:0.95rem;font-weight:700;color:{MIA_RED};margin-bottom:0.5rem;">
                        ⚠ Marjă insuficientă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:{MIA_MUTED};line-height:1.6;">
                        Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong style="color:{MIA_TEXT};">Preț recomandat (marjă 20%):</strong><br>
                        <span style="font-size:1.1rem;font-weight:700;color:{MIA_RED};">{pret_rec:.2f} RON</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            elif marja <= 20:
                st.markdown(f"""
                <div class="mia-card-sm animate-in" style="border-color:#FDE68A;">
                    <div style="font-size:0.95rem;font-weight:700;color:{MIA_AMBER};margin-bottom:0.5rem;">
                        ℹ Marjă acceptabilă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:{MIA_MUTED};line-height:1.6;">
                        Există loc de optimizare. Caută furnizori mai competitivi.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="mia-card-sm animate-in" style="border-color:#A7F3D0;">
                    <div style="font-size:0.95rem;font-weight:700;color:{MIA_GREEN};margin-bottom:0.5rem;">
                        ✓ Marjă excelentă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:{MIA_MUTED};line-height:1.6;">
                        Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="mia-card-sm animate-in animate-in-delay-1" style="margin-top:0.75rem;">
                <div class="mia-eyebrow" style="margin-bottom:0.75rem;">Detalii calcul</div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MIA_MUTED};">Food cost ingrediente</span>
                    <span style="color:{MIA_TEXT};font-weight:500;">{fc_sim:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MIA_MUTED};">Regie fixă / client</span>
                    <span style="color:{MIA_TEXT};font-weight:500;">{regie_s:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MIA_MUTED};">Preț vânzare activ</span>
                    <span style="color:{MIA_PURPLE};font-weight:700;">{pret_calc:.2f} RON</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="mia-card-sm" style="text-align:center;padding:2rem;border-style:dashed;">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">🧮</div>
            <div style="font-size:0.88rem;color:{MIA_MUTED};">
                Adaugă cel puțin un ingredient și setează un preț.
            </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:2.5rem 0 1.5rem;
    border-top:1px solid {MIA_BORDER};margin-top:3rem;">
    <span style="font-size:0.8rem;color:{MIA_FAINT};">
        ✦ <strong style="color:{MIA_PURPLE};">MIA</strong>
        &nbsp;·&nbsp; Restaurant Intelligence
        &nbsp;·&nbsp; Gestiune inteligentă
    </span>
</div>
""", unsafe_allow_html=True)
