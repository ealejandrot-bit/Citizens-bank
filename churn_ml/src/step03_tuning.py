"""Paso 3 · Algoritmo e hiperparámetros (termina en G1). Dev, target B, CV 5×5.

- XGBoost y LightGBM con monotonía por signo de negocio (I-3); Optuna TPE (semilla 42), 150 trials cada uno,
  MedianPruner, objetivo = PR-AUC media en los 25 folds. Espacio del SPEC; n_estimators por early stopping (50 rondas)
  en un 15% interno estratificado del fold de entrenamiento; LightGBM con num_leaves = 2^max_depth.
- Pesos de clase: scale_pos_weight = n0/n1 del fold; probabilidad corregida por prior (logit − ln spw).
- Evaluación final de cada algoritmo con n_estimators fijo (mediana del mejor trial) en 5×5; 3 semillas.
- Referencias (5 folds de r1): EBM monotónico, RF, campeón M1 (OOF heredado).
- Elección: mayor PR-AUC media; si la diferencia ≤ 1 sd de los folds, el más simple (árboles × profundidad) (D3.1).
"""
from __future__ import annotations

import json
import pickle
import warnings

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import statsmodels.api as sm
import xgboost as xgb
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from common import INH, MODEL, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)
set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
rv = D.relationship_value.to_numpy()
S = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
V = S["vars"]
MONO = [{"+": 1, "−": -1}.get(S["signs"][c], 0) for c in V]
X = D[V].copy()
if "cluster" in X:
    X["cluster"] = X["cluster"].astype("category")
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
CV = {r: D[f"cv_r{r}"].to_numpy() for r in range(1, 6)}
N_TRIALS = 150


def make(algo, p, spw, seed=SEED, n=2000):
    if algo == "xgboost":
        return xgb.XGBClassifier(**p, n_estimators=n, tree_method="hist", enable_categorical=True, monotone_constraints=tuple(MONO),
                                 scale_pos_weight=spw, random_state=seed, n_jobs=4, eval_metric="aucpr")
    q = {"max_depth": p["max_depth"], "num_leaves": 2 ** p["max_depth"], "min_child_weight": p["min_child_weight"], "learning_rate": p["learning_rate"],
         "subsample": p["subsample"], "subsample_freq": 1, "colsample_bytree": p["colsample_bytree"], "reg_lambda": p["reg_lambda"],
         "reg_alpha": p["reg_alpha"], "min_split_gain": p["gamma"]}
    return lgb.LGBMClassifier(**q, n_estimators=n, monotone_constraints=MONO, scale_pos_weight=spw, random_state=seed, n_jobs=4, verbose=-1)


def fit_es(algo, p, Xtr, ytr, seed=SEED):
    spw = (ytr == 0).sum() / ytr.sum()
    a, b, ya, yb = train_test_split(Xtr, ytr, test_size=0.15, stratify=ytr, random_state=seed)
    m = make(algo, p, spw, seed)
    if algo == "xgboost":
        m.set_params(early_stopping_rounds=50)
        m.fit(a, ya, eval_set=[(b, yb)], verbose=False)
        n = m.best_iteration + 1
    else:
        m.fit(a, ya, eval_set=[(b, yb)], eval_metric="average_precision", callbacks=[lgb.early_stopping(50, verbose=False)])
        n = m.best_iteration_
    return m, n, spw


def margin(m, Xt):
    return m.predict(Xt, output_margin=True) if isinstance(m, xgb.XGBClassifier) else m.predict(Xt, raw_score=True)


def space(t):
    return {"max_depth": t.suggest_categorical("max_depth", [2, 3]), "min_child_weight": t.suggest_float("min_child_weight", 5, 50),
            "learning_rate": t.suggest_float("learning_rate", 0.01, 0.1, log=True), "subsample": t.suggest_float("subsample", 0.6, 0.9),
            "colsample_bytree": t.suggest_float("colsample_bytree", 0.5, 0.9), "reg_lambda": t.suggest_float("reg_lambda", 1, 20),
            "reg_alpha": t.suggest_float("reg_alpha", 0, 5), "gamma": t.suggest_float("gamma", 0, 5)}


