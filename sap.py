#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapté le 24 Mai 2025 pour inclure le vent et l'impact des précipitations
@author: alvine
"""

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime

st.set_page_config(layout="wide", page_title="SAP Météo Cameroun", page_icon="⛈️")

# Données des régions avec vent
regions_data = {
    "Région": ["Extrême-Nord", "Nord", "Adamaoua", "Est", "Centre", 
               "Sud", "Littoral", "Ouest", "Nord-Ouest", "Sud-Ouest"],
    "Latitude": [10.5, 8.5, 7.0, 4.5, 4.75, 
                 3.0, 4.25, 5.5, 6.5, 5.0],
    "Longitude": [14.5, 13.5, 13.5, 14.0, 12.0, 
                  12.0, 9.5, 10.5, 10.0, 9.2],
    "Température": [38, 36, 32, 30, 31, 
                    29, 32, 28, 26, 30],
    "Vent": [10, 15, 20, 12, 8, 
             5, 22, 14, 11, 18],
    "Précipitations": [20, 35, 60, 120, 85, 
                       150, 180, 75, 90, 200],
    "Impacts": [
        "Déshydratation, accès limité à l'eau",
        "Coup de chaleur, routes poussiéreuses",
        "Inconfort thermique, dégradation de routes",
        "Inondations locales, perturbation du trafic",
        "Crues rapides, bouchons dans les villes",
        "Risque élevé d'inondations urbaines",
        "Inondations majeures, dégâts aux bâtiments",
        "Routes glissantes, risques d’éboulements",
        "Éboulements, inaccessibilité des villages",
        "Inondations et routes impraticables"
    ]
}

df = pd.DataFrame(regions_data)

SEUILS = {
    "Température": {
        "Vert": (15, 24.9, "Conditions normales", "Aucun risque particulier"),
        "Jaune": (25, 29.9, "Inconfort thermique", "Hydratation recommandée, prudence"),
        "Orange": (30, 34.9, "Chaleur intense", "Risque de coup de chaleur"),
        "Rouge": (35, 45, "Danger extrême", "Activités à l'extérieur à éviter")
    },
    "Vent": {
        "Vert": (5, 19, "Vent faible à modéré", "Aucun impact significatif"),
        "Jaune": (20, 40, "Vent fort", "Risque pour les structures légères"),
        "Orange": (41, 60, "Rafales dangereuses", "Endommagement d’infrastructures possibles"),
        "Rouge": (61, 120, "Vent violent", "Chutes d’arbres, coupures électriques","Destruction des batiments")
    },
    "Précipitations": {
        "Vert": (0, 49, "Pluies normales", "Pas d'impact significatif"),
        "Jaune": (50, 75, "Pluies modérées", "Risque d’inondations locales, ralentissements du trafic"),
        "Orange": (76, 100, "Pluies fortes", "Inondations, dommages à la voirie et logements"),
        "Rouge": (101, 1000, "Précipitations extrêmes", "Crues, routes impraticables, déplacement impossible")
    }
}

def get_alert_level(value, param):
    for level, (min_val, max_val, *_) in SEUILS[param].items():
        if min_val <= value <= max_val:
            return level
    return "Vert"

st.title("🌧️ Système d'Alerte Précoce Météorologique")
st.markdown("Surveillance des conditions météorologiques au Cameroun")

with st.sidebar:
    st.header("⚙️ Paramètres")
    selected_region = st.selectbox("Sélectionner une région", df["Région"].unique())
    region_idx = df[df["Région"] == selected_region].index[0]
    
    new_temp = st.number_input("Température (°C)", value=float(df.at[region_idx, "Température"]))
    new_wind = st.number_input("Vent (km/h)", value=float(df.at[region_idx, "Vent"]))
    new_precip = st.number_input("Précipitations (mm/jour)", value=float(df.at[region_idx, "Précipitations"]))
    
    if st.button("Mettre à jour"):
        df.at[region_idx, "Température"] = new_temp
        df.at[region_idx, "Vent"] = new_wind
        df.at[region_idx, "Précipitations"] = new_precip
        st.success("Valeurs mises à jour")

    st.markdown("---")
    st.markdown("**Légende**")
    st.markdown("- 🟢 Vert : Normal\n- 🟡 Jaune : Attention\n- 🟠 Orange : Alerte\n- 🔴 Rouge : Danger")

df['Alerte_Temp'] = df['Température'].apply(lambda x: get_alert_level(x, "Température"))
df['Alerte_Vent'] = df['Vent'].apply(lambda x: get_alert_level(x, "Vent"))
df['Alerte_Precip'] = df['Précipitations'].apply(lambda x: get_alert_level(x, "Précipitations"))

tab1, tab2, tab3 = st.tabs(["📊 Tableau de Bord", "🗺️ Carte", "📋 Rapport"])

with tab1:
    st.header("Tableau de Bord - Région sélectionnée")
    region_data = df[df["Région"] == selected_region].iloc[0]
    
    cols = st.columns(3)
    with cols[0]:
        alert = region_data["Alerte_Temp"]
        st.metric("Température (°C)", region_data["Température"], help=SEUILS["Température"][alert][2])
        st.write(SEUILS["Température"][alert][3])
    
    with cols[1]:
        alert = region_data["Alerte_Vent"]
        st.metric("Vent (km/h)", region_data["Vent"], help=SEUILS["Vent"][alert][2])
        st.write(SEUILS["Vent"][alert][3])
    
    with cols[2]:
        alert = region_data["Alerte_Precip"]
        st.metric("Précipitations (mm)", region_data["Précipitations"], help=SEUILS["Précipitations"][alert][2])
        st.write(SEUILS["Précipitations"][alert][3])
    
    st.markdown("---")
    st.subheader("📌 Impacts recensés")
    st.write(region_data["Impacts"])

with tab2:
    st.header("Carte des niveaux d'alerte")
    param_carte = st.radio("Paramètre à visualiser:", ["Température", "Vent", "Précipitations"], horizontal=True)
    
    color_map = {
        "Vert": [0, 200, 0, 160],
        "Jaune": [255, 255, 0, 160],
        "Orange": [255, 165, 0, 160],
        "Rouge": [255, 0, 0, 160]
    }
    
    if param_carte == "Température":
        df["color"] = df["Alerte_Temp"].apply(lambda x: color_map[x])
        value_col = "Température"
        alert_col = "Alerte_Temp"
    elif param_carte == "Vent":
        df["color"] = df["Alerte_Vent"].apply(lambda x: color_map[x])
        value_col = "Vent"
        alert_col = "Alerte_Vent"
    else:
        df["color"] = df["Alerte_Precip"].apply(lambda x: color_map[x])
        value_col = "Précipitations"
        alert_col = "Alerte_Precip"
    
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
        "html": f"<b>Région:</b> {{Région}}<br><b>{param_carte}:</b> {{{value_col}}}<br><b>Niveau:</b> {{{alert_col}}}<br><b>Impact:</b> {{Impacts}}",
        "style": {"backgroundColor": "black", "color": "white"}
    }
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))

with tab3:
    st.header("Rapport Général des Alertes")
    alertes = []

    if not df[df["Alerte_Temp"].isin(["Orange", "Rouge"])].empty:
        alertes.append(("🌡️ Température élevée", df[df["Alerte_Temp"].isin(["Orange", "Rouge"])]))
    if not df[df["Alerte_Vent"].isin(["Orange", "Rouge"])].empty:
        alertes.append(("🌬️ Vent dangereux", df[df["Alerte_Vent"].isin(["Orange", "Rouge"])]))
    if not df[df["Alerte_Precip"].isin(["Orange", "Rouge"])].empty:
        alertes.append(("🌧️ Précipitations extrêmes", df[df["Alerte_Precip"].isin(["Orange", "Rouge"])]))
    
    if not alertes:
        st.success("✅ Aucun danger signalé actuellement.")
    else:
        for titre, data in alertes:
            st.warning(titre)
            for _, row in data.iterrows():
                with st.expander(f"{row['Région']} - Niveau {row[alert_col]}"):
                    st.write(f"- Précipitations: {row['Précipitations']} mm")
                    st.write(f"- Vent: {row['Vent']} km/h")
                    st.write(f"- Température: {row['Température']} °C")
                    st.write(f"- Impact: {row['Impacts']}")

    st.markdown("---")
    st.subheader("🔧 Recommandations Générales")

    st.markdown("### 🌧️ En cas de précipitations extrêmes")
    st.markdown("""
    - Évitez de traverser des routes inondées, même si elles paraissent praticables.
    - Surélevez les équipements sensibles dans les maisons susceptibles d’être inondées.
    - Coupez l’alimentation électrique dans les zones inondées pour éviter les électrocutions.
    - Suivez les bulletins météo locaux et les alertes officielles en continu.
    """)
    
    st.markdown("### 🌬️ En cas de vent violent")
    st.markdown("""
    - Évitez de vous abriter sous les arbres ou près de structures métalliques pendant les rafales.
    - Rentrez les objets extérieurs pouvant être emportés (panneaux, poubelles, outils).
    - Renforcez les structures légères ou temporaires comme les abris de fortune.
    - Limitez vos déplacements en voiture, surtout dans les zones boisées ou montagneuses.
    """)
    
    st.markdown("### 🌡️ En cas de températures élevées")
    st.markdown("""
    - Buvez de l’eau régulièrement, même sans sensation de soif.
    - Évitez les activités physiques intenses entre 11h et 16h.
    - Portez des vêtements légers, de couleur claire et protégez-vous du soleil.
    - Vérifiez régulièrement l’état de santé des enfants, personnes âgées ou malades.
    """)


st.markdown("---")
st.markdown("""
<div style='text-align: center;'>
    <em>Système d'Alerte Précoce Climat-Risques - Ministère des Transports et de la Santé</em><br>
    <small>Démo développée avec Streamlit | Données fictives</small>
</div>
""", unsafe_allow_html=True)
