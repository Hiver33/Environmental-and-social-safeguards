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
# --------------------------- Filtrees ------------------------------
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
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")

df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]
if df_filtered.empty:
    st.warning("Aucun enregistrement après filtrage")
    st.stop()

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

#====================================================================
# ----------------------------- Thème -------------------------------
#====================================================================
page_width = "100%" if plein_ecran else "80%"
theme_choice = st.sidebar.radio("🎨 Choisir le thème :", ["Sombre", "Clair"])

if theme_choice == "Sombre":
    page_bg = "#1a1d21"
    text_color = "white"
    header_color = "#00ccff"
    card_colors = ["#00ccff","#00ff99","#ffcc00","#ff6666"]
    plotly_template = "plotly_dark"
    plot_bg = "#1a1d21"
    paper_bg = "#1a1d21"
    table_bg = "#1a1d21"
else:
    page_bg = "#f5f5f5"
    text_color = "#1a1a1a"
    header_color = "#1a73e8"
    card_colors = ["#87CEFA","#90EE90","#FFD700","#FF7F7F"]
    plotly_template = "plotly_white"
    plot_bg = "#f5f5f5"
    paper_bg = "#f5f5f5"
    table_bg = "#f5f5f5"

st.markdown(f"""
<style>
.stApp {{ background-color:{page_bg}; color:{text_color}; max-width:{page_width}; margin:auto; }}
h1,h2,h3{{color:{header_color};}}
.dataframe tbody tr td {{
    background-color: {table_bg};
    color: {text_color};
}}
</style>
""", unsafe_allow_html=True)

# ------------------- Indicateurs avec couleurs dynamiques -------------------
for col,(val,label),color in zip(cols,metrics,card_colors):
    col.markdown(f"""
        <div style='background:{color}; padding:15px; border-radius:15px;'>
            <p style='font-size:28px; font-weight:bold; color:black'>{val}</p>
            <p style='font-weight:bold; color:black'>{label}</p>
        </div>
    """, unsafe_allow_html=True)

#====================================================================
# --------------------- Graphiques principaux -----------------------
#====================================================================
st.subheader("📈 Analyse visuelle")

# Répartition par type
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=type_counts.index, y=type_counts.values, text=type_counts.values,
    title="Répartition par type de dépôt", template=plotly_template, height=400
)
fig_type.update_layout(
    xaxis_title="Type de dépôt",
    yaxis_title="Nombre de griefs",
    legend_title_text="Statut du traitement",
    plot_bgcolor=plot_bg,
    paper_bgcolor=paper_bg
)

# Avancement général
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
fig_stat.update_layout(plot_bgcolor=plot_bg, paper_bgcolor=paper_bg)

# Affichage côte à côte ou plein écran
if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)

# Histogramme par Nature
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title = "Nombre de griefs par nature", template=plotly_template, height=400, color_discrete_map=colors_map_statut
)
fig_nature.update_layout(
    xaxis_title="Nature de griefs",
    yaxis_title="Nombre",
    legend_title_text="Statut du traitement",
    plot_bgcolor=plot_bg,
    paper_bgcolor=paper_bg
)
st.plotly_chart(fig_nature, use_container_width=True)

# Répartition Communauté / Sexe
st.subheader("🏘️ Répartition par communauté et sexe")
if plein_ecran:
    fig_comm = px.bar(
        x=df_filtered["Communaute"].value_counts().sort_values().index,
        y=df_filtered["Communaute"].value_counts().sort_values().values,
        text=df_filtered["Communaute"].value_counts().sort_values().values,
        title="Nombre de griefs par communauté", template=plotly_template, height=400
    )
    fig_comm.update_layout(xaxis_title="Village/Localité", yaxis_title="Nombre de griefs", plot_bgcolor=plot_bg, paper_bgcolor=paper_bg)
    st.plotly_chart(fig_comm, use_container_width=True)

    fig_sexe = px.pie(
        df_filtered, names="Sexe", title="Répartition par sexe", template=plotly_template, height=400
    )
    fig_sexe.update_traces(textinfo="percent+label", textposition="inside")
    fig_sexe.update_layout(plot_bgcolor=plot_bg, paper_bgcolor=paper_bg)
    st.plotly_chart(fig_sexe, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    fig_comm = px.bar(
        x=df_filtered["Communaute"].value_counts().sort_values().index,
        y=df_filtered["Communaute"].value_counts().sort_values().values,
        text=df_filtered["Communaute"].value_counts().sort_values().values,
        title="Nombre de griefs par communauté", template=plotly_template, height=400
    )
    fig_comm.update_layout(xaxis_title="Village/Localité", yaxis_title="Nombre de griefs", legend_title_text="Sexe", plot_bgcolor=plot_bg, paper_bgcolor=paper_bg)
    fig_sexe = px.pie(
        df_filtered, names="Sexe", title="Répartition par sexe", template=plotly_template, height=400
    )
    fig_sexe.update_traces(textinfo="percent+label", textposition="inside")
    fig_sexe.update_layout(plot_bgcolor=plot_bg, paper_bgcolor=paper_bg)
    c1.plotly_chart(fig_comm, use_container_width=True)
    c2.plotly_chart(fig_sexe, use_container_width=True)

# (Les autres graphiques restent inchangés mais avec plot_bgcolor et paper_bgcolor = plot_bg, paper_bg)
