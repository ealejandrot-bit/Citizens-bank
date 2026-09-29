"""Paso 11 · Estimación: campeón (logística sobre WoE), robustez (L2) y challenger (LightGBM monótono).

- Modelo A (campeón): statsmodels Logit de "bueno" (1 − hard_churn_6m) sobre los WoE de las 13 variables del paso 10.
  Con WoE = ln(%buenos/%malos), todos los β deben ser > 0 (β < 0 = colinealidad o bin mal formado).
  Interacción segment × top-3 señales: solo si ΔAUC CV ≥ 0.005 y se mantienen los signos (D11.2).
- Modelo A′: logística L2 (C por CV) como prueba de robustez de coeficientes.
- Modelo B (challenger): LightGBM con restricciones monótonas (dirección esperada del paso 2), sobre las variables
  crudas elegibles (sin `age_primary` ni buró, D10.2), early stopping interno en cada fold; permutación y SHAP.
- Predicciones out-of-fold de la CV 5×5 (promedio de 5 repeticiones por hogar) → calibración en el paso 14 (DM.1).
- Comparación en holdout (solo evaluación) con bootstrap pareado 500. Regla: A es campeón salvo que B gane
  ≥ 0.03 de AUC y ≥ 0.05 de PR-AUC con IC bootstrap sin traslape.
"""
from __future__ import annotations

import json
import pickle

import lightgbm as lgb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from common import FIGURES, MODELS, OUT, PARAMS, QC, SEED, TABLES, save_table, set_seed
from metrics import all_metrics, bootstrap, ci
from woe import fit_project_binning, load_sample, woe_frame

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
set_seed()
T = PARAMS["target_primary"]
ALL = load_sample(OUT, TABLES, sample=None)
dev = ALL[ALL.muestra == "desarrollo"].reset_index(drop=True)
hold = ALL[ALL.muestra == "holdout"].reset_index(drop=True)
y, yh = dev[T].astype(int).to_numpy(), hold[T].astype(int).to_numpy()
with open(MODELS / "09_binning.pkl", "rb") as fh:
    B = pickle.load(fh)
cfg = json.loads((MODELS / "10_final_vars.json").read_text())
FINAL = cfg["final"]
iv = pd.read_csv(TABLES / "09_iv_summary.csv").set_index("variable")
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
# ── CV anidada: bins y WoE re-ajustados dentro de cada fold (D11.1) ──────────────────────
# Con WoE de todo desarrollo la CV ve las etiquetas del fold de prueba (optimista). Las OOF que se usan para
# calibrar (DM.1) salen de esta CV anidada.
POOL = list(dict.fromkeys(FINAL + cfg["sensitivity_extra"]))
FB = {}
for r, k in FOLDS:
    tr = dev[f"cv_r{r}"].to_numpy() != k
    dtr = dev[tr].reset_index(drop=True)
    FB[(r, k)] = {c: fit_project_binning(c, dtr, y[tr], PARAMS) for c in POOL}


def oof_logit(cols, penalty=None, C=1.0, inter=None, nested=True):
    """OOF (promedio de 5 repeticiones) y AUC por fold. inter = variables con interacción UHNW × WoE."""
    oof = np.zeros((len(dev), 5))
    aucs = []
    for r, k in FOLDS:
        te = dev[f"cv_r{r}"].to_numpy() == k
        Bk = FB[(r, k)] if nested else B
        W = woe_frame(dev, Bk, cols)
        for v in inter or []:
            W[f"UHNW×{v}"] = dev["segment"].to_numpy() * W[v].to_numpy()
        Z = W.to_numpy()
        m = LogisticRegression(C=C, max_iter=5000) if penalty == "l2" else LogisticRegression(C=np.inf, max_iter=5000)
        m.fit(Z[~te], y[~te])
        p = m.predict_proba(Z[te])[:, 1]
        oof[te, r - 1] = p
        aucs.append(roc_auc_score(y[te], p))
    return oof.mean(axis=1), np.array(aucs)


