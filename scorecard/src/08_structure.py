"""Paso 8 · Correlación y diagnóstico de estructura (solo desarrollo).

- Spearman (pares con dato en ambas) sobre señales + share_of_wallet + derivada aum_outflow_to_rv_90d.
- Pares |ρ| > 0.6: se identifican, no se eliminan. Información incremental por par: AUC en CV (5 folds de cv_r1)
  de una logística sobre rangos normalizados (+ indicador de missing) con cada variable sola vs las dos juntas.
- VIF diagnóstico sobre rangos normalizados (missing → 0 = mediana, + indicadores). El VIF que decide es el de
  WoE en el paso 10; aquí solo se localiza la multicolinealidad.
- PCA diagnóstico (no entra en selección ni en modelo): varianza explicada, loadings, variables dominantes.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import FIGURES, OUT, PARAMS, QC, SEED, TABLES, save_table, set_seed

set_seed()
T = PARAMS["target_primary"]
X = pd.read_pickle(OUT / "data" / "05_features.pkl")
meta = pd.read_csv(OUT / "data" / "05_predictor_meta.csv").set_index("columna")
split = pd.read_csv(TABLES / "04_split.csv", usecols=["household_id", "muestra", "cv_r1"])
dev = X.merge(split, on="household_id").query("muestra == 'desarrollo'").reset_index(drop=True)
y = dev[T].astype(int).to_numpy()

SIG = [c for c in meta.index if meta.loc[c, "rol"] == "señal"] + ["share_of_wallet"]
S = dev[SIG].astype(float)

# ── Spearman ────────────────────────────────────────────────────────────────────────────
rho = S.corr(method="spearman", min_periods=200)
save_table(rho.round(3).reset_index().rename(columns={"index": "variable"}), "08_spearman")

pairs = []
for i, a in enumerate(SIG):
    for b in SIG[i + 1:]:
        r = rho.loc[a, b]
        if pd.notna(r) and abs(r) > 0.6:
            pairs.append((a, b, r))
EXPECTED = [("aum_outflow_90d", "aum_outflow_pct_90d"), ("transfer_to_competitor_bank_amount_90d", "transfer_to_competitor_pct_90d"),
            ("net_external_flow_pct_90d", "external_transfer_pct_of_balance_60d"),
            ("deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct"), ("share_of_wallet", "share_of_wallet_change")]


def rank_normal(s: pd.Series) -> np.ndarray:
    """Rango → normal estándar; NaN → 0 (mediana)."""
    r = s.rank(pct=True, method="average")
    z = norm.ppf(r.clip(0.5 / len(s), 1 - 0.5 / len(s)))
    return np.nan_to_num(z, nan=0.0)


RN = pd.DataFrame({c: rank_normal(S[c]) for c in SIG})
MISS = pd.DataFrame({f"{c}__na": S[c].isna().astype(float) for c in SIG if S[c].isna().mean() > 0.001})
folds = dev["cv_r1"].to_numpy()


def cv_auc(cols: list[str]) -> float:
    Z = pd.concat([RN[cols], MISS[[f"{c}__na" for c in cols if f"{c}__na" in MISS]]], axis=1).to_numpy()
    p = np.zeros(len(y))
    for k in range(5):
        tr, te = folds != k, folds == k
        p[te] = LogisticRegression(max_iter=1000).fit(Z[tr], y[tr]).predict_proba(Z[te])[:, 1]
    return roc_auc_score(y, p)


rows = []
all_pairs = {(a, b) for a, b, _ in pairs} | {tuple(sorted(p)) for p in EXPECTED}
for a, b in sorted({tuple(sorted(p)) for p in all_pairs}):
    r = rho.loc[a, b]
    auc_a, auc_b, auc_ab = cv_auc([a]), cv_auc([b]), cv_auc([a, b])
    best = a if auc_a >= auc_b else b
    rows.append({"var A": a, "var B": b, "ρ Spearman": r, "|ρ| > 0.6": abs(r) > 0.6,
                 "esperado (brief)": tuple(sorted((a, b))) in {tuple(sorted(p)) for p in EXPECTED},
                 "AUC A": auc_a, "AUC B": auc_b, "AUC A+B": auc_ab, "ΔAUC por agregar la otra": auc_ab - max(auc_a, auc_b),
                 "más informativa": best,
                 "lectura": "redundantes (Δ < 0.005)" if auc_ab - max(auc_a, auc_b) < 0.005 else "información incremental"})
pt = pd.DataFrame(rows).sort_values("ρ Spearman", key=lambda s: -s.abs())
save_table(pt.round(4), "08_high_corr_pairs")

# ── VIF diagnóstico ─────────────────────────────────────────────────────────────────────
V = RN.assign(const=1.0)
vif = pd.DataFrame({"variable": SIG, "VIF (rangos normalizados)": [variance_inflation_factor(V.to_numpy(), i) for i in range(len(SIG))]})
vif["> 5"] = vif["VIF (rangos normalizados)"] > PARAMS["vif_max"]
vif = vif.sort_values("VIF (rangos normalizados)", ascending=False)
save_table(vif.round(3), "08_vif")

# ── PCA diagnóstico ─────────────────────────────────────────────────────────────────────
Zs = (RN - RN.mean()) / RN.std()
pca = PCA(random_state=SEED).fit(Zs)
ev = pd.DataFrame({"PC": [f"PC{i + 1}" for i in range(len(SIG))], "varianza explicada %": 100 * pca.explained_variance_ratio_,
                   "acumulada %": 100 * np.cumsum(pca.explained_variance_ratio_), "autovalor": pca.explained_variance_})
save_table(ev.round(3), "08_pca_variance")
L = pd.DataFrame(pca.components_[:6].T, index=SIG, columns=[f"PC{i + 1}" for i in range(6)])
save_table(L.round(3).reset_index().rename(columns={"index": "variable"}), "08_pca_loadings")
dom = []
for pc in L.columns:
    top = L[pc].abs().sort_values(ascending=False).head(5)
    pscore = Zs.to_numpy() @ pca.components_[int(pc[2:]) - 1]
    dom.append({"PC": pc, "varianza %": ev.loc[int(pc[2:]) - 1, "varianza explicada %"],
                "variables dominantes (loading)": ", ".join(f"{v} ({L.loc[v, pc]:+.2f})" for v in top.index),
                "dimensiones": ", ".join(sorted({meta.loc[v, "dimensión"] for v in top.index})),
                "AUC del PC (diagnóstico)": max(roc_auc_score(y, pscore), 1 - roc_auc_score(y, pscore))})
dom = pd.DataFrame(dom)
save_table(dom.round(3), "08_pca_dominant")
n80 = int((ev["acumulada %"] < 80).sum() + 1)
kaiser = int((ev.autovalor > 1).sum())

# ── QC ──────────────────────────────────────────────────────────────────────────────────
qc = QC("08")
qc.check("Solo desarrollo", len(dev) == 13_913, 13_913, len(dev))
qc.check("Matriz Spearman simétrica, diagonal = 1", bool(np.allclose(rho.fillna(0), rho.fillna(0).T) and np.allclose(np.diag(rho), 1)), "sí", "sí")
miss_exp = [p for p in EXPECTED if not ((pt["var A"] == min(p)) & (pt["var B"] == max(p))).any()]
qc.check("Los 5 pares esperados evaluados", not miss_exp, 5, 5 - len(miss_exp))
qc.check("Ninguna variable eliminada en este paso", True, "identificar, no eliminar", f"{len(SIG)} variables siguen")
qc.check("Varianza PCA suma 100%", abs(ev["varianza explicada %"].sum() - 100) < 1e-6, "100%", f"{ev['varianza explicada %'].sum():.4f}%")
qc.check("VIF > 5 (diagnóstico; decide paso 10)", not vif["> 5"].any(), "0", vif.loc[vif["> 5"], "variable"].tolist(), severity="warn")

# ── Figuras ─────────────────────────────────────────────────────────────────────────────
INK, MUTED, GRID, BLUE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6"
div = mcolors.LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f2f1ed", "#e34948"])
order = [c for d in meta.loc[SIG, "dimensión"].unique() for c in SIG if meta.loc[c, "dimensión"] == d]
R = rho.loc[order, order]
fig, ax = plt.subplots(figsize=(12, 10.5))
im = ax.imshow(R, cmap=div, vmin=-1, vmax=1)
ax.set_xticks(range(len(order)), order, rotation=90, fontsize=7, color=INK)
ax.set_yticks(range(len(order)), [f"{c}  · {meta.loc[c, 'dimensión'][:14]}" for c in order], fontsize=7, color=INK)
for i in range(len(order)):
    for j in range(len(order)):
        if i != j and pd.notna(R.iat[i, j]) and abs(R.iat[i, j]) > 0.6:
            ax.text(j, i, f"{R.iat[i, j]:.2f}", ha="center", va="center", fontsize=5.5, color="white")
ax.tick_params(length=0)
for sp in ax.spines.values():
    sp.set_visible(False)
cb = fig.colorbar(im, ax=ax, shrink=0.6)
cb.set_label("ρ Spearman", color=MUTED)
ax.set_title("Spearman entre señales, ordenado por dimensión · desarrollo [DATA-SINT] (se rotula |ρ| > 0.6)",
             loc="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "08_spearman_heatmap.png", dpi=130)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.4))
ax.bar(range(1, len(ev) + 1), ev["varianza explicada %"], color=BLUE, width=0.75)
ax2 = ax.twinx()  # misma unidad (%), no es doble escala de medidas distintas
ax2.plot(range(1, len(ev) + 1), ev["acumulada %"], color=INK, lw=1.5)
ax2.set_ylim(0, 100)
ax.set_ylim(0, 100 * ev["varianza explicada %"].max() / 100 * 1.15)
ax.set_xlabel("componente", color=MUTED)
ax.set_ylabel("varianza explicada %", color=MUTED)
ax2.set_ylabel("acumulada %", color=MUTED)
ax.set_title(f"PCA diagnóstico sobre {len(SIG)} señales · {n80} componentes para 80% · Kaiser = {kaiser} [DATA-SINT]",
             loc="left", color=INK, fontsize=10)
for a in (ax, ax2):
    for sp in ("top", "right", "left"):
        a.spines[sp].set_visible(False)
    a.tick_params(colors=MUTED, length=0)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(FIGURES / "08_pca_scree.png", dpi=140)

print(pt.round(3).to_string(index=False))
print("\n" + vif.head(12).round(2).to_string(index=False))
print("\n" + dom.round(3).to_string(index=False))
print(f"\nComponentes para 80%: {n80} · Kaiser: {kaiser} · PC1 {ev.iloc[0, 1]:.1f}%")
qc.gate()
