## *************** Script Python Dashboard ***************
##        Projet PyDashboard – Version Plein Écran Responsive
## *******************************************************

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ============================================================== 
# Chargement des données
# ============================================================== 
@st.cache_data(ttl=300)
def load_data(path):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

# Fichier par défaut
url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"

# ============================================================== 
# Sidebar : Upload dynamique
# ============================================================== 
st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    st.sidebar.info("Aucune source importée. Utilisation du fichier par défaut.")
    df = load_data(url_excel)

# Vérification des colonnes essentielles
colonnes_attendues = [
    "Type_depot", "Statut_traitement", "Nature_plainte",
    "Categorie", "Date_reception", "Nb_jour", "Localite"
]
if df.empty:
    st.stop()
if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Préparation des données
# ============================================================== 
df["Date_reception"] = pd.to_datetime(df["Date_reception"], dayfirst=True)
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()

# ============================================================== 
# Filtres dans la sidebar
# ============================================================== 
st.sidebar.header("Filtres")
annee_courante = datetime.now().year
annees_disponibles = sorted(df["Année"].unique())

annee_choisie = st.sidebar.selectbox(
    "📅 Filtrer par année :", 
    annees_disponibles, 
    index=annees_disponibles.index(annee_courante) if annee_courante in annees_disponibles else 0
)

Types = st.sidebar.multiselect(
    "📂 Type de dépôt :", df["Type_depot"].dropna().unique(),
    default=df["Type_depot"].dropna().unique()
)
Statuts = st.sidebar.multiselect(
    "✅ Statut de traitement :", df["Statut_traitement"].dropna().unique(),
    default=df["Statut_traitement"].dropna().unique()
)

# Option plein écran
plein_ecran = st.sidebar.toggle("🖥️ Activer le mode Plein Écran (paysage)")

# Filtrage
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]

# ============================================================== 
# Thème visuel & style
# ============================================================== 
page_width = "95%" if plein_ecran else "80%"
font_size = "18px" if plein_ecran else "16px"

st.markdown(f"""
<style>
.stApp {{
    background-color: #1a1d21;
    color: white;
    max-width: {page_width};
    margin: auto;
}}
[data-testid="stMetric"] {{
    border-radius: 15px;
    padding: 12px;
}}
h1, h2, h3 {{ color: #00ccff; font-size: {font_size}; }}
</style>
""", unsafe_allow_html=True)

# ============================================================== 
# Indicateurs clés
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")
st.subheader("📌 Indicateurs clés")

total_griefs = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé", "Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"] == "En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"])

bg_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
col1, col2, col3, col4 = st.columns(4)

indicateurs = [
    (col1, bg_colors[0], total_griefs, "Total des griefs"),
    (col2, bg_colors[1], acheves, "Achevés"),
    (col3, bg_colors[2], en_cours, "En cours"),
    (col4, bg_colors[3], non_traites, "Non traités"),
]
for col, color, value, label in indicateurs:
    col.markdown(
        f"""
        <div style="background-color:{color}; padding:15px; border-radius:15px;">
            <p style="font-size:28px; font-weight:700; color:black;">{value}</p>
            <p style="font-size:16px; font-weight:600; color:black;">{label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================== 
# Graphiques principaux
# ============================================================== 
st.subheader("📈 Analyse visuelle")

# Répartition par type de dépôt
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre").sort_values(by="Nombre", ascending=True)
fig1 = px.bar(
    ordre_type, x="Type_depot", y="Nombre", text="Nombre",
    title="Répartition des plaintes par type de dépôt",
    height=400, template="plotly_dark"
)

# Avancement général
fig2 = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général des griefs",
    height=400, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(textinfo="percent+label", textposition="inside")

c1, c2 = st.columns(2 if not plein_ecran else 1)
with c1: st.plotly_chart(fig1, use_container_width=True)
with c2: st.plotly_chart(fig2, use_container_width=True)

# ============================================================== 
# Histogramme par Nature
# ============================================================== 
ordre_nature = df_filtered["Nature_plainte"].value_counts().index.tolist()
fig3 = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement",
    title="Distribution par nature", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature},
    orientation="h", height=400, template="plotly_dark"
)
st.plotly_chart(fig3, use_container_width=True)

# ============================================================== 
# Graphique par village
# ============================================================== 
if "Localite" in df_filtered.columns:
    st.subheader("🏘️ Répartition des griefs par village")
    ordre_village = df_filtered["Localite"].value_counts().sort_values(ascending=True)
    fig_village = px.bar(
        x=ordre_village.index, y=ordre_village.values,
        labels={"x": "Village", "y": "Nombre de griefs"},
        text=ordre_village.values,
        title="Répartition des griefs par villages",
        height=400, template="plotly_dark"
    )
    st.plotly_chart(fig_village, use_container_width=True)

# ============================================================== 
# Graphique ligne : évolution temporelle (Top N)
# ============================================================== 
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Afficher le Top N des natures :", 3, 10, 5)

trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_choisi = st.selectbox("Filtrer par trimestre :", ["Tous"] + trimestres)
df_trim = df_filtered if trimestre_choisi == "Tous" else df_filtered[df_filtered["Trimestre"] == trimestre_choisi]

top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois", "Nature_plainte"]).size().reset_index(name="Nombre")

fig_line = px.line(
    df_line, x="Mois", y="Nombre", color="Nature_plainte",
    markers=True, title=f"Évolution mensuelle des griefs (Top {top_n})",
    height=400, template="plotly_dark"
)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# ============================================================== 
# Durée moyenne
# ============================================================== 
if "Nb_jour" in df_trim.columns:
    st.subheader("⏱️ Durée moyenne de traitement")
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values(by="Nb_jour")
    fig_duree = px.bar(
        df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
        title="Durée moyenne de traitement par nature", height=400, template="plotly_dark"
    )
    st.plotly_chart(fig_duree, use_container_width=True)

# ============================================================== 
# Tableau des données
# ============================================================== 
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered.style.background_gradient(cmap="Blues"), use_container_width=True)