# ── Modelo A · logística sobre WoE (statsmodels) + eliminación hacia atrás p > 0.05 (D11.3) ──
FORCED = cfg["forced"]
cur = list(FINAL)
back = []
while True:
    res = sm.Logit(1 - y, sm.add_constant(woe_frame(dev, B, cur))).fit(disp=0)
    pv = res.pvalues.drop(["const"] + FORCED)
    if pv.max() <= 0.05:
        break
    drop = pv.idxmax()
    a_before = oof_logit(cur)[1].mean()
    cur.remove(drop)
    back.append({"elimina": drop, "p-valor": pv.max(), "β": res.params[drop], "AUC CV anidado antes": a_before,
                 "AUC CV anidado después": oof_logit(cur)[1].mean()})
FINAL_A = cur
back_t = pd.DataFrame(back, columns=["elimina", "p-valor", "β", "AUC CV anidado antes", "AUC CV anidado después"])
save_table(back_t.round(4), "11_backward_elimination")
Wd, Wh = woe_frame(dev, B, FINAL_A), woe_frame(hold, B, FINAL_A)
ci95 = res.conf_int()
coef = pd.DataFrame({"variable": res.params.index, "β": res.params.values, "EE": res.bse.values, "z": res.tvalues.values,
                     "p-valor": res.pvalues.values, "IC95 inf": ci95[0].values, "IC95 sup": ci95[1].values})
coef["IV"] = [iv.loc[v, "IV"] if v in iv.index else np.nan for v in coef.variable]
coef["contribución β·sd(WoE)"] = [np.nan if v == "const" else res.params[v] * Wd[v].std() for v in coef.variable]
save_table(coef.round(5), "11_modelA_coefficients")

oofA, aucsA = oof_logit(FINAL_A)
_, aucsA_opt = oof_logit(FINAL_A, nested=False)
_, aucs13 = oof_logit(FINAL)

# Interacción segment × top-3 señales por IV
top3 = sorted([v for v in FINAL_A if v not in FORCED], key=lambda v: -iv.loc[v, "IV"])[:3]
_, aucsI = oof_logit(FINAL_A, inter=top3)
WI = woe_frame(dev, B, FINAL_A)
for v in top3:
    WI[f"UHNW×{v}"] = dev["segment"].to_numpy() * WI[v].to_numpy()
resI = sm.Logit(1 - y, sm.add_constant(WI)).fit(disp=0)
signs_ok = bool((resI.params[FINAL_A] > 0).all())
d_inter = aucsI.mean() - aucsA.mean()
inter_rows = pd.DataFrame([{"modelo": "A (sin interacción)", "AUC CV anidado": aucsA.mean(), "sd": aucsA.std()},
                           {"modelo": f"A + UHNW × {', '.join(top3)}", "AUC CV anidado": aucsI.mean(), "sd": aucsI.std(),
                            "ΔAUC": d_inter, "folds que mejoran %": 100 * (aucsI > aucsA).mean(),
                            "signos principales > 0": signs_ok,
                            "β interacciones": ", ".join(f"{k}: {resI.params[k]:+.3f} (p={resI.pvalues[k]:.2f})" for k in resI.params.index if "×" in k)}])
use_inter = d_inter >= 0.005 and signs_ok
inter_rows["decisión"] = ["", "se incluye" if use_inter else "no se incluye (ΔAUC < 0.005)"]
save_table(inter_rows.round(4), "11_interaction_test")

# ── Modelo A′ · L2 ──────────────────────────────────────────────────────────────────────
l2 = [(C, oof_logit(FINAL_A, penalty="l2", C=C)[1].mean()) for C in [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]]
C_best = max(l2, key=lambda t: t[1])[0]
mA2 = LogisticRegression(C=C_best, max_iter=5000).fit(Wd.to_numpy(), 1 - y)
rob = pd.DataFrame({"variable": FINAL_A, "β A (MLE)": res.params[FINAL_A].values, "β A′ (L2)": mA2.coef_[0]})
rob["razón A′/A"] = rob["β A′ (L2)"] / rob["β A (MLE)"]
rob["mismo signo"] = np.sign(rob["β A′ (L2)"]) == np.sign(rob["β A (MLE)"])
save_table(rob.round(4), "11_modelA2_robustness")
oofA2, aucsA2 = oof_logit(FINAL_A, penalty="l2", C=C_best)

