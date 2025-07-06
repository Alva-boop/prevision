#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul  6 17:36:56 2025

@author: alvine
"""

import xarray as xr
import pandas as pd

# === Fichier NetCDF ===
fichier_nc = "/home/alvine/prevision_1/wrfout_d01_2025-06-03_00_precipitation_total_cameroun.nc"

# === Ouvre le fichier et liste les variables ===
ds = xr.open_dataset(fichier_nc)
print("Variables disponibles :", list(ds.data_vars))

# === Remplace 'tp' par le nom exact de ta variable ===
var = "RAIN_SUM"  # À modifier si besoin

# === Convertit en DataFrame ===
df = ds[var].to_dataframe().reset_index()

# === Enregistre au format CSV ===
df.to_csv("precipitation_total.csv", index=False)
print("✅ Fichier CSV créé : precipitation_total.csv")


