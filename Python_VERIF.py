## *************** Script Python Dashboard ***************
##            Projet PyDashboard (Thème sombre stable)
## ********************************************************

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import openpyxl

# ============================================================== 
# Chargement des données
# ============================================================== 
@st.cache_data(ttl=300)
def load_data(path):
    try:
        df = pd.read_excel(path, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

# ----- Fichier par défaut
url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?dl=1"

# ----- Sidebar - uploader fichier optionnel
st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader(
    "Choisir un fichier Excel (.xlsx)", type=["XLSX"]
)

if uploaded_file is not None:
    df = load_data(uploaded_file)
else:
    st.sidebar.info("Aucun fichier importé. Utilisation du fichier par défaut.")
    df = load_data(url_excel)

colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte",
                      "Categorie", "Date_reception", "Nb_jour"]

if df.empty or not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier est vide ou ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Conversion dates et ajout colonnes dérivées
# ============================================================== 
df['Date_reception'] = pd.to_datetime(df['Date_reception'], dayfirst=True)
df['Année'] = df['Date_reception'].dt.year
df['Mois'] = df['Date_reception'].dt.to_period('M').dt.to_timestamp()
df['Trimestre'] = df['Date_reception'].dt.to_period('Q').astype(str)

# ============================================================== 
# Sidebar - filtres
# ============================================================== 
st.sidebar.header("Filtres")

# 1️⃣ Filtre année
annee_courante = datetime.now().year
annees_disponibles = sorted(df['Année'].unique())
annee_index = annees_disponibles.index(annee_courante) if annee_courante in annees_disponibles else 0
annee_choisie = st.sidebar.selectbox("📅 Filtrer par année :", annees_disponibles, index=annee_index)
df_filtered = df[df['Année'] == annee_choisie]

# 2️⃣ Filtre trimestre
trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_disponibles.insert(0, "Tous")
trimestre_choisie = st.sidebar.selectbox("Choisir un trimestre :", trimestre_disponibles)
if trimestre_choisie != "Tous":
    df_filtered = df_filtered[df_filtered['Trimestre'] == trimestre_choisie]

# 3️⃣ Filtre type dépôt et statut
Types = st.sidebar.multiselect(
    "📂 Filtrer par type de dépôt :",
    df_filtered["Type_depot"].dropna().unique(),
    default=df_filtered['Type_depot'].dropna().unique()
)
Statuts = st.sidebar.multiselect(
    "✅ Filtrer par statut de traitement :",
    df_filtered["Statut_traitement"].dropna().unique(),
    default=df_filtered["Statut_traitement"].dropna().unique()
)
df_filtered = df_filtered[df_filtered["Type_depot"].isin(Types) &
                          df_filtered["Statut_traitement"].isin(Statuts)]

# ============================================================== 
# Indicateurs clés
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")

total_griefs = len(df_filtered)
acheves = len(df_filtered[(df_filtered["Statut_traitement"] == "Achevé") |
                          (df_filtered["Statut_traitement"] == "Grief non récevable")])
en_cours = len(df_filtered[df_filtered["Statut_traitement"] == "En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"])

st.markdown("""
<style>
[data-testid="stMetric"] { border-radius:15px; padding:15px; text-align:center; box-shadow:0px 0px 10px rgba(255,255,255,0.1);}
[data-testid="stMetricLabel"] { color:white !important; font-size:16px; font-weight:600;}
[data-testid="stMetricValue"] { color:white !important; font-size:28px; font-weight:700;}
#col1 {background-color:#636EFA;}
#col2 {background-color:#EF553B;}
#col3 {background-color:#00CC96;}
#col4 {background-color:#AB63FA;}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total des griefs", total_griefs)
with col2: st.metric("Achevés", acheves)
with col3: st.metric("En cours", en_cours)
with col4: st.metric("Non traités", non_traites)

# ============================================================== 
# Graphiques
# ============================================================== 
st.subheader("📈 Analyse visuelle")

# 1️⃣ Répartition Type_depot
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre").sort_values("Nombre")
fig1 = px.bar(ordre_type, x="Type_depot", y="Nombre", text="Nombre",
              title="Répartition des plaintes par type de dépôt",
              height=350, template="plotly_dark",
              color_discrete_sequence=px.colors.qualitative.Plotly)

# 2️⃣ Pie Statut
fig2 = px.pie(df_filtered, names="Statut_traitement",
              title="Avancement général des griefs", height=350,
              template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
fig2.update_traces(marker=dict(line=dict(color='#1a1d21', width=2)), textposition='inside')

col_g1, col_g2 = st.columns(2)
with col_g1: st.plotly_chart(fig1, use_container_width=True)
with col_g2: st.plotly_chart(fig2, use_container_width=True)

# 3️⃣ Histogramme Nature
ordre_nature = df_filtered['Nature_plainte'].value_counts().index.tolist()
fig3 = px.histogram(df_filtered, y="Nature_plainte", color="Statut_traitement",
                    title="Distribution par nature", text_auto=True,
                    category_orders={"Nature_plainte": ordre_nature},
                    orientation='h', height=400,
                    template="plotly_dark",
                    color_discrete_sequence=px.colors.qualitative.Plotly)
st.plotly_chart(fig3, use_container_width=True)

# 4️⃣ Graphique ligne : évolution mensuelle
df_grief = df_filtered.groupby(['Mois', 'Nature_plainte']).size().reset_index(name='Nombre_Griefs')
fig_line = px.line(df_grief, x="Mois", y="Nombre_Griefs", color="Nature_plainte",
                   markers=True, title=f"Évolution mensuelle des griefs ({annee_choisie})",
                   height=400, template="plotly_dark",
                   color_discrete_sequence=px.colors.qualitative.Plotly)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# 5️⃣ Graphique durée moyenne
if "Nb_jour" in df_filtered.columns and not df_filtered.empty:
    df_duree = df_filtered.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index()
    df_duree = df_duree.sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour",
                       title="Durée moyenne de traitement par nature",
                       text_auto=".2f", height=400, template="plotly_dark",
                       color_discrete_sequence=px.colors.qualitative.Plotly)
    st.plotly_chart(fig_duree, use_container_width=True)
else:
    st.info("⚠️ Pas de colonne 'Nb_jour' pour calculer la durée moyenne de traitement.")

# 6️⃣ Tableau limité
max_lignes = 10
hauteur_tableau = min(len(df_filtered), max_lignes) * 35
st.subheader("📑 Tableau des griefs")
st.dataframe(df_filtered.style.background_gradient(cmap='Blues'),
             height=hauteur_tableau, use_container_width=True)