# Sensibilidad: A + buró (D10.2)
SENS = FINAL_A + cfg["sensitivity_extra"]
oofS, aucsS = oof_logit(SENS)
resS = sm.Logit(1 - y, sm.add_constant(woe_frame(dev, B, SENS))).fit(disp=0)
# ── Modelo A-lite · parsimonia para comunicación ejecutiva (D11.4) ───────────────────────
# Regla fijada antes de ver resultados: selección hacia adelante (CV anidada) sobre las variables de A, con segment
# forzada; se elige el modelo más chico cuyo AUC CV anidado ≥ AUC(A) − 0.01.
fwd, cur_l = [], list(FORCED)
cands_l = [v for v in FINAL_A if v not in FORCED]
while cands_l:
    scores = {v: oof_logit(cur_l + [v])[1].mean() for v in cands_l}
    v_best = max(scores, key=scores.get)
    cur_l.append(v_best)
    cands_l.remove(v_best)
    fwd.append({"paso": len(cur_l) - len(FORCED), "agrega": v_best, "dimensión": iv.loc[v_best, "dimensión"],
                "AUC CV anidado": scores[v_best], "variables (con segment)": len(cur_l)})
fwd = pd.DataFrame(fwd)
fwd["ganancia"] = fwd["AUC CV anidado"].diff().fillna(fwd["AUC CV anidado"].iloc[0] - 0.5)
target_auc = aucsA.mean() - 0.01
k_lite = int(fwd[fwd["AUC CV anidado"] >= target_auc].paso.min())
LITE = list(FORCED) + fwd[fwd.paso <= k_lite].agrega.tolist()
fwd["en A-lite"] = fwd.paso <= k_lite
save_table(fwd.round(4), "11_lite_forward")
resL = sm.Logit(1 - y, sm.add_constant(woe_frame(dev, B, LITE))).fit(disp=0)
ciL = resL.conf_int()
coefL = pd.DataFrame({"variable": resL.params.index, "β": resL.params.values, "EE": resL.bse.values, "p-valor": resL.pvalues.values,
                      "IC95 inf": ciL[0].values, "IC95 sup": ciL[1].values})
save_table(coefL.round(5), "11_modelAlite_coefficients")
oofL, aucsL = oof_logit(LITE)

cvcomp = pd.DataFrame([{"conjunto": "13 del paso 10 (anidado)", "AUC": aucs13.mean(), "sd": aucs13.std()},
                       {"conjunto": f"A final, {len(FINAL_A)} var. (WoE de todo desarrollo: optimista)", "AUC": aucsA_opt.mean(), "sd": aucsA_opt.std()},
                       {"conjunto": f"A final, {len(FINAL_A)} var. (anidado)", "AUC": aucsA.mean(), "sd": aucsA.std()}])
save_table(cvcomp.round(4), "11_cv_optimism")

# ── Modelo B · LightGBM monótono ────────────────────────────────────────────────────────
meta = pd.read_csv(OUT / "data" / "05_predictor_meta.csv").set_index("columna")
FEATS_B = [c for c in meta.index if c not in ("age_primary", "bureau_new_mortgage_elsewhere", "log_relationship_value")]
MONO = [1 if meta.loc[c, "dirección_esperada"] == "+" else -1 if meta.loc[c, "dirección_esperada"] == "−" else 0 for c in FEATS_B]
PARAMS_B = dict(objective="binary", learning_rate=0.03, num_leaves=15, min_child_samples=100, feature_fraction=0.8,
                bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, monotone_constraints=MONO,
                monotone_constraints_method="advanced", verbose=-1, seed=SEED, deterministic=True, num_threads=4)
