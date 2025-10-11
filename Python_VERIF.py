#*********************** Projet GriefPy ***************************
#     Dashboard interactif pour la visualisation des indicateurs
#******************************************************************

#==================================================================
# ------------------ Chargement des bibliothèques -----------------
#==================================================================
import os
import requests
import pandas as pd
import geopandas as gpd
import folium
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from shapely.geometry import Point
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from branca.element import Template, MacroElement
from datetime import datetime

#=================================================================
# -------------------- Chargement des données --------------------
#=================================================================
@st.cache_data(ttl=30)
def load_data(path):
    try:
        df = pd.read_excel(path, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel : {e}")
        return pd.DataFrame()

url_excel = "https://www.dropbox.com/scl/fi/z8djqa2kmwvv5rpy1qgc3/Table_MGG.xlsx?rlkey=knqski5ezathyuo1v44lh6icy&st=cyyjc912&dl=1"
uploaded_file = st.sidebar.file_uploader("Choisir un fichier Excel (.xlsx)", type=["xlsx"])
df = load_data(uploaded_file if uploaded_file else url_excel)

#====================================================================
# -------------------- Vérification des colonnes --------------------
#====================================================================
cols_req = [
    "Type_depot","Type","Statut_traitement","Nature_plainte",
    "Categorie","Date_reception","Nb_jour","Communaute","Sexe", 
    "Classement"
]

if df.empty:
    st.error("❌ Le fichier Excel est vide ou n’a pas pu être chargé")
    st.stop()

# Vérification des colonnes manquantes
missing_cols = [col for col in cols_req if col not in df.columns]
if missing_cols:
    st.error(f"❌ Colonnes manquantes dans le fichier : {missing_cols}")
    st.stop()

# Si tout est bon, on poursuit sans afficher aucun message
df["Date_reception"] = pd.to_datetime(df["Date_reception"], errors="coerce", dayfirst=True)
df = df.dropna(subset=["Date_reception"])
df["Année"] = df["Date_reception"].dt.year
df["Trimestre"] = df["Date_reception"].dt.to_period("Q").astype(str)
df["Mois"] = df["Date_reception"].dt.to_period("M").dt.to_timestamp()

#====================================================================
# --------------------------- Filtres -------------------------------
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

# --- Dataframe filtré pour les graphiques ---
df_filtered = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)]
if annee_choisie:
    df_filtered = df_filtered[df_filtered["Année"] == annee_choisie]
if df_filtered.empty:
    st.warning("Aucun enregistrement après filtrage")
    st.stop()

# --- Dataframe filtré pour la carte ---
df_filtered_2 = df[df["Type_depot"].isin(Types) & df["Statut_traitement"].isin(Statuts)].copy()
if annee_choisie:
    df_filtered_2 = df_filtered_2[df_filtered_2["Année"] == annee_choisie]
    
# Nettoyage pour la carte
df_filtered_2["Communaute"] = df_filtered_2["Communaute"].astype(str).str.strip().str.lower()
df_filtered_2["Statut_traitement"] = df_filtered_2["Statut_traitement"].replace(["nan","NaN","None",""], pd.NA)

#====================================================================
# ---------------------- Apparence / Thème --------------------------
#====================================================================
st.sidebar.markdown("---")
st.sidebar.header("🖌️ Apparence")
plein_ecran = st.sidebar.toggle("🖥️ Plein écran")
theme_choice = st.sidebar.radio("🎨 Choisir le thème :", ["Clair", "Sombre"])

# Définition des couleurs selon le thème
if theme_choice == "Clair":
    page_bg = "#f5f5f5"
    sidebar_bg = "#dcdcdc"
    sidebar_text_color = "#1a1a1a"
    header_color = "#1a73e8"
    card_colors = ["#87CEFA", "#90EE90", "#FFD700", "#FF7F7F"]
    plotly_template = "plotly_white"
    graph_bg_color = "#efefef"
    font_color = "#000000"
