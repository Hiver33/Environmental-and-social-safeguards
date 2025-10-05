## *************** Script Python Dashboard ***************
##        Projet PyDashboard – Version Plein Écran Responsive Dynamique
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

url_excel = "https://www.dropbox.com/scl/fi/ygl4aceq4uiuqt857hykc/Table_MGG.xlsx?rlkey=o33ioc0uz9vvtclyjp9liyk70&st=d01ynu9e&dl=1"

st.sidebar.markdown("### 🗃️ Charger un fichier Excel")
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file) if uploaded_file else load_data(url_excel)

colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte",
                      "Categorie", "Date_reception", "Nb_jour", "Communaute", "Sexe"]
if df.empty or not all(col in df.columns for col in colonnes_attendues):
    st.error("⚠️ Le fichier ne contient pas toutes les colonnes attendues ou est vide.")
    st.stop()

# ============================================================== 
# Préparation des données
# ============================================================== 
df["Date_reception"] = pd.to_datetime(df["Date_reception"], dayfirst=True)
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()

# ============================================================== 
# Filtres
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

plein_ecran = st.sidebar.toggle("🖥️ Mode Plein Écran")
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]

# ============================================================== 
# Style global responsive
# ============================================================== 
st.markdown(f"""
<style>
.stApp {{
    background-color: #1a1d21;
    color: white;
    max-width: 100%;
    margin-left:auto;
    margin-right:auto;
    padding:5px;
}}
[data-testid="stMetric"] {{
    border-radius: 15px;
    padding: 12px;
}}
h1,h2,h3{{color:#00ccff;}}
.stPlotlyChart {{
    width: 100% !important;
}}
.flex-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
}}
.flex-item {{
    flex: 1 1 45%;
    min-width: 300px;
}}
@media (max-width: 768px) {{
    .flex-item {{
        flex: 1 1 100%;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ============================================================== 
# Indicateurs clés
# ============================================================== 
st.title("📊 Dashboard Suivi du MGG")
st.subheader("📌 Indicateurs clés")

total_griefs = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé", "Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"]=="En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement"]=="Non traité"])

bg_colors = ["#00ccff","#00ff99","#ffcc00","#ff6666"]
cols = st.columns(4)
indicateurs = [(cols[i], bg_colors[i], v, l) for i,(v,l) in enumerate([
    (total_griefs,"Total des griefs"),(acheves,"Achevés"),
    (en_cours,"En cours"),(non_traites,"Non traités")
])]
for col,color,value,label in indicateurs:
    col.markdown(f"""
        <div style="background-color:{color}; padding:15px; border-radius:15px;">
            <p style="font-size:28px; font-weight:700; color:black;">{value}</p>
            <p style="font-size:16px; font-weight:600; color:black;">{label}</p>
        </div>
    """,unsafe_allow_html=True)

# ============================================================== 
# Couleurs uniformes pour "Achevé"
# ============================================================== 
color_map_statut = {
    "Achevé":"#00ff99",
    "Grief non récevable":"#636efa",
    "En cours":"#ffcc00",
    "Non traité":"#ff6666"
}

# ============================================================== 
# Graphiques principaux (responsive flex)
# ============================================================== 
st.subheader("📈 Analyse visuelle")
graph_list = []

# Type dépôt
ordre_type = df_filtered.groupby("Type_depot").size().reset_index(name="Nombre").sort_values("Nombre")
fig_type = px.bar(ordre_type, x="Type_depot", y="Nombre", text="Nombre",
                  title="Répartition des plaintes par type de dépôt",
                  height=400, template="plotly_dark")
graph_list.append(fig_type)

# Avancement général
fig_avancement = px.pie(df_filtered, names="Statut_traitement",
                        color="Statut_traitement", color_discrete_map=color_map_statut,
                        title="Avancement général des griefs", height=400, template="plotly_dark")
fig_avancement.update_traces(textinfo="percent+label", textposition="inside")
graph_list.append(fig_avancement)

# Histogramme nature
ordre_nature = df_filtered["Nature_plainte"].value_counts().index.tolist()
fig_nature = px.histogram(df_filtered, y="Nature_plainte", color="Statut_traitement",
                          category_orders={"Nature_plainte":ordre_nature},
                          title="Distribution par nature", text_auto=True,
                          orientation="h", height=400, template="plotly_dark",
                          color_discrete_map=color_map_statut)
graph_list.append(fig_nature)

# Communauté et sexe
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()

fig_comm = px.bar(df_filtered["Communaute"].value_counts().sort_values().reset_index(), 
                  x="index", y="Communaute", text="Communaute",
                  title="Nombre de griefs par communauté", height=400, template="plotly_dark")
graph_list.append(fig_comm)

fig_sexe = px.pie(df_filtered, names="Sexe", title="Répartition par sexe", height=400, template="plotly_dark")
graph_list.append(fig_sexe)

fig_cat_sexe_graph = px.bar(df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
                            category_orders={"Nature_plainte":ordre_nature_tri},
                            orientation="h", height=400, template="plotly_dark")
graph_list.append(fig_cat_sexe_graph)

# Flex container pour affichage dynamique
st.markdown('<div class="flex-container">', unsafe_allow_html=True)
for fig in graph_list:
    st.markdown('<div class="flex-item">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================== 
# Evolution temporelle Top N
# ============================================================== 
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Afficher le Top N des natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_choisi = st.selectbox("Filtrer par trimestre :", ["Tous"]+trimestres)
df_trim = df_filtered if trimestre_choisi=="Tous" else df_filtered[df_filtered["Trimestre"]==trimestre_choisi]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")

fig_line = px.line(df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
                   title=f"Évolution mensuelle des griefs (Top {top_n})", height=400, template="plotly_dark")
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# ============================================================== 
# Durée moyenne
# ============================================================== 
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
                       title="Durée moyenne de traitement par nature", height=400, template="plotly_dark")
    st.plotly_chart(fig_duree, use_container_width=True)

# ============================================================== 
# Tableau
# ============================================================== 
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered.style.background_gradient(cmap="Blues"), use_container_width=True)