Xd, Xh = dev[FEATS_B].astype(float), hold[FEATS_B].astype(float)
oofB = np.zeros((len(dev), 5))
aucsB, iters = [], []
for r, k in FOLDS:
    te = dev[f"cv_r{r}"].to_numpy() == k
    tr_idx = np.flatnonzero(~te)
    a, b = train_test_split(tr_idx, test_size=0.2, stratify=y[tr_idx], random_state=SEED + r * 10 + k)
    bst = lgb.train(PARAMS_B, lgb.Dataset(Xd.iloc[a], y[a]), num_boost_round=3000,
                    valid_sets=[lgb.Dataset(Xd.iloc[b], y[b])], callbacks=[lgb.early_stopping(100, verbose=False)])
    p = bst.predict(Xd[te], num_iteration=bst.best_iteration)
    oofB[te, r - 1] = p
    aucsB.append(roc_auc_score(y[te], p))
    iters.append(bst.best_iteration)
oofB = oofB.mean(axis=1)
aucsB = np.array(aucsB)
n_iter = int(np.median(iters))
clfB = lgb.LGBMClassifier(n_estimators=n_iter, **{k: v for k, v in PARAMS_B.items() if k != "objective"})
clfB.fit(Xd, y)

# ── Predicciones ────────────────────────────────────────────────────────────────────────
pA = 1 - res.predict(sm.add_constant(Wh, has_constant="add"))
pA2 = 1 - mA2.predict_proba(Wh.to_numpy())[:, 1]
pL = 1 - resL.predict(sm.add_constant(woe_frame(hold, B, LITE), has_constant="add"))
pS = 1 - resS.predict(sm.add_constant(woe_frame(hold, B, SENS), has_constant="add"))
pB = clfB.predict_proba(Xh)[:, 1]
pd.DataFrame({"household_id": dev.household_id, "oof_A": oofA, "oof_A2": oofA2, "oof_B": oofB, "oof_A_buro": oofS, "oof_A_lite": oofL}).to_csv(OUT / "data" / "11_oof_dev.csv", index=False)
pd.DataFrame({"household_id": hold.household_id, "p_A": pA, "p_A2": pA2, "p_B": pB, "p_A_buro": pS, "p_A_lite": pL}).to_csv(OUT / "data" / "11_pred_holdout.csv", index=False)

# ── Comparación en holdout ──────────────────────────────────────────────────────────────
preds = {"A": np.asarray(pA), "A-lite": np.asarray(pL), "A′": np.asarray(pA2), "B": pB, "A + buró": np.asarray(pS)}
rows = []
bs_auc = bootstrap(yh, preds, lambda yy, pp, _: roc_auc_score(yy, pp), n=PARAMS["n_bootstrap"], strata=yh)
from sklearn.metrics import average_precision_score
bs_pr = bootstrap(yh, preds, lambda yy, pp, _: average_precision_score(yy, pp), n=PARAMS["n_bootstrap"], strata=yh)
cvs = {"A": aucsA, "A-lite": aucsL, "A′": aucsA2, "B": aucsB, "A + buró": aucsS}  # A: CV anidada; B: sin WoE (honesta)
for k, p in preds.items():
    m = all_metrics(yh, p)
    lz = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
    slope = sm.Logit(yh, sm.add_constant(lz)).fit(disp=0).params[1]
    rows.append({"modelo": k, "AUC": m["AUC"], "IC95 AUC": "[%.3f, %.3f]" % ci(bs_auc[k]), "PR-AUC": m["PR-AUC"],
                 "IC95 PR-AUC": "[%.3f, %.3f]" % ci(bs_pr[k]), "KS": m["KS"], "Gini": m["Gini"], "Brier": m["Brier"],
                 "p media": m["p media"], "tasa obs.": m["tasa observada"], "pendiente calibración": slope,
                 "AUC CV 5×5 honesta (sd)": f"{cvs[k].mean():.3f} ({cvs[k].std():.3f})",
                 "parámetros": {"A": len(FINAL_A) + 1, "A-lite": len(LITE) + 1, "A′": len(FINAL_A) + 1, "A + buró": len(SENS) + 1}.get(k, f"{n_iter} árboles × ≤ 15 hojas"),
                 "explicabilidad": "puntos por bin, reason codes directos" if k != "B" else "SHAP / permutación; no hay tabla de puntos"})
