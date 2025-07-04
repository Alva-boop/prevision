#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapté pour SAP Météo Cameroun - 10 jours cumul, jours pluvieux consécutifs, cumul journalier
@author: alvine
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

st.set_page_config(layout="wide", page_title="SAP Météo Cameroun", page_icon="⛈️")

# Données fictives exemple (à remplacer par tes données réelles)
regions_data = {
    "Région": ["Extrême-Nord", "Nord", "Adamaoua", "Est", "Centre", 
               "Sud", "Littoral", "Ouest", "Nord-Ouest", "Sud-Ouest"],
    "Latitude": [10.5, 8.5, 7.0, 4.5, 4.75, 3.0, 4.25, 5.5, 6.5, 5.0],
    "Longitude": [14.5, 13.5, 13.5, 14.0, 12.0, 12.0, 9.5, 10.5, 10.0, 9.2],
    "Cumul_10j": [150, 120, 90, 60, 40, 80, 200, 100, 130, 50],  # mm cumuls 10 jours
    "Jours_Consec": [3, 2, 4, 1, 0, 5, 3, 2, 6, 1],  # nombre de jours pluvieux consécutifs
    "Intensite_Jours_Consec": [30, 25, 20, 10, 0, 40, 60, 35, 70, 10],  # mm/jour en moyenne pendant ces jours
    "Cumul_Journalier": [20, 45, 60, 10, 5, 80, 50, 15, 90, 30],  # mm cumuls journalier
    "Impacts": [
        "Inondations modérées, vigilance recommandée",
        "Risques localisés, suivi accru conseillé",
        "Risque d'érosion et petites inondations",
        "Pluies faibles, pas de risque immédiat",
        "Conditions sèches",
        "Risque d'inondations urbaines",
        "Inondations majeures, dégâts possibles",
        "Risques modérés, routes glissantes",
        "Crues rapides, vigilance orange",
        "Pluies faibles, situation stable"
    ]
}

df = pd.DataFrame(regions_data)

# Seuils et niveaux d'alerte adaptés au nouveau contexte
SEUILS = {
    "Cumul_10j": {
        "Vert": (0, 50, "Pluie faible sur 10 jours", "Veille"),
        "Jaune": (51, 100, "Pluie modérée sur 10 jours", "Vigilance"),
        "Orange": (101, 200, "Pluie forte sur 10 jours", "Alerte"),
        "Rouge": (200, 1000, "Précipitations très fortes sur 10 jours", "Danger")
    },
    "Jours_Consec": {
        "Vert": (0, 1, "Peu de jours pluvieux consécutifs", "Veille"),
        "Jaune": (2, 3, "Jours pluvieux consécutifs modérés", "Vigilance"),
        "Orange": (4, 5, "Plusieurs jours pluvieux consécutifs", "Alerte"),
        "Rouge": (6, 100, "Longue période pluvieuse consécutive", "Danger")
    },
    "Intensite_Jours_Consec": {
        "Vert": (0, 19, "Intensité faible de pluie", "Veille"),
        "Jaune": (20, 39, "Intensité modérée de pluie", "Vigilance"),
        "Orange": (40, 59, "Intensité forte de pluie", "Alerte"),
        "Rouge": (60, 1000, "Intensité très forte de pluie", "Danger")
    },
    "Cumul_Journalier": {
        "Vert": (0, 15, "Pluie faible journalière", "Veille"),
        "Jaune": (16, 25, "Pluie modérée journalière", "Vigilance"),
        "Orange": (26, 75, "Pluie forte journalière", "Alerte"),
        "Rouge": (75, 400, "Précipitations journalières extrêmes", "Danger")
    }
}

# Fonction pour déterminer le niveau d'alerte selon seuils
def get_alert_level(value, param):
    for level, (min_val, max_val, _, _) in SEUILS[param].items():
        if min_val <= value <= max_val:
            return level
    return "Vert"

# Interface Streamlit
st.title("🌧️ Système d'Alerte Précoce Météorologique - Cameroun")
st.markdown("Surveillance basée sur cumul 10 jours, jours pluvieux consécutifs et cumul journalier")

with st.sidebar:
    st.header("⚙️ Paramètres par région")
    selected_region = st.selectbox("Sélectionner une région", df["Région"].unique())
    region_idx = df[df["Région"] == selected_region].index[0]

    # Correction ici : types cohérents value et step
    new_cumul_10j = st.number_input(
        "Cumul précipitations sur 10 jours (mm)",
        value=int(df.at[region_idx, "Cumul_10j"]),
        step=1
    )
    new_jours_consec = st.number_input(
        "Jours pluvieux consécutifs",
        value=int(df.at[region_idx, "Jours_Consec"]),
        min_value=0,
        step=1
    )
    new_intensite_consec = st.number_input(
        "Intensité moyenne sur jours pluvieux consécutifs (mm/jour)",
        value=float(df.at[region_idx, "Intensite_Jours_Consec"]),
        step=0.1
    )
    new_cumul_journalier = st.number_input(
        "Cumul journalier de précipitations (mm)",
        value=float(df.at[region_idx, "Cumul_Journalier"]),
        step=0.1
    )

    if st.button("Mettre à jour"):
        df.at[region_idx, "Cumul_10j"] = new_cumul_10j
        df.at[region_idx, "Jours_Consec"] = new_jours_consec
        df.at[region_idx, "Intensite_Jours_Consec"] = new_intensite_consec
        df.at[region_idx, "Cumul_Journalier"] = new_cumul_journalier
        st.success("Valeurs mises à jour")

    st.markdown("---")
    st.markdown("**Légende des niveaux d'alerte**")
    st.markdown("- 🟢 Vert : Veille (conditions stables)\n- 🟡 Jaune : Vigilance (suivi renforcé)\n- 🟠 Orange : Alerte (risques accrus)\n- 🔴 Rouge : Danger (risques majeurs)")

