"""Paso 9b · Comparativa con A-lite (pedido del usuario en G3): scorecard ejecutivo de 5 variables del Modelo 1 previo
(`scorecard/`, target hard_churn_6m, split propio). No se re-ajusta: se usan sus scores ya asignados (copia con sha256).

- A-lite se desarrolló con otro split: 4,042 de los 5,779 hogares B de nuestro val estaban en su desarrollo. Comparación
  justa = los hogares fuera del desarrollo de TODOS los modelos (val ∩ holdout de scorecard/). También se muestra el val
  completo, marcado como favorable a A-lite.
- Dos targets: B (el de M1 y ML) y A = hard_churn_6m (el de A-lite). Orden (AUC, Gini, PR-AUC, KS, Precision@K, captura
  de RV) con los dos; calibración (Brier, b) solo donde el modelo fue calibrado para ese target.
- ΔPR-AUC y ΔGini pareados con IC bootstrap 95% (1,000) sobre el subconjunto justo.
"""
from __future__ import annotations

import hashlib
import shutil

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from common import ID, INH, REPORTS, ROOT, SCORES, SEED, md_table, save_table, set_seed

set_seed()
SRC = ROOT.parent / "scorecard" / "outputs"
COPIES = {"scored/scored_households.csv": "alite_scored_households.csv", "tables/04_split.csv": "alite_split.csv",
          "tables/11_modelAlite_coefficients.csv": "alite_coefficients.csv"}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
for s_, d_ in COPIES.items():
    shutil.copy2(SRC / s_, INH / d_)
    assert sha(SRC / s_) == sha(INH / d_)

A = pd.read_csv(INH / "alite_scored_households.csv")[[ID, "score_lite", "probabilidad_lite", "tramo_lite"]]
SPL = pd.read_csv(INH / "alite_split.csv")[[ID, "muestra"]].rename(columns={"muestra": "muestra A-lite"})
COEF = pd.read_csv(INH / "alite_coefficients.csv")
O = pd.read_csv(SCORES / "household_scores_ml.csv")
pop = pd.read_parquet(INH / "step01_population.parquet")[[ID, "in_pop_A", "in_pop_B", "y_A", "y_B"]]
F = pd.read_parquet(INH / "features.parquet")[[ID, "relationship_value"]]
O = O.merge(pop, on=ID).merge(F, on=ID).merge(A, on=ID, how="left").merge(SPL, on=ID, how="left")
val = O[O["partición"] == "val"].reset_index(drop=True)
assert val.probabilidad_lite.notna().all()
MODS = {"A-lite (5 variables)": "probabilidad_lite", "M1 · scorecard (8 variables)": "p_m1_calibrada", "EBM (12 variables)": "p_ebm_calibrada",
        "XGBoost (retirado, referencia)": "p_xgb_calibrada"}
CALIB = {"A-lite (5 variables)": "A", "M1 · scorecard (8 variables)": "B", "EBM (12 variables)": "B", "XGBoost (retirado, referencia)": "B"}


def ks(y, p):
    o = np.argsort(-p)
    return float(np.max(np.abs(np.cumsum(y[o]) / y.sum() - np.cumsum(1 - y[o]) / (1 - y).sum())))