else:
    page_bg = "#1a1d21"
    sidebar_bg = "#2c2f33"
    sidebar_text_color = "#ffffff"
    header_color = "#00ccff"
    card_colors = ["#00ccff", "#00ff99", "#ffcc00", "#ff6666"]
    plotly_template = "plotly_dark"
    graph_bg_color = "#2a2d33"
    font_color = "#ffffff"

page_width = "100%" if plein_ecran else "80%"

# Application du style CSS
st.markdown(f"""
<style>
.stApp {{
    background-color: {page_bg};
    color: {font_color};
    max-width: {page_width};
    margin: auto;
}}

[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
}}

[data-testid="stSidebar"] * {{
    color: {sidebar_text_color} !important;
}}

[data-testid="stSidebar"] div[data-baseweb="select"] > div > div,
[data-testid="stSidebar"] div[data-testid="stFileUploader"] > div > div {{
    background-color: {sidebar_bg} !important;
    color: {sidebar_text_color} !important;
}}

h1,h2,h3,h4 {{
    color: {header_color};
}}
</style>
""", unsafe_allow_html=True)

#====================================================================
# -------------------------- Indicateurs ----------------------------
#====================================================================
st.title("📊 Indicateurs de suivi MGG")
total = len(df_filtered)
acheves = len(df_filtered[df_filtered["Statut_traitement"].isin(["Achevé","Grief non recevable"])])
en_cours = len(df_filtered[df_filtered["Statut_traitement"].isin(["En cours", "Perdu de vue"])])
a_traiter = len(df_filtered[df_filtered["Statut_traitement"]=="A traiter"])

cols = st.columns(4)
metrics = [(total,"Total"),(acheves,"Achevés"),(en_cours,"En cours"),(a_traiter,"A traiter")]

for col,(val,label),color in zip(cols,metrics,card_colors):
    col.markdown(f"""
        <div style='background:{color}; padding:15px; border-radius:15px; text-align:left;'>
            <p style='font-size:28px; font-weight:bold; color:black;'>{val}</p>
            <p style='font-weight:bold; color:black;'>{label}</p>
        </div>
    """, unsafe_allow_html=True)

#====================================================================
# --------------------- Carte de localisation -----------------------
#====================================================================
# --- Liens Dropbox ---
point_url = "https://www.dropbox.com/scl/fi/rgf74oa5eldfci8f5lems/Boite_aux_lettres.gpkg?rlkey=b6r4flk6158dy4mze9m8f81rp&st=dcgum783&dl=1"
polygon_url = "https://www.dropbox.com/scl/fi/cqu74x55xo8phugzct5af/lim_lefini_09072020.gpkg?rlkey=15vxwezrwbo11rtfuxh2z91un&st=c05wbp5m&dl=1"

# --- Dossier temporaire ---
os.makedirs("temp_gpkg", exist_ok=True)

# --- Téléchargement des fichiers ---
for url, path in [
    (point_url, "temp_gpkg/Boite_aux_lettres.gpkg"),
    (polygon_url, "temp_gpkg/lim_lefini_09072020.gpkg")
]:
    r = requests.get(url)
    if r.status_code == 200:
        with open(path, "wb") as f:
            f.write(r.content)
    else:
        st.error(f"Erreur téléchargement : {url}")

# --- Lecture GeoPackages ---
point_gdf = gpd.read_file("temp_gpkg/Boite_aux_lettres.gpkg")
polygon_gdf = gpd.read_file("temp_gpkg/lim_lefini_09072020.gpkg")

# --- Reprojection vers WGS84 ---
point_gdf = point_gdf.to_crs(epsg=4326)
polygon_gdf = polygon_gdf.to_crs(epsg=4326)
point_gdf["name"] = point_gdf["name"].str.strip().str.lower()

# --- Fonction couleur par statut ---
def couleur_statut(statut):
    if isinstance(statut, str):
        s = statut.lower()
        if "traité" in s or "clos" in s: return "green"
        elif "cours" in s or "en cours" in s: return "orange"
        elif "non" in s or "à traiter" in s: return "red"
    return "gray"

