"""Paso 2 · Selección de variables del ML (dev, target B, CV 5×5).

Por variante (con compuestos / sin compuestos, I-2):
  1. Permutation importance OOF: GBM base (XGBoost monotónico prof. 3, 300 árboles, lr 0.05) en los 25 folds; ΔPR-AUC
     al permutar cada variable en el fold de prueba (3 permutaciones). Se queda si ΔPR-AUC > 0 en ≥ 80% de los folds.
  2. Eliminación hacia atrás: se quita la variable de menor importancia media mientras la PR-AUC CV no caiga más de
     1 error estándar (regla 1-SE sobre la diferencia pareada por fold; D2.1); mínimo 12 variables.
Elección de variante (I-2): sin compuestos si la diferencia de PR-AUC CV < 1 sd de los folds.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score

from common import COMPOSITES, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
POOL = pd.read_csv(PROC / "step01_pool.csv")
SIGN = POOL.set_index("variable").signo.to_dict()
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
CV = {r: D[f"cv_r{r}"].to_numpy() for r in range(1, 6)}
rng = np.random.default_rng(SEED)


def frame(cols):
    X = D[cols].copy()
    if "cluster" in X:
        X["cluster"] = X["cluster"].astype("category")
    return X


def mono(cols):
    return tuple({"+": 1, "−": -1}.get(SIGN.get(c, "?"), 0) for c in cols)


def model(cols, spw):
    return xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=5,
                             tree_method="hist", enable_categorical=True, monotone_constraints=mono(cols), scale_pos_weight=spw,
                             random_state=SEED, n_jobs=4)


def cv_prauc(cols):
    X = frame(cols)
    out = []
    for r, k in FOLDS:
        tr, te = CV[r] != k, CV[r] == k
        m = model(cols, (y[tr] == 0).sum() / y[tr].sum()).fit(X[tr], y[tr])
        out.append(average_precision_score(y[te], m.predict_proba(X[te])[:, 1]))
    return np.array(out)


def permutation(cols):
    X = frame(cols)
    imp = {c: [] for c in cols}
    for r, k in FOLDS:
        tr, te = CV[r] != k, CV[r] == k
        m = model(cols, (y[tr] == 0).sum() / y[tr].sum()).fit(X[tr], y[tr])
        Xt = X[te].reset_index(drop=True)
        base = average_precision_score(y[te], m.predict_proba(Xt)[:, 1])
        for c in cols:
            d = []
            for _ in range(3):
                Xp = Xt.copy()
                Xp[c] = Xp[c].to_numpy()[rng.permutation(len(Xp))]
                if c == "cluster":
                    Xp[c] = pd.Categorical(Xp[c], categories=X[c].cat.categories)
                d.append(base - average_precision_score(y[te], m.predict_proba(Xp)[:, 1]))
            imp[c].append(np.mean(d))
    return pd.DataFrame({"variable": cols, "ΔPR-AUC medio": [np.mean(imp[c]) for c in cols], "% folds > 0": [100 * np.mean(np.array(imp[c]) > 0) for c in cols]})


results, steps_all, perm_all = {}, [], []
for variant, cols0 in (("con compuestos", POOL.variable.tolist()), ("sin compuestos", [c for c in POOL.variable if c not in COMPOSITES])):
    pi = permutation(cols0).sort_values("ΔPR-AUC medio", ascending=False)
    pi["pasa (≥ 80% folds)"] = pi["% folds > 0"] >= 80
    pi.insert(0, "variante", variant)
    perm_all.append(pi)
    cols = pi[pi["pasa (≥ 80% folds)"]].variable.tolist()
    cur = cv_prauc(cols)
    steps_all.append({"variante": variant, "paso": 0, "quita": "—", "variables": len(cols), "PR-AUC CV": cur.mean(), "Δ vs actual": 0.0, "1-SE": np.nan, "acepta": True})
    order = pi.set_index("variable").loc[cols, "ΔPR-AUC medio"].sort_values().index.tolist()   # menor importancia primero
    step = 0
    while len(cols) > 12 and order:
        cand = order.pop(0)
        trial = [c for c in cols if c != cand]
        s_ = cv_prauc(trial)
        d = s_ - cur
        se = d.std(ddof=1) / np.sqrt(len(d))
        ok = d.mean() >= -se
        step += 1
        steps_all.append({"variante": variant, "paso": step, "quita": cand, "variables": len(trial), "PR-AUC CV": s_.mean(), "Δ vs actual": d.mean(), "1-SE": se, "acepta": bool(ok)})
        if ok:
            cols, cur = trial, s_
    results[variant] = {"cols": cols, "prauc": cur}
PI = pd.concat(perm_all, ignore_index=True)
ST = pd.DataFrame(steps_all)
save_table(PI, "step02_permutation")
save_table(ST, "step02_backward")
a, b = results["con compuestos"], results["sin compuestos"]
diff = a["prauc"].mean() - b["prauc"].mean()
sd = a["prauc"].std(ddof=1)
choice = "sin compuestos" if diff < sd else "con compuestos"
VC = pd.DataFrame([{"variante": k, "variables": len(v["cols"]), "PR-AUC CV media": v["prauc"].mean(), "sd folds": v["prauc"].std(ddof=1),
                    "elegida": k == choice, "variables seleccionadas": ", ".join(v["cols"])} for k, v in results.items()])
save_table(VC, "step02_variants")
SEL = results[choice]["cols"]
(PROC / "step02_selected.json").write_text(json.dumps({"variant": choice, "vars": SEL, "signs": {c: SIGN.get(c, "?") for c in SEL}}, ensure_ascii=False, indent=2), encoding="utf-8")

rep = f"""# Paso 2 · Selección de variables

## Objetivo
- Quedarse con las variables que aportan de forma estable al ML y decidir si entran los compuestos (I-2).

## Método
- Permutation importance OOF en los 25 folds (GBM base monotónico, prof. 3); pasa si ΔPR-AUC > 0 en ≥ 80% de los folds.
- Eliminación hacia atrás (menor importancia primero): se acepta quitar si la PR-AUC CV no cae más de 1 error estándar
  de la diferencia pareada (D2.1); mínimo 12 variables.
- Variante sin compuestos elegida si la diferencia de PR-AUC < 1 sd de los folds [DEF-default I-2].

## Código
- `src/step02_selection.py` · `tests/test_step02.py` · `step02_permutation.csv`, `step02_backward.csv`, `step02_variants.csv`.

## Resultados

### Variantes [DATA]
{md_table(VC, floatfmt=",.4f")}

- Diferencia con − sin compuestos: {diff:+.4f} vs 1 sd = {sd:.4f} ⟹ **{choice}** [DATA].

### Eliminación hacia atrás [DATA]
{md_table(ST, floatfmt=",.4f")}

### Permutation importance [DATA]
{md_table(PI, floatfmt=",.4f")}

## Tests
- `tests/test_step02.py` (ver pytest).

## Decisiones y preguntas abiertas
- D2.1–D2.2 en `reports/decision_log.md`.
"""
(REPORTS / "step02.md").write_text(rep, encoding="utf-8")
print(VC.drop(columns="variables seleccionadas").round(4).to_string(index=False)); print(ST.round(4).to_string(index=False)); print(SEL)