def slope(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(sm.GLM(y, sm.add_constant(np.log(p / (1 - p))), family=sm.families.Binomial()).fit().params[1])


def metrics(d, pcol, t, calibrated):
    y, p, rv = d[f"y_{t}"].astype(int).to_numpy(), d[pcol].to_numpy(), d.relationship_value.to_numpy()
    a = roc_auc_score(y, p)
    o = np.argsort(-p, kind="stable")
    r = {"hogares": len(d), "eventos": int(y.sum()), "AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(y, p), "KS": ks(y, p)}
    for k in (1, 5, 10):
        top = o[: int(round(len(d) * k / 100))]
        r[f"Precision@{k}% %"] = 100 * y[top].mean()
    top = o[: int(round(len(d) * 0.10))]
    r["captura RV eventos top 10% %"] = 100 * (rv * y)[top].sum() / (rv * y).sum()
    r["Brier"] = brier_score_loss(y, p) if calibrated else np.nan
    r["pendiente b"] = slope(y, p) if calibrated else np.nan
    return r


SUBSETS = {"justo: fuera del desarrollo de todos (val ∩ holdout de A-lite)": val["muestra A-lite"] == "holdout",
           "val completo (70% en desarrollo de A-lite: favorable a A-lite)": pd.Series(True, index=val.index)}
rows = []
for sname, sm_ in SUBSETS.items():
    for t in ("B", "A"):
        d = val[sm_ & val[f"in_pop_{t}"].astype(bool)].reset_index(drop=True)
        for m, pc in MODS.items():
            rows.append({"subconjunto": sname, "target": {"B": "B (hard ∪ soft ≥ 25%)", "A": "A (hard churn 6M)"}[t], "modelo": m, **metrics(d, pc, t, CALIB[m] == t)})
CMP = pd.DataFrame(rows)
save_table(CMP, "step09b_alite_comparison")

# Bootstrap pareado en el subconjunto justo
rng = np.random.default_rng(SEED)
BS = []
for t in ("B", "A"):
    d = val[(val["muestra A-lite"] == "holdout") & val[f"in_pop_{t}"].astype(bool)].reset_index(drop=True)
    y = d[f"y_{t}"].astype(int).to_numpy()
    P = {m: d[pc].to_numpy() for m, pc in MODS.items()}
    pairs = [("EBM (12 variables)", "A-lite (5 variables)"), ("M1 · scorecard (8 variables)", "A-lite (5 variables)"), ("EBM (12 variables)", "M1 · scorecard (8 variables)")]
    acc = {pr: [] for pr in pairs}
    for _ in range(1000):
        i = rng.choice(len(y), len(y), replace=True)
        for a_, b_ in pairs:
            acc[(a_, b_)].append((2 * (roc_auc_score(y[i], P[a_][i]) - roc_auc_score(y[i], P[b_][i])), average_precision_score(y[i], P[a_][i]) - average_precision_score(y[i], P[b_][i])))
    for (a_, b_), v in acc.items():
        v = np.array(v)
        BS.append({"target": t, "comparación": f"{a_} − {b_}", "ΔGini": 2 * (roc_auc_score(y, P[a_]) - roc_auc_score(y, P[b_])),
                   "ΔGini IC95": f"[{np.quantile(v[:, 0], .025):+.3f}, {np.quantile(v[:, 0], .975):+.3f}]",
                   "ΔPR-AUC": average_precision_score(y, P[a_]) - average_precision_score(y, P[b_]),
                   "ΔPR-AUC IC95": f"[{np.quantile(v[:, 1], .025):+.3f}, {np.quantile(v[:, 1], .975):+.3f}]", "% réplicas ΔPR-AUC > 0": 100 * (v[:, 1] > 0).mean()})
BS = pd.DataFrame(BS)
save_table(BS, "step09b_alite_bootstrap")

# Tramos de A-lite vs los demás en el subconjunto justo (target B)
d = val[(val["muestra A-lite"] == "holdout") & val.in_pop_B.astype(bool)]
TT = []
for m, col in (("A-lite", "tramo_lite"), ("M1", "tramo_m1"), ("EBM", "tramo_ebm")):
    for t in ["Crítico", "Alto", "Vigilancia", "Estable"]:
        g = d[d[col] == t]
        TT.append({"modelo": m, "tramo": t, "% hogares": 100 * len(g) / len(d), "eventos B": int(g.y_B.sum()), "tasa B %": 100 * g.y_B.mean() if len(g) else np.nan,
                   "tasa A %": 100 * g.loc[g.in_pop_A.astype(bool), "y_A"].mean() if len(g) else np.nan})
TT = pd.DataFrame(TT)
save_table(TT, "step09b_alite_tramos")
VARS = pd.DataFrame({"modelo": ["A-lite", "M1 · scorecard", "EBM"], "variables": [len(COEF) - 1, 8, 12],
                     "detalle": [", ".join(COEF.variable.iloc[1:]), "ver churn_scorecard/reports/step11.md", "ver reports/step02.md"],
                     "target de desarrollo": ["A (hard churn 6M)", "B", "B"], "forma": ["puntos por bin (logística WoE)", "puntos por bin (logística WoE)", "puntos por bin (EBM aditivo)"]})
save_table(VARS, "step09b_models")

fair = CMP[CMP.subconjunto.str.startswith("justo")]
rep = f"""# Paso 9b · Comparativa con A-lite

## Objetivo
- Poner el scorecard ejecutivo A-lite (5 variables) en la misma comparación que el M1 y el EBM, sin re-ajustarlo.

## Método
- Scores de A-lite ya asignados en `scorecard/` (copiados con sha256; nada se modifica). A-lite usó otro split: la
  comparación justa es el subconjunto de val fuera del desarrollo de todos los modelos (D9b.1); el val completo se
  muestra como referencia favorable a A-lite.
- Targets B y A; calibración solo para el target con que se calibró cada modelo. Bootstrap pareado (1,000).

## Código
- `src/step09b_alite.py` · `tests/test_step09b.py` · `step09b_*.csv`.

## Resultados

### Modelos comparados
{md_table(VARS)}

### Subconjunto justo (fuera del desarrollo de todos) [DATA]
{md_table(fair.drop(columns='subconjunto'), floatfmt=",.3f")}

### Diferencias pareadas (subconjunto justo) [DATA]
{md_table(BS, floatfmt=",.3f")}

### Tramos en el subconjunto justo [DATA]
{md_table(TT, floatfmt=",.2f")}

- Verificación: % hogares suma 100% por modelo [DATA]. A-lite define Crítico como top 3% (Modelo 1 previo).

### Val completo (referencia; favorable a A-lite) [DATA]
{md_table(CMP[~CMP.subconjunto.str.startswith('justo')].drop(columns='subconjunto'), floatfmt=",.3f")}

## Tests
- `tests/test_step09b.py` (ver pytest).

## Decisiones y preguntas abiertas
- D9b.1 en `reports/decision_log.md`.
"""
(REPORTS / "step09b.md").write_text(rep, encoding="utf-8")
print(fair.drop(columns="subconjunto").round(3).to_string(index=False)); print(BS.round(3).to_string(index=False)); print(TT.round(2).to_string(index=False))
