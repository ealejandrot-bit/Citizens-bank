"""Fase 4 · Features y monotonía (sin entrenar nada; el commit espera la confirmación de signos del usuario).

- Aplica las decisiones de la fase 2 (config.quality): dato aunque no aplica → NaN "no aplica"; falta aunque aplica →
  NaN "sin dato"; indicador miss_<feature> para missing "sin regla"; "ruido" sin indicador.
- Feature dictionary con origen de cada columna (proveedor / indicador app_ / indicador miss_ / recodificación).
- Mapa de monotonía cargado de docs/SPEC.md §4; columnas sin signo en §4 quedan "propuesta" para confirmar.
- Evidencia: dirección observada (Spearman con y_A y con y_B) solo en el dev heredado (el test no se mira).
Salidas: data/processed/X_features.parquet, outputs/p04/feature_dictionary.csv, outputs/p04/monotonicity_review.csv.
"""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from config import P, ROOT, get, set_seed
from report import render

set_seed()
X = pd.read_parquet(P.processed / "features_p02.parquet")
raw = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))[["household_id", "segment"]]
MS = pd.read_csv(P.out(2) / "missingness.csv")
pop = pd.read_parquet(P.processed / "population.parquet")

# Recodificación de excepciones al gatillo (decisión fase 2)
rec = []
for _, r in MS[MS.clase == "estructural"].iterrows():
    v, app = r.variable, f"app_{r.variable}"
    present_na = (X[app] == 0) & X[v].notna()
    if present_na.any() and get("quality.trigger_present_not_applicable") == "no_aplica":
        X.loc[present_na, v] = np.nan
    rec.append({"variable": v, "dato aunque no aplica → NaN (no aplica)": int(present_na.sum()), "falta aunque aplica (sin dato, queda NaN)": int(((X[app] == 1) & X[v].isna()).sum())})
REC = pd.DataFrame(rec)
# Indicadores de missing "sin regla"
MISS = []
for v in MS.loc[MS.clase == "sin regla", "variable"]:
    X[f"miss_{v}"] = X[v].isna().astype(int)
    MISS.append(v)
X = X.merge(raw, on="household_id")
X.insert(1, "segment_uhnw", (X.pop("segment") == "UHNW").astype(int))
APPC = [c for c in X.columns if c.startswith("app_")]
X[["household_id"] + APPC].to_parquet(P.processed / "masks_app.parquet", index=False)   # máscaras "no aplica" del NAM (no son features)

# Mapa de monotonía de SPEC §4
spec = (ROOT / "docs" / "SPEC.md").read_text(encoding="utf-8")
sec = spec[spec.index("## 4."):spec.index("## 5.")]
SIGN = {}
for line in sec.splitlines():
    m = re.match(r"^\| (.+?) \| ([+−?]) \| (dura|libre) \|$", line.strip())
    if not m:
        continue
    for tok in [t.strip() for t in m.group(1).split(",")]:
        if tok.startswith("has_*"):
            for h in [c for c in X.columns if c.startswith("has_")]:
                SIGN[h] = (m.group(2), m.group(3))
        elif tok.startswith("miss_*"):
            for h in [c for c in X.columns if c.startswith("miss_")]:
                SIGN[h] = (m.group(2), m.group(3))
        else:
            SIGN[tok] = (m.group(2), m.group(3))
SIGN["segment_uhnw"] = SIGN.pop("segment", ("?", "libre"))

