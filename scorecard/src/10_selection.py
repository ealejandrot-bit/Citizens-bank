"""Paso 10 · Selección de variables (solo desarrollo).

Embudo: IV ≥ 0.02 → exclusiones regulatorias → clustering de variables (jerárquico, promedio, sobre
1 − |Spearman| de los WoE; corte |ρ| > 0.6; representante = mayor IV, desempate menor missing) → VIF < 5 sobre WoE
(se elimina iterativamente el mayor VIF) → LASSO (L1) sobre WoE en la CV 5×5.
Regla de cierre (fijada antes de ver resultados, D10.3):
  frecuencia de selección ≥ 80% de los 25 folds en C_1SE, ≤ 3 variables por dimensión, 8–12 señales;
  si faltan, se completa por IV priorizando dimensiones sin representante; `segment` forzada (no cuenta en 8–12).
Revisión regulatoria (DM.2, D10.2): `age_primary` (fair lending) y `bureau_new_mortgage_elsewhere` (FCRA).
"""
from __future__ import annotations

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import FIGURES, MODELS, OUT, PARAMS, QC, TABLES, save_table, set_seed
from woe import load_sample, woe_frame

set_seed()
T = PARAMS["target_primary"]
dev = load_sample(OUT, TABLES)
y = dev[T].astype(int).to_numpy()
with open(MODELS / "09_binning.pkl", "rb") as fh:
    B = pickle.load(fh)
iv = pd.read_csv(TABLES / "09_iv_summary.csv").set_index("variable")
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
FORCED = ["segment"]
funnel = []


def cv_auc(cols, C=None, penalty=None):
    """AUC medio en los 25 folds (logística sobre WoE)."""
    Z = woe_frame(dev, B, cols).to_numpy()
    aucs = []
    for r, k in FOLDS:
        te = dev[f"cv_r{r}"].to_numpy() == k
        m = LogisticRegression(max_iter=2000) if penalty is None else LogisticRegression(penalty="l1", C=C, solver="liblinear", max_iter=2000)
        m.fit(Z[~te], y[~te])
        aucs.append(roc_auc_score(y[te], m.predict_proba(Z[te])[:, 1]))
    return float(np.mean(aucs)), float(np.std(aucs))


# ── 1. IV ────────────────────────────────────────────────────────────────────────────────
c1 = iv[iv.IV >= PARAMS["iv_min"]].index.tolist()
funnel.append({"etapa": "1. IV ≥ 0.02", "variables": len(c1), "salen": len(iv) - len(c1)})

# ── 2. Regulatorio ───────────────────────────────────────────────────────────────────────
W_all = woe_frame(dev, B, c1)
reg_rows = []
auc_base = cv_auc([c for c in c1 if c != "bureau_new_mortgage_elsewhere"])[0]
auc_with = cv_auc(c1)[0]
bt = pd.read_csv(TABLES / "09_woe_iv.csv").query("variable == 'bureau_new_mortgage_elsewhere'")
sd = bt[bt.bin == "sin_dato"].iloc[0]
reg_rows.append({"variable": "bureau_new_mortgage_elsewhere", "marco": "FCRA §604 (propósito permisible); DM.2",
                 "IV": iv.loc["bureau_new_mortgage_elsewhere", "IV"],
                 "evidencia": f"sin base legal documentada en la base; bin 'sin dato' (sin propósito permisible / sin aprobación) "
                              f"= {int(sd.hogares)} hogares, tasa {sd['tasa %']:.1f}%, WoE {sd.WoE:+.3f} ≠ 0 → la falta de permiso "
                              f"recibiría puntos de riesgo (proxy); ΔAUC CV por incluirla (sobre las 38) = {auc_with - auc_base:+.4f}",
                 "decisión": "fuera del campeón; modelo de sensibilidad en paso 11"})
age_iv = iv.loc["age_primary", "IV"]
reg_rows.append({"variable": "age_primary", "marco": "Fair lending (ECOA / Reg B si el score toca decisiones de crédito), UDAAP",
                 "IV": age_iv, "evidencia": f"IV {age_iv:.3f} < 0.02: sin poder predictivo; se revisa además que las seleccionadas no sean proxy de edad",
                 "decisión": "fuera por evidencia y por criterio regulatorio"})
c2 = [c for c in c1 if c != "bureau_new_mortgage_elsewhere"]
funnel.append({"etapa": "2. Exclusión regulatoria", "variables": len(c2), "salen": len(c1) - len(c2)})

