## *************** Script Python Dashboard ***************
##            Projet PyDashboard (Thème sombre)
## *******************************************************

# importation des bibliotèques
import streamlit as st
import pandas as pd
import plotly.express as px
import openpyxl
from datetime import datetime

# ============================================================== 
# Chargement des données
# ==============================================================
@st.cache_data(ttl=300)         # initialiser le cache toutes les 5 min
def load_data(path): 
    try: 
        df = pd.read_excel(path, engine = 'openpyxl')
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"

# ============================================================== 
# Chargement dynamique du fichier source
# ==============================================================
st.sidebar.markdown("###🗃️ Charger un ficher Excel")
uploaded_file = st.sidebar.file_uploader(
    "Choisir un fichier Excel (.xlsx)", 
    type = ["XLSX"],
    help = "Importer ici votre propre fichier de données"
)

if uploaded_file is not None : 
    #si un fichier est importer par l'utilisateur
    df = load_data(uploaded_file)
else : 
    #sinon, on charge le fichier le fichier par défaut
    st.sidebar.info("Aucune source importée. Utilisation du fichier par défaut.")
    
colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte", "Categorie", "Date_reception", "Nb_jour"]
df = load_data(url_excel)

if df.empty:
    st.stop()           # stopper le processus si df nulle

if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Sidebar - Filtres interactifs
# ==============================================================
st.sidebar.header("Filtres")

# Filtre année globale
df['Date_reception'] = pd.to_datetime(df['Date_reception'], dayfirst = True)
df['Année'] = df['Date_reception'].dt.year

# extraire l'anée en cours
annee_courante = datetime.now().year

annees_disponibles = sorted(df['Année'].unique())
annees_disponibles.insert(0, "Toutes")
annee_choisie = st.sidebar.selectbox("📅 Filtrer par année :", annees_disponibles,
                                     index=annees_disponibles.index(annee_courante) if annee_courante in annees_disponibles else 0)

# Filtre de type selection multiples
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

# filtrer tout le contenu de la DataFrame
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie != "Toutes" : 
    df_filtered = df_filtered[df_filtered['Année'] == annee_choisie]

# ============================================================== 
# Titre et indicateurs clés
# ==============================================================
st.title("📊 Dashboard Suivi du MGG")

st.subheader("📌 Indicateurs clés")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total des griefs", len(df_filtered))
col2.metric("En cours", len(df_filtered[df_filtered["Statut_traitement"] == "En cours"]))
col3.metric("Achevé", len(df_filtered[(df_filtered["Statut_traitement"] == "Achevé") | 
                                      (df_filtered["Statut_traitement"] == "Grief non récevable")]))
