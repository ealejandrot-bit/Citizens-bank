"""Paso 15 · Estabilidad del campeón (dev vs val; sin dimensión temporal ⟹ sin PSI temporal, L1).

- PSI = Σ (%val − %dev)·ln(%val / %dev) con bins fijados en dev: score (deciles de dev), p calibrada (deciles de dev),
  tramo, y cada variable del modelo (sus bins WoE). Umbrales de lectura: < 0.10 estable, 0.10–0.25 vigilar, > 0.25 cambio.
- Por subgrupo (segmento, quintil de RV, banda de antigüedad, historia < 24 meses, cluster): PSI del score dev → val
  dentro del subgrupo, y PSI de la mezcla de subgrupos.
- Deriva de contribuciones: |β_j·WoE_j| medio en los 25 entrenamientos de la CV 5×5 (bins fijos); coeficiente de
  variación entre folds y rango de la participación de cada variable.
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import MODEL, PROC, REPORTS, load_split, md_table, save_table, set_seed
from woe import woe_frame

set_seed()
SC = pd.read_parquet(PROC / "step12_scores.parquet")
CAL = pickle.load(open(MODEL / "step14_calibrator.pkl", "rb"))
CH = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))
V, BIN = CH["vars"], CH["binning"]
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]


def part(p):
    d = load_split(p).merge(SC, on="household_id").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
    d = d[d.in_pop_B].reset_index(drop=True)
    d["p_cal"] = 1 / (1 + np.exp(-(CAL["a"] + CAL["b"] * np.log(d.probabilidad / (1 - d.probabilidad)))))
    return d


dev, val = part("dev"), part("val")


def psi_from_labels(a, b, cats=None):
    cats = cats if cats is not None else sorted(set(a) | set(b), key=str)
    pa = pd.Series(a).value_counts(normalize=True).reindex(cats).fillna(0).to_numpy()
    pb = pd.Series(b).value_counts(normalize=True).reindex(cats).fillna(0).to_numpy()
    pa, pb = np.clip(pa, 1e-4, None), np.clip(pb, 1e-4, None)
    return float(((pb - pa) * np.log(pb / pa)).sum())


def dec_labels(x_dev, x):
    e = np.unique(np.quantile(x_dev, np.linspace(0, 1, 11)[1:-1]))
    return np.searchsorted(e, x, side="right")


def read(v):
    return "estable" if v < 0.10 else "vigilar" if v <= 0.25 else "cambio"


rows = [{"objeto": "score (deciles de dev)", "PSI": psi_from_labels(dec_labels(dev.score, dev.score), dec_labels(dev.score, val.score))},
        {"objeto": "p calibrada (deciles de dev)", "PSI": psi_from_labels(dec_labels(dev.p_cal, dev.p_cal), dec_labels(dev.p_cal, val.p_cal))},
        {"objeto": "tramo", "PSI": psi_from_labels(dev.tramo, val.tramo, TR)}]
for c in V:
    r_d = dev[f"{c}__miss"] if f"{c}__miss" in dev else None
    r_v = val[f"{c}__miss"] if f"{c}__miss" in val else None
    rows.append({"objeto": f"variable · {c} (bins WoE)", "PSI": psi_from_labels(BIN[c].bin_labels(dev[c], r_d), BIN[c].bin_labels(val[c], r_v), BIN[c].labels)})
P1 = pd.DataFrame(rows)
P1["lectura"] = P1.PSI.map(read)
save_table(P1, "step15_psi")

# Subgrupos
for d in (dev, val):
    d["quintil RV"] = pd.cut(d.relationship_value, np.quantile(dev.relationship_value, [0, .2, .4, .6, .8, 1]), labels=["Q1", "Q2", "Q3", "Q4", "Q5"], include_lowest=True)
    d["banda antigüedad"] = pd.cut(d.tenure_years, [0, 3, 7, 15, np.inf], labels=["1–3", "3–7", "7–15", "15+"], right=False)
    d["historia < 24m"] = np.where(d.hist_lt24.astype(bool), "sí", "no")
    d["segmento"] = d.segment
GR = ["segmento", "quintil RV", "banda antigüedad", "historia < 24m", "cluster"]
sub = []
mix = []
for g in GR:
    mix.append({"subgrupo": g, "PSI de la mezcla dev→val": psi_from_labels(dev[g].astype(str), val[g].astype(str))})
    for lv in sorted(dev[g].astype(str).unique()):
        a, b = dev[dev[g].astype(str) == lv], val[val[g].astype(str) == lv]
        if len(b) == 0:
            continue
        sub.append({"subgrupo": g, "nivel": lv, "hogares dev": len(a), "hogares val": len(b), "eventos val": int(b.y_B.sum()),
                    "PSI score": psi_from_labels(dec_labels(dev.score, a.score), dec_labels(dev.score, b.score)),
                    "PSI tramo": psi_from_labels(a.tramo, b.tramo, TR), "score medio dev": a.score.mean(), "score medio val": b.score.mean()})
SUB = pd.DataFrame(sub)
SUB["lectura"] = SUB[["PSI score", "PSI tramo"]].max(axis=1).map(read)
MIX = pd.DataFrame(mix)
save_table(SUB, "step15_psi_subgroups")
save_table(MIX, "step15_psi_mix")

# Deriva de contribuciones entre folds
W = woe_frame(dev, BIN, V)
y, w = dev.y_B.astype(int).to_numpy(), dev.w_B.to_numpy()
contrib = []
for rr in range(1, 6):
    for k in range(5):
        tr = dev[f"cv_r{rr}"].to_numpy() != k
        m = sm.GLM(1 - y[tr], sm.add_constant(W[tr]), family=sm.families.Binomial(), freq_weights=w[tr]).fit()
        c_ = (np.abs(W[tr].to_numpy() * m.params.iloc[1:].to_numpy())).mean(0)
        contrib.append(c_ / c_.sum())
C = np.array(contrib)
DR = pd.DataFrame({"variable": V, "participación media %": 100 * C.mean(0), "sd entre folds (pp)": 100 * C.std(0),
                   "CV %": 100 * C.std(0) / C.mean(0), "mín %": 100 * C.min(0), "máx %": 100 * C.max(0)}).sort_values("participación media %", ascending=False)
DR["orden estable (rango mín–máx del puesto)"] = ""
ranks = (-C).argsort(1).argsort(1) + 1
for i, v in enumerate(V):
    DR.loc[DR.variable == v, "orden estable (rango mín–máx del puesto)"] = f"{ranks[:, i].min()}–{ranks[:, i].max()}"
save_table(DR, "step15_contribution_drift")

rep = f"""# Paso 15 · Estabilidad

