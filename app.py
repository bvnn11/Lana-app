"""
LANA — Motor de Profitabilitate pentru Restaurante
Divizia ACQ Advisory
Cod complet, gata de deployment pe Streamlit Cloud.
"""
import subprocess
import sys
import os

# 1. Forțăm instalarea modulelor lipsă direct în sistemul Streamlit la prima rulare
try:
    import gspread
    import google.generativeai
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gspread", "google-auth", "google-generativeai", "pandas", "Pillow"])

# 2. Toate importurile unice de care are nevoie aplicația ca să meargă, scrise o singură dată:
import streamlit as st
import pandas as pd
import json
import base64
import io
from google.oauth2.service_account import Credentials
import google.generativeai as genai
from datetime import datetime

# ──────────────────────────────────────────────
# CONFIGURARE PAGINĂ & CSS GLOBAL
# ──────────────────────────────────────────────
# (De aici încolo continuă codul tău normal...)


# CSS global — estetică Apple / Minimalist Premium
st.markdown("""
<style>
  /* Import fonturi premium */
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Mono:wght@300;400&display=swap');

  /* Reset global */
  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #1a1a2e;
  }

  /* Fundal aplicație */
  .stApp {
    background-color: #f7f7f9;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #ebebf0;
  }
  [data-testid="stSidebar"] * {
    color: #1a1a2e !important;
  }
  [data-testid="stSidebarNav"] a {
    border-radius: 10px;
    padding: 8px 14px;
    transition: background 0.2s;
  }
  [data-testid="stSidebarNav"] a:hover {
    background: #f0f0f6;
  }

  /* ── Titluri ── */
  h1, h2, h3 {
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #0d0d1a;
  }

  /* ── Carduri metrice mari ── */
  .metric-card {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-radius: 20px;
    padding: 32px 28px;
    text-align: left;
    box-shadow: 0 2px 12px rgba(0,0,10,0.04);
    transition: box-shadow 0.25s;
    height: 100%;
  }
  .metric-card:hover {
    box-shadow: 0 6px 24px rgba(0,0,10,0.08);
  }
  .metric-label {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8888a0;
    margin-bottom: 12px;
  }
  .metric-value {
    font-size: 42px;
    font-weight: 600;
    color: #0d0d1a;
    letter-spacing: -0.03em;
    line-height: 1;
  }
  .metric-value-accent {
    font-size: 42px;
    font-weight: 600;
    color: #1a3a5c;
    letter-spacing: -0.03em;
    line-height: 1;
  }
  .metric-sub {
    font-size: 13px;
    color: #aaaabc;
    margin-top: 8px;
  }
  .metric-badge-green {
    display: inline-block;
    background: #e8f5e9;
    color: #2e7d32;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 10px;
  }
  .metric-badge-red {
    display: inline-block;
    background: #fce8e8;
    color: #c62828;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 500;
    margin-top: 10px;
  }

  /* ── Logo & brand sidebar ── */
  .brand-block {
    padding: 24px 20px 16px 20px;
    border-bottom: 1px solid #f0f0f5;
    margin-bottom: 8px;
  }
  .brand-name {
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #0d0d1a;
  }
  .brand-sub {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9999b0;
    margin-top: 2px;
  }

  /* ── Secțiuni ── */
  .section-header {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9999b0;
    margin: 28px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #f0f0f5;
  }

  /* ── Input fields ── */
  .stTextInput > div > div > input,
  .stNumberInput > div > div > input,
  .stSelectbox > div > div > select {
    border-radius: 10px !important;
    border: 1px solid #e0e0ea !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    background: #ffffff !important;
    color: #1a1a2e !important;
  }
  .stTextInput > div > div > input:focus,
  .stNumberInput > div > div > input:focus {
    border-color: #1a3a5c !important;
    box-shadow: 0 0 0 3px rgba(26,58,92,0.08) !important;
  }

  /* ── Butoane principale ── */
  .stButton > button {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    padding: 10px 22px !important;
    background-color: #1a3a5c !important;
    color: #ffffff !important;
    border: none !important;
    transition: background 0.2s, box-shadow 0.2s !important;
  }
  .stButton > button:hover {
    background-color: #0d2540 !important;
    box-shadow: 0 4px 14px rgba(26,58,92,0.25) !important;
  }

  /* ── Alertă factură ── */
  .alert-validation {
    border: 1.5px solid #e53935;
    background: #fff5f5;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 13px;
    color: #c62828;
    margin: 10px 0;
  }

  /* ── Rezultat Simulator ── */
  .result-box {
    background: #ffffff;
    border: 1px solid #e8e8f0;
    border-radius: 20px;
    padding: 36px 32px;
    text-align: center;
    box-shadow: 0 2px 18px rgba(0,0,10,0.05);
    margin-top: 20px;
  }
  .result-main {
    font-size: 48px;
    font-weight: 700;
    color: #1a3a5c;
    letter-spacing: -0.04em;
    line-height: 1;
  }
  .result-marja {
    font-size: 18px;
    color: #6666880;
    margin-top: 10px;
    font-weight: 400;
  }
  .result-label {
    font-size: 13px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #aaaabc;
    margin-bottom: 16px;
    font-weight: 500;
  }
  .result-breakdown {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #8888a0;
    margin-top: 20px;
    text-align: left;
    background: #f7f7f9;
    border-radius: 12px;
    padding: 16px;
    line-height: 1.9;
  }

  /* ── Divider ── */
  hr {
    border: none;
    border-top: 1px solid #f0f0f5;
    margin: 24px 0;
  }

  /* ── Tabele ── */
  .stDataFrame {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid #e8e8f0 !important;
  }

  /* ── Ascunde elemente Streamlit implicite ── */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# CONSTANTE & CONEXIUNE GOOGLE SHEETS
# ──────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(show_spinner=False)
def conecteaza_gsheets():
    """Conectare la Google Sheets prin Service Account din st.secrets."""
    credentiale_dict = st.secrets["gcp_service_account"]
    credentiale = Credentials.from_service_account_info(
        credentiale_dict, scopes=SCOPES
    )
    client = gspread.authorize(credentiale)
    spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
    return spreadsheet


def citeste_foaie(spreadsheet, nume_foaie: str) -> pd.DataFrame:
    """Citește o foaie din Google Sheets și returnează DataFrame."""
    try:
        foaie = spreadsheet.worksheet(nume_foaie)
        date = foaie.get_all_records()
        return pd.DataFrame(date)
    except Exception as e:
        st.error(f"Eroare la citirea foii '{nume_foaie}': {e}")
        return pd.DataFrame()


def scrie_rand(spreadsheet, nume_foaie: str, rand: list):
    """Adaugă un rând nou în foaia specificată."""
    try:
        foaie = spreadsheet.worksheet(nume_foaie)
        foaie.append_row(rand, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Eroare la scrierea în foaia '{nume_foaie}': {e}")
        return False


def actualizeaza_config(spreadsheet, cheie: str, valoare):
    """Actualizează o valoare în foaia Config (structură cheie-valoare)."""
    try:
        foaie = spreadsheet.worksheet("Config")
        celule = foaie.findall(cheie)
        if celule:
            foaie.update_cell(celule[0].row, 2, valoare)
        else:
            foaie.append_row([cheie, valoare])
        return True
    except Exception as e:
        st.error(f"Eroare la actualizarea config '{cheie}': {e}")
        return False


def citeste_config(spreadsheet) -> dict:
    """Citește toate configurările din foaia Config ca dicționar."""
    try:
        foaie = spreadsheet.worksheet("Config")
        date = foaie.get_all_records()
        return {rand.get("Cheie", rand.get("cheie", "")): rand.get("Valoare", rand.get("valoare", "")) for rand in date}
    except Exception:
        return {}


# ──────────────────────────────────────────────
# FUNCȚII CALCUL PROFITABILITATE
# ──────────────────────────────────────────────

def calculeaza_food_cost(retete: pd.DataFrame, stoc: pd.DataFrame) -> float:
    """
    Calculează food cost-ul mediu ponderat pe baza rețetelor și prețurilor din stoc.
    Returnează procentul food cost față de prețul de vânzare.
    """
    if retete.empty or stoc.empty:
        return 0.0

    coloane_reteta = [c.lower() for c in retete.columns]
    coloane_stoc = [c.lower() for c in stoc.columns]

    # Verificăm că avem coloanele necesare
    if not all(c in coloane_reteta for c in ["preparat", "ingredient", "gramaj", "pret_vanzare"]):
        return 0.0
    if not all(c in coloane_stoc for c in ["produs", "pret_unitar", "unitate"]):
        return 0.0

    # Normalizăm coloanele
    retete.columns = [c.lower() for c in retete.columns]
    stoc.columns = [c.lower() for c in stoc.columns]

    total_cost = 0.0
    total_vanzari = 0.0

    for preparat in retete["preparat"].unique():
        ingrediente_preparat = retete[retete["preparat"] == preparat]
        pret_vanzare = ingrediente_preparat["pret_vanzare"].iloc[0]
        cost_preparat = 0.0

        for _, ingredient_row in ingrediente_preparat.iterrows():
            ingredient_stoc = stoc[stoc["produs"] == ingredient_row["ingredient"]]
            if not ingredient_stoc.empty:
                pret_per_unitate = ingredient_stoc["pret_unitar"].iloc[0]
                gramaj = ingredient_row["gramaj"]
                cost_preparat += (gramaj / 1000) * pret_per_unitate

        total_cost += cost_preparat
        total_vanzari += pret_vanzare

    if total_vanzari == 0:
        return 0.0

    return round((total_cost / total_vanzari) * 100, 2)


def calculeaza_profit_net(vanzari_brute: float, config: dict) -> dict:
    """
    Calculează profitul net complet după toate deducerile fiscale și operative.
    Returnează un dicționar cu toate componentele de cost.
    """
    # Parametri fiscali din config
    tip_impozit = config.get("tip_impozit", "Micro 1%")
    cota_tva_str = config.get("cota_tva", "9%")
    impozit_dividend_str = config.get("impozit_dividend", "8%")
    chirie = float(config.get("chirie", 0))
    salarii = float(config.get("salarii", 0))
    utilitati = float(config.get("utilitati", 0))
    nr_clienti = float(config.get("nr_clienti", 1))

    # Conversii rate
    cota_tva = float(str(cota_tva_str).replace("%", "")) / 100
    cota_dividend = float(str(impozit_dividend_str).replace("%", "")) / 100

    if "1%" in str(tip_impozit):
        cota_firma = 0.01
    elif "3%" in str(tip_impozit):
        cota_firma = 0.03
    else:
        cota_firma = 0.16

    # Calcule secvențiale
    tva_colectat = vanzari_brute - (vanzari_brute / (1 + cota_tva))
    vanzari_fara_tva = vanzari_brute / (1 + cota_tva)
    cheltuieli_fixe_totale = chirie + salarii + utilitati
    food_cost_estimat = vanzari_fara_tva * 0.30  # estimare 30% dacă nu avem rețete
    profit_brut = vanzari_fara_tva - food_cost_estimat - cheltuieli_fixe_totale
    impozit_firma = max(profit_brut * cota_firma, 0)
    profit_dupa_firma = profit_brut - impozit_firma
    impozit_div = max(profit_dupa_firma * cota_dividend, 0)
    profit_net = profit_dupa_firma - impozit_div

    return {
        "vanzari_brute": vanzari_brute,
        "tva_colectat": round(tva_colectat, 2),
        "vanzari_fara_tva": round(vanzari_fara_tva, 2),
        "food_cost": round(food_cost_estimat, 2),
        "cheltuieli_fixe": round(cheltuieli_fixe_totale, 2),
        "profit_brut": round(profit_brut, 2),
        "impozit_firma": round(impozit_firma, 2),
        "profit_dupa_firma": round(profit_dupa_firma, 2),
        "impozit_dividend": round(impozit_div, 2),
        "profit_net": round(profit_net, 2),
        "marja_neta": round((profit_net / vanzari_brute * 100) if vanzari_brute > 0 else 0, 2),
    }


# ──────────────────────────────────────────────
# OCR FACTURI VIA GEMINI AI
# ──────────────────────────────────────────────

UNITATI_CUNOSCUTE = {"kg", "g", "l", "ml", "buc", "bucata", "bucăți", "litri", "grame", "kilograme"}

def extrage_factura_cu_ai(imagine_bytes: bytes, mime_type: str) -> list[dict]:
    """
    Trimite imaginea facturii la Gemini 1.5 Flash și extrage produsele.
    Returnează o listă de dicționare cu câmpurile necesare.
    """
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = """Ești un asistent specializat în extragerea datelor din facturi pentru restaurante din România.
Analizează această imagine de factură și extrage TOATE produsele/ingredientele.
Returnează STRICT un JSON valid (fără text suplimentar, fără markdown) cu structura:
{
  "produse": [
    {
      "produs": "Denumire produs",
      "cantitate": 5.0,
      "unitate": "kg",
      "pret_unitar": 12.50
    }
  ]
}
Dacă nu poți identifica cu certitudine unitatea de măsură, folosește "NECUNOSCUT".
Prețul unitar trebuie să fie fără TVA dacă e posibil de identificat."""

    imagine_part = {
        "mime_type": mime_type,
        "data": base64.b64encode(imagine_bytes).decode("utf-8"),
    }

    try:
        raspuns = model.generate_content([prompt, imagine_part])
        text_raspuns = raspuns.text.strip()
        # Curățăm eventuale backtick-uri markdown
        text_raspuns = text_raspuns.replace("```json", "").replace("```", "").strip()
        date = json.loads(text_raspuns)
        return date.get("produse", [])
    except json.JSONDecodeError:
        st.error("AI-ul nu a returnat un JSON valid. Te rugăm să reîncerci.")
        return []
    except Exception as e:
        st.error(f"Eroare Gemini API: {e}")
        return []


# ──────────────────────────────────────────────
# CALCUL SIMULATOR SANDBOX
# ──────────────────────────────────────────────

def calculeaza_simulator(
    pret_vanzare: float,
    ingrediente: list[dict],
    stoc: pd.DataFrame,
    config: dict,
) -> dict:
    """
    Calculează profitul net real pentru un preparat nou simulat.
    Scade TVA, Food Cost, Regie Fixă per produs, Impozit firmă, Impozit dividend.
    """
    # Parametri fiscali
    cota_tva = float(str(config.get("cota_tva", "9%")).replace("%", "")) / 100
    cota_dividend = float(str(config.get("impozit_dividend", "8%")).replace("%", "")) / 100
    tip_impozit = config.get("tip_impozit", "Micro 1%")
    nr_clienti = float(config.get("nr_clienti", 1)) or 1
    chirie = float(config.get("chirie", 0))
    salarii = float(config.get("salarii", 0))
    utilitati = float(config.get("utilitati", 0))

    if "1%" in str(tip_impozit):
        cota_firma = 0.01
    elif "3%" in str(tip_impozit):
        cota_firma = 0.03
    else:
        cota_firma = 0.16

    cheltuieli_fixe_totale = chirie + salarii + utilitati
    regie_per_produs = cheltuieli_fixe_totale / nr_clienti

    # TVA
    tva = pret_vanzare - (pret_vanzare / (1 + cota_tva))
    pret_fara_tva = pret_vanzare / (1 + cota_tva)

    # Food Cost din ingrediente
    food_cost_total = 0.0
    stoc_lower = stoc.copy()
    if not stoc_lower.empty:
        stoc_lower.columns = [c.lower() for c in stoc_lower.columns]

    for ing in ingrediente:
        if not stoc_lower.empty and "produs" in stoc_lower.columns:
            potrivire = stoc_lower[stoc_lower["produs"].str.lower() == ing["produs"].lower()]
            if not potrivire.empty:
                pret_ing = float(potrivire["pret_unitar"].iloc[0])
                gramaj_kg = ing["gramaj"] / 1000
                food_cost_total += pret_ing * gramaj_kg

    # Calcul cascadă
    profit_dupa_food = pret_fara_tva - food_cost_total
    profit_dupa_regie = profit_dupa_food - regie_per_produs
    impozit_firma = max(profit_dupa_regie * cota_firma, 0)
    profit_dupa_firma = profit_dupa_regie - impozit_firma
    impozit_div = max(profit_dupa_firma * cota_dividend, 0)
    profit_net = profit_dupa_firma - impozit_div
    marja = (profit_net / pret_vanzare * 100) if pret_vanzare > 0 else 0

    return {
        "pret_vanzare": round(pret_vanzare, 2),
        "tva": round(tva, 2),
        "pret_fara_tva": round(pret_fara_tva, 2),
        "food_cost": round(food_cost_total, 2),
        "regie_per_produs": round(regie_per_produs, 2),
        "profit_dupa_regie": round(profit_dupa_regie, 2),
        "impozit_firma": round(impozit_firma, 2),
        "profit_dupa_firma": round(profit_dupa_firma, 2),
        "impozit_dividend": round(impozit_div, 2),
        "profit_net": round(profit_net, 2),
        "marja_neta": round(marja, 2),
    }


# ──────────────────────────────────────────────
# SIDEBAR — NAVIGARE & BRAND
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="brand-block">
        <div class="brand-name">◈ Lana</div>
        <div class="brand-sub">ACQ Advisory · Profitabilitate</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Navigare</div>', unsafe_allow_html=True)

    pagina = st.radio(
        label="Secțiune",
        options=[
            "📊  Dashboard",
            "⚙️  Setup Fiscal",
            "💰  Cheltuieli Fixe",
            "📄  Scanare Facturi",
            "🧪  Simulator Sandbox",
        ],
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:12px; color:#8888a0;">Conectat · {datetime.now().strftime("%d %b %Y, %H:%M")}</div>',
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# INIȚIALIZARE CONEXIUNE
# ──────────────────────────────────────────────

try:
    spreadsheet = conecteaza_gsheets()
    conexiune_ok = True
except Exception as e:
    conexiune_ok = False
    st.error(f"⚠️ Nu s-a putut conecta la Google Sheets: {e}")


# ──────────────────────────────────────────────
# PAGINA: DASHBOARD
# ──────────────────────────────────────────────

if "📊" in pagina:
    st.markdown("## Dashboard")
    st.markdown('<div style="color:#9999b0; margin-top:-8px; margin-bottom:28px; font-size:14px;">Imagine financiară în timp real</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        df_vanzari = citeste_foaie(spreadsheet, "Vanzari")
        df_retete = citeste_foaie(spreadsheet, "Retetar")
        df_stoc = citeste_foaie(spreadsheet, "Stoc")

        # Calcul vânzări totale
        vanzari_totale = 0.0
        if not df_vanzari.empty:
            coloane_v = [c.lower() for c in df_vanzari.columns]
            df_vanzari.columns = [c.lower() for c in df_vanzari.columns]
            if "valoare" in coloane_v:
                vanzari_totale = float(df_vanzari["valoare"].sum())
            elif "total" in coloane_v:
                vanzari_totale = float(df_vanzari["total"].sum())

        # Calcul indicatori
        rezultate = calculeaza_profit_net(vanzari_totale, config)
        food_cost_pct = calculeaza_food_cost(df_retete, df_stoc)
        cheltuieli_fixe = float(config.get("chirie", 0)) + float(config.get("salarii", 0)) + float(config.get("utilitati", 0))

        profit_net = rezultate["profit_net"]
        marja = rezultate["marja_neta"]

        # ── Carduri metrice principale ──
        col1, col2, col3 = st.columns(3)

        with col1:
            badge_profit = "metric-badge-green" if profit_net >= 0 else "metric-badge-red"
            semn = "+" if profit_net >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Profit Net Real</div>
                <div class="metric-value-accent">{profit_net:,.0f} <span style="font-size:22px;font-weight:400">RON</span></div>
                <div class="metric-sub">Bani efectiv în mână, după toate taxele</div>
                <div class="{badge_profit}">{semn}{marja}% marjă netă</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            fc_badge = "metric-badge-green" if food_cost_pct <= 30 else "metric-badge-red"
            fc_label = "Optim ≤30%" if food_cost_pct <= 30 else "Atenție >30%"
            display_fc = food_cost_pct if food_cost_pct > 0 else "—"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Food Cost Mediu</div>
                <div class="metric-value">{display_fc}<span style="font-size:22px;font-weight:400"> %</span></div>
                <div class="metric-sub">Calculat din rețetar și stoc curent</div>
                <div class="{fc_badge}">{fc_label}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Cheltuieli Operative Totale</div>
                <div class="metric-value">{cheltuieli_fixe:,.0f} <span style="font-size:22px;font-weight:400">RON</span></div>
                <div class="metric-sub">Chirie + Salarii + Utilități / lună</div>
                <div style="margin-top:10px; font-size:12px; color:#aaaabc;">Vânzări brute: {vanzari_totale:,.0f} RON</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Defalcare financiară ──
        st.markdown('<div class="section-header" style="margin-top:36px;">Defalcare Financiară</div>', unsafe_allow_html=True)

        col_a, col_b = st.columns([2, 1])
        with col_a:
            defalcare = {
                "Component": ["Vânzări Brute", "TVA Colectat", "Food Cost (~30%)", "Cheltuieli Fixe", "Impozit Firmă", "Impozit Dividend", "Profit Net"],
                "Valoare (RON)": [
                    f"{rezultate['vanzari_brute']:,.2f}",
                    f"−{rezultate['tva_colectat']:,.2f}",
                    f"−{rezultate['food_cost']:,.2f}",
                    f"−{rezultate['cheltuieli_fixe']:,.2f}",
                    f"−{rezultate['impozit_firma']:,.2f}",
                    f"−{rezultate['impozit_dividend']:,.2f}",
                    f"= {rezultate['profit_net']:,.2f}",
                ],
            }
            df_defalcare = pd.DataFrame(defalcare)
            st.dataframe(df_defalcare, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown(f"""
            <div class="metric-card" style="margin-top:0">
                <div class="metric-label">Configurare Fiscală Activă</div>
                <div style="font-size:13px; color:#555; line-height:2;">
                    <b>Impozit firmă:</b> {config.get('tip_impozit', '—')}<br>
                    <b>TVA:</b> {config.get('cota_tva', '—')}<br>
                    <b>Dividend:</b> {config.get('impozit_dividend', '—')}<br>
                    <b>Clienți/lună:</b> {config.get('nr_clienti', '—')}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# PAGINA: SETUP FISCAL
# ──────────────────────────────────────────────

elif "⚙️" in pagina:
    st.markdown("## Setup Fiscal")
    st.markdown('<div style="color:#9999b0; margin-top:-8px; margin-bottom:28px; font-size:14px;">Parametri fiscali conform legislației din România</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)

        with st.container():
            st.markdown('<div class="section-header">Regim Fiscal</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                optiuni_impozit = ["Micro 1%", "Micro 3%", "Profit 16%"]
                val_curenta_imp = config.get("tip_impozit", "Micro 1%")
                idx_imp = optiuni_impozit.index(val_curenta_imp) if val_curenta_imp in optiuni_impozit else 0
                tip_impozit = st.selectbox(
                    "Tip Impozit pe Venit",
                    options=optiuni_impozit,
                    index=idx_imp,
                    help="Micro 1% — firmă cu un singur angajat cel puțin. Micro 3% — altfel. Profit 16% — firmă obișnuită.",
                )

            with col2:
                optiuni_tva = ["9%", "19%"]
                val_curenta_tva = str(config.get("cota_tva", "9%"))
                idx_tva = optiuni_tva.index(val_curenta_tva) if val_curenta_tva in optiuni_tva else 0
                cota_tva = st.selectbox(
                    "Cotă TVA Aplicabilă",
                    options=optiuni_tva,
                    index=idx_tva,
                    help="9% pentru produse alimentare de bază. 19% pentru servicii de restaurant cu alcool sau alte servicii.",
                )

            with col3:
                optiuni_div = ["8%", "10%"]
                val_curenta_div = str(config.get("impozit_dividend", "8%"))
                idx_div = optiuni_div.index(val_curenta_div) if val_curenta_div in optiuni_div else 0
                impozit_div = st.selectbox(
                    "Impozit pe Dividend",
                    options=optiuni_div,
                    index=idx_div,
                    help="8% conform legislației curente pentru dividendele distribuite de microîntreprinderi.",
                )

            st.markdown('<hr>', unsafe_allow_html=True)

            if st.button("Salvează Configurarea Fiscală"):
                ok1 = actualizeaza_config(spreadsheet, "tip_impozit", tip_impozit)
                ok2 = actualizeaza_config(spreadsheet, "cota_tva", cota_tva)
                ok3 = actualizeaza_config(spreadsheet, "impozit_dividend", impozit_div)
                if ok1 and ok2 and ok3:
                    st.success("✓ Configurarea fiscală a fost salvată cu succes.")
                    st.cache_resource.clear()


# ──────────────────────────────────────────────
# PAGINA: CHELTUIELI FIXE
# ──────────────────────────────────────────────

elif "💰" in pagina:
    st.markdown("## Cheltuieli Fixe")
    st.markdown('<div style="color:#9999b0; margin-top:-8px; margin-bottom:28px; font-size:14px;">Costuri operative lunare și volum estimat</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)

        st.markdown('<div class="section-header">Costuri Lunare (RON)</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            chirie = st.number_input(
                "Chirie lunară",
                min_value=0.0,
                value=float(config.get("chirie", 0)),
                step=100.0,
                format="%.0f",
                help="Suma lunară plătită pentru spațiu (RON, fără TVA)",
            )

            salarii = st.number_input(
                "Salarii totale brute + taxe angajator",
                min_value=0.0,
                value=float(config.get("salarii", 0)),
                step=100.0,
                format="%.0f",
                help="Total cheltuieli cu personalul, inclusiv CAS, CASS angajator (RON)",
            )

        with col2:
            utilitati = st.number_input(
                "Utilități (curent, apă, gaz, internet)",
                min_value=0.0,
                value=float(config.get("utilitati", 0)),
                step=50.0,
                format="%.0f",
                help="Total utilități estimate pe lună (RON)",
            )

            nr_clienti = st.number_input(
                "Număr clienți / vânzări estimate pe lună",
                min_value=1,
                value=int(config.get("nr_clienti", 100)),
                step=10,
                help="Numărul de bonuri/comenzi estimate pe lună — folosit pentru calculul regiei per produs",
            )

        st.markdown('<hr>', unsafe_allow_html=True)

        # Calcul instant al regiei per client
        total_fixe = chirie + salarii + utilitati
        regie_per_client = total_fixe / nr_clienti if nr_clienti > 0 else 0

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total Cheltuieli Fixe", f"{total_fixe:,.0f} RON")
        col_b.metric("Nr. Clienți/Lună", f"{nr_clienti:,}")
        col_c.metric("Regie per Bon/Produs", f"{regie_per_client:,.2f} RON")

        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

        if st.button("Salvează Cheltuielile Fixe"):
            ok1 = actualizeaza_config(spreadsheet, "chirie", chirie)
            ok2 = actualizeaza_config(spreadsheet, "salarii", salarii)
            ok3 = actualizeaza_config(spreadsheet, "utilitati", utilitati)
            ok4 = actualizeaza_config(spreadsheet, "nr_clienti", nr_clienti)
            if ok1 and ok2 and ok3 and ok4:
                st.success("✓ Cheltuielile fixe au fost salvate cu succes.")
                st.cache_resource.clear()


# ──────────────────────────────────────────────
# PAGINA: SCANARE FACTURI (AI OCR)
# ──────────────────────────────────────────────

elif "📄" in pagina:
    st.markdown("## Scanare Facturi")
    st.markdown('<div style="color:#9999b0; margin-top:-8px; margin-bottom:28px; font-size:14px;">Extragere automată a datelor din facturi prin AI (Gemini 1.5 Flash)</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        st.markdown('<div class="section-header">Încarcă Fotografie Factură</div>', unsafe_allow_html=True)

        fisier_incarcat = st.file_uploader(
            "Selectează o imagine (JPG, PNG, WEBP) sau PDF",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
            help="Fă o poză clară facturii de la furnizori și încarcă-o aici.",
            label_visibility="collapsed",
        )

        if fisier_incarcat is not None:
            # Afișăm preview imagine
            if fisier_incarcat.type.startswith("image"):
                st.image(fisier_incarcat, caption="Previzualizare factură", width=400)

            if st.button("🔍 Analizează Factura cu AI"):
                with st.spinner("Gemini analizează factura..."):
                    bytes_fisier = fisier_incarcat.read()
                    mime = fisier_incarcat.type if fisier_incarcat.type else "image/jpeg"
                    produse_extrase = extrage_factura_cu_ai(bytes_fisier, mime)

                if produse_extrase:
                    # Salvăm în session state pentru validare
                    st.session_state["produse_factura"] = produse_extrase
                    st.success(f"✓ AI a identificat {len(produse_extrase)} produs(e) în factură.")
                else:
                    st.warning("Nu s-au putut extrage produse. Verifică claritatea imaginii și reîncearcă.")

        # ── Afișare și validare produse extrase ──
        if "produse_factura" in st.session_state and st.session_state["produse_factura"]:
            st.markdown('<div class="section-header">Produse Extrase — Validare</div>', unsafe_allow_html=True)

            produse = st.session_state["produse_factura"]
            are_erori = False
            produse_validate = []

            for i, produs in enumerate(produse):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1.5, 2, 2])

                    with col1:
                        nume = st.text_input(
                            "Produs",
                            value=produs.get("produs", ""),
                            key=f"produs_{i}",
                            label_visibility="collapsed" if i > 0 else "visible",
                        )
                    with col2:
                        cantitate = st.number_input(
                            "Cantitate",
                            value=float(produs.get("cantitate", 0)),
                            min_value=0.0,
                            step=0.1,
                            key=f"cant_{i}",
                            label_visibility="collapsed" if i > 0 else "visible",
                        )
                    with col3:
                        unitate_raw = produs.get("unitate", "NECUNOSCUT")
                        unitate_valid = unitate_raw.lower().strip() in UNITATI_CUNOSCUTE

                        if not unitate_valid:
                            are_erori = True
                            st.markdown(f"""
                            <div class="alert-validation">
                                ⚠️ Unitate necunoscută detectată: <b>"{unitate_raw}"</b>. Completează manual.
                            </div>
                            """, unsafe_allow_html=True)
                            unitate = st.text_input(
                                "Unitate Măsură",
                                value="",
                                key=f"um_{i}",
                                placeholder="ex: kg, g, l, buc",
                            )
                        else:
                            unitate = st.text_input(
                                "Unitate Măsură",
                                value=unitate_raw,
                                key=f"um_{i}",
                                label_visibility="collapsed" if i > 0 else "visible",
                            )

                    with col4:
                        pret = st.number_input(
                            "Preț Unitar (RON)",
                            value=float(produs.get("pret_unitar", 0)),
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"pret_{i}",
                            label_visibility="collapsed" if i > 0 else "visible",
                        )

                    # Verificăm dacă unitățile completate manual sunt valide
                    unitate_finala = st.session_state.get(f"um_{i}", unitate)
                    if unitate_finala and unitate_finala.lower().strip() not in UNITATI_CUNOSCUTE and not unitate_valid:
                        are_erori = True

                    produse_validate.append({
                        "produs": st.session_state.get(f"produs_{i}", nume),
                        "cantitate": cantitate,
                        "unitate": unitate_finala or unitate,
                        "pret_unitar": pret,
                    })

            st.markdown('<hr>', unsafe_allow_html=True)

            # Buton salvare — blocat dacă sunt erori
            if are_erori:
                st.markdown("""
                <div class="alert-validation">
                    Salvarea este blocată până când toate unitățile de măsură necunoscute sunt completate corect.<br>
                    Unități acceptate: <b>kg, g, l, ml, buc, bucata, bucăți, litri, grame, kilograme</b>
                </div>
                """, unsafe_allow_html=True)
                st.button("Salvează în Stoc", disabled=True)
            else:
                if st.button("✓ Salvează în Stoc"):
                    with st.spinner("Salvând în Google Sheets..."):
                        succes = True
                        for p in produse_validate:
                            rand = [
                                p["produs"],
                                p["cantitate"],
                                p["unitate"],
                                p["pret_unitar"],
                                datetime.now().strftime("%Y-%m-%d"),
                            ]
                            if not scrie_rand(spreadsheet, "Stoc", rand):
                                succes = False
                    if succes:
                        st.success(f"✓ {len(produse_validate)} produs(e) salvate în foaia Stoc.")
                        del st.session_state["produse_factura"]
                    else:
                        st.error("Eroare la salvarea în Stoc. Verifică conexiunea.")


# ──────────────────────────────────────────────
# PAGINA: SIMULATOR SANDBOX
# ──────────────────────────────────────────────

elif "🧪" in pagina:
    st.markdown("## Simulator Sandbox")
    st.markdown('<div style="color:#9999b0; margin-top:-8px; margin-bottom:28px; font-size:14px;">Calculează profitul real pentru un preparat nou înainte să-l lansezi</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        df_stoc = citeste_foaie(spreadsheet, "Stoc")

        if df_stoc.empty:
            st.info("Foaia Stoc este goală. Adaugă ingrediente prin Scanare Facturi pentru a putea simula preparate.")
        else:
            df_stoc.columns = [c.lower() for c in df_stoc.columns]

        col_form, col_rez = st.columns([1, 1])

        with col_form:
            st.markdown('<div class="section-header">Date Preparat Nou</div>', unsafe_allow_html=True)

            nume_preparat = st.text_input(
                "Nume preparat",
                placeholder="ex: Burger Angus 200g",
                help="Numele care va apărea în meniu",
            )

            pret_vanzare = st.number_input(
                "Preț vânzare dorit (RON, cu TVA)",
                min_value=0.0,
                value=0.0,
                step=0.5,
                format="%.2f",
                help="Prețul final pe care îl va plăti clientul, inclusiv TVA",
            )

            st.markdown('<div class="section-header">Ingrediente din Stoc</div>', unsafe_allow_html=True)

            # Numărul de ingrediente
            nr_ingrediente = st.number_input(
                "Câte ingrediente are preparatul?",
                min_value=1,
                max_value=20,
                value=3,
                step=1,
            )

            ingrediente_selectate = []
            lista_produse_stoc = []

            if not df_stoc.empty and "produs" in df_stoc.columns:
                lista_produse_stoc = df_stoc["produs"].dropna().unique().tolist()

            for j in range(int(nr_ingrediente)):
                cj1, cj2 = st.columns([2, 1])
                with cj1:
                    if lista_produse_stoc:
                        produs_ales = st.selectbox(
                            f"Ingredient {j+1}",
                            options=lista_produse_stoc,
                            key=f"ing_produs_{j}",
                        )
                    else:
                        produs_ales = st.text_input(
                            f"Ingredient {j+1}",
                            key=f"ing_produs_{j}",
                            placeholder="Nume ingredient",
                        )
                with cj2:
                    gramaj = st.number_input(
                        "Gramaj (g)",
                        min_value=0.0,
                        value=100.0,
                        step=5.0,
                        format="%.0f",
                        key=f"ing_gramaj_{j}",
                    )

                if produs_ales:
                    ingrediente_selectate.append({"produs": produs_ales, "gramaj": gramaj})

            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            calculeaza_btn = st.button("Calculează Profitabilitatea", use_container_width=True)

        # ── Rezultat simulator ──
        with col_rez:
            st.markdown('<div class="section-header">Rezultat</div>', unsafe_allow_html=True)

            if calculeaza_btn and pret_vanzare > 0 and ingrediente_selectate:
                rez = calculeaza_simulator(
                    pret_vanzare=pret_vanzare,
                    ingrediente=ingrediente_selectate,
                    stoc=df_stoc,
                    config=config,
                )

                culoare_profit = "#1a3a5c" if rez["profit_net"] >= 0 else "#c62828"
                semn = "" if rez["profit_net"] < 0 else ""

                st.markdown(f"""
                <div class="result-box">
                    <div class="result-label">Rămâi în mână cu</div>
                    <div class="result-main" style="color:{culoare_profit}">
                        {rez['profit_net']:,.2f} <span style="font-size:24px; font-weight:400">lei</span>
                    </div>
                    <div class="result-marja" style="color:{culoare_profit}; margin-top:12px;">
                        {rez['marja_neta']:+.1f}% marjă netă reală
                    </div>
                    <div class="result-breakdown">
Preț vânzare (cu TVA)      {rez['pret_vanzare']:>10.2f} RON
− TVA ({config.get('cota_tva','9%')})               {rez['tva']:>10.2f} RON
= Preț fără TVA            {rez['pret_fara_tva']:>10.2f} RON
− Food Cost ingrediente    {rez['food_cost']:>10.2f} RON
− Regie fixă/produs        {rez['regie_per_produs']:>10.2f} RON
────────────────────────────────────────
= Profit înainte de taxe   {rez['profit_dupa_regie']:>10.2f} RON
− Impozit firmă            {rez['impozit_firma']:>10.2f} RON
− Impozit dividend         {rez['impozit_dividend']:>10.2f} RON
────────────────────────────────────────
✓ PROFIT NET REAL          {rez['profit_net']:>10.2f} RON
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Recomandare
                if rez["marja_neta"] < 10:
                    st.warning(f"⚠️ Marjă netă sub 10% ({rez['marja_neta']:.1f}%). Consideră ajustarea prețului sau reducerea ingredientelor costisitoare.")
                elif rez["marja_neta"] < 20:
                    st.info(f"💡 Marjă netă acceptabilă ({rez['marja_neta']:.1f}%). Există loc de optimizare.")
                else:
                    st.success(f"✓ Marjă netă excelentă ({rez['marja_neta']:.1f}%). Preparat viabil comercial.")

            elif calculeaza_btn:
                st.warning("Completează prețul de vânzare și cel puțin un ingredient pentru a calcula.")
            else:
                st.markdown("""
                <div style="text-align:center; padding:60px 20px; color:#c0c0d0;">
                    <div style="font-size:48px; margin-bottom:16px; opacity:0.3;">◈</div>
                    <div style="font-size:14px;">Completează formularul și apasă<br><b>Calculează Profitabilitatea</b></div>
                </div>
                """, unsafe_allow_html=True)


# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown("""
<div style="text-align:center; padding:32px 0 16px 0; color:#c0c0cc; font-size:11px; letter-spacing:0.06em;">
    LANA · ACQ Advisory · Motor de Profitabilitate pentru Restaurante
</div>
""", unsafe_allow_html=True)
