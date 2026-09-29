"""Paso 11C · Vista de ajuste de probabilidad del ML vs el campeón (pedido del usuario en G2-4).

OOF de la repetición 1 de la CV (5 folds, dev, target B), sin tocar validación:
- campeón (logística WoE, intercepto corregido; binning re-ajustado por fold), XGBoost monotónico (prior corregido),
  EBM monotónico, random forest (crudo y corregido por prior: sus pesos balanceados inflan la probabilidad).
- Por decil de probabilidad predicha: media predicha vs tasa observada. Métricas: Brier, pendiente b, media p − tasa,
  ECE (Σ share_decil × |predicha − observada|).
Es descriptivo: la calibración formal (Platt / isotónica sobre validación) es del paso 14 y solo para el campeón.
"""
from __future__ import annotations

import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss

from common import FIGS, MODEL, PROC, SEED, load_split, save_table, set_seed

set_seed()
dev = load_split("dev").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
cv = D.cv_r1.to_numpy()
CH = pickle.load(open(MODEL / "step11B_challenger.pkl", "rb"))
V, MONO = CH["vars"], CH["mono"]
X = D[V].copy()
if "cluster" in X:
    X["cluster"] = X["cluster"].cat.codes if hasattr(X["cluster"], "cat") else X["cluster"]

P = pd.DataFrame({"household_id": D.household_id})
P = P.merge(pd.read_parquet(PROC / "step11A_oof.parquet"), on="household_id").merge(pd.read_parquet(PROC / "step11B_oof.parquet"), on="household_id")
P = P.set_index("household_id").loc[D.household_id].reset_index()
p_ebm, p_rf, p_rfc = np.zeros(len(D)), np.zeros(len(D)), np.zeros(len(D))
for k in range(5):
    tr, te = cv != k, cv == k
    e = ExplainableBoostingClassifier(monotone_constraints=list(MONO), random_state=SEED, n_jobs=4, interactions=0).fit(X[tr], y[tr])
    p_ebm[te] = e.predict_proba(X[te])[:, 1]
    rf = RandomForestClassifier(500, min_samples_leaf=50, class_weight="balanced_subsample", random_state=SEED, n_jobs=4).fit(X[tr], y[tr])
    p = np.clip(rf.predict_proba(X[te])[:, 1], 1e-6, 1 - 1e-6)
    spw = (y[tr] == 0).sum() / y[tr].sum()
    p_rf[te] = p
    p_rfc[te] = 1 / (1 + np.exp(-(np.log(p / (1 - p)) - np.log(spw))))
MODELS = {"campeón (logística WoE)": P.p_champion_oof_r1.to_numpy(), "XGBoost monotónico": P.p_challenger_oof_r1.to_numpy(),
          "EBM monotónico": p_ebm, "random forest (crudo)": p_rf, "random forest (corregido por prior)": p_rfc}


def slope(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(sm.GLM(y, sm.add_constant(np.log(p / (1 - p))), family=sm.families.Binomial()).fit().params[1])


dec_rows, met = [], []
for name, p in MODELS.items():
    d = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False) + 1
    g = pd.DataFrame({"decil": d, "p": p, "y": y}).groupby("decil").agg(hogares=("y", "size"), predicha=("p", "mean"), observada=("y", "mean"))
    g["modelo"] = name
    dec_rows.append(g.reset_index())
    ece = float((g.hogares / g.hogares.sum() * (g.predicha - g.observada).abs()).sum())
    met.append({"modelo": name, "Brier": brier_score_loss(y, p), "pendiente b": slope(p), "media p %": 100 * p.mean(), "tasa observada %": 100 * y.mean(),
                "ECE (pp)": 100 * ece, "tasa decil 10 predicha %": 100 * g.predicha.iloc[-1], "tasa decil 10 observada %": 100 * g.observada.iloc[-1]})
dec = pd.concat(dec_rows, ignore_index=True)[["modelo", "decil", "hogares", "predicha", "observada"]]
met = pd.DataFrame(met)
save_table(dec, "step11C_calibration_deciles")
save_table(met, "step11C_calibration_metrics")

# Figura: small multiples (un panel por modelo), predicha vs observada por decil, diagonal = ajuste perfecto
names = list(MODELS)
fig, axes = plt.subplots(1, len(names), figsize=(19, 4.2), sharex=True, sharey=True)
lim = max(dec.predicha.max(), dec.observada.max()) * 1.05
for ax, n in zip(axes, names):
    g = dec[dec.modelo == n]
    ax.plot([0, lim], [0, lim], color="#a3a29c", lw=1, ls="--")
    ax.plot(g.predicha, g.observada, color="#2a78d6", lw=2, marker="o", ms=5, markeredgecolor="white", markeredgewidth=1.5)
    m = met.set_index("modelo").loc[n]
    ax.set_title(f"{n}\nBrier {m['Brier']:.4f} · b {m['pendiente b']:.2f} · ECE {m['ECE (pp)']:.1f} pp", fontsize=8.5, loc="left", color="#1f1f1e")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(color="#e6e5df", lw=0.6); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7.5, colors="#52514e")
    ax.set_xlabel("probabilidad predicha (media del decil)", fontsize=7.5, color="#52514e")
axes[0].set_ylabel("tasa de churn B observada", fontsize=7.5, color="#52514e")
fig.suptitle("Ajuste de probabilidad por decil · OOF de dev, CV r1 (5 folds) · target B [DATA] · línea punteada = ajuste perfecto",
             x=0.01, ha="left", fontsize=10.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
FIGS.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGS / "step11C_calibration.png", dpi=120)

print(met.round(4).to_string(index=False))
