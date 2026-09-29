"""Paso 7 · Segmentación.

Clustering sobre estructura del hogar (sin señales ni target): age_primary, tenure_years,
log10 relationship_value y los 8 has_*, estandarizados. Ajuste en desarrollo; se asigna a todos.
K ∈ 2..8 con K-means (n_init = 20); GMM diagonal como comparación (BIC).
Regla de elección de K, fijada antes de ver resultados (D7.1):
  entre los K con cluster mínimo ≥ 5% y estabilidad bootstrap (ARI medio) ≥ 0.80 → mayor silhouette;
  si ninguno cumple → mayor ARI. Luego se valida interpretabilidad de centroides.
Churn por cluster solo en desarrollo, descriptivo (sin inferir causalidad).
Regla del brief: ningún modelo separado por segmento (UHNW = 80 eventos < 100); `segment` entra forzado;
cluster = variable candidata para el binning (paso 9).
"""
from __future__ import annotations

import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.proportion import proportion_confint

from common import FIGURES, MODELS, OUT, PARAMS, QC, SEED, TABLES, save_table, set_seed

set_seed()
T = PARAMS["target_primary"]
X = pd.read_pickle(OUT / "data" / "05_features.pkl")
split = pd.read_csv(TABLES / "04_split.csv", usecols=["household_id", "muestra"])
X = X.merge(split, on="household_id")
HAS = ["has_investments", "has_advisory", "has_linked_business", "has_trust", "has_credit_anchor",
       "has_payroll_stream", "has_pension_stream", "has_dividend_stream"]
FEATS = ["age_primary", "tenure_years", "log_relationship_value"] + HAS
dev_mask = (X.muestra == "desarrollo").to_numpy()

scaler = StandardScaler().fit(X.loc[dev_mask, FEATS])
Z = scaler.transform(X[FEATS])
Zd = Z[dev_mask]
rng = np.random.default_rng(SEED)
sil_idx = rng.choice(len(Zd), 5000, replace=False)

rows, fits = [], {}
for k in range(2, 9):
    km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(Zd)
    lab = km.labels_
    aris = []
    for b in range(20):
        bi = rng.choice(len(Zd), len(Zd), replace=True)
        kb = KMeans(n_clusters=k, n_init=5, random_state=SEED + b).fit(Zd[bi])
        aris.append(adjusted_rand_score(lab, kb.predict(Zd)))
    gm = GaussianMixture(k, covariance_type="diag", random_state=SEED, n_init=3).fit(Zd)
    sizes = np.bincount(lab) / len(lab)
    rows.append({"K": k, "silhouette": silhouette_score(Zd[sil_idx], lab[sil_idx]), "WCSS": km.inertia_,
                 "ARI bootstrap medio": np.mean(aris), "ARI p5": np.percentile(aris, 5),
                 "cluster mín %": 100 * sizes.min(), "cluster máx %": 100 * sizes.max(),
                 "BIC GMM diag": gm.bic(Zd), "ARI K-means vs GMM": adjusted_rand_score(lab, gm.predict(Zd))})
    fits[k] = km
sel = pd.DataFrame(rows)
ok = sel[(sel["cluster mín %"] >= 5) & (sel["ARI bootstrap medio"] >= 0.80)]
K = int(ok.loc[ok.silhouette.idxmax(), "K"]) if len(ok) else int(sel.loc[sel["ARI bootstrap medio"].idxmax(), "K"])
sel["elegido"] = np.where(sel.K == K, "◀", "")
save_table(sel.round(4), "07_k_selection")

km = fits[K]
X["cluster"] = km.predict(Z)
dev = X[dev_mask]

# Perfil de centroides (unidades originales) y churn descriptivo en desarrollo
prof = dev.groupby("cluster").agg(
    hogares=("household_id", "size"), edad_media=("age_primary", "mean"), antigüedad_mediana=("tenure_years", "median"),
    RV_mediano_M=("log_relationship_value", lambda s: 10 ** s.median() / 1e6), pct_UHNW=("segment", lambda s: 100 * s.mean()),
    **{f"%{h.replace('has_', '')}": (h, lambda s: 100 * s.mean()) for h in HAS},
    eventos=(T, "sum"), tasa_hard=(T, "mean"))
