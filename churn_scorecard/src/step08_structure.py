"""Paso 8 · Correlación y diagnóstico de estructura (dev, target B).

- Pearson y Spearman (pares con dato en ambas, mín. 200) entre candidatas numéricas (+ compuestos, informativo).
- Pares |ρ| > 0.6: decisión = cuál aporta información incremental: IV preliminar (paso 6) y ΔAUC en CV (5 folds de
  cv_r1) de una logística sobre rangos normalizados + indicador de missing con las dos vs la mejor sola. Nada se elimina
  aquí: la decisión final es del paso 10.
- VIF diagnóstico sobre rangos normalizados (missing → 0).
- PCA por bloques (depósitos, salidas de AUM, externalización): varianza explicada y loadings. No entra al modelo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import COMPOSITES, REPORTS, TABLES, candidates, load_split, md_table, save_table, set_seed

set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
C = candidates(include_composites=True)
X = D[C].astype(float)
iv = pd.read_csv(TABLES / "step06_univariate_B.csv").set_index("variable")["IV preliminar"]

sp = X.corr(method="spearman", min_periods=200)
pe = X.corr(method="pearson", min_periods=200)
save_table(sp.round(4).reset_index().rename(columns={"index": "variable"}), "step08_spearman")
save_table(pe.round(4).reset_index().rename(columns={"index": "variable"}), "step08_pearson")


def rank_normal(s):
    r = s.rank(pct=True)
    return np.nan_to_num(norm.ppf(r.clip(0.5 / len(s), 1 - 0.5 / len(s))), nan=0.0)


RN = pd.DataFrame({c: rank_normal(X[c]) for c in C})
NA = pd.DataFrame({c: X[c].isna().astype(float) for c in C})
folds = D.cv_r1.to_numpy()


def cv_auc(cols):
    Z = np.column_stack([RN[cols].to_numpy()] + [NA[[c]].to_numpy() for c in cols if NA[c].sum() > 0])
    p = np.zeros(len(y))
    for k in range(5):
        tr, te = folds != k, folds == k
        p[te] = LogisticRegression(max_iter=2000).fit(Z[tr], y[tr]).predict_proba(Z[te])[:, 1]
    return roc_auc_score(y, p)


rows = []
for i, a in enumerate(C):
    for b in C[i + 1:]:
        r_s, r_p = sp.loc[a, b], pe.loc[a, b]
        if pd.notna(r_s) and (abs(r_s) > 0.6 or abs(r_p) > 0.6):
            aa, ab, aab = cv_auc([a]), cv_auc([b]), cv_auc([a, b])
            best = a if iv[a] >= iv[b] else b
            rows.append({"var A": a, "var B": b, "Spearman": r_s, "Pearson": r_p, "IV A": iv[a], "IV B": iv[b], "AUC A": aa, "AUC B": ab,
                         "AUC A+B": aab, "ΔAUC por agregar la otra": aab - max(aa, ab), "mayor IV": best,
                         "decisión": ("redundantes: queda la de mayor IV" if aab - max(aa, ab) < 0.005 else "información incremental: ambas pasan al paso 10")
                         + (" (compuesto: solo challenger)" if a in COMPOSITES or b in COMPOSITES else "")})
pairs = pd.DataFrame(rows).sort_values("Spearman", key=lambda s: -s.abs())
save_table(pairs, "step08_pairs")

NC = [c for c in C if c not in COMPOSITES]
V = RN[NC].assign(const=1.0).to_numpy()
vif = pd.DataFrame({"variable": NC, "VIF (rangos normalizados)": [variance_inflation_factor(V, i) for i in range(len(NC))]}).sort_values("VIF (rangos normalizados)", ascending=False)
save_table(vif, "step08_vif")

BLOCKS = {
    "depósitos": ["deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct", "net_deposit_flow_pct_90d", "net_deposit_flow_pct_90d_peer", "recurring_deposit_change_pct"],
    "salidas de AUM": ["aum_outflow_90d", "aum_outflow_pct_90d", "aum_outflow_pct_90d_peer", "investment_redemption_pct", "positions_liquidated_pct", "aum_vs_baseline_pct", "cash_pct_of_portfolio_chg"],
    "externalización": ["external_transfer_pct_of_balance_60d", "new_external_destinations_90d", "transfer_to_competitor_pct_90d",
                        "transfer_to_competitor_bank_amount_90d", "external_transfer_acceleration", "net_external_flow_pct_90d",
                        "external_destination_concentration", "outflow_vs_baseline_pct", "competitor_x_new_destinations"],
}
pca_rows, load_rows = [], []
for blk, cols in BLOCKS.items():
    Zb = RN[cols]
    Zb = (Zb - Zb.mean()) / Zb.std()
    p = PCA().fit(Zb)
    ev = p.explained_variance_ratio_
    pca_rows.append({"bloque": blk, "variables": len(cols), "PC1 %": 100 * ev[0], "PC1+PC2 %": 100 * ev[:2].sum(),
                     "componentes para 80%": int(np.searchsorted(np.cumsum(ev), 0.80) + 1), "autovalores > 1": int((p.explained_variance_ > 1).sum())})
    for j, c in enumerate(cols):
        load_rows.append({"bloque": blk, "variable": c, "loading PC1": p.components_[0][j], "loading PC2": p.components_[1][j]})
pca = pd.DataFrame(pca_rows)
loads = pd.DataFrame(load_rows)
save_table(pca, "step08_pca_blocks")
save_table(loads, "step08_pca_loadings")

rep = f"""# Paso 8 · Correlación y diagnóstico de estructura

