"""Paso 4 · Explicabilidad del candidato principal (EBM) y del segundo (XGBoost). Dev, target B.

- EBM monotónico sin interacciones (G1-1): logit = intercepto + Σ f_j(x_j) exacto; funciones de forma por bin (tabla y
  figura); monotonía verificada en las funciones y por ICE/PDP.
- XGBoost (paso 3): TreeSHAP raw (log-odds), aditividad φ₀ + Σφ = margen, ICE/PDP, interacciones SHAP.
- Ambos: importancia (|contribución| media), ALE de las 5 principales, reason codes = top 3 contribuciones positivas
  (empujan a churn) y su estabilidad en 200 réplicas bootstrap sobre 1,000 hogares de referencia; coherencia de signo.
"""
from __future__ import annotations

import json
import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from interpret.glassbox import ExplainableBoostingClassifier

from common import FIGS, MODEL, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
S = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
V = S["vars"]
MONO = [{"+": 1, "−": -1}.get(S["signs"][c], 0) for c in V]
X = D[V].copy()
CH = pickle.load(open(MODEL / "step03_choice.pkl", "rb"))
XB = CH["best"]["xgboost"]
SPW = (y == 0).sum() / y.sum()


def ebm(seed=SEED):
    return ExplainableBoostingClassifier(monotone_constraints=MONO, interactions=0, random_state=seed, n_jobs=4)


def xgbm(seed=SEED):
    return xgb.XGBClassifier(**XB["params"], n_estimators=XB["n_estimators"], tree_method="hist", monotone_constraints=tuple(MONO),
                             scale_pos_weight=SPW, random_state=seed, n_jobs=4)


E = ebm().fit(X, y)
M = xgbm().fit(X, y)
with open(MODEL / "step04_ebm.pkl", "wb") as fh:
    pickle.dump(E, fh)
M.save_model(str(MODEL / "step04_xgb.json"))

CE = E.eval_terms(X)                                              # contribuciones EBM (log-odds)
add_e = float(np.max(np.abs(E.intercept_[0] + CE.sum(1) - E.decision_function(X))))
EX = shap.TreeExplainer(M, model_output="raw")
CX = EX.shap_values(X).astype(float)                           # float64: los % suman 100 exacto
add_x = float(np.max(np.abs(EX.expected_value + CX.sum(1) - M.predict(X, output_margin=True))))

# Funciones de forma EBM
shape_rows = []
for j, c in enumerate(V):
    cuts = np.asarray(E.bins_[j][0], float)
    sc = np.asarray(E.term_scores_[j], float)                     # [missing, bin_1..bin_n, unknown]
    edges = np.concatenate([[-np.inf], cuts, [np.inf]])
    b = np.searchsorted(cuts, X[c].to_numpy(float), side="right")
    for i in range(len(cuts) + 1):
        m = (b == i) & X[c].notna().to_numpy()
        shape_rows.append({"variable": c, "bin": f"[{edges[i]:.6g}, {edges[i + 1]:.6g})", "desde": edges[i], "hasta": edges[i + 1],
                           "f(x) log-odds": sc[i + 1], "hogares": int(m.sum()), "tasa B %": 100 * y[m].mean() if m.sum() else np.nan})
    if X[c].isna().any():
        m = X[c].isna().to_numpy()
        shape_rows.append({"variable": c, "bin": "missing", "desde": np.nan, "hasta": np.nan, "f(x) log-odds": sc[0], "hogares": int(m.sum()),
                           "tasa B %": 100 * y[m].mean()})
SH = pd.DataFrame(shape_rows)
save_table(SH, "step04_ebm_shape")
mono_rows = []
for j, c in enumerate(V):
    f = SH[(SH.variable == c) & (SH.bin != "missing")]["f(x) log-odds"].to_numpy()
    viol = int((np.diff(f) * MONO[j] < -1e-9).sum()) if MONO[j] else np.nan
    mono_rows.append({"variable": c, "restricción": MONO[j], "bins": len(f), "violaciones en f(x) EBM": viol})


