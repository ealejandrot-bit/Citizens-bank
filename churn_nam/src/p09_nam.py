"""Fase 9 · NAM monótono (src/nam/): entrenamiento en train, métricas en validación (el test no se abre).

- Mismas 58 features y signos confirmados; sin pesos de clase; parámetros de config.nam; ensamble de N semillas.
- Monotonía: violaciones en las funciones de forma (grilla de 201 puntos por miembro y ensamble) y por ICE sobre el
  modelo completo; tests/test_monotone.py las verifica = 0 en las variables duras.
- Curva de entrenamiento (pérdida train y early-stop por época) y funciones de forma de las 12 variables de mayor peso.
- Comparación en validación con el champion provisional (EBM monótono, fase 8) y con A-lite en el subconjunto justo.
"""
from __future__ import annotations

import json
import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from config import P, SEED, need, set_seed
from nam import NAMEnsemble
from report import render

warnings.filterwarnings("ignore")
set_seed()
cfg = {k: need(f"nam.{k}", fase=9) for k in ("hidden_units", "epochs_max", "learning_rate", "weight_decay", "dropout", "ensemble_members", "batch_size", "patience")}
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A", "y_B"]]
S = pd.read_parquet(P.processed / "splits.parquet")
MAP = json.load(open(P.out(4) / "monotonicity_map.json"))
F = [c for c in X.columns if c != "household_id"]
SIGNS = [{"+": 1, "−": -1}.get(MAP[c]["signo"], 0) for c in F]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "probabilidad_lite"]]
alh = pd.read_csv(P.alite / "outputs" / "tables" / "04_split.csv")[["household_id", "muestra"]]
D = D.merge(al, on="household_id", how="left").merge(alh, on="household_id", how="left")
TR, VA = D[D.split == "train"].reset_index(drop=True), D[D.split == "validation"].reset_index(drop=True)
EBM = pickle.load(open(P.out(8) / "models.pkl", "rb"))
out = P.out(9)


def lift5(y, p):
    t = np.argsort(-p, kind="stable")[: int(round(0.05 * len(p)))]
    return y[t].mean() / y.mean()


def metrics(y, p):
    return {"AUC": roc_auc_score(y, p), "PR-AUC": average_precision_score(y, p), "lift@5%": lift5(y, p), "Brier": brier_score_loss(y, p)}


rows, curves, viol, NAMS, P9 = [], [], [], {}, {}
rng = np.random.default_rng(SEED)
for t in ("A", "B"):
    tr, va = TR[TR[f"y_{t}"].notna()].reset_index(drop=True), VA[VA[f"y_{t}"].notna()].reset_index(drop=True)
    ytr, yva = tr[f"y_{t}"].astype(int).to_numpy(), va[f"y_{t}"].astype(int).to_numpy()
    nam = NAMEnsemble(SIGNS, cfg, SEED).fit(tr[F].to_numpy(float), ytr)
    NAMS[t] = nam
    curves.append(nam.curve.assign(target=t))
    p_nam = nam.predict_proba(va[F].to_numpy(float))
    p_ebm = EBM[(t, "EBM monótono")].predict_proba(va[F])[:, 1]
    P9[t] = pd.Series(p_nam, index=va.household_id)
    for name, p in (("NAM monótono", p_nam), ("EBM monótono (champion provisional)", p_ebm)):
        for seg in ("pooled", "HNW", "UHNW"):
            mk = np.ones(len(va), bool) if seg == "pooled" else (va.segment == seg).to_numpy()
            rows.append({"target": t, "modelo": name, "segmento": seg, "hogares": int(mk.sum()), "eventos": int(yva[mk].sum()), **metrics(yva[mk], p[mk])})
    # Monotonía: funciones de forma y ICE del modelo completo
    for j, c in enumerate(F):
        if SIGNS[j] == 0:
            continue
        g = nam.shape_grid(j)
        v_member = int((np.diff(g, axis=1) * SIGNS[j] < -1e-9).sum())
        v_ens = int((np.diff(g.mean(0)) * SIGNS[j] < -1e-9).sum())
        Xi = tr[F].to_numpy(float)[rng.choice(len(tr), 300, replace=False)]
        grid = np.unique(np.nanquantile(tr[c].astype(float), np.linspace(0, 1, 21)))
        L = []
        for gv in grid:
            Z = Xi.copy()
            Z[:, j] = gv
            L.append(nam.logit(Z))
        L = np.array(L).T
        v_ice = int((np.diff(L, axis=1) * SIGNS[j] < -1e-7).sum())
        viol.append({"target": t, "feature": c, "signo": "+" if SIGNS[j] > 0 else "−", "violaciones forma (miembros)": v_member, "violaciones forma (ensamble)": v_ens,
                     "violaciones ICE": v_ice})