# Calcul des alertes pour chaque paramètre
df['Alerte_Cumul_10j'] = df['Cumul_10j'].apply(lambda x: get_alert_level(x, "Cumul_10j"))
df['Alerte_Jours_Consec'] = df['Jours_Consec'].apply(lambda x: get_alert_level(x, "Jours_Consec"))
df['Alerte_Intensite_Consec'] = df['Intensite_Jours_Consec'].apply(lambda x: get_alert_level(x, "Intensite_Jours_Consec"))
df['Alerte_Cumul_Journalier'] = df['Cumul_Journalier'].apply(lambda x: get_alert_level(x, "Cumul_Journalier"))

# Affichage par région sélectionnée
tab1, tab2, tab3 = st.tabs(["📊 Tableau de Bord", "🗺️ Carte", "📋 Rapport"])

with tab1:
    st.header(f"Tableau de Bord - Région : {selected_region}")
    region_data = df[df["Région"] == selected_region].iloc[0]

    cols = st.columns(4)
    with cols[0]:
        alerte = region_data["Alerte_Cumul_10j"]
        st.metric("Cumul précipitations 10 jours (mm)", region_data["Cumul_10j"], help=SEUILS["Cumul_10j"][alerte][2])
        st.write(f"Niveau: {alerte} ({SEUILS['Cumul_10j'][alerte][3]})")
    with cols[1]:
        alerte = region_data["Alerte_Jours_Consec"]
        st.metric("Jours pluvieux consécutifs", region_data["Jours_Consec"], help=SEUILS["Jours_Consec"][alerte][2])
        st.write(f"Niveau: {alerte} ({SEUILS['Jours_Consec'][alerte][3]})")
    with cols[2]:
        alerte = region_data["Alerte_Intensite_Consec"]
        st.metric("Intensité moyenne jours consécutifs (mm/j)", region_data["Intensite_Jours_Consec"], help=SEUILS["Intensite_Jours_Consec"][alerte][2])
        st.write(f"Niveau: {alerte} ({SEUILS['Intensite_Jours_Consec'][alerte][3]})")
    with cols[3]:
        alerte = region_data["Alerte_Cumul_Journalier"]
        st.metric("Cumul journalier précipitations (mm)", region_data["Cumul_Journalier"], help=SEUILS["Cumul_Journalier"][alerte][2])
        st.write(f"Niveau: {alerte} ({SEUILS['Cumul_Journalier'][alerte][3]})")

    st.markdown("---")
    st.subheader("📌 Impacts recensés")
    st.write(region_data["Impacts"])

with tab2:
    st.header("Carte des niveaux d'alerte (Cumul 10 jours)")
    param_carte = st.radio("Paramètre à visualiser:", ["Cumul_10j", "Jours_Consec", "Intensite_Consec", "Cumul_Journalier"], horizontal=True)

    color_map = {
        "Vert": [0, 200, 0, 160],
        "Jaune": [255, 255, 0, 160],
        "Orange": [255, 165, 0, 160],
        "Rouge": [255, 0, 0, 160]
    }

    # Définir la colonne couleur selon paramètre sélectionné
    col_alert = "Alerte_" + param_carte
    df["color"] = df[col_alert].map(lambda x: color_map[x])

    view_state = pdk.ViewState(latitude=df["Latitude"].mean(), longitude=df["Longitude"].mean(), zoom=5.5)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["Longitude", "Latitude"],
        get_color="color",
        get_radius=20000,
        pickable=True
    )
    tooltip = {
        "html": "<b>Région:</b> {Région}<br><b>Valeur:</b> {" + param_carte + "}<br><b>Niveau:</b> {" + col_alert + "}<br><b>Impact:</b> {Impacts}",
        "style": {"backgroundColor": "black", "color": "white"}
    }
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

with tab3:
    st.header("Rapport Général des Alertes")

    alertes = []
    for param in ["Alerte_Cumul_10j", "Alerte_Jours_Consec", "Alerte_Intensite_Consec", "Alerte_Cumul_Journalier"]:
        data = df[df[param].isin(["Orange", "Rouge"])]
        if not data.empty:
            alertes.append((param.replace("Alerte_", "").replace("_", " "), data))

    if not alertes:
        st.success("✅ Aucun danger signalé actuellement.")
    else:
        for titre, data in alertes:
            st.warning(f"⚠️ Alertes pour {titre}")
            for _, row in data.iterrows():
                with st.expander(f"{row['Région']} - Niveau {row['Alerte_' + titre.replace(' ', '_')]}"):
                    st.write(f"- Cumul 10j : {row['Cumul_10j']} mm")
                    st.write(f"- Jours pluvieux consécutifs : {row['Jours_Consec']}")
                    st.write(f"- Intensité jours consécutifs : {row['Intensite_Jours_Consec']} mm/j")
                    st.write(f"- Cumul journalier : {row['Cumul_Journalier']} mm")
                    st.write(f"- Impact: {row['Impacts']}")

st.markdown("---")
st.markdown("""
<div style='text-align: center;'>
    <em>Système d'Alerte Précoce Climat-Risques - Ministère des Transports et de la Santé</em><br>
    <small>Démo développée avec Streamlit | Données fictives</small>
</div>
""", unsafe_allow_html=True)