BEST, TRIALS = {}, []
for algo in ("xgboost", "lightgbm"):
    def objective(trial, algo=algo):
        p = space(trial)
        s, nt = [], []
        for i, (r, k) in enumerate(FOLDS):
            tr, te = CV[r] != k, CV[r] == k
            m, n, _ = fit_es(algo, p, X[tr], y[tr])
            s.append(average_precision_score(y[te], margin(m, X[te])))
            nt.append(n)
            trial.report(float(np.mean(s)), i)
            if trial.should_prune():
                raise optuna.TrialPruned()
        trial.set_user_attr("n_estimators", int(np.median(nt)))
        return float(np.mean(s))
    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=SEED),
                             pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=5))
    st.optimize(objective, n_trials=N_TRIALS,
                callbacks=[lambda s_, t, a=algo: print(f"{a} trial {t.number + 1}/{N_TRIALS} mejor {s_.best_value:.4f}", flush=True) if (t.number + 1) % 25 == 0 else None])
    df = st.trials_dataframe()
    df.insert(0, "algoritmo", algo)
    TRIALS.append(df)
    BEST[algo] = {"params": st.best_params, "n_estimators": st.best_trial.user_attrs["n_estimators"], "cv_optuna": st.best_value,
                  "completos": int((df.state == "COMPLETE").sum()), "podados": int((df.state == "PRUNED").sum())}
save_table(pd.concat(TRIALS, ignore_index=True), "step03_optuna_trials")


def ks(yy, p):
    o = np.argsort(-p)
    return float(np.max(np.abs(np.cumsum(yy[o]) / yy.sum() - np.cumsum(1 - yy[o]) / (1 - yy).sum())))


