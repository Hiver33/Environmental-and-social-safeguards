## *************** Script Python Dashboard ***************
##        Projet PyDashboard – Version Plein Écran Responsive
## *******************************************************

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import io
import requests

# ============================================================== 
# Fonction pour charger les données Excel
# ============================================================== 
@st.cache_data(ttl=300)
def load_data(path_or_url):
    try:
        if path_or_url.startswith("http"):
            r = requests.get(path_or_url)
            r.raise_for_status()
            df = pd.read_excel(io.BytesIO(r.content), engine="openpyxl")
        else:
            df = pd.read_excel(path_or_url, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

# ============================================================== 
# Fichier par défaut (Dropbox dl=1 pour lien direct)
# ============================================================== 
url_excel = "https://www.dropbox.com/s/ygl4aceq4uiuqt857hykc70/Table_MGG.xlsx?dl=1"

# ============================================================== 
# Sidebar : Upload dynamique
# ============================================================== 
st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file if uploaded_file else url_excel)

# Colonnes attendues
colonnes_attendues = ["Type_depot","Statut_traitement","Nature_plainte","Categorie",
                      "Date_reception","Nb_jour","Communaute","Sexe"]
if df.empty:
    st.stop()
if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Préparation des données
# ============================================================== 
df["Date_reception"] = pd.to_datetime(df["Date_reception"], errors="coerce", dayfirst=True)
df = df.dropna(subset=["Date_reception"])
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()

# ============================================================== 
# Sidebar - filtres
# ============================================================== 
st.sidebar.header("Filtres")
annee_courante = datetime.now().year
annees_dispo = sorted(df["Année"].unique())
annee_choisie = st.sidebar.selectbox(
    "📅 Filtrer par année :", annees_dispo,
    index=annees_dispo.index(annee_courante) if annee_courante in annees_dispo else 0
)

Types = st.sidebar.multiselect(
    "📂 Type de dépôt :", df["Type_depot"].unique(),
    default=df["Type_depot"].unique()
)
Statuts = st.sidebar.multiselect(
    "✅ Statut de traitement :", df["Statut_traitement"].unique(),
    default=df["Statut_traitement"].unique()
)

plein_ecran = st.sidebar.toggle("🖥️ Activer le mode Plein Écran (paysage)")

# Filtrage
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]
if df_filtered.empty:
    st.warning("⚠️ Aucun enregistrement après filtrage.")
    st.stop()

# ============================================================== 
# Style général
# ============================================================== 
page_width = "100%" if plein_ecran else "80%"
st.markdown(f"""
<style>
.stApp {{
    background-color:#1a1d21;
    color:white;
    max-width:{page_width};
    margin:auto;
}}
h1,h2,h3{{color:#00ccff;}}
</style>
""", unsafe_allow_html=True)

# ============================================================== 
# Indicateurs clés - alignement à gauche, en gras
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")
st.subheader("📌 Indicateurs clés")

total_griefs = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé","Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"]=="En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"]=="Non traité"])

cols = st.columns(4)
metrics = [(total_griefs,"Total des griefs"),
           (acheves,"Achevés"),
           (en_cours,"En cours"),
           (non_traites,"Non traités")]

colors = ["#00ccff","#90ee90","#ffcc00","#ff6666"]

for col,(val,label),color in zip(cols,metrics,colors):
    col.markdown(f"""
        <div style='background-color:{color}; padding:15px; border-radius:15px; text-align:left;'>
            <p style='font-size:28px; font-weight:bold; color:black'>{val}</p>
            <p style='font-size:16px; font-weight:bold; color:black'>{label}</p>
        </div>
    """, unsafe_allow_html=True)

# ============================================================== 
# Graphiques principaux
# ============================================================== 
st.subheader("📈 Analyse visuelle")

# --- Répartition par type de dépôt ---
ordre_type = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=ordre_type.index, y=ordre_type.values, text=ordre_type.values,
    title="Répartition des plaintes par type de dépôt",
    template="plotly_dark", height=400
)

