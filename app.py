# ═══════════════════════════════════════════════════════════════════════════════
#  MIA · Restaurant Intelligence Platform
#  v5 — zero dependențe externe (fără cryptography, fără plotly)
#  RSA PKCS#1 v1.5 SHA-256 implementat în Python pur (stdlib only)
#  Backend: Google Sheets API + Gemini 1.5 Flash
#  Auth: st.secrets → gcp_service_account, spreadsheet_id, GEMINI_API_KEY
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import pandas as pd
import json, base64, io, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, date
from PIL import Image
# Plotly opțional — grafice cu HTML pur dacă nu e disponibil
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG PAGINĂ — primul apel Streamlit, înainte de orice altceva
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MIA · Restaurant Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# PALETĂ & CONSTANTE
# ─────────────────────────────────────────────────────────────────────────────
P = "#7C3AED"       # violet principal
P_SOFT = "#EDE9FE"
P_MID  = "#DDD6FE"
BG     = "#F9F9FB"
SURF   = "#FFFFFF"
BORD   = "#E5E7EB"
TEXT   = "#111827"
MUTED  = "#6B7280"
FAINT  = "#9CA3AF"
GREEN  = "#059669"
RED    = "#DC2626"
AMBER  = "#D97706"
BLUE   = "#2563EB"

SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash"

UNITATI = ["kg", "g", "l", "ml", "buc"]

# ─────────────────────────────────────────────────────────────────────────────
# CSS GLOBAL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, html, body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; box-sizing: border-box; }}
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="collapsedControl"], [data-testid="stSidebarNav"] {{ display:none !important; }}
[data-testid="stSidebar"] {{ display:none !important; }}
.stApp {{ background:{BG} !important; }}

