import streamlit as st
import gspread
import pandas as pd
import json
import base64
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime, date
from PIL import Image
import io

# ─────────────────────────────────────────────
# CONSTANTE
# ─────────────────────────────────────────────
UNITATI_CUNOSCUTE = {"kg", "g", "l", "ml", "buc", "bucata", "bucăți", "bucati", "litri", "grame", "kilograme"}
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─────────────────────────────────────────────
# PAGINA CONFIG & CSS GLOBAL
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

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, header, footer, [data-testid="stToolbar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Background */
.stApp {
    background-color: #f7f7f9;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #ebebf0;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 2rem 1.5rem;
}

/* Radio buttons in sidebar */
[data-testid="stSidebar"] .stRadio > label {
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    color: #8a8a99;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 2px;
}
[data-testid="stSidebar"] .stRadio > div > label {
    display: flex;
    align-items: center;
    padding: 0.55rem 0.75rem;
    border-radius: 10px;
    font-size: 0.92rem;
    font-weight: 400;
    color: #1a1a2e;
    cursor: pointer;
    transition: background 0.15s ease;
    letter-spacing: 0;
    text-transform: none;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: #f7f7f9;
}
[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
    background: #f0f0f7;
    font-weight: 500;
    color: #1a3a5c;
}

/* Input fields */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    border: 1px solid #e8e8f0 !important;
    border-radius: 10px !important;
    background: #ffffff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.93rem !important;
    color: #1a1a2e !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #1a3a5c !important;
    box-shadow: 0 0 0 3px rgba(26,58,92,0.07) !important;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    border: 1px solid #e8e8f0;
    background: #ffffff;
    color: #1a1a2e;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    padding: 0.5rem 1.2rem;
    transition: all 0.15s ease;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.stButton > button:hover {
    background: #1a3a5c;
    color: #ffffff;
    border-color: #1a3a5c;
    box-shadow: 0 2px 8px rgba(26,58,92,0.15);
}
.stButton > button:active {
    transform: scale(0.98);
}

/* Primary button override */
.stButton > button[kind="primary"] {
    background: #1a3a5c;
    color: #ffffff;
    border-color: #1a3a5c;
}
.stButton > button[kind="primary"]:hover {
    background: #0d2a45;
    border-color: #0d2a45;
}

/* Alerts */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
    font-size: 0.9rem !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    border: 1.5px dashed #d8d8e8;
    border-radius: 14px;
    background: #ffffff;
    padding: 1rem;
}

/* Dividers */
hr {
    border: none;
    border-top: 1px solid #ebebf0;
    margin: 1.5rem 0;
}

/* DataFrame/Table */
.stDataFrame {
    border: 1px solid #e8e8f0;
    border-radius: 12px;
    overflow: hidden;
}

/* Section titles */
.section-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #0d0d1a;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}
.section-sub {
    font-size: 0.88rem;
    color: #8a8a99;
    margin-bottom: 2rem;
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONEXIUNE GOOGLE SHEETS
# ─────────────────────────────────────────────
@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)

def get_spreadsheet():
    client = get_gsheet_client()
    return client.open_by_key(st.secrets["spreadsheet_id"])

# ─────────────────────────────────────────────
# CITIRE / SCRIERE SHEETS
# ─────────────────────────────────────────────
def citeste_config() -> dict:
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Config")
        rows = ws.get_all_values()
        cfg = {}
        for row in rows:
            if len(row) >= 2 and row[0]:
                key = row[0].strip()
                val = row[1].strip() if row[1] else ""
                try:
                    cfg[key] = float(val)
                except ValueError:
                    cfg[key] = val
        return cfg
    except Exception as e:
        st.error(f"Eroare la citirea Config: {e}")
        return {}

def salveaza_config(cfg: dict):
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Config")
        ws.clear()
        ws.append_row(["Cheie", "Valoare"])
        for k, v in cfg.items():
            ws.append_row([k, str(v)])
        st.cache_resource.clear()
    except Exception as e:
        st.error(f"Eroare la salvarea Config: {e}")

def citeste_stoc() -> pd.DataFrame:
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Stoc")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Eroare la citirea Stoc: {e}")
        return pd.DataFrame(columns=["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data"])

def salveaza_stoc(df: pd.DataFrame):
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Stoc")
        ws.clear()
        ws.append_row(["Produs", "Cantitate", "Unitate", "Pret_Unitar", "Data"])
        for _, row in df.iterrows():
            ws.append_row([
                str(row.get("Produs", "")),
                str(row.get("Cantitate", 0)),
                str(row.get("Unitate", "")),
                str(row.get("Pret_Unitar", 0)),
                str(row.get("Data", "")),
            ])
    except Exception as e:
        st.error(f"Eroare la salvarea Stoc: {e}")

def citeste_vanzari() -> pd.DataFrame:
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Vanzari")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["Preparat", "Cantitate_Vanduta", "Data"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Eroare la citirea Vanzari: {e}")
        return pd.DataFrame(columns=["Preparat", "Cantitate_Vanduta", "Data"])

def salveaza_vanzari(rows: list):
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Vanzari")
        for row in rows:
            ws.append_row([
                str(row["Preparat"]),
                str(row["Cantitate_Vanduta"]),
                str(row["Data"]),
            ])
    except Exception as e:
        st.error(f"Eroare la salvarea Vanzari: {e}")

