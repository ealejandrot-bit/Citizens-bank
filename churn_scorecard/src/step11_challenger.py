"""Paso 11B · Challenger: XGBoost monotónico (Optuna), EBM, variante WoE, RF de referencia (dev, target B).

- Variables: preselección del paso 10 (valores crudos, NaN nativo, `cluster` categórica).
- Monotonía: signo a priori + → +1, − → −1, "?" → 0 (G1-1); compuestos +1.
- Optuna (TPE, semilla 42): max_depth {2,3}, min_child_weight [5,50], learning_rate log-U[0.01,0.1], subsample [0.6,0.9],
  colsample_bytree [0.5,0.9], reg_lambda [1,20], reg_alpha [0,5], gamma [0,5]; n_estimators por early stopping
  (50 rondas, 15% interno del fold de entrenamiento); 150 trials; MedianPruner; objetivo = PR-AUC media en la CV 5×5.
- Pesos de clase: scale_pos_weight = n0/n1 del fold; probabilidad corregida por prior: logit − ln(spw) + 0 (ver D11.3).
- Sensibilidad a 3 semillas; variante con entradas WoE; EBM monotónico; RF de referencia.
- Explicabilidad: TreeSHAP raw (log-odds); ICE/PDP (violaciones de monotonía); interacciones SHAP; ALE (top 5);
  estabilidad de reason codes (top 1 / top 3 SHAP positivo) en 200 réplicas bootstrap sobre 1,000 hogares de referencia.
"""
from __future__ import annotations

import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import shap
import xgboost as xgb
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from common import FIGS, MODEL, PROC, SEED, TABLES, load_split, save_table, set_seed
from woe import fit_main, woe_frame

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
set_seed()
dev = load_split("dev").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
rv = D.relationship_value.to_numpy()
V = pickle.load(open(MODEL / "step10_selection.pkl", "rb"))["challenger"]
SIGN = pd.read_csv(TABLES / "step05_features.csv").set_index("variable")["signo esperado"].to_dict()
SIGN.update({"multi_signal_count": "+", "multi_signal_flag": "+"})
MONO = tuple({"+": 1, "−": -1}.get(SIGN.get(c, "?"), 0) if c != "cluster" else 0 for c in V)
X = D[V].copy()
if "cluster" in X:
    X["cluster"] = X["cluster"].astype("category")
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
CV = {rr: D[f"cv_r{rr}"].to_numpy() for rr in range(1, 6)}
N_TRIALS = 150


def model(params, spw, seed=SEED, n=1000):
    return xgb.XGBClassifier(**params, n_estimators=n, tree_method="hist", enable_categorical=True, monotone_constraints=MONO,
                             scale_pos_weight=spw, random_state=seed, n_jobs=4, eval_metric="aucpr")


def fit_es(params, Xtr, ytr, seed=SEED):
    """Early stopping en un 15% interno estratificado del entrenamiento; devuelve modelo y nº de árboles."""
    spw = (ytr == 0).sum() / ytr.sum()
    a, b, ya, yb = train_test_split(Xtr, ytr, test_size=0.15, stratify=ytr, random_state=seed)
    m = model(params, spw, seed)
    m.set_params(early_stopping_rounds=50)
    m.fit(a, ya, eval_set=[(b, yb)], verbose=False)
    return m, m.best_iteration + 1, spw


def p_corr(m, Xte, spw):
    lg = m.predict(Xte, output_margin=True)
    return 1 / (1 + np.exp(-(lg - np.log(spw))))


def ks(yy, p):
    o = np.argsort(-p)
    return float(np.max(np.abs(np.cumsum(yy[o]) / yy.sum() - np.cumsum(1 - yy[o]) / (1 - yy).sum())))


def cal_slope(yy, p):
    import statsmodels.api as sm
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(sm.GLM(yy, sm.add_constant(np.log(p / (1 - p))), family=sm.families.Binomial()).fit().params[1])


def metrics(yy, p, r):
    a = roc_auc_score(yy, p)
    top = p >= np.quantile(p, 0.9)
    return {"AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(yy, p), "KS": ks(yy, p), "Brier": brier_score_loss(yy, p),
            "pendiente calibración b": cal_slope(yy, p), "captura RV eventos decil 1": float((r * yy)[top].sum() / (r * yy).sum())}