# ── 3. Clustering de variables ───────────────────────────────────────────────────────────
W = W_all[c2]
R = W.corr(method="spearman").abs().fillna(0)
D = 1 - R.to_numpy()
np.fill_diagonal(D, 0)
Lk = linkage(squareform(D, checks=False), method="average")
cl = fcluster(Lk, t=1 - 0.6, criterion="distance")
miss_pct = {c: (100 * (dev[f"{c}__miss"] != "ok").mean() if f"{c}__miss" in dev else 0.0) for c in c2}
vc = pd.DataFrame({"variable": c2, "cluster_var": cl, "IV": [iv.loc[c, "IV"] for c in c2],
                   "% missing": [miss_pct[c] for c in c2], "dimensión": [iv.loc[c, "dimensión"] for c in c2]})
vc = vc.sort_values(["cluster_var", "IV", "% missing"], ascending=[True, False, True])
vc["representante"] = ~vc.duplicated("cluster_var")
vc["|ρ| máx con representante"] = [R.loc[v, vc[(vc.cluster_var == k) & vc.representante].variable.iloc[0]] for v, k in zip(vc.variable, vc.cluster_var)]
save_table(vc.round(4), "10_var_clusters")
c3 = vc[vc.representante].sort_values("IV", ascending=False).variable.tolist()
funnel.append({"etapa": "3. Clustering de variables (|ρ| > 0.6)", "variables": len(c3), "salen": len(c2) - len(c3)})

# ── 4. VIF sobre WoE ─────────────────────────────────────────────────────────────────────
c4 = list(c3)
vif_log = []
while True:
    V = W[c4].assign(const=1.0).to_numpy()
    vifs = pd.Series([variance_inflation_factor(V, i) for i in range(len(c4))], index=c4)
    if vifs.max() < PARAMS["vif_max"]:
        break
    drop = vifs.idxmax()
    vif_log.append({"elimina": drop, "VIF": vifs.max(), "IV": iv.loc[drop, "IV"]})
    c4.remove(drop)
vif_final = vifs.rename("VIF").reset_index().rename(columns={"index": "variable"}).sort_values("VIF", ascending=False)
save_table(vif_final.round(3), "10_vif_woe")
save_table(pd.DataFrame(vif_log, columns=["elimina", "VIF", "IV"]).round(3), "10_vif_drops")
funnel.append({"etapa": "4. VIF < 5 (WoE)", "variables": len(c4), "salen": len(c3) - len(c4)})

# ── 5. LASSO en CV 5×5 ───────────────────────────────────────────────────────────────────
Z = W[c4].to_numpy()
Cs = np.logspace(-3.5, 0, 22)
path, sel_count = [], {C: np.zeros(len(c4)) for C in Cs}
for C in Cs:
    aucs, nz = [], []
    for r, k in FOLDS:
        te = dev[f"cv_r{r}"].to_numpy() == k
        m = LogisticRegression(penalty="l1", C=C, solver="liblinear", max_iter=2000).fit(Z[~te], y[~te])
        aucs.append(roc_auc_score(y[te], m.predict_proba(Z[te])[:, 1]))
        nz.append((m.coef_[0] != 0).sum())
        sel_count[C] += (m.coef_[0] != 0)
    path.append({"C": C, "AUC medio": np.mean(aucs), "SE": np.std(aucs) / np.sqrt(len(aucs)), "variables (media)": np.mean(nz)})
path = pd.DataFrame(path)
best = path.loc[path["AUC medio"].idxmax()]
C_1se = float(path[path["AUC medio"] >= best["AUC medio"] - best["SE"]].C.min())
freq = pd.Series(sel_count[C_1se] / len(FOLDS), index=c4, name="frecuencia")
save_table(path.round(5), "10_lasso_path")

# ── 6. Regla de cierre ───────────────────────────────────────────────────────────────────
cand = pd.DataFrame({"variable": c4, "frecuencia L1 (C_1SE)": freq.values, "IV": [iv.loc[c, "IV"] for c in c4],
                     "dimensión": [iv.loc[c, "dimensión"] for c in c4]}).sort_values(["frecuencia L1 (C_1SE)", "IV"], ascending=False)
pool = cand[cand["frecuencia L1 (C_1SE)"] >= 0.80]