::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:#F3F4F6; }}
::-webkit-scrollbar-thumb {{ background:#D1D5DB; border-radius:3px; }}

/* Header */
.mia-header {{
    display:flex; align-items:center; justify-content:space-between;
    padding:0.85rem 2rem; background:rgba(255,255,255,0.9);
    backdrop-filter:blur(20px); border-bottom:1px solid {BORD};
    position:sticky; top:0; z-index:999;
    margin:-3rem -4rem 2rem -4rem;
}}
.mia-logo {{ font-size:1.1rem; font-weight:800; color:{TEXT}; letter-spacing:-0.03em; }}
.mia-logo span {{ color:{P}; }}
.mia-meta {{ font-size:0.78rem; color:{MUTED}; text-align:right; line-height:1.5; }}

/* Typography */
.eyebrow {{
    font-size:0.68rem; font-weight:700; letter-spacing:0.12em;
    text-transform:uppercase; color:{P}; margin-bottom:0.35rem;
}}
.page-title {{
    font-size:2rem; font-weight:800; letter-spacing:-0.04em;
    color:{TEXT}; line-height:1.1; margin-bottom:0.3rem;
}}
.page-sub {{ font-size:0.88rem; color:{MUTED}; margin-bottom:1.6rem; }}

/* Cards */
.card {{
    background:{SURF}; border:1px solid {BORD}; border-radius:16px;
    padding:1.5rem 1.8rem; box-shadow:0 1px 4px rgba(0,0,0,.06);
    margin-bottom:1rem; transition:box-shadow 0.2s,border-color 0.2s;
}}
.card:hover {{ box-shadow:0 4px 20px rgba(124,58,237,.1); border-color:{P_MID}; }}
.card-sm {{
    background:{SURF}; border:1px solid {BORD}; border-radius:12px;
    padding:1.2rem 1.5rem; box-shadow:0 1px 3px rgba(0,0,0,.05);
}}

/* Metric */
.metric-card {{
    background:{SURF}; border:1px solid {BORD}; border-radius:16px;
    padding:1.4rem 1.6rem; box-shadow:0 1px 4px rgba(0,0,0,.05);
    height:100%; transition:transform 0.2s,box-shadow 0.2s,border-color 0.2s;
}}
.metric-card:hover {{ transform:translateY(-2px); box-shadow:0 4px 20px rgba(124,58,237,.1); border-color:{P_MID}; }}
.metric-lbl {{ font-size:0.68rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:{P}; margin-bottom:0.5rem; }}
.metric-val {{ font-size:1.85rem; font-weight:800; color:{TEXT}; letter-spacing:-0.04em; line-height:1.1; }}
.metric-sub {{ font-size:0.78rem; color:{MUTED}; margin-top:0.4rem; }}

/* Badges */
.badge {{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; margin-top:0.5rem; }}
.b-purple {{ background:{P_SOFT}; color:{P}; }}
.b-green  {{ background:#D1FAE5; color:{GREEN}; }}
.b-red    {{ background:#FEE2E2; color:{RED}; }}
.b-blue   {{ background:#DBEAFE; color:{BLUE}; }}
.b-amber  {{ background:#FEF3C7; color:{AMBER}; }}

/* Cascadă */
.casc-row {{ display:flex; justify-content:space-between; align-items:center; padding:0.55rem 0; border-bottom:1px solid #F3F4F6; }}
.casc-lbl {{ font-size:0.88rem; color:{MUTED}; }}
.casc-val {{ font-size:0.88rem; font-weight:600; font-variant-numeric:tabular-nums; }}

/* Bon fiscal */
.bon {{ background:{SURF}; border:1px solid {BORD}; border-radius:16px; padding:1.8rem; box-shadow:0 2px 12px rgba(124,58,237,.08); }}
.bon-title {{ font-size:0.65rem; font-weight:800; letter-spacing:0.18em; text-transform:uppercase; color:{P}; text-align:center; margin-bottom:0.3rem; }}
.bon-date  {{ font-size:0.72rem; color:{FAINT}; text-align:center; margin-bottom:1.2rem; }}
.bon-sep   {{ border:none; border-top:1px dashed {BORD}; margin:0.8rem 0; }}
.bon-line  {{ display:flex; justify-content:space-between; padding:0.28rem 0; font-size:0.86rem; }}

/* Stoc bar */
.stoc-bar-wrap {{ background:#F3F4F6; border-radius:4px; height:6px; overflow:hidden; margin-top:6px; }}
.stoc-bar-fill {{ height:100%; border-radius:4px; transition:width 0.5s ease; }}

/* Login */
.login-wrap {{ max-width:420px; margin:8vh auto 0; padding:2.5rem; background:{SURF}; border:1px solid {BORD}; border-radius:20px; box-shadow:0 8px 40px rgba(124,58,237,.12); }}
.login-logo  {{ font-size:1.6rem; font-weight:800; letter-spacing:-0.04em; color:{TEXT}; text-align:center; margin-bottom:0.2rem; }}
.login-logo span {{ color:{P}; }}
.login-tag   {{ font-size:0.82rem; color:{MUTED}; text-align:center; margin-bottom:2rem; }}

/* Tabs */
[data-testid="stTabs"] > div:first-child {{ background:transparent !important; border-bottom:1px solid {BORD} !important; gap:0 !important; margin-bottom:1.5rem !important; padding:0 !important; }}
[data-testid="stTabs"] button {{ font-family:'Inter',sans-serif !important; font-size:0.88rem !important; font-weight:500 !important; color:{MUTED} !important; padding:0.6rem 1.1rem !important; border:none !important; border-bottom:2px solid transparent !important; background:transparent !important; border-radius:0 !important; transition:color .15s,border-color .15s !important; }}
[data-testid="stTabs"] button:hover {{ color:{TEXT} !important; }}
[data-testid="stTabs"] button[aria-selected="true"] {{ color:{P} !important; font-weight:700 !important; border-bottom:2px solid {P} !important; }}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{ display:none !important; }}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {{
    background:{SURF} !important; border:1.5px solid {BORD} !important;
    border-radius:10px !important; color:{TEXT} !important;
    font-family:'Inter',sans-serif !important; font-size:0.9rem !important;
    padding:0.55rem 0.85rem !important; box-shadow:0 1px 2px rgba(0,0,0,.04) !important;
    transition:border-color .15s,box-shadow .15s !important;
}}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {{
    border-color:{P} !important; box-shadow:0 0 0 3px {P_SOFT} !important; outline:none !important;
}}
.stTextInput label,.stNumberInput label,.stSelectbox label,
.stDateInput label,.stFileUploader label,.stTextArea label,.stSlider label {{
    color:{MUTED} !important; font-size:0.78rem !important; font-weight:600 !important; letter-spacing:0.03em !important;
}}
.stSelectbox > div > div {{ background:{SURF} !important; border:1.5px solid {BORD} !important; border-radius:10px !important; color:{TEXT} !important; }}
[data-testid="stFileUploader"] {{ border:1.5px dashed {P_MID} !important; border-radius:14px !important; background:{P_SOFT} !important; padding:1.2rem !important; }}
[data-testid="stFileUploader"]:hover {{ border-color:{P} !important; background:{P_MID} !important; }}

/* Buttons */
.stButton > button {{ border-radius:10px !important; border:1.5px solid {BORD} !important; background:{SURF} !important; color:{TEXT} !important; font-family:'Inter',sans-serif !important; font-size:0.88rem !important; font-weight:600 !important; padding:0.55rem 1.3rem !important; box-shadow:0 1px 3px rgba(0,0,0,.08) !important; transition:all .15s ease !important; }}
.stButton > button:hover {{ background:{BG} !important; border-color:{P_MID} !important; box-shadow:0 2px 8px rgba(124,58,237,.12) !important; transform:translateY(-1px) !important; }}
.stButton > button[kind="primary"] {{ background:{P} !important; color:#fff !important; border-color:{P} !important; box-shadow:0 2px 8px rgba(124,58,237,.35) !important; }}
.stButton > button[kind="primary"]:hover {{ background:#6D28D9 !important; box-shadow:0 4px 14px rgba(124,58,237,.45) !important; transform:translateY(-1px) !important; }}

/* Slider */
.stSlider > div > div > div > div {{ background:{P} !important; }}

/* Alerts */
.stSuccess {{ background:#D1FAE5 !important; color:{GREEN} !important; border-color:#A7F3D0 !important; border-radius:10px !important; }}
.stWarning {{ background:#FEF3C7 !important; color:{AMBER} !important; border-color:#FDE68A !important; border-radius:10px !important; }}
.stError   {{ background:#FEE2E2 !important; color:{RED} !important; border-color:#FECACA !important; border-radius:10px !important; }}
.stInfo    {{ background:{P_SOFT} !important; color:{P} !important; border-color:{P_MID} !important; border-radius:10px !important; }}

[data-testid="stDataFrame"] {{ border-radius:12px !important; overflow:hidden !important; border:1px solid {BORD} !important; }}
.stSpinner > div {{ border-top-color:{P} !important; }}

@keyframes fadeUp {{ from{{opacity:0;transform:translateY(8px)}} to{{opacity:1;transform:translateY(0)}} }}
.fade-in {{ animation:fadeUp 0.3s cubic-bezier(0.16,1,0.3,1) both; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTENTIFICARE
# ─────────────────────────────────────────────────────────────────────────────
if "auth_ok" not in st.session_state:
    st.session_state.auth_ok = False

if not st.session_state.auth_ok:
    st.markdown("""
    <div class='login-wrap fade-in'>
        <div class='login-logo'>M<span>IA</span></div>
        <div class='login-tag'>Restaurant Intelligence · gestiune simplă și rapidă</div>
    </div>""", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        user = st.text_input("Utilizator", placeholder="username")
        pwd  = st.text_input("Parolă", type="password", placeholder="••••••")
        if st.button("Intră în MIA →", type="primary", use_container_width=True):
            if user == "serban" and pwd == "mia":
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Date incorecte. Încearcă din nou.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class='mia-header'>
    <div class='mia-logo'>M<span>IA</span> · Restaurant Intelligence</div>
    <div class='mia-meta'>
        <strong>{datetime.now().strftime("%d %b %Y · %H:%M")}</strong><br>
        Bun venit, serban
    </div>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE AUTH — JWT + token (cryptography >= 42)
# ─────────────────────────────────────────────────────────────────────────────
def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

# ── RSA PKCS#1 v1.5 SHA-256 — implementare pură Python, zero dependențe ──────
def _parse_pem_private_key(pem: str) -> tuple:
    """
    Parsează cheie privată RSA PEM (PKCS#8 sau PKCS#1) → (n, d, e).
    Stdlib only: base64 + aritmetică DER manuală.
    """
    lines = pem.strip().splitlines()
    b64   = "".join(l for l in lines if not l.startswith("-----"))
    der   = base64.b64decode(b64)

    def rd_len(buf, pos):
        l = buf[pos]; pos += 1
        if l < 0x80:
            return l, pos
        nb = l & 0x7F
        val = 0
        for _ in range(nb):
            val = (val << 8) | buf[pos]; pos += 1
        return val, pos

    def rd_tag(buf, pos, tag):
        assert buf[pos] == tag, f"Așteptat tag {tag:#04x} la {pos}, găsit {buf[pos]:#04x}"
        pos += 1
        l, pos = rd_len(buf, pos)
        return pos, pos + l, l

    def rd_int(buf, pos):
        inner_start, inner_end, l = rd_tag(buf, pos, 0x02)
        raw = buf[inner_start:inner_end]
        return int.from_bytes(raw, "big"), inner_end

    # Outer SEQUENCE
    inner_start, outer_end, _ = rd_tag(der, 0, 0x30)
    pos = inner_start

    # Detectăm formatul:
    # PKCS#1: SEQUENCE { INTEGER(version=0), INTEGER(n), INTEGER(e), INTEGER(d), ... }
    # PKCS#8: SEQUENCE { INTEGER(version=0), SEQUENCE(algId), OCTET_STRING { RSAPrivateKey } }

    # Primul element e întotdeauna version INTEGER
    version, pos_after_ver = rd_int(der, pos)

    # Al doilea element: dacă e 0x30 (SEQUENCE) → PKCS#8, dacă e 0x02 (INTEGER) → PKCS#1
    if der[pos_after_ver] == 0x30:
        # PKCS#8 — sari algorithmIdentifier SEQUENCE
        alg_start, alg_end, alg_l = rd_tag(der, pos_after_ver, 0x30)
        pos = alg_end
        # OCTET STRING conține RSAPrivateKey (PKCS#1)
        oct_start, oct_end, _ = rd_tag(der, pos, 0x04)
        inner = der[oct_start:oct_end]
        # Parsează PKCS#1 din inner
        seq_start, _, _ = rd_tag(inner, 0, 0x30)
        pos2 = seq_start
        _ver, pos2 = rd_int(inner, pos2)   # version
        n,    pos2 = rd_int(inner, pos2)
        e,    pos2 = rd_int(inner, pos2)
        d,    _    = rd_int(inner, pos2)
    else:
        # PKCS#1 direct (version deja citit)
        pos = pos_after_ver
        n, pos = rd_int(der, pos)
        e, pos = rd_int(der, pos)
        d, _   = rd_int(der, pos)

    return n, d, e


def _rsa_pkcs1_sha256_sign(msg: bytes, n: int, d: int) -> bytes:
    """
    RSA PKCS#1 v1.5 cu SHA-256 — implementare pură Python.
    Compatibil cu Google OAuth2 RS256.
    """
    import hashlib
    # DER prefix pentru SHA-256 DigestInfo (RFC 8017)
    DER_SHA256 = bytes([
        0x30, 0x31, 0x30, 0x0d, 0x06, 0x09,
        0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,
        0x05, 0x00, 0x04, 0x20,
    ])
    digest  = hashlib.sha256(msg).digest()
    T       = DER_SHA256 + digest
    k       = (n.bit_length() + 7) // 8
    ps_len  = k - len(T) - 3
    assert ps_len >= 8, "Cheie RSA prea scurtă"
    em      = b"\x00\x01" + b"\xff" * ps_len + b"\x00" + T
    m       = int.from_bytes(em, "big")
    s       = pow(m, d, n)
    return s.to_bytes(k, "big")


def _make_jwt(sa: dict) -> str:
    """Construiește JWT semnat RS256 pentru Google OAuth2 — zero dependențe externe."""
    n, d, e = _parse_pem_private_key(sa["private_key"])
    now = int(time.time())
    hdr = _b64u(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    pld = _b64u(json.dumps({
        "iss": sa["client_email"], "sub": sa["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud":   "https://oauth2.googleapis.com/token",
        "iat":   now, "exp": now + 3600,
    }, separators=(",", ":")).encode())
    msg = f"{hdr}.{pld}".encode()
    sig = _rsa_pkcs1_sha256_sign(msg, n, d)
    return f"{hdr}.{pld}.{_b64u(sig)}"

@st.cache_resource(ttl=3000)
def get_token() -> str:
    sa   = dict(st.secrets["gcp_service_account"])
    jwt  = _make_jwt(sa)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion":  jwt,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]

# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE SHEETS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sid() -> str:
    return st.secrets["spreadsheet_id"]

def sheets_get(rng: str) -> list:
    token = get_token()
    url   = f"{SHEETS_BASE}/{_sid()}/values/{urllib.parse.quote(rng)}"
    req   = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()).get("values", [])
    except Exception as e:
        st.error(f"Eroare citire Sheet ({rng}): {e}")
        return []

def sheets_clear_write(sheet: str, rows: list):
    token = get_token()
    sid   = _sid()
    # 1) clear
    req = urllib.request.Request(
        f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}:clear",
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare clear ({sheet}): {e}"); return
    # 2) write
    body = json.dumps({"values": rows}).encode()
    req2 = urllib.request.Request(
        f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet)}?valueInputOption=RAW",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        urllib.request.urlopen(req2)
    except Exception as e:
        st.error(f"Eroare scriere ({sheet}): {e}")

def sheets_append(sheet: str, rows: list):
    token = get_token()
    body  = json.dumps({"values": rows}).encode()
    url   = (f"{SHEETS_BASE}/{_sid()}/values/{urllib.parse.quote(sheet)}:append"
             f"?valueInputOption=RAW&insertDataOption=INSERT_ROWS")
    req   = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare append ({sheet}): {e}")

def _sheet_to_df(sheet: str, cols: list) -> pd.DataFrame:
    rows = sheets_get(sheet)
    if len(rows) <= 1:
        return pd.DataFrame(columns=cols)
    hdr  = rows[0]
    data = [dict(zip(hdr, row + [""] * max(0, len(hdr) - len(row)))) for row in rows[1:]]
    df   = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

# ─────────────────────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────────────────────
def citeste_config() -> dict:
    rows = sheets_get("Config")
    cfg  = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            try:    cfg[row[0].strip()] = float(row[1].strip())
            except: cfg[row[0].strip()] = row[1].strip()
    return cfg

def salveaza_config(cfg: dict):
    sheets_clear_write("Config", [["Cheie", "Valoare"]] + [[k, str(v)] for k, v in cfg.items()])
    get_token.clear()

def citeste_stoc() -> pd.DataFrame:
    return _sheet_to_df("Stoc", ["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data", "Stoc_Minim"])

def salveaza_stoc(df: pd.DataFrame):
    rows = [["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data", "Stoc_Minim"]]
    for _, r in df.iterrows():
        rows.append([
            str(r.get("Produs", "")), str(r.get("Cantitate", 0)),
            str(r.get("Unitate", "")), str(r.get("Pret_Unitar", 0)),
            str(r.get("Data", "")), str(r.get("Stoc_Minim", 0)),
        ])
    sheets_clear_write("Stoc", rows)

def citeste_vanzari() -> pd.DataFrame:
    return _sheet_to_df("Vanzari", ["Preparat", "Cantitate_Vanduta", "Data"])

def salveaza_vanzari(rows_data: list):
    sheets_append("Vanzari", [[r["Preparat"], str(r["Cantitate_Vanduta"]), str(r["Data"])] for r in rows_data])

def citeste_retetar() -> pd.DataFrame:
    return _sheet_to_df("Retetar", ["Preparat", "Ingredient", "Gramaj", "Pret_Vanzare"])

def salveaza_retetar(df: pd.DataFrame):
    rows = [["Preparat", "Ingredient", "Gramaj", "Pret_Vanzare"]]
    for _, r in df.iterrows():
        rows.append([str(r.get("Preparat", "")), str(r.get("Ingredient", "")),
                     str(r.get("Gramaj", 0)), str(r.get("Pret_Vanzare", 0))])
    sheets_clear_write("Retetar", rows)

def citeste_facturi_log() -> pd.DataFrame:
    return _sheet_to_df("FacturiLog", ["Data", "Furnizor", "NrFactura", "Total", "Produse"])

def salveaza_factura_log(data: str, furnizor: str, nr: str, total: float, produse_json: str):
    sheets_append("FacturiLog", [[data, furnizor, nr, str(total), produse_json]])

# ─────────────────────────────────────────────────────────────────────────────
# UTILITARE
# ─────────────────────────────────────────────────────────────────────────────
def _f(x) -> float:
    try: return float(x)
    except: return 0.0

def _normalize(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower().strip())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

def fuzzy_match(name: str, options: list, threshold: float = 0.35):
    """Potrivire fuzzy simplă bazată pe overlap de cuvinte."""
    best, best_sc = None, 0.0
    na = set(_normalize(name).split())
    for opt in options:
        nb = set(_normalize(opt).split())
        if not na or not nb: continue
        sc = len(na & nb) / max(len(na), len(nb))
        if _normalize(opt).startswith(_normalize(name)[:4]):
            sc += 0.2
        if sc > best_sc:
            best_sc, best = sc, opt
    return (best, best_sc) if best_sc >= threshold else (None, 0.0)

# ─────────────────────────────────────────────────────────────────────────────
# LOGICĂ STOC
# ─────────────────────────────────────────────────────────────────────────────
def adauga_in_stoc(produse_list: list):
    stoc_df = citeste_stoc()
    for prod in produse_list:
        nu  = str(prod.get("Produs", "")).strip()
        can = _f(prod.get("Cantitate", 0))
        un  = str(prod.get("Unitate", "")).strip()
        pr  = _f(prod.get("Pret_Unitar", 0))
        dat = str(prod.get("Data", date.today().isoformat()))
        sm  = _f(prod.get("Stoc_Minim", 0))
        if not nu: continue
        if not stoc_df.empty:
            mask = stoc_df["Produs"].astype(str).str.lower().str.strip() == nu.lower().strip()
            if mask.any():
                idx = stoc_df[mask].index[0]
                stoc_df.at[idx, "Cantitate"]   = round(_f(stoc_df.at[idx, "Cantitate"]) + can, 4)
                stoc_df.at[idx, "Pret_Unitar"] = pr
                stoc_df.at[idx, "Data"]        = dat
                continue
        new_row = {"Produs": nu, "Cantitate": can, "Unitate": un,
                   "Pret_Unitar": pr, "Data": dat, "Stoc_Minim": sm}
        stoc_df = pd.concat([stoc_df, pd.DataFrame([new_row])], ignore_index=True)
    salveaza_stoc(stoc_df)
    return stoc_df

def scade_stoc(vanzari_input: list, retetar_df: pd.DataFrame):
    stoc_df = citeste_stoc()
    if retetar_df.empty or stoc_df.empty:
        return stoc_df, []
    scazut = []
    for v in vanzari_input:
        prep  = str(v["Preparat"]).lower().strip()
        cant  = _f(v["Cantitate_Vanduta"])
        ings  = retetar_df[retetar_df["Preparat"].astype(str).str.lower().str.strip() == prep]
        for _, irow in ings.iterrows():
            ing_name = str(irow.get("Ingredient", "")).lower().strip()
            gramaj_g = _f(irow.get("Gramaj", 0))
            de_scazut = cant * gramaj_g / 1000.0
            mask = stoc_df["Produs"].astype(str).str.lower().str.strip() == ing_name
            if mask.any():
                idx = stoc_df[mask].index[0]
                vechi = _f(stoc_df.at[idx, "Cantitate"])
                nou   = max(0.0, vechi - de_scazut)
                stoc_df.at[idx, "Cantitate"] = round(nou, 4)
                scazut.append({
                    "ingredient": str(irow.get("Ingredient", "")),
                    "scazut": round(de_scazut, 4),
                    "dupa": round(nou, 4),
                    "minim": _f(stoc_df.at[idx, "Stoc_Minim"]),
                })
    return stoc_df, scazut

# ─────────────────────────────────────────────────────────────────────────────
# CALCULE FINANCIARE
# ─────────────────────────────────────────────────────────────────────────────
def calculeaza_food_cost(vanzari_df, retetar_df, stoc_df) -> float:
    if vanzari_df.empty or retetar_df.empty or stoc_df.empty:
        return 0.0
    idx = {str(r.get("Produs", "")).lower().strip(): _f(r.get("Pret_Unitar", 0))
           for _, r in stoc_df.iterrows()}
    total = 0.0
    for _, vrow in vanzari_df.iterrows():
        prep = str(vrow.get("Preparat", "")).lower().strip()
        cant = _f(vrow.get("Cantitate_Vanduta", 0))
        ings = retetar_df[retetar_df["Preparat"].astype(str).str.lower().str.strip() == prep]
        for _, irow in ings.iterrows():
            kg = _f(irow.get("Gramaj", 0)) / 1000.0
            total += cant * kg * idx.get(str(irow.get("Ingredient", "")).lower().strip(), 0.0)
    return round(total, 2)

def cascada(vanzari_brute: float, food_cost: float, cfg: dict) -> dict:
    """Calculează cascada financiară completă."""
    tva       = _f(cfg.get("cota_tva", 0.09))
    chirie    = _f(cfg.get("chirie_lunara", 0))
    salarii   = _f(cfg.get("salarii_lunare", 0))
    utilitati = _f(cfg.get("utilitati_lunare", 0))
    regim     = str(cfg.get("regim_fiscal", "micro1"))
    div       = _f(cfg.get("cota_dividend", 0.08))
    ci        = {"micro1": 0.01, "micro3": 0.03, "profit16": 0.16}.get(regim, 0.01)

    tva_col     = vanzari_brute - vanzari_brute / (1 + tva)
    net_tva     = vanzari_brute / (1 + tva)
    fixe_zi     = (chirie + salarii + utilitati) / 30.0
    fc_eff      = food_cost if food_cost > 0 else net_tva * 0.30
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
        "profit_brut":             round(profit_brut, 2),
        "impozit_firma":           round(imp_firma, 2),
        "profit_dupa_impozit":     round(dupa_imp, 2),
        "impozit_dividend":        round(imp_div, 2),
        "profit_net_real":         round(net, 2),
        "marja_neta":              round(marja, 2),
    }

# ─────────────────────────────────────────────────────────────────────────────
# AI — GEMINI 1.5 FLASH
# ─────────────────────────────────────────────────────────────────────────────
def _gemini_call(img_bytes: bytes, prompt: str) -> dict | None:
    try:
        key     = st.secrets["GEMINI_API_KEY"]
        b64_img = base64.b64encode(img_bytes).decode()
        payload = json.dumps({"contents": [{"parts": [
            {"inline_data": {"mime_type": "image/jpeg", "data": b64_img}},
            {"text": prompt},
        ]}]}).encode()
        
        # CORECTAT: Am adăugat :generateContent direct aici în URL, înainte de cheie
        req = urllib.request.Request(
            f"{GEMINI_BASE}:generateContent?key={key}", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
        raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("Extragerea nu a returnat date valide. Încearcă cu o imagine mai clară.")
        return None
    except Exception as e:
        st.error(f"Eroare Gemini: {e}")
        return None

def extrage_factura(img_bytes: bytes) -> dict | None:
    prompt = (
        "Ești un sistem specializat în extragerea datelor din facturi fiscale românești. "
        "Analizează imaginea și extrage: furnizorul (numele firmei), numărul facturii, "
        "data facturii și TOATE produsele cu cantitate, unitate de măsură și preț unitar. "
        "Returnează EXCLUSIV JSON valid, fără text extra, fără markdown. "
        'Format exact: {"furnizor":"Firma SRL","nr_factura":"F001","data":"2024-01-15",'
        '"total":150.0,"produse":[{"produs":"Făină","cantitate":50.0,"unitate":"kg","pret_unitar":2.5}]}'
    )
    return _gemini_call(img_bytes, prompt)

def extrage_raport_z(img_bytes: bytes) -> dict | None:
    prompt = (
        "Ești un sistem OCR specializat pentru bonuri fiscale și Rapoarte Z din restaurante românești. "
        "Analizează imaginea și extrage TOATE produsele/preparatele vândute cu cantitățile lor. "
        "Ignoră taxe, subtotaluri, TVA, totaluri — extrage doar produsele individuale. "
        "Returnează EXCLUSIV JSON valid, fără text extra, fără markdown. "
        'Format exact: {"vanzari":[{"produs":"Burger Clasic","cantitate":5}]} '
        "Cantitățile trebuie să fie numere. Sumează dacă același produs apare de mai multe ori."
    )
    return _gemini_call(img_bytes, prompt)

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENTE UI REUTILIZABILE
# ─────────────────────────────────────────────────────────────────────────────
def card_metric(label: str, value: str, sub: str = "", badge: str = "", tip: str = "purple"):
    colors = {"purple": P, "green": GREEN, "red": RED, "blue": BLUE, "amber": AMBER}
    color  = colors.get(tip, P)
    badge_html = f'<div class="badge b-{tip}">{badge}</div>' if badge else ""
    st.markdown(f"""
    <div class="metric-card fade-in">
        <div class="metric-lbl">{label}</div>
        <div class="metric-val" style="color:{color};">{value}</div>
        {f'<div class="metric-sub">{sub}</div>' if sub else ''}
        {badge_html}
    </div>""", unsafe_allow_html=True)

def casc_row(label: str, val: float, plus: bool = False, bold: bool = False):
    color  = GREEN if plus else RED
    sign   = "+" if plus else "−"
    weight = "700" if bold else "600"
    vcolor = P if bold else TEXT
    st.markdown(f"""
    <div class="casc-row">
        <span class="casc-lbl" style="font-weight:{weight};color:{vcolor if bold else MUTED};">{label}</span>
        <span class="casc-val" style="color:{color if not bold else vcolor};">
            {sign if not bold else ''}{val:,.2f} RON
        </span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(c: dict, titlu: str = "SIMULARE"):
    tva_pct = round(c["tva_colectat"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] else 9
    net_color = GREEN if c["profit_net_real"] >= 0 else RED
    st.markdown(f"""
    <div class="bon fade-in">
        <div class="bon-title">{titlu}</div>
        <div class="bon-date">{datetime.now().strftime("%d.%m.%Y · %H:%M")}</div>
        <hr class="bon-sep">
        <div class="bon-line"><span style="color:{MUTED};">Preț vânzare (cu TVA)</span><span style="font-weight:600;">{c['vanzari_brute']:.2f} RON</span></div>
        <div class="bon-line"><span style="color:{MUTED};">TVA {tva_pct}% → ANAF</span><span style="color:{RED};">− {c['tva_colectat']:.2f} RON</span></div>
        <div class="bon-line"><span style="color:{MUTED};">Bază impozabilă</span><span>{c['vanzari_fara_tva']:.2f} RON</span></div>
        <hr class="bon-sep">
        <div class="bon-line"><span style="color:{MUTED};">Food cost</span><span style="color:{RED};">− {c['food_cost']:.2f} RON</span></div>
        <div class="bon-line"><span style="color:{MUTED};">Cheltuieli fixe / zi</span><span style="color:{RED};">− {c['cheltuieli_fixe_zilnice']:.2f} RON</span></div>
        <div class="bon-line"><span style="color:{MUTED};">Profit brut op.</span><span style="color:{P};font-weight:600;">{c['profit_brut']:.2f} RON</span></div>
        <hr class="bon-sep">
        <div class="bon-line"><span style="color:{MUTED};">Impozit firmă</span><span style="color:{RED};">− {c['impozit_firma']:.2f} RON</span></div>
        <div class="bon-line"><span style="color:{MUTED};">Impozit dividende</span><span style="color:{RED};">− {c['impozit_dividend']:.2f} RON</span></div>
        <hr class="bon-sep">
        <div style="display:flex;justify-content:space-between;align-items:center;padding-top:0.6rem;">
            <span style="font-size:0.95rem;font-weight:700;color:{TEXT};">✦ Bani în mână</span>
            <span style="font-size:1.5rem;font-weight:800;color:{net_color};">{c['profit_net_real']:.2f} RON</span>
        </div>
        <div style="text-align:right;font-size:0.78rem;color:{FAINT};margin-top:4px;">Marjă netă: {c['marja_neta']:.1f}%</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# GRAFICE — HTML/CSS pur, zero dependențe externe
# ─────────────────────────────────────────────────────────────────────────────

def _graf_vanzari_html(vanzari_df: pd.DataFrame, retetar_df: pd.DataFrame) -> str | None:
    """Bar chart vânzări 7 zile — HTML/CSS pur."""
    if vanzari_df.empty or retetar_df.empty:
        return None
    pret_idx = {str(r["Preparat"]).lower().strip(): _f(r["Pret_Vanzare"])
                for _, r in retetar_df.iterrows()}
    df = vanzari_df.copy()
    df["Data_dt"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Valoare"] = df.apply(
        lambda r: _f(r["Cantitate_Vanduta"]) * pret_idx.get(str(r["Preparat"]).lower().strip(), 0), axis=1)
    zilnic = (df.groupby(df["Data_dt"].dt.date)["Valoare"]
              .sum().reset_index().sort_values("Data_dt").tail(7))
    if zilnic.empty:
        return None
    max_val = max(zilnic["Valoare"].max(), 1)
    bars = ""
    for _, row in zilnic.iterrows():
        pct   = row["Valoare"] / max_val * 100
        label = row["Data_dt"].strftime("%d %b") if hasattr(row["Data_dt"], "strftime") else str(row["Data_dt"])
        bars += f"""
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.55rem;">
            <div style="font-size:0.72rem;color:{MUTED};width:42px;text-align:right;flex-shrink:0;">{label}</div>
            <div style="flex:1;background:#F3F4F6;border-radius:4px;height:22px;overflow:hidden;">
                <div style="width:{pct:.1f}%;background:{P};height:100%;border-radius:4px;
                    display:flex;align-items:center;padding-left:8px;transition:width 0.6s ease;">
                    <span style="font-size:0.7rem;font-weight:600;color:#fff;white-space:nowrap;">
                        {row['Valoare']:,.0f} RON
                    </span>
                </div>
            </div>
        </div>"""
    return f"""
    <div class="card fade-in" style="padding:1.4rem 1.6rem;">
        <div class="eyebrow" style="margin-bottom:1rem;">Vânzări brute · ultimele 7 zile</div>
        {bars}
    </div>"""

def _graf_top_preparate_html(vanzari_df: pd.DataFrame) -> str | None:
    """Bar chart orizontal top preparate — HTML/CSS pur."""
    if vanzari_df.empty:
        return None
    top = (vanzari_df.groupby("Preparat")["Cantitate_Vanduta"]
           .apply(lambda x: sum(_f(v) for v in x))
           .reset_index()
           .sort_values("Cantitate_Vanduta", ascending=False)
           .head(7))
    if top.empty:
        return None
    max_val = max(top["Cantitate_Vanduta"].max(), 1)
    bars = ""
    for _, row in top.iterrows():
        pct  = row["Cantitate_Vanduta"] / max_val * 100
        name = str(row["Preparat"])[:28]
        bars += f"""
        <div style="margin-bottom:0.55rem;">
            <div style="display:flex;justify-content:space-between;font-size:0.78rem;margin-bottom:3px;">
                <span style="color:{TEXT};font-weight:500;">{name}</span>
                <span style="color:{MUTED};">{row['Cantitate_Vanduta']:.0f} buc</span>
            </div>
            <div style="background:#F3F4F6;border-radius:4px;height:10px;overflow:hidden;">
                <div style="width:{pct:.1f}%;background:{P_MID};border-left:3px solid {P};height:100%;border-radius:4px;"></div>
            </div>
        </div>"""
    return f"""
    <div class="card fade-in" style="padding:1.4rem 1.6rem;">
        <div class="eyebrow" style="margin-bottom:1rem;">Top preparate vândute</div>
        {bars}
    </div>"""

def _graf_cheltuieli_html(c: dict) -> str | None:
    """Mini donut chart cheltuieli — HTML/CSS pur (segmente colorate)."""
    total = c["vanzari_brute"]
    if total <= 0:
        return None
    segmente = [
        ("Food Cost",        max(c["food_cost"], 0),                                              AMBER),
        ("Cheltuieli fixe",  max(c["cheltuieli_fixe_zilnice"], 0),                                BLUE),
        ("Taxe",             max(c["impozit_firma"] + c["impozit_dividend"] + c["tva_colectat"], 0), RED),
        ("Profit net",       max(c["profit_net_real"], 0),                                        GREEN),
    ]
    randuri = ""
    for label, val, color in segmente:
        pct = val / total * 100
        randuri += f"""
        <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;">
            <div style="width:10px;height:10px;border-radius:2px;background:{color};flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;font-size:0.8rem;margin-bottom:2px;">
                    <span style="color:{MUTED};">{label}</span>
                    <span style="color:{TEXT};font-weight:600;">{val:,.2f} RON <span style="color:{FAINT};font-weight:400;">({pct:.1f}%)</span></span>
                </div>
                <div style="background:#F3F4F6;border-radius:4px;height:8px;overflow:hidden;">
                    <div style="width:{pct:.1f}%;background:{color};height:100%;border-radius:4px;opacity:0.8;"></div>
                </div>
            </div>
        </div>"""
    return f"""
    <div class="card fade-in" style="padding:1.4rem 1.6rem;">
        <div class="eyebrow" style="margin-bottom:1rem;">Structura cheltuielilor · azi</div>
        {randuri}
        <div style="border-top:1px solid {BORD};margin-top:0.75rem;padding-top:0.75rem;
            display:flex;justify-content:space-between;font-size:0.82rem;">
            <span style="color:{MUTED};">Total încasări brute</span>
            <span style="font-weight:700;color:{P};">{total:,.2f} RON</span>
        </div>
    </div>"""

# ─────────────────────────────────────────────────────────────────────────────
# TABS PRINCIPALE
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
    st.markdown('<p class="eyebrow">Situație financiară</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Date live din Google Sheets · actualizate la fiecare încărcare</p>', unsafe_allow_html=True)

    cfg        = citeste_config()
    stoc_df    = citeste_stoc()
    vanzari_df = citeste_vanzari()
    retetar_df = citeste_retetar()

    azi   = date.today().isoformat()
    v_azi = vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)] if not vanzari_df.empty else pd.DataFrame(columns=["Preparat", "Cantitate_Vanduta", "Data"])

    # Vânzări brute azi
    vb = 0.0
    if not v_azi.empty and not retetar_df.empty:
        pret_idx = {str(r["Preparat"]).lower().strip(): _f(r["Pret_Vanzare"]) for _, r in retetar_df.iterrows()}
        for _, row in v_azi.iterrows():
            vb += _f(row["Cantitate_Vanduta"]) * pret_idx.get(str(row["Preparat"]).lower().strip(), 0)

    fc_zi = calculeaza_food_cost(v_azi, retetar_df, stoc_df)
    c     = cascada(vb, fc_zi, cfg)

    # Alerte stoc
    stoc_alerte = []
    if not stoc_df.empty:
        for _, row in stoc_df.iterrows():
            if _f(row.get("Stoc_Minim", 0)) > 0 and _f(row.get("Cantitate", 0)) <= _f(row.get("Stoc_Minim", 0)):
                stoc_alerte.append(str(row.get("Produs", "")))

    if stoc_alerte:
        st.markdown(f"""
        <div class="card fade-in" style="border-color:#FDE68A;background:#FFFBEB;">
            <div style="font-size:0.85rem;font-weight:600;color:{AMBER};">
                ⚠ Stoc scăzut · {len(stoc_alerte)} produse sub limita minimă
            </div>
            <div style="font-size:0.82rem;color:{MUTED};margin-top:4px;">
                {', '.join(stoc_alerte[:8])}{'…' if len(stoc_alerte) > 8 else ''}
            </div>
        </div>""", unsafe_allow_html=True)

    # ── Metrici ──
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        tip = "green" if c["profit_net_real"] >= 0 else "red"
        card_metric("Profit Net · Bani în mână", f"{c['profit_net_real']:,.2f} RON",
                    sub=f"azi · {azi}", badge=f"Marjă {c['marja_neta']:.1f}%", tip=tip)
    with col2:
        fc_pct = (c["food_cost"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] > 0 else 0
        card_metric("Food Cost", f"{c['food_cost']:,.2f} RON",
                    sub=f"{fc_pct:.1f}% din vânzări nete", tip="amber")
    with col3:
        card_metric("Vânzări Brute · Azi", f"{c['vanzari_brute']:,.2f} RON",
                    sub="inclusiv TVA", tip="blue")
    with col4:
        nr_stoc = len(stoc_df) if not stoc_df.empty else 0
        card_metric("Produse în Stoc", str(nr_stoc),
                    sub=f"{len(stoc_alerte)} sub limită" if stoc_alerte else "Stoc OK",
                    badge="⚠ Alertă" if stoc_alerte else "✓ OK",
                    tip="amber" if stoc_alerte else "green")

    st.markdown("<div style='height:1.25rem;'></div>", unsafe_allow_html=True)

    # ── Grafice ──
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        html_vz = _graf_vanzari_html(vanzari_df, retetar_df)
        if html_vz:
            st.markdown(html_vz, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card" style="text-align:center;padding:2rem;color:{MUTED};font-size:0.88rem;">📈 Date insuficiente pentru grafic vânzări</div>', unsafe_allow_html=True)

    with col_g2:
        html_ch = _graf_cheltuieli_html(c)
        if html_ch and c["vanzari_brute"] > 0:
            st.markdown(html_ch, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card" style="text-align:center;padding:2rem;color:{MUTED};font-size:0.88rem;">🥧 Fără vânzări azi — nu există date pentru grafic</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Cascadă + Top preparate ──
    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.markdown('<div class="card fade-in">', unsafe_allow_html=True)
        st.markdown(f'<div class="eyebrow" style="margin-bottom:0.75rem;">Cascadă financiară · azi</div>', unsafe_allow_html=True)
        casc_row("Încasări brute (cu TVA)",    c["vanzari_brute"],           plus=True)
        casc_row("TVA colectat (→ ANAF)",       c["tva_colectat"])
        casc_row("Food Cost ingrediente",       c["food_cost"])
        casc_row("Cheltuieli fixe zilnice",      c["cheltuieli_fixe_zilnice"])
        st.markdown(f"""
        <div class="casc-row">
            <span class="casc-lbl" style="font-weight:700;color:{TEXT};">Profit brut operațional</span>
            <span class="casc-val" style="color:{P};font-weight:700;">{c['profit_brut']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        casc_row("Impozit firmă",      c["impozit_firma"])
        casc_row("Impozit dividende",  c["impozit_dividend"])
        nc = GREEN if c["profit_net_real"] >= 0 else RED
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.9rem 0 0.2rem;">
            <span style="font-size:0.95rem;font-weight:700;color:{TEXT};">✦ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:800;color:{nc};">{c['profit_net_real']:,.2f} RON</span>
        </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_r:
        html_top = _graf_top_preparate_html(vanzari_df)
        if html_top:
            st.markdown(html_top, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="card" style="text-align:center;padding:2rem;color:{MUTED};font-size:0.88rem;">📊 Nicio vânzare înregistrată încă</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 2 — STOC
# ═════════════════════════════════════════════════════════════════════════════
with tab_stoc:
    st.markdown('<p class="eyebrow">Gestiune inventar</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Stoc</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Adaugă produse manual sau prin scanare facturi. Stocul se scade automat din Raportul Z.</p>', unsafe_allow_html=True)

    stoc_df = citeste_stoc()

    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s2:
        if st.button("➕ Adaugă produs", type="primary", use_container_width=True):
            st.session_state["show_add_stoc"] = not st.session_state.get("show_add_stoc", False)
    with col_s3:
        if st.button("🔄 Reîncarcă", use_container_width=True):
            st.rerun()

    if st.session_state.get("show_add_stoc", False):
        with st.container():
            st.markdown(f"""
            <div class="card fade-in" style="border-color:{P_MID};background:#FAFAFF;">
                <div class="eyebrow" style="margin-bottom:0.75rem;">➕ Adaugă / Actualizează produs</div>
            </div>""", unsafe_allow_html=True)
            ca, cb, cc, cd, ce = st.columns([2.5, 1, 1, 1, 1])
            with ca: nm = st.text_input("Produs *", key="snm", placeholder="ex: Făină albă")
            with cb: qm = st.number_input("Cantitate", min_value=0.0, step=0.1, key="sqm")
            with cc: um = st.selectbox("UM", UNITATI, key="sum")
            with cd: pm = st.number_input("Preț/UM (RON)", min_value=0.0, step=0.01, key="spm")
            with ce: sm = st.number_input("Stoc minim", min_value=0.0, step=0.1, key="ssm")
            c1, c2, _ = st.columns([1.2, 1, 3])
            with c1:
                if st.button("💾 Salvează", type="primary", key="sbtn_save"):
                    if nm.strip():
                        adauga_in_stoc([{"Produs": nm.strip(), "Cantitate": qm, "Unitate": um,
                                         "Pret_Unitar": pm, "Data": date.today().isoformat(), "Stoc_Minim": sm}])
                        st.success(f"✓ '{nm}' salvat în stoc.")
                        st.session_state["show_add_stoc"] = False
                        st.rerun()
                    else:
                        st.warning("Completează numele produsului.")
            with c2:
                if st.button("Anulează", key="sbtn_cancel"):
                    st.session_state["show_add_stoc"] = False
                    st.rerun()

    if stoc_df.empty:
        st.markdown(f"""
        <div class="card" style="text-align:center;padding:3rem;">
            <div style="font-size:2.5rem;margin-bottom:0.8rem;">📦</div>
            <div style="font-size:1rem;font-weight:600;color:{TEXT};">Stocul este gol</div>
            <div style="font-size:0.85rem;color:{MUTED};margin-top:6px;">
                Apasă <strong>➕ Adaugă produs</strong> sau scanează o factură.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # Alerte
        alerte_rows = []
        ok_rows     = []
        for _, row in stoc_df.iterrows():
            cant = _f(row.get("Cantitate", 0))
            minim = _f(row.get("Stoc_Minim", 0))
            if minim > 0 and cant <= minim:
                alerte_rows.append(row)
            else:
                ok_rows.append(row)

        if alerte_rows:
            st.markdown(f'<div class="eyebrow" style="margin-bottom:0.5rem;color:{RED};">⚠ Sub limita minimă ({len(alerte_rows)})</div>', unsafe_allow_html=True)
            for row in alerte_rows:
                cant  = _f(row.get("Cantitate", 0))
                minim = _f(row.get("Stoc_Minim", 0))
                pct   = min(int(cant / minim * 100), 100) if minim > 0 else 0
                st.markdown(f"""
                <div class="card-sm fade-in" style="border-color:#FDE68A;margin-bottom:0.5rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;color:{TEXT};">{row.get('Produs','')}</span>
                        <span class="badge b-amber">{cant:.2f} {row.get('Unitate','')}</span>
                    </div>
                    <div class="stoc-bar-wrap">
                        <div class="stoc-bar-fill" style="width:{pct}%;background:{RED};"></div>
                    </div>
                    <div style="font-size:0.72rem;color:{FAINT};margin-top:3px;">
                        {pct}% din minimul de {minim:.2f} · Preț: {_f(row.get('Pret_Unitar',0)):.2f} RON/{row.get('Unitate','')}
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown(f'<div class="eyebrow" style="margin:1rem 0 0.5rem;">Toate produsele ({len(stoc_df)})</div>', unsafe_allow_html=True)
        st.dataframe(
            stoc_df.rename(columns={"Produs": "Produs", "Cantitate": "Cant.", "Unitate": "UM",
                                    "Pret_Unitar": "Preț/UM", "Data": "Actualizat", "Stoc_Minim": "Minim"}),
            use_container_width=True, hide_index=True,
        )

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 3 — SCANARE FACTURI
# ═════════════════════════════════════════════════════════════════════════════
with tab_facturi:
    st.markdown('<p class="eyebrow">Procesare automată · Gemini Vision</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Scanare Facturi</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Fotografiază factura → produsele sunt extrase automat → se adaugă în stoc.</p>', unsafe_allow_html=True)

    if "produse_factura" not in st.session_state:
        st.session_state.produse_factura = []
    if "meta_factura" not in st.session_state:
        st.session_state.meta_factura = {}

    uploaded = st.file_uploader("Imagine factură (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="fact_upload")

    if uploaded:
        img_bytes = uploaded.read()
        try:
            img_pil = Image.open(io.BytesIO(img_bytes))
        except Exception:
            st.error("Fișierul nu este o imagine validă.")
            img_pil = None

        if img_pil:
            col_img, col_act = st.columns([1, 2])
            with col_img:
                st.image(img_pil, use_container_width=True, caption="Factură")
            with col_act:
                st.markdown(f"""
                <div class="card-sm fade-in">
                    <div class="eyebrow">Extragere automată · Gemini Vision</div>
                    <p style="font-size:0.88rem;color:{MUTED};margin:0.5rem 0 1rem;">
                        AI-ul identifică furnizorul, numărul facturii, produsele, cantitățile și prețurile unitare.
                    </p>
                </div>""", unsafe_allow_html=True)
                if st.button("🔍 Extrage date din factură", type="primary", key="btn_extrage"):
                    with st.spinner("Gemini analizează factura…"):
                        rez = extrage_factura(img_bytes)
                    if rez and "produse" in rez:
                        st.session_state.produse_factura = rez["produse"]
                        st.session_state.meta_factura = {
                            "furnizor":   rez.get("furnizor", ""),
                            "nr_factura": rez.get("nr_factura", ""),
                            "data":       rez.get("data", date.today().isoformat()),
                            "total":      _f(rez.get("total", 0)),
                        }
                        st.success(f"✓ {len(rez['produse'])} produse identificate.")
                    else:
                        st.session_state.produse_factura = []

    if st.session_state.meta_factura:
        meta = st.session_state.meta_factura
        st.markdown(f"""
        <div class="card fade-in" style="margin-top:1rem;">
            <div class="eyebrow" style="margin-bottom:0.5rem;">Date factură</div>
            <div style="display:flex;gap:2rem;flex-wrap:wrap;font-size:0.88rem;">
                <div><span style="color:{MUTED};">Furnizor: </span><strong>{meta.get('furnizor','—')}</strong></div>
                <div><span style="color:{MUTED};">Nr.: </span><strong>{meta.get('nr_factura','—')}</strong></div>
                <div><span style="color:{MUTED};">Data: </span><strong>{meta.get('data','—')}</strong></div>
                <div><span style="color:{MUTED};">Total: </span><strong style="color:{P};">{meta.get('total',0):.2f} RON</strong></div>
            </div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.produse_factura:
        st.markdown(f'<div class="eyebrow" style="margin:1.25rem 0 0.75rem;">Produse detectate — verifică și corectează</div>', unsafe_allow_html=True)
        produse_editabile = []
        for i, prod in enumerate(st.session_state.produse_factura):
            ca, cb, cc, cd = st.columns([2.5, 1, 1, 1])
            with ca: nm = st.text_input("Produs", value=str(prod.get("produs", "")), key=f"fnm_{i}")
            with cb: qt = st.number_input("Cantitate", value=_f(prod.get("cantitate", 0)), min_value=0.0, step=0.1, key=f"fqt_{i}")
            with cc:
                um_val = str(prod.get("unitate", "kg")).lower()
                um_idx = UNITATI.index(um_val) if um_val in UNITATI else 0
                um = st.selectbox("UM", UNITATI, index=um_idx, key=f"fum_{i}")
            with cd: pr = st.number_input("Preț/UM", value=_f(prod.get("pret_unitar", 0)), min_value=0.0, step=0.01, key=f"fpr_{i}")
            if nm.strip():
                produse_editabile.append({"Produs": nm.strip(), "Cantitate": qt, "Unitate": um, "Pret_Unitar": pr,
                                          "Data": st.session_state.meta_factura.get("data", date.today().isoformat())})

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if produse_editabile and st.button("💾 Adaugă în Stoc →", type="primary", key="btn_fact_save"):
            adauga_in_stoc(produse_editabile)
            salveaza_factura_log(
                st.session_state.meta_factura.get("data", date.today().isoformat()),
                st.session_state.meta_factura.get("furnizor", ""),
                st.session_state.meta_factura.get("nr_factura", ""),
                st.session_state.meta_factura.get("total", 0),
                json.dumps(produse_editabile, ensure_ascii=False),
            )
            st.success(f"✓ {len(produse_editabile)} produse adăugate în stoc.")
            st.session_state.produse_factura = []
            st.session_state.meta_factura    = {}
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 4 — RAPORT Z
# ═════════════════════════════════════════════════════════════════════════════
with tab_z:
    st.markdown('<p class="eyebrow">Vânzări zilnice · scădere stoc automată</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Raport Z</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Scanează Raportul Z → preparatele vândute se cuplează cu rețetarul → stocul se scade automat.</p>', unsafe_allow_html=True)

    retetar_df_z = citeste_retetar()
    preparate_z  = sorted(retetar_df_z["Preparat"].dropna().unique().tolist()) if not retetar_df_z.empty else []

    if "z_rezultate" not in st.session_state:
        st.session_state.z_rezultate = []
    if "z_subtab" not in st.session_state:
        st.session_state.z_subtab = "scanare"

    c1, c2, _ = st.columns([1.2, 1.2, 5])
    with c1:
        if st.button("📷 Scanare", type="primary" if st.session_state.z_subtab == "scanare" else "secondary", key="z_btn_scan"):
            st.session_state.z_subtab = "scanare"; st.rerun()
    with c2:
        if st.button("✏️ Manual", type="primary" if st.session_state.z_subtab == "manual" else "secondary", key="z_btn_manual"):
            st.session_state.z_subtab = "manual"; st.rerun()

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    # ── SCANARE ──
    if st.session_state.z_subtab == "scanare":
        uploaded_z = st.file_uploader("Imagine Raport Z / Bon (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"], key="z_upload")

        if uploaded_z:
            img_bytes_z = uploaded_z.read()
            try:   img_z = Image.open(io.BytesIO(img_bytes_z))
            except: img_z = None; st.error("Fișier invalid.")

            if img_z:
                ci, ca = st.columns([1, 2])
                with ci: st.image(img_z, use_container_width=True, caption="Raport Z")
                with ca:
                    st.markdown(f'<div class="card-sm"><div class="eyebrow">Recunoaștere text · Gemini Vision</div></div>', unsafe_allow_html=True)
                    if st.button("🔍 Scanează Raportul Z", type="primary", key="btn_scan_z"):
                        if not preparate_z:
                            st.warning("Rețetarul este gol. Adaugă preparate mai întâi.")
                        else:
                            with st.spinner("Gemini analizează raportul…"):
                                rez_z = extrage_raport_z(img_bytes_z)
                            if rez_z and "vanzari" in rez_z:
                                rezultate = []
                                for item in rez_z["vanzari"]:
                                    ai_name = str(item.get("produs", "")).strip()
                                    ai_cant = _f(item.get("cantitate", 0))
                                    matched, score = fuzzy_match(ai_name, preparate_z)
                                    rezultate.append({"ai_name": ai_name, "preparat": matched or "",
                                                      "cant": ai_cant, "score": score, "matched": matched is not None})
                                st.session_state.z_rezultate = rezultate
                                st.success(f"✓ {len(rezultate)} preparate detectate.")
                            else:
                                st.session_state.z_rezultate = []

    # ── MANUAL ──
    else:
        if not preparate_z:
            st.warning("Rețetarul este gol. Adaugă preparate în tab-ul Rețetar înainte.")
        else:
            st.markdown(f'<div class="eyebrow" style="margin-bottom:0.75rem;">Introduci manual vânzările zilei</div>', unsafe_allow_html=True)
            nr_prep = st.number_input("Câte preparate diferite ai vândut?", min_value=1, max_value=30, value=3, step=1)
            rezultate_manual = []
            for i in range(int(nr_prep)):
                ca, cb = st.columns([2.5, 1])
                with ca:
                    prep = st.selectbox("Preparat", ["— alege —"] + preparate_z, key=f"mp_{i}")
                with cb:
                    cant = st.number_input("Cantitate", min_value=0.0, step=1.0, key=f"mc_{i}")
                if prep and prep != "— alege —" and cant > 0:
                    rezultate_manual.append({"ai_name": prep, "preparat": prep, "cant": cant, "score": 1.0, "matched": True})
            if rezultate_manual and st.button("Folosește aceste vânzări →", type="primary", key="z_manual_set"):
                st.session_state.z_rezultate = rezultate_manual
                st.rerun()

    # ── CONFIRMARE + SALVARE ──
    if st.session_state.z_rezultate:
        st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card fade-in">
            <div class="eyebrow" style="margin-bottom:0.5rem;">Confirmă și corectează</div>
            <p style="font-size:0.85rem;color:{MUTED};margin:0 0 1rem;">
                Verifică preparatele cuplare automat. Ajustează dacă e nevoie, apoi salvează.
            </p>
        </div>""", unsafe_allow_html=True)

        vanzari_confirmate = []
        for i, row in enumerate(st.session_state.z_rezultate):
            ca, cb, cc = st.columns([2, 2, 1])
            with ca:
                badge = (f'<span style="background:#D1FAE5;color:{GREEN};padding:2px 8px;border-radius:6px;font-size:0.72rem;font-weight:700;">✓ {row["score"]*100:.0f}%</span>'
                         if row["matched"] else f'<span style="background:#FEE2E2;color:{RED};padding:2px 8px;border-radius:6px;font-size:0.72rem;font-weight:700;">⚠ Necuplat</span>')
                st.markdown(f'<div style="padding-top:1.6rem;font-size:0.78rem;color:{FAINT};">Detectat: {row["ai_name"]} &nbsp;{badge}</div>', unsafe_allow_html=True)
            with cb:
                opts    = ["— alege —"] + preparate_z
                def_idx = opts.index(row["preparat"]) if row["preparat"] in opts else 0
                sel_p   = st.selectbox("Preparat", opts, index=def_idx, key=f"zp_{i}")
            with cc:
                sel_c = st.number_input("Cant.", value=float(row["cant"]), min_value=0.0, step=1.0, key=f"zc_{i}")
            if sel_p and sel_p != "— alege —" and sel_c > 0:
                vanzari_confirmate.append({"Preparat": sel_p, "Cantitate_Vanduta": sel_c, "Data": date.today().isoformat()})

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        data_z = st.date_input("Data raportului", value=date.today(), key="z_date")

        if vanzari_confirmate and st.button("💾 Salvează Vânzările + Scade Stoc →", type="primary", key="z_save"):
            stoc_nou, scazut = scade_stoc([{"Preparat": v["Preparat"], "Cantitate_Vanduta": v["Cantitate_Vanduta"]}
                                            for v in vanzari_confirmate], retetar_df_z)
            salveaza_stoc(stoc_nou)
            vz_cu_data = [{**v, "Data": str(data_z)} for v in vanzari_confirmate]
            salveaza_vanzari(vz_cu_data)
            st.success(f"✓ {len(vanzari_confirmate)} vânzări salvate. {len(scazut)} ingrediente scăzute din stoc.")
            if scazut:
                for item in scazut:
                    cls = RED if item["minim"] > 0 and item["dupa"] <= item["minim"] else GREEN
                    st.markdown(f'<div style="font-size:0.82rem;padding:2px 0;color:{cls};">— {item["ingredient"]}: {item["scazut"]:.3f} kg scăzut → rămân {item["dupa"]:.3f}</div>', unsafe_allow_html=True)
            st.session_state.z_rezultate = []
            st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 5 — REȚETAR & FOOD COST
# ═════════════════════════════════════════════════════════════════════════════
with tab_retetar:
    st.markdown('<p class="eyebrow">Rețete & profitabilitate</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Rețetar & Food Cost</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Definește rețetele preparatelor. Food cost-ul se calculează automat din prețurile din stoc.</p>', unsafe_allow_html=True)

    retetar_df = citeste_retetar()
    stoc_df_r  = citeste_stoc()

    # Adaugă rând în rețetar
    st.markdown(f'<div class="eyebrow" style="margin-bottom:0.5rem;">Adaugă rând în rețetar</div>', unsafe_allow_html=True)
    produse_stoc = sorted(stoc_df_r["Produs"].dropna().unique().tolist()) if not stoc_df_r.empty else []

    ca, cb, cc, cd = st.columns([2, 2, 1, 1])
    with ca: prep_nou = st.text_input("Preparat", key="rnm", placeholder="ex: Burger Clasic")
    with cb:
        if produse_stoc:
            ing_nou = st.selectbox("Ingredient", ["— alege —"] + produse_stoc, key="ring")
        else:
            ing_nou = st.text_input("Ingredient", key="ring", placeholder="ex: Carne vită")
    with cc: gram_nou = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key="rgram")
    with cd: pret_vz  = st.number_input("Preț vânzare (RON)", min_value=0.0, step=0.5, key="rpret")

    if st.button("➕ Adaugă rând", type="primary", key="r_add"):
        ing_val = ing_nou if not isinstance(ing_nou, str) or ing_nou != "— alege —" else ""
        if prep_nou.strip() and ing_val and str(ing_val) != "— alege —" and gram_nou > 0:
            new_r = pd.DataFrame([{"Preparat": prep_nou.strip(), "Ingredient": str(ing_val),
                                    "Gramaj": gram_nou, "Pret_Vanzare": pret_vz}])
            retetar_df = pd.concat([retetar_df, new_r], ignore_index=True)
            salveaza_retetar(retetar_df)
            st.success(f"✓ Rând adăugat: {prep_nou} ← {ing_val} {gram_nou}g")
            st.rerun()
        else:
            st.warning("Completează: preparat, ingredient și gramaj.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if retetar_df.empty:
        st.markdown(f'<div class="card" style="text-align:center;padding:2.5rem;"><div style="font-size:2rem;">📋</div><div style="color:{MUTED};font-size:0.9rem;margin-top:0.5rem;">Rețetarul este gol. Adaugă primul preparat.</div></div>', unsafe_allow_html=True)
    else:
        # Food cost per preparat
        stoc_idx = {str(r.get("Produs", "")).lower().strip(): _f(r.get("Pret_Unitar", 0))
                    for _, r in stoc_df_r.iterrows()} if not stoc_df_r.empty else {}

        preparate_unice = sorted(retetar_df["Preparat"].dropna().unique().tolist())
        st.markdown(f'<div class="eyebrow" style="margin-bottom:0.75rem;">Food Cost per preparat</div>', unsafe_allow_html=True)

        for prep in preparate_unice:
            ings     = retetar_df[retetar_df["Preparat"].astype(str).str.strip() == prep]
            fc_prep  = sum(_f(r["Gramaj"]) / 1000.0 * stoc_idx.get(str(r["Ingredient"]).lower().strip(), 0)
                          for _, r in ings.iterrows())
            pret_vz_p = _f(ings.iloc[0].get("Pret_Vanzare", 0)) if not ings.empty else 0
            pret_fara_tva = pret_vz_p / 1.09
            marja = ((pret_fara_tva - fc_prep) / pret_fara_tva * 100) if pret_fara_tva > 0 else 0
            m_color = GREEN if marja >= 30 else (AMBER if marja >= 15 else RED)

            with st.expander(f"**{prep}** · FC: {fc_prep:.2f} RON · Preț: {pret_vz_p:.2f} RON · Marjă: {marja:.1f}%"):
                st.dataframe(ings[["Ingredient", "Gramaj"]].rename(columns={"Gramaj": "Gramaj (g)"}),
                             use_container_width=True, hide_index=True)
                st.markdown(f"""
                <div style="display:flex;gap:1.5rem;margin-top:0.5rem;font-size:0.86rem;flex-wrap:wrap;">
                    <div><span style="color:{MUTED};">Food cost: </span><strong>{fc_prep:.2f} RON</strong></div>
                    <div><span style="color:{MUTED};">Preț vânzare: </span><strong>{pret_vz_p:.2f} RON</strong></div>
                    <div><span style="color:{MUTED};">Marjă brută: </span><strong style="color:{m_color};">{marja:.1f}%</strong></div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"🗑 Șterge toate rândurile pentru {prep}", key=f"del_{prep}"):
                    retetar_df = retetar_df[retetar_df["Preparat"].astype(str).str.strip() != prep]
                    salveaza_retetar(retetar_df)
                    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 6 — SETĂRI
# ═════════════════════════════════════════════════════════════════════════════
with tab_setari:
    st.markdown('<p class="eyebrow">Configurare</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Setări</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Configurează regimul fiscal, cheltuielile fixe și parametrii financiari.</p>', unsafe_allow_html=True)

    cfg_s = citeste_config()

    st.markdown(f'<div class="eyebrow" style="margin-bottom:0.5rem;">Fiscal</div>', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3)

    regim_opts = {"Microîntreprindere 1%": "micro1", "Microîntreprindere 3%": "micro3", "Impozit profit 16%": "profit16"}
    regim_rev  = {v: k for k, v in regim_opts.items()}
    regim_cur  = regim_rev.get(str(cfg_s.get("regim_fiscal", "micro1")), "Microîntreprindere 1%")
    with col_f1:
        regim_sel = st.selectbox("Regim fiscal", list(regim_opts.keys()), index=list(regim_opts.keys()).index(regim_cur))

    tva_opts  = {"TVA 9% (restaurante)": 0.09, "TVA 19% (standard)": 0.19, "Neplătitor TVA": 0.0}
    tva_rev   = {v: k for k, v in tva_opts.items()}
    tva_cur   = tva_rev.get(round(_f(cfg_s.get("cota_tva", 0.09)), 2), "TVA 9% (restaurante)")
    with col_f2:
        tva_sel = st.selectbox("Cotă TVA", list(tva_opts.keys()), index=list(tva_opts.keys()).index(tva_cur))

    div_opts  = {"8% (standard)": 0.08, "5% (reinvestire profit)": 0.05, "0%": 0.0}
    div_rev   = {v: k for k, v in div_opts.items()}
    div_cur   = div_rev.get(round(_f(cfg_s.get("cota_dividend", 0.08)), 2), "8% (standard)")
    with col_f3:
        div_sel = st.selectbox("Impozit dividende", list(div_opts.keys()), index=list(div_opts.keys()).index(div_cur))

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    st.markdown(f'<div class="eyebrow" style="margin-bottom:0.5rem;">Cheltuieli fixe lunare</div>', unsafe_allow_html=True)
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1: chirie    = st.number_input("Chirie (RON)", value=_f(cfg_s.get("chirie_lunara", 0)), min_value=0.0, step=100.0)
    with col_c2: salarii   = st.number_input("Salarii (RON)", value=_f(cfg_s.get("salarii_lunare", 0)), min_value=0.0, step=100.0)
    with col_c3: utilitati = st.number_input("Utilități (RON)", value=_f(cfg_s.get("utilitati_lunare", 0)), min_value=0.0, step=50.0)
    with col_c4: nr_clienti = st.number_input("Clienți/lună (estimat)", value=int(_f(cfg_s.get("nr_clienti_lunar", 500))), min_value=1, step=10)

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
    if st.button("💾 Salvează Configurația", type="primary"):
        salveaza_config({
            "regim_fiscal":     regim_opts[regim_sel],
            "cota_tva":         tva_opts[tva_sel],
            "cota_dividend":    div_opts[div_sel],
            "chirie_lunara":    chirie,
            "salarii_lunare":   salarii,
            "utilitati_lunare": utilitati,
            "nr_clienti_lunar": nr_clienti,
        })
        st.success("✓ Configurația a fost salvată.")

# ═════════════════════════════════════════════════════════════════════════════
#  TAB 7 — SIMULATOR PREPARAT
# ═════════════════════════════════════════════════════════════════════════════
with tab_sim:
    st.markdown('<p class="eyebrow">Analiză profitabilitate</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Simulator Preparat</h1>', unsafe_allow_html=True)
    st.markdown('<p class="page-sub">Testează profitabilitatea unui preparat nou înainte de a-l introduce în meniu.</p>', unsafe_allow_html=True)

    cfg_sim  = citeste_config()
    stoc_sim = citeste_stoc()
    produse_s = sorted(stoc_sim["Produs"].dropna().unique().tolist()) if not stoc_sim.empty else []

    col_s1, col_s2 = st.columns(2)
    with col_s1: nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger Clasic")
    with col_s2: pret_vz   = st.number_input("Preț vânzare (cu TVA) · RON", min_value=0.0, step=0.5, format="%.2f")

    st.markdown(f'<div class="eyebrow" style="margin-top:0.25rem;margin-bottom:0.4rem;">Ajustare rapidă preț</div>', unsafe_allow_html=True)
    sl_min     = max(1.0, pret_vz - 20) if pret_vz > 0 else 1.0
    sl_max     = pret_vz + 40 if pret_vz > 0 else 100.0
    sl_default = float(pret_vz) if pret_vz > 0 else 20.0
    pret_slider = st.slider("Preț", min_value=sl_min, max_value=sl_max, value=sl_default,
                             step=0.5, label_visibility="collapsed")
    pret_calc = pret_vz if pret_vz > 0 else pret_slider
    st.markdown(f"""
    <div style="font-size:0.82rem;color:{MUTED};margin-bottom:1rem;">
        Preț activ: <strong style="color:{P};font-size:1rem;">{pret_calc:.2f} RON</strong>
        &nbsp;·&nbsp; <span style="color:{FAINT};">{'tastat' if pret_vz > 0 else 'din slider'}</span>
    </div>""", unsafe_allow_html=True)

    nr_ing = st.number_input("Nr. ingrediente", min_value=1, max_value=20, value=3, step=1)
    st.markdown(f'<div class="eyebrow" style="margin-bottom:0.75rem;">Ingrediente & Gramaje</div>', unsafe_allow_html=True)

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
        if ing and str(ing) != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": str(ing), "gramaj_g": gram})

    if ingrediente_sim and pret_calc > 0:
        stoc_idx_sim = {str(r.get("Produs", "")).lower().strip(): _f(r.get("Pret_Unitar", 0))
                        for _, r in stoc_sim.iterrows()} if not stoc_sim.empty else {}
        fc_sim = sum((x["gramaj_g"] / 1000.0) * stoc_idx_sim.get(x["ingredient"].lower().strip(), 0.0)
                     for x in ingrediente_sim)

        nr_cl  = max(_f(cfg_sim.get("nr_clienti_lunar", 500)), 1)
        fixe   = _f(cfg_sim.get("chirie_lunara", 0)) + _f(cfg_sim.get("salarii_lunare", 0)) + _f(cfg_sim.get("utilitati_lunare", 0))
        regie  = fixe / nr_cl

        # Cascadă fără a dubla cheltuielile fixe (regie e deja inclusă în food_cost)
        cfg_fara_fixe = {**cfg_sim, "chirie_lunara": 0, "salarii_lunare": 0, "utilitati_lunare": 0}
        c_sim = cascada(pret_calc, fc_sim + regie, cfg_fara_fixe)
        c_sim["food_cost"]               = round(fc_sim, 2)
        c_sim["cheltuieli_fixe_zilnice"]  = round(regie, 2)

        col_bon, col_rec = st.columns([1, 1])
        with col_bon:
            bon_fiscal(c_sim, titlu=f"SIMULARE · {(nume_prep or 'PREPARAT').upper()}")

        with col_rec:
            marja = c_sim["marja_neta"]
            if marja < 10:
                cota_tva = _f(cfg_sim.get("cota_tva", 0.09))
                ci_s     = {"micro1": 0.01, "micro3": 0.03, "profit16": 0.16}.get(str(cfg_sim.get("regim_fiscal", "micro1")), 0.01)
                cd_s     = _f(cfg_sim.get("cota_dividend", 0.08))
                factor   = (1 - ci_s) * (1 - cd_s)
                pret_rec = (((fc_sim + regie) / (factor * 0.8)) * (1 + cota_tva) if factor > 0 else (fc_sim + regie) * 3)
                st.markdown(f"""
                <div class="card-sm fade-in" style="border-color:#FECACA;">
                    <div style="font-size:0.95rem;font-weight:700;color:{RED};margin-bottom:0.5rem;">⚠ Marjă insuficientă ({marja:.1f}%)</div>
                    <div style="font-size:0.85rem;color:{MUTED};line-height:1.7;">
                        Prețul este prea mic față de costuri. Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong style="color:{TEXT};">Preț recomandat (marjă 20%):</strong><br>
                        <span style="font-size:1.15rem;font-weight:800;color:{RED};">{pret_rec:.2f} RON</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            elif marja <= 20:
                st.markdown(f"""
                <div class="card-sm fade-in" style="border-color:#FDE68A;">
                    <div style="font-size:0.95rem;font-weight:700;color:{AMBER};margin-bottom:0.5rem;">ℹ Marjă acceptabilă ({marja:.1f}%)</div>
                    <div style="font-size:0.85rem;color:{MUTED};line-height:1.7;">
                        Preparatul este viabil, dar există loc de optimizare.<br>
                        Caută furnizori mai competitivi pentru ingredientele principale.
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="card-sm fade-in" style="border-color:#A7F3D0;">
                    <div style="font-size:0.95rem;font-weight:700;color:{GREEN};margin-bottom:0.5rem;">✓ Marjă excelentă ({marja:.1f}%)</div>
                    <div style="font-size:0.85rem;color:{MUTED};line-height:1.7;">
                        Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="card-sm fade-in" style="margin-top:0.75rem;">
                <div class="eyebrow" style="margin-bottom:0.75rem;">Detalii calcul</div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MUTED};">Food cost ingrediente</span>
                    <span style="font-weight:500;">{fc_sim:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MUTED};">Regie fixă / client</span>
                    <span style="font-weight:500;">{regie:.2f} RON</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.86rem;">
                    <span style="color:{MUTED};">Preț vânzare activ</span>
                    <span style="color:{P};font-weight:700;">{pret_calc:.2f} RON</span>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="card-sm" style="text-align:center;padding:2rem;border-style:dashed;">
            <div style="font-size:1.8rem;margin-bottom:0.5rem;">🧮</div>
            <div style="font-size:0.88rem;color:{MUTED};">Adaugă cel puțin un ingredient și setează un preț.</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:2.5rem 0 1.5rem;border-top:1px solid {BORD};margin-top:3rem;">
    <span style="font-size:0.8rem;color:{FAINT};">
        ✦ <strong style="color:{P};">MIA</strong> · Restaurant Intelligence · Gestiune inteligentă
    </span>
</div>""", unsafe_allow_html=True)