# ── Optuna ───────────────────────────────────────────────────────────────────────────────────────────────────
def objective(trial):
    params = {"max_depth": trial.suggest_categorical("max_depth", [2, 3]), "min_child_weight": trial.suggest_float("min_child_weight", 5, 50),
              "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1, log=True), "subsample": trial.suggest_float("subsample", 0.6, 0.9),
              "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 0.9), "reg_lambda": trial.suggest_float("reg_lambda", 1, 20),
              "reg_alpha": trial.suggest_float("reg_alpha", 0, 5), "gamma": trial.suggest_float("gamma", 0, 5)}
    s, nt = [], []
    for i, (rr, k) in enumerate(FOLDS):
        tr, te = CV[rr] != k, CV[rr] == k
        m, n, spw = fit_es(params, X[tr], y[tr])
        s.append(average_precision_score(y[te], m.predict(X[te], output_margin=True)))
        nt.append(n)
        trial.report(float(np.mean(s)), i)
        if trial.should_prune():
            raise optuna.TrialPruned()
    trial.set_user_attr("n_estimators_median", int(np.median(nt)))
    trial.set_user_attr("pr_auc_sd", float(np.std(s)))
    return float(np.mean(s))


study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED),
                            pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=5))
study.optimize(objective, n_trials=N_TRIALS,
               callbacks=[lambda st, t: print(f"trial {t.number + 1}/{N_TRIALS} mejor PR-AUC {st.best_value:.4f}", flush=True) if (t.number + 1) % 10 == 0 else None])
trials = study.trials_dataframe()
save_table(trials, "step11B_optuna_trials")
BEST = study.best_params
N_EST = study.best_trial.user_attrs["n_estimators_median"]


# ── CV final (5×5, n_estimators fijo), 3 semillas ────────────────────────────────────────────────────────────
def cv_eval(make, Xm, folds=FOLDS, keep_oof=False):
    rows, oof = [], {}
    for rr, k in folds:
        tr, te = CV[rr] != k, CV[rr] == k
        m, spw = make(Xm[tr], y[tr])
        p = p_corr(m, Xm[te], spw) if isinstance(m, xgb.XGBClassifier) else m.predict_proba(Xm[te])[:, 1]
        ptr = p_corr(m, Xm[tr], spw) if isinstance(m, xgb.XGBClassifier) else m.predict_proba(Xm[tr])[:, 1]
        rows.append({"repetición": rr, "fold": k, **metrics(y[te], p, rv[te]), "Gini entrenamiento": 2 * roc_auc_score(y[tr], ptr) - 1})
        if keep_oof and rr == 1:
            oof.update(dict(zip(D.household_id[te], p)))
    return pd.DataFrame(rows), oof


def mk_xgb(seed):
    def f(Xtr, ytr):
        spw = (ytr == 0).sum() / ytr.sum()
        return model(BEST, spw, seed, N_EST).fit(Xtr, ytr), spw
    return f


print("optuna listo", flush=True)
cv_x, oof = cv_eval(mk_xgb(SEED), X, keep_oof=True)
save_table(cv_x, "step11B_cv_folds_xgb")
pd.DataFrame({"household_id": list(oof), "p_challenger_oof_r1": list(oof.values())}).to_parquet(PROC / "step11B_oof.parquet", index=False)
seeds = []
for sd in (SEED, SEED + 1, SEED + 2):
    c, _ = cv_eval(mk_xgb(sd), X) if sd != SEED else (cv_x, None)
    seeds.append({"semilla": sd, "PR-AUC media": c["PR-AUC"].mean(), "Gini medio": c.Gini.mean()})
seeds = pd.DataFrame(seeds)
save_table(seeds, "step11B_seeds")

# Variante WoE (bins del paso 9; compuestos binados con la misma regla)
B9 = pickle.load(open(MODEL / "step09_binning.pkl", "rb"))
BW = {c: B9[c] if c in B9 else fit_main(c, D, y) for c in V}
XW = woe_frame(D, BW, V)
MONO_W = tuple(-1 for _ in V)                                   # WoE alto = menos churn


def mk_woe(Xtr, ytr):
    spw = (ytr == 0).sum() / ytr.sum()
    m = model(BEST, spw, SEED, N_EST)
    m.set_params(monotone_constraints=MONO_W, enable_categorical=False)
    return m.fit(Xtr, ytr), spw


cv_w, _ = cv_eval(mk_woe, XW)


# EBM monotónico y RF (CV 5 folds de la repetición 1: costo)
def mk_ebm(Xtr, ytr):
    m = ExplainableBoostingClassifier(monotone_constraints=list(MONO), random_state=SEED, n_jobs=4, interactions=0)
    return m.fit(Xtr, ytr), None


