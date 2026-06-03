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

# ─────────────────────────────────────────────
# CONSTANTE
# ─────────────────────────────────────────────
UNITATI_CUNOSCUTE = {
    "kg", "g", "l", "ml", "buc", "bucata", "bucăți",
    "bucati", "litri", "grame", "kilograme"
}
SHEETS_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Lana · ACQ Advisory",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], [class*="st-"] {
    font-family: 'Inter', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, header, footer, [data-testid="stToolbar"],
[data-testid="collapsedControl"] { display: none !important; }

/* App background */
.stApp { background-color: #0f1117 !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background-color: #16181f !important;
    border-right: 1px solid #2a2d3a !important;
}
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.25rem; }

/* Sidebar radio label (section header) */
[data-testid="stSidebar"] .stRadio > label {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    color: #4a4d5e !important;
    text-transform: uppercase !important;
    margin-bottom: 0.5rem !important;
}

/* Sidebar radio options */
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important;
    align-items: center !important;
    padding: 0.6rem 0.85rem !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    color: #c8cad8 !important;
    cursor: pointer !important;
    transition: background 0.15s ease, color 0.15s ease !important;
    margin-bottom: 2px !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #1e2130 !important;
    color: #ffffff !important;
}
[data-testid="stSidebar"] .stRadio > div [data-checked="true"] + label,
[data-testid="stSidebar"] .stRadio > div > label[data-testid*="checked"] {
    background: #1e2130 !important;
    color: #6c8eff !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #1e2130 !important;
    border: 1px solid #2e3245 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 0.85rem !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #6c8eff !important;
    box-shadow: 0 0 0 3px rgba(108,142,255,0.15) !important;
}
.stTextInput > div > div > input::placeholder { color: #4a4d5e !important; }

/* Selectbox */
.stSelectbox > div > div {
    background: #1e2130 !important;
    border: 1px solid #2e3245 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}
.stSelectbox > div > div > div { color: #e8eaf0 !important; }

/* Labels for inputs */
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stDateInput label, .stFileUploader label {
    color: #8a8d9e !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}

/* ── BUTTONS ── */
.stButton > button {
    border-radius: 8px !important;
    border: 1px solid #2e3245 !important;
    background: #1e2130 !important;
    color: #c8cad8 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: #252a3d !important;
    color: #ffffff !important;
    border-color: #6c8eff !important;
}
.stButton > button[kind="primary"] {
    background: #6c8eff !important;
    color: #ffffff !important;
    border-color: #6c8eff !important;
}
.stButton > button[kind="primary"]:hover {
    background: #5a7aee !important;
    border-color: #5a7aee !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1.5px dashed #2e3245 !important;
    border-radius: 12px !important;
    background: #1e2130 !important;
    padding: 1rem !important;
    color: #8a8d9e !important;
}

/* Date input */
.stDateInput > div > div > input {
    background: #1e2130 !important;
    border: 1px solid #2e3245 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}

/* Success / warning / error */
.stSuccess { background: #0d2818 !important; color: #4ade80 !important; border-radius: 8px !important; }
.stWarning { background: #2a1f00 !important; color: #fbbf24 !important; border-radius: 8px !important; }
.stError   { background: #2a0d0d !important; color: #f87171 !important; border-radius: 8px !important; }

/* Spinner */
.stSpinner > div { border-top-color: #6c8eff !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #16181f; }
::-webkit-scrollbar-thumb { background: #2e3245; border-radius: 3px; }

/* Number input stepper buttons */
.stNumberInput button {
    background: #1e2130 !important;
    border-color: #2e3245 !important;
    color: #8a8d9e !important;
}

/* Image caption */
.stImage > div > div { color: #4a4d5e !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# TOKEN GOOGLE — JWT RS256 pur Python, ZERO dependențe externe
# Folosește exclusiv stdlib: json, base64, hashlib, time, urllib
# ─────────────────────────────────────────────

def _parse_asn1_len(d, p):
    b = d[p]; p += 1
    if b < 0x80: return b, p
    n = b & 0x7f
    return int.from_bytes(d[p:p+n], 'big'), p + n

def _parse_asn1_int(d, p):
    assert d[p] == 0x02, f"ASN.1: așteptat INTEGER(0x02) la {p}, găsit 0x{d[p]:02x}"
    p += 1; ln, p = _parse_asn1_len(d, p)
    return int.from_bytes(d[p:p+ln], 'big'), p + ln

def _parse_pkcs1(data):
    """Parsează RSAPrivateKey PKCS#1 DER, returnează (n, d)."""
    p = 0
    assert data[p] == 0x30; p += 1
    _, p = _parse_asn1_len(data, p)
    _, p = _parse_asn1_int(data, p)   # version
    n, p = _parse_asn1_int(data, p)   # modulus
    _, p = _parse_asn1_int(data, p)   # publicExponent
    d, p = _parse_asn1_int(data, p)   # privateExponent
    return n, d

def _load_rsa_private_key(pem: str):
    """Încarcă cheia RSA privată din PEM (PKCS#1 sau PKCS#8), returnează (n, d)."""
    lines = pem.strip().splitlines()
    b64 = ''.join(l for l in lines if not l.startswith('---'))
    der = base64.b64decode(b64)
    if b'RSA PRIVATE' in pem.encode():
        # PKCS#1 direct
        return _parse_pkcs1(der)
    # PKCS#8: SEQUENCE { version, AlgorithmIdentifier, OCTET STRING { PKCS#1 } }
    p = 0
    assert der[p] == 0x30; p += 1
    _, p = _parse_asn1_len(der, p)
    _, p = _parse_asn1_int(der, p)        # version INTEGER
    assert der[p] == 0x30; p += 1         # AlgorithmIdentifier SEQUENCE
    aln, p = _parse_asn1_len(der, p); p += aln
    assert der[p] == 0x04; p += 1         # OCTET STRING
    olen, p = _parse_asn1_len(der, p)
    return _parse_pkcs1(der[p:p+olen])

# DigestInfo prefix pentru SHA-256 (RFC 3447)
_SHA256_DER = bytes([
    0x30,0x31,0x30,0x0d,0x06,0x09,0x60,0x86,0x48,0x01,0x65,0x03,0x04,
    0x02,0x01,0x05,0x00,0x04,0x20
])

def _rsa_pkcs1v15_sha256_sign(message: bytes, n: int, d: int) -> bytes:
    """Semnătură RSA PKCS#1 v1.5 SHA-256, implementare pură Python."""
    import hashlib
    k = (n.bit_length() + 7) // 8
    t = _SHA256_DER + hashlib.sha256(message).digest()
    ps = b'\xff' * (k - len(t) - 3)
    em = b'\x00\x01' + ps + b'\x00' + t
    s = pow(int.from_bytes(em, 'big'), d, n)
    return s.to_bytes(k, 'big')

def _make_jwt(sa_info: dict) -> str:
    def b64u(data): return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
    now = int(time.time())
    hdr = b64u(json.dumps({"alg":"RS256","typ":"JWT"}, separators=(',',':')).encode())
    pld = b64u(json.dumps({
        "iss": sa_info["client_email"],
        "sub": sa_info["client_email"],
        "scope": "https://www.googleapis.com/auth/spreadsheets",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now, "exp": now + 3600,
    }, separators=(',',':')).encode())
    signing_input = f"{hdr}.{pld}".encode()
    n, d = _load_rsa_private_key(sa_info["private_key"])
    sig = _rsa_pkcs1v15_sha256_sign(signing_input, n, d)
    return f"{hdr}.{pld}.{b64u(sig)}"

@st.cache_resource(ttl=3000)
def get_access_token() -> str:
    sa_info = dict(st.secrets["gcp_service_account"])
    jwt_token = _make_jwt(sa_info)
    body = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt_token,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["access_token"]

# HELPERS SHEETS API
# ─────────────────────────────────────────────
def sheets_get(range_name: str) -> list:
    token = get_access_token()
    sid = st.secrets["spreadsheet_id"]
    url = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(range_name)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("values", [])
    except Exception as e:
        st.error(f"Eroare citire Sheet ({range_name}): {e}")
        return []

def sheets_clear_and_write(sheet_name: str, rows: list):
    token = get_access_token()
    sid = st.secrets["spreadsheet_id"]
    url_clear = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet_name)}:clear"
    req = urllib.request.Request(
        url_clear, data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare clear Sheet: {e}")
        return
    body = json.dumps({"values": rows}).encode()
    url_write = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet_name)}?valueInputOption=RAW"
    req2 = urllib.request.Request(
        url_write, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT",
    )
    try:
        urllib.request.urlopen(req2)
    except Exception as e:
        st.error(f"Eroare scriere Sheet: {e}")

def sheets_append(sheet_name: str, rows: list):
    token = get_access_token()
    sid = st.secrets["spreadsheet_id"]
    body = json.dumps({"values": rows}).encode()
    url = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet_name)}:append?valueInputOption=RAW&insertDataOption=INSERT_ROWS"
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare append Sheet: {e}")

# ─────────────────────────────────────────────
# CITIRE / SCRIERE SHEETS
# ─────────────────────────────────────────────
def citeste_config() -> dict:
    rows = sheets_get("Config")
    cfg = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            try:
                cfg[row[0].strip()] = float(row[1].strip())
            except ValueError:
                cfg[row[0].strip()] = row[1].strip()
    return cfg

def salveaza_config(cfg: dict):
    rows = [["Cheie", "Valoare"]] + [[k, str(v)] for k, v in cfg.items()]
    sheets_clear_and_write("Config", rows)
    st.cache_resource.clear()

def citeste_sheet_df(sheet_name: str, cols: list) -> pd.DataFrame:
    rows = sheets_get(sheet_name)
    if len(rows) <= 1:
        return pd.DataFrame(columns=cols)
    header = rows[0]
    data = []
    for row in rows[1:]:
        padded = row + [""] * (len(header) - len(row))
        data.append(dict(zip(header, padded)))
    df = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]

def citeste_stoc() -> pd.DataFrame:
    return citeste_sheet_df("Stoc", ["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data"])

def salveaza_stoc(df: pd.DataFrame):
    rows = [["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data"]]
    for _, r in df.iterrows():
        rows.append([
            str(r.get("Produs", "")), str(r.get("Cantitate", 0)),
            str(r.get("Unitate", "")), str(r.get("Pret_Unitar", 0)),
            str(r.get("Data", "")),
        ])
    sheets_clear_and_write("Stoc", rows)

def citeste_vanzari() -> pd.DataFrame:
    return citeste_sheet_df("Vanzari", ["Preparat", "Cantitate_Vanduta", "Data"])

def salveaza_vanzari(rows_data: list):
    rows = [[r["Preparat"], str(r["Cantitate_Vanduta"]), str(r["Data"])] for r in rows_data]
    sheets_append("Vanzari", rows)

def citeste_retetar() -> pd.DataFrame:
    return citeste_sheet_df("Retetar", ["Preparat", "Ingredient", "Gramaj", "Pret_Vanzare"])

# ─────────────────────────────────────────────
# LOGICĂ FINANCIARĂ
# ─────────────────────────────────────────────
def calculeaza_food_cost_zilnic(vanzari_df, retetar_df, stoc_df) -> float:
    if vanzari_df.empty or retetar_df.empty or stoc_df.empty:
        return 0.0
    stoc_index = {}
    for _, row in stoc_df.iterrows():
        key = str(row.get("Produs", "")).lower().strip()
        try:
            stoc_index[key] = float(row.get("Pret_Unitar", 0))
        except (ValueError, TypeError):
            stoc_index[key] = 0.0
    total = 0.0
    for _, vrow in vanzari_df.iterrows():
        preparat = str(vrow.get("Preparat", "")).lower().strip()
        try:
            cant = float(vrow.get("Cantitate_Vanduta", 0))
        except (ValueError, TypeError):
            cant = 0.0
        ingrediente = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == preparat]
        for _, irow in ingrediente.iterrows():
            ing = str(irow.get("Ingredient", "")).lower().strip()
            try:
                gramaj = float(irow.get("Gramaj", 0)) / 1000.0
            except (ValueError, TypeError):
                gramaj = 0.0
            total += cant * gramaj * stoc_index.get(ing, 0.0)
    return round(total, 2)

def calculeaza_cascada(vanzari_brute: float, food_cost: float, cfg: dict) -> dict:
    cota_tva = float(cfg.get("cota_tva", 0.09))
    chirie = float(cfg.get("chirie_lunara", 0.0))
    salarii = float(cfg.get("salarii_lunare", 0.0))
    utilitati = float(cfg.get("utilitati_lunare", 0.0))
    regim = cfg.get("regim_fiscal", "micro1")
    cota_div = float(cfg.get("cota_dividend", 0.08))
    cota_imp = {"micro1": 0.01, "micro3": 0.03, "profit16": 0.16}.get(str(regim), 0.01)

    tva_col = vanzari_brute - (vanzari_brute / (1 + cota_tva))
    vanzari_net = vanzari_brute / (1 + cota_tva)
    fixe_zi = (chirie + salarii + utilitati) / 30.0
    fc_eff = food_cost if food_cost > 0 else vanzari_net * 0.30
    fc_sursa = "calculat din rețetar" if food_cost > 0 else "estimat (30%)"
    profit_brut = vanzari_net - fc_eff - fixe_zi
    imp_firma = max(profit_brut * cota_imp, 0.0)
    profit_dupa = profit_brut - imp_firma
    imp_div = max(profit_dupa * cota_div, 0.0)
    net = profit_dupa - imp_div
    marja = (net / vanzari_brute * 100) if vanzari_brute > 0 else 0.0

    return {
        "vanzari_brute": round(vanzari_brute, 2),
        "tva_colectat": round(tva_col, 2),
        "vanzari_fara_tva": round(vanzari_net, 2),
        "cheltuieli_fixe_zilnice": round(fixe_zi, 2),
        "food_cost": round(fc_eff, 2),
        "food_cost_sursa": fc_sursa,
        "profit_brut": round(profit_brut, 2),
        "impozit_firma": round(imp_firma, 2),
        "profit_dupa_impozit": round(profit_dupa, 2),
        "impozit_dividend": round(imp_div, 2),
        "profit_net_real": round(net, 2),
        "marja_neta": round(marja, 2),
    }

# ─────────────────────────────────────────────
# AI – GEMINI
# ─────────────────────────────────────────────
def extrage_factura_cu_ai(image_bytes: bytes) -> dict | None:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "Ești un sistem de extragere date din facturi fiscale românești. "
            "Analizează imaginea și extrage TOATE produsele. "
            "Returnează EXCLUSIV JSON valid, fără text suplimentar, fără markdown, fără backticks. "
            'Structura: {"produse": [{"produs": "Nume", "cantitate": 2.0, "unitate": "kg", "pret_unitar": 15.0}]}'
        )
        payload = json.dumps({
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_b64}},
                    {"text": prompt},
                ]
            }]
        }).encode()
        url = f"{GEMINI_BASE}?key={api_key}"
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("AI-ul nu a returnat JSON valid. Încearcă cu o imagine mai clară.")
        return None
    except Exception as e:
        st.error(f"Eroare AI: {e}")
        return None

