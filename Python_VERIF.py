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
# ---------------------- Apparence / Thème --------------------------
#====================================================================
st.sidebar.markdown("---")
st.sidebar.header("🖌️ Apparence")

# Choix du thème
theme_choice = st.sidebar.radio("🎨 Choisir le thème :", ["Sombre", "Clair"])

# Choix du mode plein écran
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")

# Couleurs selon le thème
if theme_choice == "Sombre":
    page_bg = "#1a1d21"          # fond sombre principal
    sidebar_bg = "#2c2f33"       # sidebar plus sombre
    text_color = "#ffffff"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
else:
    page_bg = "#f5f5f5"          # fond gris clair
    sidebar_bg = "#dcdcdc"       # gris moyen
    text_color = "#1a1a1a"       # texte noir doux
    header_color = "#1a73e8"     # bleu doux
    card_colors = ["#87CEFA", "#90EE90", "#FFD700", "#FF7F7F"]
    plotly_template = "plotly_white"

# Largeur de la page selon le mode
page_width = "100%" if plein_ecran else "80%"

# Application du style CSS global
st.markdown(f"""
<style>
    /* Fond général */
    .stApp {{
        background-color: {page_bg};
        color: {text_color};
        max-width: {page_width};
        margin: auto;
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}
    
    /* Titres */
    h1, h2, h3, h4 {{
        color: {header_color};
    }}
</style>
""", unsafe_allow_html=True)

#====================================================================
# ---------------------------- Filtres ------------------------------
#====================================================================
st.sidebar.header("Filtres")

annee_courante = datetime.now().year
annees_dispo = sorted(df["Année"].unique())
annee_choisie = st.sidebar.selectbox("📅 Année :", annees_dispo, index=annees_dispo.index(annee_courante) if annee_courante in annees_dispo else 0)
Types = st.sidebar.multiselect("📂 Type de dépôt :", df["Type_depot"].unique(), default=df["Type_depot"].unique())
Statuts = st.sidebar.multiselect("✅ Statut :", df["Statut_traitement"].unique(), default=df["Statut_traitement"].unique())

plein_ecran = st.sidebar.toggle("🖥️ Plein écran")

df_filtered = df[(df["Année"] == annee_choisie) & (df["Type_depot"].isin(Types)) & (df["Statut_traitement"].isin(Statuts))]
if df_filtered.empty:
    st.warning("Aucun enregistrement trouvé avec les filtres choisis.")
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
metrics = [(total,"Total"),(acheves,"Achevés"),(en_cours,"En cours"),(a_traiter,"À traiter")]
card_colors = ["#00ccff","#00ff99","#ffcc00","#ff6666"] if theme_choice=="Sombre" else ["#87CEFA","#90EE90","#FFD700","#FF7F7F"]

for col,(val,label),color in zip(cols,metrics,card_colors):
    col.markdown(f"""
        <div style='background:{color}; padding:15px; border-radius:12px; text-align:center;'>
            <p style='font-size:28px; font-weight:bold; color:black;'>{val}</p>
            <p style='font-weight:bold; color:black;'>{label}</p>
        </div>
    """, unsafe_allow_html=True)

#====================================================================
# ---------------------- Graphiques principaux ----------------------
#====================================================================
st.subheader("📈 Analyse visuelle")

# --- Répartition par Type de dépôt ---
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=type_counts.index, y=type_counts.values, text=type_counts.values,
    title="Répartition par type de dépôt", template=plotly_template
)
fig_type.update_traces(textfont_color=text_color)
fig_type.update_layout(
    xaxis_title="Type de dépôt",
    yaxis_title="Nombre de griefs",
    font=dict(color=text_color),
    title_font_color=header_color
)

# --- Statut global ---
colors_map_statut = {"Achevé": "#00ff99", "Grief non recevable": "#ffcc00", "En cours": "#636efa", "A traiter": "#ff6666"}
fig_stat = px.pie(df_filtered, names="Statut_traitement", title="Avancement général",
                  color="Statut_traitement", color_discrete_map=colors_map_statut,
                  template=plotly_template)
fig_stat.update_traces(textinfo="percent+label", textfont_color=text_color)
fig_stat.update_layout(font=dict(color=text_color), title_font_color=header_color)

# --- Affichage côte à côte ---
if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)

# --- Histogramme par Nature ---
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title="Nombre de griefs par nature", template=plotly_template,
    color_discrete_map=colors_map_statut
)
fig_nature.update_layout(font=dict(color=text_color), title_font_color=header_color)
fig_nature.update_traces(textfont_color=text_color)
st.plotly_chart(fig_nature, use_container_width=True)

#====================================================================
# ----------------------- Graphiques secondaires --------------------
#====================================================================
st.subheader("🏘️ Répartition par communauté et sexe")

# Communauté
fig_comm = px.bar(
    x=df_filtered["Communaute"].value_counts().index,
    y=df_filtered["Communaute"].value_counts().values,
    text=df_filtered["Communaute"].value_counts().values,
    title="Nombre de griefs par communauté", template=plotly_template
)
fig_comm.update_layout(font=dict(color=text_color), title_font_color=header_color)
fig_comm.update_traces(textfont_color=text_color)

# Sexe
fig_sexe = px.pie(df_filtered, names="Sexe", title="Répartition par sexe", template=plotly_template)
fig_sexe.update_traces(textinfo="percent+label", textfont_color=text_color)
fig_sexe.update_layout(font=dict(color=text_color), title_font_color=header_color)

if plein_ecran:
    st.plotly_chart(fig_comm, use_container_width=True)
    st.plotly_chart(fig_sexe, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_comm, use_container_width=True)
    c2.plotly_chart(fig_sexe, use_container_width=True)

#====================================================================
# ---------------------- Graphique temporel -------------------------
#====================================================================
st.subheader("📅 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :", 3, 10, 5)
df_line = df_filtered.groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
top_natures = df_line.groupby("Nature_plainte")["Nombre"].sum().nlargest(top_n).index
df_line = df_line[df_line["Nature_plainte"].isin(top_natures)]

fig_line = px.line(
    df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
    title=f"Évolution du Top {top_n}", template=plotly_template
)
fig_line.update_layout(font=dict(color=text_color), title_font_color=header_color)
st.plotly_chart(fig_line, use_container_width=True)

#====================================================================
# ------------------------- Tableau final ---------------------------
#====================================================================
st.subheader("📋 Aperçu des données filtrées")
st.dataframe(df_filtered, use_container_width=True)
