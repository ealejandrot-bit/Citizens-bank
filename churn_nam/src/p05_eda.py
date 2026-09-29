"""Fase 5 · EDA exploratoria (solo dev heredado; el test no se mira). Nada de esto entra al modelo sin evidencia.

- Churn rate por decil de cada feature con IC Wilson 95% (target A principal, B al lado); binarias: 0/1; NaN como grupo.
  Figuras: las 24 features de mayor |ρ| con A.
- Clusters de redundancia: enlace completo sobre 1 − |ρ Spearman|, corte |ρ| ≥ 0.70.
- PCA y K-means exploratorios sobre rangos normalizados (NaN → 0 = mediana de rango, solo para explorar; declarado).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from scipy.stats import norm
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from statsmodels.stats.proportion import proportion_confint

from config import P, SEED, set_seed
from report import render

set_seed()
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "y_A", "y_B"]]
dev_ids = set(pd.read_parquet(P.m1 / "data" / "processed" / "dev.parquet").household_id)
D = X[X.household_id.isin(dev_ids)].merge(pop, on="household_id").reset_index(drop=True)
F = [c for c in X.columns if c != "household_id"]
out = P.out(5)

rows = []
for c in F:
    x = D[c]
    if x.dropna().nunique() <= 2:
        g = x.astype("object").where(x.notna(), "NaN").astype(str)
    else:
        g = pd.qcut(x.rank(method="first"), 10, labels=[f"D{i}" for i in range(1, 11)]).astype(str).where(x.notna(), "NaN")
    for lv, s in D.groupby(g):
        for t in ("A", "B"):
            yy = s[f"y_{t}"].dropna()
            e, n = int(yy.sum()), len(yy)
            lo, hi = proportion_confint(e, n, alpha=0.05, method="wilson")
            rows.append({"feature": c, "grupo": lv, "target": t, "hogares": n, "eventos": e, "tasa %": 100 * e / n, "IC95 inf %": 100 * lo, "IC95 sup %": 100 * hi,
                         "valor mín": x[g == lv].min(), "valor máx": x[g == lv].max()})
DR = pd.DataFrame(rows)
DR.to_csv(out / "decile_rates.csv", index=False)
rho = pd.Series({c: D[c].corr(D.y_A, method="spearman") for c in F}).sort_values(key=np.abs, ascending=False)
top = rho.index[:24].tolist()
fig, axes = plt.subplots(4, 6, figsize=(22, 13), sharey=True)
base = 100 * D.y_A.mean()
for ax, c in zip(axes.flat, top):
    t = DR[(DR.feature == c) & (DR.target == "A")]
    order = [g for g in [f"D{i}" for i in range(1, 11)] + ["0", "1", "0.0", "1.0", "NaN"] if g in set(t.grupo)]
    t = t.set_index("grupo").loc[order].reset_index()
    xs = np.arange(len(t))
    ax.errorbar(xs, t["tasa %"], yerr=[t["tasa %"] - t["IC95 inf %"], t["IC95 sup %"] - t["tasa %"]], fmt="o", color="#2a78d6", ms=4, lw=1, capsize=0)
    ax.axhline(base, color="#a3a29c", lw=0.8, ls="--")
    ax.set_xticks(xs, t.grupo, fontsize=6.5, rotation=90, color="#52514e")
    ax.set_title(f"{c}\nρ = {rho[c]:+.3f}", fontsize=8, loc="left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7, colors="#52514e")
    ax.grid(axis="y", color="#e6e5df", lw=0.5)
fig.suptitle("Tasa de hard churn (A) por decil de cada feature con IC Wilson 95% · dev · 24 features de mayor |ρ| (línea = tasa base) [DATA]", x=0.01, ha="left", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))
fig.savefig(out / "decile_rates_top24.png", dpi=100)
plt.close(fig)

# Redundancia
Xn = D[F].astype(float)
SP = Xn.corr(method="spearman").fillna(0)
R = SP.abs().to_numpy().copy()
np.fill_diagonal(R, 1)
lab = fcluster(linkage(squareform(1 - R, checks=False), "complete"), t=0.30, criterion="distance")
CL = pd.DataFrame({"feature": F, "cluster": lab, "ρ con A": [rho[c] for c in F]})
multi = CL.groupby("cluster").filter(lambda g: len(g) > 1).sort_values(["cluster", "ρ con A"], key=lambda s: s if s.name == "cluster" else -s.abs())
multi["máx |ρ| dentro del cluster"] = multi.cluster.map(lambda k: SP.loc[CL.feature[CL.cluster == k], CL.feature[CL.cluster == k]].abs().where(~np.eye((CL.cluster == k).sum(), dtype=bool)).max().max())
multi.to_csv(out / "redundancy_clusters.csv", index=False)

# PCA y K-means exploratorios
Z = pd.DataFrame({c: np.nan_to_num(norm.ppf(Xn[c].rank(pct=True).clip(0.5 / len(Xn), 1 - 0.5 / len(Xn))), nan=0.0) for c in F})
pca = PCA().fit(Z)
ev = pca.explained_variance_ratio_
PC = pd.DataFrame({"componente": [f"PC{i + 1}" for i in range(10)], "varianza %": 100 * ev[:10], "acumulada %": 100 * np.cumsum(ev)[:10],
                   "top 4 loadings": [", ".join(f"{F[j]} {pca.components_[i][j]:+.2f}" for j in np.argsort(-np.abs(pca.components_[i]))[:4]) for i in range(10)]})
PC.to_csv(out / "pca_exploratory.csv", index=False)
rng = np.random.default_rng(SEED)
idx = rng.choice(len(Z), 5000, replace=False)
KM = []
for k in range(2, 7):
    km = KMeans(k, n_init=10, random_state=SEED).fit(Z)
    KM.append({"K": k, "silhouette": silhouette_score(Z.iloc[idx], km.labels_[idx]), "cluster mín %": 100 * np.bincount(km.labels_).min() / len(Z),
               "tasa A % por cluster": " / ".join(f"{100 * D.y_A[km.labels_ == j].mean():.1f}" for j in range(k))})
KM = pd.DataFrame(KM)
KM.to_csv(out / "kmeans_exploratory.csv", index=False)

SUM = {"hogares dev": len(D), "eventos A dev": int(D.y_A.sum()), "features": len(F), "features con IC que excluye la tasa base en algún decil":
       int(DR[(DR.target == "A") & ((DR["IC95 inf %"] > base) | (DR["IC95 sup %"] < base))].feature.nunique()),
       "clusters de redundancia (|ρ| ≥ 0.70)": int(multi.cluster.nunique()), "features en clusters": len(multi),
       "PCA: componentes para 80% de varianza": int(np.searchsorted(np.cumsum(ev), 0.80) + 1), "K-means: mejor silhouette": float(KM.silhouette.max()),
       "recordatorio": "EDA exploratoria: nada de esto entra al modelo sin evidencia (PCA y clustering solo diagnósticos)"}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 5 · EDA (exploratoria, solo dev)", "order": ["summary.json", "decile_rates_top24.png", "redundancy_clusters.csv", "pca_exploratory.csv", "kmeans_exploratory.csv", "decile_rates.csv"],
           "notes": {"pca_exploratory.csv": "Rangos normalizados con NaN → 0 solo para explorar (no se usa en ningún modelo).",
                     "redundancy_clusters.csv": "Enlace completo: dentro de cada cluster todos los pares tienen |ρ| ≥ 0.70."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
render(5)
print(SUM); print(multi.round(3).to_string(index=False)); print(PC.round(1).head(6).to_string(index=False)); print(KM.round(3).to_string(index=False))
