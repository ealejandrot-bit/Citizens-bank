"""Fase 2 · Data quality (población de la fase 1; no se elimina ninguna fila).

Missingness (clasificación con criterios declarados, D2.1):
  estructural  el missing coincide con un gatillo has_* = False en ≥ 97% de los faltantes y ≥ 97% de los gatillo False
               (detectado en los datos, no copiado de M1);
  ruido        sin gatillo, missing ≤ 5% y sin asociación con el churn (IC 95% de Newcombe de la diferencia de tasa
               any_churn, faltante vs no faltante, incluye 0);
  sin regla    el resto (missing alto o informativo).
Indicadores app_<feature> = 1 si la variable aplica (gatillo True) para las variables estructurales.
Rangos extremos: por variable numérica, filas fuera de límites lógicos (error) y fuera de [Q1 − 3·IQR, Q3 + 3·IQR]
(extremo); decisión propuesta por variable (conservar / revisar), sin aplicar nada.
Salidas: outputs/p02/*.csv, data/processed/features_p02.parquet (features crudas + app_*; sin columnas de resultado).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from statsmodels.stats.proportion import proportion_confint

from config import P, get, set_seed
from report import render

set_seed()
raw = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))
pop = pd.read_parquet(P.processed / "population.parquet")
df = raw.merge(pop[["household_id", "y_any"]], on="household_id")          # solo población de la fase 1
FORB = set(get("leakage.forbidden")) | set(get("leakage.excluded_regulatory"))
if get("leakage.multi_signal_count") == "exclude":                        # decisión del usuario (fase 3)
    FORB |= {"multi_signal_count", "multi_signal_flag"}
FEAT = [c for c in raw.columns if c not in FORB and c != "segment"]
HAS = [c for c in raw.columns if c.startswith("has_")]
y = df.y_any.to_numpy()

rows = []
for c in FEAT:
    na = df[c].isna()
    if not na.any():
        continue
    best, agree_na, agree_f = None, 0.0, 0.0
    for h in HAS:
        f = ~df[h].astype(bool)
        a1 = (na & f).sum() / na.sum()                 # faltantes explicados por gatillo False
        a2 = (na & f).sum() / max(f.sum(), 1)          # gatillo False que efectivamente faltan
        if min(a1, a2) > min(agree_na, agree_f):
            best, agree_na, agree_f = h, a1, a2
    e1, n1, e0, n0 = int(y[na.to_numpy()].sum()), int(na.sum()), int(y[~na.to_numpy()].sum()), int((~na).sum())
    r1, r0 = e1 / n1, e0 / n0
    l1, u1 = proportion_confint(e1, n1, method="wilson")
    l0, u0 = proportion_confint(e0, n0, method="wilson")
    lo = (r1 - r0) - np.sqrt((r1 - l1) ** 2 + (u0 - r0) ** 2)     # IC de Newcombe (válido con pocos casos)
    hi = (r1 - r0) + np.sqrt((u1 - r1) ** 2 + (r0 - l0) ** 2)
    if best is not None and agree_na >= 0.97 and agree_f >= 0.97:
        cls = "estructural"
    elif na.mean() <= 0.05 and lo <= 0 <= hi:
        cls = "ruido"
    else:
        cls = "sin regla"
    exc_a = int((na & df[best].astype(bool)).sum()) if best else np.nan        # falta aunque aplica
    exc_b = int((~na & ~df[best].astype(bool)).sum()) if best else np.nan      # tiene dato aunque no aplica
    rows.append({"variable": c, "% missing": 100 * na.mean(), "faltantes": int(na.sum()), "clase": cls, "gatillo": best if cls == "estructural" else "",
                 "% faltantes con gatillo False": 100 * agree_na if best else np.nan, "% gatillo False que faltan": 100 * agree_f if best else np.nan,
                 "falta aunque aplica": exc_a if cls == "estructural" else np.nan, "dato aunque no aplica": exc_b if cls == "estructural" else np.nan, "any_churn % faltante": 100 * r1, "any_churn % no faltante": 100 * r0,
                 "Δ pp (IC 95%)": f"{100 * (r1 - r0):+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}]"})
MS = pd.DataFrame(rows).sort_values(["clase", "% missing"], ascending=[True, False])

# Indicadores app_<feature>
X = df[["household_id"] + FEAT].copy()
APP = []
for _, r in MS[MS.clase == "estructural"].iterrows():
    col = f"app_{r.variable}"
    X[col] = df[r.gatillo].astype(int)
    APP.append({"indicador": col, "definición": f"1 si {r.gatillo} = True (la variable aplica)", "% con 1": 100 * X[col].mean(),
                "coincide con dato presente %": 100 * ((X[col] == 1) == df[r.variable].notna()).mean()})
APPT = pd.DataFrame(APP)
X.to_parquet(P.processed / "features_p02.parquet", index=False)

# Rangos extremos
PCT_NONNEG = [c for c in FEAT if c.endswith(("_pct", "_ratio")) and ("outflow" in c or "redemption" in c or "liquidated" in c or "transfer" in c)
              and "net" not in c and "change" not in c and "vs_baseline" not in c]          # "vs_baseline" es un cambio: admite negativos
ext = []
for c in FEAT:
    x = pd.to_numeric(df[c], errors="coerce")
    if x.dropna().nunique() <= 2 or c.startswith("has_"):
        continue
    q1, q3 = x.quantile([0.25, 0.75])
    iqr = q3 - q1
    lo_f, hi_f = q1 - 3 * iqr, q3 + 3 * iqr
    n_ext = int(((x < lo_f) | (x > hi_f)).sum()) if iqr > 0 else 0
    rules = []
    if c in ("share_of_wallet", "client_reply_rate"):
        rules.append(((x < 0) | (x > 1)).sum())
    if c in PCT_NONNEG or c in ("tenure_years", "history_months", "relationship_value", "deposit_balance", "aum", "recurring_income_monthly", "aum_outflow_90d",
                                "transfer_to_competitor_bank_amount_90d", "complaint_age_days", "new_external_destinations_90d", "products_closed_180d", "accounts_closed_90d",
                                "meetings_cancelled_by_client", "contact_gap_ratio"):
        rules.append((x < 0).sum())
    n_err = int(sum(rules)) if rules else 0
    ext.append({"variable": c, "mín": x.min(), "p1": x.quantile(0.01), "mediana": x.median(), "p99": x.quantile(0.99), "máx": x.max(),
                "filas fuera de límite lógico (error)": n_err, "filas extremas (3·IQR)": n_ext, "% extremas": 100 * n_ext / x.notna().sum(),
                "decisión propuesta": ("revisar con el dueño del dato (valores imposibles)" if n_err else
                                       "conservar (extremo real); NAM: transformación por cuantiles, sin recorte" if n_ext else "conservar")})
EXT = pd.DataFrame(ext).sort_values("filas extremas (3·IQR)", ascending=False)

out = P.out(2)
MS.to_csv(out / "missingness.csv", index=False)
APPT.to_csv(out / "app_indicators.csv", index=False)
EXT.to_csv(out / "extreme_ranges.csv", index=False)
SUM = {"hogares (población fase 1)": len(df), "features evaluadas": len(FEAT), "variables con missing": len(MS),
       **{f"missing {k}": int(v) for k, v in MS.clase.value_counts().items()}, "indicadores app_ creados": len(APPT),
       "variables con valores imposibles": int((EXT["filas fuera de límite lógico (error)"] > 0).sum()),
       "variables con extremos (3·IQR)": int((EXT["filas extremas (3·IQR)"] > 0).sum()), "filas eliminadas": 0}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 2 · Data quality", "order": ["summary.json", "missingness.csv", "app_indicators.csv", "extreme_ranges.csv"],
           "notes": {"missingness.csv": "Criterios: estructural ≥ 97% de acuerdo con un gatillo has_* en ambos sentidos; ruido ≤ 5% sin asociación con any_churn; sin regla = resto.",
                     "extreme_ranges.csv": "Decisiones propuestas, no aplicadas: se esperan decisiones del usuario."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
print(render(2)); print(SUM); print(MS[["variable", "% missing", "clase", "gatillo", "falta aunque aplica", "dato aunque no aplica", "Δ pp (IC 95%)"]].round(2).to_string(index=False))
print(APPT.round(2).to_string(index=False)); print(EXT[["variable", "filas fuera de límite lógico (error)", "filas extremas (3·IQR)", "% extremas", "máx", "decisión propuesta"]].head(25).round(3).to_string(index=False))
