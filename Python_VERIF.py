# ============================================================== 
# Graphique ligne : évolution temporelle (après filtrage année et trimestre)
# ============================================================== 
df_filtered['Mois'] = df_filtered['Date_reception'].dt.to_period('M').dt.to_timestamp()
df_filtered['Trimestre'] = df_filtered['Date_reception'].dt.to_period('Q').astype(str)

# Filtre trimestre
trimestre_disponibles = sorted(df_filtered['Trimestre'].unique())
trimestre_disponibles.insert(0, "Tous")
trimestre_choisie = st.selectbox("Choisir un trimestre :", trimestre_disponibles)

if trimestre_choisie != "Tous":
    df_trim = df_filtered[df_filtered['Trimestre'] == trimestre_choisie]
else:
    df_trim = df_filtered.copy()

# Préparer données graphique ligne
df_grief = df_trim.groupby(['Mois', 'Nature_plainte']).size().reset_index(name='Nombre_Griefs')

# Graphique ligne
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
# Graphique durée moyenne de traitement (sous graphique ligne)
# ============================================================== 
if "Nb_jour" in df_trim.columns:
    df_duree = df_trim.groupby("Nature_plainte")["Nb_jour"].mean().round().reset_index()
    df_duree = df_duree.sort_values(by="Nb_jour")  # tri croissant
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
