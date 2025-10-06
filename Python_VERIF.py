#****************** Projet GriefPy ********************************
#     Dashboard interactif pour la visualisation des indicateurs
#******************************************************************

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

# --------- Couleurs dynamiques selon thème ---------
if theme_choice == "Sombre":
    page_bg = "#1a1d21"
    sidebar_bg = "#2c2f33"
    text_color = "#ffffff"
    widget_text_color = "#000000"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
else:
    page_bg = "#f5f5f5"
    sidebar_bg = "#dcdcdc"
    text_color = "#1a1a1a"
    widget_text_color = "#000000"
    header_color = "#1a73e8"
    card_colors = ["#87CEFA", "#90EE90", "#FFD700", "#FF7F7F"]
    plotly_template = "plotly_white"

page_width = "100%" if plein_ecran else "80%"

# --------- CSS dynamique pour sidebar et widgets ---------
st.markdown(f"""
<style>
    .stApp {{
        background-color: {page_bg};
        color: {text_color};
        max-width: {page_width};
        margin:auto;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
        color: {text_color};
    }}
    section[data-testid="stSidebar"] * {{
        color: {text_color} !important;
    }}
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] select,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[role='listbox'],
    section[data-testid="stSidebar"] label {{
        color: {widget_text_color} !important;
    }}
    h1,h2,h3,h4 {{
        color: {header_color};
    }}
</style>
""", unsafe_allow_html=True)

#====================================================================
# -------------------------- Indicateurs ----------------------------
#====================================================================
st.title("📊 Dashboard Suivi du MGG")
total = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé","Grief non recevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"]=="En cours"])
a_traiter = len(df_filtered[df_filtered["Statut_traitement"]=="A traiter"])

cols = st.columns(4)
metrics = [(total,"Total"),(acheves,"Achevés"),(en_cours,"En cours"),(a_traiter,"A traiter")]

for col,(val,label),color in zip(cols,metrics,card_colors):
    col.markdown(f"""
        <div style='background:{color}; padding:15px; border-radius:15px; text-align:left;'>
            <p style='font-size:28px; font-weight:bold; color:black;'>{val}</p>
            <p style='font-weight:bold; color:black;'>{label}</p>
        </div>
    """, unsafe_allow_html=True)

#====================================================================
# --------------------- Graphiques principaux -----------------------
#====================================================================
st.subheader("📈 Analyse visuelle")

# --- Répartition type dépôt ---
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=type_counts.index, y=type_counts.values, text=type_counts.values,
    title="Répartition par type de dépôt", template=plotly_template, height=400
)
fig_type.update_layout(
    title_font=dict(color=header_color, size=18),
    xaxis_title="Type de dépôt", yaxis_title="Nombre de griefs"
)

# --- Pie statut ---
colors_map_statut = {
    "Achevé": "#00ff99",
    "Grief non recevable": "#ffcc00",
    "En cours": "#636efa",
    "A traiter": "#ff6666"
}
fig_stat = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général",
    color="Statut_traitement", color_discrete_map=colors_map_statut,
    template=plotly_template, height=400
)
fig_stat.update_traces(textinfo="percent+label", textposition="inside")
fig_stat.update_layout(title_font=dict(color=header_color, size=18))

if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)

# --- Histogramme par nature ---
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title="Nombre de griefs par nature", template=plotly_template,
    color_discrete_map=colors_map_statut, height=400
)
fig_nature.update_layout(
    title_font=dict(color=header_color, size=18),
    xaxis_title="Nature de griefs", yaxis_title="Nombre"
)
st.plotly_chart(fig_nature, use_container_width=True)

# --- Répartition communauté / sexe ---
st.subheader("🏘️ Répartition par communauté et sexe")
c1, c2 = st.columns(2)
fig_comm = px.bar(
   