# --- Avancement général des griefs ---
stat_counts = df_filtered["Statut_traitement"].value_counts()
colors_map = {s:"#90ee90" if s=="Achevé" else px.colors.qualitative.Plotly[i%10] 
              for i,s in enumerate(stat_counts.index)}
fig_stat = px.pie(
    df_filtered, names="Statut_traitement", values=stat_counts.values,
    color="Statut_traitement", color_discrete_map=colors_map,
    title="Avancement général des griefs", template="plotly_dark", height=400
)
fig_stat.update_traces(textinfo="percent+label", textposition="inside")

c1,c2 = st.columns(2 if not plein_ecran else 1)
c1.plotly_chart(fig_type,use_container_width=True)
c2.plotly_chart(fig_stat,use_container_width=True)

# --- Distribution par Nature ---
ordre_nature = df_filtered["Nature_plainte"].value_counts().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement",
    title="Distribution par nature", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature},
    orientation="h", height=400, template="plotly_dark",
    color_discrete_map={s:"#90ee90" if s=="Achevé" else px.colors.qualitative.Plotly[i%10] 
                        for i,s in enumerate(df_filtered["Statut_traitement"].unique())}
)
st.plotly_chart(fig_nature,use_container_width=True)

# --- Répartition par Communauté et Sexe ---
st.subheader("🏘️ Répartition des griefs par communauté et par sexe")
col_c1,col_c2 = st.columns(2 if not plein_ecran else 1)

# Nb de griefs par communauté
ordre_comm = df_filtered["Communaute"].value_counts().sort_values()
fig_comm = px.bar(
    x=ordre_comm.index, y=ordre_comm.values, text=ordre_comm.values,
    labels={"x":"Communauté","y":"Nombre de griefs"},
    title="Nombre de griefs par communauté", template="plotly_dark", height=400
)

# Répartition par sexe
fig_sexe = px.pie(
    df_filtered, names="Sexe", title="Répartition des griefs par sexe",
    height=400, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Plotly
)
fig_sexe.update_traces(textinfo="percent+label", textposition="inside")

col_c1.plotly_chart(fig_comm,use_container_width=True)
col_c2.plotly_chart(fig_sexe,use_container_width=True)

# --- Nature des griefs par sexe (tri croissant + labels) ---
st.subheader("👥 Nature des griefs par sexe")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values(ascending=True).index.tolist()
fig_cat_sexe = px.bar(
    df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
    category_orders={"Nature_plainte": ordre_nature_tri},
    orientation="h", title="Nature des griefs par sexe",
    template="plotly_dark", height=400, text="Nombre"
)
st.plotly_chart(fig_cat_sexe,use_container_width=True)

# --- Évolution temporelle (Top N) ---
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Afficher le Top N des natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_choisi = st.selectbox("Filtrer par trimestre :", ["Tous"]+trimestres)
df_trim = df_filtered if trimestre_choisi=="Tous" else df_filtered[df_filtered["Trimestre"]==trimestre_choisi]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(df_line,x="Mois",y="Nombre",color="Nature_plainte",markers=True,
                   title=f"Évolution mensuelle des griefs (Top {top_n})",
                   template="plotly_dark", height=400)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line,use_container_width=True)

# --- Durée moyenne de traitement ---
if "Nb_jour" in df_trim.columns:
    st.subheader("⏱️ Durée moyenne de traitement")
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values(by="Nb_jour")
    fig_duree = px.bar(df_duree,x="Nature_plainte",y="Nb_jour",text_auto=".1f",
                       title="Durée moyenne de traitement par nature", template="plotly_dark", height=400)
    st.plotly_chart(fig_duree,use_container_width=True)

# --- Tableau final ---
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered.style.background_gradient(cmap="Blues"), use_container_width=True)
