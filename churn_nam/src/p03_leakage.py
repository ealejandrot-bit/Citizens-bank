"""Fase 3 · Leakage: outputs/p03/leakage_table.csv con una fila por columna del archivo + indicadores app_.

Por columna: rol, momento (resultado post-T0 / señal pre-T0 asumida, L2), AUC univariada orientada vs A y vs B, IV
(deciles), |ρ Spearman| con value_lost_6m, y decisión: prohibida (resultado, id, fecha, regulatoria G1-3) / revisar
(AUC > 0.85 o IV > 0.50, regla de M1) / permitida. `multi_signal_count` y `multi_signal_flag`: decisión según
config.leakage.multi_signal_count (si está en null, la fase se detiene y pregunta).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from config import P, get, need, set_seed
from report import render

set_seed()
raw = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))
pop = pd.read_parquet(P.processed / "population.parquet")
X2 = pd.read_parquet(P.processed / "features_p02.parquet")
D = raw.merge(pop[["household_id", "y_A", "y_B"]], on="household_id").merge(X2[["household_id"] + [c for c in X2.columns if c.startswith("app_")]], on="household_id")
FORB, REG = get("leakage.forbidden"), get("leakage.excluded_regulatory")
COMP = ["multi_signal_count", "multi_signal_flag"]


def auc(y, x):
    m = ~np.isnan(y)
    x, y = x[m], y[m]
    x = np.where(np.isnan(x), np.nanmedian(x), x)
    if np.unique(x).size < 2:
        return np.nan
    a = roc_auc_score(y, x)
    return max(a, 1 - a)


def iv(y, x, q=10):
    m = ~np.isnan(y)
    s = pd.DataFrame({"x": x[m], "y": y[m]})
    s["b"] = pd.qcut(s.x.rank(method="first"), q, labels=False) if s.x.nunique() > q else s.x
    s["b"] = s["b"].astype("object").where(s.x.notna(), "NA")
    t = s.groupby("b").y.agg(["sum", "size"])
    bad, good = t["sum"] + 0.5, t["size"] - t["sum"] + 0.5
    pb, pg = bad / bad.sum(), good / good.sum()
    return float(((pg - pb) * np.log(pg / pb)).sum())


yA, yB = D.y_A.to_numpy(float), D.y_B.to_numpy(float)
vl = D.value_lost_6m.fillna(0)
rows = []
for c in [c for c in raw.columns] + [c for c in D.columns if c.startswith("app_")]:
    if c in FORB:
        rol = "resultado (post-T0)" if c in ("value_lost_6m", "hard_churn_6m", "soft_churn_3m", "churn_excluded") else "identificador / fecha"
    elif c in REG:
        rol = "regulatoria (G1-3 de M1)"
    elif c in COMP:
        rol = "compuesto del proveedor (regla no documentada, L3)"
    elif c.startswith("app_"):
        rol = "indicador de aplicabilidad (fase 2)"
    else:
        rol = "predictor candidato"
    x = pd.to_numeric(D[c], errors="coerce").to_numpy(float) if c not in ("household_id", "snapshot_date", "segment") else None
    if c == "segment":
        x = (D.segment == "UHNW").astype(float).to_numpy()
    a_A = auc(yA, x) if x is not None else np.nan
    a_B = auc(yB, x) if x is not None else np.nan
    i_B = iv(yB, x) if x is not None and c not in FORB else np.nan
    r_vl = abs(pd.Series(x).corr(vl, method="spearman")) if x is not None and c != "value_lost_6m" else np.nan
    if c in FORB or c in REG:
        dec, why = "prohibida", rol
    elif c in COMP:
        dec, why = "pendiente", "según config.leakage.multi_signal_count"
    elif (a_B > 0.85) or (i_B > 0.50):
        dec, why = "revisar", "AUC > 0.85 o IV > 0.50"
    else:
        dec, why = "permitida", "señal pre-T0 (asumida, L2) sin evidencia de fuga"
    rows.append({"columna": c, "rol": rol, "momento": "post-T0" if c in ("value_lost_6m", "hard_churn_6m", "soft_churn_3m", "churn_excluded") else "pre-T0 (asumido)",
                 "AUC vs A": a_A, "AUC vs B": a_B, "IV vs B": i_B, "|ρ| con value_lost_6m": r_vl, "decisión": dec, "motivo": why})
L = pd.DataFrame(rows)
out = P.out(3)
policy = get("leakage.multi_signal_count")
if policy is not None:
    mp = {"include": ("permitida", "decisión del usuario: include"), "exclude": ("prohibida", "decisión del usuario: exclude"),
          "challenger_only": ("solo challenger", "decisión del usuario: challenger_only")}[policy]
    L.loc[L.columna.isin(COMP), ["decisión", "motivo"]] = mp
L.to_csv(out / "leakage_table.csv", index=False)
SUM = {"columnas evaluadas": len(L), **{f"decisión {k}": int(v) for k, v in L["decisión"].value_counts().items()},
       "máx AUC vs B entre permitidas": float(L.loc[L["decisión"] == "permitida", "AUC vs B"].max()),
       "máx IV vs B entre permitidas": float(L.loc[L["decisión"] == "permitida", "IV vs B"].max()),
       "multi_signal_count (config)": policy}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 3 · Leakage", "order": ["summary.json", "leakage_table.csv"],
           "notes": {"leakage_table.csv": "AUC orientada = máx(AUC, 1 − AUC); IV por deciles con missing como bin; umbrales de sospecha de M1 (AUC > 0.85 o IV > 0.50)."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(3)
print(SUM); print(L.sort_values("AUC vs B", ascending=False).head(12)[["columna", "rol", "AUC vs A", "AUC vs B", "IV vs B", "|ρ| con value_lost_6m", "decisión"]].round(3).to_string(index=False))
need("leakage.multi_signal_count", fase=3)          # la fase se cierra solo con la decisión del usuario
