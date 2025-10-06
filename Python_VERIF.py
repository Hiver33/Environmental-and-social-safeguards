#****************** Projet GriefPy ********************************
#     Dashboard interactif pour la visualisation des indicateurs
#******************************************************************

#==================================================================
# ------------------ Chargement des bibliothèques -----------------
#==================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

#=================================================================
# -------------------- Chargement des données --------------------
#=================================================================
@st.cache_data(ttl=300)
def load_data(path):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file if uploaded_file else url_excel)

#====================================================================
# -------------------- Vérification des colonnes --------------------
#====================================================================
cols_req = ["Type_depot","Statut_traitement","Nature_plainte","Categorie","Date_reception","Nb_jour","Communaute","Sexe"]
if df.empty or not all(col in df.columns for col in cols_req):
    st.stop()

# -------------------- Préparation --------------------
df["Date_reception"] = pd.to_datetime(df["Date_reception"], errors="coerce", dayfirst=True)
df = df.dropna(subset=["Date_reception"])
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()

#====================================================================
# --------------------------- Filtres -------------------------------
#====================================================================
st.sidebar.header("Filtres")
annee_courante = datetime.now().year
annees_dispo = sorted(df["Année"].unique())
annee_choisie = st.sidebar.selectbox(
    "📅 Filtrer par année :",
    annees_dispo,
    index=annees_dispo.index(annee_courante) if annee_courante in annees_dispo else 0
)
Types = st.sidebar.multiselect("📂 Type de dépôt :", df["Type_depot"].unique(), default=df["Type_depot"].unique())
Statuts = st.sidebar.multiselect("✅ Statut de traitement :", df["Statut_traitement"].unique(), default=df["Statut_traitement"].unique())

df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]
if df_filtered.empty:
    st.warning("Aucun enregistrement après filtrage")
    st.stop()

#====================================================================
# ---------------------- Apparence / Thème --------------------------
#====================================================================
st.sidebar.markdown("---")
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")
theme_choice = st.sidebar.radio("🖌️ Apparence :", ["Sombre", "Clair"])

# Définition des couleurs selon le thème
if theme_choice == "Sombre":
    page_bg = "#1a1d21"
    sidebar_bg = "#2c2f33"
    sidebar_text_color = "#ffffff"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
    graph_bg_color = "#2b2d33"  # gris foncé
    toggle_color = "#00ccff"
    toggle_bg = "#444"
else:
    page_bg = "#f5f5f5"
    sidebar_bg = "#dcdcdc"
    sidebar_text_color = "#1a1a1a"
    header_color = "#1a73e8"
    card_colors = ["#87CEFA", "#90EE90", "#FFD700", "#FF7F7F"]
    plotly_template = "plotly_white"
    graph_bg_color = "#f0f0f5"  # gris clair
    toggle_color = "#1a73e8"
    toggle_bg = "#ddd"

# Widgets sidebar : fond blanc et texte bleu fixe
sidebar_widget_bg = "#ffffff"
sidebar_widget_text = "#0000ff"

page_width = "100%" if plein_ecran else "80%"

# Application du style CSS
st.markdown(f"""
<style>
/* Application générale */
.stApp {{
    background-color: {page_bg};
    color: {sidebar_text_color};
    max-width: {page_width};
    margin: auto;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {sidebar_bg};
}}

/* Texte clair dans la sidebar si thème sombre */
section[data-testid="stSidebar"] * {{
    color: {sidebar_text_color} !important;
}}

/* Multiselect / selectbox */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div > div {{
    background-color: {sidebar_widget_bg} !important;
    color: {sidebar_widget_text} !important;
}}

/* File uploader */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] > div > div {{
    background-color: {sidebar_widget_bg} !important;
    color: {sidebar_widget_text} !important;
}}

/* Toggle button couleurs */
div[data-baseweb="switch"] > div {{
    background-color: {toggle_bg} !important;
}}
div[data-baseweb="switch"] input:checked + span {{
    background-color: {toggle_color} !important;
}}

/* Titres des graphiques */
h1, h2, h3, h4 {{
    color: {header_color};
}}
</style>
""", unsafe_allow_html=True)

#====================================================================
# -------------------------- Indicateurs ----------------------------
#====================================================================
st.title("📊 Dashboard Suivi du MGG")
total = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé","Grief non recevable"])] )
en_cours = len(df_filtered[df_filtered["Statut_traitement"]=="En cours"])
a_traiter = len(df_filtered[df_filtered["Statut_traitement"]=="A traiter"])

cols = st.columns(4