## Objetivo
- Verificar que score, probabilidad, tramos y variables no cambian entre desarrollo y validación, ni dentro de los
  subgrupos, y que el peso de cada variable es estable entre folds.

## Método
- PSI = Σ (%val − %dev)·ln(%val/%dev) con bins de dev; lectura < 0.10 estable, 0.10–0.25 vigilar, > 0.25 cambio [DEF SPEC paso 17].
- Subgrupos: segmento, quintil de RV (cortes de dev), antigüedad, historia < 24 meses, cluster.
- Deriva de contribuciones: participación de |β_j·WoE_j| en los 25 entrenamientos de la CV 5×5.
- Sin PSI temporal: un solo snapshot (L1).

## Código
- `src/step15_stability.py` · `tests/test_step15.py` · `step15_*.csv`.

## Resultados

### PSI dev → val [DATA]
{md_table(P1, floatfmt=",.4f")}

### PSI por subgrupo [DATA]
{md_table(SUB, floatfmt=",.4f")}

### PSI de la mezcla de subgrupos [DATA]
{md_table(MIX, floatfmt=",.4f")}

### Deriva de contribuciones entre folds [DATA]
{md_table(DR, floatfmt=",.2f")}

- Verificación: participación media suma {DR['participación media %'].sum():.1f}% [DATA].
- Máx. PSI de subgrupo: {SUB[['PSI score', 'PSI tramo']].max(axis=1).max():.4f} ({SUB.loc[SUB[['PSI score', 'PSI tramo']].max(axis=1).idxmax(), 'subgrupo']} ·
  {SUB.loc[SUB[['PSI score', 'PSI tramo']].max(axis=1).idxmax(), 'nivel']}) [DATA]; subgrupos pequeños tienen PSI más ruidoso.

## Tests
- `tests/test_step15.py` (ver pytest).

## Decisiones y preguntas abiertas
- D15.1 en `reports/decision_log.md`.
"""
(REPORTS / "step15.md").write_text(rep, encoding="utf-8")
print(P1.round(4).to_string(index=False)); print(SUB.round(4).to_string(index=False)); print(MIX.round(4).to_string(index=False)); print(DR.round(2).to_string(index=False))
