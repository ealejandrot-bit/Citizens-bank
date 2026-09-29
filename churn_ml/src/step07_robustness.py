"""Paso 7 · Robustez en dev (EBM principal; XGBoost y M1 como referencia). Target B.

- Estabilidad de importancias: EBM re-ajustado en los 25 entrenamientos de la CV 5×5; participación de |f_j| por
  variable (media, sd, rango del puesto).
- Sensibilidad a quitar la variable principal: PR-AUC CV 5×5 del EBM sin ella vs con ella (pareado por fold).
- Desempeño OOF por subgrupo (segmento, quintil de RV, antigüedad, historia < 24 meses, cluster): EBM y XGBoost con OOF
  promediado 5×5 (paso 5); M1 con su OOF de r1 (heredado).
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from common import INH, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
S = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
V = S["vars"]
MONO = [{"+": 1, "−": -1}.get(S["signs"][c], 0) for c in V]
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
CV = {r: D[f"cv_r{r}"].to_numpy() for r in range(1, 6)}


def ebm(cols):
    return ExplainableBoostingClassifier(monotone_constraints=[MONO[V.index(c)] for c in cols], interactions=0, random_state=SEED, n_jobs=4)


shares, pr_full, pr_drop = [], [], []
TOP = None
for r, k in FOLDS:
    tr, te = CV[r] != k, CV[r] == k
    e = ebm(V).fit(D.loc[tr, V], y[tr])
    c = np.abs(e.eval_terms(D.loc[tr, V])).mean(0)
    shares.append(c / c.sum())
    pr_full.append(average_precision_score(y[te], e.predict_proba(D.loc[te, V])[:, 1]))
SH = np.array(shares)
ranks = (-SH).argsort(1).argsort(1) + 1
ST = pd.DataFrame({"variable": V, "participación media %": 100 * SH.mean(0), "sd (pp)": 100 * SH.std(0), "CV %": 100 * SH.std(0) / SH.mean(0),
                   "puesto mín–máx": [f"{ranks[:, j].min()}–{ranks[:, j].max()}" for j in range(len(V))]}).sort_values("participación media %", ascending=False)
save_table(ST, "step07_importance_stability")
TOP = ST.variable.iloc[0]
V2 = [c for c in V if c != TOP]
for r, k in FOLDS:
    tr, te = CV[r] != k, CV[r] == k
    pr_drop.append(average_precision_score(y[te], ebm(V2).fit(D.loc[tr, V2], y[tr]).predict_proba(D.loc[te, V2])[:, 1]))
pf, pd_ = np.array(pr_full), np.array(pr_drop)
SENS = pd.DataFrame([{"variante": "EBM completo", "PR-AUC CV": pf.mean(), "sd": pf.std(ddof=1)},
                     {"variante": f"EBM sin {TOP}", "PR-AUC CV": pd_.mean(), "sd": pd_.std(ddof=1), "Δ pareado": (pd_ - pf).mean(),
                      "% folds peor": 100 * (pd_ < pf).mean()}])
save_table(SENS, "step07_drop_top")

# Subgrupos (OOF)
O = pd.read_parquet(PROC / "step05_oof.parquet").set_index("household_id").loc[D.household_id]
m1 = pd.read_parquet(INH / "m1_champion_oof_r1.parquet").set_index("household_id").loc[D.household_id, "p_champion_oof_r1"].to_numpy()
P = {"EBM": O.p_oof_ebm.to_numpy(), "XGBoost": O.p_oof_xgb.to_numpy(), "M1 (OOF r1)": m1}
D["quintil RV"] = pd.qcut(D.relationship_value, 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
D["antigüedad"] = pd.cut(D.tenure_years, [0, 3, 7, 15, np.inf], labels=["1–3", "3–7", "7–15", "15+"], right=False)
D["historia < 24m"] = np.where(D.hist_lt24.astype(bool), "sí", "no")
rows = []
for g in ["segment", "quintil RV", "antigüedad", "historia < 24m", "cluster"]:
    for lv in sorted(D[g].astype(str).unique()):
        m = (D[g].astype(str) == lv).to_numpy()
        if y[m].sum() < 30:
            continue
        row = {"subgrupo": g, "nivel": lv, "hogares": int(m.sum()), "eventos": int(y[m].sum()), "tasa %": 100 * y[m].mean()}
        for n_, p in P.items():
            row[f"AUC {n_}"] = roc_auc_score(y[m], p[m])
            row[f"PR-AUC {n_}"] = average_precision_score(y[m], p[m])
            row[f"p media % {n_}"] = 100 * p[m].mean()
        rows.append(row)
SUB = pd.DataFrame(rows)
SUB["ΔAUC EBM − M1"] = SUB["AUC EBM"] - SUB["AUC M1 (OOF r1)"]
save_table(SUB, "step07_subgroups")

rep = f"""# Paso 7 · Robustez en dev

## Objetivo
- Verificar que el EBM no depende de una sola variable ni de un subgrupo, y que su peso por variable es estable.

## Método
- EBM re-ajustado en los 25 entrenamientos de la CV 5×5: participación de |f_j|; sensibilidad a quitar la variable
  principal (PR-AUC pareado); desempeño OOF por subgrupo (≥ 30 eventos) frente a XGBoost y M1.

## Código
- `src/step07_robustness.py` · `tests/test_step07.py` · `step07_*.csv`.

## Resultados

### Estabilidad de importancias (25 folds) [DATA]
{md_table(ST, floatfmt=",.2f")}

- Verificación: participación media suma {ST['participación media %'].sum():.1f}% [DATA].

### Sensibilidad a quitar la variable principal [DATA]
{md_table(SENS, floatfmt=",.4f")}

### Desempeño por subgrupo (OOF) [DATA]
{md_table(SUB, floatfmt=",.3f")}

- EBM supera o iguala al M1 en AUC en {int((SUB['ΔAUC EBM − M1'] >= 0).sum())} de {len(SUB)} subgrupos [DATA]; el OOF de M1 es solo de r1 (menos estable).

## Tests
- `tests/test_step07.py` (ver pytest).

## Decisiones y preguntas abiertas
- D7.1 en `reports/decision_log.md`.
"""
(REPORTS / "step07.md").write_text(rep, encoding="utf-8")
print(ST.round(2).to_string(index=False)); print(SENS.round(4).to_string(index=False)); print(SUB[["subgrupo", "nivel", "eventos", "AUC EBM", "AUC XGBoost", "AUC M1 (OOF r1)", "p media % EBM", "tasa %"]].round(3).to_string(index=False))