def slope(yy, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(sm.GLM(yy, sm.add_constant(np.log(p / (1 - p))), family=sm.families.Binomial()).fit().params[1])


def metrics(yy, p, r):
    a = roc_auc_score(yy, p)
    top = p >= np.quantile(p, 0.9)
    return {"AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(yy, p), "KS": ks(yy, p), "Brier": brier_score_loss(yy, p),
            "pendiente b": slope(yy, p), "captura RV eventos decil 1": float((r * yy)[top].sum() / (r * yy).sum())}


rows, OOF = [], {}
for algo, B_ in BEST.items():
    for sd in (SEED, SEED + 1, SEED + 2):
        oof = np.zeros((5, len(y)))
        for r, k in FOLDS:
            tr, te = CV[r] != k, CV[r] == k
            spw = (y[tr] == 0).sum() / y[tr].sum()
            m = make(algo, B_["params"], spw, sd, B_["n_estimators"]).fit(X[tr], y[tr])
            p = 1 / (1 + np.exp(-(margin(m, X[te]) - np.log(spw))))
            ptr = 1 / (1 + np.exp(-(margin(m, X[tr]) - np.log(spw))))
            oof[r - 1, te] = p
            rows.append({"algoritmo": algo, "semilla": sd, "repetición": r, "fold": k, **metrics(y[te], p, rv[te]), "Gini entrenamiento": 2 * roc_auc_score(y[tr], ptr) - 1})
        if sd == SEED:
            OOF[algo] = oof
CVT = pd.DataFrame(rows)
save_table(CVT, "step03_cv_folds")
pd.DataFrame({"household_id": D.household_id, **{f"p_{a}_r{r + 1}": OOF[a][r] for a in OOF for r in range(5)}}).to_parquet(PROC / "step03_oof.parquet", index=False)
main = CVT[CVT.semilla == SEED]
SUM = main.groupby("algoritmo").agg(**{f"{m} media": (m, "mean") for m in ["AUC", "Gini", "PR-AUC", "KS", "Brier", "pendiente b", "captura RV eventos decil 1", "Gini entrenamiento"]},
                                    **{"PR-AUC sd": ("PR-AUC", "std")}).reset_index()
SUM["árboles"] = SUM.algoritmo.map({a: b["n_estimators"] for a, b in BEST.items()})
SUM["profundidad"] = SUM.algoritmo.map({a: b["params"]["max_depth"] for a, b in BEST.items()})
SUM["complejidad (árboles × prof.)"] = SUM["árboles"] * SUM["profundidad"]
SEEDS = CVT.groupby(["algoritmo", "semilla"])["PR-AUC"].mean().unstack().reset_index()
save_table(SEEDS, "step03_seeds")
s_ = SUM.sort_values("PR-AUC media", ascending=False).reset_index(drop=True)
if s_.loc[0, "PR-AUC media"] - s_.loc[1, "PR-AUC media"] <= s_.loc[0, "PR-AUC sd"]:
    CHOICE = s_.sort_values("complejidad (árboles × prof.)").algoritmo.iloc[0]
    why = "diferencia ≤ 1 sd ⟹ el más simple"
else:
    CHOICE, why = s_.algoritmo.iloc[0], "mayor PR-AUC por más de 1 sd"
SUM["elegido"] = SUM.algoritmo == CHOICE
save_table(SUM, "step03_algorithms")

# Referencias en r1 (5 folds): EBM, RF, campeón M1 y los dos GBM
m1 = pd.read_parquet(INH / "m1_champion_oof_r1.parquet").set_index("household_id").loc[D.household_id, "p_champion_oof_r1"].to_numpy()
ref, p_ebm, p_rf = [], np.zeros(len(y)), np.zeros(len(y))
XR = X.copy()
if "cluster" in XR:
    XR["cluster"] = XR["cluster"].cat.codes
for k in range(5):
    tr, te = CV[1] != k, CV[1] == k
    p_ebm[te] = ExplainableBoostingClassifier(monotone_constraints=MONO, interactions=0, random_state=SEED, n_jobs=4).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    spw = (y[tr] == 0).sum() / y[tr].sum()
    pr = np.clip(RandomForestClassifier(500, min_samples_leaf=50, class_weight="balanced_subsample", random_state=SEED, n_jobs=4).fit(XR[tr], y[tr]).predict_proba(XR[te])[:, 1], 1e-6, 1 - 1e-6)
    p_rf[te] = 1 / (1 + np.exp(-(np.log(pr / (1 - pr)) - np.log(spw))))
for name, p in (("campeón M1 (logística WoE)", m1), ("EBM monotónico", p_ebm), ("RF (corregido por prior)", p_rf), ("XGBoost", OOF["xgboost"][0]), ("LightGBM", OOF["lightgbm"][0])):
    fm = [metrics(y[CV[1] == k], p[CV[1] == k], rv[CV[1] == k]) for k in range(5)]
    ref.append({"modelo": name, **{f"{m} media": np.mean([f[m] for f in fm]) for m in ["AUC", "Gini", "PR-AUC", "Brier", "pendiente b", "captura RV eventos decil 1"]}})
REF = pd.DataFrame(ref)
save_table(REF, "step03_references_r1")
with open(MODEL / "step03_choice.pkl", "wb") as fh:
    pickle.dump({"algo": CHOICE, "best": BEST, "vars": V, "mono": MONO}, fh)
BT = pd.DataFrame([{"algoritmo": a, "árboles": b["n_estimators"], "trials completos": b["completos"], "podados": b["podados"], "PR-AUC Optuna": b["cv_optuna"],
                    **{f"param {k}": v for k, v in b["params"].items()}} for a, b in BEST.items()])
save_table(BT, "step03_best_params")

rep = f"""# Paso 3 · Algoritmo e hiperparámetros

## Objetivo
- Elegir algoritmo e hiperparámetros del ML con la CV 5×5 de dev y compararlo con las referencias.

## Método
- XGBoost y LightGBM monotónicos, Optuna 150 trials cada uno (TPE semilla 42, MedianPruner), objetivo PR-AUC media 5×5;
  early stopping en 15% interno; probabilidad corregida por prior. 3 semillas. Referencias en r1: EBM, RF, campeón M1.
- Regla de elección (D3.1): mayor PR-AUC; si la diferencia ≤ 1 sd, el más simple.

## Código
- `src/step03_tuning.py` · `tests/test_step03.py` · `step03_*.csv`, `outputs/model/step03_choice.pkl`.

## Resultados

### Mejores hiperparámetros [DATA]
{md_table(BT, floatfmt=",.4f")}

### Algoritmos (CV 5×5, semilla 42) [DATA]
{md_table(SUM, floatfmt=",.4f")}

- Elegido: **{CHOICE}** ({why}) [DATA].

### Sensibilidad a la semilla (PR-AUC media) [DATA]
{md_table(SEEDS, floatfmt=",.4f")}

### Referencias (5 folds de r1, mismos hogares) [DATA]
{md_table(REF, floatfmt=",.4f")}

## Tests
- `tests/test_step03.py` (ver pytest).

## Decisiones y preguntas abiertas
- D3.1–D3.2 en `reports/decision_log.md`; preguntas G1 en `reports/gate_1.md`.
"""
(REPORTS / "step03.md").write_text(rep, encoding="utf-8")
print(BT.round(4).to_string(index=False)); print(SUM.round(4).to_string(index=False)); print(SEEDS.round(4).to_string(index=False)); print(REF.round(4).to_string(index=False)); print("elegido", CHOICE, why)
