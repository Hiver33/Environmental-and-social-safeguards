import streamlit as st
import pandas as pd
import plotly.express as px

#==============================================================
# connexion  et chargement des données sources
#==============================================================

# @st.cache_data (ttl = 300)   # met en cache toutes les 300 secondes, soit 5 minutes
def load_data(path) : 
    try : 
        df = pd.read_excel(path)
        return df
    except Exception as e:
        st.error(f"❌ Impossible de charger le fichier Excel :{e}")
        return pd.DataFrame()   # retourne vide si erreur

## --------------- Chemin d'accès au fichier Excel ---------------
chemin_excel = r"C:\Users\hiver.segna\Desktop\Data Science\Dashbords\Environmental-and-social-safeguards\Data\Table_MGG.xlsx"

## colonnes à charger depuis Excel
colonnes_attendues = ["Type_depot", "Statut_traitement", "Nature_plainte", "Categorie"]
df = load_data(chemin_excel)

## si aucune données, on stoppe
if df.empty : 
    st.stop()
df.head()