# --- Création de la carte ---
m = folium.Map(location=[-0.8, 17], zoom_start=6, tiles="CartoDB dark_matter")

# --- Polygone Domaine ---
folium.GeoJson(
    polygon_gdf,
    name="Domaine",
    style_function=lambda x: {"fillColor": "#ff7800","color": "#ffffff","weight": 2,"fillOpacity": 0.3},
    tooltip="Zone de projet"
).add_to(m)

# --- Merge pour avoir la géométrie pour chaque grief ---
df_geo = df_filtered_2.merge(
    point_gdf[["name", "geometry"]],
    left_on="Communaute",
    right_on="name",
    how="left"
).dropna(subset=["geometry"])

# --- Cluster des points ---
marker_cluster = MarkerCluster(name="📍 Griefs individuels").add_to(m)

# --- Ajouter tous les griefs individuellement ---
for idx, row in df_geo.iterrows():
    lat, lon = row.geometry.y, row.geometry.x
    statut = row.get("Statut_traitement", "N/A")
    couleur = couleur_statut(statut)
    plaignant = row.get("Plaignant_(si_anonyme_preciser)", "Anonyme")
    type_depot = row.get("Type_depot", "Inconnu")
    nature = row.get("Nature_plainte", "Inconnue")
    date_rec = row.get("Date_reception", "N/A")

    popup_html = f"""
    <b>Communauté :</b> {row['Communaute']}<br>
    <b>Type :</b> {type_depot}<br>
    <b>Nature :</b> {nature}<br>
    <b>Date réception :</b> {date_rec}<br>
    <b>Statut :</b> {statut}<br>
    <b>Plaignant :</b> {plaignant}
    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=6,
        color="white",
        fill=True,
        fill_color=couleur,
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(marker_cluster)

# --- Contrôle des couches (LayerControl compact) ---
folium.LayerControl(collapsed=False).add_to(m)
macro = MacroElement()
macro._template = Template("""
{% macro html(this, kwargs) %}
<style>
.leaflet-control-layers {
    font-size: 10px !important;
    line-height: 1.1 !important;
    max-height: 150px !important;
    overflow-y: auto !important;
}
</style>
{% endmacro %}
""")
m.get_root().add_child(macro)

# --- Affichage dans Streamlit ---
st.subheader("📍 Carte de local400)

#====================================================================
# --------------------- Graphiques principaux -----------------------
#====================================================================
st.subheader("📈 Analyse visuelle")

colors_map_statut = {
    "Achevé": "#00ff99",
    "Grief non recevable": "#ffcc00",
    "En cours": "#636efa",
    "A traiter": "#ff6666"
}
#-------------------------------------------------------------------------------------
# --- Répartition par type de dépôt ---
type_counts = df_filtered["Type_depot"].value_counts().sort_values()
fig_type = px.bar(
    x=type_counts.index, y=type_counts.values, text=type_counts.values,
    title="Répartition par type de dépôt", template=plotly_template, height=400
)
fig_type.update_traces(marker_line_width=0)
fig_type.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Type de dépôt", yaxis_title="Nombre de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

# --- Avancement général ---
fig_stat = px.pie(
    df_filtered, names="Statut_traitement", title="Avancement général du traitement",
    color="Statut_traitement", color_discrete_map=colors_map_statut,
    template=plotly_template, height=400
)
fig_stat.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
fig_stat.update_layout(
    title_font=dict(color=font_color, size=18),
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

if plein_ecran:
    st.plotly_chart(fig_type, use_container_width=True)
    st.plotly_chart(fig_stat, use_container_width=True)
else:
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig_type, use_container_width=True)
    c2.plotly_chart(fig_stat, use_container_width=True)
#-------------------------------------------------------------------------------------

# --- Répartition par Type de population et Genre ---
# --- Filtre d'affichage du genre ---
genre_mode = st.radio(
    "Affichage du genre (H/F):",
    ["Tout genre", "Catégoriser"],
    index=0,
    horizontal=True
)

# --- Préparation des données ---
df_pop_sexe = df_filtered.groupby(["Type", "Sexe"]).size().reset_index(name="Nombre")

# --- Cas 1 : fusionner tous les genres ---
if genre_mode == "Tout genre":
    df_plot = (
        df_pop_sexe.groupby("Type")["Nombre"]
        .sum()
        .reset_index()
    )
    color_arg = None  # pas de coloration par genre
    barmode = "relative"
else:
    df_plot = df_pop_sexe.copy()
    color_arg = "Sexe"
    barmode = "group"

# --- Tri croissant selon total des griefs ---
ordre_tri = (
    df_pop_sexe.groupby("Type")["Nombre"]
    .sum()
    .sort_values()
    .index.tolist()
)

# --- Création du graphique ---
fig_pop_sexe = px.bar(
    df_plot,
    x="Type",
    y="Nombre",
    color=color_arg,
    text="Nombre",
    title="Répartition par type de population",
    template=plotly_template,
    height=400,
    category_orders={"Type": ordre_tri},
    barmode=barmode
)

# Style du graphque
fig_pop_sexe.update_traces(marker_line_width=0)
fig_pop_sexe.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Type de population",
    yaxis_title="Nombre de griefs",
    plot_bgcolor=graph_bg_color,
    paper_bgcolor=graph_bg_color,
    font=dict(color=font_color),
    legend_title_text = "Genre"
)

st.plotly_chart(fig_pop_sexe, use_container_width=True)    # affichage dans streamlit
#-------------------------------------------------------------------------------------

# --- Histogramme par nature ---
st.subheader("🔵 Statut de traitement")
ordre_nature = df_filtered["Nature_plainte"].value_counts().sort_values().index.tolist()
fig_nature = px.histogram(
    df_filtered, y="Nature_plainte", color="Statut_traitement", text_auto=True,
    category_orders={"Nature_plainte": ordre_nature}, orientation="h",
    title="Nature de griefs par traitement", template=plotly_template,
    color_discrete_map=colors_map_statut, height=400
)
# Style du graphique
fig_nature.update_traces(marker_line_width=0)
fig_nature.update_layout(
    title_font=dict(color=font_color, size=18),
    xaxis_title="Nombre", yaxis_title="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color),
    legend_title_text="Statut de traitement"
)
st.plotly_chart(fig_nature, use_container_width=True)
#-------------------------------------------------------------------------------------

st.subheader("🏘️ Répartition par communauté et genre")

# --- 🔘 Bouton radio pour le mode d'affichage ---
choix_type = st.radio(
    "Afficher selon :",
    ["Tout type", "Catégoriser"],
    horizontal=True,
    key="choix_type_comm"
)

# --- Nettoyage complet de la colonne 'Communaute' ---
df_filtered["Communaute"] = (
    df_filtered["Communaute"]
    .astype(str)
    .str.strip()
    .str.lower()
)

# --- Vérification des colonnes requises ---
if "Communaute" in df_filtered.columns and "Type_depot" in df_filtered.columns:

    # --- Mode "Tout type" : deux colonnes côte à côte ---
    if choix_type == "Tout type":
        c1, c2 = st.columns(2)

        # Comptage correct des griefs par communauté
        comm_counts = (
            df_filtered.groupby("Communaute", dropna=False)
            .size()
            .reset_index(name="Nombre_de_griefs")
            .sort_values(by="Nombre_de_griefs", ascending=True)
        )

        fig_comm = px.bar(
            comm_counts,
            x="Communaute",
            y="Nombre_de_griefs",
            text="Nombre_de_griefs",
            title="Nombre total de griefs par communauté",
            template=plotly_template,
            height=400,
            color_discrete_sequence=["#00ccff"]
        )

        fig_comm.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig_comm.update_layout(
            title_font=dict(color=font_color, size=18),
            xaxis_title="Village / Localité",
            yaxis_title="Nombre de griefs",
            plot_bgcolor=graph_bg_color,
            paper_bgcolor=graph_bg_color,
            font=dict(color=font_color),
            showlegend=False,
        )

        c1.plotly_chart(fig_comm, use_container_width=True)

        # --- Graphique pie ---
        if "Sexe" in df_filtered.columns:
            df_sexe = df_filtered[df_filtered["Sexe"].notna()]
            if not df_sexe.empty:
                fig_sexe = px.pie(
                    df_sexe,
                    names="Sexe",
                    title="Répartition en genre",
                    template=plotly_template,
                    height=400
                )
                fig_sexe.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
                fig_sexe.update_layout(
                    title_font=dict(color=font_color, size=18),
                    plot_bgcolor=graph_bg_color,
                    paper_bgcolor=graph_bg_color,
                    font=dict(color=font_color)
                )
                c2.plotly_chart(fig_sexe, use_container_width=True)

    # --- Mode "Catégoriser" : barre pleine largeur, pie en dessous ---
    else:
        comm_type_counts = (
            df_filtered.groupby(["Communaute", "Type_depot"], dropna=False)
            .size()
            .reset_index(name="Nombre_de_griefs")
        )

        ordre_tri = (
            comm_type_counts.groupby("Communaute")["Nombre_de_griefs"]
            .sum()
            .sort_values(ascending=True)
            .index.tolist()
        )

        fig_comm = px.bar(
            comm_type_counts,
            x="Communaute",
            y="Nombre_de_griefs",
            color="Type_depot",
            text="Nombre_de_griefs",
            title="Griefs par communauté et type de dépôt",
            template=plotly_template,
            height=600,
            category_orders={"Communaute": ordre_tri},
            barmode="group"
        )

        fig_comm.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
        fig_comm.update_layout(
            title_font=dict(color=font_color, size=18),
            xaxis_title="Village / Localité",
            yaxis_title="Nombre de griefs",
            plot_bgcolor=graph_bg_color,
            paper_bgcolor=graph_bg_color,
            font=dict(color=font_color),
            showlegend=True,
            legend_title_text="Type de dépôt"
        )

        st.plotly_chart(fig_comm, use_container_width=True)

        # --- Graphique pie en dessous ---
        if "Sexe" in df_filtered.columns:
            df_sexe = df_filtered[df_filtered["Sexe"].notna()]
            if not df_sexe.empty:
                fig_sexe = px.pie(
                    df_sexe,
                    names="Sexe",
                    title="Répartition en genre",
                    template=plotly_template,
                    height=350
                )
                fig_sexe.update_traces(textinfo="percent+label", textposition="inside", marker_line_width=0)
                fig_sexe.update_layout(
                    title_font=dict(color=font_color, size=18),
                    plot_bgcolor=graph_bg_color,
                    paper_bgcolor=graph_bg_color,
                    font=dict(color=font_color)
                )
                st.plotly_chart(fig_sexe, use_container_width=True)

else:
    st.warning("⚠️ Les colonnes 'Communaute' et 'Type_depot' doivent exister dans le jeu de données.")
#-------------------------------------------------------------------------------------

# --- Nature par Genre ---
st.subheader("👥 Nature des griefs par genre")
df_cat_sexe = df_filtered.groupby(["Nature_plainte","Sexe"]).size().reset_index(name="Nombre")
ordre_nature_tri = df_cat_sexe.groupby("Nature_plainte")["Nombre"].sum().sort_values().index.tolist()
fig_cat_sexe = px.bar(
    df_cat_sexe, y="Nature_plainte", x="Nombre", color="Sexe",
    category_orders={"Nature_plainte": ordre_nature_tri}, orientation="h",
    template=plotly_template, text="Nombre", height=400
)

# Style du graphique
fig_cat_sexe.update_traces(marker_line_width=0)
fig_cat_sexe.update_layout(
    title="Nature des griefs par sexe",
    title_font=dict(color=font_color, size=18),
    xaxis_title="Nombre", yaxis_title="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color),
    legend_title_text = "Genre"
)
st.plotly_chart(fig_cat_sexe, use_container_width=True)    # affichage dans srtreamlit
#-------------------------------------------------------------------------------------

# --- Évolution temporelle ---
st.subheader("📈 Évolution temporelle des griefs")
top_n = st.slider("Top N natures :", 3, 10, 5)
trimestres = sorted(df_filtered["Trimestre"].unique())
trimestre_sel = st.selectbox("Filtrer par trimestre :", ["Tous"] + trimestres)
df_trim = df_filtered if trimestre_sel == "Tous" else df_filtered[df_filtered["Trimestre"] == trimestre_sel]
top_natures = df_trim["Nature_plainte"].value_counts().nlargest(top_n).index
df_line = df_trim[df_trim["Nature_plainte"].isin(top_natures)].groupby(["Mois","Nature_plainte"]).size().reset_index(name="Nombre")
fig_line = px.line(df_line, x="Mois", y="Nombre", color="Nature_plainte", markers=True,
    title=f"Top {top_n} évolution", template=plotly_template, height=400)
fig_line.update_layout(
    title_font=dict(color=font_color, size=18),
    legend_title_text="Nature de griefs",
    plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
    font=dict(color=font_color)
)

# Style du graphique
fig_line.update_xaxes(dtick="M1", tickformat="%b", tickangle=-45)
st.plotly_chart(fig_line, use_container_width=True)    # affichage dans srtreamlit
#-------------------------------------------------------------------------------------

# --- Classement par nature ---
if "Classement" in df_filtered.columns:
    st.subheader("🏁 Griefs classés par nature")

    # Filtrer uniquement les griefs classés
    df_classe = df_filtered[df_filtered["Classement"].astype(str).str.lower() == "oui"]

    if not df_classe.empty:
        # Compter les griefs par nature
        nature_counts = df_classe["Nature_plainte"].value_counts().sort_values()

        fig_classement = px.bar(
            x=nature_counts.index,
            y=nature_counts.values,
            text=nature_counts.values,
            title="Répartition des griefs classés par nature",
            template=plotly_template,
            height=400,
            color_discrete_sequence=["#00ccff"]
        )

        # Style du graphique
        fig_classement.update_traces(marker_line_width=0)
        fig_classement.update_layout(
            title_font=dict(color=font_color, size=18),
            xaxis_title="Nature de grief",
            yaxis_title="Nombre de griefs classés",
            plot_bgcolor=graph_bg_color,
            paper_bgcolor=graph_bg_color,
            font=dict(color=font_color)
        )

        st.plotly_chart(fig_classement, use_container_width=True)

    else:
        st.info("ℹ️ Aucun grief classé ('Classement = Oui') trouvé dans les données.")
#-------------------------------------------------------------------------------------

# --- Durée moyenne ---
st.subheader("⌛ Durée de traitement")
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index().sort_values("Nb_jour")
    fig_duree = px.bar(df_duree, x="Nature_plainte", y="Nb_jour", text_auto=".1f",
        title="Durée moyenne de traitement par nature", template=plotly_template, height=400)
    fig_duree.update_traces(marker_line_width=0)
    
    # Style du graphique
    fig_duree.update_layout(
        title_font=dict(color=font_color, size=18),
        xaxis_title="Nature de griefs", yaxis_title="Durée (jours)",
        plot_bgcolor=graph_bg_color, paper_bgcolor=graph_bg_color,
        font=dict(color=font_color)
    )
    st.plotly_chart(fig_duree, use_container_width=True)    # affichage dans srtreamlit

#====================================================================
# ------------------------ Tableau final ---------------------------
#====================================================================
st.subheader("📋 Aperçu des données")
st.dataframe(df_filtered, use_container_width=True)