# ─────────────────────────────────────────────
# UI COMPONENTS
# ─────────────────────────────────────────────
def card_metric(titlu, valoare, sub="", badge="", badge_tip="neutru"):
    if badge_tip == "profit":
        bc, btc = "rgba(74,222,128,0.12)", "#4ade80"
    elif badge_tip == "pierdere":
        bc, btc = "rgba(248,113,113,0.12)", "#f87171"
    else:
        bc, btc = "rgba(108,142,255,0.12)", "#6c8eff"
    badge_html = f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;background:{bc};color:{btc};font-size:0.72rem;font-weight:600;letter-spacing:0.03em;">{badge}</span>' if badge else ""
    sub_html = f'<div style="font-size:0.78rem;color:#4a4d5e;margin-top:5px;line-height:1.4;">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div style="background:#16181f;border-radius:12px;border:1px solid #2a2d3a;
        padding:1.4rem 1.5rem;margin-bottom:0.75rem;">
        <div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.75rem;">{titlu}</div>
        <div style="font-size:2rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;line-height:1.1;">{valoare}</div>
        {sub_html}
        <div style="margin-top:0.8rem;">{badge_html}</div>
    </div>""", unsafe_allow_html=True)

def linie_cascada(eticheta, valoare, prefix="−"):
    color = "#4ade80" if prefix == "+" else "#f87171" if valoare > 0 else "#4a4d5e"
    val_str = f"{'+ ' if prefix == '+' else '− '}{abs(valoare):,.2f} RON"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:0.6rem 0;border-bottom:1px solid #1e2130;">
        <span style="font-size:0.88rem;color:#8a8d9e;">{eticheta}</span>
        <span style="font-size:0.88rem;font-weight:500;color:{color};font-variant-numeric:tabular-nums;">{val_str}</span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(data, titlu="BON FISCAL"):
    net = data["profit_net_real"]
    bc = "rgba(74,222,128,0.12)"
    btc = "#4ade80" if net >= 0 else "#f87171"
    st.markdown(f"""
    <div style="background:#16181f;border:1px solid #2a2d3a;border-radius:12px;padding:1.8rem;
        max-width:420px;">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:0.65rem;font-weight:600;letter-spacing:0.15em;color:#4a4d5e;text-transform:uppercase;">{titlu}</div>
            <div style="font-size:0.75rem;color:#2e3245;margin-top:5px;">{datetime.now().strftime("%d.%m.%Y · %H:%M")}</div>
        </div>
        <div style="border-top:1px dashed #2a2d3a;border-bottom:1px dashed #2a2d3a;padding:1rem 0;margin-bottom:1rem;">
            {"".join(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.86rem;"><span style="color:#8a8d9e;">{lab}</span><span style="color:{col};">{val}</span></div>' for lab, col, val in [
                ("Încasări brute", "#e8eaf0", f"{data['vanzari_brute']:,.2f} RON"),
                ("TVA colectat", "#f87171", f"− {data['tva_colectat']:,.2f} RON"),
                ("Food Cost", "#f87171", f"− {data['food_cost']:,.2f} RON"),
                ("Cheltuieli fixe", "#f87171", f"− {data['cheltuieli_fixe_zilnice']:,.2f} RON"),
                ("Impozit firmă", "#f87171", f"− {data['impozit_firma']:,.2f} RON"),
                ("Impozit dividende", "#f87171", f"− {data['impozit_dividend']:,.2f} RON"),
            ])}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;">
            <span style="font-size:0.95rem;font-weight:600;color:#e8eaf0;">BANI ÎN MÂNĂ</span>
            <span style="font-size:1.5rem;font-weight:700;color:{btc};">{net:,.2f} RON</span>
        </div>
        <div style="text-align:right;margin-top:0.6rem;">
            <span style="display:inline-block;padding:4px 12px;border-radius:20px;background:{bc};color:{btc};font-size:0.75rem;font-weight:600;">
                Marjă netă {data["marja_neta"]:.1f}%
            </span>
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:2rem;padding-bottom:1.5rem;border-bottom:1px solid #2a2d3a;">
        <div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;">◈ Lana</div>
        <div style="font-size:0.65rem;font-weight:500;color:#4a4d5e;letter-spacing:0.18em;margin-top:5px;text-transform:uppercase;">ACQ Advisory · Consulting</div>
    </div>""", unsafe_allow_html=True)

    sectiune = st.radio("NAVIGARE", [
        "📊  Dashboard",
        "⚙️  Setări Fiscale",
        "📄  Scanare Facturi",
        "📥  Vânzări Zilnice",
        "🧪  Simulator Sandbox",
    ])

    st.markdown("""
    <div style="padding-top:2rem;margin-top:3rem;border-top:1px solid #2a2d3a;">
        <div style="font-size:0.68rem;color:#2e3245;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;">Plan activ</div>
        <div style="font-size:0.9rem;font-weight:600;color:#6c8eff;margin-top:4px;">Lana ADVISORY</div>
        <div style="font-size:0.8rem;color:#4a4d5e;margin-top:2px;">79€ / lună</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
