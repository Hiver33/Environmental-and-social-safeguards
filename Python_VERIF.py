## *************** Script Python Dashboard ***************
##            Projet PyDashboard (Thème sombre)
## *******************************************************

# importation des bibliothèques
import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl
from datetime import datetime

# ============================================================== 
# Chargement des données
# ============================================================== 
@st.cache_data(ttl=300)         # cache toutes les 5 min
def load_data(path): 
    try: 
        df = pd.read_excel(path, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"

# ============================================================== 
# Chargement dynamique du fichier source
# ============================================================== 
st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader(
    "Choisir un fichier Excel (.xlsx)", 
    type=["XLSX"],
    help="Importer ici votre propre fichier de données"
)

if uploaded_file is not None: 
    df = load_data(uploaded_file)
else: 
    st.sidebar.info("Aucune source importée. Utilisation du fichier par défaut.")
    df = load_data(url_excel)

colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte", "Categorie", "Date_reception", "Nb_jour"]

if df.empty:
    st.stop()

if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Sidebar - Filtres interactifs
# ============================================================== 
st.sidebar.header("Filtres")

# Filtre année globale
df['Date_reception'] = pd.to_datetime(df['Date_reception'], dayfirst=True)
df['Année'] = df['Date_reception'].dt.year
annee_courante = datetime.now().year
annees_disponibles = sorted(df['Année'].unique())
annees_disponibles.insert(0, annee_courante)  # afficher année en cours par défaut
annee_choisie = st.sidebar.selectbox("📅 Filtrer par année :", annees_disponibles,
                                     index=0)

# Filtre type dépôt et statut
Types = st.sidebar.multiselect(
    "📂 Filtrer par type de dépôt :",
    df["Type_depot"].dropna().unique(),
    default=df['Type_depot'].dropna().unique()
)
Statuts = st.sidebar.multiselect(
    "✅ Filtrer par statut de traitement :",
    df["Statut_traitement"].dropna().unique(),
    default=df["Statut_traitement"].dropna().unique()
)

# filtrer DataFrame
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie != "Toutes": 
    df_filtered = df_filtered[df_filtered['Année'] == annee_choisie]

# ============================================================== 
# Titre Dashboard
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")

# ============================================================== 
# 🔹 Indicateurs clés colorés
# ============================================================== 
total_griefs = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé", "Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"] == "En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"])

# CSS pour styliser indicateurs
st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #1c1c1c;  
    border-radius: 15px;
    padding: 15px;
    text-align: center;
    box-shadow: 0px 0px 10px rgba(255,255,255,0.1);
}
[data-testid="stMetricLabel"] {
    color: #ffffff !important;   
    font-size: 16px;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    font-size: 28px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# Palette colorée pour valeurs
valeur_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]  # Total, Achevés, En cours, Non traités

# Disposition sur 4 colonnes
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<p style="color:{valeur_colors[0]}; font-size:28px; font-weight:700;">{total_griefs}</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:white; font-size:16px; font-weight:600;">Total des griefs</p>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<p style="color:{valeur_colors[1]}; font-size:28px; font-weight:700;">{acheves}</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:white; font-size:16px; font-weight:600;">Achevés</p>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<p style="color:{valeur_colors[2]}; font-size:28px; font-weight:700;">{en_cours}</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:white; font-size:16px; font-weight:600;">En cours</p>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<p style="color:{valeur_colors[3]}; font-size:28px; font-weight:700;">{non_traites}</p>', unsafe_allow_html=True)
    st.markdown('<p style="color:white; font-size:16px; font-weight:600;">Non traités</p>', unsafe_allow_html=True)

# ============================================================== 
# Graphiques ligne 1 : Type_depot et Statut
# ============================================================== 
st.subheader("📈 Analyse visuelle")
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre").sort_values(by="Nombre")
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
fig2 = px.pie(
    df_filtered,
    names="Statut_traitement",
    title="Avancement général des griefs",
    height=350,
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(marker=dict(line=dict(color='#1a1d21', width=2)), textposition='inside')

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
# Graphique ligne : évolution temporelle
# ============================================================== 
df_filtered['Mois'] = df_filtered['Date_reception'].dt.to_period('M').dt.to_timestamp()
df_filtered['Trimestre'] = df_filtered['Date_reception'].dt.to_period('Q').astype(str)
trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_disponibles.insert(0, "Tous")
trimestre_choisie = st.selectbox("Choisir un trimestre :", trimestre_disponibles)
df_trim = df_filtered if trimestre_choisie=="Tous" else df_filtered[df_filtered['Trimestre']==trimestre_choisie]
df_grief = df_trim.groupby(['Mois','Nature_plainte']).size().reset_index(name='Nombre_Griefs')
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
if "Nb_jour" in df_filtered.columns:
    df_duree = df_filtered.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values(by="Nb_jour")
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
