# ═══════════════════════════════════════════════════════════════════════════════
#  LANA · Advisory Platform  —  app.py
#  Design: Apple minimalist · Inter font · light mode
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
# PAGE CONFIG  (apelat înainte de orice alt st.*)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lana Advisory",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  — Apple-minimalist, light mode, Inter
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarNav"]          { display: none !important; }

.stApp                                { background: #f5f5f7 !important; }
[data-testid="stSidebar"]             { display: none !important; }

/* ── Typography helpers ── */
.lana-eyebrow {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #86868b; margin-bottom: 0.4rem;
}
.lana-title {
    font-size: 2rem; font-weight: 700; letter-spacing: -0.03em;
    color: #1d1d1f; line-height: 1.1; margin-bottom: 0.35rem;
}
.lana-subtitle { font-size: 0.9rem; color: #86868b; margin-bottom: 1.8rem; }

/* ── Cards ── */
.lana-card {
    background: #ffffff;
    border: 1px solid #e0e0e5;
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.06);
    margin-bottom: 1rem;
}
.lana-card-sm {
    background: #ffffff;
    border: 1px solid #e0e0e5;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}

/* ── Metric cards ── */
.metric-card {
    background: #ffffff;
    border: 1px solid #e0e0e5;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
    height: 100%;
}
.metric-label {
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #86868b; margin-bottom: 0.6rem;
}
.metric-value {
    font-size: 1.85rem; font-weight: 700; color: #1d1d1f;
    letter-spacing: -0.03em; line-height: 1.1;
}
.metric-sub { font-size: 0.78rem; color: #86868b; margin-top: 0.4rem; }

/* ── Badge ── */
.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.02em;
    margin-top: 0.6rem;
}
.badge-green  { background: rgba(52,199,89,.12);  color: #1a7a36; }
.badge-red    { background: rgba(255,59,48,.10);   color: #c0392b; }
.badge-blue   { background: rgba(0,122,255,.10);   color: #0056cc; }
.badge-amber  { background: rgba(255,159,10,.12);  color: #a05a00; }

/* ── Header bar ── */
.lana-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 2rem;
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid #e0e0e5;
    position: sticky; top: 0; z-index: 999;
    margin: -3rem -4rem 2rem -4rem;
}
.lana-header-logo {
    font-size: 1.15rem; font-weight: 700; color: #1d1d1f; letter-spacing: -0.02em;
}
.lana-header-meta {
    font-size: 0.8rem; color: #86868b; text-align: right; line-height: 1.5;
}
.lana-header-meta strong { color: #1d1d1f; font-weight: 600; }

/* ── Tabs ── */
[data-testid="stTabs"] > div:first-child {
    background: transparent !important;
    border-bottom: 1px solid #e0e0e5 !important;
    gap: 0 !important;
    margin-bottom: 1.5rem !important;
    padding: 0 !important;
}
[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #86868b !important;
    padding: 0.6rem 1.1rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    border-radius: 0 !important;
    transition: color .15s, border-color .15s !important;
}
[data-testid="stTabs"] button:hover { color: #1d1d1f !important; }
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1d1d1f !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #1d1d1f !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #ffffff !important;
    border: 1px solid #d2d2d7 !important;
    border-radius: 10px !important;
    color: #1d1d1f !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.85rem !important;
    box-shadow: none !important;
    transition: border-color .15s, box-shadow .15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #0071e3 !important;
    box-shadow: 0 0 0 3px rgba(0,113,227,.15) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: #c7c7cc !important; }
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label,
.stFileUploader label, .stTextArea label,
.stSlider label {
    color: #6e6e73 !important; font-size: 0.78rem !important;
    font-weight: 500 !important; letter-spacing: 0.03em !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 1px solid #d2d2d7 !important;
    border-radius: 10px !important;
    color: #1d1d1f !important;
}
.stSelectbox > div > div > div { color: #1d1d1f !important; }

/* Password field */
.stTextInput [type="password"] { letter-spacing: 0.15em !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1.5px dashed #d2d2d7 !important;
    border-radius: 14px !important;
    background: #fafafa !important;
    padding: 1.2rem !important;
    color: #86868b !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px !important;
    border: 1px solid #d2d2d7 !important;
    background: #ffffff !important;
    color: #1d1d1f !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.3rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.06) !important;
    transition: all .15s ease !important;
}
.stButton > button:hover {
    background: #f5f5f7 !important;
    border-color: #aeaeb2 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,.09) !important;
}
.stButton > button[kind="primary"] {
    background: #0071e3 !important;
    color: #ffffff !important;
    border-color: #0071e3 !important;
    box-shadow: 0 2px 6px rgba(0,113,227,.35) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #0077ed !important;
    border-color: #0077ed !important;
    box-shadow: 0 3px 10px rgba(0,113,227,.4) !important;
}

/* Slider */
.stSlider > div > div > div > div {
    background: #0071e3 !important;
}

/* Alerts */
.stSuccess, .stWarning, .stError, .stInfo {
    border-radius: 10px !important;
    font-size: 0.88rem !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }

/* Spinner */
.stSpinner > div { border-top-color: #0071e3 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f5f5f7; }
::-webkit-scrollbar-thumb { background: #d2d2d7; border-radius: 3px; }

/* Login page */
.login-wrap {
    max-width: 420px; margin: 5vh auto 0; padding: 2.5rem;
    background: #ffffff; border: 1px solid #e0e0e5;
    border-radius: 20px; box-shadow: 0 4px 24px rgba(0,0,0,.08);
}
.login-logo {
    font-size: 1.5rem; font-weight: 700; letter-spacing: -0.03em;
    color: #1d1d1f; text-align: center; margin-bottom: 0.25rem;
}
.login-tagline {
    font-size: 0.82rem; color: #86868b; text-align: center; margin-bottom: 2rem;
}

/* Cascadă row */
.casc-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.55rem 0; border-bottom: 1px solid #f2f2f2;
}
.casc-label { font-size: 0.88rem; color: #6e6e73; }
.casc-val   { font-size: 0.88rem; font-weight: 500; font-variant-numeric: tabular-nums; }

/* Bon fiscal */
.bon-wrap {
    background: #ffffff; border: 1px solid #e0e0e5; border-radius: 16px;
    padding: 1.8rem; max-width: 400px; box-shadow: 0 2px 10px rgba(0,0,0,.07);
}
.bon-title {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.18em;
    text-transform: uppercase; color: #86868b; text-align: center;
    margin-bottom: 0.3rem;
}
.bon-date  { font-size: 0.72rem; color: #c7c7cc; text-align: center; margin-bottom: 1.2rem; }
.bon-sep   { border: none; border-top: 1px dashed #e0e0e5; margin: 0.8rem 0; }
.bon-line  {
    display: flex; justify-content: space-between;
    padding: 0.28rem 0; font-size: 0.86rem;
}
.bon-net   {
    display: flex; justify-content: space-between; align-items: center; padding-top: 0.8rem;
}
.bon-net-label { font-size: 0.95rem; font-weight: 700; color: #1d1d1f; }
.bon-net-val   { font-size: 1.5rem; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTENTIFICARE  —  credențiale hardcoded
# ─────────────────────────────────────────────────────────────────────────────
CREDENTIALE = {"serban": "lana"}
RESTAURANT   = "Restaurantul Meu SRL"
PLAN_ACTIV   = "Lana Advisory"

def pagina_login():
    """Redă formularul de login centrat, Apple-style."""
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">◈ Lana</div>
        <div class="login-tagline">Platforma ta de management financiar</div>
    </div>
    """, unsafe_allow_html=True)

    # Folosim un container centrat de Streamlit
    col_l, col_c, col_r = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        user  = st.text_input("Utilizator", placeholder="serban")
        parola = st.text_input("Parolă", type="password", placeholder="••••••")
        st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
        if st.button("Autentificare →", type="primary", use_container_width=True):
            if CREDENTIALE.get(user) == parola:
                st.session_state["autentificat"] = True
                st.session_state["utilizator"]   = user
                st.rerun()
            else:
                st.error("Credențiale incorecte. Încearcă din nou.")

# Verificare sesiune
if "autentificat" not in st.session_state:
    st.session_state["autentificat"] = False

if not st.session_state["autentificat"]:
    pagina_login()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER  —  afișat după login
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="lana-header">
    <div style="display:flex;align-items:center;gap:0.75rem;">
        <span style="font-size:1.3rem;font-weight:700;color:#1d1d1f;letter-spacing:-0.02em;">◈ Lana</span>
        <span style="font-size:0.75rem;font-weight:500;color:#aeaeb2;padding:2px 10px;
            border:1px solid #e0e0e5;border-radius:20px;">Advisory</span>
    </div>
    <div class="lana-header-meta">
        <strong>{RESTAURANT}</strong><br>
        <span style="color:#0071e3;font-weight:500;">{PLAN_ACTIV}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ════════════════  BACKEND — JWT / GOOGLE SHEETS  ════════════════════════════
# Implementare pură Python (zero dependențe extra): RSA PKCS#1 v1.5, JWT RS256
# ─────────────────────────────────────────────────────────────────────────────

def _parse_asn1_len(d, p):
    b = d[p]; p += 1
    if b < 0x80: return b, p
    n = b & 0x7f
    return int.from_bytes(d[p:p+n], 'big'), p + n

def _parse_asn1_int(d, p):
    assert d[p] == 0x02, f"ASN.1 INT expected at {p}"
    p += 1; ln, p = _parse_asn1_len(d, p)
    return int.from_bytes(d[p:p+ln], 'big'), p + ln

def _parse_pkcs1(data):
    p = 0
    assert data[p] == 0x30; p += 1
    _, p = _parse_asn1_len(data, p)
    _, p = _parse_asn1_int(data, p)   # version
    n, p = _parse_asn1_int(data, p)   # modulus
    _, p = _parse_asn1_int(data, p)   # publicExponent
    d, p = _parse_asn1_int(data, p)   # privateExponent
    return n, d

def _load_rsa_key(pem: str):
    lines = pem.strip().splitlines()
    b64   = ''.join(l for l in lines if not l.startswith('---'))
    der   = base64.b64decode(b64)
    if b'RSA PRIVATE' in pem.encode():
        return _parse_pkcs1(der)
    # PKCS#8 wrapper
    p = 0
    assert der[p] == 0x30; p += 1
    _, p = _parse_asn1_len(der, p)
    _, p = _parse_asn1_int(der, p)
    assert der[p] == 0x30; p += 1
    aln, p = _parse_asn1_len(der, p); p += aln
    assert der[p] == 0x04; p += 1
    olen, p = _parse_asn1_len(der, p)
    return _parse_pkcs1(der[p:p+olen])

_SHA256_DER = bytes([
    0x30,0x31,0x30,0x0d,0x06,0x09,0x60,0x86,0x48,0x01,0x65,0x03,0x04,
    0x02,0x01,0x05,0x00,0x04,0x20
])

def _rsa_sign(message: bytes, n: int, d: int) -> bytes:
    import hashlib
    k  = (n.bit_length() + 7) // 8
    t  = _SHA256_DER + hashlib.sha256(message).digest()
    ps = b'\xff' * (k - len(t) - 3)
    em = b'\x00\x01' + ps + b'\x00' + t
    s  = pow(int.from_bytes(em, 'big'), d, n)
    return s.to_bytes(k, 'big')

def _make_jwt(sa: dict) -> str:
    def b64u(x): return base64.urlsafe_b64encode(x).rstrip(b'=').decode()
    now = int(time.time())
    hdr = b64u(json.dumps({"alg":"RS256","typ":"JWT"}, separators=(',',':')).encode())
    pld = b64u(json.dumps({
        "iss": sa["client_email"], "sub": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }, separators=(',',':')).encode())
    msg = f"{hdr}.{pld}".encode()
    n, d = _load_rsa_key(sa["private_key"])
    return f"{hdr}.{pld}.{b64u(_rsa_sign(msg, n, d))}"

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

# ── Helpers Sheets ──────────────────────────────────────────────────────────

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
    # clear
    req = urllib.request.Request(
        f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}:clear",
        data=b"{}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    try: urllib.request.urlopen(req)
    except Exception as e: st.error(f"Eroare clear: {e}"); return
    # write
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

# ── CRUD Sheets ──────────────────────────────────────────────────────────────

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
    return _sheet_to_df("Stoc",    ["Produs","Cantitate","Unitate","Pret_Unitar","Data"])

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

def calculeaza_food_cost(vanzari_df, retetar_df, stoc_df) -> float:
    """Calculează food cost total pe baza vânzărilor, rețetarului și stocului."""
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

def _f(x) -> float:
    """Safe float cast."""
    try: return float(x)
    except: return 0.0

def cascada(vanzari_brute: float, food_cost: float, cfg: dict) -> dict:
    """
    Cascadă fiscală:
    Încasări brute → TVA → Food Cost → Cheltuieli fixe
    → Impozit firmă → Impozit dividende → Profit net real
    """
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
    color = "#34c759" if plus else "#ff3b30" if valoare > 0 else "#aeaeb2"
    sign  = "+" if plus else "−"
    st.markdown(f"""
    <div class="casc-row">
        <span class="casc-label">{label}</span>
        <span class="casc-val" style="color:{color};">{sign} {abs(valoare):,.2f} RON</span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(d: dict, titlu: str = "BON FISCAL"):
    net = d["profit_net_real"]
    nc  = "#34c759" if net >= 0 else "#ff3b30"
    linii = [
        ("Încasări brute", "#1d1d1f",  f"{d['vanzari_brute']:,.2f} RON"),
        ("TVA colectat",   "#ff3b30",  f"− {d['tva_colectat']:,.2f} RON"),
        ("Food Cost",      "#ff3b30",  f"− {d['food_cost']:,.2f} RON"),
        ("Cheltuieli fixe","#ff3b30",  f"− {d['cheltuieli_fixe_zilnice']:,.2f} RON"),
        ("Impozit firmă",  "#ff3b30",  f"− {d['impozit_firma']:,.2f} RON"),
        ("Impozit div.",   "#ff3b30",  f"− {d['impozit_dividend']:,.2f} RON"),
    ]
    rows_html = "".join(
        f'<div class="bon-line"><span style="color:#6e6e73;">{l}</span>'
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
# NAVIGARE  —  st.tabs (Apple-style, fără sidebar)
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

    azi = date.today().strftime("%Y-%m-%d")
    v_azi = (vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)]
             if not vanzari_df.empty and "Data" in vanzari_df.columns
             else pd.DataFrame(columns=["Preparat","Cantitate_Vanduta","Data"]))

    # Calculează vânzări brute din rețetar
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

    # ── Carduri metrice ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        tip = "green" if c["profit_net_real"] >= 0 else "red"
        card_metric(
            "Profit Net Real · Bani în mână",
            f"{c['profit_net_real']:,.2f} RON",
            sub=f"Ziua de {azi}",
            badge=f"Marjă {c['marja_neta']:.1f}%",
            tip=tip,
        )
    with col2:
        fc_pct = (c["food_cost"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] > 0 else 0
        card_metric(
            "Food Cost",
            f"{c['food_cost']:,.2f} RON",
            sub=f"{fc_pct:.1f}% din vânzări · {c['food_cost_sursa']}",
        )
    with col3:
        total_chelt = c["cheltuieli_fixe_zilnice"] + c["tva_colectat"] + c["impozit_firma"] + c["impozit_dividend"]
        card_metric(
            "Cheltuieli Totale",
            f"{total_chelt:,.2f} RON",
            sub="Taxe + fixe zilnice",
        )

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Cascadă + vânzări azi ───────────────────────────────────────────────
    col_left, col_right = st.columns([1.3, 1])

    with col_left:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Cascadă Financiară Zilnică</div>',
                    unsafe_allow_html=True)
        casc_row("Încasări brute (cu TVA)", c["vanzari_brute"], plus=True)
        casc_row("TVA colectat (→ ANAF)",   c["tva_colectat"])
        casc_row("Food Cost ingrediente",   c["food_cost"])
        casc_row("Cheltuieli fixe zilnice", c["cheltuieli_fixe_zilnice"])
        # Profit brut intermediar
        pb_col = "#0071e3"
        st.markdown(f"""
        <div class="casc-row">
            <span class="casc-label" style="color:#1d1d1f;font-weight:500;">Profit brut operațional</span>
            <span class="casc-val" style="color:{pb_col};font-weight:600;">{c['profit_brut']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        casc_row("Impozit firmă",     c["impozit_firma"])
        casc_row("Impozit dividende", c["impozit_dividend"])
        # Net final
        nc = "#34c759" if c["profit_net_real"] >= 0 else "#ff3b30"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.9rem 0 0.2rem;">
            <span style="font-size:0.95rem;font-weight:700;color:#1d1d1f;">◈ Bani în mână (net real)</span>
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
                    border-bottom:1px solid #f2f2f2;font-size:0.88rem;">
                    <span style="color:#6e6e73;">{row.get('Preparat','')}</span>
                    <span style="color:#0071e3;font-weight:500;">{row.get('Cantitate_Vanduta',0)} buc</span>
                </div>""", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="lana-card" style="text-align:center;padding:2.5rem;">
                <div style="font-size:2.2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:#6e6e73;font-weight:500;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.78rem;color:#aeaeb2;margin-top:4px;">
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
            st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True,
                     caption="Factură încărcată")
        with col_act:
            st.markdown('<div class="lana-card-sm">', unsafe_allow_html=True)
            st.markdown('<div class="lana-eyebrow">Procesare AI</div>', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:0.88rem;color:#6e6e73;margin-bottom:1rem;">'
                'Gemini 1.5 Flash va identifica produsele, cantitățile, '
                'unitățile și prețurile unitare.</p>',
                unsafe_allow_html=True
            )
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
                    unit = st.text_input(
                        "Unitate",
                        value="" if unit_invalid else unit_ai,
                        key=f"pu_{i}",
                        placeholder="kg / g / l / buc",
                    )
                    if unit_invalid:
                        st.markdown(
                            '<p style="font-size:0.72rem;color:#ff3b30;margin-top:-8px;">'
                            '⚠ Unitate necunoscută</p>',
                            unsafe_allow_html=True
                        )
                        are_invalide = True
                    if unit and unit.lower().strip() not in UNITATI_VALIDE:
                        are_invalide = True
                with c4:
                    pret = st.number_input("Preț / U", value=_f(prod.get("pret_unitar",0)),
                                           key=f"pp_{i}", min_value=0.0)

                # Alertă de scumpire (>0% față de stoc)
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

        # Alerte de scumpire
        for a in alerte:
            diff_pct = (a['nou'] - a['vechi']) / a['vechi'] * 100
            badge_cls = "badge-red" if diff_pct > 5 else "badge-amber"
            st.markdown(f"""
            <div class="lana-card-sm" style="border-color:#ffd60a;margin-bottom:0.5rem;">
                ⚠️ <strong>{a['produs']}</strong> s-a scumpit de la
                <strong>{a['vechi']:.2f}</strong> la
                <strong>{a['nou']:.2f} RON</strong>
                &nbsp;<span class="badge {badge_cls}">+{diff_pct:.1f}%</span>
                {'&nbsp;<span class="badge badge-red">Alertă de Scumpire</span>' if diff_pct > 5 else ''}
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
#  TAB 3 — VÂNZĂRI ZILNICE
# ═════════════════════════════════════════════════════════════════════════════
with tab_vanzari:
    st.markdown('<p class="lana-eyebrow">Închidere de zi</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="lana-title">Vânzări Zilnice</h1>', unsafe_allow_html=True)
    st.markdown('<p class="lana-subtitle">Introdu ce ai vândut azi — stocul se scade automat din rețetar.</p>',
                unsafe_allow_html=True)

    retetar_df = citeste_retetar()
    preparate  = sorted(retetar_df["Preparat"].dropna().unique().tolist()) if not retetar_df.empty else []

    if "vanzari_zi" not in st.session_state:
        st.session_state.vanzari_zi = [{"preparat":"","cantitate":0}]

    if st.button("+ Adaugă preparat"):
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

    data_zi = st.date_input("Data închiderii", value=date.today())
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    if st.button("Înregistrează Închiderea de Zi →", type="primary"):
        if not vanzari_input:
            st.warning("Nu ai introdus niciun preparat.")
        else:
            rows_v = [{"Preparat": v["Preparat"],
                       "Cantitate_Vanduta": v["Cantitate_Vanduta"],
                       "Data": data_zi.strftime("%Y-%m-%d")}
                      for v in vanzari_input if v["Cantitate_Vanduta"] > 0]
            salveaza_vanzari(rows_v)

            # Scade din stoc pe baza rețetarului
            stoc_df = citeste_stoc()
            if not retetar_df.empty and not stoc_df.empty:
                for v in vanzari_input:
                    prep_v = str(v["Preparat"]).lower().strip()
                    cant_v = _f(v["Cantitate_Vanduta"])
                    ings   = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == prep_v]
                    for _, irow in ings.iterrows():
                        ing     = str(irow.get("Ingredient","")).lower().strip()
                        gramaj  = _f(irow.get("Gramaj",0)) / 1000.0
                        consum  = cant_v * gramaj
                        mask    = stoc_df["Produs"].str.lower().str.strip() == ing
                        if mask.any():
                            idx3 = stoc_df[mask].index[0]
                            cur  = _f(stoc_df.at[idx3,"Cantitate"])
                            stoc_df.at[idx3,"Cantitate"] = max(0, round(cur - consum, 4))
                salveaza_stoc(stoc_df)

            st.success(f"✓ {len(rows_v)} preparate înregistrate. Stocul actualizat.")
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
        regim_sel    = st.selectbox("Regim fiscal",list(regim_opts.keys()),
                                    index=list(regim_opts.keys()).index(regim_actual))

        tva_opts   = {"TVA 9% (restaurante)":0.09,"TVA 19% (standard)":0.19}
        tva_rev    = {v:k for k,v in tva_opts.items()}
        tva_actual = tva_rev.get(_f(cfg.get("cota_tva",0.09)),"TVA 9% (restaurante)")
        tva_sel    = st.selectbox("TVA",list(tva_opts.keys()),
                                   index=list(tva_opts.keys()).index(tva_actual))

        div_opts   = {"Impozit dividend 8%":0.08,"Impozit dividend 10%":0.10}
        div_rev    = {v:k for k,v in div_opts.items()}
        div_actual = div_rev.get(_f(cfg.get("cota_dividend",0.08)),"Impozit dividend 8%")
        div_sel    = st.selectbox("Dividend",list(div_opts.keys()),
                                   index=list(div_opts.keys()).index(div_actual))
        st.markdown('</div>', unsafe_allow_html=True)

    with col_s2:
        st.markdown('<div class="lana-card">', unsafe_allow_html=True)
        st.markdown('<div class="lana-eyebrow" style="margin-bottom:1rem;">Cheltuieli Lunare Fixe (RON)</div>',
                    unsafe_allow_html=True)
        chirie    = st.number_input("Chirie lunară",   value=_f(cfg.get("chirie_lunara",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        salarii   = st.number_input("Salarii lunare",  value=_f(cfg.get("salarii_lunare",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        utilitati = st.number_input("Utilități lunare",value=_f(cfg.get("utilitati_lunare",0)),
                                    min_value=0.0, step=100.0, format="%.2f")
        st.markdown('</div>', unsafe_allow_html=True)

    nr_clienti = st.number_input("Nr. estimat clienți / bonuri pe lună",
                                  value=int(_f(cfg.get("nr_clienti_lunar",500))),
                                  min_value=1, step=10)
    total_fixe = chirie + salarii + utilitati
    regie_bon  = total_fixe / nr_clienti if nr_clienti > 0 else 0

    st.markdown(f"""
    <div class="lana-card-sm" style="display:inline-block;margin-top:0.5rem;">
        <span style="font-size:0.8rem;color:#86868b;">Regie fixă per bon: </span>
        <span style="font-size:1.1rem;font-weight:700;color:#0071e3;">{regie_bon:.2f} RON</span>
        <span style="font-size:0.78rem;color:#aeaeb2;"> / client</span>
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
#  TAB 5 — SIMULATOR
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
        pret_vz = st.number_input("Preț vânzare (cu TVA) · RON",
                                   min_value=0.0, step=0.5, format="%.2f")

    # Slider interactiv pentru preț
    pret_slider = st.slider(
        "Ajustează prețul de vânzare (RON)",
        min_value=max(1.0, pret_vz - 20),
        max_value=pret_vz + 40 if pret_vz > 0 else 100.0,
        value=pret_vz if pret_vz > 0 else 20.0,
        step=0.5,
    )
    pret_calc = pret_slider  # prețul activ vine din slider

    nr_ing = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)
    st.markdown('<div class="lana-eyebrow" style="margin-top:0.5rem;margin-bottom:0.8rem;">Ingrediente & Gramaje</div>',
                unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ing)):
        col_a, col_b = st.columns([2.5, 1])
        with col_a:
            if produse_stoc:
                ing = st.selectbox("Ingredient",["— alege —"] + produse_stoc, key=f"si_{i}")
            else:
                ing = st.text_input("Ingredient", key=f"si_{i}", placeholder="Ingredient")
        with col_b:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sg_{i}")
        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Calcul în timp real (se recalculează la orice modificare slider) ──────
    if ingrediente_sim and pret_calc > 0:
        stoc_idx = {str(r.get("Produs","")).lower().strip(): _f(r.get("Pret_Unitar",0))
                    for _, r in stoc_sim.iterrows()}
        fc_sim = sum(
            (x["gramaj_g"] / 1000.0) * stoc_idx.get(x["ingredient"].lower().strip(), 0.0)
            for x in ingrediente_sim
        )
        nr_cl   = _f(cfg_sim.get("nr_clienti_lunar", 500))
        fixe    = _f(cfg_sim.get("chirie_lunara",0)) + _f(cfg_sim.get("salarii_lunare",0)) + _f(cfg_sim.get("utilitati_lunare",0))
        regie_s = fixe / nr_cl if nr_cl > 0 else 0
        c_sim   = cascada(pret_calc, fc_sim + regie_s, cfg_sim)
        c_sim["food_cost"]               = round(fc_sim, 2)
        c_sim["cheltuieli_fixe_zilnice"]  = round(regie_s, 2)

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
                <div class="lana-card-sm" style="border-color:#ff3b30;">
                    <div style="font-size:0.95rem;font-weight:600;color:#ff3b30;margin-bottom:0.5rem;">
                        ⚠ Marjă insuficientă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#6e6e73;line-height:1.6;">
                        Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong style="color:#1d1d1f;">Preț recomandat pentru marjă 20%:</strong><br>
                        <span style="font-size:1.1rem;font-weight:700;color:#ff3b30;">{pret_rec:.2f} RON</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            elif marja <= 20:
                st.markdown(f"""
                <div class="lana-card-sm" style="border-color:#ffd60a;">
                    <div style="font-size:0.95rem;font-weight:600;color:#a05a00;margin-bottom:0.5rem;">
                        ℹ Marjă acceptabilă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#6e6e73;line-height:1.6;">
                        Există loc de optimizare. Caută furnizori mai competitivi pentru ingredientele cheie.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="lana-card-sm" style="border-color:#34c759;">
                    <div style="font-size:0.95rem;font-weight:600;color:#1a7a36;margin-bottom:0.5rem;">
                        ✓ Marjă excelentă ({marja:.1f}%)
                    </div>
                    <div style="font-size:0.85rem;color:#6e6e73;line-height:1.6;">
                        Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.
                    </div>
                </div>""", unsafe_allow_html=True)

            # Detalii calcul
            st.markdown(f"""
            <div class="lana-card-sm" style="margin-top:0.75rem;">
                <div class="lana-eyebrow" style="margin-bottom:0.75rem;">Detalii calcul</div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Food cost ingrediente</span>
                    <span style="color:#1d1d1f;font-weight:500;">{fc_sim:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Regie fixă / client</span>
                    <span style="color:#1d1d1f;font-weight:500;">{regie_s:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:#6e6e73;">Preț vânzare (slider)</span>
                    <span style="color:#0071e3;font-weight:600;">{pret_calc:.2f} RON</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Adaugă cel puțin un ingredient și setează un preț pentru a vedea simularea.")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2.5rem 0 1.5rem;
    border-top:1px solid #e0e0e5;margin-top:3rem;">
    <span style="font-size:0.8rem;color:#aeaeb2;">
        ◈ <strong style="color:#86868b;">Lana Advisory</strong>
        &nbsp;·&nbsp; Consultantul tău digital de buzunar
        &nbsp;·&nbsp; Powered by Gemini AI
    </span>
</div>
""", unsafe_allow_html=True)