def ice_viol(model_margin, j, c):
    if MONO[j] == 0:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(X), 500, replace=False)
    grid = np.unique(np.nanquantile(X[c].astype(float), np.linspace(0, 1, 21)))
    Xi = X.iloc[idx].copy()
    out = []
    for g in grid:
        Xi[c] = g
        out.append(model_margin(Xi))
    out = np.array(out).T
    return int((np.diff(out, axis=1) * MONO[j] < -1e-6).sum()), int((np.diff(out.mean(0)) * MONO[j] < -1e-6).sum())


for j, c in enumerate(V):
    ie, pe = ice_viol(E.decision_function, j, c)
    ix, px = ice_viol(lambda Z: M.predict(Z, output_margin=True), j, c)
    mono_rows[j].update({"ICE EBM": ie, "PDP EBM": pe, "ICE XGBoost": ix, "PDP XGBoost": px})
MO = pd.DataFrame(mono_rows)
save_table(MO, "step04_monotonicity")

IMP = pd.DataFrame({"variable": V, "|contribución| media EBM": np.abs(CE).mean(0), "|φ| medio XGBoost": np.abs(CX).mean(0), "signo": [S["signs"][c] for c in V]})
IMP["% EBM"] = 100 * IMP["|contribución| media EBM"] / IMP["|contribución| media EBM"].sum()
IMP["% XGBoost"] = 100 * IMP["|φ| medio XGBoost"] / IMP["|φ| medio XGBoost"].sum()
IMP = IMP.sort_values("% EBM", ascending=False)
save_table(IMP, "step04_importance")

# Interacciones XGBoost (EBM: 0 por construcción)
rng = np.random.default_rng(SEED)
ii = rng.choice(len(X), 2000, replace=False)
inter = EX.shap_interaction_values(X.iloc[ii])
tot, diag = np.abs(inter).sum(), np.abs(np.einsum("nii->ni", inter)).sum()
INT = pd.DataFrame([{"variable": c, "% interacción en |φ| XGBoost": 100 * (np.abs(inter[:, j, :]).sum() - np.abs(inter[:, j, j]).sum()) / np.abs(inter[:, j, :]).sum()}
                    for j, c in enumerate(V)]).sort_values("% interacción en |φ| XGBoost", ascending=False)
INT["> 20%"] = INT["% interacción en |φ| XGBoost"] > 20
save_table(INT, "step04_interactions")


# ALE (primer orden) top 5 del EBM
def ale(model_margin, c, k=10):
    xv = X[c].astype(float)
    ok = xv.notna().to_numpy()
    edges = np.unique(np.nanquantile(xv, np.linspace(0, 1, k + 1)))
    eff = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = ok & (xv >= lo).to_numpy() & (xv <= hi).to_numpy()
        if not m.any():
            eff.append(0.0)
            continue
        a_, b_ = X[m].copy(), X[m].copy()
        a_[c], b_[c] = lo, hi
        eff.append(float((model_margin(b_) - model_margin(a_)).mean()))
    a = np.concatenate([[0], np.cumsum(eff)])
    return edges, a - a.mean()


top = IMP.variable.tolist()
fig, axes = plt.subplots(3, 4, figsize=(17, 10))
for ax, c in zip(axes.flat, top):
    s = SH[(SH.variable == c) & (SH.bin != "missing")]
    xs = np.where(np.isinf(s.desde), s.hasta, s.desde)
    ax.step(xs, s["f(x) log-odds"], where="post", color="#2a78d6", lw=2)
    ax.axhline(0, color="#a3a29c", lw=0.8)
    ax.set_title(f"{c} ({S['signs'][c]})", fontsize=8.5, loc="left")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7, colors="#52514e")
    ax.grid(color="#e6e5df", lw=0.5)
fig.suptitle("EBM · función de forma por variable (log-odds de churn; > 0 = más riesgo que el promedio) · dev [DATA]", x=0.01, ha="left", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.96))
FIGS.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGS / "step04_ebm_shapes.png", dpi=110)
ALE = []
for c in top[:5]:
    e_, a_ = ale(E.decision_function, c)
    ALE += [{"variable": c, "x": u, "ALE EBM (log-odds)": v} for u, v in zip(e_, a_)]
save_table(pd.DataFrame(ALE), "step04_ale_ebm")

# Reason codes y estabilidad (200 bootstrap)
ref = rng.choice(len(X), 1000, replace=False)
Xr = X.iloc[ref]


