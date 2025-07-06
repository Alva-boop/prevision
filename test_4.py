#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAP Météo Cameroun - Carte + PDF + Alertes (version automatisée depuis NetCDF)
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from fpdf import FPDF
import io
import os
import re
import xarray as xr
import numpy as np
from shapely.geometry import Point
from datetime import timedelta

st.set_page_config(layout="wide", page_title="SAP Météo Cameroun", page_icon="⛈️")

# === PARAMÈTRES ===
fichier_nc = "/home/alvine/prevision_1/wrfout_d01_2025-06-03_00_precipitation_total_cameroun.nc"
shapefile = "/home/alvine/Cartographie/CMR_adm_Donald/CMR_adm1.shp"

# === CHARGER LES DONNÉES ===
ds = xr.open_dataset(fichier_nc)
rain = ds["RAIN_SUM"]
gdf_regions = gpd.read_file(shapefile).to_crs("EPSG:4326")

rain_df = rain.to_dataframe().reset_index()
rain_df = rain_df.dropna(subset=["RAIN_SUM"])
rain_df["geometry"] = [Point(xy) for xy in zip(rain_df["lon"], rain_df["lat"])]
rain_gdf = gpd.GeoDataFrame(rain_df, geometry="geometry", crs="EPSG:4326")
rain_gdf = gpd.sjoin(rain_gdf, gdf_regions[["NAME_1", "geometry"]], how="inner", predicate="within")
rain_gdf = rain_gdf.rename(columns={"NAME_1": "Région"})

regions = rain_gdf["Région"].unique()
regions_data = {"Région": [], "Cumul_10j": [], "Jours_Consec": [], "Intensite_Jours_Consec": [], "Cumul_Journalier": [], "Latitude": [], "Longitude": [], "Impacts": [], "Dates_Journalier": []}

for region in regions:
    rdata = rain_gdf[rain_gdf["Région"] == region].copy()
    ts_region = rdata.groupby("time")["RAIN_SUM"].mean()

    cumul_journalier = ts_region[-1]
    date_cumul_journalier = ts_region.index[-1].strftime("%Y-%m-%d")

    cumul_10j = ts_region[-10:].max()

    is_rain = ts_region > 1.0
    groupes = (is_rain != is_rain.shift()).cumsum()
    series = is_rain.groupby(groupes).agg(['all', 'size'])
    max_consec = series[series["all"] == True]["size"].max()
    max_consec = int(max_consec) if not np.isnan(max_consec) else 0

    if max_consec > 0:
        intensite_consec = ts_region[-max_consec:].mean()
    else:
        intensite_consec = 0

    geom = gdf_regions[gdf_regions["NAME_1"] == region].geometry.iloc[0]
    lon, lat = geom.centroid.x, geom.centroid.y
    impact = "À définir selon le niveau de risque"

    regions_data["Région"].append(region)
    regions_data["Latitude"].append(lat)
    regions_data["Longitude"].append(lon)
    regions_data["Cumul_10j"].append(round(cumul_10j, 1))
    regions_data["Jours_Consec"].append(max_consec)
    regions_data["Intensite_Jours_Consec"].append(round(intensite_consec, 1))
    regions_data["Cumul_Journalier"].append(round(cumul_journalier, 1))
    regions_data["Dates_Journalier"].append(date_cumul_journalier)
    regions_data["Impacts"].append(impact)

df = pd.DataFrame(regions_data)

# === Interface de modification manuelle ===
with st.sidebar:
    st.header("⚙️ Modifier une région")
    selected_region = st.selectbox("Sélectionner une région", df["Région"].unique())
    region_idx = df[df["Région"] == selected_region].index[0]

    df.at[region_idx, "Cumul_10j"] = st.number_input("Cumul 10 jours (mm)", value=float(df.at[region_idx, "Cumul_10j"]))
    df.at[region_idx, "Jours_Consec"] = st.number_input("Jours consécutifs", value=int(df.at[region_idx, "Jours_Consec"]))
    df.at[region_idx, "Intensite_Jours_Consec"] = st.number_input("Intensité consécutifs (mm/j)", value=float(df.at[region_idx, "Intensite_Jours_Consec"]))
    df.at[region_idx, "Cumul_Journalier"] = st.number_input("Cumul journalier (mm)", value=float(df.at[region_idx, "Cumul_Journalier"]))