def mk_rf(Xtr, ytr):
    Xn = Xtr.copy()
    if "cluster" in Xn:
        Xn["cluster"] = Xn["cluster"].cat.codes
    return RandomForestClassifier(500, min_samples_leaf=50, class_weight="balanced_subsample", random_state=SEED, n_jobs=4).fit(Xn, ytr), None


XE = X.copy()
cv_e, _ = cv_eval(mk_ebm, XE, FOLDS[:5])
XR = X.copy()
if "cluster" in XR:
    XR["cluster"] = XR["cluster"].cat.codes
cv_r, _ = cv_eval(mk_rf, XR, FOLDS[:5])
summ = []
for name, c in [("XGBoost monotónico (Optuna)", cv_x), ("XGBoost entradas WoE", cv_w), ("EBM monotónico (5 folds)", cv_e), ("RF referencia (5 folds)", cv_r)]:
    summ.append({"modelo": name, "folds": len(c), **{f"{m_} media": c[m_].mean() for m_ in ["AUC", "Gini", "PR-AUC", "KS", "Brier", "pendiente calibración b", "captura RV eventos decil 1", "Gini entrenamiento"]},
                 "PR-AUC sd": c["PR-AUC"].std()})
summ = pd.DataFrame(summ)
save_table(summ, "step11B_models_summary")

# ── Modelo final en dev + SHAP ───────────────────────────────────────────────────────────────────────────────
SPW = (y == 0).sum() / y.sum()
M = model(BEST, SPW, SEED, N_EST).fit(X, y)
M.save_model(str(MODEL / "step11B_xgb.json"))
expl = shap.TreeExplainer(M, model_output="raw")
phi = expl.shap_values(X)
imp = pd.DataFrame({"variable": V, "|φ| medio": np.abs(phi).mean(0), "restricción": MONO}).sort_values("|φ| medio", ascending=False)
imp["% de Σ|φ|"] = 100 * imp["|φ| medio"] / imp["|φ| medio"].sum()
save_table(imp, "step11B_shap_importance")
rng = np.random.default_rng(SEED)
# Aditividad SHAP: φ0 + Σφ = margen
marg = M.predict(X, output_margin=True)
add_err = float(np.max(np.abs(expl.expected_value + phi.sum(1) - marg)))

# ICE / PDP: violaciones de monotonía
ice_idx = rng.choice(len(X), 500, replace=False)
viol = []
for j, c in enumerate(V):
    if MONO[j] == 0:
        viol.append({"variable": c, "restricción": 0, "violaciones ICE": np.nan, "violaciones PDP": np.nan})
        continue
    grid = np.unique(np.nanquantile(X[c].astype(float), np.linspace(0, 1, 21)))
    Xi = X.iloc[ice_idx].copy()
    out = []
    for g in grid:
        Xi[c] = g
        out.append(M.predict(Xi, output_margin=True))
    out = np.array(out).T                                        # hogares × grid
    d = np.diff(out, axis=1) * MONO[j]
    viol.append({"variable": c, "restricción": MONO[j], "violaciones ICE": int((d < -1e-6).sum()), "violaciones PDP": int((np.diff(out.mean(0)) * MONO[j] < -1e-6).sum())})
viol = pd.DataFrame(viol)
save_table(viol, "step11B_monotonicity")

# Interacciones SHAP
ii = rng.choice(len(X), 2000, replace=False)
inter = expl.shap_interaction_values(X.iloc[ii])
tot = np.abs(inter).sum(axis=(1, 2)).sum()
diag = np.abs(np.einsum("nii->ni", inter)).sum()
per = []
for j, c in enumerate(V):
    a = np.abs(inter[:, j, :]).sum()
    off = a - np.abs(inter[:, j, j]).sum()
    k = int(np.argmax(np.where(np.arange(len(V)) == j, -1, np.abs(inter[:, j, :]).sum(0))))
    per.append({"variable": c, "% interacción en |φ|": 100 * off / a if a > 0 else 0.0, "principal socio": V[k]})
per = pd.DataFrame(per).sort_values("% interacción en |φ|", ascending=False)
per["> 20%"] = per["% interacción en |φ|"] > 20
save_table(per, "step11B_interactions")
inter_share = 100 * (tot - diag) / tot