def close_rule(pool: pd.DataFrame, rest: pd.DataFrame, diversity_first: bool) -> list[str]:
    """Regla de cierre. v1 (inicial): orden por frecuencia L1 y luego IV. v2 (adoptada, D10.3): primero la variable
    de mayor IV de cada dimensión de señal / nivel, luego relleno por IV; ≤ 3 por dimensión; 8–12 señales."""
    chosen, per_dim = [], {}

    def add(r):
        chosen.append(r.variable)
        per_dim[r.dimensión] = per_dim.get(r.dimensión, 0) + 1

    order = pool.sort_values("IV", ascending=False) if diversity_first else pool
    if diversity_first:
        for _, r in order.iterrows():
            if r.dimensión != "estructura" and r.dimensión not in per_dim:
                add(r)
    for _, r in order.iterrows():
        if len(chosen) < 12 and r.variable not in chosen and per_dim.get(r.dimensión, 0) < 3:
            add(r)
    for prefer_new in (True, False):
        for _, r in rest.sort_values("IV", ascending=False).iterrows():
            if len(chosen) >= 8:
                break
            if r.variable in chosen or per_dim.get(r.dimensión, 0) >= 3 or (prefer_new and r.dimensión in per_dim):
                continue
            add(r)
    return chosen


chosen_v1 = close_rule(pool, cand[~cand.variable.isin(pool.variable)], diversity_first=False)
chosen = close_rule(pool, cand[~cand.variable.isin(pool.variable)], diversity_first=True)
final = chosen + FORCED
cand["seleccionada"] = cand.variable.isin(chosen)
cand["cierre v1"] = cand.variable.isin(chosen_v1)
save_table(cand.round(4), "10_lasso_selection")
funnel.append({"etapa": "5–6. LASSO C_1SE (≥ 80% folds) + regla de cierre", "variables": len(chosen), "salen": len(c4) - len(chosen)})
funnel.append({"etapa": "Final (+ segment forzada)", "variables": len(final), "salen": 0})
fun = pd.DataFrame(funnel)
save_table(fun, "10_selection_funnel")

# ── Rendimiento por etapa (CV 5×5, logística sin penalizar sobre WoE) ─────────────────────
perf = []
for lab, cols in [("38 con IV ≥ 0.02 (incl. buró)", c1), ("tras clustering", c3), ("tras VIF", c4),
                  ("cierre v1: orden por frecuencia (descartada)", chosen_v1 + FORCED),
                  ("final (campeón, cierre v2)", final), ("final + buró (sensibilidad)", final + ["bureau_new_mortgage_elsewhere"])]:
    a, s = cv_auc(cols)
    perf.append({"conjunto": lab, "variables": len(cols), "AUC CV 5×5": a, "sd": s})
perf = pd.DataFrame(perf)
save_table(perf.round(4), "10_performance_by_stage")

# Proxy de edad: Spearman de los WoE finales con age_primary
proxy = pd.DataFrame({"variable": final, "ρ Spearman WoE vs edad": [pd.Series(woe_frame(dev, B, [c])[c]).corr(dev.age_primary, method="spearman") for c in final]})
reg_rows.append({"variable": "(proxy de edad)", "marco": "Fair lending", "IV": np.nan,
                 "evidencia": f"|ρ| máx de las variables finales con edad = {proxy['ρ Spearman WoE vs edad'].abs().max():.3f} ({proxy.loc[proxy['ρ Spearman WoE vs edad'].abs().idxmax(), 'variable']})",
                 "decisión": "sin proxy relevante (|ρ| < 0.30)" if proxy["ρ Spearman WoE vs edad"].abs().max() < 0.30 else "REVISAR"})
reg = pd.DataFrame(reg_rows)
save_table(reg.round(4), "10_regulatory_review")
save_table(proxy.round(4), "10_age_proxy")

fv = pd.DataFrame({"variable": final, "dimensión": [iv.loc[c, "dimensión"] for c in final], "IV": [iv.loc[c, "IV"] for c in final],
                   "frecuencia L1": [freq.get(c, np.nan) for c in final], "VIF WoE": [vifs.get(c, np.nan) for c in final],
                   "forzada": [c in FORCED for c in final]})
fv.loc[fv.forzada, "VIF WoE"] = variance_inflation_factor(W_all.reindex(columns=c1).assign(segment=woe_frame(dev, B, ["segment"]).segment)[final].assign(const=1.0).to_numpy(), final.index("segment"))
save_table(fv.round(4), "10_final_vars")
(MODELS / "10_final_vars.json").write_text(json.dumps({"final": final, "forced": FORCED, "sensitivity_extra": ["bureau_new_mortgage_elsewhere"],
                                                       "C_1se": C_1se}, indent=2), encoding="utf-8")

