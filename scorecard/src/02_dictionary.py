"""Paso 2 · Diccionario de datos.

Clasifica las 62 columnas (rol, dimensión, ventana, unidad, tipo de feature, missing estructural,
dirección esperada, elegibilidad) a partir de src/dictionary.py y agrega el % missing observado.
"""
from __future__ import annotations

import pandas as pd

from common import FORBIDDEN, QC, load_raw, save_table
from dictionary import dictionary

raw = load_raw()
d = dictionary()
d["tipo"] = d["columna"].map(lambda c: str(raw[c].dtype))
d["% missing"] = d["columna"].map(lambda c: round(raw[c].isna().mean() * 100, 2))
d = d[["columna", "rol", "dimensión", "tipo", "ventana", "unidad", "tipo_feature", "% missing", "missing_estructural",
       "dirección_esperada", "elegible", "revisión", "descripción"]]

qc = QC("02")
qc.check("Las 62 columnas clasificadas", set(d["columna"]) == set(raw.columns) and len(d) == 62, 62,
         f"{len(d)} (faltan: {sorted(set(raw.columns) - set(d['columna']))}, sobran: {sorted(set(d['columna']) - set(raw.columns))})")
qc.check("Ninguna columna prohibida es elegible", not d.loc[d.columna.isin(FORBIDDEN), "elegible"].any(), "0",
         d.loc[d.columna.isin(FORBIDDEN) & d.elegible, "columna"].tolist())
qc.check("Toda señal tiene dirección esperada", bool(d.loc[d.rol == "señal", "dirección_esperada"].isin(["+", "−"]).all()), "+/−",
         d.loc[(d.rol == "señal") & ~d["dirección_esperada"].isin(["+", "−"]), "columna"].tolist())
missing_cols = d.loc[d["% missing"] > 0, "columna"]
undoc = [c for c in missing_cols if not d.set_index("columna").loc[c, "missing_estructural"]]
print(f"  [INFO] Columnas con missing sin condición estructural (se explican en el paso 3): {undoc}")

save_table(d, "02_data_dictionary")
summary = (d.groupby(["rol", "dimensión"], sort=False)
           .agg(columnas=("columna", "size"), elegibles=("elegible", "sum")).reset_index())
save_table(summary, "02_dictionary_summary")
print("\n" + summary.to_string(index=False))
print(f"\nElegibles: {int(d.elegible.sum())} · No elegibles: {int((~d.elegible).sum())}")
qc.gate()
