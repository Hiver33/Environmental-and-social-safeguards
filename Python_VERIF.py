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
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")
theme_choice = st.sidebar.radio("🎨 Apparence :", ["Clair", "Sombre"])

# 🎨 Définition des couleurs selon le thème
if theme_choice == "Clair":
    page_bg = "#f7f8fa"  # pas blanc pur
    sidebar_bg = "#e4e6eb"
    sidebar_text_color = "#1a1a1a"
    header_color = "#1a73e8"
    card_colors = ["#ADD8E6", "#B0E57C", "#FFE87C", "#FFA07A"]
    plotly_template = "plotly_white"
    graph_bg_color = "#efefef"  # gris très clair
    font_color = "#111111"
    grid_color = "#cccccc"
else:
    page_bg = "#121416"
    sidebar_bg = "#1c1e22"
    sidebar_text_color = "#ffffff"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
    graph_bg_color = "#1a1d21"  # sombre mais pas noir
    font_color = "#ffffff"
    grid_color = "#444444"

page_width = "100%" if plein_ecran else "80%"

# 🧩 Application du style CSS global
st.markdown(f"""
<style>
.stApp {{
    background-color: {page_bg};
    color: {font_color};
    max-width: {page_width};
    margin: auto;
}}

section[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
}}

section[data-testid="stSidebar"] * {{
    color: {sidebar_text_color} !important;
}}

section[data-testid="stSidebar"] div[data-baseweb="select"] > div > div,
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] > div > div {{
    background-color: {sidebar_bg} !important;
    color: {sidebar_text_color} !important;
}}

.stFileUploader {{
    background-color: #ffffff !important;
    color: blue !important;
    border-radius: 6px;
    padding: 8px;
}}

h1,h2,h3,h4 {{
    color: {header_color};
}}
</style>
""", unsafe_allow_html=True)

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

colors_map_statut = {
    "Achevé": "#00ff99",
    "Grief non recevable": "#ffcc00",
    "En cours": "#636efa",
    "A traiter": "#ff6666"
}

def update_layout_common(fig, title):
    fig.update_layout(
        title=title,
        title_font=dict(color=font_color, size=18),
        plot_bgcolor=graph_bg_color,
        paper_bgcolor=graph_bg_color,
        font=dict(color=font_color),
        xaxis=dict(showgrid=True, gridcolor=grid_color),
        yaxis=dict(showgrid=True, gridcolor=grid_color),
        legend=dict(title_font=dict(color=font_color), font=dict(color=font_color))
    )
    fig.update_traces(marker_line_width=0)

# --- Répartition par type de dépôt ---
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(x=type_counts.index, y=type_counts.values, text=type_counts.values,
                  template=plotly_template, height=400)
update_layout_common(fig_type, "Répartition par type de dépôt")

# --- Avancement général ---
fig_stat = px.pie(df_filtered, names="Statut_traitement",
                  color="Statut_traitement", color_discrete_map=colors_map_statut,
                  template=plotly_template, height=400)
fig_stat.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
update_layout_common(fig_stat, "Avancement général")

if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)

# --- Histogramme par nature ---
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
                          category_orders={"Nature_plainte": ordre_nature}, orientation="h",
                          template=plotly_template, color_discrete_map=colors_map_statut, height=400)
update_layout_common(fig_nature, "Nombre de griefs par nature")
st.plotly_chart(fig_nature, use_container_width=True)

# --- Communauté / Sexe ---
st.subheader("🏘️ Répartition par communauté et sexe")
c1, c2 = st.columns(2)

fig_comm = px.bar(x=df_filtered["Communaute"].value_counts().sort_values().index,
                  y=df_filtered["Communaute"].value_counts().sort_values().values,
                  text=df_filtered["Communaute"].value_counts().sort_values().values,
                  template=plotly_template, height=400)
update_layout_common(fig_comm, "Nombre de griefs par communauté")
c1.plotly_chart(fig_comm, use_container_width=True)

fig_sexe = px.pie(df_filtered, names="Sexe", template=plotly_template, height=400)
fig_sexe.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
update_layout_common(fig_sexe, "Répartition par sexe")
c2.plotly_chart(fig_sexe, use_container_width=True)

# --- Nature par Sexe ---
st.subheader("👥 Nature des griefs par sexe")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()
fig_cat_sexe = px.bar(df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
                      category_orders={"Nature_plainte": ordre_nature_tri}, orientation="h",
                      template=plotly_template, text="Nombre", height=400)
update_layout_common(fig_cat_sexe, "Nature des griefs par sexe")
st.plotly_chart(fig_cat_sexe, use_container_width=True)

# --- Évolution temporelle ---
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_sel = st.selectbox("Filtrer par trimestre :", ["Tous"] + trimestres)
df_trim = df_filtered if trimestre_sel == "Tous" else df_filtered[df_filtered["Trimestre"] == trimestre_sel]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
                   template=plotly_template, height=400)
update_layout_common(fig_line, f"Top {top_n} évolution")
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# --- Durée moyenne ---
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
                       template=plotly_template, height=400)
    update_layout_common(fig_duree, "Durée moyenne de traitement par nature")
    st.plotly_chart(fig_duree, use_container_width=True)

#====================================================================
# ------------------------ Tableau final ---------------------------
#====================================================================
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered, use_container_width=True)