# ── QC ──────────────────────────────────────────────────────────────────────────────────
qc = QC("10")
qc.check("Entre 8 y 12 señales + segment", 8 <= len(chosen) <= 12 and "segment" in final, "8–12 + segment", f"{len(chosen)} + segment")
qc.check("Ninguna prohibida ni excluida por regulación", not set(final) & {"bureau_new_mortgage_elsewhere", "age_primary", T, "multi_signal_count", "multi_signal_flag"}, "∅",
         sorted(set(final) & {"bureau_new_mortgage_elsewhere", "age_primary"}))
Vf = woe_frame(dev, B, final).assign(const=1.0).to_numpy()
vf = [variance_inflation_factor(Vf, i) for i in range(len(final))]
qc.check("VIF < 5 en el conjunto final (WoE)", max(vf) < PARAMS["vif_max"], "< 5", f"máx {max(vf):.2f}")
qc.check("≤ 3 variables por dimensión", max(pd.Series([iv.loc[c, 'dimensión'] for c in chosen]).value_counts()) <= 3, "≤ 3",
         pd.Series([iv.loc[c, "dimensión"] for c in chosen]).value_counts().to_dict())
ndim = len({iv.loc[c, "dimensión"] for c in chosen})
qc.check("Diversidad: ≥ 5 dimensiones de señal", ndim >= 5, "≥ 5", ndim, severity="warn")
pool_dims = {d for d in pool.dimensión if d != "estructura"}
miss_dims = pool_dims - {iv.loc[c, "dimensión"] for c in chosen}
qc.check("Toda dimensión con candidata estable está representada", not miss_dims, "∅", sorted(miss_dims))
loss = perf.set_index("conjunto").loc["38 con IV ≥ 0.02 (incl. buró)", "AUC CV 5×5"] - perf.set_index("conjunto").loc["final (campeón, cierre v2)", "AUC CV 5×5"]
qc.check("Pérdida de AUC final vs 38 variables ≤ 0.02", loss <= 0.02, "≤ 0.02", f"{loss:.4f}", severity="warn")
qc.check("Sin proxy de edad (|ρ| < 0.30)", proxy["ρ Spearman WoE vs edad"].abs().max() < 0.30, "< 0.30", f"{proxy['ρ Spearman WoE vs edad'].abs().max():.3f}")

# Figura: LASSO
INK, MUTED, GRID, BLUE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6"
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
ax = axes[0]
ax.errorbar(path.C, path["AUC medio"], yerr=path.SE, color=BLUE, lw=2, marker="o", ms=4, capsize=2)
ax.axvline(C_1se, color=MUTED, ls="--", lw=1)
ax.text(C_1se, path["AUC medio"].min(), " C_1SE", color=MUTED, fontsize=8)
ax.set_xscale("log")
ax.set_xlabel("C (inverso de la penalización L1)", color=MUTED)
ax.set_ylabel("AUC medio CV 5×5", color=MUTED)
ax.set_title("Ruta LASSO sobre WoE", loc="left", color=INK, fontsize=10)
ax2 = axes[1]
cs = cand.sort_values("frecuencia L1 (C_1SE)")
ax2.barh(cs.variable, 100 * cs["frecuencia L1 (C_1SE)"], color=[BLUE if s else "#a3a29c" for s in cs.seleccionada])
ax2.axvline(80, color=MUTED, ls="--", lw=1)
ax2.set_xlabel("% de los 25 folds con β ≠ 0 en C_1SE", color=MUTED)
ax2.set_title("Frecuencia de selección (azul = final)", loc="left", color=INK, fontsize=10)
ax2.tick_params(axis="y", labelsize=7)
for a in axes:
    a.grid(axis="x" if a is ax2 else "y", color=GRID, lw=0.8)
    a.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        a.spines[sp].set_visible(False)
    a.tick_params(colors=MUTED, length=0)
fig.suptitle("Selección por LASSO · desarrollo [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "10_lasso.png", dpi=140)

print(fun.to_string(index=False))
print("\n" + vc[vc.representante | (vc.groupby("cluster_var").variable.transform("size") > 1)].round(3).to_string(index=False))
print("\nVIF drops:", vif_log)
print(f"\nC_1SE = {C_1se:.4g}")
print(cand.round(3).to_string(index=False))
print("\n" + perf.round(4).to_string(index=False))
print("\n" + fv.round(3).to_string(index=False))
print("\n" + reg.to_string(index=False))
qc.gate()