CMP, CUR, VIO = pd.DataFrame(rows), pd.concat(curves, ignore_index=True), pd.DataFrame(viol)
with open(out / "nam_models.pkl", "wb") as fh:
    pickle.dump({"models": NAMS, "features": F, "signs": SIGNS, "cfg": cfg}, fh)

# Referencia A-lite en el subconjunto justo
ref = []
for t in ("A", "B"):
    v = VA[VA[f"y_{t}"].notna() & (VA.muestra == "holdout")].reset_index(drop=True)
    yy = v[f"y_{t}"].astype(int).to_numpy()
    ref.append({"target": t, "modelo": "A-lite (congelado)", "hogares": len(v), "eventos": int(yy.sum()), **metrics(yy, v.probabilidad_lite.to_numpy())})
    ref.append({"target": t, "modelo": "NAM monótono", "hogares": len(v), "eventos": int(yy.sum()), **metrics(yy, P9[t].loc[v.household_id].to_numpy())})
    ref.append({"target": t, "modelo": "EBM monótono", "hogares": len(v), "eventos": int(yy.sum()), **metrics(yy, EBM[(t, "EBM monótono")].predict_proba(v[F])[:, 1])})
REF = pd.DataFrame(ref)

# Figuras
fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, t in zip(axes, ("A", "B")):
    c = CUR[CUR.target == t]
    for sd, g in c.groupby("semilla"):
        ax.plot(g["época"], g["pérdida train"], color="#a3a29c", lw=1)
        ax.plot(g["época"], g["pérdida early-stop"], color="#2a78d6", lw=1.5)
    ax.set_title(f"target {t} · gris = train, azul = early-stop (15% interno) · {c.semilla.nunique()} miembros", fontsize=9, loc="left")
    ax.set_xlabel("época", fontsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=7.5)
axes[0].set_ylabel("pérdida BCE", fontsize=8)
fig.tight_layout()
fig.savefig(out / "training_curve.png", dpi=110)
plt.close(fig)
namA = NAMS["A"]
C = namA.contributions(TR[F].to_numpy(float))
top = np.argsort(-np.abs(C).mean(0))[:12]
fig, axes = plt.subplots(3, 4, figsize=(15, 9))
for ax, j in zip(axes.flat, top):
    g = namA.shape_grid(j)
    u = np.linspace(0, 1, g.shape[1])
    for row in g:
        ax.plot(u, row - row.mean(), color="#a3a29c", lw=0.8)
    ax.plot(u, g.mean(0) - g.mean(), color="#2a78d6", lw=2)
    s = {1: "+", -1: "−", 0: "libre"}[SIGNS[j]]
    ax.set_title(f"{F[j]} ({s})", fontsize=8.5, loc="left")
    ax.set_xlabel("percentil de la variable (train)", fontsize=7)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=7)
fig.suptitle("NAM · funciones de forma (log-odds, centradas) de las 12 variables de mayor peso · target A · gris = miembros, azul = ensamble", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(out / "shape_functions_A.png", dpi=110)
plt.close(fig)

ep = CUR.groupby(["target", "semilla"])["época"].max()
SUM = {"parámetros": cfg, "épocas por miembro (A)": ep.loc["A"].tolist(), "épocas por miembro (B)": ep.loc["B"].tolist(),
       "violaciones totales en variables duras": int(VIO[["violaciones forma (miembros)", "violaciones forma (ensamble)", "violaciones ICE"]].to_numpy().sum()),
       "convergió (early stopping antes de epochs_max)": bool((ep < cfg["epochs_max"]).all()), "test abierto": False}
CUR.to_csv(out / "training_curve.csv", index=False)
CMP.to_csv(out / "nam_validation.csv", index=False)
VIO.to_csv(out / "monotonicity_violations.csv", index=False)
REF.to_csv(out / "alite_fair_validation.csv", index=False)
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 9 · NAM monótono (validación)", "order": ["summary.json", "nam_validation.csv", "alite_fair_validation.csv", "training_curve.png", "shape_functions_A.png", "monotonicity_violations.csv"],
           "notes": {"monotonicity_violations.csv": "Monotonía por construcción (pesos ≥ 0 + tanh); se verifica igual en funciones de forma e ICE."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(9)
print(json.dumps(SUM, ensure_ascii=False)); print(CMP.round(4).to_string(index=False)); print(REF.round(4).to_string(index=False))
