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
@st.cache_data(ttl=30)
def load_data(path):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

url_excel = "https://www.dropbox.com/scl/fi/ufku5z80buf14ldn0cei4/Table_MGG.xlsx?rlkey=zkfdat1vjlpkuveu7kfjhrxit&st=5uic6qsz&dl=1"
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file if uploaded_file else url_excel)

#====================================================================
# -------------------- Vérification des colonnes --------------------
#====================================================================
cols_req = ["Type_depot","Type","Statut_traitement","Nature_plainte",
            "Categorie","Date_reception","Nb_jour","Communaute","Sexe"]

if df.empty:
    st.error("❌ Le fichier Excel est vide ou n’a pas pu être chargé")
    st.stop()

st.write("✅ Colonnes disponibles :", df.columns.tolist())
st.write("📄 Nombre de lignes :", len(df))

# Vérification des colonnes manquantes
missing_cols = [col for col in cols_req if col not in df.columns]
if missing_cols:
    st.error(f"❌ Colonnes manquantes dans le fichier : {missing_cols}")
    st.stop()

st.success("✅ Toutes les colonnes requises sont présentes !")
else :
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
st.sidebar.header("🖌️ Apparence")
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")
theme_choice = st.sidebar.radio("🎨 Choisir le thème :", ["Clair", "Sombre"])

# Définition des couleurs selon le thème
if theme_choice == "Clair":
    page_bg = "#f5f5f5"
    sidebar_bg = "#dcdcdc"
    sidebar_text_color = "#1a1a1a"
    header_color = "#1a73e8"
    card_colors = ["#87CEFA", "#90EE90", "#FFD700", "#FF7F7F"]
    plotly_template = "plotly_white"
    graph_bg_color = "#efefef"
    font_color = "#000000"
else:
    page_bg = "#1a1d21"
    sidebar_bg = "#2c2f33"
    sidebar_text_color = "#ffffff"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
    graph_bg_color = "#2a2d33"
    font_color = "#ffffff"

page_width = "100%" if plein_ecran else "80%"

# Application du style CSS
st.markdown(f"""
<style>
.stApp {{
    background-color: {page_bg};
    color: {font_color};
    max-width: {page_width};
    margin: auto;
}}

[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
}}

[data-testid="stSidebar"] * {{
    color: {sidebar_text_color} !important;
}}

[data-testid="stSidebar"] div[data-baseweb="select"] > div > div,
[data-testid="stSidebar"] div[data-testid="stFileUploader"] > div > div {{
    background-color: {sidebar_bg} !important;
    color: {sidebar_text_color} !important;
}}

h1,h2,h3,h4 {{
    color: {header_color};
}}
</style>
""", unsafe_allow_html=True)

#====================================================================
# -------------------------- Indicateurs ----------------------------
#====================================================================
st.title("📊 Indicateurs de suivi MGG")
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

colors_map_statut = {
    "Achevé": "#00ff99",
    "Grief non recevable": "#ffcc00",
    "En cours": "#636efa",
    "A traiter": "#ff6666"
}
#-------------------------------------------------------------------------------------
# --- Répartition par type de dépôt ---
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=type_counts.index, y=type_counts.values, text=type_counts.values,
    title="Répartition par type de dépôt", template=plotly_template, height=400
)
fig_type.update_traces(marker_line_width=0)
fig_type.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Type de dépôt", yaxis_title="Nombre de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

# --- Avancement général ---
fig_stat = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général",
    color="Statut_traitement", color_discrete_map=colors_map_statut,
    template=plotly_template, height=400
)
fig_stat.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
fig_stat.update_layout(
    title_font=dict(color=font_color, size=18),
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)
#-------------------------------------------------------------------------------------

# --- Répartition par Type de population et Sexe ---
# --- Filtre d'affichage du genre ---
genre_mode = st.radio(
    "Affichage du genre (H/F):",
    ["Tout genre", "Catégoriser"],
    index=0,
    horizontal=True
)

# --- Préparation des données ---
df_pop_sexe = df_filtered.groupby(["Type", "Sexe"]).size().reset_index(name="Nombre")

# --- Cas 1 : fusionner tous les sexes ---
if genre_mode == "Tout genre":
    df_plot = (
        df_pop_sexe.groupby("Type")["Nombre"]
        .sum()
        .reset_index()
    )
    color_arg = None  # pas de coloration par sexe
    barmode = "relative"
else:
    df_plot = df_pop_sexe.copy()
    color_arg = "Sexe"
    barmode = "group"

