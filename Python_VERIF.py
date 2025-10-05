## *************** Script Python Dashboard ***************
##            Projet PyDashboard (Thème sombre amélioré)
## *******************************************************

# Importation des bibliothèques
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
        df = pd.read_excel(path, engine='openpyxl')
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

# Fichier par défaut
url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"

# ============================================================== 
# Sidebar - Upload dynamique
# ============================================================== 
st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader(
    "Choisir un fichier Excel (.xlsx)", 
    type=["xlsx"],
    help="Importer ici votre propre fichier de données"
)

if uploaded_file is not None: 
    df = load_data(uploaded_file)
else: 
    st.sidebar.info("Aucune source importée. Utilisation du fichier par défaut.")
    df = load_data(url_excel)

# Colonnes attendues
colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte", 
                      "Categorie", "Date_reception", "Nb_jour", "Communaute", "Sexe"]

if df.empty:
    st.stop()
if not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues.")
    st.stop()

# ============================================================== 
# Sidebar - Filtres interactifs
# ============================================================== 
st.sidebar.header("Filtres")
df['Date_reception'] = pd.to_datetime(df['Date_reception'], dayfirst=True)
df['Année'] = df['Date_reception'].dt.year
df['Trimestre'] = df['Date_reception'].dt.to_period('Q').astype(str)
df['Mois'] = df['Date_reception'].dt.to_period('M').dt.to_timestamp()

# Bouton reset
if st.sidebar.button("🔄 Réinitialiser les filtres"):
    st.experimental_rerun()

# Filtre année
annee_courante = datetime.now().year
annees_disponibles = sorted(df['Année'].unique())
annee_choisie = st.sidebar.selectbox(
    "📅 Filtrer par année :", 
    annees_disponibles, 
    index=annees_disponibles.index(annee_courante) if annee_courante in annees_disponibles else 0
)

# Filtre type de dépôt et statut
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

# Filtrage global
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered['Année'] == annee_choisie]

# ============================================================== 
# Indicateurs clés avec fond coloré et texte blanc
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")
st.subheader("📌 Indicateurs clés")

total_griefs = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé", "Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"] == "En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"] == "Non traité"])

bg_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
if non_traites > 50:
    bg_colors[3] = "#b30000"

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div style="background-color:{bg_colors[0]}; padding:15px; border-radius:15px;">'
                f'<p style="font-size:28px; font-weight:700; color:black;">{total_griefs}</p>'
                f'<p style="font-size:16px; font-weight:600; color:black;">Total des griefs</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div style="background-color:{bg_colors[1]}; padding:15px; border-radius:15px;">'
                f'<p style="font-size:28px; font-weight:700; color:black;">{acheves}</p>'
                f'<p style="font-size:16px; font-weight:600; color:black;">Achevés</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div style="background-color:{bg_colors[2]}; padding:15px; border-radius:15px;">'
                f'<p style="font-size:28px; font-weight:700; color:black;">{en_cours}</p>'
                f'<p style="font-size:16px; font-weight:600; color:black;">En cours</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div style="background-color:{bg_colors[3]}; padding:15px; border-radius:15px;">'
                f'<p style="font-size:28px; font-weight:700; color:black;">{non_traites}</p>'
                f'<p style="font-size:16px; font-weight:600; color:black;">Non traités</p></div>', unsafe_allow_html=True)

# ============================================================== 
# Graphiques Type_depot et Statut
# ============================================================== 
st.subheader("📈 Analyse visuelle")
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre").sort_values(by="Nombre", ascending=True)
fig1 = px.bar(
    ordre_type, x="Type_depot", y="Nombre", text="Nombre",
    title="Répartition des plaintes par type de dépôt",
    height=350, template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
fig2 = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général des griefs",
    height=350, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2
)
fig2.update_traces(marker=dict(line=dict(color='#1a1d21', width=2)),
                   textinfo='percent+label',
                   hovertemplate='<b>%{label}</b><br>Nombre: %{value}<br>Pourcentage: %{percent}',
                   pull=[0.05 if val==df_filtered["Statut_traitement"].value_counts().idxmax() else 0 
                         for val in df_filtered["Statut_traitement"].unique()],
                   textposition='inside')

col_g1, col_g2 = st.columns(2)
with col_g1: st.plotly_chart(fig1, use_container_width=True)
with col_g2: st.plotly_chart(fig2, use_container_width=True)

# ============================================================== 
# Histogramme par Nature
# ============================================================== 
ordre_nature = df_filtered['Nature_plainte'].value_counts().index.tolist()
fig3 = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement",
    title="Distribution par nature", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature},
    orientation='h', height=400, template="plotly_dark",
    color_discrete_sequence=px.colors.qualitative.Plotly
)
st.plotly_chart(fig3, use_container_width=True)

# ============================================================== 
# Graphique Nb de griefs par Communaute et répartition Sexe
# ============================================================== 
if "Communaute" in df_filtered.columns and not df_filtered["Communaute"].dropna().empty:
    df_comm = df_filtered.groupby("Communaute").size().reset_index(name="Nombre")
    df_comm = df_comm.sort_values(by="Nombre", ascending=True)
    fig_comm = px.bar(df_comm, x="Nombre", y="Communaute", orientation='h',
                      title="Nombre de griefs par Communauté", text="Nombre",
                      template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Plotly)
    st.plotly_chart(fig_comm, use_container_width=True)

if "Sexe" in df_filtered.columns and not df_filtered["Sexe"].dropna().empty:
    df_sexe = df_filtered.groupby("Sexe").size().reset_index(name="Nombre")
    fig_sexe = px.pie(df_sexe, names="Sexe", values="Nombre", title="Répartition par Sexe",
                      template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_sexe, use_container_width=True)

# ============================================================== 
# Graphique Nature x Sexe
# ============================================================== 
if "Nature_plainte" in df_filtered.columns and "Sexe" in df_filtered.columns:
    df_ns = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
    if not df_ns.empty:
        fig_ns = px.bar(df_ns, x="Nombre", y="Nature_plainte", color="Sexe",
                        orientation='h', barmode='group',
                        title="Nature des griefs par Sexe",
                        template="plotly_dark", text="Nombre",
                        color_discrete_sequence=px.colors.qualitative.Plotly)
        st.plotly_chart(fig_ns, use_container_width=True)

# ============================================================== 
# Filtre Trimestre avant graphique évolution
# ============================================================== 
trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_choisie = st.selectbox("Choisir un trimestre :", ["Tous"] + trimestre_disponibles)
if trimestre_choisie != "Tous":
    df_trim = df_filtered[df_filtered['Trimestre'] == trimestre_choisie]
else:
    df_trim = df_filtered

# ============================================================== 
# Graphique évolution temporelle Top N natures
# ============================================================== 
top_n = st.sidebar.slider("Top N Natures", min_value=1, max_value=10, value=3)
top_natures = df_trim['Nature_plainte'].value_counts().nlargest(top_n).index.tolist()
df_line_top = df_trim[df_trim['Nature_plainte'].isin(top_natures)]
if not df_line_top.empty:
    df_grief = df_line_top.groupby(['Mois','Nature_plainte']).size().reset_index(name='Nombre_Griefs')
    if not df_grief.empty:
        fig_line = px.line(
            df_grief, x="Mois", y="Nombre_Griefs", color="Nature_plainte",
            markers=True, title=f"Évolution mensuelle des griefs (Top {top_n} natures) - {annee_choisie}",
