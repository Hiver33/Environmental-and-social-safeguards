## *************** ceci est le script du code Python pour le projet ***************
##                                Projet PyDashboard 

## import des bibliotèques 
import streamlit as st
import pandas as pd
import plotly.express as px
import pyodbc

#==============================================================
# connexion  et chargement des données sources
#==============================================================
@st.cache_data (ttl = 300)   # met en cache toutes les 300 secondes, soit 5 minutes
def load_data(path) : 
    try : 
        conn = pyodbc.conneect(
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f'DBQ = {path};'
        )
        df = pd.read_sql('SELECT * FROM Table_MGG', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f'❌ Impossible de charger la base Access :{e}')
        return pd.DataFrame()   # retourne vide si erreur

## --------------- Chemin d'accès à la BD Access ---------------
chemin_base = r"C:\Users\hiver.segna\Desktop\Data Science\Dashbords\Environmental-and-social-safeguards\Data\BD_Gestion_Sociale_et_Environnementale_Backup.accdb"
df = load_data(chemin_base)

## si aucune données, on stoppe
if df.empty : 
    st.stop()
    
#==============================================================
# Dashbord
#==============================================================
st.title('📊 Dashbord Suivi des Plaintes')

## vérifierq ue les colonnes attendues existent
colonnes_attendues = ['Type_depot', 'Statut_traitement', 'Nature_plainte', 'Categorie']
for col in colonnes_attendues :
    if col not in df.columns :
        st.error (f'⚠️ La colonne "{col}" est manquante dans la table.')
        st.stop()

st.write("Aperçu des données :", df.head())

## --------------- Initialiser les filtres ---------------
Types = st.multiselect(
    'Filtrer par type de dépot :',
    df['Type_depot'].dropna().unique(),
    default = df['Type_depot'].dropna().unique()
)
Statuts = st.multiselect(
    'Filtrer par statut :',
    df['Statut_traitement'].dropna().unique(),
    default = df['Statut_traitement'].dropna().unique()
)

df_filtered = df[df['Type_depot'].idin(Types) & df['Statut_traitement'].isin(Statuts)]   # créer une copie de la data filtrée

## --------------- Dresser un tableau ---------------
st.subhader('📑 Tableau des griefs')
st.dataframe(df_filtered)

## --------------- Afficher les indicateurs ---------------
st.subheader('📌 Indicateurs clés')
col1, col2, col3, col4 = st.columns(4)
col1.metric('Total des griefs', len(df_filtered))
col2.metric = ('En cours', len(df_filtered[df_filtered['Statut_traitement'] == 'En cours']))
col3.metric = ('Achevé', len(df_filtered[df_filtered['Statut_traitement'] == 'Achevé'| df_filtered[df_filtered['Statut_traitement'] == 'Grief non récevable']]))
col4.metric = ('Non traité', len(df_filtered[df_filtered['Statut_traitement'] == 'Non traité']))

## --------------- Dresser les graphiques ---------------
st.subheader('📈 Analyse visuelles')

## répartition par Type de dépôt
fig1 = px.bar(df_filtered , x = 'Type_depot', tite = 'Répartitionpar type de dépôt')
st.plotly_chart(fig1, use_container_width = True)

## répartition par statut
fig2 = px.pie(df_filtered, names = 'Statut_traitement', title = 'Avancement général des griefs')
st.plotly_chart(fig2, use_container_width = True)

## répartition par nature
fig3 = px.histogram(df_filtered, x = 'Nature_plainte', color = 'Statut_traitement', title = 'Distribution par nature')
st.plotly_chart(fig3, use_container_width = True)
