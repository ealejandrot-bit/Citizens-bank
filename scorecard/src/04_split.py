"""Paso 4 · Muestra.

Desarrollo / holdout 70/30 estratificado por hard_churn_6m × segment (semilla 42) y folds de la
CV 5×5 en desarrollo con la misma estratificación. Excluidos fuera de ambas muestras.
Guarda índices en outputs/tables/04_split.csv. El holdout solo evalúa (DM.1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split

from common import PARAMS, QC, SEED, TABLES, load_raw, save_table, set_seed

set_seed()
raw = load_raw()
T = PARAMS["target_primary"]
excl = raw["churn_excluded"].astype(bool)
pop = raw.loc[~excl].reset_index(drop=True)
strata = pop[T].astype(int).astype(str) + "_" + pop["segment"]

dev_idx, hold_idx = train_test_split(np.arange(len(pop)), test_size=PARAMS["holdout_frac"], stratify=strata, random_state=SEED)
split = pd.DataFrame({"household_id": raw["household_id"], "segment": raw["segment"], T: raw[T], "muestra": "excluido"})
split.loc[split.household_id.isin(pop.household_id.iloc[dev_idx]), "muestra"] = "desarrollo"
split.loc[split.household_id.isin(pop.household_id.iloc[hold_idx]), "muestra"] = "holdout"

# CV 5×5 en desarrollo, misma estratificación
dev = pop.iloc[np.sort(dev_idx)].reset_index(drop=True)
dev_strata = dev[T].astype(int).astype(str) + "_" + dev["segment"]
rskf = RepeatedStratifiedKFold(n_splits=PARAMS["cv_folds"], n_repeats=PARAMS["cv_repeats"], random_state=SEED)
folds = np.full((len(dev), PARAMS["cv_repeats"]), -1)
for k, (_, te) in enumerate(rskf.split(dev, dev_strata)):
    folds[te, k // PARAMS["cv_folds"]] = k % PARAMS["cv_folds"]
fold_df = pd.DataFrame(folds, columns=[f"cv_r{r + 1}" for r in range(PARAMS["cv_repeats"])])
fold_df["household_id"] = dev["household_id"]
split = split.merge(fold_df, on="household_id", how="left")
for c in fold_df.columns.drop("household_id"):
    split[c] = split[c].astype("Int64")
split.to_csv(TABLES / "04_split.csv", index=False)

# ── Balance entre muestras ──────────────────────────────────────────────────────────────
pop = pop.merge(split[["household_id", "muestra"]], on="household_id")
pop["union"] = ((pop.hard_churn_6m == 1) | (pop.soft_churn_3m == 1)).astype(int)
rows = []
for m, g in pop.groupby("muestra"):
    rows.append({"muestra": m, "hogares": len(g), "% hogares": 100 * len(g) / len(pop),
                 "eventos hard": int(g[T].sum()), "tasa hard %": 100 * g[T].mean(),
                 "% UHNW": 100 * (g.segment == "UHNW").mean(),
                 "eventos hard UHNW": int(g.loc[g.segment == "UHNW", T].sum()),
                 "tasa hard HNW %": 100 * g.loc[g.segment == "HNW", T].mean(),
                 "tasa hard UHNW %": 100 * g.loc[g.segment == "UHNW", T].mean(),
                 "tasa soft %": 100 * g.soft_churn_3m.mean(), "tasa unión %": 100 * g.union.mean(),
                 "RV $M": g.relationship_value.sum() / 1e6, "% RV": 100 * g.relationship_value.sum() / pop.relationship_value.sum(),
                 "churn valor hard %": 100 * (g.relationship_value * g[T]).sum() / g.relationship_value.sum(),
                 "RV máx $M": g.relationship_value.max() / 1e6})
bal = pd.DataFrame(rows)
save_table(bal.round(3), "04_balance")

cv = []
for c in [f"cv_r{r + 1}" for r in range(PARAMS["cv_repeats"])]:
    s = split[split.muestra == "desarrollo"]
    g = s.groupby(c).agg(hogares=(T, "size"), eventos=(T, "sum"),
                         eventos_uhnw=(T, lambda x: x[s.loc[x.index, "segment"] == "UHNW"].sum()))
    cv.append({"repetición": c, "hogares por fold": f"{g.hogares.min()}–{g.hogares.max()}",
               "eventos por fold": f"{int(g.eventos.min())}–{int(g.eventos.max())}",
               "eventos UHNW por fold": f"{int(g.eventos_uhnw.min())}–{int(g.eventos_uhnw.max())}"})
cv = pd.DataFrame(cv)
save_table(cv, "04_cv_folds")

qc = QC("04")
d, h = bal.set_index("muestra").loc["desarrollo"], bal.set_index("muestra").loc["holdout"]
qc.check("Desarrollo + holdout = población elegible", d.hogares + h.hogares == len(pop), len(pop), int(d.hogares + h.hogares))
qc.check("Sin hogares en ambas muestras", split.household_id.is_unique, "único", split.household_id.is_unique)
qc.check("Excluidos fuera de la muestra", int((split.muestra == "excluido").sum()) == 123, 123, int((split.muestra == "excluido").sum()))
qc.check("Proporción holdout ≈ 30%", abs(h["% hogares"] - 30) < 0.1, "30%", f"{h['% hogares']:.2f}%")
qc.check("Tasa hard dev vs holdout (±0.5 pp)", abs(d["tasa hard %"] - h["tasa hard %"]) <= 0.5,
         "≤ 0.5 pp", f"{d['tasa hard %']:.3f}% vs {h['tasa hard %']:.3f}%")
qc.check("% UHNW dev vs holdout (±0.5 pp)", abs(d["% UHNW"] - h["% UHNW"]) <= 0.5, "≤ 0.5 pp", f"{d['% UHNW']:.3f}% vs {h['% UHNW']:.3f}%")
qc.check("Tasa hard UHNW dev vs holdout (±0.5 pp)", abs(d["tasa hard UHNW %"] - h["tasa hard UHNW %"]) <= 0.5,
         "≤ 0.5 pp", f"{d['tasa hard UHNW %']:.3f}% vs {h['tasa hard UHNW %']:.3f}%")
qc.check("Todo hogar de desarrollo tiene fold en las 5 repeticiones", bool((folds >= 0).all()), "100%", f"{(folds >= 0).mean():.0%}")
qc.check("Churn por valor dev vs holdout (informativo, no estratificado)", abs(d["churn valor hard %"] - h["churn valor hard %"]) <= 1.0,
         "≤ 1 pp", f"{d['churn valor hard %']:.2f}% vs {h['churn valor hard %']:.2f}%", severity="warn")
print("\n" + bal.round(2).to_string(index=False))
print("\n" + cv.to_string(index=False))
qc.gate()