if sectiune == "📊  Dashboard":
    st.markdown('<div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;margin-bottom:0.2rem;">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#4a4d5e;margin-bottom:2rem;">Situația financiară zilnică · actualizată la ultima închidere</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    stoc_df = citeste_stoc()
    vanzari_df = citeste_vanzari()
    retetar_df = citeste_retetar()

    azi = date.today().strftime("%Y-%m-%d")
    if not vanzari_df.empty and "Data" in vanzari_df.columns:
        vanzari_azi = vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)]
    else:
        vanzari_azi = pd.DataFrame(columns=["Preparat", "Cantitate_Vanduta", "Data"])

    vanzari_brute = 0.0
    if not vanzari_azi.empty and not retetar_df.empty:
        for _, row in vanzari_azi.iterrows():
            preparat = str(row.get("Preparat", "")).lower().strip()
            try:
                cant = float(row.get("Cantitate_Vanduta", 0))
            except (ValueError, TypeError):
                cant = 0.0
            match = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == preparat]
            if not match.empty:
                try:
                    pret = float(match.iloc[0].get("Pret_Vanzare", 0))
                    vanzari_brute += cant * pret
                except (ValueError, TypeError):
                    pass

    food_cost_zi = calculeaza_food_cost_zilnic(vanzari_azi, retetar_df, stoc_df)
    c = calculeaza_cascada(vanzari_brute, food_cost_zi, cfg)

    col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
    with col1:
        tip = "profit" if c["profit_net_real"] >= 0 else "pierdere"
        card_metric("Profit Net Real · Bani în mână", f"{c['profit_net_real']:,.2f} RON",
                    sub=f"Ziua de {azi}", badge=f"Marjă {c['marja_neta']:.1f}%", badge_tip=tip)
    with col2:
        fc_pct = (c["food_cost"] / c["vanzari_fara_tva"] * 100) if c["vanzari_fara_tva"] > 0 else 0
        card_metric("Food Cost Mediu", f"{c['food_cost']:,.2f} RON",
                    sub=f"{fc_pct:.1f}% din vânzări nete · {c['food_cost_sursa']}")
    with col3:
        total_op = c["cheltuieli_fixe_zilnice"] + c["tva_colectat"] + c["impozit_firma"] + c["impozit_dividend"]
        card_metric("Cheltuieli Operative", f"{total_op:,.2f} RON", sub="Taxe + Fixe zilnice")
    with col4:
        st.markdown("""
        <div style="background:#16181f;border-radius:12px;border:1px solid #2a2d3a;padding:1.4rem 1.5rem;">
            <div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.75rem;">Plan Activ</div>
            <div style="font-size:1rem;font-weight:600;color:#6c8eff;">Lana ADVISORY</div>
            <div style="font-size:0.85rem;color:#4a4d5e;margin-top:4px;">79€ / lună</div>
            <div style="margin-top:0.9rem;font-size:0.75rem;color:#2e3245;">Consultant digital de buzunar</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("""<div style="background:#16181f;border-radius:12px;border:1px solid #2a2d3a;padding:1.5rem 1.8rem;">
            <div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.2rem;">Cascadă Financiară Zilnică</div>""",
            unsafe_allow_html=True)
        linie_cascada("Încasări brute (cu TVA)", c["vanzari_brute"], prefix="+")
        linie_cascada("TVA colectat (→ ANAF)", c["tva_colectat"])
        linie_cascada("Food Cost ingrediente", c["food_cost"])
        linie_cascada("Cheltuieli fixe zilnice", c["cheltuieli_fixe_zilnice"])
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.6rem 0;border-bottom:1px solid #2a2d3a;">
            <span style="font-size:0.88rem;color:#e8eaf0;font-weight:500;">Profit brut operațional</span>
            <span style="font-size:0.88rem;font-weight:600;color:#6c8eff;">{c['profit_brut']:,.2f} RON</span>
            </div>""", unsafe_allow_html=True)
        linie_cascada("Impozit firmă", c["impozit_firma"])
        linie_cascada("Impozit dividende", c["impozit_dividend"])
        net_col = "#4ade80" if c["profit_net_real"] >= 0 else "#f87171"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:1rem 0;margin-top:0.3rem;">
            <span style="font-size:0.95rem;font-weight:700;color:#e8eaf0;">◈ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:700;color:{net_col};">{c['profit_net_real']:,.2f} RON</span>
            </div></div>""", unsafe_allow_html=True)

    with col_right:
        if not vanzari_azi.empty:
            st.markdown("""<div style="background:#16181f;border-radius:12px;border:1px solid #2a2d3a;padding:1.5rem 1.8rem;">
                <div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">Vânzări de azi</div>""",
                unsafe_allow_html=True)
            for _, row in vanzari_azi.iterrows():
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:0.45rem 0;border-bottom:1px solid #1e2130;font-size:0.86rem;">
                    <span style="color:#8a8d9e;">{row.get('Preparat','')}</span>
                    <span style="color:#6c8eff;font-weight:500;">{row.get('Cantitate_Vanduta',0)} buc</span>
                    </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:#16181f;border-radius:12px;border:1px solid #2a2d3a;padding:2rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:#4a4d5e;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.78rem;color:#2e3245;margin-top:4px;">Mergi la Vânzări Zilnice pentru a înregistra</div>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SETĂRI FISCALE