def citeste_retetar() -> pd.DataFrame:
    try:
        sh = get_spreadsheet()
        ws = sh.worksheet("Retetar")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["Preparat", "Ingredient", "Gramaj", "Pret_Vanzare"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Eroare la citirea Retetar: {e}")
        return pd.DataFrame(columns=["Preparat", "Ingredient", "Gramaj", "Pret_Vanzare"])

# ─────────────────────────────────────────────
# LOGICA FINANCIARĂ
# ─────────────────────────────────────────────
def calculeaza_food_cost_zilnic(vanzari_df: pd.DataFrame, retetar_df: pd.DataFrame, stoc_df: pd.DataFrame) -> float:
    if vanzari_df.empty or retetar_df.empty or stoc_df.empty:
        return 0.0

    total_food_cost = 0.0
    stoc_index = {}
    for _, row in stoc_df.iterrows():
        key = str(row.get("Produs", "")).lower().strip()
        try:
            stoc_index[key] = float(row.get("Pret_Unitar", 0))
        except (ValueError, TypeError):
            stoc_index[key] = 0.0

    for _, vrow in vanzari_df.iterrows():
        preparat = str(vrow.get("Preparat", "")).lower().strip()
        try:
            cantitate_vanduta = float(vrow.get("Cantitate_Vanduta", 0))
        except (ValueError, TypeError):
            cantitate_vanduta = 0.0

        ingrediente = retetar_df[
            retetar_df["Preparat"].str.lower().str.strip() == preparat
        ]

        for _, irow in ingrediente.iterrows():
            ingredient = str(irow.get("Ingredient", "")).lower().strip()
            try:
                gramaj = float(irow.get("Gramaj", 0)) / 1000.0
            except (ValueError, TypeError):
                gramaj = 0.0

            pret_unitar = stoc_index.get(ingredient, 0.0)
            total_food_cost += cantitate_vanduta * gramaj * pret_unitar

    return round(total_food_cost, 2)

def calculeaza_cascada(vanzari_brute: float, food_cost: float, cfg: dict) -> dict:
    cota_tva = cfg.get("cota_tva", 0.09)
    chirie = cfg.get("chirie_lunara", 0.0)
    salarii = cfg.get("salarii_lunare", 0.0)
    utilitati = cfg.get("utilitati_lunare", 0.0)
    regim_fiscal = cfg.get("regim_fiscal", "micro1")
    cota_dividend = cfg.get("cota_dividend", 0.08)

    if regim_fiscal == "micro1":
        cota_impozit = 0.01
    elif regim_fiscal == "micro3":
        cota_impozit = 0.03
    else:
        cota_impozit = 0.16

    tva_colectat = vanzari_brute - (vanzari_brute / (1 + cota_tva))
    vanzari_fara_tva = vanzari_brute / (1 + cota_tva)
    cheltuieli_fixe_zilnice = (chirie + salarii + utilitati) / 30.0

    if food_cost == 0.0:
        food_cost_efectiv = vanzari_fara_tva * 0.30
        food_cost_sursa = "estimat (30%)"
    else:
        food_cost_efectiv = food_cost
        food_cost_sursa = "calculat din rețetar"

    profit_brut = vanzari_fara_tva - food_cost_efectiv - cheltuieli_fixe_zilnice
    impozit_firma = max(profit_brut * cota_impozit, 0.0)
    profit_dupa_impozit = profit_brut - impozit_firma
    impozit_dividend = max(profit_dupa_impozit * cota_dividend, 0.0)
    profit_net_real = profit_dupa_impozit - impozit_dividend
    marja_neta = (profit_net_real / vanzari_brute * 100) if vanzari_brute > 0 else 0.0

    return {
        "vanzari_brute": round(vanzari_brute, 2),
        "tva_colectat": round(tva_colectat, 2),
        "vanzari_fara_tva": round(vanzari_fara_tva, 2),
        "cheltuieli_fixe_zilnice": round(cheltuieli_fixe_zilnice, 2),
        "food_cost": round(food_cost_efectiv, 2),
        "food_cost_sursa": food_cost_sursa,
        "profit_brut": round(profit_brut, 2),
        "impozit_firma": round(impozit_firma, 2),
        "profit_dupa_impozit": round(profit_dupa_impozit, 2),
        "impozit_dividend": round(impozit_dividend, 2),
        "profit_net_real": round(profit_net_real, 2),
        "marja_neta": round(marja_neta, 2),
    }

# ─────────────────────────────────────────────
# AI – SCANARE FACTURĂ
# ─────────────────────────────────────────────
def extrage_factura_cu_ai(image_bytes: bytes) -> dict | None:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        img_b64 = base64.b64encode(image_bytes).decode("utf-8")

        prompt = """Ești un sistem de extragere date din facturi fiscale românești.
Analizează imaginea și extrage TOATE produsele de pe factură.
Returnează EXCLUSIV un obiect JSON valid, fără niciun text suplimentar, fără markdown, fără backticks.
Structura obligatorie:
{"produse": [{"produs": "Nume produs", "cantitate": 2.0, "unitate": "kg", "pret_unitar": 15.0}]}
Dacă nu poți extrage un câmp, folosește null pentru text și 0 pentru numere.
Nu adăuga explicații. Răspunde DOAR cu JSON-ul."""

        response = model.generate_content([
            {"mime_type": "image/jpeg", "data": img_b64},
            prompt,
        ])

        raw = response.text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        st.error("AI-ul nu a returnat un JSON valid. Încearcă din nou cu o imagine mai clară.")
        return None
    except Exception as e:
        st.error(f"Eroare AI: {e}")
        return None

# ─────────────────────────────────────────────
# COMPONENTE UI CUSTOM
# ─────────────────────────────────────────────
def card_metric(titlu: str, valoare: str, sub: str = "", badge: str = "", badge_tip: str = "neutru"):
    badge_html = ""
    if badge:
        if badge_tip == "profit":
            badge_color = "#e8f5e9"
            badge_text_color = "#2e7d32"
        elif badge_tip == "pierdere":
            badge_color = "#fce8e8"
            badge_text_color = "#c62828"
        else:
            badge_color = "#eef2f7"
            badge_text_color = "#4a6785"
        badge_html = f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;background:{badge_color};color:{badge_text_color};font-size:0.72rem;font-weight:500;letter-spacing:0.01em;">{badge}</span>'

    sub_html = f'<div style="font-size:0.82rem;color:#8a8a99;margin-top:4px;font-weight:400;">{sub}</div>' if sub else ""

    st.markdown(f"""
    <div style="
        background:#ffffff;
        border-radius:16px;
        border:1px solid #e8e8f0;
        box-shadow:0 2px 8px rgba(0,0,0,0.02);
        padding:1.4rem 1.6rem;
        margin-bottom:0.75rem;
    ">
        <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.6rem;">{titlu}</div>
        <div style="font-size:2.1rem;font-weight:600;color:#1a3a5c;letter-spacing:-0.03em;line-height:1.1;">{valoare}</div>
        {sub_html}
        <div style="margin-top:0.7rem;">{badge_html}</div>
    </div>
    """, unsafe_allow_html=True)

def linie_cascada(eticheta: str, valoare: float, culoare: str = "#0d0d1a", prefix: str = "−"):
    semn = "+" if prefix == "+" else "−"
    val_str = f"{'+ ' if prefix == '+' else '− '}{abs(valoare):,.2f} RON"
    color_val = "#2e7d32" if prefix == "+" else "#c62828" if valoare > 0 else "#8a8a99"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:0.55rem 0;border-bottom:1px solid #f0f0f5;">
        <span style="font-size:0.9rem;color:#4a4a5a;font-weight:400;">{eticheta}</span>
        <span style="font-size:0.9rem;font-weight:500;color:{color_val};font-variant-numeric:tabular-nums;">{val_str}</span>
    </div>
    """, unsafe_allow_html=True)

def bon_fiscal(data: dict, titlu: str = "BON FISCAL"):
    net = data["profit_net_real"]
    marja = data["marja_neta"]
    badge_color = "#e8f5e9" if net >= 0 else "#fce8e8"
    badge_text = "#2e7d32" if net >= 0 else "#c62828"

    st.markdown(f"""
    <div style="
        background:#ffffff;
        border:1px solid #e8e8f0;
        border-radius:16px;
        padding:2rem;
        max-width:420px;
        font-family:'DM Sans',sans-serif;
        box-shadow:0 4px 24px rgba(0,0,0,0.04);
    ">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:0.7rem;font-weight:500;letter-spacing:0.15em;color:#8a8a99;text-transform:uppercase;">{titlu}</div>
            <div style="font-size:0.78rem;color:#c0c0cc;margin-top:4px;">{datetime.now().strftime("%d.%m.%Y · %H:%M")}</div>
        </div>
        <div style="border-top:1px dashed #e8e8f0;border-bottom:1px dashed #e8e8f0;padding:1rem 0;margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>Încasări brute</span><span style="font-weight:500;color:#0d0d1a;">{data["vanzari_brute"]:,.2f} RON</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>TVA colectat</span><span style="color:#c62828;">− {data["tva_colectat"]:,.2f} RON</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>Food Cost</span><span style="color:#c62828;">− {data["food_cost"]:,.2f} RON</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>Cheltuieli fixe</span><span style="color:#c62828;">− {data["cheltuieli_fixe_zilnice"]:,.2f} RON</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>Impozit firmă</span><span style="color:#c62828;">− {data["impozit_firma"]:,.2f} RON</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:0.3rem 0;font-size:0.88rem;color:#4a4a5a;">
                <span>Impozit dividende</span><span style="color:#c62828;">− {data["impozit_dividend"]:,.2f} RON</span>
            </div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;">
            <span style="font-size:1rem;font-weight:600;color:#0d0d1a;">BANI ÎN MÂNĂ</span>
            <span style="font-size:1.6rem;font-weight:700;color:#1a3a5c;letter-spacing:-0.02em;">{net:,.2f} RON</span>
        </div>
        <div style="text-align:right;margin-top:0.5rem;">
            <span style="display:inline-block;padding:4px 12px;border-radius:20px;background:{badge_color};color:{badge_text};font-size:0.78rem;font-weight:500;">
                Marjă netă {marja:.1f}%
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:2rem;padding-bottom:1.5rem;border-bottom:1px solid #ebebf0;">
        <div style="font-size:1.8rem;font-weight:700;color:#0d0d1a;letter-spacing:-0.03em;">◈ Lana</div>
        <div style="font-size:0.68rem;font-weight:500;color:#b0b0be;letter-spacing:0.18em;margin-top:4px;text-transform:uppercase;">ACQ Advisory · Consulting</div>
    </div>
    """, unsafe_allow_html=True)

    sectiune = st.radio(
        "NAVIGARE",
        [
            "📊  Dashboard",
            "⚙️  Setări Fiscale",
            "📄  Scanare Facturi",
            "📥  Vânzări Zilnice",
            "🧪  Simulator Sandbox",
        ],
        label_visibility="visible",
    )

    st.markdown("""
    <div style="margin-top:auto;padding-top:2rem;border-top:1px solid #ebebf0;margin-top:3rem;">
        <div style="font-size:0.72rem;color:#c0c0cc;font-weight:400;">Lana ADVISORY</div>
        <div style="font-size:0.8rem;font-weight:500;color:#8a8a99;margin-top:2px;">79€ / lună</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECȚIUNEA: DASHBOARD
# ─────────────────────────────────────────────
if sectiune == "📊  Dashboard":
    st.markdown('<div class="section-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Situația financiară zilnică · actualizată la ultima închidere</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    stoc_df = citeste_stoc()
    vanzari_df = citeste_vanzari()
    retetar_df = citeste_retetar()

    # Filtrare vânzări pe ziua curentă
    azi = date.today().strftime("%Y-%m-%d")
    if not vanzari_df.empty and "Data" in vanzari_df.columns:
        vanzari_azi = vanzari_df[vanzari_df["Data"].astype(str).str.startswith(azi)]
    else:
        vanzari_azi = pd.DataFrame(columns=["Preparat", "Cantitate_Vanduta", "Data"])

    # Calcul vânzări brute din prețuri în rețetar
    vanzari_brute = 0.0
    if not vanzari_azi.empty and not retetar_df.empty:
        for _, row in vanzari_azi.iterrows():
            preparat = str(row.get("Preparat", "")).lower().strip()
            cantitate = 0.0
            try:
                cantitate = float(row.get("Cantitate_Vanduta", 0))
            except (ValueError, TypeError):
                pass
            pret_match = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == preparat]
            if not pret_match.empty:
                try:
                    pret = float(pret_match.iloc[0].get("Pret_Vanzare", 0))
                    vanzari_brute += cantitate * pret
                except (ValueError, TypeError):
                    pass

    food_cost_zi = calculeaza_food_cost_zilnic(vanzari_azi, retetar_df, stoc_df)
    cascada = calculeaza_cascada(vanzari_brute, food_cost_zi, cfg)

    col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
    with col1:
        marja = cascada["marja_neta"]
        badge_tip = "profit" if cascada["profit_net_real"] >= 0 else "pierdere"
        card_metric(
            "Profit Net Real · Bani în mână",
            f"{cascada['profit_net_real']:,.2f} RON",
            sub=f"Ziua de {azi}",
            badge=f"Marjă {marja:.1f}%",
            badge_tip=badge_tip,
        )
    with col2:
        fc_pct = (cascada["food_cost"] / cascada["vanzari_fara_tva"] * 100) if cascada["vanzari_fara_tva"] > 0 else 0
        card_metric(
            "Food Cost Mediu",
            f"{cascada['food_cost']:,.2f} RON",
            sub=f"{fc_pct:.1f}% din vânzări nete · {cascada['food_cost_sursa']}",
        )
    with col3:
        total_op = cascada["cheltuieli_fixe_zilnice"] + cascada["tva_colectat"] + cascada["impozit_firma"] + cascada["impozit_dividend"]
        card_metric(
            "Cheltuieli Operative Totale",
            f"{total_op:,.2f} RON",
            sub="Taxe + Fixe zilnice",
        )
    with col4:
        plan_html = """
        <div style="background:#ffffff;border-radius:16px;border:1px solid #e8e8f0;
            box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.4rem 1.6rem;height:100%;">
            <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
                text-transform:uppercase;margin-bottom:0.6rem;">Plan Activ</div>
            <div style="font-size:1.1rem;font-weight:600;color:#1a3a5c;">Lana ADVISORY</div>
            <div style="font-size:0.88rem;color:#8a8a99;margin-top:4px;">79€ / lună</div>
            <div style="margin-top:0.9rem;font-size:0.78rem;color:#b0b0be;">Consultant digital de buzunar</div>
        </div>
        """
        st.markdown(plan_html, unsafe_allow_html=True)

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.markdown("""
        <div style="background:#ffffff;border-radius:16px;border:1px solid #e8e8f0;
            box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.6rem 2rem;">
            <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
                text-transform:uppercase;margin-bottom:1.2rem;">Cascada Financiară Zilnică</div>
        """, unsafe_allow_html=True)

        linie_cascada("Încasări brute (cu TVA)", cascada["vanzari_brute"], prefix="+")
        linie_cascada("TVA colectat (→ ANAF)", cascada["tva_colectat"])
        linie_cascada("Food Cost ingrediente", cascada["food_cost"])
        linie_cascada("Cheltuieli fixe zilnice", cascada["cheltuieli_fixe_zilnice"])

        st.markdown("""
        <div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.55rem 0;border-bottom:1px solid #e8e8f0;">
            <span style="font-size:0.9rem;color:#0d0d1a;font-weight:500;">Profit brut operațional</span>
            <span style="font-size:0.9rem;font-weight:600;color:#1a3a5c;">""" + f"{cascada['profit_brut']:,.2f} RON" + """</span>
        </div>""", unsafe_allow_html=True)

        linie_cascada("Impozit firmă", cascada["impozit_firma"])
        linie_cascada("Impozit dividende", cascada["impozit_dividend"])

        net = cascada["profit_net_real"]
        net_color = "#2e7d32" if net >= 0 else "#c62828"
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;
            padding:0.9rem 0;margin-top:0.5rem;">
            <span style="font-size:1rem;font-weight:700;color:#0d0d1a;">◈ Bani în mână (net real)</span>
            <span style="font-size:1.1rem;font-weight:700;color:{net_color};">{net:,.2f} RON</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        if not vanzari_azi.empty:
            st.markdown("""
            <div style="background:#ffffff;border-radius:16px;border:1px solid #e8e8f0;
                box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:1.6rem 2rem;">
                <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
                    text-transform:uppercase;margin-bottom:1rem;">Vânzări de azi</div>
            """, unsafe_allow_html=True)
            for _, row in vanzari_azi.iterrows():
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;
                    padding:0.4rem 0;border-bottom:1px solid #f5f5f8;font-size:0.88rem;">
                    <span style="color:#4a4a5a;">{row.get('Preparat','')}</span>
                    <span style="color:#1a3a5c;font-weight:500;">{row.get('Cantitate_Vanduta',0)} buc</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:#ffffff;border-radius:16px;border:1px solid #e8e8f0;
                box-shadow:0 2px 8px rgba(0,0,0,0.02);padding:2rem;text-align:center;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">📭</div>
                <div style="font-size:0.9rem;color:#8a8a99;">Nicio vânzare înregistrată azi</div>
                <div style="font-size:0.8rem;color:#c0c0cc;margin-top:4px;">Mergi la Vânzări Zilnice pentru a înregistra</div>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SECȚIUNEA: SETĂRI FISCALE
# ─────────────────────────────────────────────
elif sectiune == "⚙️  Setări Fiscale":
    st.markdown('<div class="section-title">Setări Fiscale & Cheltuieli Fixe</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Configurează parametrii fiscali și cheltuielile lunare ale afacerii tale</div>', unsafe_allow_html=True)

    cfg = citeste_config()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
            text-transform:uppercase;margin-bottom:1rem;">Regim Fiscal</div>
        """, unsafe_allow_html=True)

        regim_options = {"Micro 1%": "micro1", "Micro 3%": "micro3", "Profit 16%": "profit16"}
        regim_actual = cfg.get("regim_fiscal", "micro1")
        regim_label_actual = {v: k for k, v in regim_options.items()}.get(regim_actual, "Micro 1%")
        regim_sel = st.selectbox("Regim fiscal", list(regim_options.keys()), index=list(regim_options.keys()).index(regim_label_actual), label_visibility="collapsed")

        tva_options = {"TVA 9% (restaurante)": 0.09, "TVA 19% (standard)": 0.19}
        tva_actual = cfg.get("cota_tva", 0.09)
        tva_label_actual = {v: k for k, v in tva_options.items()}.get(tva_actual, "TVA 9% (restaurante)")
        tva_sel = st.selectbox("Cotă TVA", list(tva_options.keys()), index=list(tva_options.keys()).index(tva_label_actual), label_visibility="collapsed")

        div_options = {"Impozit dividend 8%": 0.08, "Impozit dividend 10%": 0.10}
        div_actual = cfg.get("cota_dividend", 0.08)
        div_label_actual = {v: k for k, v in div_options.items()}.get(div_actual, "Impozit dividend 8%")
        div_sel = st.selectbox("Impozit dividende", list(div_options.keys()), index=list(div_options.keys()).index(div_label_actual), label_visibility="collapsed")

    with col2:
        st.markdown("""
        <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
            text-transform:uppercase;margin-bottom:1rem;">Cheltuieli Lunare Fixe (RON)</div>
        """, unsafe_allow_html=True)

        chirie = st.number_input("Chirie lunară", value=float(cfg.get("chirie_lunara", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        salarii = st.number_input("Salarii totale brute", value=float(cfg.get("salarii_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")
        utilitati = st.number_input("Utilități (curent, gaz, apă)", value=float(cfg.get("utilitati_lunare", 0.0)), min_value=0.0, step=100.0, format="%.2f")

    st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

    nr_clienti = st.number_input(
        "Număr estimat clienți/bonuri pe lună",
        value=int(cfg.get("nr_clienti_lunar", 500)),
        min_value=1, step=10,
    )

    total_fixe = chirie + salarii + utilitati
    regie_per_bon = total_fixe / nr_clienti if nr_clienti > 0 else 0

    st.markdown(f"""
    <div style="background:#f7f7f9;border-radius:12px;padding:1rem 1.4rem;margin:1rem 0;
        border:1px solid #e8e8f0;display:inline-block;">
        <span style="font-size:0.8rem;color:#8a8a99;">Regie fixă per bon: </span>
        <span style="font-family:'DM Mono',monospace;font-size:1.1rem;font-weight:600;
            color:#1a3a5c;letter-spacing:0.02em;">{regie_per_bon:.2f} RON</span>
        <span style="font-size:0.78rem;color:#b0b0be;margin-left:6px;">/ client</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if st.button("Salvează în Config →", type="primary"):
        new_cfg = {
            "regim_fiscal": regim_options[regim_sel],
            "cota_tva": tva_options[tva_sel],
            "cota_dividend": div_options[div_sel],
            "chirie_lunara": chirie,
            "salarii_lunare": salarii,
            "utilitati_lunare": utilitati,
            "nr_clienti_lunar": nr_clienti,
        }
        salveaza_config(new_cfg)
        st.success("✓ Configurația a fost salvată cu succes.")

# ─────────────────────────────────────────────
# SECȚIUNEA: SCANARE FACTURI
# ─────────────────────────────────────────────
elif sectiune == "📄  Scanare Facturi":
    st.markdown('<div class="section-title">Scanare Facturi & Alerte de Preț</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Încarcă o imagine a facturii. AI-ul extrage produsele automat.</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader("Încarcă imagine factură", type=["jpg", "jpeg", "png", "webp"])

    if "produse_factura" not in st.session_state:
        st.session_state.produse_factura = []
    if "alerte_pret" not in st.session_state:
        st.session_state.alerte_pret = []

    if uploaded:
        img_bytes = uploaded.read()
        col_img, col_proc = st.columns([1, 2])
        with col_img:
            image = Image.open(io.BytesIO(img_bytes))
            st.image(image, use_container_width=True, caption="Factura încărcată")

        with col_proc:
            if st.button("🔍 Extrage cu AI"):
                with st.spinner("Gemini analizează factura..."):
                    rezultat = extrage_factura_cu_ai(img_bytes)
                    if rezultat and "produse" in rezultat:
                        st.session_state.produse_factura = rezultat["produse"]
                        st.success(f"✓ {len(rezultat['produse'])} produse identificate.")
                    else:
                        st.session_state.produse_factura = []

    if st.session_state.produse_factura:
        stoc_df = citeste_stoc()
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
            text-transform:uppercase;margin-bottom:1rem;">Produse extrase · Verifică și editează</div>
        """, unsafe_allow_html=True)

        alerte = []
        produse_editate = []
        are_unitati_invalide = False

        for i, prod in enumerate(st.session_state.produse_factura):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    nume = st.text_input("Produs", value=str(prod.get("produs", "")), key=f"pnume_{i}", label_visibility="collapsed")
                with col2:
                    cant = st.number_input("Cantitate", value=float(prod.get("cantitate") or 0), key=f"pcant_{i}", label_visibility="collapsed", min_value=0.0)
                with col3:
                    unitate_ai = str(prod.get("unitate", "")).lower().strip()
                    unitate_invalida = unitate_ai not in UNITATI_CUNOSCUTE
                    unitate = st.text_input(
                        "Unitate",
                        value=unitate_ai if not unitate_invalida else "",
                        key=f"punit_{i}",
                        label_visibility="collapsed",
                        placeholder="kg/g/l/buc" if unitate_invalida else unitate_ai,
                    )
                    if unitate_invalida:
                        st.markdown("""
                        <div style="font-size:0.75rem;color:#e57373;margin-top:2px;">
                            ⚠ Unitate necunoscută · introdu manual
                        </div>""", unsafe_allow_html=True)
                        are_unitati_invalide = True
                    if unitate and unitate.lower().strip() not in UNITATI_CUNOSCUTE:
                        are_unitati_invalide = True
                with col4:
                    pret = st.number_input("Preț/U", value=float(prod.get("pret_unitar") or 0), key=f"ppret_{i}", label_visibility="collapsed", min_value=0.0)

                # Alertă preț
                if not stoc_df.empty and "Produs" in stoc_df.columns:
                    match = stoc_df[stoc_df["Produs"].str.lower().str.strip() == str(nume).lower().strip()]
                    if not match.empty:
                        try:
                            pret_vechi = float(match.iloc[0].get("Pret_Unitar", 0))
                            if pret > pret_vechi and pret_vechi > 0:
                                alerte.append({
                                    "produs": nume,
                                    "pret_vechi": pret_vechi,
                                    "pret_nou": pret,
                                })
                        except (ValueError, TypeError):
                            pass

                produse_editate.append({
                    "Produs": nume,
                    "Cantitate": cant,
                    "Unitate": unitate,
                    "Pret_Unitar": pret,
                    "Data": date.today().strftime("%Y-%m-%d"),
                })

        st.session_state.alerte_pret = alerte

        for alerta in alerte:
            st.markdown(f"""
            <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:12px;
                padding:1rem 1.4rem;margin:0.5rem 0;font-size:0.9rem;">
                ⚠️ <strong>{alerta['produs']}</strong> s-a scumpit de la
                <strong>{alerta['pret_vechi']:.2f}</strong> la
                <strong>{alerta['pret_nou']:.2f} RON</strong>.
                Profitul preparatelor care conțin acest ingredient a scăzut.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        salvare_disabled = are_unitati_invalide
        if salvare_disabled:
            st.markdown("""
            <div style="font-size:0.85rem;color:#e57373;margin-bottom:0.5rem;">
                Completează unitățile lipsă pentru a activa salvarea.
            </div>""", unsafe_allow_html=True)

        btn_col, _ = st.columns([1, 3])
        with btn_col:
            if st.button("Salvează în Stoc →", disabled=salvare_disabled, type="primary"):
                stoc_nou = pd.DataFrame(produse_editate)
                if not stoc_df.empty:
                    # Actualizează sau adaugă
                    for _, row in stoc_nou.iterrows():
                        mask = stoc_df["Produs"].str.lower().str.strip() == str(row["Produs"]).lower().strip()
                        if mask.any():
                            idx = stoc_df[mask].index[0]
                            stoc_df.at[idx, "Cantitate"] = row["Cantitate"]
                            stoc_df.at[idx, "Pret_Unitar"] = row["Pret_Unitar"]
                            stoc_df.at[idx, "Data"] = row["Data"]
                        else:
                            stoc_df = pd.concat([stoc_df, pd.DataFrame([row])], ignore_index=True)
                    salveaza_stoc(stoc_df)
                else:
                    salveaza_stoc(stoc_nou)
                st.success(f"✓ {len(produse_editate)} produse salvate în stoc.")
                st.session_state.produse_factura = []
                st.rerun()

# ─────────────────────────────────────────────
# SECȚIUNEA: VÂNZĂRI ZILNICE
# ─────────────────────────────────────────────
elif sectiune == "📥  Vânzări Zilnice":
    st.markdown('<div class="section-title">Înregistrare Vânzări Zilnice</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Introdu ce ai vândut azi. Stocul se actualizează automat.</div>', unsafe_allow_html=True)

    retetar_df = citeste_retetar()
    stoc_df = citeste_stoc()

    preparate_disponibile = []
    if not retetar_df.empty and "Preparat" in retetar_df.columns:
        preparate_disponibile = sorted(retetar_df["Preparat"].dropna().unique().tolist())

    if "vanzari_zi" not in st.session_state:
        st.session_state.vanzari_zi = [{"preparat": "", "cantitate": 0}]

    def adauga_preparat():
        st.session_state.vanzari_zi.append({"preparat": "", "cantitate": 0})

    if st.button("+ Adaugă preparat"):
        adauga_preparat()

    vanzari_input = []
    for i, item in enumerate(st.session_state.vanzari_zi):
        col1, col2 = st.columns([2, 1])
        with col1:
            if preparate_disponibile:
                prep = st.selectbox(
                    "Preparat",
                    options=["— alege —"] + preparate_disponibile,
                    key=f"vprep_{i}",
                    label_visibility="collapsed",
                )
            else:
                prep = st.text_input("Preparat", value=item.get("preparat", ""), key=f"vprep_{i}", label_visibility="collapsed", placeholder="Nume preparat")
        with col2:
            cant = st.number_input("Cantitate", value=int(item.get("cantitate", 0)), min_value=0, step=1, key=f"vcant_{i}", label_visibility="collapsed")

        if prep and prep != "— alege —":
            vanzari_input.append({"Preparat": prep, "Cantitate_Vanduta": cant})

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    data_inchidere = st.date_input("Data închiderii de zi", value=date.today())

    if st.button("Înregistrează Închiderea de Zi →", type="primary"):
        if not vanzari_input:
            st.warning("Nu ai introdus niciun preparat.")
        else:
            rows_de_salvat = [
                {
                    "Preparat": v["Preparat"],
                    "Cantitate_Vanduta": v["Cantitate_Vanduta"],
                    "Data": data_inchidere.strftime("%Y-%m-%d"),
                }
                for v in vanzari_input
                if v["Cantitate_Vanduta"] > 0
            ]
            salveaza_vanzari(rows_de_salvat)

            # Scade din stoc
            if not retetar_df.empty and not stoc_df.empty:
                stoc_actualizat = stoc_df.copy()
                for v in vanzari_input:
                    preparat = str(v["Preparat"]).lower().strip()
                    cantitate_vanduta = float(v["Cantitate_Vanduta"])
                    ingrediente = retetar_df[retetar_df["Preparat"].str.lower().str.strip() == preparat]
                    for _, irow in ingrediente.iterrows():
                        ingredient = str(irow.get("Ingredient", "")).lower().strip()
                        try:
                            gramaj_kg = float(irow.get("Gramaj", 0)) / 1000.0
                        except (ValueError, TypeError):
                            gramaj_kg = 0.0
                        total_consum = cantitate_vanduta * gramaj_kg
                        mask = stoc_actualizat["Produs"].str.lower().str.strip() == ingredient
                        if mask.any():
                            idx = stoc_actualizat[mask].index[0]
                            cant_curenta = 0.0
                            try:
                                cant_curenta = float(stoc_actualizat.at[idx, "Cantitate"])
                            except (ValueError, TypeError):
                                pass
                            stoc_actualizat.at[idx, "Cantitate"] = max(0, round(cant_curenta - total_consum, 4))
                salveaza_stoc(stoc_actualizat)

            st.success(f"✓ {len(rows_de_salvat)} preparate înregistrate. Stocul a fost actualizat.")
            st.session_state.vanzari_zi = [{"preparat": "", "cantitate": 0}]
            st.rerun()

# ─────────────────────────────────────────────
# SECȚIUNEA: SIMULATOR SANDBOX
# ─────────────────────────────────────────────
elif sectiune == "🧪  Simulator Sandbox":
    st.markdown('<div class="section-title">Simulator Sandbox</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Testează profitabilitatea unui preparat nou înainte de a-l pune în meniu.</div>', unsafe_allow_html=True)

    cfg = citeste_config()
    stoc_df = citeste_stoc()

    produse_stoc = []
    if not stoc_df.empty and "Produs" in stoc_df.columns:
        produse_stoc = sorted(stoc_df["Produs"].dropna().unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        nume_preparat = st.text_input("Nume preparat", placeholder="ex: Burger clasic")
    with col2:
        pret_vanzare = st.number_input("Preț de vânzare dorit (cu TVA) · RON", min_value=0.0, step=0.5, format="%.2f")

    nr_ingrediente = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.78rem;font-weight:500;color:#8a8a99;letter-spacing:0.06em;
        text-transform:uppercase;margin-bottom:0.8rem;">Ingrediente & Gramaje</div>
    """, unsafe_allow_html=True)

    ingrediente_sim = []
    for i in range(int(nr_ingrediente)):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            if produse_stoc:
                ing = st.selectbox("Ingredient", options=["— alege —"] + produse_stoc, key=f"sing_{i}", label_visibility="collapsed")
            else:
                ing = st.text_input("Ingredient", key=f"sing_{i}", label_visibility="collapsed", placeholder="Ingredient")
        with col_b:
            gram = st.number_input("Gramaj (g)", min_value=0.0, step=1.0, key=f"sgram_{i}", label_visibility="collapsed")

        if ing and ing != "— alege —" and gram > 0:
            ingrediente_sim.append({"ingredient": ing, "gramaj_g": gram})

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    if st.button("Calculează Profitabilitatea →", type="primary"):
        if not nume_preparat or pret_vanzare <= 0:
            st.warning("Completează numele preparatului și prețul de vânzare.")
        elif not ingrediente_sim:
            st.warning("Adaugă cel puțin un ingredient cu gramaj.")
        else:
            # Calcul food cost
            food_cost_preparat = 0.0
            stoc_index = {}
            if not stoc_df.empty:
                for _, row in stoc_df.iterrows():
                    key = str(row.get("Produs", "")).lower().strip()
                    try:
                        stoc_index[key] = float(row.get("Pret_Unitar", 0))
                    except (ValueError, TypeError):
                        stoc_index[key] = 0.0

            for item in ingrediente_sim:
                key = str(item["ingredient"]).lower().strip()
                pret_ing = stoc_index.get(key, 0.0)
                gramaj_kg = item["gramaj_g"] / 1000.0
                food_cost_preparat += gramaj_kg * pret_ing

            # Regie fixă per preparat
            nr_clienti = cfg.get("nr_clienti_lunar", 500)
            chirie = cfg.get("chirie_lunara", 0.0)
            salarii = cfg.get("salarii_lunare", 0.0)
            utilitati = cfg.get("utilitati_lunare", 0.0)
            total_fixe = chirie + salarii + utilitati
            regie_per_preparat = total_fixe / float(nr_clienti) if nr_clienti > 0 else 0

            # Cascadă fiscală pentru 1 preparat
            cascada_sim = calculeaza_cascada(
                vanzari_brute=pret_vanzare,
                food_cost=food_cost_preparat + regie_per_preparat,
                cfg=cfg,
            )

            # Override food_cost în cascadă pentru afișare corectă
            cascada_sim["food_cost"] = round(food_cost_preparat, 2)
            cascada_sim["cheltuieli_fixe_zilnice"] = round(regie_per_preparat, 2)

            col_bon, col_rec = st.columns([1, 1])
            with col_bon:
                bon_fiscal(cascada_sim, titlu=f"SIMULARE · {nume_preparat.upper()}")

            with col_rec:
                marja = cascada_sim["marja_neta"]
                net = cascada_sim["profit_net_real"]

                if marja < 10:
                    # Calcul preț recomandat pentru marjă 20%
                    # net_dorit = pret_rec * 0.20
                    # rezolvăm: pret_rec brut astfel încât marja_neta=20%
                    # Aproximare: pret_rec = (food_cost + regie) / (1 - 0.20 - tax_rate)
                    cota_tva = cfg.get("cota_tva", 0.09)
                    cota_div = cfg.get("cota_dividend", 0.08)
                    regim_fiscal = cfg.get("regim_fiscal", "micro1")
                    if regim_fiscal == "micro1":
                        cota_imp = 0.01
                    elif regim_fiscal == "micro3":
                        cota_imp = 0.03
                    else:
                        cota_imp = 0.16

                    total_cost = food_cost_preparat + regie_per_preparat
                    factor_net = (1 - cota_imp) * (1 - cota_div)
                    # pret_fara_tva = total_cost / (factor_net - 0.20 * (1+cota_tva) / (1+cota_tva))
                    # Simplificat:
                    pret_net_necesar = total_cost / (factor_net * 0.8) if factor_net > 0 else total_cost * 2
                    pret_rec = pret_net_necesar * (1 + cota_tva)

                    st.markdown(f"""
                    <div style="background:#fce8e8;border:1px solid #f5c6c6;border-radius:14px;
                        padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#c62828;margin-bottom:0.5rem;">
                            ⚠ Marjă insuficientă ({marja:.1f}%)
                        </div>
                        <div style="font-size:0.88rem;color:#7f1f1f;line-height:1.6;">
                            Ajustează prețul sau reduce ingredientele costisitoare.<br>
                            <strong>Preț recomandat pentru marjă 20%:</strong>
                            <span style="font-size:1.1rem;font-weight:700;"> {pret_rec:.2f} RON</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif marja <= 20:
                    st.markdown(f"""
                    <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:14px;
                        padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#f57f17;margin-bottom:0.5rem;">
                            ℹ Marjă acceptabilă ({marja:.1f}%)
                        </div>
                        <div style="font-size:0.88rem;color:#795700;line-height:1.6;">
                            Există loc de optimizare a costurilor. Încearcă să reduci gramajele
                            sau să cauți furnizori mai competitivi pentru ingredientele cheie.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:14px;
                        padding:1.5rem;margin-top:1rem;">
                        <div style="font-size:1rem;font-weight:600;color:#2e7d32;margin-bottom:0.5rem;">
                            ✓ Marjă excelentă ({marja:.1f}%)
                        </div>
                        <div style="font-size:0.88rem;color:#1b5e20;line-height:1.6;">
                            Preparatul este viabil comercial. Poți să-l introduci cu încredere în meniu.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background:#ffffff;border:1px solid #e8e8f0;border-radius:14px;
                    padding:1.2rem 1.5rem;font-size:0.85rem;">
                    <div style="color:#8a8a99;font-size:0.72rem;letter-spacing:0.06em;
                        text-transform:uppercase;margin-bottom:0.8rem;">Detalii calcul</div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;">
                        <span>Food cost ingrediente</span>
                        <span style="font-weight:500;">{food_cost_preparat:.2f} RON</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;">
                        <span>Regie fixă / client</span>
                        <span style="font-weight:500;">{regie_per_preparat:.2f} RON</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;padding:3px 0;color:#4a4a5a;">
                        <span>Preț vânzare (cu TVA)</span>
                        <span style="font-weight:500;">{pret_vanzare:.2f} RON</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
