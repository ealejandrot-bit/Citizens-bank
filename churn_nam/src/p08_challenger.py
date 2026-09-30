"""Fase 8 · Challenger interpretable: LightGBM monótono vs EBM monótono (aditivo, sin interacciones), en validación.

- Mismas 58 features y el mapa de signos confirmado (fase 4): +1 / −1 duras, 0 libres. Sin pesos de clase (fase 7).
- LightGBM: mismos hiperparámetros fijos que el benchmark de la fase 7 + monotone_constraints; early stopping interno.
- EBM: interpret-core, interactions = 0, monotone_constraints; parámetros por defecto.
- Violaciones de monotonía: ICE (500 hogares × 21 puntos) y PDP por variable dura, en ambos.
- Regla de champion fijada antes de ver resultados (D8.1): mayor PR-AUC (target A, validación); si |Δ| < 1 sd bootstrap
  pareada (1,000 réplicas), gana EBM por ser aditivo (misma estructura que A-lite/scorecard y NAM).
- A-lite congelado como referencia en validación ∩ holdout de A-lite.
"""
from __future__ import annotations

import json
import pickle
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from config import P, SEED, set_seed
from report import render

warnings.filterwarnings("ignore")
set_seed()
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A", "y_B"]]
S = pd.read_parquet(P.processed / "splits.parquet")
MAP = json.load(open(P.out(4) / "monotonicity_map.json"))
F = [c for c in X.columns if c != "household_id"]
MONO = [{"+": 1, "−": -1}.get(MAP[c]["signo"], 0) for c in F]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "probabilidad_lite"]]
alh = pd.read_csv(P.alite / "outputs" / "tables" / "04_split.csv")[["household_id", "muestra"]]
D = D.merge(al, on="household_id", how="left").merge(alh, on="household_id", how="left")
TR, VA = D[D.split == "train"].reset_index(drop=True), D[D.split == "validation"].reset_index(drop=True)
rng = np.random.default_rng(SEED)


def lift5(y, p):
    t = np.argsort(-p, kind="stable")[: int(round(0.05 * len(p)))]
    return y[t].mean() / y.mean()


def metrics(y, p):
    return {"AUC": roc_auc_score(y, p), "PR-AUC": average_precision_score(y, p), "lift@5%": lift5(y, p), "Brier": brier_score_loss(y, p)}


def fit_lgbm(Xtr, ytr):
    a, b, ya, yb = train_test_split(Xtr, ytr, test_size=0.15, stratify=ytr, random_state=SEED)
    m = lgb.LGBMClassifier(n_estimators=2000, max_depth=3, num_leaves=8, learning_rate=0.05, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                           min_child_weight=5, monotone_constraints=MONO, metric="average_precision", random_state=SEED, n_jobs=4, verbose=-1)
    return m.fit(a, ya, eval_set=[(b, yb)], callbacks=[lgb.early_stopping(100, first_metric_only=True, verbose=False)])


def fit_ebm(Xtr, ytr):
    return ExplainableBoostingClassifier(monotone_constraints=MONO, interactions=0, random_state=SEED, n_jobs=4).fit(Xtr, ytr)


def violations(model, Xref):
    idx = rng.choice(len(Xref), 500, replace=False)
    tot_ice = tot_pdp = 0
    for j, c in enumerate(F):
        if MONO[j] == 0:
            continue
        grid = np.unique(np.nanquantile(Xref[c].astype(float), np.linspace(0, 1, 21)))
        Xi = Xref.iloc[idx].copy()
        outp = []
        for g in grid:
            Xi[c] = g
            outp.append(model.predict_proba(Xi)[:, 1])
        outp = np.log(np.clip(np.array(outp).T, 1e-9, 1 - 1e-9))
        d = np.diff(outp, axis=1) * MONO[j]
        tot_ice += int((d < -1e-7).sum())
        tot_pdp += int((np.diff(outp.mean(0)) * MONO[j] < -1e-7).sum())
    return tot_ice, tot_pdp