# === SEUILS ===
SEUILS = {
    "Cumul_10j": {"Vert": (0, 50), "Jaune": (51, 100), "Orange": (101, 200), "Rouge": (201, 1000)},
    "Jours_Consec": {"Vert": (0, 1), "Jaune": (2, 3), "Orange": (4, 5), "Rouge": (6, 100)},
    "Intensite_Jours_Consec": {"Vert": (0, 19), "Jaune": (20, 39), "Orange": (40, 59), "Rouge": (60, 1000)},
    "Cumul_Journalier": {"Vert": (0, 15), "Jaune": (16, 25), "Orange": (26, 75), "Rouge": (76, 400)}
}

# === Alerte

def get_alert_level(value, param):
    for level, (min_val, max_val) in SEUILS[param].items():
        if min_val <= value <= max_val:
            return level
    return "Vert"

for param in ["Cumul_10j", "Jours_Consec", "Intensite_Jours_Consec", "Cumul_Journalier"]:
    df[f"Alerte_{param}"] = df[param].apply(lambda x: get_alert_level(x, param))

PARAMS = {
    "Cumul_10j": "Alerte_Cumul_10j",
    "Jours_Consec": "Alerte_Jours_Consec",
    "Intensite_Jours_Consec": "Alerte_Intensite_Jours_Consec",
    "Cumul_Journalier": "Alerte_Cumul_Journalier"
}

# === Rapport PDF

def strip_emojis(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

def generate_pdf(df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Rapport des Alertes Météo", ln=True, align="C")

    for i, row in df.iterrows():
        pdf.ln(5)
        pdf.set_font("Helvetica", 'B', 12)
        titre = strip_emojis(row['Région'])
        pdf.cell(0, 10, f"{titre}", ln=True)
        pdf.set_font("Helvetica", '', 11)
        texte = (
            f"- Cumul 10 jours : {row['Cumul_10j']} mm\n"
            f"- Jours consécutifs : {row['Jours_Consec']}\n"
            f"- Intensité consécutifs : {row['Intensite_Jours_Consec']} mm/j\n"
            f"- Cumul journalier ({row['Dates_Journalier']}) : {row['Cumul_Journalier']} mm\n"
            f"- Impact : {strip_emojis(row['Impacts'])}\n"
        )
        pdf.multi_cell(0, 8, texte)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

if st.button("📄 Générer le rapport PDF"):
    pdf_file = generate_pdf(df)
    st.download_button("📥 Télécharger le PDF", data=pdf_file, file_name="rapport_alertes.pdf", mime="application/pdf")

# === Interface
st.header("🚨 Système d'Alerte Précoce - Cameroun")
tab1, tab2 = st.tabs(["📊 Tableau de bord", "🗺️ Carte"])

with tab1:
    st.subheader(f"📍 {selected_region}")
    region_data = df[df["Région"] == selected_region].iloc[0]
    cols = st.columns(4)
    for i, param in enumerate(PARAMS):
        with cols[i]:
            alert = region_data[PARAMS[param]]
            st.metric(param.replace("_", " "), region_data[param])
            st.write(f"🟢 Niveau : {alert}")
    st.markdown(f"#### 📅 Date : {region_data['Dates_Journalier']}")
    st.markdown("#### 💬 Impacts")
    st.write(region_data["Impacts"])

with tab2:
    st.header("🗺️ Carte par région")
    param_carte = st.radio("Paramètre à visualiser :", list(PARAMS.keys()), horizontal=True)
    col_alert = PARAMS[param_carte]
    gdf = gpd.read_file(shapefile).to_crs("EPSG:4326")
    gdf = gdf.merge(df[["Région", col_alert]], left_on="NAME_1", right_on="Région", how="left")

    colors = {"Vert": "#00cc00", "Jaune": "#ffff00", "Orange": "#ff9900", "Rouge": "#cc0000"}
    gdf["color"] = gdf[col_alert].map(colors)

    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(color=gdf["color"], edgecolor="black", ax=ax)
    ax.set_title(f"Niveau d'alerte - {param_carte}", fontsize=14)
    ax.axis("off")
    legend = [Line2D([0], [0], marker='s', color='w', label=k, markerfacecolor=v, markersize=15) for k, v in colors.items()]
    ax.legend(handles=legend, title="Niveaux", loc="lower left")
    st.pyplot(fig)

# === Footer
st.markdown("""
<div style='text-align: center; margin-top:30px'>
    <em>Système d'Alerte Précoce Climat-Risques - Cameroun</em><br>
    <small>Développé avec Streamlit</small>
</div>
""", unsafe_allow_html=True)


