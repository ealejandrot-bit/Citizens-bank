"""Fase 11 · Calibración (target A): Platt vs isotónica ajustadas en validación, elegida por ECE, evaluada en test.

- Modelos: EBM monótono (champion), NAM monótono (challenger), A-lite congelado (en validación ∩ holdout de A-lite).
- Para no premiar el sobreajuste de la isotónica, el ECE de selección es fuera de muestra: CV 5 folds dentro de
  validación (D11.1). El método elegido se re-ajusta en toda la validación y se evalúa una vez en test.
- Platt: y ~ a + b·logit(p). ECE = Σ share_decil · |p media − tasa|. a y b guardados (también los de Platt cuando gana
  la isotónica, como referencia).
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
import statsmodels.api as sm
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold

from config import P, SEED, set_seed
from report import render

warnings.filterwarnings("ignore")
set_seed()
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A"]]
S = pd.read_parquet(P.processed / "splits.parquet")
F = [c for c in X.columns if c != "household_id"]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "probabilidad_lite"]]
alh = pd.read_csv(P.alite / "outputs" / "tables" / "04_split.csv")[["household_id", "muestra"]]
D = D.merge(al, on="household_id", how="left").merge(alh, on="household_id", how="left")
NAM = pickle.load(open(P.out(9) / "nam_models.pkl", "rb"))["models"]["A"]
EBM = pickle.load(open(P.out(8) / "models.pkl", "rb"))[("A", "EBM monótono")]
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731


def ece(y, p, k=10):
    d = pd.qcut(pd.Series(p).rank(method="first"), k, labels=False)
    g = pd.DataFrame({"d": d, "p": p, "y": y}).groupby("d").agg(n=("y", "size"), p=("p", "mean"), y=("y", "mean"))
    return float((g.n / g.n.sum() * (g.p - g.y).abs()).sum())


def platt(x, y):
    m = sm.GLM(y, sm.add_constant(x), family=sm.families.Binomial()).fit()
    return float(m.params[0]), float(m.params[1])


def score(name, d):
    if name == "EBM monótono (champion)":
        return EBM.predict_proba(d[F])[:, 1]
    if name == "NAM monótono (challenger)":
        return NAM.predict_proba(d[F].to_numpy(float))
    return d.probabilidad_lite.to_numpy()


rows, CAL, curves = [], {}, {}
for name in ("EBM monótono (champion)", "NAM monótono (challenger)", "A-lite (congelado)"):
    va = D[(D.split == "validation") & ((D.muestra == "holdout") if name.startswith("A-lite") else True)].reset_index(drop=True)
    te = D[(D.split == "test") & (D.test_alite if name.startswith("A-lite") else True)].reset_index(drop=True)
    yv, yt = va.y_A.astype(int).to_numpy(), te.y_A.astype(int).to_numpy()
    pv, pt = score(name, va), score(name, te)
    xv, xt = lg(pv), lg(pt)
    op, oi = np.zeros(len(yv)), np.zeros(len(yv))
    for tr, ts in StratifiedKFold(5, shuffle=True, random_state=SEED).split(xv, yv):
        a_, b_ = platt(xv[tr], yv[tr])
        op[ts] = 1 / (1 + np.exp(-(a_ + b_ * xv[ts])))
        oi[ts] = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(xv[tr], yv[tr]).predict(xv[ts])
    e_p, e_i = ece(yv, op), ece(yv, oi)
    choice = "platt" if e_p <= e_i else "isotonic"
    a, b = platt(xv, yv)
    iso = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(xv, yv)
    pc = 1 / (1 + np.exp(-(a + b * xt))) if choice == "platt" else iso.predict(xt)
    CAL[name] = {"method": choice, "a": a, "b": b, "isotonic": iso if choice == "isotonic" else None}
    curves[name] = (yt, pt, pc)
    rows.append({"modelo": name, "hogares validación": len(yv), "eventos validación": int(yv.sum()), "ECE CV Platt (pp)": 100 * e_p, "ECE CV isotónica (pp)": 100 * e_i,
                 "elegido": choice, "a (Platt)": a, "b (Platt)": b, "hogares test": len(yt), "eventos test": int(yt.sum()),
                 "ECE test sin calibrar (pp)": 100 * ece(yt, pt), "ECE test calibrado (pp)": 100 * ece(yt, pc), "Brier test sin calibrar": brier_score_loss(yt, pt),
                 "Brier test calibrado": brier_score_loss(yt, pc), "media p test %": 100 * pc.mean(), "tasa test %": 100 * yt.mean()})
CT = pd.DataFrame(rows)
out = P.out(11)
CT.to_csv(out / "calibration.csv", index=False)
with open(out / "calibrators.pkl", "wb") as fh:
    pickle.dump(CAL, fh)
json.dump({k: {"method": v["method"], "a": v["a"], "b": v["b"]} for k, v in CAL.items()}, open(out / "calibrators.json", "w"), ensure_ascii=False, indent=1)
fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), sharey=True)
for ax, (name, (y, p0, p1)) in zip(axes, curves.items()):
    for p, lab, col in ((p0, "sin calibrar", "#a3a29c"), (p1, "calibrada", "#2a78d6")):
        d = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
        g = pd.DataFrame({"d": d, "p": p, "y": y}).groupby("d").mean()
        ax.plot(g.p, g.y, marker="o", ms=5, lw=2, color=col, label=lab, markeredgecolor="white", markeredgewidth=1.5)
    ax.plot([0, .45], [0, .45], ls="--", lw=1, color="#52514e")
    ax.set_xlim(0, .45); ax.set_ylim(0, .45)
    ax.set_title(f"{name} · test", fontsize=9, loc="left")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(color="#e6e5df", lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7.5)
    ax.set_xlabel("probabilidad (media del decil)", fontsize=8)
axes[0].set_ylabel("tasa de hard churn observada", fontsize=8)
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(out / "calibration_test.png", dpi=110)
json.dump({"title": "Fase 11 · Calibración (target A)", "order": ["calibration.csv", "calibrators.json", "calibration_test.png"],
           "notes": {"calibration.csv": "ECE de selección fuera de muestra (CV 5 folds dentro de validación); evaluación en test. A-lite en su subconjunto justo."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(11)
print(CT.round(4).to_string(index=False))
