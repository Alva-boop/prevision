#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  6 18:58:06 2025

@author: alvine

SAP Météo Cameroun - Carte + PDF + Alertes (sans geopandas)
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from fpdf import FPDF
import io
import re

st.set_page_config(layout="wide", page_title="SAP Météo Cameroun", page_icon="⛈️")

# === Données de base ===
regions_data = {
    "Région": ["Extrême-Nord", "Nord", "Adamaoua", "Est", "Centre",
               "Sud", "Littoral", "Ouest", "Nord-Ouest", "Sud-Ouest"],
    "Latitude": [10.5, 8.5, 7.0, 4.5, 4.75, 3.0, 4.25, 5.5, 6.5, 5.0],
    "Longitude": [14.5, 13.5, 13.5, 14.0, 12.0, 12.0, 9.5, 10.5, 10.0, 9.2],
    "Cumul_10j": [150, 120, 90, 60, 40, 80, 200, 100, 130, 50],
    "Jours_Consec": [3, 2, 4, 1, 0, 5, 3, 2, 6, 1],
    "Intensite_Jours_Consec": [30, 25, 20, 10, 0, 40, 60, 35, 70, 10],
    "Cumul_Journalier": [20, 45, 60, 10, 5, 80, 50, 15, 90, 30],
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

SEUILS = {
    "Cumul_10j": {"Vert": (0, 50), "Jaune": (51, 100), "Orange": (101, 200), "Rouge": (201, 1000)},
    "Jours_Consec": {"Vert": (0, 1), "Jaune": (2, 3), "Orange": (4, 5), "Rouge": (6, 100)},
    "Intensite_Jours_Consec": {"Vert": (0, 19), "Jaune": (20, 39), "Orange": (40, 59), "Rouge": (60, 1000)},
    "Cumul_Journalier": {"Vert": (0, 15), "Jaune": (16, 25), "Orange": (26, 75), "Rouge": (76, 400)}
}

def get_alert_level(value, param):
    for level, (min_val, max_val) in SEUILS[param].items():
        if min_val <= value <= max_val:
            return level
    return "Vert"

with st.sidebar:
    st.header("⚙️ Modifier une région")
    selected_region = st.selectbox("Sélectionner une région", df["Région"].unique())
    region_idx = df[df["Région"] == selected_region].index[0]

    df.at[region_idx, "Cumul_10j"] = st.number_input("Cumul 10 jours (mm)", value=int(df.at[region_idx, "Cumul_10j"]))
    df.at[region_idx, "Jours_Consec"] = st.number_input("Jours consécutifs", value=int(df.at[region_idx, "Jours_Consec"]))
    df.at[region_idx, "Intensite_Jours_Consec"] = st.number_input("Intensité consécutifs (mm/j)", value=float(df.at[region_idx, "Intensite_Jours_Consec"]))
    df.at[region_idx, "Cumul_Journalier"] = st.number_input("Cumul journalier (mm)", value=float(df.at[region_idx, "Cumul_Journalier"]))

for param in SEUILS.keys():
    df[f"Alerte_{param}"] = df[param].apply(lambda x: get_alert_level(x, param))

PARAMS = {
    "Cumul_10j": "Alerte_Cumul_10j",
    "Jours_Consec": "Alerte_Jours_Consec",
    "Intensite_Jours_Consec": "Alerte_Intensite_Jours_Consec",
    "Cumul_Journalier": "Alerte_Cumul_Journalier"
}

# === Tabs

tab1, tab2, tab3 = st.tabs(["📊 Tableau de bord", "🟘️ Carte", "📋 Rapport"])

with tab1:
    st.subheader(f"📍 {selected_region}")
    region_data = df[df["Région"] == selected_region].iloc[0]

    cols = st.columns(4)
    for i, param in enumerate(PARAMS):
        with cols[i]:
            alert = region_data[PARAMS[param]]
            st.metric(param.replace("_", " "), region_data[param])
            st.write(f"🟢 Niveau : {alert}")
    st.markdown("#### 💬 Impacts")
    st.write(region_data["Impacts"])

with tab2:
    st.header("🟘️ Carte par région")
    param_carte = st.radio("Paramètre à visualiser :", list(PARAMS.keys()), horizontal=True)
    col_alert = PARAMS[param_carte]

    colors = {"Vert": "#00cc00", "Jaune": "#ffff00", "Orange": "#ff9900", "Rouge": "#cc0000"}

    fig, ax = plt.subplots(figsize=(10, 10))
    for _, row in df.iterrows():
        ax.scatter(row["Longitude"], row["Latitude"], color=colors[row[col_alert]], s=300, edgecolor='black')
        ax.text(row["Longitude"], row["Latitude"] + 0.3, row["Région"], ha='center', fontsize=8)

    ax.set_title(f"Niveau d'alerte - {param_carte}", fontsize=14)
    ax.set_xlim(8, 16)
    ax.set_ylim(2, 12)
    ax.set_aspect('equal')
    ax.axis("off")
    legend = [Line2D([0], [0], marker='o', color='w', label=k, markerfacecolor=v, markersize=15) for k, v in colors.items()]
    ax.legend(handles=legend, title="Niveaux", loc="lower left")
    st.pyplot(fig)

with tab3:
    st.header("📋 Rapport des alertes")
    alertes = []
    for param in PARAMS:
        alert_col = PARAMS[param]
        data = df[df[alert_col].isin(["Orange", "Rouge"])]
        if not data.empty:
            alertes.append((param.replace("_", " "), data))

    if not alertes:
        st.success("✅ Aucun danger signalé.")
    else:
        for titre, data in alertes:
            st.warning(f"⚠️ Alertes : {titre}")
            for _, row in data.iterrows():
                with st.expander(f"{row['Région']} - {row[PARAMS[titre.replace(' ', '_')]]}"):
                    st.write(f"- Cumul 10j : {row['Cumul_10j']} mm")
                    st.write(f"- Jours pluvieux consécutifs : {row['Jours_Consec']}")
                    st.write(f"- Intensité : {row['Intensite_Jours_Consec']} mm/j")
                    st.write(f"- Cumul journalier : {row['Cumul_Journalier']} mm")
                    st.write(f"- Impact : {row['Impacts']}")

        def strip_emojis(text):
            return re.sub(r'[^\x00-\x7F]+', '', text)

        def generate_pdf(alertes):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            pdf.set_font("Helvetica", 'B', 14)
            pdf.cell(0, 10, "Rapport des Alertes Meteo", ln=True, align="C")

            for titre, d in alertes:
                pdf.ln(8)
                clean_titre = strip_emojis(titre).upper()
                pdf.set_font("Helvetica", 'B', 12)
                pdf.cell(0, 10, f"ALERTE : {clean_titre}", ln=True)

                alerte_col = f"Alerte_{titre.replace(' ', '_')}"
                for _, row in d.iterrows():
                    pdf.set_font("Helvetica", '', 11)
                    impact_clean = strip_emojis(row['Impacts'])
                    texte = (
                        f"{row['Région']} - {row[alerte_col]}\n"
                        f"- Cumul 10j : {row['Cumul_10j']} mm\n"
                        f"- Jours consecutifs : {row['Jours_Consec']}\n"
                        f"- Intensite : {row['Intensite_Jours_Consec']} mm/j\n"
                        f"- Cumul journalier : {row['Cumul_Journalier']} mm\n"
                        f"- Impact : {impact_clean}\n"
                    )
                    pdf.multi_cell(0, 8, texte)

            buffer = io.BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            return buffer

        if st.button("📄 Générer rapport PDF"):
            pdf_file = generate_pdf(alertes)
            st.download_button("📅 Télécharger le PDF", data=pdf_file, file_name="rapport_alertes.pdf", mime="application/pdf")

# === Footer
st.markdown("""
<div style='text-align: center; margin-top:30px'>
    <em>Système d'Alerte Précoce Climat-Risques - Cameroun</em><br>
    <small>Développé avec Streamlit</small>
</div>
""", unsafe_allow_html=True)
