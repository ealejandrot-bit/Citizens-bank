"""Fase 7 · Benchmarks en validación (el test no se abre). Targets A (principal) y B.

Modelos (entrenados en train, sin monotonía, sin tuning pesado; hiperparámetros fijos declarados):
  - Logística L2: entradas por cuantiles → normal (ajustado en train), NaN → 0 (centro) con los indicadores ya
    existentes (has_* para estructurales, miss_* para "sin regla"; "ruido" sin indicador, decisión fase 2); C por CV 5 en train.
  - XGBoost y LightGBM: NaN nativo, profundidad 3, lr 0.05, early stopping en un 15% interno del train (no en validación).
  - Con y sin pesos de clase (balanced / scale_pos_weight = n0/n1).
Métricas en validación: AUC, PR-AUC, lift@5%, Brier (probabilidad sin calibrar); pooled / HNW / UHNW; IC bootstrap 95%
(1,000) de PR-AUC y lift@5% pooled. Referencia: A-lite congelado en validación ∩ holdout de A-lite (subconjunto justo).
"""
from __future__ import annotations

import json
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import QuantileTransformer

from config import P, SEED, set_seed
from report import render

warnings.filterwarnings("ignore")
set_seed()
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A", "y_B"]]
S = pd.read_parquet(P.processed / "splits.parquet")
D = X.merge(pop, on="household_id").merge(S, on="household_id")
F = [c for c in X.columns if c != "household_id"]
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


def boot(y, p, B=1000):
    v = []
    for _ in range(B):
        i = rng.choice(len(y), len(y), replace=True)
        if y[i].sum() > 0:
            v.append((average_precision_score(y[i], p[i]), lift5(y[i], p[i])))
    v = np.array(v)
    return np.quantile(v, [0.025, 0.975], axis=0)


def fit_predict(name, weighted, Xtr, ytr, Xva):
    spw = (ytr == 0).sum() / ytr.sum()
    if name == "logística L2":
        qt = QuantileTransformer(output_distribution="normal", n_quantiles=1000, random_state=SEED).fit(Xtr)
        Ztr, Zva = np.nan_to_num(qt.transform(Xtr)), np.nan_to_num(qt.transform(Xva))
        m = LogisticRegressionCV(Cs=np.logspace(-3, 1, 12), cv=5, scoring="average_precision", class_weight="balanced" if weighted else None,
                                 max_iter=5000, random_state=SEED).fit(Ztr, ytr)
        return m.predict_proba(Zva)[:, 1]
    a, b, ya, yb = train_test_split(Xtr, ytr, test_size=0.15, stratify=ytr, random_state=SEED)
    if name == "XGBoost":
        m = xgb.XGBClassifier(n_estimators=2000, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=5, tree_method="hist",
                              scale_pos_weight=spw if weighted else 1.0, eval_metric="aucpr", early_stopping_rounds=100, random_state=SEED, n_jobs=4)
        m.fit(a, ya, eval_set=[(b, yb)], verbose=False)
        return m.predict_proba(Xva)[:, 1]
    m = lgb.LGBMClassifier(n_estimators=2000, max_depth=3, num_leaves=8, learning_rate=0.05, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
                           min_child_weight=5, scale_pos_weight=spw if weighted else 1.0, metric="average_precision", random_state=SEED, n_jobs=4, verbose=-1)
    m.fit(a, ya, eval_set=[(b, yb)], callbacks=[lgb.early_stopping(100, first_metric_only=True, verbose=False)])
    return m.predict_proba(Xva)[:, 1]


rows, preds = [], {}
for t in ("A", "B"):
    tr, va = TR[TR[f"y_{t}"].notna()], VA[VA[f"y_{t}"].notna()].reset_index(drop=True)
    ytr, yva = tr[f"y_{t}"].astype(int).to_numpy(), va[f"y_{t}"].astype(int).to_numpy()
    for name in ("logística L2", "XGBoost", "LightGBM"):
        for w in (False, True):
            p = fit_predict(name, w, tr[F], ytr, va[F])
            preds[(t, name, w)] = pd.Series(p, index=va.household_id)
            ci = boot(yva, p)
            for seg in ("pooled", "HNW", "UHNW"):
                m = np.ones(len(va), bool) if seg == "pooled" else (va.segment == seg).to_numpy()
                r = {"target": t, "modelo": name, "pesos de clase": "balanced" if w else "ninguno", "segmento": seg, "hogares": int(m.sum()), "eventos": int(yva[m].sum()),
                     **metrics(yva[m], p[m])}
                if seg == "pooled":
                    r.update({"PR-AUC IC95": f"[{ci[0, 0]:.3f}, {ci[1, 0]:.3f}]", "lift@5% IC95": f"[{ci[0, 1]:.2f}, {ci[1, 1]:.2f}]"})
                rows.append(r)
BM = pd.DataFrame(rows)

# Referencia A-lite y los benchmarks en el subconjunto justo de validación (fuera del desarrollo de A-lite)
ref = []
for t in ("A", "B"):
    va = VA[VA[f"y_{t}"].notna() & (VA.muestra == "holdout")].reset_index(drop=True)
    y = va[f"y_{t}"].astype(int).to_numpy()
    ref.append({"target": t, "modelo": "A-lite (congelado)", "pesos de clase": "—", "hogares": len(va), "eventos": int(y.sum()), **metrics(y, va.probabilidad_lite.to_numpy())})
    for (tt, name, w), s in preds.items():
        if tt == t:
            ref.append({"target": t, "modelo": name, "pesos de clase": "balanced" if w else "ninguno", "hogares": len(va), "eventos": int(y.sum()),
                        **metrics(y, s.loc[va.household_id].to_numpy())})
REF = pd.DataFrame(ref)
out = P.out(7)
BM.to_csv(out / "benchmarks_validation.csv", index=False)
REF.to_csv(out / "alite_fair_validation.csv", index=False)
best = BM[(BM.segmento == "pooled") & (BM.target == "A")].sort_values("PR-AUC", ascending=False).iloc[0]
SUM = {"hogares train / validación": f"{len(TR):,} / {len(VA):,}", "eventos A validación": int(VA.y_A.sum()), "features": len(F),
       "mejor benchmark target A (PR-AUC pooled)": f"{best.modelo} · {best['pesos de clase']} · {best['PR-AUC']:.3f}",
       "hogares en validación ∩ holdout A-lite": int(REF.hogares.iloc[0]), "eventos A en ese subconjunto": int(REF.eventos.iloc[0]), "test abierto": False}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 7 · Benchmarks (validación)", "order": ["summary.json", "benchmarks_validation.csv", "alite_fair_validation.csv"],
           "notes": {"benchmarks_validation.csv": "Brier con probabilidad sin calibrar: con pesos balanced la probabilidad está inflada por construcción (se calibra en la fase 11).",
                     "alite_fair_validation.csv": "Mismos hogares para todos: validación fuera del desarrollo de A-lite."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
render(7)
print(SUM); print(BM[BM.segmento == "pooled"].round(4).to_string(index=False)); print(BM[BM.segmento != "pooled"][["target", "modelo", "pesos de clase", "segmento", "eventos", "AUC", "PR-AUC", "lift@5%"]].round(3).to_string(index=False)); print(REF.round(4).to_string(index=False))