# --- Tri croissant selon total des griefs ---
ordre_tri = (
    df_pop_sexe.groupby("Type")["Nombre"]
    .sum()
    .sort_values()
    .index.tolist()
)

# --- Création du graphique ---
fig_pop_sexe = px.bar(
    df_plot,
    x="Type",
    y="Nombre",
    color=color_arg,
    text="Nombre",
    title="Répartition par type de population",
    template=plotly_template,
    height=400,
    category_orders={"Type": ordre_tri},
    barmode=barmode
)

# Style du graphque
fig_pop_sexe.update_traces(marker_line_width=0)
fig_pop_sexe.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Type de population",
    yaxis_title="Nombre de griefs",
    plot_bgcolor=graph_bg_color,
    paper_bgcolor=graph_bg_color,
    font=dict(color=font_color),
)

st.plotly_chart(fig_pop_sexe, use_container_width=True)    # affichage dans streamlit
#-------------------------------------------------------------------------------------

# --- Histogramme par nature ---
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title="Nature de griefs par traitement", template=plotly_template,
    color_discrete_map=colors_map_statut, height=400
)
# Style du graphique
fig_nature.update_traces(marker_line_width=0)
fig_nature.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Nombre", yaxis_title="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color),
    legend_title_text="Statut de traitement"
)
st.plotly_chart(fig_nature, use_container_width=True)
#-------------------------------------------------------------------------------------

# --- Répartition Communauté / Sexe ---
st.subheader("🏘️ Répartition par communauté et sexe")
c1, c2 = st.columns(2)

# Graphique bar
fig_comm = px.bar(
    x=df_filtered["Communaute"].value_counts().sort_values().index,
    y=df_filtered["Communaute"].value_counts().sort_values().values,
    text=df_filtered["Communaute"].value_counts().sort_values().values,
    title="Nombre de griefs par communauté", template=plotly_template, height=400
)

# Style du graphique
fig_comm.update_traces(marker_line_width=0)
fig_comm.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Village/Localité", yaxis_title="Nombre de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)
c1.plotly_chart(fig_comm, use_container_width=True)    # affichage dans srtreamlit

# Graphique pie
fig_sexe = px.pie(
    df_filtered, names="Sexe", title="Répartition par sexe", template=plotly_template, height=400
)

# Style du graphique
fig_sexe.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
fig_sexe.update_layout(
    title_font=dict(color=font_color, size=18),
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)
c2.plotly_chart(fig_sexe, use_container_width=True)    # affichage dans srtreamlit
#-------------------------------------------------------------------------------------

# --- Nature par Sexe ---
st.subheader("👥 Nature des griefs par sexe")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()
fig_cat_sexe = px.bar(
    df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
    category_orders={"Nature_plainte": ordre_nature_tri}, orientation="h",
    template=plotly_template, text="Nombre", height=400
)

# Style du graphique
fig_cat_sexe.update_traces(marker_line_width=0)
fig_cat_sexe.update_layout(
    title="Nature des griefs par sexe",
    title_font=dict(color=font_color, size=18),
    xaxis_title="Nombre", yaxis_title="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)
st.plotly_chart(fig_cat_sexe, use_container_width=True)    # affichage dans srtreamlit
#-------------------------------------------------------------------------------------

# --- Évolution temporelle ---
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_sel = st.selectbox("Filtrer par trimestre :", ["Tous"] + trimestres)
df_trim = df_filtered if trimestre_sel == "Tous" else df_filtered[df_filtered["Trimestre"] == trimestre_sel]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
    title=f"Top {top_n} évolution", template=plotly_template, height=400)
fig_line.update_layout(
    title_font=dict(color=font_color, size=18),
    legend_title_text="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

# Style du graphique
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)    # affichage dans srtreamlit
#-------------------------------------------------------------------------------------

# --- Durée moyenne ---
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
        title="Durée moyenne de traitement par nature", template=plotly_template, height=400)
    fig_duree.update_traces(marker_line_width=0)
    
    # Style du graphique
    fig_duree.update_layout(
        title_font=dict(color=font_color, size=18),
        xaxis_title="Nature de griefs", yaxis_title="Durée (jours)",
        plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
        font=dict(color=font_color)
    )
    st.plotly_chart(fig_duree, use_container_width=True)    # affichage dans srtreamlit

#====================================================================
# ------------------------ Tableau final ---------------------------
#====================================================================
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered, use_container_width=True)