rows, P_ = [], {}
MODELS = {}
for t in ("A", "B"):
    tr, va = TR[TR[f"y_{t}"].notna()], VA[VA[f"y_{t}"].notna()].reset_index(drop=True)
    ytr, yva = tr[f"y_{t}"].astype(int).to_numpy(), va[f"y_{t}"].astype(int).to_numpy()
    for name, fit in (("LightGBM monótono", fit_lgbm), ("EBM monótono", fit_ebm)):
        m = fit(tr[F], ytr)
        MODELS[(t, name)] = m
        p = m.predict_proba(va[F])[:, 1]
        P_[(t, name)] = pd.Series(p, index=va.household_id)
        vi, vp = violations(m, tr[F]) if t == "A" else (np.nan, np.nan)
        for seg in ("pooled", "HNW", "UHNW"):
            mk = np.ones(len(va), bool) if seg == "pooled" else (va.segment == seg).to_numpy()
            rows.append({"target": t, "modelo": name, "segmento": seg, "hogares": int(mk.sum()), "eventos": int(yva[mk].sum()), **metrics(yva[mk], p[mk]),
                         "violaciones ICE": vi if seg == "pooled" else np.nan, "violaciones PDP": vp if seg == "pooled" else np.nan,
                         "árboles / términos": (int(m.best_iteration_) if isinstance(m, lgb.LGBMClassifier) else len(m.term_names_)) if seg == "pooled" else np.nan})
CMP = pd.DataFrame(rows)

# Regla de champion (target A) con bootstrap pareado
va = VA[VA.y_A.notna()].reset_index(drop=True)
y = va.y_A.astype(int).to_numpy()
pl, pe = P_[("A", "LightGBM monótono")].to_numpy(), P_[("A", "EBM monótono")].to_numpy()
d = []
for _ in range(1000):
    i = rng.choice(len(y), len(y), replace=True)
    d.append((average_precision_score(y[i], pl[i]) - average_precision_score(y[i], pe[i]), lift5(y[i], pl[i]) - lift5(y[i], pe[i])))
d = np.array(d)
dpr = average_precision_score(y, pl) - average_precision_score(y, pe)
sd = d[:, 0].std(ddof=1)
champ = ("LightGBM monótono" if dpr > 0 else "EBM monótono") if abs(dpr) >= sd else "EBM monótono"
DEC = {"regla (D8.1)": "mayor PR-AUC (A, validación); si |Δ| < 1 sd bootstrap pareada ⟹ EBM (aditivo)", "ΔPR-AUC LightGBM − EBM": dpr, "sd bootstrap": sd,
       "IC95 ΔPR-AUC": [float(np.quantile(d[:, 0], .025)), float(np.quantile(d[:, 0], .975))],
       "Δlift@5% LightGBM − EBM": lift5(y, pl) - lift5(y, pe), "IC95 Δlift@5%": [float(np.quantile(d[:, 1], .025)), float(np.quantile(d[:, 1], .975))],
       "champion provisional": champ, "test abierto": False}

# Referencia A-lite en el subconjunto justo
ref = []
for t in ("A", "B"):
    v = VA[VA[f"y_{t}"].notna() & (VA.muestra == "holdout")].reset_index(drop=True)
    yy = v[f"y_{t}"].astype(int).to_numpy()
    ref.append({"target": t, "modelo": "A-lite (congelado)", "hogares": len(v), "eventos": int(yy.sum()), **metrics(yy, v.probabilidad_lite.to_numpy())})
    for name in ("LightGBM monótono", "EBM monótono"):
        ref.append({"target": t, "modelo": name, "hogares": len(v), "eventos": int(yy.sum()), **metrics(yy, P_[(t, name)].loc[v.household_id].to_numpy())})
REF = pd.DataFrame(ref)
out = P.out(8)
CMP.to_csv(out / "challenger_validation.csv", index=False)
REF.to_csv(out / "alite_fair_validation.csv", index=False)
json.dump(DEC, open(out / "champion_decision.json", "w"), ensure_ascii=False, indent=1)
with open(out / "models.pkl", "wb") as fh:
    pickle.dump({k: v for k, v in MODELS.items()}, fh)
json.dump({"title": "Fase 8 · Challenger interpretable (validación)", "order": ["champion_decision.json", "challenger_validation.csv", "alite_fair_validation.csv"],
           "notes": {"champion_decision.json": "Regla fijada antes de ver resultados; test sin abrir."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
render(8)
print(json.dumps(DEC, ensure_ascii=False, indent=1)); print(CMP.round(4).to_string(index=False)); print(REF.round(4).to_string(index=False))
