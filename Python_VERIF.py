## *************** Script Python Dashboard ***************
##            Projet PyDashboard (Thème sombre corrigé)
## ********************************************************

import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl
from datetime import datetime

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

url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?dl=1"
df = load_data(url_excel)

colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte", 
                      "Categorie", "Date_reception", "Nb_jour"]

if df.empty:
    st.stop()
if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Sidebar - Filtres interactifs
# ============================================================== 
st.sidebar.header("Filtres")

# Conversion date + extraction année
df['Date_reception'] = pd.to_datetime(df['Date_reception'], dayfirst=True)
df['Année'] = df['Date_reception'].dt.year

# Filtre année
annee_courante = datetime.now().year
annees_disponibles = sorted(df['Année'].unique())
annee_index = annees_disponibles.index(annee_courante) if annee_courante in annees_disponibles else 0
annee_choisie = st.sidebar.selectbox("📅 Filtrer par année :", annees_disponibles, index=annee_index)

df_filtered = df[df['Année'] == annee_choisie]

# Filtres type dépôt et statut
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
# Titre et indicateurs clés
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")

total_griefs = len(df_filtered)
acheves = len(df_filtered[(df_filtered["Statut_traitement"] == "Achevé") | 
                          (df_filtered["Statut_traitement"] == "Grief non récevable")])
en_cours = len(df_filtered[df_filtered["Statut_traitement"] == "En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"])

# --- CSS indicateurs clés (fond coloré + texte blanc)
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
with col1:
    st.metric(label="Total des griefs", value=total_griefs)
with col2:
    st.metric(label="Achevés", value=acheves)
with col3:
    st.metric(label="En cours", value=en_cours)
with col4:
    st.metric(label="Non traités", value=non_traites)

# ============================================================== 
# Graphiques ligne 1 : Type_depot et Statut
# ============================================================== 
st.subheader("📈 Analyse visuelle")

# Graphique barre Type_depot
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre")
ordre_type = ordre_type.sort_values(by="Nombre", ascending=True)
fig1 = px.bar(
    ordre_type,
    x="Type_depot",
    y="Nombre",
    text="Nombre",
    title="Répartition des plaintes par type de dépôt",
    height=350,
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)

# Graphique pie Statut
fig2 = px.pie(
    df_filtered,
    names="Statut_traitement",
    title="Avancement général des griefs",
    height=350,
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(marker=dict(line=dict(color='#1a1d21', width=2)), 
                   textposition='inside')

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.plotly_chart(fig1, use_container_width=True)
with col_g2:
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================== 
# Histogramme par Nature
# ============================================================== 
ordre_nature = df_filtered['Nature_plainte'].value_counts().index.tolist()
fig3 = px.histogram(
    df_filtered,
    y="Nature_plainte",
    color="Statut_traitement",
    title="Distribution par nature",
    text_auto=True,
    category_orders={"Nature_plainte": ordre_nature},
    orientation='h',
    height=400,
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
st.plotly_chart(fig3, use_container_width=True)

# ============================================================== 
# Graphique ligne : évolution mensuelle
# ============================================================== 
df_filtered['Mois'] = df_filtered['Date_reception'].dt.to_period('M').dt.to_timestamp()
df_filtered['Trimestre'] = df_filtered['Date_reception'].dt.to_period('Q').astype(str)

trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_disponibles.insert(0, "Tous")
trimestre_choisie = st.selectbox("Choisir un trimestre :", trimestre_disponibles)

if trimestre_choisie != "Tous":
    df_trim = df_filtered[df_filtered['Trimestre'] == trimestre_choisie]
else:
    df_trim = df_filtered.copy()

df_grief = df_trim.groupby(['Mois', 'Nature_plainte']).size().reset_index(name='Nombre_Griefs')

fig_line = px.line(
    df_grief,
    x="Mois",
    y="Nombre_Griefs",
    color="Nature_plainte",
    markers=True,
    title=f"Évolution mensuelle des griefs par nature ({annee_choisie})",
    height=400,
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# ============================================================== 
# Graphique durée moyenne de traitement
# ============================================================== 
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index()
    df_duree = df_duree.sort_values(by="Nb_jour")
    fig_duree = px.bar(
        df_duree,
        x="Nature_plainte",
        y="Nb_jour",
        title="Durée moyenne de traitement par nature",
        text_auto=".2f",
        height=400,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig_duree, use_container_width=True)
else:
    st.info("⚠️ Pas de colonne 'Nb_jour' pour calculer la durée moyenne de traitement.")

# ============================================================== 
# Tableau détaillé limité à 10 lignes
# ============================================================== 
max_lignes = 10
hauteur_ligne = 35
hauteur_tableau = min(len(df_filtered), max_lignes) * hauteur_ligne

st.subheader("📑 Tableau des griefs")
st.dataframe(
    df_filtered.style.background_gradient(cmap='Blues'),
    height=hauteur_tableau,
    use_container_width=True
)
