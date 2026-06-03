import streamlit as st

st.set_page_config(
    page_title="Lana · ACQ Advisory",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    import gspread
    from google.oauth2.service_account import Credentials
    import google.generativeai as genai
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    st.error(f"Dependență lipsă: {e}")
    st.info("Verifică că requirements.txt conține toate pachetele și dă Reboot app.")
    st.stop()

import pandas as pd
import json
import base64
from datetime import datetime

# ──────────────────────────────────────────────
# CSS GLOBAL — Estetică Apple / Minimalist Premium
# ──────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Mono:wght@300;400&display=swap');

  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color: #1a1a2e; }
  .stApp { background-color: #f7f7f9; }

  [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ebebf0; }
  [data-testid="stSidebar"] * { color: #1a1a2e !important; }

  h1, h2, h3 { font-weight: 600; letter-spacing: -0.02em; color: #0d0d1a; }

  .metric-card {
    background: #ffffff; border: 1px solid #e8e8f0; border-radius: 20px;
    padding: 32px 28px; text-align: left;
    box-shadow: 0 2px 12px rgba(0,0,10,0.04);
    transition: box-shadow 0.25s; height: 100%;
  }
  .metric-card:hover { box-shadow: 0 6px 24px rgba(0,0,10,0.08); }
  .metric-label { font-size: 12px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: #8888a0; margin-bottom: 12px; }
  .metric-value { font-size: 42px; font-weight: 600; color: #0d0d1a; letter-spacing: -0.03em; line-height: 1; }
  .metric-value-accent { font-size: 42px; font-weight: 600; color: #1a3a5c; letter-spacing: -0.03em; line-height: 1; }
  .metric-sub { font-size: 13px; color: #aaaabc; margin-top: 8px; }
  .metric-badge-green { display: inline-block; background: #e8f5e9; color: #2e7d32; border-radius: 20px; padding: 3px 10px; font-size: 12px; font-weight: 500; margin-top: 10px; }
  .metric-badge-red { display: inline-block; background: #fce8e8; color: #c62828; border-radius: 20px; padding: 3px 10px; font-size: 12px; font-weight: 500; margin-top: 10px; }

  .brand-block { padding: 24px 20px 16px 20px; border-bottom: 1px solid #f0f0f5; margin-bottom: 8px; }
  .brand-name { font-size: 22px; font-weight: 700; letter-spacing: -0.03em; color: #0d0d1a; }
  .brand-sub { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: #9999b0; margin-top: 2px; }

  .section-header { font-size: 11px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #9999b0; margin: 28px 0 16px 0; padding-bottom: 8px; border-bottom: 1px solid #f0f0f5; }

  .stButton > button { border-radius: 10px !important; font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important; font-size: 14px !important; padding: 10px 22px !important; background-color: #1a3a5c !important; color: #ffffff !important; border: none !important; }
  .stButton > button:hover { background-color: #0d2540 !important; box-shadow: 0 4px 14px rgba(26,58,92,0.25) !important; }

  .alert-validation { border: 1.5px solid #e53935; background: #fff5f5; border-radius: 12px; padding: 14px 18px; font-size: 13px; color: #c62828; margin: 10px 0; }

  .result-box { background: #ffffff; border: 1px solid #e8e8f0; border-radius: 20px; padding: 36px 32px; text-align: center; box-shadow: 0 2px 18px rgba(0,0,10,0.05); margin-top: 20px; }
  .result-main { font-size: 48px; font-weight: 700; letter-spacing: -0.04em; line-height: 1; }
  .result-label { font-size: 13px; letter-spacing: 0.08em; text-transform: uppercase; color: #aaaabc; margin-bottom: 16px; font-weight: 500; }
  .result-breakdown { font-family: 'DM Mono', monospace; font-size: 12px; color: #8888a0; margin-top: 20px; text-align: left; background: #f7f7f9; border-radius: 12px; padding: 16px; line-height: 1.9; }

  hr { border: none; border-top: 1px solid #f0f0f5; margin: 24px 0; }
  .stDataFrame { border-radius: 14px !important; overflow: hidden !important; border: 1px solid #e8e8f0 !important; }
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONSTANTE
# ──────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

UNITATI_CUNOSCUTE = {
    "kg", "g", "l", "ml", "buc", "bucata", "bucată",
    "bucăți", "litri", "grame", "kilograme", "pcs", "pc"
}

# ──────────────────────────────────────────────
# CONEXIUNE GOOGLE SHEETS
# ──────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def conecteaza_gsheets():
    """Conectare la Google Sheets prin Service Account din st.secrets."""
    credentiale = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    client = gspread.authorize(credentiale)
    return client.open_by_key(st.secrets["spreadsheet_id"])


def citeste_foaie(spreadsheet, nume: str) -> pd.DataFrame:
    """Citește o foaie și returnează DataFrame."""
    try:
        return pd.DataFrame(spreadsheet.worksheet(nume).get_all_records())
    except Exception as e:
        st.error(f"Eroare citire foaie '{nume}': {e}")
        return pd.DataFrame()


def scrie_rand(spreadsheet, nume: str, rand: list) -> bool:
    """Adaugă un rând în foaia specificată."""
    try:
        spreadsheet.worksheet(nume).append_row(rand, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Eroare scriere în '{nume}': {e}")
        return False


def citeste_config(spreadsheet) -> dict:
    """Citește foaia Config ca dicționar cheie→valoare."""
    try:
        date = spreadsheet.worksheet("Config").get_all_records()
        rezultat = {}
        for rand in date:
            cheie = rand.get("Cheie") or rand.get("cheie", "")
            valoare = rand.get("Valoare") or rand.get("valoare", "")
            if cheie:
                rezultat[cheie] = valoare
        return rezultat
    except Exception:
        return {}


def actualizeaza_config(spreadsheet, cheie: str, valoare) -> bool:
    """Actualizează sau adaugă o cheie în foaia Config."""
    try:
        foaie = spreadsheet.worksheet("Config")
        celule = foaie.findall(cheie)
        if celule:
            foaie.update_cell(celule[0].row, 2, valoare)
        else:
            foaie.append_row([cheie, valoare])
        return True
    except Exception as e:
        st.error(f"Eroare config '{cheie}': {e}")
        return False

# ──────────────────────────────────────────────
# FUNCȚII CALCUL
# ──────────────────────────────────────────────

def get_cote(config: dict) -> tuple:
    """Extrage cotele fiscale din config ca valori float."""
    tip = str(config.get("tip_impozit", "Micro 1%"))
    tva = float(str(config.get("cota_tva", "9%")).replace("%", "")) / 100
    div = float(str(config.get("impozit_dividend", "8%")).replace("%", "")) / 100
    if "1%" in tip:
        firma = 0.01
    elif "3%" in tip:
        firma = 0.03
    else:
        firma = 0.16
    return tva, firma, div


def calculeaza_food_cost(retete: pd.DataFrame, stoc: pd.DataFrame) -> float:
    """Food cost mediu ponderat din rețetar și prețuri stoc."""
    if retete.empty or stoc.empty:
        return 0.0
    r = retete.copy()
    s = stoc.copy()
    r.columns = [c.lower() for c in r.columns]
    s.columns = [c.lower() for c in s.columns]
    necesar = ["preparat", "ingredient", "gramaj", "pret_vanzare"]
    if not all(c in r.columns for c in necesar):
        return 0.0
    total_cost, total_vanzari = 0.0, 0.0
    for preparat in r["preparat"].unique():
        ing_prep = r[r["preparat"] == preparat]
        pv = float(ing_prep["pret_vanzare"].iloc[0])
        cost = 0.0
        for _, row in ing_prep.iterrows():
            match = s[s["produs"] == row["ingredient"]] if "produs" in s.columns else pd.DataFrame()
            if not match.empty:
                cost += (float(row["gramaj"]) / 1000) * float(match["pret_unitar"].iloc[0])
        total_cost += cost
        total_vanzari += pv
    return round((total_cost / total_vanzari * 100) if total_vanzari else 0, 2)


def calculeaza_profit_net(vanzari_brute: float, config: dict) -> dict:
    """Cascadă completă de calcul profit net după toate taxele."""
    tva, firma, div = get_cote(config)
    chirie = float(config.get("chirie", 0))
    salarii = float(config.get("salarii", 0))
    utilitati = float(config.get("utilitati", 0))

    tva_col = vanzari_brute - vanzari_brute / (1 + tva)
    fara_tva = vanzari_brute / (1 + tva)
    fixe = chirie + salarii + utilitati
    food = fara_tva * 0.30
    profit_b = fara_tva - food - fixe
    imp_f = max(profit_b * firma, 0)
    dupa_f = profit_b - imp_f
    imp_d = max(dupa_f * div, 0)
    net = dupa_f - imp_d

    return {
        "vanzari_brute": vanzari_brute,
        "tva_colectat": round(tva_col, 2),
        "vanzari_fara_tva": round(fara_tva, 2),
        "food_cost": round(food, 2),
        "cheltuieli_fixe": round(fixe, 2),
        "profit_brut": round(profit_b, 2),
        "impozit_firma": round(imp_f, 2),
        "profit_dupa_firma": round(dupa_f, 2),
        "impozit_dividend": round(imp_d, 2),
        "profit_net": round(net, 2),
        "marja_neta": round((net / vanzari_brute * 100) if vanzari_brute else 0, 2),
    }


def calculeaza_simulator(pret_vanzare: float, ingrediente: list, stoc: pd.DataFrame, config: dict) -> dict:
    """Profit net real per preparat simulat."""
    tva, firma, div = get_cote(config)
    nr_clienti = float(config.get("nr_clienti", 1)) or 1
    fixe = float(config.get("chirie", 0)) + float(config.get("salarii", 0)) + float(config.get("utilitati", 0))
    regie = fixe / nr_clienti

    tva_val = pret_vanzare - pret_vanzare / (1 + tva)
    fara_tva = pret_vanzare / (1 + tva)

    food = 0.0
    s = stoc.copy()
    if not s.empty:
        s.columns = [c.lower() for c in s.columns]
    for ing in ingrediente:
        if not s.empty and "produs" in s.columns:
            match = s[s["produs"].str.lower() == ing["produs"].lower()]
            if not match.empty:
                food += (ing["gramaj"] / 1000) * float(match["pret_unitar"].iloc[0])

    dupa_food = fara_tva - food
    dupa_regie = dupa_food - regie
    imp_f = max(dupa_regie * firma, 0)
    dupa_f = dupa_regie - imp_f
    imp_d = max(dupa_f * div, 0)
    net = dupa_f - imp_d

    return {
        "pret_vanzare": round(pret_vanzare, 2),
        "tva": round(tva_val, 2),
        "pret_fara_tva": round(fara_tva, 2),
        "food_cost": round(food, 2),
        "regie_per_produs": round(regie, 2),
        "profit_dupa_regie": round(dupa_regie, 2),
        "impozit_firma": round(imp_f, 2),
        "profit_dupa_firma": round(dupa_f, 2),
        "impozit_dividend": round(imp_d, 2),
        "profit_net": round(net, 2),
        "marja_neta": round((net / pret_vanzare * 100) if pret_vanzare else 0, 2),
    }


def extrage_factura_cu_ai(imagine_bytes: bytes, mime_type: str) -> list:
    """OCR factură prin Gemini 1.5 Flash → listă produse."""
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """Ești un asistent specializat în extragerea datelor din facturi pentru restaurante din România.
Analizează această imagine și extrage TOATE produsele/ingredientele.
Returnează STRICT un JSON valid (fără text suplimentar, fără markdown) cu structura:
{"produse": [{"produs": "Denumire", "cantitate": 5.0, "unitate": "kg", "pret_unitar": 12.50}]}
Dacă nu poți identifica cu certitudine unitatea de măsură, folosește "NECUNOSCUT".
Prețul unitar să fie fără TVA dacă e posibil de identificat."""

    parte_img = {"mime_type": mime_type, "data": base64.b64encode(imagine_bytes).decode()}
    try:
        raspuns = model.generate_content([prompt, parte_img])
        text = raspuns.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(text).get("produse", [])
    except json.JSONDecodeError:
        st.error("AI-ul nu a returnat JSON valid. Reîncearcă.")
        return []
    except Exception as e:
        st.error(f"Eroare Gemini: {e}")
        return []

# ──────────────────────────────────────────────
# SIDEBAR
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
        "Secțiune",
        ["📊  Dashboard", "⚙️  Setup Fiscal", "💰  Cheltuieli Fixe", "📄  Scanare Facturi", "🧪  Simulator Sandbox"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:12px;color:#8888a0;">Conectat · {datetime.now().strftime("%d %b %Y, %H:%M")}</div>',
        unsafe_allow_html=True,
    )

# ──────────────────────────────────────────────
# CONEXIUNE
# ──────────────────────────────────────────────

try:
    spreadsheet = conecteaza_gsheets()
    conexiune_ok = True
except Exception as e:
    conexiune_ok = False
    st.error(f"⚠️ Eroare conectare Google Sheets: {e}")

# ──────────────────────────────────────────────
# PAGINA: DASHBOARD
# ──────────────────────────────────────────────

if "📊" in pagina:
    st.markdown("## Dashboard")
    st.markdown('<div style="color:#9999b0;margin-top:-8px;margin-bottom:28px;font-size:14px;">Imagine financiară în timp real</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        df_vanzari = citeste_foaie(spreadsheet, "Vanzari")
        df_retete = citeste_foaie(spreadsheet, "Retetar")
        df_stoc = citeste_foaie(spreadsheet, "Stoc")

        vanzari_totale = 0.0
        if not df_vanzari.empty:
            df_vanzari.columns = [c.lower() for c in df_vanzari.columns]
            if "valoare" in df_vanzari.columns:
                vanzari_totale = float(df_vanzari["valoare"].sum())
            elif "total" in df_vanzari.columns:
                vanzari_totale = float(df_vanzari["total"].sum())

        rez = calculeaza_profit_net(vanzari_totale, config)
        fc_pct = calculeaza_food_cost(df_retete, df_stoc)
        fixe_total = float(config.get("chirie", 0)) + float(config.get("salarii", 0)) + float(config.get("utilitati", 0))

        col1, col2, col3 = st.columns(3)

        with col1:
            badge = "metric-badge-green" if rez["profit_net"] >= 0 else "metric-badge-red"
            semn = "+" if rez["profit_net"] >= 0 else ""
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Profit Net Real</div>
                <div class="metric-value-accent">{rez['profit_net']:,.0f} <span style="font-size:22px;font-weight:400">RON</span></div>
                <div class="metric-sub">Bani efectiv în mână, după toate taxele</div>
                <div class="{badge}">{semn}{rez['marja_neta']}% marjă netă</div>
            </div>""", unsafe_allow_html=True)

        with col2:
            fc_badge = "metric-badge-green" if fc_pct <= 30 else "metric-badge-red"
            fc_label = "Optim ≤30%" if fc_pct <= 30 else "Atenție >30%"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Food Cost Mediu</div>
                <div class="metric-value">{fc_pct if fc_pct > 0 else "—"}<span style="font-size:22px;font-weight:400"> %</span></div>
                <div class="metric-sub">Calculat din rețetar și stoc curent</div>
                <div class="{fc_badge}">{fc_label}</div>
            </div>""", unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Cheltuieli Operative Totale</div>
                <div class="metric-value">{fixe_total:,.0f} <span style="font-size:22px;font-weight:400">RON</span></div>
                <div class="metric-sub">Chirie + Salarii + Utilități / lună</div>
                <div style="margin-top:10px;font-size:12px;color:#aaaabc;">Vânzări brute: {vanzari_totale:,.0f} RON</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:36px;">Defalcare Financiară</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([2, 1])
        with col_a:
            df_def = pd.DataFrame({
                "Component": ["Vânzări Brute", "− TVA", "− Food Cost (~30%)", "− Cheltuieli Fixe", "− Impozit Firmă", "− Impozit Dividend", "= Profit Net"],
                "Valoare (RON)": [
                    f"{rez['vanzari_brute']:,.2f}", f"{rez['tva_colectat']:,.2f}",
                    f"{rez['food_cost']:,.2f}", f"{rez['cheltuieli_fixe']:,.2f}",
                    f"{rez['impozit_firma']:,.2f}", f"{rez['impozit_dividend']:,.2f}",
                    f"{rez['profit_net']:,.2f}",
                ]
            })
            st.dataframe(df_def, use_container_width=True, hide_index=True)
        with col_b:
            st.markdown(f"""
            <div class="metric-card" style="margin-top:0">
                <div class="metric-label">Configurare Fiscală</div>
                <div style="font-size:13px;color:#555;line-height:2.2;">
                    <b>Firmă:</b> {config.get('tip_impozit','—')}<br>
                    <b>TVA:</b> {config.get('cota_tva','—')}<br>
                    <b>Dividend:</b> {config.get('impozit_dividend','—')}<br>
                    <b>Clienți/lună:</b> {config.get('nr_clienti','—')}
                </div>
            </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# PAGINA: SETUP FISCAL
# ──────────────────────────────────────────────

elif "⚙️" in pagina:
    st.markdown("## Setup Fiscal")
    st.markdown('<div style="color:#9999b0;margin-top:-8px;margin-bottom:28px;font-size:14px;">Parametri fiscali conform legislației din România</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        st.markdown('<div class="section-header">Regim Fiscal</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            opts_imp = ["Micro 1%", "Micro 3%", "Profit 16%"]
            val_imp = config.get("tip_impozit", "Micro 1%")
            tip_impozit = st.selectbox("Tip Impozit pe Venit", opts_imp,
                index=opts_imp.index(val_imp) if val_imp in opts_imp else 0,
                help="Micro 1% — cu cel puțin un angajat. Micro 3% — fără angajat. Profit 16% — firmă mare.")

        with col2:
            opts_tva = ["9%", "19%"]
            val_tva = str(config.get("cota_tva", "9%"))
            cota_tva = st.selectbox("Cotă TVA", opts_tva,
                index=opts_tva.index(val_tva) if val_tva in opts_tva else 0,
                help="9% alimente. 19% servicii restaurant cu alcool.")

        with col3:
            opts_div = ["8%", "10%"]
            val_div = str(config.get("impozit_dividend", "8%"))
            imp_div = st.selectbox("Impozit Dividend", opts_div,
                index=opts_div.index(val_div) if val_div in opts_div else 0)

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Salvează Configurarea Fiscală"):
            if all([
                actualizeaza_config(spreadsheet, "tip_impozit", tip_impozit),
                actualizeaza_config(spreadsheet, "cota_tva", cota_tva),
                actualizeaza_config(spreadsheet, "impozit_dividend", imp_div),
            ]):
                st.success("✓ Configurare fiscală salvată.")
                st.cache_resource.clear()

# ──────────────────────────────────────────────
# PAGINA: CHELTUIELI FIXE
# ──────────────────────────────────────────────

elif "💰" in pagina:
    st.markdown("## Cheltuieli Fixe")
    st.markdown('<div style="color:#9999b0;margin-top:-8px;margin-bottom:28px;font-size:14px;">Costuri operative lunare și volum estimat</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        st.markdown('<div class="section-header">Costuri Lunare (RON)</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            chirie = st.number_input("Chirie lunară", min_value=0.0, value=float(config.get("chirie", 0)), step=100.0, format="%.0f")
            salarii = st.number_input("Salarii totale brute + taxe", min_value=0.0, value=float(config.get("salarii", 0)), step=100.0, format="%.0f")
        with col2:
            utilitati = st.number_input("Utilități", min_value=0.0, value=float(config.get("utilitati", 0)), step=50.0, format="%.0f")
            nr_clienti = st.number_input("Clienți / vânzări estimate/lună", min_value=1, value=int(config.get("nr_clienti", 100)), step=10)

        st.markdown("<hr>", unsafe_allow_html=True)
        total_fixe = chirie + salarii + utilitati
        regie = total_fixe / nr_clienti if nr_clienti else 0
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Cheltuieli Fixe", f"{total_fixe:,.0f} RON")
        c2.metric("Nr. Clienți/Lună", f"{nr_clienti:,}")
        c3.metric("Regie per Bon", f"{regie:,.2f} RON")

        if st.button("Salvează Cheltuielile Fixe"):
            if all([
                actualizeaza_config(spreadsheet, "chirie", chirie),
                actualizeaza_config(spreadsheet, "salarii", salarii),
                actualizeaza_config(spreadsheet, "utilitati", utilitati),
                actualizeaza_config(spreadsheet, "nr_clienti", nr_clienti),
            ]):
                st.success("✓ Cheltuieli fixe salvate.")
                st.cache_resource.clear()

# ──────────────────────────────────────────────
# PAGINA: SCANARE FACTURI
# ──────────────────────────────────────────────

elif "📄" in pagina:
    st.markdown("## Scanare Facturi")
    st.markdown('<div style="color:#9999b0;margin-top:-8px;margin-bottom:28px;font-size:14px;">Extragere automată prin AI (Gemini 1.5 Flash)</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        st.markdown('<div class="section-header">Încarcă Fotografie Factură</div>', unsafe_allow_html=True)
        fisier = st.file_uploader("Factură (JPG, PNG, WEBP)", type=["jpg","jpeg","png","webp","pdf"], label_visibility="collapsed")

        if fisier:
            if fisier.type.startswith("image"):
                st.image(fisier, caption="Previzualizare", width=380)

            if st.button("🔍 Analizează cu AI"):
                with st.spinner("Gemini procesează factura..."):
                    bytes_f = fisier.read()
                    mime = fisier.type or "image/jpeg"
                    produse = extrage_factura_cu_ai(bytes_f, mime)
                if produse:
                    st.session_state["produse_factura"] = produse
                    st.success(f"✓ {len(produse)} produs(e) identificate.")
                else:
                    st.warning("Nu s-au putut extrage produse. Verifică claritatea imaginii.")

        if st.session_state.get("produse_factura"):
            st.markdown('<div class="section-header">Produse Extrase — Validare</div>', unsafe_allow_html=True)
            produse = st.session_state["produse_factura"]
            are_erori = False
            produse_ok = []

            for i, p in enumerate(produse):
                c1, c2, c3, c4 = st.columns([3, 1.5, 2, 2])
                with c1:
                    nume = st.text_input("Produs", value=p.get("produs",""), key=f"p_{i}",
                        label_visibility="visible" if i==0 else "collapsed")
                with c2:
                    cant = st.number_input("Cantitate", value=float(p.get("cantitate",0)),
                        min_value=0.0, step=0.1, key=f"c_{i}",
                        label_visibility="visible" if i==0 else "collapsed")
                with c3:
                    um_raw = p.get("unitate", "NECUNOSCUT")
                    um_valid = um_raw.lower().strip() in UNITATI_CUNOSCUTE
                    if not um_valid:
                        are_erori = True
                        st.markdown(f'<div class="alert-validation">⚠️ Unitate necunoscută: <b>"{um_raw}"</b></div>', unsafe_allow_html=True)
                        um = st.text_input("Unitate", value="", key=f"u_{i}", placeholder="kg, g, l, buc")
                    else:
                        um = st.text_input("Unitate", value=um_raw, key=f"u_{i}",
                            label_visibility="visible" if i==0 else "collapsed")
                with c4:
                    pret = st.number_input("Preț Unitar (RON)", value=float(p.get("pret_unitar",0)),
                        min_value=0.0, step=0.01, format="%.2f", key=f"pr_{i}",
                        label_visibility="visible" if i==0 else "collapsed")

                um_final = st.session_state.get(f"u_{i}", um)
                if um_final and um_final.lower().strip() not in UNITATI_CUNOSCUTE and not um_valid:
                    are_erori = True

                produse_ok.append({"produs": st.session_state.get(f"p_{i}", nume),
                                   "cantitate": cant, "unitate": um_final or um, "pret_unitar": pret})

            st.markdown("<hr>", unsafe_allow_html=True)
            if are_erori:
                st.markdown('<div class="alert-validation">Salvarea este blocată — completează toate unitățile de măsură.<br>Acceptate: kg, g, l, ml, buc, bucata, bucăți, litri, grame, kilograme</div>', unsafe_allow_html=True)
                st.button("Salvează în Stoc", disabled=True)
            else:
                if st.button("✓ Salvează în Stoc"):
                    with st.spinner("Salvând..."):
                        ok = all(scrie_rand(spreadsheet, "Stoc",
                            [p["produs"], p["cantitate"], p["unitate"], p["pret_unitar"],
                             datetime.now().strftime("%Y-%m-%d")]) for p in produse_ok)
                    if ok:
                        st.success(f"✓ {len(produse_ok)} produs(e) salvate în Stoc.")
                        del st.session_state["produse_factura"]

# ──────────────────────────────────────────────
# PAGINA: SIMULATOR SANDBOX
# ──────────────────────────────────────────────

elif "🧪" in pagina:
    st.markdown("## Simulator Sandbox")
    st.markdown('<div style="color:#9999b0;margin-top:-8px;margin-bottom:28px;font-size:14px;">Calculează profitul real pentru un preparat nou înainte să-l lansezi</div>', unsafe_allow_html=True)

    if not conexiune_ok:
        st.warning("Conexiunea la Google Sheets nu este disponibilă.")
    else:
        config = citeste_config(spreadsheet)
        df_stoc = citeste_foaie(spreadsheet, "Stoc")
        if not df_stoc.empty:
            df_stoc.columns = [c.lower() for c in df_stoc.columns]

        col_form, col_rez = st.columns(2)

        with col_form:
            st.markdown('<div class="section-header">Date Preparat Nou</div>', unsafe_allow_html=True)
            nume_prep = st.text_input("Nume preparat", placeholder="ex: Burger Angus 200g")
            pret_v = st.number_input("Preț vânzare (RON, cu TVA)", min_value=0.0, value=0.0, step=0.5, format="%.2f")

            st.markdown('<div class="section-header">Ingrediente din Stoc</div>', unsafe_allow_html=True)
            nr_ing = st.number_input("Număr ingrediente", min_value=1, max_value=20, value=3, step=1)

            lista_stoc = []
            if not df_stoc.empty and "produs" in df_stoc.columns:
                lista_stoc = df_stoc["produs"].dropna().unique().tolist()

            ingrediente = []
            for j in range(int(nr_ing)):
                cj1, cj2 = st.columns([2, 1])
                with cj1:
                    if lista_stoc:
                        prod = st.selectbox(f"Ingredient {j+1}", lista_stoc, key=f"ip_{j}")
                    else:
                        prod = st.text_input(f"Ingredient {j+1}", key=f"ip_{j}", placeholder="Nume ingredient")
                with cj2:
                    gram = st.number_input("Gramaj (g)", min_value=0.0, value=100.0, step=5.0, format="%.0f", key=f"ig_{j}")
                if prod:
                    ingrediente.append({"produs": prod, "gramaj": gram})

            calc_btn = st.button("Calculează Profitabilitatea", use_container_width=True)

        with col_rez:
            st.markdown('<div class="section-header">Rezultat</div>', unsafe_allow_html=True)

            if calc_btn and pret_v > 0 and ingrediente:
                rez = calculeaza_simulator(pret_v, ingrediente, df_stoc, config)
                culoare = "#1a3a5c" if rez["profit_net"] >= 0 else "#c62828"
                cota_tva_label = config.get("cota_tva", "9%")

                st.markdown(f"""
                <div class="result-box">
                    <div class="result-label">Rămâi în mână cu</div>
                    <div class="result-main" style="color:{culoare}">
                        {rez['profit_net']:,.2f} <span style="font-size:24px;font-weight:400">lei</span>
                    </div>
                    <div style="font-size:18px;color:{culoare};margin-top:12px;">
                        {rez['marja_neta']:+.1f}% marjă netă reală
                    </div>
                    <div class="result-breakdown">
Preț vânzare (cu TVA)       {rez['pret_vanzare']:>9.2f} RON
− TVA ({cota_tva_label})                {rez['tva']:>9.2f} RON
= Preț fără TVA             {rez['pret_fara_tva']:>9.2f} RON
− Food Cost ingrediente     {rez['food_cost']:>9.2f} RON
− Regie fixă/produs         {rez['regie_per_produs']:>9.2f} RON
────────────────────────────────────────
= Profit înainte taxe       {rez['profit_dupa_regie']:>9.2f} RON
− Impozit firmă             {rez['impozit_firma']:>9.2f} RON
− Impozit dividend          {rez['impozit_dividend']:>9.2f} RON
────────────────────────────────────────
✓ PROFIT NET REAL           {rez['profit_net']:>9.2f} RON
                    </div>
                </div>""", unsafe_allow_html=True)

                if rez["marja_neta"] < 10:
                    st.warning(f"⚠️ Marjă sub 10% ({rez['marja_neta']:.1f}%). Ajustează prețul sau ingredientele.")
                elif rez["marja_neta"] < 20:
                    st.info(f"💡 Marjă acceptabilă ({rez['marja_neta']:.1f}%). Există loc de optimizare.")
                else:
                    st.success(f"✓ Marjă excelentă ({rez['marja_neta']:.1f}%). Preparat viabil.")

            elif calc_btn:
                st.warning("Completează prețul și cel puțin un ingredient.")
            else:
                st.markdown("""
                <div style="text-align:center;padding:60px 20px;color:#c0c0d0;">
                    <div style="font-size:48px;margin-bottom:16px;opacity:0.3;">◈</div>
                    <div style="font-size:14px;">Completează formularul și apasă<br><b>Calculează Profitabilitatea</b></div>
                </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.markdown("""
<div style="text-align:center;padding:32px 0 16px 0;color:#c0c0cc;font-size:11px;letter-spacing:0.06em;">
    LANA · ACQ Advisory · Motor de Profitabilitate pentru Restaurante
</div>
""", unsafe_allow_html=True)
