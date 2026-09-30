"""Fase 10 · Gate: única apertura del test.

- Guarda: si outputs/p10/decision.json ya existe, el script se niega a correr (el test se abre una sola vez).
- Modelos congelados, entrenados solo con train (fases 7–9): NAM monótono, EBM monótono (champion provisional),
  LightGBM monótono, logística L2, XGBoost, LightGBM (benchmarks sin pesos, re-ajustados con el mismo código y semilla
  de la fase 7); más M1 scorecard y M2 EBM (sus probabilidades publicadas; entrenados en el dev heredado) y A-lite
  congelado (solo en test ∩ holdout de A-lite).
- Gate pre-registrado (fase 6 + enmienda UHNW): NAM vs A-lite, target A, en test ∩ holdout A-lite: ΔPR-AUC ≥ 0.03 y
  Δlift@5% ≥ 0.25 con límite inferior del IC bootstrap pareado 95% (2,000) > 0 en ambas; violaciones = 0; UHNW reportado.
- Además (SPEC fase 10): champion (EBM) vs NAM con IC bootstrap, pooled y UHNW, en todo el test.
"""
from __future__ import annotations

import json
import pickle
import warnings
from datetime import datetime, timezone

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import QuantileTransformer

from config import P, SEED, get, set_seed
from report import render

warnings.filterwarnings("ignore")
out = P.out(10)
if (out / "decision.json").exists():
    raise SystemExit("El test ya fue abierto (outputs/p10/decision.json existe). La fase 10 no se re-ejecuta.")
set_seed()
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A", "y_B"]]
S = pd.read_parquet(P.processed / "splits.parquet")
F = [c for c in X.columns if c != "household_id"]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "probabilidad_lite"]]
m1 = pd.read_csv(P.m1 / "outputs" / "scores" / "household_scores.csv")[["household_id", "probabilidad_calibrada"]].rename(columns={"probabilidad_calibrada": "p_m1"})
m2 = pd.read_csv(P.m2 / "outputs" / "scores" / "household_scores_ml.csv")[["household_id", "p_ebm_calibrada"]].rename(columns={"p_ebm_calibrada": "p_m2"})
D = D.merge(al, on="household_id", how="left").merge(m1, on="household_id", how="left").merge(m2, on="household_id", how="left")
TR, TE = D[D.split == "train"].reset_index(drop=True), D[D.split == "test"].reset_index(drop=True)
opened = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
NAM = pickle.load(open(P.out(9) / "nam_models.pkl", "rb"))["models"]
CH = pickle.load(open(P.out(8) / "models.pkl", "rb"))
rng = np.random.default_rng(SEED)


def lift5(y, p):
    t = np.argsort(-p, kind="stable")[: int(round(0.05 * len(p)))]
    return y[t].mean() / y.mean()


def metrics(y, p):
    return {"AUC": roc_auc_score(y, p), "PR-AUC": average_precision_score(y, p), "lift@5%": lift5(y, p), "Brier": brier_score_loss(y, p)}


def bench(name, Xtr, ytr, Xte):                                   # mismo código y semilla que la fase 7, sin pesos
    if name == "logística L2":
        qt = QuantileTransformer(output_distribution="normal", n_quantiles=1000, random_state=SEED).fit(Xtr)
        m = LogisticRegressionCV(Cs=np.logspace(-3, 1, 12), cv=5, scoring="average_precision", max_iter=5000, random_state=SEED).fit(np.nan_to_num(qt.transform(Xtr)), ytr)
        return m.predict_proba(np.nan_to_num(qt.transform(Xte)))[:, 1]
    a, b, ya, yb = train_test_split(Xtr, ytr, test_size=0.15, stratify=ytr, random_state=SEED)
    if name == "XGBoost":
        m = xgb.XGBClassifier(n_estimators=2000, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=5, tree_method="hist",
                              eval_metric="aucpr", early_stopping_rounds=100, random_state=SEED, n_jobs=4).fit(a, ya, eval_set=[(b, yb)], verbose=False)
        return m.predict_proba(Xte)[:, 1]
    m = lgb.LGBMClassifier(n_estimators=2000, max_depth=3, num_leaves=8, learning_rate=0.05, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, min_child_weight=5,
                           metric="average_precision", random_state=SEED, n_jobs=4, verbose=-1)
    m.fit(a, ya, eval_set=[(b, yb)], callbacks=[lgb.early_stopping(100, first_metric_only=True, verbose=False)])
    return m.predict_proba(Xte)[:, 1]


PRED = {}
for t in ("A", "B"):
    tr = TR[TR[f"y_{t}"].notna()]
    ytr = tr[f"y_{t}"].astype(int).to_numpy()
    te = TE
    PRED[(t, "NAM monótono")] = NAM[t].predict_proba(te[F].to_numpy(float))
    PRED[(t, "EBM monótono (champion)")] = CH[(t, "EBM monótono")].predict_proba(te[F])[:, 1]
    PRED[(t, "LightGBM monótono")] = CH[(t, "LightGBM monótono")].predict_proba(te[F])[:, 1]
    for b in ("logística L2", "XGBoost", "LightGBM"):
        PRED[(t, b)] = bench(b, tr[F], ytr, te[F])
    PRED[(t, "M1 scorecard (target B)")] = te.p_m1.to_numpy()
    PRED[(t, "M2 EBM (target B)")] = te.p_m2.to_numpy()
    PRED[(t, "A-lite (congelado, target A)")] = te.probabilidad_lite.to_numpy()

