import streamlit as st
import pandas as pd
import json
import base64
import io
import urllib.request
import urllib.error
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

# ─────────────────────────────────────────────
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
#MainMenu, header, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.stApp { background-color: #f7f7f9; }
[data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #ebebf0; }
[data-testid="stSidebar"] > div:first-child { padding: 2rem 1.5rem; }
[data-testid="stSidebar"] .stRadio > label {
    font-size: 0.78rem; font-weight: 500; letter-spacing: 0.06em;
    color: #8a8a99; text-transform: uppercase; margin-bottom: 0.6rem;
}
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex; align-items: center; padding: 0.55rem 0.75rem;
    border-radius: 10px; font-size: 0.92rem; font-weight: 400;
    color: #1a1a2e; cursor: pointer; transition: background 0.15s ease;
}
[data-testid="stSidebar"] .stRadio > div > label:hover { background: #f7f7f9; }
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    border: 1px solid #e8e8f0 !important; border-radius: 10px !important;
    background: #ffffff !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 0.93rem !important; color: #1a1a2e !important; box-shadow: none !important;
}
.stButton > button {
    border-radius: 10px; border: 1px solid #e8e8f0; background: #ffffff;
    color: #1a1a2e; font-family: 'DM Sans', sans-serif; font-size: 0.88rem;
    font-weight: 500; padding: 0.5rem 1.2rem; transition: all 0.15s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stButton > button:hover { background: #1a3a5c; color: #ffffff; border-color: #1a3a5c; }
.stButton > button[kind="primary"] { background: #1a3a5c; color: #ffffff; border-color: #1a3a5c; }
.stButton > button[kind="primary"]:hover { background: #0d2a45; border-color: #0d2a45; }
[data-testid="stFileUploader"] {
    border: 1.5px dashed #d8d8e8; border-radius: 14px; background: #ffffff; padding: 1rem;
}
hr { border: none; border-top: 1px solid #ebebf0; margin: 1.5rem 0; }
.section-title { font-size: 1.5rem; font-weight: 600; color: #0d0d1a; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
.section-sub { font-size: 0.88rem; color: #8a8a99; margin-bottom: 2rem; font-weight: 400; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TOKEN GOOGLE (OAuth2 cu service account via JWT)
# ─────────────────────────────────────────────
@st.cache_resource(ttl=3000)
def get_access_token() -> str:
    import time
    import hmac
    import hashlib
    import struct

    sa = st.secrets["gcp_service_account"]
    private_key_pem = sa["private_key"]
    client_email = sa["client_email"]
    token_uri = sa.get("token_uri", "https://oauth2.googleapis.com/token")
    scope = "https://www.googleapis.com/auth/spreadsheets"

    now = int(time.time())
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    payload = base64.urlsafe_b64encode(json.dumps({
        "iss": client_email,
        "scope": scope,
        "aud": token_uri,
        "exp": now + 3600,
        "iat": now,
    }).encode()).rstrip(b"=").decode()
    signing_input = f"{header}.{payload}".encode()

    # Sign with RSA-SHA256 using only stdlib
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None
        )
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    except ImportError:
        # fallback: use google-auth if available
        import google.auth.crypt
        import google.auth.jwt
        signer = google.auth.crypt.RSASigner.from_service_account_info(dict(sa))
        token_data = {
            "iss": client_email,
            "scope": scope,
            "aud": token_uri,
            "exp": now + 3600,
            "iat": now,
        }
        jwt_token = google.auth.jwt.encode(signer, token_data).decode()
        # Exchange JWT for access token
        body = (
            f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
            f"&assertion={jwt_token}"
        ).encode()
        req = urllib.request.Request(
            token_uri,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())["access_token"]

    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    jwt_token = f"{header}.{payload}.{sig_b64}"

    body = (
        f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer"
        f"&assertion={jwt_token}"
    ).encode()
    req = urllib.request.Request(
        token_uri,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]

# ─────────────────────────────────────────────
# HELPERS SHEETS API (HTTP pur)
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
    # Clear
    url_clear = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet_name)}:clear"
    req = urllib.request.Request(
        url_clear,
        data=b"{}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare clear Sheet: {e}")
        return
    # Write
    body = json.dumps({"values": rows}).encode()
    url_write = f"{SHEETS_BASE}/{sid}/values/{urllib.parse.quote(sheet_name)}?valueInputOption=RAW"
    req2 = urllib.request.Request(
        url_write,
        data=body,
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
        url,
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        st.error(f"Eroare append Sheet: {e}")

import urllib.parse

# ─────────────────────────────────────────────
# CITIRE / SCRIERE SHEETS
# ─────────────────────────────────────────────
def citeste_config() -> dict:
    rows = sheets_get("Config")
    cfg = {}
    for row in rows[1:]:  # skip header
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
# LOGICA FINANCIARĂ
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
# AI – GEMINI (HTTP pur, fără SDK)
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
        bc, btc = "#e8f5e9", "#2e7d32"
    elif badge_tip == "pierdere":
        bc, btc = "#fce8e8", "#c62828"
    else:
        bc, btc = "#eef2f7", "#4a6785"
    badge_html = f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;background:{bc};color:{btc};font-size:0.72rem;font-weight:500;">{badge}</span>' if badge else ""
    sub_html = f'<div style="font-size:0.82rem;color:#8a8a99;margin-top:4px;">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div style="background:#fff;border-radius:16px;border:1px solid #e8e8f0;
        box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.4rem 1.6rem;margin-bottom:0.75rem;">
        <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.6rem;">{titlu}</div>
        <div style="font-size:2.1rem;font-weight:600;color:#1a3a5c;letter-spacing:-0.03em;line-height:1.1;">{valoare}</div>
        {sub_html}<div style="margin-top:0.7rem;">{badge_html}</div>
    </div>""", unsafe_allow_html=True)

def linie_cascada(eticheta, valoare, prefix="−"):
    color = "#2e7d32" if prefix == "+" else "#c62828" if valoare > 0 else "#8a8a99"
    val_str = f"{'+ ' if prefix == '+' else '− '}{abs(valoare):,.2f} RON"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:0.55rem 0;border-bottom:1px solid #f0f0f5;">
        <span style="font-size:0.9rem;color:#4a4a5a;">{eticheta}</span>
        <span style="font-size:0.9rem;font-weight:500;color:{color};font-variant-numeric:tabular-nums;">{val_str}</span>
    </div>""", unsafe_allow_html=True)

def bon_fiscal(data, titlu="BON FISCAL"):
    net = data["profit_net_real"]
    bc = "#e8f5e9" if net >= 0 else "#fce8e8"
    btc = "#2e7d32" if net >= 0 else "#c62828"
    st.markdown(f"""
    <div style="background:#fff;border:1px solid #e8e8f0;border-radius:16px;padding:2rem;
        max-width:420px;box-shadow:0 4px 24px rgba(0,0,0,0.04);">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:0.7rem;font-weight:500;letter-spacing:0.15em;color:#8a8a99;text-transform:uppercase;">{titlu}</div>
            <div style="font-size:0.78rem;color:#c0c0cc;margin-top:4px;">{datetime.now().strftime("%d.%m.%Y · %H:%M")}</div>
        </div>
        <div style="border-top:1px dashed #e8e8f0;border-bottom:1px dashed #e8e8f0;padding:1rem 0;margin-bottom:1rem;">
            {"".join(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;"><span>{lab}</span><span style="color:{col};">{val}</span></div>' for lab, col, val in [
                ("Încasări brute", "#0d0d1a", f"{data['vanzari_brute']:,.2f} RON"),
                ("TVA colectat", "#c62828", f"− {data['tva_colectat']:,.2f} RON"),
                ("Food Cost", "#c62828", f"− {data['food_cost']:,.2f} RON"),
                ("Cheltuieli fixe", "#c62828", f"− {data['cheltuieli_fixe_zilnice']:,.2f} RON"),
                ("Impozit firmă", "#c62828", f"− {data['impozit_firma']:,.2f} RON"),
                ("Impozit dividende", "#c62828", f"− {data['impozit_dividend']:,.2f} RON"),
            ])}
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;">
            <span style="font-size:1rem;font-weight:600;color:#0d0d1a;">BANI ÎN MÂNĂ</span>
            <span style="font-size:1.6rem;font-weight:700;color:#1a3a5c;">{net:,.2f} RON</span>
        </div>
        <div style="text-align:right;margin-top:0.5rem;">
            <span style="display:inline-block;padding:4px 12px;border-radius:20px;background:{bc};color:{btc};font-size:0.78rem;font-weight:500;">
                Marjă netă {data["marja_neta"]:.1f}%
            </span>
        </div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:2rem;padding-bottom:1.5rem;border-bottom:1px solid #ebebf0;">
        <div style="font-size:1.8rem;font-weight:700;color:#0d0d1a;letter-spacing:-0.03em;">◈ Lana</div>
        <div style="font-size:0.68rem;font-weight:500;color:#b0b0be;letter-spacing:0.18em;margin-top:4px;text-transform:uppercase;">ACQ Advisory · Consulting</div>
    </div>""", unsafe_allow_html=True)

    sectiune = st.radio("NAVIGARE", [
        "📊  Dashboard",
        "⚙️  Setări Fiscale",
        "📄  Scanare Facturi",
        "📥  Vânzări Zilnice",
        "🧪  Simulator Sandbox",
    ])

    st.markdown("""
    <div style="padding-top:2rem;margin-top:3rem;border-top:1px solid #ebebf0;">
        <div style="font-size:0.72rem;color:#c0c0cc;">Lana ADVISORY</div>
        <div style="font-size:0.8rem;font-weight:500;color:#8a8a99;margin-top:2px;">79€ / lună</div>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
if sectiune == "📊  Dashboard":
    st.markdown('<div class="section-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Situația financiară zilnică · actualizată la ultima închidere</div>', unsafe_allow_html=True)

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
        card_metric("Cheltuieli Operative Totale", f"{total_op:,.2f} RON", sub="Taxe + Fixe zilnice")
    with col4:
        st.markdown("""
        <div style="background:#fff;border-radius:16px;border:1px solid #e8e8f0;
            box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.4rem 1.6rem;">
            <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.6rem;">Plan Activ</div>
            <div style="font-size:1.1rem;font-weight:600;color:#1a3a5c;">Lana ADVISORY</div>
            <div style="font-size:0.88rem;color:#8a8a99;margin-top:4px;">79€ / lună</div>
            <div style="margin-top:0.9rem;font-size:0.78rem;color:#b0b0be;">Consultant digital de buzunar</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("""<div style="background:#fff;border-radius:16px;border:1px solid #e8e8f0;
            box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.6rem 2rem;">
            <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1.2rem;">Cascada Financiară Zilnică</div>""",
            unsafe_allow_html=True)
        linie_cascada("Încasări brute (cu TVA)", c["vanzari_brute"], prefix="+")
        linie_cascada("TVA colectat (→ ANAF)", c["tva_colectat"])
        linie_cascada("Food Cost ingrediente", c["food_cost"])
        linie_cascada("Cheltuieli fixe zilnice", c["cheltuieli_fixe_zilnice"])
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.55rem 0;border-bottom:1px solid #e8e8f0;">
            <span style="font-size:0.9rem;color:#0d0d1a;font-weight:500;">Profit brut operațional</span>
            <span style="font-size:0.9rem;font-weight:600;color:#1a3a5c;">{c['profit_brut']:,.2f} RON</span>
            </div>""", unsafe_allow_html=True)
        linie_cascada("Impozit firmă", c["impozit_firma"])
        linie_cascada("Impozit dividende", c["impozit_dividend"])
        net_col = "#2e7d32" if c["profit_net_real"] >= 0 else "#c62828"
        st.markdown(f"""<div style="display:flex;justify-content:space-between;align-items:center;padding:0.9rem 0;margin-top:0.5rem;">
            <span style="font-size:1rem;font-weight:700;color:#0d0d1a;">◈ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:700;color:{net_col};">{c['profit_net_real']:,.2f} RON</span>
            </div></div>""", unsafe_allow_html=True)

    with col_right:
        if not vanzari_azi.empty:
            st.markdown("""<div style="background:#fff;border-radius:16px;border:1px solid #e8e8f0;
                box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.6rem 2rem;">
                <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1rem;">Vânzări de azi</div>""",
                unsafe_allow_html=True)
            for _, row in vanzari_azi.iterrows():
                st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px solid #f5f5f8;font-size:0.88rem;">
                    <span style="color:#4a4a5a;">{row.get('Preparat','')}</span>
                    <span style="color:#1a3a5c;font-weight:500;">{row.get('Cantitate_Vanduta',0)} buc</span>
                    </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background:#fff;border-radius:16px;border:1px solid #e8e8f0;
                box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:2rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:#8a8a99;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.8rem;color:#c0c0cc;margin-top:4px;">Mergi la Vânzări Zilnice pentru a înregistra</div>
                </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SETĂRI FISCALE
# ─────────────────────────────────────────────
elif sectiune == "⚙️  Setări Fiscale":
    st.markdown('<div class="section-title">Setări Fiscale & Cheltuieli Fixe</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Configurează parametrii fiscali și cheltuielile lunare ale afacerii tale</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1rem;">Regim Fiscal</div>', unsafe_allow_html=True)
        regim_opts = {"Micro 1%": "micro1", "Micro 3%": "micro3", "Profit 16%": "profit16"}
        regim_rev = {v: k for k, v in regim_opts.items()}
        regim_actual = regim_rev.get(str(cfg.get("regim_fiscal", "micro1")), "Micro 1%")
        regim_sel = st.selectbox("Regim fiscal", list(regim_opts.keys()),
                                  index=list(regim_opts.keys()).index(regim_actual), label_visibility="collapsed")

        tva_opts = {"TVA 9% (restaurante)": 0.09, "TVA 19% (standard)": 0.19}
        tva_rev = {v: k for k, v in tva_opts.items()}
        tva_actual = tva_rev.get(float(cfg.get("cota_tva", 0.09)), "TVA 9% (restaurante)")
        tva_sel = st.selectbox("TVA", list(tva_opts.keys()),
                                index=list(tva_opts.keys()).index(tva_actual), label_visibility="collapsed")

        div_opts = {"Impozit dividend 8%": 0.08, "Impozit dividend 10%": 0.10}
        div_rev = {v: k for k, v in div_opts.items()}
        div_actual = div_rev.get(float(cfg.get("cota_dividend", 0.08)), "Impozit dividend 8%")
        div_sel = st.selectbox("Dividend", list(div_opts.keys()),
                                index=list(div_opts.keys()).index(div_actual), label_visibility="collapsed")

    with col2:
        st.markdown('<div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1rem;">Cheltuieli Lunare Fixe (RON)</div>', unsafe_allow_html=True)
        chirie = st.number_input("Chirie", value=float(cfg.get("chirie_lunara", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        salarii = st.number_input("Salarii", value=float(cfg.get("salarii_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        utilitati = st.number_input("Utilități", value=float(cfg.get("utilitati_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")

    nr_clienti = st.number_input("Nr. estimat clienți/bonuri pe lună",
                                  value=int(cfg.get("nr_clienti_lunar", 500)), min_value=1, step=10)
    total_fixe = chirie + salarii + utilitati
    regie = total_fixe / nr_clienti if nr_clienti > 0 else 0

    st.markdown(f"""<div style="background:#f7f7f9;border-radius:12px;padding:1rem 1.4rem;margin:1rem 0;border:1px solid #e8e8f0;display:inline-block;">
        <span style="font-size:0.8rem;color:#8a8a99;">Regie fixă per bon: </span>
        <span style="font-size:1.1rem;font-weight:600;color:#1a3a5c;">{regie:.2f} RON</span>
        <span style="font-size:0.78rem;color:#b0b0be;margin-left:6px;">/ client</span>
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
    st.markdown('<div class="section-title">Scanare Facturi & Alerte de Preț</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Încarcă o imagine a facturii. AI-ul extrage produsele automat.</div>', unsafe_allow_html=True)

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
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:1rem;">Produse extrase · Verifică și editează</div>', unsafe_allow_html=True)

        produse_editate = []
        alerte = []
        are_invalide = False

        for i, prod in enumerate(st.session_state.produse_factura):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                nume = st.text_input("Produs", value=str(prod.get("produs", "")), key=f"pn_{i}", label_visibility="collapsed")
            with col2:
                cant = st.number_input("Cant", value=float(prod.get("cantitate") or 0), key=f"pc_{i}", label_visibility="collapsed", min_value=0.0)
            with col3:
                unit_ai = str(prod.get("unitate", "")).lower().strip()
                unit_invalid = unit_ai not in UNITATI_CUNOSCUTE
                unit = st.text_input("Unitate", value="" if unit_invalid else unit_ai,
                                     key=f"pu_{i}", label_visibility="collapsed",
                                     placeholder="kg/g/l/buc" if unit_invalid else unit_ai)
                if unit_invalid:
                    st.markdown('<div style="font-size:0.75rem;color:#e57373;margin-top:2px;">⚠ Unitate necunoscută</div>', unsafe_allow_html=True)
                    are_invalide = True
                if unit and unit.lower().strip() not in UNITATI_CUNOSCUTE:
                    are_invalide = True
            with col4:
                pret = st.number_input("Preț/U", value=float(prod.get("pret_unitar") or 0), key=f"pp_{i}", label_visibility="collapsed", min_value=0.0)

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
            st.markdown(f"""<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:12px;
                padding:1rem 1.4rem;margin:0.5rem 0;font-size:0.9rem;">
                ⚠️ <strong>{a['produs']}</strong> s-a scumpit de la <strong>{a['vechi']:.2f}</strong>
                la <strong>{a['nou']:.2f} RON</strong>. Profitul preparatelor a scăzut.
                </div>""", unsafe_allow_html=True)

        if are_invalide:
            st.markdown('<div style="font-size:0.85rem;color:#e57373;margin-bottom:0.5rem;">Completează unitățile lipsă pentru a activa salvarea.</div>', unsafe_allow_html=True)

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
    st.markdown('<div class="section-title">Înregistrare Vânzări Zilnice</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Introdu ce ai vândut azi. Stocul se actualizează automat.</div>', unsafe_allow_html=True)

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
                prep = st.selectbox("Preparat", ["— alege —"] + preparate, key=f"vp_{i}", label_visibility="collapsed")
            else:
                prep = st.text_input("Preparat", value="", key=f"vp_{i}", label_visibility="collapsed", placeholder="Nume preparat")
        with col2:
            cant = st.number_input("Cant", value=0, min_value=0, step=1, key=f"vc_{i}", label_visibility="collapsed")
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
    st.markdown('<div class="section-title">Simulator Sandbox</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Testează profitabilitatea unui preparat nou înainte de a-l pune în meniu.</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    stoc_df = citeste_stoc()
    produse_stoc = sorted(stoc_df["Produs"].dropna().unique().tolist()) if not stoc_df.empty else []

    col1, col2 = st.columns(2)
    with col1:
        nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger clasic")
    with col2:
        pret_vz = st.number_input("Preț vânzare dorit (cu TVA) · RON", min_value=0.0, step=0.5, format="%.2f")

    nr_ing = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)

    st.markdown('<div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.8rem;">Ingrediente & Gramaje</div>', unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ing)):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            if produse_stoc:
                ing = st.selectbox("Ingredient", ["— alege —"] + produse_stoc, key=f"si_{i}", label_visibility="collapsed")
            else:
                ing = st.text_input("Ingredient", key=f"si_{i}", label_visibility="collapsed", placeholder="Ingredient")
        with col_b:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sg_{i}", label_visibility="collapsed")
        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

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
                    st.markdown(f"""<div style="background:#fce8e8;border:1px solid #f5c6c6;border-radius:14px;padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#c62828;margin-bottom:0.5rem;">⚠ Marjă insuficientă ({marja:.1f}%)</div>
                        <div style="font-size:0.88rem;color:#7f1f1f;line-height:1.6;">
                        Ajustează prețul sau reduce ingredientele costisitoare.<br>
                        <strong>Preț recomandat pentru marjă 20%:</strong>
                        <span style="font-size:1.1rem;font-weight:700;"> {pret_rec:.2f} RON</span></div>
                        </div>""", unsafe_allow_html=True)
                elif marja <= 20:
                    st.markdown(f"""<div style="background:#fff8e1;border:1px solid #ffe082;border-radius:14px;padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#f57f17;margin-bottom:0.5rem;">ℹ Marjă acceptabilă ({marja:.1f}%)</div>
                        <div style="font-size:0.88rem;color:#795700;line-height:1.6;">Există loc de optimizare. Caută furnizori mai competitivi pentru ingredientele cheie.</div>
                        </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:14px;padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#2e7d32;margin-bottom:0.5rem;">✓ Marjă excelentă ({marja:.1f}%)</div>
                        <div style="font-size:0.88rem;color:#1b5e20;line-height:1.6;">Preparatul este viabil comercial. Îl poți introduce cu încredere în meniu.</div>
                        </div>""", unsafe_allow_html=True)

                st.markdown(f"""<div style="background:#fff;border:1px solid #e8e8f0;border-radius:14px;padding:1.2rem 1.5rem;margin-top:1rem;font-size:0.85rem;">
                    <div style="color:#8a8a99;font-size:0.72rem;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.8rem;">Detalii calcul</div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;"><span>Food cost ingrediente</span><span style="font-weight:500;">{fc:.2f} RON</span></div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;"><span>Regie fixă / client</span><span style="font-weight:500;">{regie:.2f} RON</span></div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;"><span>Preț vânzare (cu TVA)</span><span style="font-weight:500;">{pret_vz:.2f} RON</span></div>
                    </div>""", unsafe_allow_html=True)