# ─────────────────────────────────────────────
elif sectiune == "⚙️  Setări Fiscale":
    st.markdown('<div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;margin-bottom:0.2rem;">Setări Fiscale & Cheltuieli Fixe</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#4a4d5e;margin-bottom:2rem;">Configurează parametrii fiscali și cheltuielile lunare ale afacerii tale</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">Regim Fiscal</div>', unsafe_allow_html=True)
        regim_opts = {"Micro 1%": "micro1", "Micro 3%": "micro3", "Profit 16%": "profit16"}
        regim_rev = {v: k for k, v in regim_opts.items()}
        regim_actual = regim_rev.get(str(cfg.get("regim_fiscal", "micro1")), "Micro 1%")
        regim_sel = st.selectbox("Regim fiscal", list(regim_opts.keys()),
                                  index=list(regim_opts.keys()).index(regim_actual))

        tva_opts = {"TVA 9% (restaurante)": 0.09, "TVA 19% (standard)": 0.19}
        tva_rev = {v: k for k, v in tva_opts.items()}
        tva_actual = tva_rev.get(float(cfg.get("cota_tva", 0.09)), "TVA 9% (restaurante)")
        tva_sel = st.selectbox("TVA", list(tva_opts.keys()),
                                index=list(tva_opts.keys()).index(tva_actual))

        div_opts = {"Impozit dividend 8%": 0.08, "Impozit dividend 10%": 0.10}
        div_rev = {v: k for k, v in div_opts.items()}
        div_actual = div_rev.get(float(cfg.get("cota_dividend", 0.08)), "Impozit dividend 8%")
        div_sel = st.selectbox("Dividend", list(div_opts.keys()),
                                index=list(div_opts.keys()).index(div_actual))

    with col2:
        st.markdown('<div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">Cheltuieli Lunare Fixe (RON)</div>', unsafe_allow_html=True)
        chirie = st.number_input("Chirie lunară", value=float(cfg.get("chirie_lunara", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        salarii = st.number_input("Salarii lunare", value=float(cfg.get("salarii_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        utilitati = st.number_input("Utilități lunare", value=float(cfg.get("utilitati_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")

    nr_clienti = st.number_input("Nr. estimat clienți/bonuri pe lună",
                                  value=int(cfg.get("nr_clienti_lunar", 500)), min_value=1, step=10)
    total_fixe = chirie + salarii + utilitati
    regie = total_fixe / nr_clienti if nr_clienti > 0 else 0

    st.markdown(f"""<div style="background:#16181f;border-radius:10px;padding:1rem 1.4rem;margin:1rem 0;border:1px solid #2a2d3a;display:inline-block;">
        <span style="font-size:0.78rem;color:#4a4d5e;">Regie fixă per bon: </span>
        <span style="font-size:1.1rem;font-weight:700;color:#6c8eff;">{regie:.2f} RON</span>
        <span style="font-size:0.75rem;color:#2e3245;margin-left:6px;">/ client</span>
        </div>""", unsafe_allow_html=True)

    if st.button("Salvează în Config →", type="primary"):
        salveaza_config({
            "regim_fiscal": regim_opts[regim_sel],
            "cota_tva": tva_opts[tva_sel],
            "cota_dividend": div_opts[div_sel],
            "chirie_lunara": chirie,
            "salarii_lunare": salarii,
            "utilitati_lunare": utilitati,
            "nr_clienti_lunar": nr_clienti,
        })
        st.success("✓ Configurația a fost salvată.")

# ─────────────────────────────────────────────
# SCANARE FACTURI
# ─────────────────────────────────────────────
elif sectiune == "📄  Scanare Facturi":
    st.markdown('<div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;margin-bottom:0.2rem;">Scanare Facturi & Alerte de Preț</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#4a4d5e;margin-bottom:2rem;">Încarcă o imagine a facturii. AI-ul extrage produsele automat.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Încarcă imagine factură", type=["jpg", "jpeg", "png", "webp"])

    if "produse_factura" not in st.session_state:
        st.session_state.produse_factura = []

    if uploaded:
        img_bytes = uploaded.read()
        col_img, col_proc = st.columns([1, 2])
        with col_img:
            st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True, caption="Factura încărcată")
        with col_proc:
            if st.button("🔍 Extrage cu AI"):
                with st.spinner("Gemini analizează factura..."):
                    rez = extrage_factura_cu_ai(img_bytes)
                    if rez and "produse" in rez:
                        st.session_state.produse_factura = rez["produse"]
                        st.success(f"✓ {len(rez['produse'])} produse identificate.")
                    else:
                        st.session_state.produse_factura = []

    if st.session_state.produse_factura:
        stoc_df = citeste_stoc()
        st.markdown("<hr style='border-color:#2a2d3a;margin:1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">Produse extrase · Verifică și editează</div>', unsafe_allow_html=True)

        produse_editate = []
        alerte = []
        are_invalide = False

        for i, prod in enumerate(st.session_state.produse_factura):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                nume = st.text_input("Produs", value=str(prod.get("produs", "")), key=f"pn_{i}")
            with col2:
                cant = st.number_input("Cantitate", value=float(prod.get("cantitate") or 0), key=f"pc_{i}", min_value=0.0)
            with col3:
                unit_ai = str(prod.get("unitate", "")).lower().strip()
                unit_invalid = unit_ai not in UNITATI_CUNOSCUTE
                unit = st.text_input("Unitate", value="" if unit_invalid else unit_ai,
                                     key=f"pu_{i}",
                                     placeholder="kg/g/l/buc" if unit_invalid else unit_ai)
                if unit_invalid:
                    st.markdown('<div style="font-size:0.72rem;color:#f87171;margin-top:2px;">⚠ Unitate necunoscută</div>', unsafe_allow_html=True)
                    are_invalide = True
                if unit and unit.lower().strip() not in UNITATI_CUNOSCUTE:
                    are_invalide = True
            with col4:
                pret = st.number_input("Preț/U", value=float(prod.get("pret_unitar") or 0), key=f"pp_{i}", min_value=0.0)

            if not stoc_df.empty and "Produs" in stoc_df.columns:
                match = stoc_df[stoc_df["Produs"].str.lower().str.strip() == str(nume).lower().strip()]
                if not match.empty:
                    try:
                        pret_vechi = float(match.iloc[0].get("Pret_Unitar", 0))
                        if pret > pret_vechi > 0:
                            alerte.append({"produs": nume, "vechi": pret_vechi, "nou": pret})
                    except (ValueError, TypeError):
                        pass

            produse_editate.append({"Produs": nume, "Cantitate": cant, "Unitate": unit,
                                    "Pret_Unitar": pret, "Data": date.today().strftime("%Y-%m-%d")})

        for a in alerte:
            st.markdown(f"""<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);border-radius:10px;
                padding:1rem 1.4rem;margin:0.5rem 0;font-size:0.88rem;color:#e8eaf0;">
                ⚠️ <strong style="color:#fbbf24;">{a['produs']}</strong> s-a scumpit de la
                <strong>{a['vechi']:.2f}</strong> la <strong>{a['nou']:.2f} RON</strong>.
                Profitul preparatelor a scăzut.
                </div>""", unsafe_allow_html=True)

        if are_invalide:
            st.markdown('<div style="font-size:0.83rem;color:#f87171;margin-bottom:0.5rem;">Completează unitățile lipsă pentru a activa salvarea.</div>', unsafe_allow_html=True)

        if st.button("Salvează în Stoc →", disabled=are_invalide, type="primary"):
            stoc_df_curent = citeste_stoc()
            stoc_nou = pd.DataFrame(produse_editate)
            if not stoc_df_curent.empty:
                for _, row in stoc_nou.iterrows():
                    mask = stoc_df_curent["Produs"].str.lower().str.strip() == str(row["Produs"]).lower().strip()
                    if mask.any():
                        idx = stoc_df_curent[mask].index[0]
                        stoc_df_curent.at[idx, "Cantitate"] = row["Cantitate"]
                        stoc_df_curent.at[idx, "Pret_Unitar"] = row["Pret_Unitar"]
                        stoc_df_curent.at[idx, "Data"] = row["Data"]
                    else:
                        stoc_df_curent = pd.concat([stoc_df_curent, pd.DataFrame([row])], ignore_index=True)
                salveaza_stoc(stoc_df_curent)
            else:
                salveaza_stoc(stoc_nou)
            st.success(f"✓ {len(produse_editate)} produse salvate în stoc.")
            st.session_state.produse_factura = []
            st.rerun()

# ─────────────────────────────────────────────
# VÂNZĂRI ZILNICE
# ─────────────────────────────────────────────
elif sectiune == "📥  Vânzări Zilnice":
    st.markdown('<div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;margin-bottom:0.2rem;">Înregistrare Vânzări Zilnice</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#4a4d5e;margin-bottom:2rem;">Introdu ce ai vândut azi. Stocul se actualizează automat.</div>', unsafe_allow_html=True)

    retetar_df = citeste_retetar()
    preparate = sorted(retetar_df["Preparat"].dropna().unique().tolist()) if not retetar_df.empty else []

    if "vanzari_zi" not in st.session_state:
        st.session_state.vanzari_zi = [{"preparat": "", "cantitate": 0}]

    if st.button("+ Adaugă preparat"):
        st.session_state.vanzari_zi.append({"preparat": "", "cantitate": 0})

    vanzari_input = []
    for i, item in enumerate(st.session_state.vanzari_zi):
        col1, col2 = st.columns([2, 1])
        with col1:
            if preparate:
                prep = st.selectbox("Preparat", ["— alege —"] + preparate, key=f"vp_{i}")
            else:
                prep = st.text_input("Preparat", value="", key=f"vp_{i}", placeholder="Nume preparat")
        with col2:
            cant = st.number_input("Cantitate", value=0, min_value=0, step=1, key=f"vc_{i}")
        if prep and prep != "— alege —":
            vanzari_input.append({"Preparat": prep, "Cantitate_Vanduta": cant})

    data_zi = st.date_input("Data închiderii", value=date.today())

    if st.button("Înregistrează Închiderea de Zi →", type="primary"):
        if not vanzari_input:
            st.warning("Nu ai introdus niciun preparat.")
        else:
            rows = [{"Preparat": v["Preparat"], "Cantitate_Vanduta": v["Cantitate_Vanduta"],
                     "Data": data_zi.strftime("%Y-%m-%d")}
                    for v in vanzari_input if v["Cantitate_Vanduta"] > 0]
            salveaza_vanzari(rows)

            stoc_df = citeste_stoc()
            if not retetar_df.empty and not stoc_df.empty:
                for v in vanzari_input:
                    preparat = str(v["Preparat"]).lower().strip()
                    cant_v = float(v["Cantitate_Vanduta"])
                    ingrediente = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == preparat]
                    for _, irow in ingrediente.iterrows():
                        ing = str(irow.get("Ingredient", "")).lower().strip()
                        try:
                            gramaj_kg = float(irow.get("Gramaj", 0)) / 1000.0
                        except (ValueError, TypeError):
                            gramaj_kg = 0.0
                        consum = cant_v * gramaj_kg
                        mask = stoc_df["Produs"].str.lower().str.strip() == ing
                        if mask.any():
                            idx = stoc_df[mask].index[0]
                            try:
                                cur = float(stoc_df.at[idx, "Cantitate"])
                            except (ValueError, TypeError):
                                cur = 0.0
                            stoc_df.at[idx, "Cantitate"] = max(0, round(cur - consum, 4))
                salveaza_stoc(stoc_df)

            st.success(f"✓ {len(rows)} preparate înregistrate. Stocul actualizat.")
            st.session_state.vanzari_zi = [{"preparat": "", "cantitate": 0}]
            st.rerun()

# ─────────────────────────────────────────────
# SIMULATOR SANDBOX
# ─────────────────────────────────────────────
elif sectiune == "🧪  Simulator Sandbox":
    st.markdown('<div style="font-size:1.6rem;font-weight:700;color:#e8eaf0;letter-spacing:-0.02em;margin-bottom:0.2rem;">Simulator Sandbox</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:#4a4d5e;margin-bottom:2rem;">Testează profitabilitatea unui preparat nou înainte de a-l pune în meniu.</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    stoc_df = citeste_stoc()
    produse_stoc = sorted(stoc_df["Produs"].dropna().unique().tolist()) if not stoc_df.empty else []

    col1, col2 = st.columns(2)
    with col1:
        nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger clasic")
    with col2:
        pret_vz = st.number_input("Preț vânzare dorit (cu TVA) · RON", min_value=0.0, step=0.5, format="%.2f")

    nr_ing = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)

    st.markdown('<div style="font-size:0.68rem;font-weight:600;color:#4a4d5e;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.8rem;margin-top:0.5rem;">Ingrediente & Gramaje</div>', unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ing)):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            if produse_stoc:
                ing = st.selectbox("Ingredient", ["— alege —"] + produse_stoc, key=f"si_{i}")
            else:
                ing = st.text_input("Ingredient", key=f"si_{i}", placeholder="Ingredient")
        with col_b:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sg_{i}")
        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)

    if st.button("Calculează Profitabilitatea →", type="primary"):
        if not nume_prep or pret_vz <= 0:
            st.warning("Completează numele și prețul.")
        elif not ingrediente_sim:
            st.warning("Adaugă cel puțin un ingredient cu gramaj.")
        else:
            stoc_idx = {}
            for _, row in stoc_df.iterrows():
                k = str(row.get("Produs", "")).lower().strip()
                try:
                    stoc_idx[k] = float(row.get("Pret_Unitar", 0))
                except (ValueError, TypeError):
                    stoc_idx[k] = 0.0

            fc = sum((x["gramaj_g"] / 1000.0) * stoc_idx.get(x["ingredient"].lower().strip(), 0.0)
                     for x in ingrediente_sim)

            nr_cl = float(cfg.get("nr_clienti_lunar", 500))
            fixe = float(cfg.get("chirie_lunara", 0)) + float(cfg.get("salarii_lunare", 0)) + float(cfg.get("utilitati_lunare", 0))
            regie = fixe / nr_cl if nr_cl > 0 else 0

            c = calculeaza_cascada(pret_vz, fc + regie, cfg)
            c["food_cost"] = round(fc, 2)
            c["cheltuieli_fixe_zilnice"] = round(regie, 2)

            col_bon, col_rec = st.columns([1, 1])
            with col_bon:
                bon_fiscal(c, titlu=f"SIMULARE · {nume_prep.upper()}")
            with col_rec:
                marja = c["marja_neta"]
                if marja < 10:
                    cota_tva = float(cfg.get("cota_tva", 0.09))
                    regim = cfg.get("regim_fiscal", "micro1")
                    ci = {"micro1": 0.01, "micro3": 0.03, "profit16": 0.16}.get(str(regim), 0.01)
                    cd = float(cfg.get("cota_dividend", 0.08))
                    factor = (1 - ci) * (1 - cd)
                    pret_rec = ((fc + regie) / (factor * 0.8)) * (1 + cota_tva) if factor > 0 else (fc + regie) * 3
                    st.markdown(f"""<div style="background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.2);border-radius:12px;padding:1.4rem;margin-top:1rem;">
                        <div style="font-size:0.95rem;font-weight:600;color:#f87171;margin-bottom:0.5rem;">⚠ Marjă insuficientă ({marja:.1f}%)</div>
                        <div style="font-size:0.85rem;color:#8a8d9e;line-height:1.6;">
                        Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong style="color:#e8eaf0;">Preț recomandat pentru marjă 20%:</strong>
                        <span style="font-size:1.05rem;font-weight:700;color:#f87171;"> {pret_rec:.2f} RON</span></div>
                        </div>""", unsafe_allow_html=True)
                elif marja <= 20:
                    st.markdown(f"""<div style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.2);border-radius:12px;padding:1.4rem;margin-top:1rem;">
                        <div style="font-size:0.95rem;font-weight:600;color:#fbbf24;margin-bottom:0.5rem;">ℹ Marjă acceptabilă ({marja:.1f}%)</div>
                        <div style="font-size:0.85rem;color:#8a8d9e;line-height:1.6;">Există loc de optimizare. Caută furnizori mai competitivi pentru ingredientele cheie.</div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background:rgba(74,222,128,0.08);border:1px solid rgba(74,222,128,0.2);border-radius:12px;padding:1.4rem;margin-top:1rem;">
                        <div style="font-size:0.95rem;font-weight:600;color:#4ade80;margin-bottom:0.5rem;">✓ Marjă excelentă ({marja:.1f}%)</div>
                        <div style="font-size:0.85rem;color:#8a8d9e;line-height:1.6;">Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown(f"""<div style="background:#16181f;border:1px solid #2a2d3a;border-radius:12px;padding:1.2rem 1.5rem;margin-top:1rem;font-size:0.84rem;">
                    <div style="color:#4a4d5e;font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.8rem;">Detalii calcul</div>
                    <div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="color:#8a8d9e;">Food cost ingrediente</span><span style="color:#e8eaf0;font-weight:500;">{fc:.2f} RON</span></div>
                    <div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="color:#8a8d9e;">Regie fixă / client</span><span style="color:#e8eaf0;font-weight:500;">{regie:.2f} RON</span></div>
                    <div style="display:flex;justify-content:space-between;padding:4px 0;"><span style="color:#8a8d9e;">Preț vânzare (cu TVA)</span><span style="color:#e8eaf0;font-weight:500;">{pret_vz:.2f} RON</span></div>
                    </div>""", unsafe_allow_html=True)