col4.metric("Non traité", len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"]))

# ============================================================== 
# Graphiques ligne 1 : Type_depot et Statut
# ============================================================== 
st.subheader("📈 Analyse visuelle")

# Graphique barre : Type_depot
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre")
ordre_type = ordre_type.sort_values(by="Nombre", ascending=True)    # tri croissant

#dresser le graphique
fig1 = px.bar(
    ordre_type,
    x="Type_depot",
    y="Nombre",
    text="Nombre",
    title="Répartition des plaintes par type de dépôt",
    height=350,  # Taille initiale restaurée
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)

# Graphique pie : Statut
fig2 = px.pie(
    df_filtered,
    names="Statut_traitement",
    title="Avancement général des griefs",
    height=350,  # Taille initiale restaurée
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(marker=dict(line=dict(color='#1a1d21', width=2)), 
                   pull=[0.1, 0, 0],  # optionnel pour “décaler” certaines parts
                   textposition='inside')

col_g1, col_g2 = st.columns(2)
with col_g1:
    st.plotly_chart(fig1, use_container_width=True)
with col_g2:
    st.plotly_chart(fig2, use_container_width=True)

# ============================================================== 
# Histogramme par Nature
# ============================================================== 
ordre_nature = df_filtered['Nature_plainte'].value_counts().index.tolist()  # tri par fréquence

# dresser le graphique
fig3 = px.histogram(
    df_filtered,
    y="Nature_plainte",
    color="Statut_traitement",
    title="Distribution par nature",
    text_auto=True,
    category_orders={"Nature_plainte": ordre_nature},
    orientation='h',
    height=400,  # Taille initiale restaurée
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
st.plotly_chart(fig3, use_container_width=True)

# ============================================================== 
# Graphique ligne : évolution temporelle
# ============================================================== 
df_filtered['Date_reception'] = pd.to_datetime(df_filtered['Date_reception'], dayfirst=True)
df_filtered['Année'] = df_filtered['Date_reception'].dt.year
df_filtered['Mois'] = df_filtered['Date_reception'].dt.to_period('M').dt.to_timestamp()
df_filtered['Trimestre'] = df_filtered['Date_reception'].dt.to_period('Q').astype(str)          # ex : 2023Q1

# selecteur de trimestre
trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_disponibles.insert(0, "Tous")
trimestre_choisie = st.selectbox("Choisir un trimestre :", trimestre_disponibles)

if trimestre_choisie != "Tous":
    df_trim = df_filtered[df_filtered['Trimestre'] == trimestre_choisie]
else:
    df_trim = df_filtered

df_grief = df_trim.groupby(['Mois', 'Nature_plainte']).size().reset_index(name='Nombre_Griefs')

# dresser le graphqiue
fig_line = px.line(
    df_grief,
    x="Mois",
    y="Nombre_Griefs",
    color="Nature_plainte",
    markers=True,
    title=f"Évolution mensuelle des griefs par nature ({annee_choisie})",
    height=400,  # Taille initiale restaurée
    template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)

# ============================================================== 
# Affichage graphique ligne
# ============================================================== 
st.plotly_chart(fig_line, use_container_width=True)

# ============================================================== 
# Graphique durée moyenne de traitement (juste sous le graphique ligne)
# ============================================================== 
if "Nb_jour" in df_filtered.columns:
    df_duree = df_filtered.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index()    # calcul la moyenne du nb jour (arrondi)
    df_duree = df_duree.sort_values(by="Nb_jour", ascending=True)   # tri croissant
    
    # dresser le graphique
    fig_duree = px.bar(
        df_duree,
        x="Nature_plainte",
        y="Nb_jour",
        title="Durée moyenne de traitement par nature",
        text_auto=".2f",
        height=400,  # Taille initiale restaurée
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig_duree, use_container_width=True)
else:
    st.info("⚠️ Pas de colonne 'Nb_jour' pour calculer la durée moyenne de traitement.")

# ==============================================
# 🔹 Indicateurs clés du tableau de bord
# ==============================================
import streamlit as st

# --- CSS pour styliser uniquement les 4 indicateurs ---
st.markdown("""
<style>
/* Style général de chaque carte indicateur */
[data-testid="stMetric"] {
    background-color: #1c1c1c;   /* fond sombre */
    border-radius: 15px;         /* coins arrondis */
    padding: 15px;
    text-align: center;
    box-shadow: 0px 0px 10px rgba(255,255,255,0.1); /* effet lumineux doux */
}

/* Couleur et style du titre de chaque indicateur */
[data-testid="stMetricLabel"] {
    color: #ffffff !important;   /* texte blanc */
    font-size: 16px;
    font-weight: 600;
}

/* Couleur et style de la valeur principale */
[data-testid="stMetricValue"] {
    color: #ffffff !important;   /* valeur blanche */
    font-size: 28px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# --- Disposition sur 4 colonnes ---
col1, col2, col3, col4 = st.columns(4)

# --- Affichage des indicateurs ---
with col1:
    st.metric(label="Total des griefs", value=total_griefs)

with col2:
    st.metric(label="Achevés", value=acheves)

with col3:
    st.metric(label="En cours", value=en_cours)

with col4:
    st.metric(label="Non traités", value=non_traites)