## Objetivo
- Identificar redundancias entre candidatas y decidir cuál aporta información incremental, antes de seleccionar.

## Método
- Pearson y Spearman en dev (target B); pares con |ρ| > 0.6 en cualquiera de las dos.
- Información incremental: ΔAUC (CV 5 folds, logística sobre rangos normalizados + indicador de missing) de agregar la
  otra variable; < 0.005 = redundantes. IV del paso 6 como desempate.
- VIF sobre rangos normalizados (diagnóstico; el VIF que decide es sobre WoE, paso 10). PCA por bloque: solo diagnóstico.

## Código
- `src/step08_structure.py` · `tests/test_step08.py` · `step08_spearman.csv`, `step08_pearson.csv`, `step08_pairs.csv`,
  `step08_vif.csv`, `step08_pca_blocks.csv`, `step08_pca_loadings.csv`.

## Resultados

### Pares con |ρ| > 0.6 y decisión [DATA]
{md_table(pairs[['var A', 'var B', 'Spearman', 'Pearson', 'IV A', 'IV B', 'ΔAUC por agregar la otra', 'mayor IV', 'decisión']], floatfmt=",.3f")}

- {len(pairs)} pares [DATA]; {int(pairs['decisión'].str.startswith('redundantes').sum())} redundantes y {int(pairs['decisión'].str.startswith('información').sum())} con información incremental.
- El par RV–AUM (G0-a) aparece por construcción: RV = AUM + depósitos.

### VIF (top 12, rangos normalizados) [DATA]
{md_table(vif.head(12), floatfmt=",.2f")}

### PCA por bloque (diagnóstico) [DATA]
{md_table(pca, floatfmt=",.1f")}

- VIF infinito o muy alto por identidades exactas de construcción [DATA]: `log_rv` y `relationship_value` (mismo orden),
  `aum_share` + `deposit_share` = 1 (RV = AUM + depósitos), `n_streams_eligible` = suma de 3 `has_*`, variables base y su
  `_peer` dentro de celda. Se resuelve en el paso 10 (un representante por cluster de variables; VIF < 5 sobre WoE).
- PCA no entra en selección ni en modelo (SPEC D.5).

## Tests
- `tests/test_step08.py` (ver pytest).

## Decisiones y preguntas abiertas
- D8.1 en `reports/decision_log.md`.
"""
(REPORTS / "step08.md").write_text(rep, encoding="utf-8")
print(pairs[["var A", "var B", "Spearman", "ΔAUC por agregar la otra", "decisión"]].round(3).to_string(index=False)); print(vif.head(10).round(2).to_string(index=False)); print(pca.round(1).to_string(index=False))