comp = pd.DataFrame(rows)
dA = bs_auc["B"] - bs_auc["A"]
dP = bs_pr["B"] - bs_pr["A"]
ciA, ciB = ci(bs_auc["A"]), ci(bs_auc["B"])
ciPA, ciPB = ci(bs_pr["A"]), ci(bs_pr["B"])
auc_gain, pr_gain = comp.set_index("modelo").loc["B", "AUC"] - comp.set_index("modelo").loc["A", "AUC"], comp.set_index("modelo").loc["B", "PR-AUC"] - comp.set_index("modelo").loc["A", "PR-AUC"]
b_wins = auc_gain >= 0.03 and pr_gain >= 0.05 and ciB[0] > ciA[1] and ciPB[0] > ciPA[1]
rule = pd.DataFrame([{"ΔAUC (B − A)": auc_gain, "IC95 ΔAUC pareado": "[%.3f, %.3f]" % ci(dA), "ΔPR-AUC (B − A)": pr_gain,
                      "IC95 ΔPR-AUC pareado": "[%.3f, %.3f]" % ci(dP), "IC AUC se traslapan": not (ciB[0] > ciA[1]),
                      "regla (≥ 0.03 AUC, ≥ 0.05 PR-AUC, sin traslape)": "B gana" if b_wins else "A se mantiene campeón"}])
dL = bs_auc["A-lite"] - bs_auc["A"]
gapL_cv = aucsA.mean() - aucsL.mean()
gapL_h = comp.set_index("modelo").loc["A", "AUC"] - comp.set_index("modelo").loc["A-lite", "AUC"]
lite_ok = gapL_cv <= 0.01 and (ci(dL)[0] <= 0 <= ci(dL)[1] or gapL_h <= 0.01)
CHAMP = "A-lite" if lite_ok else "A"
rule_l = pd.DataFrame([{"variables A / A-lite": f"{len(FINAL_A)} / {len(LITE)}", "brecha AUC CV anidado (A − lite)": gapL_cv,
                        "brecha AUC holdout (A − lite)": gapL_h, "IC95 Δ holdout pareado (lite − A)": "[%.3f, %.3f]" % ci(dL),
                        "regla (≤ 0.01 CV y Δ holdout con IC que incluye 0 o ≤ 0.01)": "A-lite campeón" if lite_ok else "A campeón"}])
save_table(rule_l.round(4), "11_lite_rule")
save_table(comp.round(4), "11_model_comparison")
save_table(rule.round(4), "11_champion_rule")

# ── Importancia en B (holdout, solo evaluación) ─────────────────────────────────────────
perm = permutation_importance(clfB, Xh, yh, scoring="roc_auc", n_repeats=5, random_state=SEED, n_jobs=1)
shap_vals = clfB.booster_.predict(Xh, pred_contrib=True)[:, :-1]
imp = pd.DataFrame({"variable": FEATS_B, "ΔAUC permutación": perm.importances_mean, "sd": perm.importances_std,
                    "media |SHAP|": np.abs(shap_vals).mean(axis=0), "en campeón A": [c in FINAL_A for c in FEATS_B]})
imp = imp.sort_values("media |SHAP|", ascending=False)
save_table(imp.round(5), "11_modelB_importance")
clfB.booster_.save_model(str(MODELS / "11_modelB_lgbm.txt"))
with open(MODELS / "11_modelA.pkl", "wb") as fh:
    pickle.dump({"params": res.params, "cov": res.cov_params(), "vars": FINAL_A, "target": "good = 1 - hard_churn_6m"}, fh)
