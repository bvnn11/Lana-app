# ═══════════════════════════════════════════════════════════════════════════════
#  LANA · Advisory Platform  —  app.py
#  Design: Apple Dark Mode (macOS-style) · Inter font
#  Features: OCR Raport Z, Stoc Critic, Simulator preț manual, Tabs Vânzări
#  Auth: hardcoded (serban / lana)
#  Connections: st.secrets → gcp_service_account, spreadsheet_id, GEMINI_API_KEY
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
SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lana Advisory",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS — Apple Dark Mode (macOS), animații subtile, Inter
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base dark ── */
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"] { display: none !important; }

.stApp { background: #161617 !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stAppViewContainer"] { background: #161617 !important; }
[data-testid="stVerticalBlock"] { background: transparent !important; }

/* ── Typography ── */
.lana-eyebrow {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #6e6e73; margin-bottom: 0.4rem;
}
.lana-title {
    font-size: 2rem; font-weight: 700; letter-spacing: -0.03em;
    color: #f5f5f7; line-height: 1.1; margin-bottom: 0.35rem;
}
.lana-subtitle { font-size: 0.9rem; color: #6e6e73; margin-bottom: 1.8rem; }

/* ── Cards dark ── */
.lana-card {
    background: #1c1c1e;
    border: 1px solid #2c2c2e;
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.4);
    margin-bottom: 1rem;
    animation: fadeIn .3s ease;
}
.lana-card-sm {
    background: #1c1c1e;
    border: 1px solid #2c2c2e;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
    animation: fadeIn .3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Metric cards dark ── */
.metric-card {
    background: #1c1c1e;
    border: 1px solid #2c2c2e;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(0,0,0,.35);
    height: 100%;
    transition: transform .2s ease, box-shadow .2s ease;
    animation: fadeIn .35s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,.5);
}
.metric-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #6e6e73; margin-bottom: 0.6rem;
}
.metric-value {
    font-size: 1.85rem; font-weight: 700; color: #f5f5f7;
    letter-spacing: -0.03em; line-height: 1.1;
}
.metric-sub { font-size: 0.78rem; color: #6e6e73; margin-top: 0.4rem; }

/* ── Badges dark ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
    margin-top: 0.6rem;
}
.badge-green  { background: rgba(52,199,89,.18);  color: #30d158; }
.badge-red    { background: rgba(255,69,58,.18);   color: #ff453a; }
.badge-blue   { background: rgba(10,132,255,.18);  color: #0a84ff; }
.badge-amber  { background: rgba(255,159,10,.18);  color: #ffd60a; }
.badge-critical {
    background: rgba(255,69,58,.25);
    color: #ff453a;
    border: 1px solid rgba(255,69,58,.4);
    font-size: 0.82rem;
    padding: 5px 14px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(255,69,58,.4); }
    50%      { box-shadow: 0 0 0 6px rgba(255,69,58,.0); }
}

/* ── Header dark ── */
.lana-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 2rem;
    background: rgba(22,22,23,0.88);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid #2c2c2e;
    position: sticky; top: 0; z-index: 999;
    margin: -3rem -4rem 2rem -4rem;
}
.lana-header-logo {
    font-size: 1.15rem; font-weight: 700; color: #f5f5f7; letter-spacing: -0.02em;
}
.lana-header-meta {
    font-size: 0.8rem; color: #6e6e73; text-align: right; line-height: 1.5;
}
.lana-header-meta strong { color: #f5f5f7; font-weight: 600; }

/* ── Tabs dark ── */
[data-testid="stTabs"] > div:first-child {
    background: transparent !important;
    border-bottom: 1px solid #2c2c2e !important;
    gap: 0 !important;
    margin-bottom: 1.5rem !important;
    padding: 0 !important;
}
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #6e6e73 !important;
    padding: 0.6rem 1.1rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    border-radius: 0 !important;
    transition: color .15s, border-color .15s !important;
}
[data-testid="stTabs"] button:hover { color: #f5f5f7 !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #f5f5f7 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #0a84ff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Inputs dark ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #2c2c2e !important;
    border: 1px solid #3a3a3c !important;
    border-radius: 10px !important;
    color: #f5f5f7 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.85rem !important;
    box-shadow: none !important;
    transition: border-color .15s, box-shadow .15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #0a84ff !important;
    box-shadow: 0 0 0 3px rgba(10,132,255,.2) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #48484a !important; }
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stFileUploader label, .stTextArea label,
.stSlider label {
    color: #aeaeb2 !important; font-size: 0.78rem !important;
    font-weight: 500 !important; letter-spacing: 0.03em !important;
}

/* Selectbox dark */
.stSelectbox > div > div {
    background: #2c2c2e !important;
    border: 1px solid #3a3a3c !important;
    border-radius: 10px !important;
    color: #f5f5f7 !important;
}
.stSelectbox > div > div > div { color: #f5f5f7 !important; }
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p { color: #f5f5f7 !important; }

/* Password */
.stTextInput [type="password"] { letter-spacing: 0.15em !important; }

/* File uploader dark */
[data-testid="stFileUploader"] {
    border: 1.5px dashed #3a3a3c !important;
    border-radius: 14px !important;
    background: #1c1c1e !important;
    padding: 1.2rem !important;
    color: #6e6e73 !important;
    transition: border-color .2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #0a84ff !important;
}

/* Buttons dark */
.stButton > button {
    border-radius: 10px !important;
    border: 1px solid #3a3a3c !important;
    background: #2c2c2e !important;
    color: #f5f5f7 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.3) !important;
    transition: all .15s ease !important;
}
.stButton > button:hover {
    background: #3a3a3c !important;
    border-color: #48484a !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: #0a84ff !important;
    color: #ffffff !important;
    border-color: #0a84ff !important;
    box-shadow: 0 2px 10px rgba(10,132,255,.4) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #409cff !important;
    border-color: #409cff !important;
    box-shadow: 0 4px 16px rgba(10,132,255,.5) !important;
    transform: translateY(-1px) !important;
}

/* Slider dark */
.stSlider > div > div > div > div { background: #0a84ff !important; }
.stSlider > div > div > div { background: #3a3a3c !important; }

/* Alerts dark */
.stSuccess { background: rgba(48,209,88,.12) !important; border: 1px solid rgba(48,209,88,.25) !important;
    border-radius: 10px !important; color: #30d158 !important; }
.stWarning { background: rgba(255,159,10,.12) !important; border: 1px solid rgba(255,159,10,.25) !important;
    border-radius: 10px !important; color: #ffd60a !important; }
.stError   { background: rgba(255,69,58,.12) !important; border: 1px solid rgba(255,69,58,.25) !important;
    border-radius: 10px !important; color: #ff453a !important; }
.stInfo    { background: rgba(10,132,255,.12) !important; border: 1px solid rgba(10,132,255,.25) !important;
    border-radius: 10px !important; color: #0a84ff !important; }

/* Dataframe dark */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }

/* Spinner */
.stSpinner > div { border-top-color: #0a84ff !important; }

/* Scrollbar dark */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #161617; }
::-webkit-scrollbar-thumb { background: #3a3a3c; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #48484a; }

/* Login dark */
.login-wrap {
    max-width: 420px; margin: 5vh auto 0; padding: 2.5rem;
    background: #1c1c1e; border: 1px solid #2c2c2e;
    border-radius: 20px; box-shadow: 0 8px 40px rgba(0,0,0,.6);
}
.login-logo {
    font-size: 1.5rem; font-weight: 700; letter-spacing: -0.03em;
    color: #f5f5f7; text-align: center; margin-bottom: 0.25rem;
}
.login-tagline { font-size: 0.82rem; color: #6e6e73; text-align: center; margin-bottom: 2rem; }

/* Cascadă row dark */
.casc-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0; border-bottom: 1px solid #2c2c2e;
}
.casc-label { font-size: 0.88rem; color: #aeaeb2; }
.casc-val   { font-size: 0.88rem; font-weight: 500; font-variant-numeric: tabular-nums; }

/* Bon fiscal dark */
.bon-wrap {
    background: #1c1c1e; border: 1px solid #2c2c2e; border-radius: 16px;
    padding: 1.8rem; max-width: 400px; box-shadow: 0 4px 20px rgba(0,0,0,.4);
}
.bon-title {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em;
    text-transform: uppercase; color: #6e6e73; text-align: center;
    margin-bottom: 0.3rem;
}
.bon-date  { font-size: 0.72rem; color: #48484a; text-align: center; margin-bottom: 1.2rem; }
.bon-sep   { border: none; border-top: 1px dashed #2c2c2e; margin: 0.8rem 0; }
.bon-line  {
    display: flex; justify-content: space-between;
    padding: 0.28rem 0; font-size: 0.86rem;
}
.bon-net   {
    display: flex; justify-content: space-between; align-items: center; padding-top: 0.8rem;
}
.bon-net-label { font-size: 0.95rem; font-weight: 700; color: #f5f5f7; }
.bon-net-val   { font-size: 1.5rem; font-weight: 700; }

/* Sub-tab pills */
.subtab-container {
    display: flex; gap: 0.5rem; margin-bottom: 1.5rem;
}
.subtab-pill {
    padding: 0.45rem 1.1rem; border-radius: 20px; font-size: 0.84rem; font-weight: 500;
    cursor: pointer; border: 1px solid #3a3a3c; background: #2c2c2e; color: #aeaeb2;
    transition: all .15s ease;
}
.subtab-pill.active {
    background: #0a84ff; color: #ffffff; border-color: #0a84ff;
    box-shadow: 0 2px 10px rgba(10,132,255,.35);
}

/* Stoc critic banner */
.stoc-critic-banner {
    background: rgba(255,69,58,.1);
    border: 1px solid rgba(255,69,58,.3);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 1rem;
    animation: fadeIn .4s ease;
}
.stoc-critic-title {
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em;
    text-transform: uppercase; color: #ff453a; margin-bottom: 0.4rem;
}

/* Confirm table rows */
.confirm-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.6rem 0; border-bottom: 1px solid #2c2c2e;
}

/* Match badge */
.match-exact  { color: #30d158; font-size: 0.72rem; font-weight: 600; }
.match-fuzzy  { color: #ffd60a; font-size: 0.72rem; font-weight: 600; }
.match-none   { color: #ff453a; font-size: 0.72rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTENTIFICARE
# ─────────────────────────────────────────────────────────────────────────────
CREDENTIALE = {"serban": "lana"}
RESTAURANT   = "Restaurantul Meu SRL"
PLAN_ACTIV   = "Lana Advisory"

def pagina_login():
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">◈ Lana</div>
        <div class="login-tagline">Platforma ta de management financiar</div>
    </div>
    """, unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        user   = st.text_input("Utilizator", placeholder="serban")
        parola = st.text_input("Parolă", type="password", placeholder="••••••")
        st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
        if st.button("Autentificare →", type="primary", use_container_width=True):
            if CREDENTIALE.get(user) == parola:
                st.session_state["autentificat"] = True
                st.session_state["utilizator"]   = user
                st.rerun()
            else:
                st.error("Credențiale incorecte. Încearcă din nou.")

if "autentificat" not in st.session_state:
    st.session_state["autentificat"] = False

if not st.session_state["autentificat"]:
    pagina_login()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="lana-header">
    <div style="display:flex;align-items:center;gap:0.75rem;">
        <span style="font-size:1.3rem;font-weight:700;color:#f5f5f7;letter-spacing:-0.02em;">◈ Lana</span>
        <span style="font-size:0.75rem;font-weight:500;color:#6e6e73;padding:2px 10px;
            border:1px solid #2c2c2e;border-radius:20px;">Advisory</span>
    </div>
    <div class="lana-header-meta">
        <strong>{RESTAURANT}</strong><br>
        <span style="color:#0a84ff;font-weight:500;">{PLAN_ACTIV}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND — JWT / GOOGLE SHEETS  (folosește cryptography, disponibil pe Streamlit Cloud)
# ─────────────────────────────────────────────────────────────────────────────

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

@st.cache_resource(ttl=3500)
def get_access_token() -> str:
    sa  = st.secrets["gcp_service_account"]
    now = int(time.time())

    hdr = _b64u(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    clm = _b64u(json.dumps({
        "iss":   sa["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   "https://oauth2.googleapis.com/token",
        "iat":   now,
        "exp":   now + 3600,
    }).encode())

    private_key = serialization.load_pem_private_key(
        sa["private_key"].encode(), password=None
    )
    sig_bytes = private_key.sign(
        f"{hdr}.{clm}".encode(),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    jwt = f"{hdr}.{clm}.{_b64u(sig_bytes)}"

    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion":  jwt,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]

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

def citeste_stoc()    -> pd.DataFrame:
    return _sheet_to_df("Stoc", ["Produs","Cantitate","Unitate","Pret_Unitar","Data"])

def salveaza_stoc(df: pd.DataFrame):
    rows = [["Produs","Cantitate","Unitate","Pret_Unitar","Data"]]
    for _, r in df.iterrows():
        rows.append([str(r.get("Produs","")), str(r.get("Cantitate",0)),
                     str(r.get("Unitate","")), str(r.get("Pret_Unitar",0)),
                     str(r.get("Data",""))])
    sheets_clear_write("Stoc", rows)

def citeste_vanzari() -> pd.DataFrame:
    return _sheet_to_df("Vanzari", ["Preparat","Cantitate_Vanduta","Data"])

def salveaza_vanzari(rows_data: list):
    sheets_append("Vanzari",
        [[r["Preparat"], str(r["Cantitate_Vanduta"]), str(r["Data"])] for r in rows_data])

def citeste_retetar() -> pd.DataFrame:
    return _sheet_to_df("Retetar", ["Preparat","Ingredient","Gramaj","Pret_Vanzare"])

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
        ings  = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == prep]
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
# FUZZY MATCHING — potrivire denumiri fără librării externe
# ─────────────────────────────────────────────────────────────────────────────

def _similarity(a: str, b: str) -> float:
    """Similaritate simplă: caractere comune / max lungime (Dice coefficient)."""
    a, b = a.lower().strip(), b.lower().strip()
    if a == b: return 1.0
    if not a or not b: return 0.0
    # Bigrams
    def bigrams(s):
        return {s[i:i+2] for i in range(len(s)-1)}
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb: return 0.0
    return 2.0 * len(ba & bb) / (len(ba) + len(bb))

def fuzzy_match(name: str, candidates: list, threshold: float = 0.45):
    """
    Returnează (match, score, tip) unde tip e 'exact'/'fuzzy'/'none'.
    """
    name_l = name.lower().strip()
    # Exact
    for c in candidates:
        if c.lower().strip() == name_l:
            return c, 1.0, "exact"
    # Contains
    for c in candidates:
        if name_l in c.lower().strip() or c.lower().strip() in name_l:
            return c, 0.85, "fuzzy"
    # Dice
    best, best_score = None, 0.0
    for c in candidates:
        s = _similarity(name_l, c.lower().strip())
        if s > best_score:
            best, best_score = c, s
    if best and best_score >= threshold:
        return best, best_score, "fuzzy"
    return None, 0.0, "none"

# ─────────────────────────────────────────────────────────────────────────────
# AI — GEMINI 1.5 Flash
# ─────────────────────────────────────────────────────────────────────────────

def extrage_factura_ai(img_bytes: bytes) -> dict | None:
    try:
        key    = st.secrets["GEMINI_API_KEY"]
        b64img = base64.b64encode(img_bytes).decode()
        prompt = (
            "Ești un sistem de extragere date din facturi fiscale românești. "
            "Analizează imaginea și extrage TOATE produsele. "
            "Returnează EXCLUSIV JSON valid, fără text extra, fără markdown, fără backticks. "
            'Format: {"produse":[{"produs":"Nume","cantitate":2.0,"unitate":"kg","pret_unitar":15.0}]}'
        )
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
        st.error("AI-ul nu a returnat JSON valid. Încearcă cu o imagine mai clară.")
        return None
    except Exception as e:
        st.error(f"Eroare AI: {e}"); return None

def extrage_raport_z_ai(img_bytes: bytes) -> dict | None:
    """Extrage produsele și cantitățile vândute dintr-un Raport Z / bon fiscal de zi."""
    try:
        key    = st.secrets["GEMINI_API_KEY"]
        b64img = base64.b64encode(img_bytes).decode()
        prompt = (
            "Ești un sistem de extragere date din Rapoarte Z și bonuri fiscale de zi din România. "
            "Analizează imaginea și extrage TOATE produsele/preparatele cu cantitățile VÂNDUTE. "
            "Nu confunda cantitățile cu prețurile. Cantitatea = număr de bucăți/porții vândute. "
            "Returnează EXCLUSIV JSON valid, fără text, fără markdown, fără backticks. "
            'Format exact: {"vanzari":[{"preparat":"Burger Angus","cantitate":20},{"preparat":"Bere","cantitate":30}]}'
        )
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
        st.error("AI-ul nu a returnat JSON valid. Încearcă cu o imagine mai clară.")
        return None
    except Exception as e:
        st.error(f"Eroare AI Raport Z: {e}"); return None

# ─────────────────────────────────────────────────────────────────────────────
# STOC CRITIC — verificare și alertare
# ─────────────────────────────────────────────────────────────────────────────

PRAGURI_CRITICE = {
    "kg": 1.0,
    "g": 500.0,
    "l": 1.0,
    "ml": 500.0,
    "buc": 5.0,
    "bucata": 5.0,
    "bucăți": 5.0,
    "bucati": 5.0,
    "litri": 1.0,
    "grame": 500.0,
    "kilograme": 1.0,
}

def verifica_stoc_critic(stoc_df: pd.DataFrame) -> list:
    """Returnează lista de ingrediente cu stoc critic."""
    critice = []
    if stoc_df.empty: return critice
    for _, row in stoc_df.iterrows():
        prod  = str(row.get("Produs","")).strip()
        cant  = _f(row.get("Cantitate", 0))
        unit  = str(row.get("Unitate","")).lower().strip()
        prag  = PRAGURI_CRITICE.get(unit, 1.0)
        if cant <= prag and cant >= 0:
            critice.append({
                "produs": prod,
                "cantitate": cant,
                "unitate": unit,
                "prag": prag,
            })
    return critice

def afiseaza_alerte_stoc(critice: list):
    if not critice: return
    items_html = " · ".join(
        f"<strong>{c['produs']}</strong> ({c['cantitate']:.2f} {c['unitate']})"
        for c in critice
    )
    st.markdown(f"""
    <div class="stoc-critic-banner">
        <div class="stoc-critic-title">⚠️ Stoc critic detectat</div>
        <div style="font-size:0.86rem;color:#ff453a;">{items_html}</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTE UI
# ─────────────────────────────────────────────────────────────────────────────

def card_metric(titlu: str, valoare: str, sub: str = "", badge: str = "", tip: str = "blue"):
    cls = {"green":"badge-green","red":"badge-red","blue":"badge-blue","amber":"badge-amber"}.get(tip,"badge-blue")
    badge_html = f'<div><span class="badge {cls}">{badge}</span></div>' if badge else ""
    sub_html   = f'<div class="metric-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{titlu}</div>
        <div class="metric-value">{valoare}</div>
        {sub_html}{badge_html}
    </div>""", unsafe_allow_html=True)

def casc_row(label: str, valoare: float, plus: bool = False):
    color = "#30d158" if plus else "#ff453a" if valoare > 0 else "#6e6e73"
    sign  = "+" if plus else "−"
    st.markdown(f"""
    <div class="casc-row">
        <span class="casc-label">{label}</span>
        <span class="casc-val" style="color:{color};">{sign} {abs(valoare):,.2f} RON</span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(d: dict, titlu: str = "BON FISCAL"):
    net = d["profit_net_real"]
    nc  = "#30d158" if net >= 0 else "#ff453a"
    linii = [
        ("Încasări brute", "#f5f5f7",  f"{d['vanzari_brute']:,.2f} RON"),
        ("TVA colectat",   "#ff453a",  f"− {d['tva_colectat']:,.2f} RON"),
        ("Food Cost",      "#ff453a",  f"− {d['food_cost']:,.2f} RON"),
        ("Cheltuieli fixe","#ff453a",  f"− {d['cheltuieli_fixe_zilnice']:,.2f} RON"),
        ("Impozit firmă",  "#ff453a",  f"− {d['impozit_firma']:,.2f} RON"),
        ("Impozit div.",   "#ff453a",  f"− {d['impozit_dividend']:,.2f} RON"),
    ]
    rows_html = "".join(
        f'<div class="bon-line"><span style="color:#aeaeb2;">{l}</span>'
        f'<span style="color:{c};">{v}</span></div>'
        for l, c, v in linii
    )
    st.markdown(f"""
    <div class="bon-wrap">
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
            <span class="badge {'badge-green' if net>=0 else 'badge-red'}">Marjă {d['marja_neta']:.1f}%</span>
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# NAVIGARE
# ─────────────────────────────────────────────────────────────────────────────

tab_dash, tab_facturi, tab_vanzari, tab_setari, tab_sim = st.tabs([
    "Dashboard",
    "Scanare Facturi",
    "Vânzări Zilnice",
    "Setări & Cheltuieli",
    "Simulator",
])

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 1 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
with tab_dash:
    st.markdown('<p class="lana-eyebrow">Situație financiară</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Actualizat la ultima închidere · date live din Google Sheets</p>',
                unsafe_allow_html=True)

    cfg        = citeste_config()
    stoc_df    = citeste_stoc()
    vanzari_df = citeste_vanzari()
    retetar_df = citeste_retetar()

    # ── Alerte stoc critic pe Dashboard ──────────────────────────────────────
    critice_dash = verifica_stoc_critic(stoc_df)
    if critice_dash:
        afiseaza_alerte_stoc(critice_dash)

    azi = date.today().strftime("%Y-%m-%d")
    v_azi = (vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)]
             if not vanzari_df.empty and "Data" in vanzari_df.columns
             else pd.DataFrame(columns=["Preparat","Cantitate_Vanduta","Data"]))

    vb = 0.0
    if not v_azi.empty and not retetar_df.empty:
        for _, row in v_azi.iterrows():
            prep = str(row.get("Preparat","")).lower().strip()
            cant = _f(row.get("Cantitate_Vanduta",0))
            m    = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == prep]
            if not m.empty:
                vb += cant * _f(m.iloc[0].get("Pret_Vanzare",0))

    fc_zi = calculeaza_food_cost(v_azi, retetar_df, stoc_df)
    c     = cascada(vb, fc_zi, cfg)

    col1, col2, col3 = st.columns(3)
    with col1:
        tip = "green" if c["profit_net_real"] >= 0 else "red"
        card_metric("Profit Net Real · Bani în mână", f"{c['profit_net_real']:,.2f} RON",
                    sub=f"Ziua de {azi}", badge=f"Marjă {c['marja_neta']:.1f}%", tip=tip)
    with col2:
        fc_pct = (c["food_cost"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] > 0 else 0
        card_metric("Food Cost", f"{c['food_cost']:,.2f} RON",
                    sub=f"{fc_pct:.1f}% din vânzări · {c['food_cost_sursa']}")
    with col3:
        total_chelt = c["cheltuieli_fixe_zilnice"] + c["tva_colectat"] + c["impozit_firma"] + c["impozit_dividend"]
        card_metric("Cheltuieli Totale", f"{total_chelt:,.2f} RON", sub="Taxe + fixe zilnice")

    # Stoc critic badge suplimentar sub metrici
    if critice_dash:
        badges_html = " ".join(
            f'<span class="badge badge-critical">⚠️ {c["produs"]}</span>'
            for c in critice_dash
        )
        st.markdown(f"<div style='margin-top:0.5rem;'>{badges_html}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Cascadă Financiară Zilnică</div>',
                    unsafe_allow_html=True)
        casc_row("Încasări brute (cu TVA)", c["vanzari_brute"], plus=True)
        casc_row("TVA colectat (→ ANAF)",   c["tva_colectat"])
        casc_row("Food Cost ingrediente",   c["food_cost"])
        casc_row("Cheltuieli fixe zilnice", c["cheltuieli_fixe_zilnice"])
        pb_col = "#0a84ff"
        st.markdown(f"""
        <div class="casc-row">
            <span class="casc-label" style="color:#f5f5f7;font-weight:500;">Profit brut operațional</span>
            <span class="casc-val" style="color:{pb_col};font-weight:600;">{c['profit_brut']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        casc_row("Impozit firmă",     c["impozit_firma"])
        casc_row("Impozit dividende", c["impozit_dividend"])
        nc = "#30d158" if c["profit_net_real"] >= 0 else "#ff453a"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.9rem 0 0.2rem;">
            <span style="font-size:0.95rem;font-weight:700;color:#f5f5f7;">◈ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:700;color:{nc};font-variant-numeric:tabular-nums;">
                {c['profit_net_real']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        if not v_azi.empty:
            st.markdown('<div class="lana-card">', unsafe_allow_html=True)
            st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Vânzări de azi</div>',
                        unsafe_allow_html=True)
            for _, row in v_azi.iterrows():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.4rem 0;
                    border-bottom:1px solid #2c2c2e;font-size:0.88rem;">
                    <span style="color:#aeaeb2;">{row.get('Preparat','')}</span>
                    <span style="color:#0a84ff;font-weight:500;">{row.get('Cantitate_Vanduta',0)} buc</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="lana-card" style="text-align:center;padding:2.5rem;">
                <div style="font-size:2.2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:#aeaeb2;font-weight:500;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.78rem;color:#6e6e73;margin-top:4px;">
                    Mergi la Vânzări Zilnice pentru a înregistra
                </div>
            </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2 — SCANARE FACTURI
# ═════════════════════════════════════════════════════════════════════════════
with tab_facturi:
    st.markdown('<p class="lana-eyebrow">AI · Gemini 1.5 Flash</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Scanare Facturi</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Încarcă o imagine a facturii — AI-ul extrage produsele și alertează scumpirile.</p>',
                unsafe_allow_html=True)

    if "produse_factura" not in st.session_state:
        st.session_state.produse_factura = []

    uploaded = st.file_uploader("Imagine factură (JPG, PNG, WEBP)", type=["jpg","jpeg","png","webp"])

    if uploaded:
        img_bytes = uploaded.read()
        col_img, col_act = st.columns([1, 2])
        with col_img:
            st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True, caption="Factură încărcată")
        with col_act:
            st.markdown('<div class="lana-card-sm">', unsafe_allow_html=True)
            st.markdown('<div class="lana-eyebrow">Procesare AI</div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:0.88rem;color:#6e6e73;margin-bottom:1rem;">'
                'Gemini 1.5 Flash va identifica produsele, cantitățile, unitățile și prețurile unitare.</p>',
                unsafe_allow_html=True)
            if st.button("🔍 Extrage cu AI", type="primary"):
                with st.spinner("Gemini analizează factura…"):
                    rez = extrage_factura_ai(img_bytes)
                    if rez and "produse" in rez:
                        st.session_state.produse_factura = rez["produse"]
                        st.success(f"✓ {len(rez['produse'])} produse identificate.")
                    else:
                        st.session_state.produse_factura = []
            st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.produse_factura:
        stoc_df = citeste_stoc()
        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow">Produse extrase · Verifică și editează</div>',
                    unsafe_allow_html=True)

        produse_editate = []
        alerte          = []
        are_invalide    = False

        for i, prod in enumerate(st.session_state.produse_factura):
            with st.container():
                c1, c2, c3, c4 = st.columns([2.5, 1, 1.2, 1.2])
                with c1:
                    nume = st.text_input("Produs", value=str(prod.get("produs","")), key=f"pn_{i}")
                with c2:
                    cant = st.number_input("Cantitate", value=_f(prod.get("cantitate",0)),
                                           key=f"pc_{i}", min_value=0.0)
                with c3:
                    unit_ai      = str(prod.get("unitate","")).lower().strip()
                    unit_invalid = unit_ai not in UNITATI_VALIDE
                    unit = st.text_input("Unitate", value="" if unit_invalid else unit_ai,
                                         key=f"pu_{i}", placeholder="kg / g / l / buc")
                    if unit_invalid:
                        st.markdown('<p style="font-size:0.72rem;color:#ff453a;margin-top:-8px;">⚠ Unitate necunoscută</p>',
                                    unsafe_allow_html=True)
                        are_invalide = True
                    if unit and unit.lower().strip() not in UNITATI_VALIDE:
                        are_invalide = True
                with c4:
                    pret = st.number_input("Preț / U", value=_f(prod.get("pret_unitar",0)),
                                           key=f"pp_{i}", min_value=0.0)

                if not stoc_df.empty and "Produs" in stoc_df.columns:
                    m = stoc_df[stoc_df["Produs"].str.lower().str.strip() == str(nume).lower().strip()]
                    if not m.empty:
                        try:
                            pret_v = _f(m.iloc[0].get("Pret_Unitar",0))
                            if pret > pret_v > 0:
                                alerte.append({"produs": nume, "vechi": pret_v, "nou": pret})
                        except: pass

                produse_editate.append({
                    "Produs": nume, "Cantitate": cant, "Unitate": unit,
                    "Pret_Unitar": pret, "Data": date.today().strftime("%Y-%m-%d"),
                })

        for a in alerte:
            diff_pct = (a['nou'] - a['vechi']) / a['vechi'] * 100
            badge_cls = "badge-red" if diff_pct > 5 else "badge-amber"
            st.markdown(f"""
            <div class="lana-card-sm" style="border-color:rgba(255,69,58,.4);margin-bottom:0.5rem;">
                ⚠️ <strong style="color:#f5f5f7;">{a['produs']}</strong>
                <span style="color:#aeaeb2;"> s-a scumpit de la
                <strong>{a['vechi']:.2f}</strong> la
                <strong>{a['nou']:.2f} RON</strong></span>
                &nbsp;<span class="badge {badge_cls}">+{diff_pct:.1f}%</span>
                {'&nbsp;<span class="badge badge-red">Alertă Scumpire</span>' if diff_pct > 5 else ''}
            </div>""", unsafe_allow_html=True)

        if are_invalide:
            st.warning("Completează unitățile marcate cu ⚠ pentru a activa salvarea.")

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Salvează în Stoc →", disabled=are_invalide, type="primary"):
            stoc_curent = citeste_stoc()
            stoc_nou    = pd.DataFrame(produse_editate)
            if not stoc_curent.empty:
                for _, row in stoc_nou.iterrows():
                    mask = stoc_curent["Produs"].str.lower().str.strip() == str(row["Produs"]).lower().strip()
                    if mask.any():
                        idx2 = stoc_curent[mask].index[0]
                        stoc_curent.at[idx2,"Cantitate"]   = row["Cantitate"]
                        stoc_curent.at[idx2,"Pret_Unitar"] = row["Pret_Unitar"]
                        stoc_curent.at[idx2,"Data"]        = row["Data"]
                    else:
                        stoc_curent = pd.concat([stoc_curent, pd.DataFrame([row])], ignore_index=True)
                salveaza_stoc(stoc_curent)
            else:
                salveaza_stoc(stoc_nou)
            st.success(f"✓ {len(produse_editate)} produse salvate în Stoc.")
            st.session_state.produse_factura = []
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3 — VÂNZĂRI ZILNICE  (cu sub-tabs: Scanare Raport Z / Introducere Manuală)
# ═════════════════════════════════════════════════════════════════════════════
with tab_vanzari:
    st.markdown('<p class="lana-eyebrow">Închidere de zi</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Vânzări Zilnice</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Alege metoda de înregistrare a vânzărilor din ziua curentă.</p>',
                unsafe_allow_html=True)

    # ── Sub-tab selector ──────────────────────────────────────────────────────
    if "vanzari_subtab" not in st.session_state:
        st.session_state.vanzari_subtab = "manual"

    col_tb1, col_tb2, _ = st.columns([1, 1, 3])
    with col_tb1:
        if st.button("📷 Scanare Raport Z",
                     type="primary" if st.session_state.vanzari_subtab == "scan" else "secondary",
                     use_container_width=True):
            st.session_state.vanzari_subtab = "scan"
            st.rerun()
    with col_tb2:
        if st.button("✏️ Introducere Manuală",
                     type="primary" if st.session_state.vanzari_subtab == "manual" else "secondary",
                     use_container_width=True):
            st.session_state.vanzari_subtab = "manual"
            st.rerun()

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    retetar_df = citeste_retetar()
    preparate  = sorted(retetar_df["Preparat"].dropna().unique().tolist()) if not retetar_df.empty else []

    # ══════════════════════════════════════════════════════════════════════════
    #  SUB-TAB A — SCANARE RAPORT Z
    # ══════════════════════════════════════════════════════════════════════════
    if st.session_state.vanzari_subtab == "scan":
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:0.5rem;">AI · Scanare Raport Z</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.88rem;color:#6e6e73;margin-bottom:1rem;">'
            'Fă o poză la Raportul Z sau la bonul de zi. Gemini extrage automat preparatele '
            'și cantitățile, apoi le potrivește cu rețetarul tău.</p>',
            unsafe_allow_html=True)

        uploaded_z = st.file_uploader(
            "Raport Z / Bon fiscal de zi (JPG, PNG, WEBP)",
            type=["jpg","jpeg","png","webp"],
            key="upload_rapz"
        )

        if "raport_z_rezultat" not in st.session_state:
            st.session_state.raport_z_rezultat = []

        if uploaded_z:
            col_img_z, col_act_z = st.columns([1, 2])
            with col_img_z:
                img_z = Image.open(io.BytesIO(uploaded_z.read()))
                st.image(img_z, use_container_width=True, caption="Raport Z")
                uploaded_z.seek(0)
            with col_act_z:
                if st.button("🔍 Analizează cu AI", type="primary", key="btn_rapz"):
                    with st.spinner("Gemini extrage vânzările din raport…"):
                        img_bytes_z = uploaded_z.read()
                        rez_z = extrage_raport_z_ai(img_bytes_z)
                        if rez_z and "vanzari" in rez_z:
                            # Fuzzy matching cu rețetarul
                            matched = []
                            for item in rez_z["vanzari"]:
                                preparat_ai = str(item.get("preparat","")).strip()
                                cantitate   = _f(item.get("cantitate", 0))
                                match, score, tip = fuzzy_match(preparat_ai, preparate)
                                matched.append({
                                    "preparat_ai":    preparat_ai,
                                    "preparat_match": match or preparat_ai,
                                    "cantitate":      cantitate,
                                    "match_tip":      tip,
                                    "match_score":    round(score * 100),
                                })
                            st.session_state.raport_z_rezultat = matched
                            st.success(f"✓ {len(matched)} preparate detectate. Verifică mai jos.")
                        else:
                            st.error("AI-ul nu a putut extrage vânzările. Încearcă cu o imagine mai clară.")

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Tabel de confirmare ───────────────────────────────────────────────
        if st.session_state.raport_z_rezultat:
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="lana-card">', unsafe_allow_html=True)
            st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Confirmare Vânzări · Verifică și corectează</div>',
                        unsafe_allow_html=True)

            # Header tabel
            st.markdown("""
            <div style="display:grid;grid-template-columns:2fr 2fr 1fr 1fr;gap:0.5rem;
                padding:0.5rem 0;border-bottom:1px solid #3a3a3c;margin-bottom:0.5rem;">
                <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    text-transform:uppercase;color:#6e6e73;">AI a scris</span>
                <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    text-transform:uppercase;color:#6e6e73;">Potrivit cu Rețetar</span>
                <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    text-transform:uppercase;color:#6e6e73;">Match</span>
                <span style="font-size:0.72rem;font-weight:600;letter-spacing:0.08em;
                    text-transform:uppercase;color:#6e6e73;">Cantitate</span>
            </div>""", unsafe_allow_html=True)

            vanzari_confirmate = []
            for i, item in enumerate(st.session_state.raport_z_rezultat):
                tip = item["match_tip"]
                tip_cls = "match-exact" if tip=="exact" else "match-fuzzy" if tip=="fuzzy" else "match-none"
                tip_label = {"exact":"✓ Exact","fuzzy":f"≈ Fuzzy {item['match_score']}%","none":"✗ Nematch"}.get(tip,"?")

                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
                with c1:
                    st.markdown(f"<div style='padding-top:0.6rem;font-size:0.86rem;color:#aeaeb2;'>{item['preparat_ai']}</div>",
                                unsafe_allow_html=True)
                with c2:
                    if preparate:
                        default_idx = preparate.index(item["preparat_match"]) if item["preparat_match"] in preparate else 0
                        preparat_sel = st.selectbox("Preparat", preparate,
                                                    index=default_idx, key=f"rz_prep_{i}",
                                                    label_visibility="collapsed")
                    else:
                        preparat_sel = st.text_input("Preparat", value=item["preparat_match"],
                                                     key=f"rz_prep_{i}", label_visibility="collapsed")
                with c3:
                    st.markdown(f"<div style='padding-top:0.6rem;'><span class='{tip_cls}'>{tip_label}</span></div>",
                                unsafe_allow_html=True)
                with c4:
                    cant_conf = st.number_input("Cant", value=int(item["cantitate"]),
                                               min_value=0, step=1, key=f"rz_cant_{i}",
                                               label_visibility="collapsed")

                if preparat_sel and cant_conf > 0:
                    vanzari_confirmate.append({
                        "Preparat": preparat_sel,
                        "Cantitate_Vanduta": cant_conf,
                    })

            st.markdown('</div>', unsafe_allow_html=True)

            data_z = st.date_input("Data Raportului Z", value=date.today(), key="data_raport_z")
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

            if st.button("✅ Înregistrează Închiderea →", type="primary", key="btn_inreg_z"):
                if not vanzari_confirmate:
                    st.warning("Nu există preparate valide de înregistrat.")
                else:
                    rows_v = [{"Preparat": v["Preparat"],
                               "Cantitate_Vanduta": v["Cantitate_Vanduta"],
                               "Data": data_z.strftime("%Y-%m-%d")}
                              for v in vanzari_confirmate]
                    salveaza_vanzari(rows_v)

                    # Scade din stoc
                    stoc_df = citeste_stoc()
                    if not retetar_df.empty and not stoc_df.empty:
                        for v in vanzari_confirmate:
                            prep_v = str(v["Preparat"]).lower().strip()
                            cant_v = _f(v["Cantitate_Vanduta"])
                            ings   = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == prep_v]
                            for _, irow in ings.iterrows():
                                ing    = str(irow.get("Ingredient","")).lower().strip()
                                gramaj = _f(irow.get("Gramaj",0)) / 1000.0
                                consum = cant_v * gramaj
                                mask   = stoc_df["Produs"].str.lower().str.strip() == ing
                                if mask.any():
                                    idx3 = stoc_df[mask].index[0]
                                    cur  = _f(stoc_df.at[idx3,"Cantitate"])
                                    stoc_df.at[idx3,"Cantitate"] = max(0, round(cur - consum, 4))
                        salveaza_stoc(stoc_df)

                    # Verifică stoc critic după înregistrare
                    stoc_df_nou = citeste_stoc()
                    critice_post = verifica_stoc_critic(stoc_df_nou)
                    st.success(f"✓ {len(rows_v)} preparate înregistrate din Raport Z. Stoc actualizat.")
                    if critice_post:
                        afiseaza_alerte_stoc(critice_post)

                    st.session_state.raport_z_rezultat = []
                    st.rerun()

    # ══════════════════════════════════════════════════════════════════════════
    #  SUB-TAB B — INTRODUCERE MANUALĂ
    # ══════════════════════════════════════════════════════════════════════════
    else:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Introdu Vânzările Manual</div>',
                    unsafe_allow_html=True)
        st.markdown('<p style="font-size:0.88rem;color:#6e6e73;margin-bottom:1rem;">'
                    'Stocul se scade automat din rețetar după înregistrare.</p>',
                    unsafe_allow_html=True)

        if "vanzari_zi" not in st.session_state:
            st.session_state.vanzari_zi = [{"preparat":"","cantitate":0}]

        if st.button("+ Adaugă preparat", key="btn_add_prep"):
            st.session_state.vanzari_zi.append({"preparat":"","cantitate":0})

        vanzari_input = []
        for i, item in enumerate(st.session_state.vanzari_zi):
            col_v1, col_v2 = st.columns([2.5, 1])
            with col_v1:
                if preparate:
                    prep = st.selectbox("Preparat", ["— alege —"] + preparate, key=f"vp_{i}")
                else:
                    prep = st.text_input("Preparat", value="", key=f"vp_{i}", placeholder="Nume preparat")
            with col_v2:
                cant = st.number_input("Cantitate", value=0, min_value=0, step=1, key=f"vc_{i}")
            if prep and prep != "— alege —":
                vanzari_input.append({"Preparat": prep, "Cantitate_Vanduta": cant})

        st.markdown('</div>', unsafe_allow_html=True)

        data_zi = st.date_input("Data închiderii", value=date.today(), key="data_manual")
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        if st.button("Înregistrează Închiderea de Zi →", type="primary", key="btn_inreg_manual"):
            if not vanzari_input:
                st.warning("Nu ai introdus niciun preparat.")
            else:
                rows_v = [{"Preparat": v["Preparat"],
                           "Cantitate_Vanduta": v["Cantitate_Vanduta"],
                           "Data": data_zi.strftime("%Y-%m-%d")}
                          for v in vanzari_input if v["Cantitate_Vanduta"] > 0]
                salveaza_vanzari(rows_v)

                stoc_df = citeste_stoc()
                if not retetar_df.empty and not stoc_df.empty:
                    for v in vanzari_input:
                        prep_v = str(v["Preparat"]).lower().strip()
                        cant_v = _f(v["Cantitate_Vanduta"])
                        ings   = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == prep_v]
                        for _, irow in ings.iterrows():
                            ing    = str(irow.get("Ingredient","")).lower().strip()
                            gramaj = _f(irow.get("Gramaj",0)) / 1000.0
                            consum = cant_v * gramaj
                            mask   = stoc_df["Produs"].str.lower().str.strip() == ing
                            if mask.any():
                                idx3 = stoc_df[mask].index[0]
                                cur  = _f(stoc_df.at[idx3,"Cantitate"])
                                stoc_df.at[idx3,"Cantitate"] = max(0, round(cur - consum, 4))
                    salveaza_stoc(stoc_df)

                # Alerte stoc critic după înregistrare
                stoc_df_nou = citeste_stoc()
                critice_post = verifica_stoc_critic(stoc_df_nou)
                st.success(f"✓ {len(rows_v)} preparate înregistrate. Stocul actualizat.")
                if critice_post:
                    afiseaza_alerte_stoc(critice_post)

                st.session_state.vanzari_zi = [{"preparat":"","cantitate":0}]
                st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4 — SETĂRI & CHELTUIELI
# ═════════════════════════════════════════════════════════════════════════════
with tab_setari:
    st.markdown('<p class="lana-eyebrow">Configurare</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Setări & Cheltuieli</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Configurează parametrii fiscali și cheltuielile lunare fixe.</p>',
                unsafe_allow_html=True)

    cfg = citeste_config()

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Regim Fiscal</div>',
                    unsafe_allow_html=True)

        regim_opts   = {"Micro 1%":"micro1","Micro 3%":"micro3","Profit 16%":"profit16"}
        regim_rev    = {v:k for k,v in regim_opts.items()}
        regim_actual = regim_rev.get(str(cfg.get("regim_fiscal","micro1")),"Micro 1%")
        regim_sel    = st.selectbox("Regim fiscal", list(regim_opts.keys()),
                                    index=list(regim_opts.keys()).index(regim_actual))

        tva_opts   = {"TVA 9% (restaurante)":0.09,"TVA 19% (standard)":0.19}
        tva_rev    = {v:k for k,v in tva_opts.items()}
        tva_actual = tva_rev.get(_f(cfg.get("cota_tva",0.09)),"TVA 9% (restaurante)")
        tva_sel    = st.selectbox("TVA", list(tva_opts.keys()),
                                   index=list(tva_opts.keys()).index(tva_actual))

        div_opts   = {"Impozit dividend 8%":0.08,"Impozit dividend 10%":0.10}
        div_rev    = {v:k for k,v in div_opts.items()}
        div_actual = div_rev.get(_f(cfg.get("cota_dividend",0.08)),"Impozit dividend 8%")
        div_sel    = st.selectbox("Dividend", list(div_opts.keys()),
                                   index=list(div_opts.keys()).index(div_actual))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_s2:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Cheltuieli Lunare Fixe (RON)</div>',
                    unsafe_allow_html=True)
        chirie    = st.number_input("Chirie lunară",    value=_f(cfg.get("chirie_lunara",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        salarii   = st.number_input("Salarii lunare",   value=_f(cfg.get("salarii_lunare",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        utilitati = st.number_input("Utilități lunare", value=_f(cfg.get("utilitati_lunare",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        st.markdown('</div>', unsafe_allow_html=True)

    nr_clienti = st.number_input("Nr. estimat clienți / bonuri pe lună",
                                  value=int(_f(cfg.get("nr_clienti_lunar",500))),
                                  min_value=1, step=10)
    total_fixe = chirie + salarii + utilitati
    regie_bon  = total_fixe / nr_clienti if nr_clienti > 0 else 0

    st.markdown(f"""
    <div class="lana-card-sm" style="display:inline-block;margin-top:0.5rem;">
        <span style="font-size:0.8rem;color:#6e6e73;">Regie fixă per bon: </span>
        <span style="font-size:1.1rem;font-weight:700;color:#0a84ff;">{regie_bon:.2f} RON</span>
        <span style="font-size:0.78rem;color:#6e6e73;"> / client</span>
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
        st.success("✓ Configurația a fost salvată în Google Sheets.")

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5 — SIMULATOR  (preț manual + slider)
# ═════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown('<p class="lana-eyebrow">Analiză profitabilitate</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Simulator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Testează un preparat nou înainte de a-l introduce în meniu.</p>',
                unsafe_allow_html=True)

    cfg_sim  = citeste_config()
    stoc_sim = citeste_stoc()
    produse_stoc = sorted(stoc_sim["Produs"].dropna().unique().tolist()) if not stoc_sim.empty else []

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger clasic")
    with col_s2:
        pret_vz = st.number_input(
            "Preț vânzare (cu TVA) · RON",
            min_value=0.0, step=0.5, format="%.2f",
            help="Introdu prețul direct sau folosește sliderul de mai jos pentru ajustare fină."
        )

    # ── Slider sincronizat cu input manual ───────────────────────────────────
    slider_min = max(0.5, pret_vz - 20) if pret_vz > 0 else 0.5
    slider_max = pret_vz + 40 if pret_vz > 0 else 100.0
    slider_val = float(pret_vz) if pret_vz > 0 else 20.0

    pret_slider = st.slider(
        "Ajustează prețul (RON)",
        min_value=slider_min,
        max_value=slider_max,
        value=slider_val,
        step=0.5,
        help="Mișcă sliderul sau schimbă prețul direct în câmpul de mai sus.",
    )
    # Prețul activ = cel mai mare dintre ce s-a tastat și slider (slider câștigă dacă diferit)
    pret_calc = pret_slider if abs(pret_slider - slider_val) > 0.01 else (pret_vz if pret_vz > 0 else pret_slider)

    st.markdown(f"""
    <div style="display:inline-flex;align-items:center;gap:0.5rem;margin-top:-0.5rem;margin-bottom:1rem;">
        <span style="font-size:0.78rem;color:#6e6e73;">Preț activ:</span>
        <span style="font-size:1.2rem;font-weight:700;color:#0a84ff;">{pret_calc:.2f} RON</span>
    </div>""", unsafe_allow_html=True)

    nr_ing = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)
    st.markdown('<div class="lana-eyebrow" style="margin-top:0.5rem;margin-bottom:0.8rem;">Ingrediente & Gramaje</div>',
                unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ing)):
        col_a, col_b = st.columns([2.5, 1])
        with col_a:
            if produse_stoc:
                ing = st.selectbox("Ingredient", ["— alege —"] + produse_stoc, key=f"si_{i}")
            else:
                ing = st.text_input("Ingredient", key=f"si_{i}", placeholder="Ingredient")
        with col_b:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sg_{i}")
        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    if ingrediente_sim and pret_calc > 0:
        stoc_idx = {str(r.get("Produs","")).lower().strip(): _f(r.get("Pret_Unitar",0))
                    for _, r in stoc_sim.iterrows()}
        fc_sim = sum(
            (x["gramaj_g"] / 1000.0) * stoc_idx.get(x["ingredient"].lower().strip(), 0.0)
            for x in ingrediente_sim
        )
        nr_cl   = _f(cfg_sim.get("nr_clienti_lunar", 500))
        fixe    = (_f(cfg_sim.get("chirie_lunara",0)) +
                   _f(cfg_sim.get("salarii_lunare",0)) +
                   _f(cfg_sim.get("utilitati_lunare",0)))
        regie_s = fixe / nr_cl if nr_cl > 0 else 0
        c_sim   = cascada(pret_calc, fc_sim + regie_s, cfg_sim)
        c_sim["food_cost"]              = round(fc_sim, 2)
        c_sim["cheltuieli_fixe_zilnice"] = round(regie_s, 2)

        col_bon, col_rec = st.columns([1, 1])
        with col_bon:
            bon_fiscal(c_sim, titlu=f"SIMULARE · {(nume_prep or 'PREPARAT').upper()}")
        with col_rec:
            marja = c_sim["marja_neta"]
            if marja < 10:
                cota_tva  = _f(cfg_sim.get("cota_tva", 0.09))
                regim_s   = cfg_sim.get("regim_fiscal","micro1")
                ci_s      = {"micro1":0.01,"micro3":0.03,"profit16":0.16}.get(str(regim_s),0.01)
                cd_s      = _f(cfg_sim.get("cota_dividend", 0.08))
                factor    = (1 - ci_s) * (1 - cd_s)
                pret_rec  = ((fc_sim + regie_s) / (factor * 0.8)) * (1 + cota_tva) if factor > 0 else (fc_sim + regie_s) * 3
                st.markdown(f"""
                <div class="lana-card-sm" style="border-color:rgba(255,69,58,.4);">
                    <div style="font-size:0.95rem;font-weight:600;color:#ff453a;margin-bottom:0.5rem;">
                        ⚠ Marjă insuficientă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#aeaeb2;line-height:1.6;">
                        Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong style="color:#f5f5f7;">Preț recomandat pentru marjă 20%:</strong><br>
                        <span style="font-size:1.1rem;font-weight:700;color:#ff453a;">{pret_rec:.2f} RON</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            elif marja <= 20:
                st.markdown(f"""
                <div class="lana-card-sm" style="border-color:rgba(255,214,10,.3);">
                    <div style="font-size:0.95rem;font-weight:600;color:#ffd60a;margin-bottom:0.5rem;">
                        ℹ Marjă acceptabilă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#aeaeb2;line-height:1.6;">
                        Există loc de optimizare. Caută furnizori mai competitivi.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="lana-card-sm" style="border-color:rgba(48,209,88,.3);">
                    <div style="font-size:0.95rem;font-weight:600;color:#30d158;margin-bottom:0.5rem;">
                        ✓ Marjă excelentă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#aeaeb2;line-height:1.6;">
                        Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="lana-card-sm" style="margin-top:0.75rem;">
                <div class="lana-eyebrow" style="margin-bottom:0.75rem;">Detalii calcul</div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Food cost ingrediente</span>
                    <span style="color:#f5f5f7;font-weight:500;">{fc_sim:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Regie fixă / client</span>
                    <span style="color:#f5f5f7;font-weight:500;">{regie_s:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Preț activ</span>
                    <span style="color:#0a84ff;font-weight:600;">{pret_calc:.2f} RON</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="lana-card" style="text-align:center;padding:2.5rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">🧪</div>
            <div style="font-size:0.9rem;color:#aeaeb2;font-weight:500;">
                Adaugă ingrediente și setează un preț pentru a vedea simularea.
            </div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.5rem;
    border-top:1px solid #2c2c2e;margin-top:3rem;">
    <span style="font-size:0.8rem;color:#3a3a3c;">
        ◈ <strong style="color:#48484a;">Lana Advisory</strong>
        &nbsp;·&nbsp; Consultantul tău digital de buzunar
        &nbsp;·&nbsp; Powered by Gemini AI
    </span>
</div>
""", unsafe_allow_html=True)