# ALE (primer orden) de las 5 variables de mayor |φ|
top5 = imp.variable.head(5).tolist()
fig, axes = plt.subplots(1, 5, figsize=(18, 3.6))
ale_rows = []
for ax, c in zip(axes, top5):
    xv = X[c].astype(float)
    ok = xv.notna().to_numpy()
    edges = np.unique(np.nanquantile(xv, np.linspace(0, 1, 11)))
    eff = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m_ = ok & (xv >= lo).to_numpy() & (xv <= hi).to_numpy()
        if m_.sum() == 0:
            eff.append(0.0)
            continue
        a_, b_ = X[m_].copy(), X[m_].copy()
        a_[c], b_[c] = lo, hi
        eff.append(float((M.predict(b_, output_margin=True) - M.predict(a_, output_margin=True)).mean()))
    ale = np.concatenate([[0], np.cumsum(eff)])
    ale -= ale.mean()
    for e_, a_ in zip(edges, ale):
        ale_rows.append({"variable": c, "x": e_, "ALE (log-odds)": a_})
    ax.plot(edges, ale, color="#2a78d6", marker="o", ms=3)
    ax.set_title(c, fontsize=8, loc="left")
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
    ax.tick_params(labelsize=7)
fig.suptitle("ALE de las 5 variables de mayor |φ| · challenger XGBoost · dev [DATA]", x=0.01, ha="left", fontsize=10)
fig.tight_layout(rect=(0, 0, 1, 0.92))
FIGS.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGS / "step11B_ale_top5.png", dpi=110)
save_table(pd.DataFrame(ale_rows), "step11B_ale")

# Estabilidad de reason codes (SHAP positivo = empuja a churn)
ref = rng.choice(len(X), 1000, replace=False)
Xref = X.iloc[ref]
phr = phi[ref]


def top3(ph):
    return np.argsort(-ph, axis=1)[:, :3]


base = top3(phr)
has_reason = phr.max(axis=1) > 0
print("bootstrap reason codes", flush=True)
a1, a3, sgn = [], [], []
for b in range(200):
    i = rng.choice(len(X), len(X), replace=True)
    mb = model(BEST, SPW, SEED + b, N_EST).fit(X.iloc[i], y[i])
    pb = shap.TreeExplainer(mb, model_output="raw").shap_values(Xref)
    t = top3(pb)
    a1.append((t[:, 0] == base[:, 0]).astype(float))
    a3.append(np.array([len(set(u) & set(v)) / 3 for u, v in zip(t, base)]))
    # coherencia de signo: correlación φ_j vs x_j con el signo de la restricción
    s_ = []
    for j, c in enumerate(V):
        if MONO[j] != 0:
            xv = Xref[c].astype(float).to_numpy()
            ok = ~np.isnan(xv)
            s_.append(np.sign(np.corrcoef(xv[ok], pb[ok, j])[0, 1]) in (MONO[j], 0) if np.std(xv[ok]) > 0 and np.std(pb[ok, j]) > 0 else True)
    sgn.append(np.mean(s_))
a1, a3 = np.array(a1), np.array(a3)
rc = pd.DataFrame([{"modelo": "challenger XGBoost", "réplicas": 200, "hogares referencia": len(ref), "con al menos 1 reason code": int(has_reason.sum()),
                    "acuerdo top 1 %": 100 * a1[:, has_reason].mean(), "acuerdo top 3 %": 100 * a3[:, has_reason].mean(),
                    "% hogares con acuerdo top 1 ≥ 70%": 100 * (a1[:, has_reason].mean(0) >= 0.70).mean(),
                    "% variables con signo coherente (media réplicas)": 100 * np.mean(sgn)}])
save_table(rc, "step11B_reason_stability")
diag_t = pd.DataFrame([{"error máx. aditividad SHAP": add_err, "% interacción en Σ|φ| (global)": inter_share,
                        "n_estimators": N_EST, **{f"param {k}": v for k, v in BEST.items()}, "PR-AUC Optuna (mejor trial)": study.best_value,
                        "trials completos": int((trials.state == "COMPLETE").sum()), "trials podados": int((trials.state == "PRUNED").sum())}])
save_table(diag_t, "step11B_diagnostics")
with open(MODEL / "step11B_challenger.pkl", "wb") as fh:
    pickle.dump({"vars": V, "mono": MONO, "params": BEST, "n_estimators": N_EST, "spw": SPW}, fh)
print(summ.round(4).to_string(index=False)); print(seeds.round(4).to_string(index=False)); print(imp.round(4).to_string(index=False))
print(viol.to_string(index=False)); print(per.head(10).round(1).to_string(index=False)); print(rc.round(1).to_string(index=False)); print(diag_t.T)
