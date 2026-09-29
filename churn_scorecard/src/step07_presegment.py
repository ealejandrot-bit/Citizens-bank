"""Paso 7 · Pre-segmentación estructural (K-means y GMM), ajustada en dev y asignada sin reajuste.

Variables: segment_uhnw, tenure_years, log_rv, has_* (8), estandarizadas con media / sd de dev. Sin age_primary
(G1-3: el cluster es candidato a predictor y no debe reintroducir la edad; D7.1).
K ∈ 2..8. Regla fijada antes de ver resultados: tamaño mínimo ≥ 5% y ARI bootstrap ≥ 0.80 → mayor silhouette.
GMM (diagonal) como comparación. Tasa de churn por cluster sin inferencia causal. Sin scorecard separado (UHNW < 100 eventos).
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.proportion import proportion_confint

from common import MODEL, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

set_seed()
dev, val = load_split("dev"), load_split("val")
F = pd.read_parquet(PROC / "features.parquet")
F["segment_uhnw"] = (F.segment == "UHNW").astype(int)
HAS = [c for c in dev.columns if c.startswith("has_")]
X_COLS = ["segment_uhnw", "tenure_years", "log_rv"] + HAS
sc = StandardScaler().fit(dev[X_COLS].astype(float))
Zd = sc.transform(dev[X_COLS].astype(float))
rng = np.random.default_rng(SEED)
sil_idx = rng.choice(len(Zd), 5000, replace=False)
rows, fits = [], {}
for k in range(2, 9):
    km = KMeans(k, n_init=20, random_state=SEED).fit(Zd)
    aris = [adjusted_rand_score(km.labels_, KMeans(k, n_init=5, random_state=SEED + b).fit(Zd[rng.choice(len(Zd), len(Zd))]).predict(Zd)) for b in range(20)]
    gm = GaussianMixture(k, covariance_type="diag", random_state=SEED, n_init=3).fit(Zd)
    rows.append({"K": k, "silhouette": silhouette_score(Zd[sil_idx], km.labels_[sil_idx]), "WCSS": km.inertia_, "ARI bootstrap": np.mean(aris),
                 "cluster mín %": 100 * np.bincount(km.labels_).min() / len(Zd), "BIC GMM": gm.bic(Zd), "ARI K-means vs GMM": adjusted_rand_score(km.labels_, gm.predict(Zd))})
    fits[k] = km
sel = pd.DataFrame(rows)
ok = sel[(sel["cluster mín %"] >= 5) & (sel["ARI bootstrap"] >= 0.80)]
K = int(ok.loc[ok.silhouette.idxmax(), "K"]) if len(ok) else int(sel.loc[sel["ARI bootstrap"].idxmax(), "K"])
sel["elegido"] = np.where(sel.K == K, "◀", "")
save_table(sel, "step07_k_selection")
km = fits[K]
F["cluster"] = km.predict(sc.transform(F[X_COLS].astype(float)))
F[["household_id", "cluster"]].to_parquet(PROC / "step07_clusters.parquet", index=False)
with open(MODEL / "step07_kmeans.pkl", "wb") as fh:
    pickle.dump({"scaler": sc, "kmeans": km, "features": X_COLS, "K": K}, fh)

dev = dev.merge(F[["household_id", "cluster"]], on="household_id")
prof = []
for c_ in range(K):
    g = dev[dev.cluster == c_]
    b = g[g.in_pop_B]
    lo, hi = proportion_confint(b.y_B.sum(), len(b), alpha=0.10, method="wilson")
    prof.append({"cluster": c_, "hogares dev": len(g), "% dev": 100 * len(g) / len(dev), "% UHNW": 100 * g.segment_uhnw.mean(),
                 "antigüedad mediana": g.tenure_years.median(), "RV mediano $M": 10 ** g.log_rv.median() / 1e6,
                 **{f"% {h.replace('has_', '')}": 100 * g[h].mean() for h in HAS},
                 "eventos B": int(b.y_B.sum()), "tasa B %": 100 * b.y_B.mean(), "Wilson 90% B": f"[{100 * lo:.1f}, {100 * hi:.1f}]",
                 "tasa A %": 100 * g.loc[g.in_pop_A.astype(bool), "y_A"].mean()})
pr = pd.DataFrame(prof)
save_table(pr, "step07_cluster_profile")
b_ = dev[dev.in_pop_B]
chi = chi2_contingency(pd.crosstab(b_.cluster, b_.y_B))
mix = (pr["hogares dev"] / pr["hogares dev"].sum() * pr["tasa B %"]).sum()

rep = f"""# Paso 7 · Pre-segmentación

## Objetivo
- Ver si hay perfiles estructurales con riesgo distinto; decidir si justifican variable o modelo propio.

## Método
- K-means (n_init = 20) y GMM diagonal sobre {', '.join(f'`{c}`' for c in X_COLS)}, estandarizadas en dev. Sin `age_primary` (D7.1).
- Regla (antes de ver resultados): tamaño ≥ 5% y ARI bootstrap ≥ 0.80 → mayor silhouette. Ajuste en dev; asignación a
  val y a toda la base sin reajuste. Tasas descriptivas, sin causalidad.

## Código
- `src/step07_presegment.py` · `tests/test_step07.py` · `data/processed/step07_clusters.parquet`, `outputs/model/step07_kmeans.pkl`.

## Resultados

### Selección de K [DATA]
{md_table(sel, floatfmt=",.3f")}

### Perfil de clusters (dev) [DATA]
{md_table(pr, floatfmt=",.2f")}

- Verificación: Σ share × tasa B = {mix:.4f}% = tasa B de dev {100 * b_.y_B.mean():.4f}% [DATA]. χ² cluster × y_B: p = {chi[1]:.3f} [DATA].
- UHNW con target B: 175 eventos en total y 122 en dev [DATA], por encima del mínimo de 100 del SPEC (pensado para A,
  con 79). Se aplica I-7 [DEF-default]: libro completo con `segment_uhnw` como variable; la pregunta de un scorecard UHNW
  propio con B se lleva a G2 (D7.2). `segment_uhnw` y `cluster` pasan como candidatas al paso 9.

## Tests
- `tests/test_step07.py` (ver pytest).

## Decisiones y preguntas abiertas
- D7.1–D7.2 en `reports/decision_log.md`.
"""
(REPORTS / "step07.md").write_text(rep, encoding="utf-8")
print(sel.round(3).to_string(index=False)); print(pr.iloc[:, [0, 1, 2, 3, 4, 5, 14, 15, 16, 17]].round(2).to_string(index=False)); print("chi2 p", chi[1])