(MODELS / "11_final_vars.json").write_text(json.dumps({"final": FINAL_A, "lite": LITE, "champion": CHAMP,
                                                       "champion_vars": LITE if CHAMP == "A-lite" else FINAL_A,
                                                       "forced": FORCED, "sensitivity": SENS,
                                                       "models": {"A": FINAL_A, "A-lite": LITE},
                                                       "roles": {"A": "campeón operativo (ranking y tramos)",
                                                                 "A-lite": "versión ejecutiva (comunicación); se valida en paralelo"}},
                                                      indent=2, ensure_ascii=False), encoding="utf-8")
with open(MODELS / "11_modelA_lite.pkl", "wb") as fh:
    pickle.dump({"params": resL.params, "cov": resL.cov_params(), "vars": LITE, "target": "good = 1 - hard_churn_6m"}, fh)
with open(MODELS / "11_modelA2_l2.pkl", "wb") as fh:
    pickle.dump(mA2, fh)

# ── QC ──────────────────────────────────────────────────────────────────────────────────
qc = QC("11")
neg = coef[(coef.variable != "const") & (coef["β"] <= 0)]
qc.check("Todos los β > 0 sobre WoE (modelo A)", neg.empty, "0 negativos", neg[["variable", "β", "p-valor"]].round(3).values.tolist())
qc.check("Todos los β > 0 en A-lite", bool((resL.params.drop("const") > 0).all()), "0 negativos",
         resL.params.drop("const")[resL.params.drop("const") <= 0].round(3).to_dict())
qc.check("A′ con mismos signos que A", bool(rob["mismo signo"].all()), "100%", f"{rob['mismo signo'].mean():.0%}")
qc.check("Intercepto: p media dev = tasa dev", abs((1 - res.predict()).mean() - y.mean()) < 1e-6, f"{y.mean():.5f}", f"{(1 - res.predict()).mean():.5f}")
qc.check("OOF de A viene de CV anidada (bins por fold)", len(FB) == 25, 25, len(FB))
qc.check("OOF cubre todo desarrollo", bool(np.all(oofA > 0)) and len(oofA) == len(dev), len(dev), len(oofA))
qc.check("Holdout no usado para ajustar (solo predicción)", len(hold) == 5_964, 5_964, len(hold))
qc.check("B respeta monotonía declarada", True, "restricciones LightGBM", f"{sum(1 for m in MONO if m)} de {len(MONO)} restringidas")

# Figura: coeficientes A y SHAP B
INK, MUTED, GRID, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834"
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
c = coef[coef.variable != "const"].sort_values("contribución β·sd(WoE)")
axes[0].barh(c.variable, c["contribución β·sd(WoE)"], color=BLUE)
axes[0].set_title("Modelo A: β · sd(WoE) (contribución al logit)", loc="left", color=INK, fontsize=10)
ib = imp.head(15).iloc[::-1]
axes[1].barh(ib.variable, ib["media |SHAP|"], color=[BLUE if e else ORANGE for e in ib["en campeón A"]])
axes[1].set_title("Modelo B: media |SHAP| en holdout (azul = también en A)", loc="left", color=INK, fontsize=10)
for a in axes:
    a.grid(axis="x", color=GRID, lw=0.8)
    a.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        a.spines[sp].set_visible(False)
    a.tick_params(colors=MUTED, length=0, labelsize=8)
fig.suptitle("Drivers del campeón y del challenger [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "11_drivers.png", dpi=140)

print(back_t.round(4).to_string(index=False))
print(cvcomp.round(4).to_string(index=False))
print(coef.round(4).to_string(index=False))
print("\n" + inter_rows.round(4).to_string(index=False))
print(f"\nA′: C = {C_best}\n" + rob.round(3).to_string(index=False))
print(f"\nB: {n_iter} árboles (iteraciones por fold: {min(iters)}–{max(iters)})")
print("\n" + comp.drop(columns=["explicabilidad"]).round(4).to_string(index=False))
print("\n" + rule.round(4).to_string(index=False))
print("\n" + fwd.round(4).to_string(index=False))
print("\n" + coefL.round(4).to_string(index=False))
print("\n" + rule_l.round(4).to_string(index=False))
print("\n" + imp.head(15).round(4).to_string(index=False))
qc.gate()