dev_ids = set(pd.read_parquet(P.m1 / "data" / "processed" / "dev.parquet").household_id)
D = X[X.household_id.isin(dev_ids)].merge(pop[["household_id", "y_A", "y_B"]], on="household_id")
feats = [c for c in X.columns if c != "household_id"]
rows = []
for c in feats:
    if c.startswith("app_"):
        base = c[4:]
        origen, src = "indicador de aplicabilidad (fase 2)", "igual a su gatillo has_*"
        gat = MS.set_index("variable").loc[base, "gatillo"]
        dup = bool((X[c] == X[gat].astype(int)).all())
        sg, kind, fuente = SIGN.get(gat, ("?", "libre"))[0], SIGN.get(gat, ("?", "libre"))[1], f"hereda de {gat} (duplicado exacto: {dup})"
    elif c.startswith("miss_"):
        origen, fuente = "indicador de missing 'sin regla' (fase 2)", "propuesta: libre (sin hipótesis de negocio)"
        sg, kind = "?", "libre"
    else:
        origen = "proveedor" if c != "segment_uhnw" else "proveedor (segment → 1 si UHNW)"
        if c in SIGN:
            sg, kind = SIGN[c]
            fuente = "SPEC §4 (G1-1 de M1)"
        else:
            sg, kind, fuente = "?", "libre", "propuesta: no está en SPEC §4"
    rA = D[c].corr(D.y_A, method="spearman")
    rB = D[c].corr(D.y_B, method="spearman")
    obs = "+" if rA > 0.01 else "−" if rA < -0.01 else "≈0"
    rows.append({"feature": c, "origen": origen, "tipo": "binaria" if X[c].dropna().nunique() <= 2 else "continua/conteo", "% NaN": 100 * X[c].isna().mean(),
                 "signo propuesto": sg, "restricción": kind, "fuente del signo": fuente, "ρ Spearman dev vs A": rA, "ρ Spearman dev vs B": rB, "dirección observada (A)": obs,
                 "coincide": "—" if sg == "?" else ("sí" if obs == sg else "≈0 (sin señal)" if obs == "≈0" else "NO")})
FD = pd.DataFrame(rows)
FD["entra como feature"] = ~FD.origen.str.startswith("indicador de aplic")                 # E: app_ solo como máscara
FD["estado"] = "confirmado por el usuario (2026-09-29)"
FEATS = FD.loc[FD["entra como feature"], "feature"].tolist()
X[["household_id"] + FEATS].to_parquet(P.processed / "X_features.parquet", index=False)
MAP = {r.feature: {"signo": r["signo propuesto"], "restricción": r.restricción} for _, r in FD[FD["entra como feature"]].iterrows()}
out = P.out(4)
json.dump(MAP, open(out / "monotonicity_map.json", "w"), ensure_ascii=False, indent=1)
FD.to_csv(out / "feature_dictionary.csv", index=False)
REV = FD[["feature", "signo propuesto", "restricción", "fuente del signo", "ρ Spearman dev vs A", "ρ Spearman dev vs B", "coincide"]]
REV.to_csv(out / "monotonicity_review.csv", index=False)
REC.to_csv(out / "trigger_recodes.csv", index=False)
SUM = {"features": len(feats), "proveedor": int(FD.origen.str.startswith("proveedor").sum()), "app_": int(FD.origen.str.startswith("indicador de aplic").sum()),
       "miss_": len(MISS), "restricción dura +": int(((FD.restricción == "dura") & (FD["signo propuesto"] == "+")).sum()),
       "restricción dura −": int(((FD.restricción == "dura") & (FD["signo propuesto"] == "−")).sum()), "libres": int((FD.restricción == "libre").sum()),
       "signo contrario a lo observado (NO)": FD.loc[FD.coincide == "NO", "feature"].tolist(), "sin señal observada (≈0)": FD.loc[FD.coincide == "≈0 (sin señal)", "feature"].tolist(),
       "app_ duplicados exactos de has_* (máscaras, no features)": int(FD["fuente del signo"].str.contains("duplicado exacto: True").sum()),
       "features que entran": len(FEATS), "estado": "mapa confirmado por el usuario (2026-09-29)"}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 4 · Features y monotonía (mapa confirmado)", "order": ["summary.json", "monotonicity_map.json", "monotonicity_review.csv", "trigger_recodes.csv", "feature_dictionary.csv"],
           "notes": {"monotonicity_review.csv": "Dirección observada solo en dev heredado (sin mirar test); 'NO' = signo propuesto contrario a lo observado."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(4)
print(SUM)