fair = (TE.split == "test") & TE.test_alite
rows = []
for (t, name), p in PRED.items():
    for sub, mk0 in (("test completo", np.ones(len(TE), bool)), ("test ∩ holdout A-lite", fair.to_numpy())):
        if name.startswith("A-lite") and sub == "test completo":
            continue
        for seg in ("pooled", "HNW", "UHNW"):
            mk = mk0 & TE[f"y_{t}"].notna().to_numpy() & (np.ones(len(TE), bool) if seg == "pooled" else (TE.segment == seg).to_numpy())
            y = TE.loc[mk, f"y_{t}"].astype(int).to_numpy()
            rows.append({"target": t, "subconjunto": sub, "segmento": seg, "modelo": name, "hogares": int(mk.sum()), "eventos": int(y.sum()), **metrics(y, p[mk])})
ALL = pd.DataFrame(rows)


def paired(t, a, b, mk, B):
    y = TE.loc[mk, f"y_{t}"].astype(int).to_numpy()
    pa, pb = PRED[(t, a)][mk], PRED[(t, b)][mk]
    d = []
    for _ in range(B):
        i = rng.choice(len(y), len(y), replace=True)
        if y[i].sum() > 0:
            d.append((average_precision_score(y[i], pa[i]) - average_precision_score(y[i], pb[i]), lift5(y[i], pa[i]) - lift5(y[i], pb[i])))
    d = np.array(d)
    return {"ΔPR-AUC": average_precision_score(y, pa) - average_precision_score(y, pb), "ΔPR-AUC IC95 inf": np.quantile(d[:, 0], .025), "ΔPR-AUC IC95 sup": np.quantile(d[:, 0], .975),
            "Δlift@5%": lift5(y, pa) - lift5(y, pb), "Δlift@5% IC95 inf": np.quantile(d[:, 1], .025), "Δlift@5% IC95 sup": np.quantile(d[:, 1], .975), "eventos": int(y.sum()), "hogares": len(y)}


B = get("gate.bootstrap_reps")
bt = []
for sub, mkf in (("test ∩ holdout A-lite", fair.to_numpy()),):
    for seg in ("pooled", "UHNW"):
        mk = mkf & TE.y_A.notna().to_numpy() & (np.ones(len(TE), bool) if seg == "pooled" else (TE.segment == "UHNW").to_numpy())
        bt.append({"comparación": "NAM − A-lite", "target": "A", "subconjunto": sub, "segmento": seg, **paired("A", "NAM monótono", "A-lite (congelado, target A)", mk, B)})
for t in ("A", "B"):
    for seg in ("pooled", "UHNW"):
        mk = TE[f"y_{t}"].notna().to_numpy() & (np.ones(len(TE), bool) if seg == "pooled" else (TE.segment == "UHNW").to_numpy())
        bt.append({"comparación": "NAM − EBM (champion)", "target": t, "subconjunto": "test completo", "segmento": seg, **paired(t, "NAM monótono", "EBM monótono (champion)", mk, B)})
BT = pd.DataFrame(bt)

g = BT[(BT["comparación"] == "NAM − A-lite") & (BT.segmento == "pooled")].iloc[0]
viol = json.load(open(P.out(9) / "summary.json"))["violaciones totales en variables duras"]
crit = {"ΔPR-AUC ≥ 0.03": bool(g["ΔPR-AUC"] >= get("gate.delta_pr_auc")), "IC95 ΔPR-AUC inf > 0": bool(g["ΔPR-AUC IC95 inf"] > 0),
        "Δlift@5% ≥ 0.25": bool(g["Δlift@5%"] >= get("gate.delta_lift_at_5")), "IC95 Δlift@5% inf > 0": bool(g["Δlift@5% IC95 inf"] > 0), "violaciones de monotonía = 0": viol == 0}
u = BT[(BT["comparación"] == "NAM − A-lite") & (BT.segmento == "UHNW")].iloc[0]
DEC = {"test abierto (UTC)": opened, "gate": "NAM vs A-lite · target A · test ∩ holdout A-lite", "hogares": int(g.hogares), "eventos A": int(g.eventos),
       "ΔPR-AUC": float(g["ΔPR-AUC"]), "ΔPR-AUC IC95": [float(g["ΔPR-AUC IC95 inf"]), float(g["ΔPR-AUC IC95 sup"])],
       "Δlift@5%": float(g["Δlift@5%"]), "Δlift@5% IC95": [float(g["Δlift@5% IC95 inf"]), float(g["Δlift@5% IC95 sup"])], "criterios": crit,
       "UHNW (solo reportado)": {"eventos": int(u.eventos), "ΔPR-AUC": float(u["ΔPR-AUC"]), "IC95": [float(u["ΔPR-AUC IC95 inf"]), float(u["ΔPR-AUC IC95 sup"])]},
       "decisión": "NAM reemplaza a A-lite" if all(crit.values()) else "NAM no reemplaza a A-lite: queda documentado como challenger",
       "nota": "NAM sin convergencia completa (8 de 10 miembros en epochs_max); decisión del usuario (c): ir al gate con el NAM actual"}
ALL.to_csv(out / "test_metrics_all.csv", index=False)
BT.to_csv(out / "gate_bootstrap.csv", index=False)
json.dump(DEC, open(out / "decision.json", "w"), ensure_ascii=False, indent=1)
json.dump({"title": "Fase 10 · Gate (única apertura del test)", "order": ["decision.json", "gate_bootstrap.csv", "test_metrics_all.csv"],
           "notes": {"test_metrics_all.csv": "Todos los modelos entrenados solo con train (M1/M2: dev heredado); A-lite solo en test ∩ holdout de A-lite."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(10)
print(json.dumps(DEC, ensure_ascii=False, indent=1)); print(BT.round(4).to_string(index=False))
v = ALL[(ALL.segmento == "pooled")].pivot_table(index="modelo", columns=["target", "subconjunto"], values="PR-AUC")
print(v.round(3).to_string())