def top3(C):
    return np.argsort(-C, axis=1)[:, :3]


def stability(fit, contrib, base_C, name):
    base = top3(base_C)
    has = base_C.max(1) > 0
    a1, a3, sg = [], [], []
    for b in range(200):
        i = rng.choice(len(X), len(X), replace=True)
        mb = fit(SEED + b).fit(X.iloc[i], y[i])
        Cb = contrib(mb)
        t = top3(Cb)
        a1.append((t[:, 0] == base[:, 0]).astype(float))
        a3.append(np.array([len(set(u) & set(v)) / 3 for u, v in zip(t, base)]))
        s_ = []
        for j, c in enumerate(V):
            if MONO[j] != 0:
                xv = Xr[c].astype(float).to_numpy()
                ok = ~np.isnan(xv)
                if np.std(xv[ok]) > 0 and np.std(Cb[ok, j]) > 0:
                    s_.append(np.sign(np.corrcoef(xv[ok], Cb[ok, j])[0, 1]) == MONO[j])
        sg.append(np.mean(s_))
    a1, a3 = np.array(a1), np.array(a3)
    return {"modelo": name, "réplicas": 200, "hogares referencia": len(ref), "con reason code": int(has.sum()), "acuerdo top 1 %": 100 * a1[:, has].mean(),
            "acuerdo top 3 %": 100 * a3[:, has].mean(), "% hogares con acuerdo top 1 ≥ 70%": 100 * (a1[:, has].mean(0) >= 0.7).mean(),
            "% variables con signo coherente": 100 * np.mean(sg)}


RC = pd.DataFrame([stability(ebm, lambda m: m.eval_terms(Xr), CE[ref], "EBM"),
                   stability(xgbm, lambda m: shap.TreeExplainer(m, model_output="raw").shap_values(Xr), CX[ref], "XGBoost")])
save_table(RC, "step04_reason_stability")
DG = pd.DataFrame([{"modelo": "EBM", "error máx. aditividad": add_e, "% interacción global": 0.0},
                   {"modelo": "XGBoost", "error máx. aditividad": add_x, "% interacción global": 100 * (tot - diag) / tot}])
save_table(DG, "step04_diagnostics")

rep = f"""# Paso 4 · Explicabilidad

## Objetivo
- Verificar que el EBM (principal) y el XGBoost (segundo) se explican por hogar, respetan el signo de negocio y dan
  reason codes estables.

## Método
- EBM sin interacciones: logit = intercepto + Σ f_j(x_j) (exacto). XGBoost: TreeSHAP raw. ICE (500 hogares × 21
  puntos) y PDP por variable restringida; interacciones SHAP (2,000 hogares); ALE top 5 del EBM.
- Reason codes = top 3 contribuciones positivas; estabilidad en 200 réplicas bootstrap sobre 1,000 hogares.

## Código
- `src/step04_explain.py` · `tests/test_step04.py` · `step04_*.csv`, `outputs/model/step04_ebm.pkl`, `step04_xgb.json`.

## Resultados

### Aditividad e interacciones [DATA]
{md_table(DG, floatfmt=",.2e")}

### Importancia [DATA]
{md_table(IMP, floatfmt=",.3f")}

- Verificación: % EBM y % XGBoost suman {IMP['% EBM'].sum():.1f}% y {IMP['% XGBoost'].sum():.1f}% [DATA].

### Monotonía (violaciones) [DATA]
{md_table(MO, floatfmt=",.0f")}

### Funciones de forma del EBM
![EBM](../outputs/figs/step04_ebm_shapes.png)

- Tabla completa por bin: `step04_ebm_shape.csv` [DATA].

### Interacciones XGBoost [DATA]
{md_table(INT, floatfmt=",.1f")}

### Estabilidad de reason codes [DATA]
{md_table(RC, floatfmt=",.1f")}

## Tests
- `tests/test_step04.py` (ver pytest).

## Decisiones y preguntas abiertas
- D4.1 en `reports/decision_log.md`.
"""
(REPORTS / "step04.md").write_text(rep, encoding="utf-8")
print(DG.to_string(index=False)); print(IMP.round(3).to_string(index=False)); print(MO.to_string(index=False)); print(INT.round(1).to_string(index=False)); print(RC.round(1).to_string(index=False))
