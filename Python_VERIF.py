import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# -------------------- Chargement des données --------------------
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
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file if uploaded_file else url_excel)

# -------------------- Vérification des colonnes --------------------
cols_req = ["Type_depot","Statut_traitement","Nature_plainte","Categorie",
            "Date_reception","Nb_jour","Communaute","Sexe"]
if df.empty or not all(col in df.columns for col in cols_req):
    st.stop()

# -------------------- Préparation --------------------
df["Date_reception"] = pd.to_datetime(df["Date_reception"], errors="coerce", dayfirst=True)
df = df.dropna(subset=["Date_reception"])
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()
df["Statut_traitement_clean"] = df["Statut_traitement"].str.strip()  # Nettoyage

# -------------------- Sidebar filtres --------------------
st.sidebar.header("Filtres")
annee_courante = datetime.now().year
annees_dispo = sorted(df["Année"].unique())
annee_choisie = st.sidebar.selectbox("📅 Filtrer par année :", annees_dispo,
                                     index=annees_dispo.index(annee_courante) if annee_courante in annees_dispo else 0)
Types = st.sidebar.multiselect("📂 Type de dépôt :", df["Type_depot"].unique(), default=df["Type_depot"].unique())
Statuts = st.sidebar.multiselect("✅ Statut de traitement :", df["Statut_traitement_clean"].unique(), default=df["Statut_traitement_clean"].unique())
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")

df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement_clean"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"]==annee_choisie]
if df_filtered.empty:
    st.warning("Aucun enregistrement après filtrage")
    st.stop()

# -------------------- Thème --------------------
page_width = "100%" if plein_ecran else "80%"
st.markdown(f"""
<style>
.stApp {{ background-color:#1a1d21; color:white; max-width:{page_width}; margin:auto; }}
h1,h2,h3{{color:#00ccff;}}
</style>
""", unsafe_allow_html=True)

# -------------------- Indicateurs --------------------
st.title("📊 Dashboard Suivi du MGG")
total = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement_clean"].isin(["Achevé","Grief non récevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement_clean"]=="En cours"])
non_traites = len(df_filtered[df_filtered["Statut_traitement_clean"]=="Non traité"])

cols = st.columns(4)
metrics = [(total,"Total"),(acheves,"Achevés"),(en_cours,"En cours"),(non_traites,"Non traités")]
colors = ["#00ccff","#90ee90","#ffcc00","#ff6666"]
for col,(val,label),color in zip(cols,metrics,colors):
    col.markdown(
        f"<div style='background:{color}; padding:15px; border-radius:15px;'>"
        f"<p style='font-size:28px; font-weight:bold;color:black'>{val}</p>"
        f"<p style='color:black; font-weight:bold'>{label}</p></div>",
        unsafe_allow_html=True
    )

# -------------------- Graphiques principaux --------------------
st.subheader("📈 Analyse visuelle")

# Répartition par type de dépôt
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(x=type_counts.index, y=type_counts.values, text=type_counts.values,
                  title="Répartition par type de dépôt", template="plotly_dark", height=400)
fig_type.update_traces(textposition="outside")

# Avancement général
all_status = df_filtered["Statut_traitement_clean"].unique()
theme_colors = px.colors.qualitative.Dark24
colors_map = {s:"#90ee90" if s=="Achevé" else theme_colors[i % len(theme_colors)] for i,s in enumerate(all_status)}
fig_stat = px.pie(df_filtered, names="Statut_traitement_clean", title="Avancement général des griefs",
                  color="Statut_traitement_clean", color_discrete_map=colors_map,
                  template="plotly_dark", height=400)
fig_stat.update_traces(textinfo="percent+label", textposition="inside")

c1, c2 = st.columns(2 if not plein_ecran else 1)
c1.plotly_chart(fig_type, use_container_width=True)
c2.plotly_chart(fig_stat, use_container_width=True)

# Histogramme par Nature
ordre_nature = df_filtered["Nature_plainte"].value_counts().index.tolist()
fig_nature = px.histogram(df_filtered, y="Nature_plainte", color="Statut_traitement_clean", text_auto=True,
                          category_orders={"Nature_plainte": ordre_nature}, orientation="h",
                          template="plotly_dark", height=400,
                          color_discrete_map=colors_map)
fig_nature.update_traces(textposition="inside")
st.plotly_chart(fig_nature, use_container_width=True)

# Répartition Communauté / Sexe
st.subheader("🏘️ Répartition par communauté et sexe")
c1, c2 = st.columns(2 if not plein_ecran else 1)
comm_counts = df_filtered["Communaute"].value_counts().sort_values()
fig_comm = px.bar(x=comm_counts.index, y=comm_counts.values, text=comm_counts.values,
                  title="Nombre de griefs par communauté", template="plotly_dark", height=400)
fig_comm.update_traces(marker_color="#00ccff", textposition="outside")
fig_sexe = px.pie(df_filtered, names="Sexe", title="Répartition par sexe", template="plotly_dark", height=400)
fig_sexe.update_traces(textinfo="percent+label", textposition="inside")
c1.plotly_chart(fig_comm, use_container_width=True)
c2.plotly_chart(fig_sexe, use_container_width=True)

# Nature par Sexe
st.subheader("👥 Nature des griefs par sexe")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()
fig_cat_sexe = px.bar(df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
                      category_orders={"Nature_plainte": ordre_nature_tri},
                      orientation="h", template="plotly_dark", height=400,
                      text="Nombre")
fig_cat_sexe.update_traces(textposition="inside")
st.plotly_chart(fig_cat_sexe, use_container_width=True)

# Evolution Top N
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :",3,10,5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_sel = st.selectbox("Filtrer par trimestre :", ["Tous"]+trimestres)
df_trim = df_filtered if trimestre_sel=="Tous" else df_filtered[df_filtered["Trimestre"]==trimestre_sel]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
                   title=f"Top {top_n} évolution", template="plotly_dark", height=400)
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)

# Durée moyenne
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
                       title="Durée moyenne par nature", template="plotly_dark", height=400)
    fig_duree.update_traces(textposition="outside")
    st.plotly_chart(fig_duree, use_container_width=True)

# Tableau final
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered, use_container_width=True)