prof["% hogares"] = 100 * prof.hogares / prof.hogares.sum()
lo, hi = proportion_confint(prof.eventos, prof.hogares, alpha=0.10, method="wilson")
prof["tasa hard %"] = 100 * prof.tasa_hard
prof["Wilson 90%"] = [f"[{100 * a:.2f}, {100 * b:.2f}]" for a, b in zip(lo, hi)]
prof["lift"] = prof.tasa_hard / dev[T].mean()
rv = 10 ** dev.log_relationship_value
prof["% RV"] = 100 * rv.groupby(dev.cluster).sum() / rv.sum()
prof["churn valor hard %"] = 100 * (rv * dev[T]).groupby(dev.cluster).sum() / rv.groupby(dev.cluster).sum()
prof = prof.drop(columns=["tasa_hard"]).reset_index()
chi2, p_chi, dof, _ = chi2_contingency(pd.crosstab(dev.cluster, dev[T]))
save_table(prof.round(3), "07_cluster_profile")
seg_x = pd.crosstab(dev.cluster, dev.segment.map({0: "HNW", 1: "UHNW"}), margins=True)
save_table(seg_x.reset_index(), "07_cluster_x_segment")

X[["household_id", "cluster"]].to_csv(OUT / "data" / "07_clusters.csv", index=False)
with open(MODELS / "07_kmeans.pkl", "wb") as fh:
    pickle.dump({"scaler": scaler, "kmeans": km, "features": FEATS, "K": K}, fh)

qc = QC("07")
qc.check("Clustering sin señales ni target", not set(FEATS) & {T, "soft_churn_3m", "value_lost_6m", "multi_signal_count"}, "∅", "∅")
qc.check("Ajuste solo en desarrollo", len(Zd) == 13_913, 13_913, len(Zd))
qc.check("K elegido cumple tamaño mínimo 5%", float(sel.loc[sel.K == K, "cluster mín %"].iloc[0]) >= 5, "≥ 5%",
         f"{float(sel.loc[sel.K == K, 'cluster mín %'].iloc[0]):.1f}%", severity="warn")
qc.check("K elegido estable (ARI ≥ 0.80)", float(sel.loc[sel.K == K, "ARI bootstrap medio"].iloc[0]) >= 0.80, "≥ 0.80",
         f"{float(sel.loc[sel.K == K, 'ARI bootstrap medio'].iloc[0]):.3f}", severity="warn")
qc.check("Tramos suman 100% de hogares de desarrollo", abs(prof["% hogares"].sum() - 100) < 1e-9, "100%", f"{prof['% hogares'].sum():.4f}%")
mix = (prof["% hogares"] / 100 * prof["tasa hard %"]).sum()
qc.check("Churn desarrollo = Σ share × tasa por cluster", abs(mix - 100 * dev[T].mean()) < 1e-9, f"{100 * dev[T].mean():.4f}", f"{mix:.4f}")
qc.check("Asignación a toda la base", X.cluster.notna().all() and len(X) == 20_000, 20_000, len(X))
print(f"  [INFO] χ² cluster × hard (desarrollo): χ²={chi2:.1f}, gl={dof}, p={p_chi:.3g}")

# Figuras
INK, MUTED, GRID, BLUE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6"
fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
for ax, col, ttl in zip(axes, ["silhouette", "ARI bootstrap medio", "WCSS"], ["Silhouette", "Estabilidad (ARI bootstrap)", "WCSS (codo)"]):
    ax.plot(sel.K, sel[col], color=BLUE, lw=2, marker="o", ms=6)
    ax.plot([K], sel.loc[sel.K == K, col], "o", color=INK, ms=9, mfc="none", mew=1.5)
    ax.set_title(ttl, loc="left", color=INK, fontsize=10)
    ax.set_xlabel("K", color=MUTED)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
axes[1].axhline(0.80, color=MUTED, lw=1, ls="--")
fig.suptitle(f"Selección de K (círculo = K elegido = {K}) · desarrollo [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "07_k_selection.png", dpi=140)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 3.4))
lo_e = prof["tasa hard %"] - 100 * lo.values
hi_e = 100 * hi.values - prof["tasa hard %"]
ax.bar(prof.cluster.astype(str), prof["tasa hard %"], color=BLUE, width=0.6)
ax.errorbar(prof.cluster.astype(str), prof["tasa hard %"], yerr=[lo_e, hi_e], fmt="none", ecolor=INK, capsize=4, lw=1)
ax.axhline(100 * dev[T].mean(), color=MUTED, lw=1, ls="--")
for i, r in prof.iterrows():
    ax.text(i, 0.3, f"{r['% hogares']:.0f}% hog.", ha="center", color="white", fontsize=8)
ax.set_xlabel("cluster", color=MUTED)
ax.set_ylabel("tasa hard % (Wilson 90%)", color=MUTED)
ax.set_title("Tasa de hard churn por cluster · desarrollo [DATA-SINT]", loc="left", color=INK, fontsize=11)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, length=0)
fig.tight_layout()
fig.savefig(FIGURES / "07_churn_by_cluster.png", dpi=140)

print("\n" + sel.round(3).to_string(index=False))
print("\n" + prof.round(2).to_string(index=False))
print("\n" + seg_x.to_string())
qc.gate()
