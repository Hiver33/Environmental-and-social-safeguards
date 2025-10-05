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
# ----------------------------- Thème -------------------------------
#====================================================================
page_width = "100%" if plein_ecran else "80%"
st.markdown(f"""
<style>
.stApp {{ background-color:#1a1d21; color:white; max-width:{page_width}; margin:auto; }}
h1,h2,h3{{color:#00ccff;}}
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
colors = ["#00ccff","#00ff99","#ffcc00","#ff6666"]
for col,(val,label),color in zip(cols,metrics,colors):
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
    title="Répartition par type de dépôt", template="plotly_dark", height=400
)
# 🏷️ Renommage des axes
fig_type.update_layout(
    xaxis_title="Type de dépôt",
    yaxis_title="Nombre de griefs"
)
# Avancement général avec couleurs fixes
colors_map_statut = {
    "Achevé": "#00ff99",
    "Grief non recevable": "#ffcc00",
    "En cours": "#636efa",
    "A traiter": "#ff6666"
}
fig_stat = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général",
    color="Statut_traitement", color_discrete_map=colors_map_statut,
    template="plotly_dark", height=400
)
fig_type.update_layout(
    legend_title_text = "Statut du traitement"
)
fig_stat.update_traces(textinfo="percent+label", textposition="inside")

# -------------------- Affichage côte à côte --------------------
if plein_ecran:
    # Plein écran : une colonne = les deux graphiques empilés (responsive)
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    # Normal : côte à côte
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)

# Histogramme par Nature
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title = "Nombre de griefs par nature", template="plotly_dark", height=400, color_discrete_map=colors_map_statut
)
# 🏷️ Renommage des axes
fig_nature.update_layout(
    xaxis_title="Nature de griefs",
    yaxis_title="Nombre",
    legend_title_text = "Statut du traitement"
)
st.plotly_chart(fig_nature, use_container_width=True)

# Répartition Communauté / Sexe
st.subheader("🏘️ Répartition par communauté et sexe")
if plein_ecran:
    fig_comm = px.bar(
        x=df_filtered["Communaute"].value_counts().sort_values().index,
        y=df_filtered["Communaute"].value_counts().sort_values().values,
        text=df_filtered["Communaute"].value_counts().sort_values().values,
        title="Nombre de griefs par communauté", template="plotly_dark", height=400
    )
    # 🏷️ Renommage des axes
    fig_comm.update_layout(
        xaxis_title="Village/Localité",
        yaxis_title="Nombre de griefs"
    )
    st.plotly_chart(fig_comm, use_container_width=True)

    fig_sexe = px.pie(
        df_filtered, names="Sexe", title="Répartition par sexe", template="plotly_dark", height=400
    )
    fig_sexe.update_traces(textinfo="percent+label", textposition="inside")
    st.plotly_chart(fig_sexe, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    fig_comm = px.bar(
        x=df_filtered["Communaute"].value_counts().sort_values().index,
        y=df_filtered["Communaute"].value_counts().sort_values().values,
        text=df_filtered["Communaute"].value_counts().sort_values().values,
        title="Nombre de griefs par communauté", template="plotly_dark", height=400
    )
    # 🏷️ Renommage des axes
    fig_comm.update_layout(
        xaxis_title="Village/Localité",
        yaxis_title="Nombre de griefs"
    )
    fig_sexe = px.pie(
        df_filtered, names="Sexe", title="Répartition par sexe", template="plotly_dark", height=400
    )
    fig_comm.update_layout(
        legend_title_text = "Sexe"
    )
    fig_sexe.update_traces(textinfo="percent+label", textposition="inside")
    c1.plotly_chart(fig_comm, use_container_width=True)
    c2.plotly_chart(fig_sexe, use_container_width=True)

# Nature par Sexe avec labels
st.subheader("👥 Nature des griefs par sexe")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()
fig_cat_sexe = px.bar(
    df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
    category_orders={"Nature_plainte": ordre_nature_tri},
    orientation="h", template="plotly_dark", height=400, text="Nombre",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
# 🏷️ Renommage des axes
fig_cat_sexe.update_layout(
        xaxis_title="Nombre",
        yaxis_title="Nature de griefs"
    )    
fig_cat_sexe.update_traces(textposition="inside")
st.plotly_chart(fig_cat_sexe, use_container_width=True)

# Evolution Top N
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_sel = st.selectbox("Filtrer par trimestre :", ["Tous"]+trimestres)
df_trim = df_filtered if trimestre_sel=="Tous" else df_filtered[df_filtered["Trimestre"]==trimestre_sel]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(
    df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
    title=f"Top {top_n} évolution", template="plotly_dark", height=400
)
fig_duree.update_layout(
        legend_title_text = "Nature de griefs"
    )
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# Durée moyenne
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(
        df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
        title="Durée moyenne de traitement par nature", template="plotly_dark", height=400
    )
    # 🏷️ Renommage des axes
    fig_duree.update_layout(
        xaxis_title="Nature de griefs",
        yaxis_title="Durée (Nb de jours)",
        legend_title_text = "Nature de griefs"
    )
    st.plotly_chart(fig_duree, use_container_width=True)

# Tableau final
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered, use_container_width=True)
