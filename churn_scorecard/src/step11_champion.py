"""Paso 11A · Campeón: logística sobre WoE (dev, target B; A como sensibilidad).

- statsmodels GLM Binomial sobre y_bueno = 1 − y_B con WoE = ln(%buenos/%malos) ⟹ todos los β > 0.
- Pesos de clase balanceados (w_B, paso 1); intercepto corregido: β₀ = β₀* − ln(odds buenos muestra ponderada)
  + ln(odds buenos población).
- Desempeño honesto: CV 5×5 anidada (binning re-ajustado dentro de cada fold de entrenamiento) → AUC, Gini, PR-AUC, KS,
  Brier, pendiente de calibración, captura de RV de eventos en el decil superior.
- Reason codes: puntos que pierde cada variable frente a su mejor bin = β·Factor·(WoE máx − WoE); top 1 y top 3.
  Estabilidad en 200 réplicas bootstrap de dev (bins fijos) sobre 1,000 hogares de referencia de dev.
- Sensibilidad A: mismas variables, bins y logística re-ajustados con y_A.
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import FACTOR, MODEL, PROC, SEED, TABLES, load_split, save_table, set_seed
from woe import fit_main, woe_frame

set_seed()
dev = load_split("dev").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
w = D.w_B.to_numpy()
B = pickle.load(open(MODEL / "step09_binning.pkl", "rb"))
V = pickle.load(open(MODEL / "step10_selection.pkl", "rb"))["champion"]
POP = pd.read_parquet(PROC / "step01_population.parquet")
LN_ODDS_GOOD_POP = {t: float(np.log((1 - POP.loc[POP[f"in_pop_{t}"], f"y_{t}"].mean()) / POP.loc[POP[f"in_pop_{t}"], f"y_{t}"].mean())) for t in ("A", "B")}
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]


def fit_glm(X, yy, ww, target="B"):
    m = sm.GLM(1 - yy, sm.add_constant(X, has_constant="add"), family=sm.families.Binomial(), freq_weights=ww).fit()
    ln_odds_s = np.log(ww[yy == 0].sum() / ww[yy == 1].sum())
    b0 = m.params.iloc[0] - ln_odds_s + LN_ODDS_GOOD_POP[target]
    return m, b0


def p_churn(X, m, b0):
    return 1 / (1 + np.exp(b0 + X.to_numpy() @ m.params.iloc[1:].to_numpy()))


def ks(yy, p):
    o = np.argsort(-p)
    c1, c0 = np.cumsum(yy[o]) / yy.sum(), np.cumsum(1 - yy[o]) / (1 - yy).sum()
    return float(np.max(np.abs(c1 - c0)))


def cal_slope(yy, p):
    lg = np.log(p / (1 - p))
    return float(sm.GLM(yy, sm.add_constant(lg), family=sm.families.Binomial()).fit().params[1])


def rv_capture(yy, p, rv, q=0.10):
    top = p >= np.quantile(p, 1 - q)
    return float((rv * yy)[top].sum() / (rv * yy).sum())


def metrics(yy, p, rv):
    a = roc_auc_score(yy, p)
    return {"AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(yy, p), "KS": ks(yy, p), "Brier": brier_score_loss(yy, p),
            "pendiente calibración b": cal_slope(yy, p), "captura RV eventos decil 1": rv_capture(yy, p, rv)}


# ── Modelo final en dev ──────────────────────────────────────────────────────────────────────────────────────
W = woe_frame(D, B, V)
m, b0 = fit_glm(W, y, w)
coef = pd.DataFrame({"variable": ["intercepto"] + V, "β (muestra ponderada)": m.params.to_numpy(), "EE": m.bse.to_numpy(),
                     "z": m.tvalues.to_numpy(), "p-valor": m.pvalues.to_numpy()})
coef["β final"] = coef["β (muestra ponderada)"]
coef.loc[0, "β final"] = b0
vif = [np.nan] + [variance_inflation_factor(W.assign(const=1.0).to_numpy(), i) for i in range(len(V))]
coef["VIF (WoE)"] = vif
save_table(coef, "step11A_coefficients")
p_dev = p_churn(W, m, b0)

# ── CV 5×5 anidada ───────────────────────────────────────────────────────────────────────────────────────────
rows, oof = [], {}
for rr, k in FOLDS:
    cv = D[f"cv_r{rr}"].to_numpy()
    tr, te = cv != k, cv == k
    Dtr, Dte = D[tr].reset_index(drop=True), D[te].reset_index(drop=True)
    Bf = {c: fit_main(c, Dtr, y[tr]) for c in V}
    mf, b0f = fit_glm(woe_frame(Dtr, Bf, V), y[tr], w[tr])
    pte = p_churn(woe_frame(Dte, Bf, V), mf, b0f)
    ptr = p_churn(woe_frame(Dtr, Bf, V), mf, b0f)
    rows.append({"repetición": rr, "fold": k, **metrics(y[te], pte, Dte.relationship_value.to_numpy()),
                 "Gini entrenamiento": 2 * roc_auc_score(y[tr], ptr) - 1, "β > 0 todos": bool((mf.params.iloc[1:] > 0).all())})
    if rr == 1:
        oof.update(dict(zip(Dte.household_id, pte)))
cvt = pd.DataFrame(rows)
save_table(cvt, "step11A_cv_folds")
pd.DataFrame({"household_id": list(oof), "p_champion_oof_r1": list(oof.values())}).to_parquet(PROC / "step11A_oof.parquet", index=False)

# ── Reason codes y estabilidad (200 bootstrap, bins fijos) ──────────────────────────────────────────────────
WMAX = np.array([max(B[c].woe.values()) for c in V])
rng = np.random.default_rng(SEED)
ref = rng.choice(len(D), 1000, replace=False)
Wr = W.iloc[ref].to_numpy()


def reasons(beta):
    loss = beta * FACTOR * (WMAX - Wr)                         # puntos perdidos vs. mejor bin
    return np.argsort(-loss, axis=1)[:, :3], loss


base_top, base_loss = reasons(m.params.iloc[1:].to_numpy())
agree1, agree3, sign_ok = [], [], []
for b in range(200):
    i = rng.choice(len(D), len(D), replace=True)
    mb, _ = fit_glm(W.iloc[i], y[i], w[i])
    beta = mb.params.iloc[1:].to_numpy()
    sign_ok.append(bool((beta > 0).all()))
    t, _ = reasons(beta)
    agree1.append((t[:, 0] == base_top[:, 0]).astype(float))
    agree3.append(np.array([len(set(a) & set(bb)) / 3 for a, bb in zip(t, base_top)]))
agree1, agree3 = np.array(agree1), np.array(agree3)
has_reason = base_loss.max(axis=1) > 0
rc = pd.DataFrame([{"modelo": "campeón", "réplicas": 200, "hogares referencia": len(ref), "con al menos 1 reason code": int(has_reason.sum()),
                    "acuerdo top 1 %": 100 * agree1[:, has_reason].mean(), "acuerdo top 3 %": 100 * agree3[:, has_reason].mean(),
                    "% hogares con acuerdo top 1 ≥ 70%": 100 * (agree1[:, has_reason].mean(0) >= 0.70).mean(),
                    "% réplicas con todos los β > 0": 100 * np.mean(sign_ok)}])
save_table(rc, "step11A_reason_stability")

# ── Sensibilidad target A ────────────────────────────────────────────────────────────────────────────────────
DA = dev[dev.in_pop_A.astype(bool)].reset_index(drop=True)
yA = DA.y_A.astype(int).to_numpy()
rowsA = []
for rr, k in FOLDS[:5]:
    cv = DA[f"cv_r{rr}"].to_numpy()
    tr, te = cv != k, cv == k
    Dtr, Dte = DA[tr].reset_index(drop=True), DA[te].reset_index(drop=True)
    BfB = {c: fit_main(c, Dtr[Dtr.in_pop_B].reset_index(drop=True), Dtr.loc[Dtr.in_pop_B, "y_B"].astype(int).to_numpy()) for c in V}
    DtrB = Dtr[Dtr.in_pop_B].reset_index(drop=True)
    mB, b0B = fit_glm(woe_frame(DtrB, BfB, V), DtrB.y_B.astype(int).to_numpy(), DtrB.w_B.to_numpy())
    BfA = {c: fit_main(c, Dtr, yA[tr]) for c in V}
    mA, b0A = fit_glm(woe_frame(Dtr, BfA, V), yA[tr], Dtr.w_A.to_numpy(), "A")
    pB = p_churn(woe_frame(Dte, BfB, V), mB, b0B)
    pA = p_churn(woe_frame(Dte, BfA, V), mA, b0A)
    rowsA.append({"fold": k, "AUC vs A · modelo B": roc_auc_score(yA[te], pB), "AUC vs A · modelo A": roc_auc_score(yA[te], pA),
                  "PR-AUC vs A · modelo B": average_precision_score(yA[te], pB), "PR-AUC vs A · modelo A": average_precision_score(yA[te], pA),
                  "β > 0 todos (A)": bool((mA.params.iloc[1:] > 0).all())})
sa = pd.DataFrame(rowsA)
save_table(sa, "step11A_sensitivity_A")

with open(MODEL / "step11A_champion.pkl", "wb") as fh:
    pickle.dump({"vars": V, "params": m.params, "b0_corr": b0, "binning": {c: B[c] for c in V}, "ln_odds_good_pop": LN_ODDS_GOOD_POP["B"]}, fh)
summ = cvt.drop(columns=["repetición", "fold", "β > 0 todos"]).agg(["mean", "std"]).T.reset_index().rename(columns={"index": "métrica", "mean": "media", "std": "sd"})
save_table(summ, "step11A_cv_summary")
print(coef.round(4).to_string(index=False)); print(summ.round(4).to_string(index=False)); print(rc.round(1).to_string(index=False)); print(sa.mean(numeric_only=True).round(4))
print("media p dev", p_dev.mean(), "tasa pop B", 1 / (1 + np.exp(LN_ODDS_GOOD_POP["B"])))
